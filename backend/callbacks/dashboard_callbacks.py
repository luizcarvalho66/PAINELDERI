from dash import Input, Output, State, html, dcc, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import traceback
from backend.repositories import get_ri_evolution_data, check_database_status
from frontend.components.filters.filter_bar import render_filter_bar
from frontend.components.preventiva_section import render_preventiva_section
from frontend.components.kpi_card import render_kpi_card
from frontend.components.dashboard_charts import create_ri_geral_chart, create_comparative_chart
from frontend.components.error_display import render_error_display

def register_dashboard_callbacks(app):
    # Callback 1: Toggle Visibility of Onboarding, Charts and Filters
    @app.callback(
        [Output("onboarding-container", "children"),
         Output("dashboard-charts-container", "style"),
         Output("filter-bar-container", "style")],
        Input("processing-complete-store", "data"),
        prevent_initial_call=True
    )
    def toggle_dashboard_sections(is_processed):
        if not is_processed:
            # Show onboarding, hide charts and filters
            charts_style = {"display": "none"}
            filters_style = {"display": "none"}
            onboarding_content = html.Div([
                # Empty State — Onboarding com botão de Sync
                html.Div([
                    html.Div([
                        html.I(className="bi bi-cloud-arrow-down", 
                               style={"fontSize": "4rem", "color": "#E20613", "opacity": "0.85"})
                    ], className="empty-state-icon mb-3"),
                    html.H2("Bem-vindo ao Painel de RI", 
                            className="empty-state-title", 
                            style={"fontFamily": "Ubuntu", "fontWeight": "700", "color": "#1A1A2E"}),
                    html.P("Nenhum dado encontrado no banco local. Inicie uma sincronização para carregar os dados do Databricks.", 
                           className="empty-state-subtitle",
                           style={"color": "#64748b", "maxWidth": "500px", "margin": "0 auto"}),
                    
                    # Botão de Sync — mesmo ID do sidebar, reusa o callback existente
                    html.Div([
                        html.Button([
                            html.I(className="bi bi-arrow-repeat me-2"),
                            "Sincronizar Dados"
                        ], id="btn-sync-empty-state", className="btn btn-lg",
                           style={
                               "background": "linear-gradient(135deg, #E20613, #c00510)",
                               "color": "white",
                               "border": "none",
                               "borderRadius": "12px",
                               "padding": "14px 36px",
                               "fontWeight": "600",
                               "fontSize": "1.05rem",
                               "boxShadow": "0 4px 14px rgba(226,6,19,0.3)",
                               "cursor": "pointer",
                               "transition": "all 0.2s ease",
                           }),
                    ], className="mt-4"),
                    
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-info-circle me-2", style={"color": "#94a3b8"}),
                            html.Small("A sincronização pode levar alguns minutos dependendo do volume de dados.", 
                                      style={"color": "#94a3b8"})
                        ], className="d-flex align-items-center justify-content-center"),
                    ], className="mt-3"),
                ], className="empty-state-container text-center",
                   style={"padding": "80px 20px"})
            ], className="p-4")
            return onboarding_content, charts_style, filters_style
        else:
            # Show charts and filters, hide onboarding
            return None, {"display": "block"}, {"display": "block"}

    @app.callback(
        Output("dashboard-charts-container", "children"),
        [
            Input("processing-complete-store", "data"),
            Input("global-filters-applied-store", "data"),
        ],
        prevent_initial_call=False
    )
    def update_dashboard_charts(is_processed, filters_state):
        if not is_processed:
            return html.Div()
        
        # Evitar re-render quando filtros são populados inicialmente (None → None)
        triggered_id = ctx.triggered_id
        if triggered_id == 'global-filters-applied-store' and not filters_state:
            return no_update
        
        try:
            return _build_dashboard_content(is_processed, filters_state)
        except Exception as e:
            traceback.print_exc()
            return html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-warning mb-3", style={"fontSize": "2rem"}),
                html.H4("Erro ao carregar o dashboard", className="text-center text-muted"),
                html.P(f"Detalhes: {str(e)[:200]}", className="text-center text-secondary small"),
                html.P("Tente recarregar a página.", className="text-center text-muted mt-2")
            ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
    
    def _build_dashboard_content(is_processed, filters_state):
        """Lógica interna do dashboard, separada para facilitar try/except."""
        
        # Extract filters from state
        filters = None
        if filters_state and filters_state.get("applied"):
            filters = filters_state
        else:
            filters = None
        
        df = get_ri_evolution_data(filters)
        
        # CHECK FOR CRITICAL ERROR STATE
        if 'error_state' in df.columns and df['error_state'].iloc[0] == True:
            return render_error_display(
                error_message=df['message'].iloc[0], 
                technical_details=df['technical_details'].iloc[0]
            )
        
        if df.empty:
            if filters:
                return html.Div([
                    html.I(className="bi bi-funnel-fill text-muted mb-3", style={"fontSize": "2rem"}),
                    html.H4("Nenhum dado encontrado para os filtros selecionados.", className="text-center text-muted"),
                    html.P("Tente limpar os filtros ou selecionar um período diferente.", className="text-center text-secondary small")
                ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
            else:
                return html.Div([
                    html.I(className="bi bi-cloud-slash-fill text-muted mb-3", style={"fontSize": "2rem"}),
                    html.H4("Nenhum dado encontrado.", className="text-center text-muted"),
                    html.P("Os dados podem não ter sido carregados corretamente.", className="text-center text-secondary small")
                ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
            
        # Prepare X-Axis: Simple chronological timeline (Month/Year)
        df['x_label'] = df['mes_nome'].str[:3] + '/' + df['ano'].astype(str)
        
        # --- CALCULATE METRICS FOR KPIs ---
        # 1. Total Analisado
        total_analisado = int((df['qtd_prev'] + df['qtd_corr']).sum())
        
        # 2. RI Geral
        ri_geral_avg = df['ri_geral'].mean() * 100
        
        # 3. Economia Real (Atualizado para Pricing Engine)
        # Corretiva usa a economia_calculada; Preventiva usa delta simples
        econ_corr = df['sum_economia_pricing'].sum() if 'sum_economia_pricing' in df.columns else 0
        econ_prev = (df['sum_total_prev'] - df['sum_aprovado_prev']).clip(lower=0).sum()
        economia_real = econ_corr + econ_prev
        
        # 4. Comparativo Metrics
        total_prev = int(df['qtd_prev'].sum())
        total_corr = int(df['qtd_corr'].sum())
        ratio_prev_corr = (total_prev / (total_corr + total_prev) * 100) if (total_corr + total_prev) > 0 else 0
        
        avg_ri_prev = df['ri_preventiva'].mean() * 100
        avg_ri_corr = df['ri_corretiva'].mean() * 100
        
        # 5. Cálculo de Tendências (comparando último vs penúltimo mês)
        trend_ri_geral = None
        trend_ri_prev = None
        trend_ri_corr = None
        
        if len(df) >= 2:
            df_sorted = df.sort_values('mes_ref')
            ultimo_mes = df_sorted.iloc[-1]
            penultimo_mes = df_sorted.iloc[-2]
            
            # RI Geral Trend
            if penultimo_mes['ri_geral'] > 0:
                trend_ri_geral = ((ultimo_mes['ri_geral'] - penultimo_mes['ri_geral']) / penultimo_mes['ri_geral']) * 100
            
            # RI Preventiva Trend
            if penultimo_mes['ri_preventiva'] > 0:
                trend_ri_prev = ((ultimo_mes['ri_preventiva'] - penultimo_mes['ri_preventiva']) / penultimo_mes['ri_preventiva']) * 100
            
            # RI Corretiva Trend
            if penultimo_mes['ri_corretiva'] > 0:
                trend_ri_corr = ((ultimo_mes['ri_corretiva'] - penultimo_mes['ri_corretiva']) / penultimo_mes['ri_corretiva']) * 100
        
        
        # --- CHARTS GENERATION ---
        fig_geral = create_ri_geral_chart(df)
        fig_comp = create_comparative_chart(df)

        section_title_style = {
            "fontFamily": "Ubuntu", 
            "color": "#1e293b", 
            "fontWeight": "600", 
            "borderLeft": "4px solid #E20613", 
            "paddingLeft": "12px", 
            "marginBottom": "20px"
        }

        return html.Div([
            
            # 1. TOP KPI ROW (Unified Executive Ribbon)
            html.Div([
                dbc.Row([
                    # Group 1: Volumetria & Financeiro
                    dbc.Col(render_kpi_card(
                        "Análise Total", 
                        f"{total_analisado:,}", 
                        "Ordens processadas", 
                        "bi-layers", 
                        "text-primary"
                    ), width=12, sm=6, md=4, lg=2),
                    
                    dbc.Col(render_kpi_card(
                        "Economia Real", 
                        f"R$ {economia_real/1000000:,.1f}M", 
                        "Valor economizado", 
                        "bi-cash-stack", 
                        "text-success"
                    ), width=12, sm=6, md=4, lg=2),
                    
                    dbc.Col(render_kpi_card(
                        "Share Preventiva", 
                        f"{ratio_prev_corr:.1f}%", 
                        "Mix de manutenções", 
                        "bi-pie-chart-fill", 
                        "text-info"
                    ), width=12, sm=6, md=4, lg=2),

                    # Group 2: Performance (RI) com Tendências
                    dbc.Col(render_kpi_card(
                        "RI Geral", 
                        f"{ri_geral_avg:.1f}%", 
                        "Média do período", 
                        "bi-graph-up-arrow", 
                        "text-danger",
                        trend_value=trend_ri_geral,
                        trend_label="vs mês anterior"
                    ), width=12, sm=6, md=4, lg=2),

                    dbc.Col(render_kpi_card(
                        "RI Preventiva", 
                        f"{avg_ri_prev:.1f}%", 
                        "Manutenção programada", 
                        "bi-shield-check", 
                        "text-success",
                        trend_value=trend_ri_prev,
                        trend_label="vs mês anterior"
                    ), width=12, sm=6, md=4, lg=2),

                    dbc.Col(render_kpi_card(
                        "RI Corretiva", 
                        f"{avg_ri_corr:.1f}%", 
                        "Manutenção sob demanda", 
                        "bi-tools", 
                        "text-danger",
                        trend_value=trend_ri_corr,
                        trend_label="vs mês anterior"
                    ), width=12, sm=6, md=4, lg=2),
                    
                ], className="g-3 mb-4")
            ], className="dashboard-top-kpis"),


            # 2. MAIN CONTENT AREA (Stacked Charts)
            html.Div([
                # Row 1: Main Overview Chart (Full Width)
                dbc.Row([
                    dbc.Col([
                        html.H3("Visão Geral", style=section_title_style),
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(
                                    figure=fig_geral, 
                                    config={'displayModeBar': False},
                                    style={"height": "400px"} 
                                ),
                                # --- INSIGHT STRIP ---
                                html.Div([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                html.Small("Máxima do Período", className="text-muted", style={"fontSize": "0.75rem"}),
                                                html.Div([
                                                    html.I(className="bi bi-arrow-up-circle-fill text-success me-2"),
                                                    html.Span(f"{df['ri_geral'].max()*100:.2f}%", className="fw-bold text-dark")
                                                ], className="d-flex align-items-center mt-1"),
                                                html.Small(df.loc[df['ri_geral'].idxmax()]['x_label'], className="text-muted", style={"fontSize": "0.7rem"})
                                            ], className="p-2 rounded bg-light border h-100")
                                        ], width=4),
                                        dbc.Col([
                                            html.Div([
                                                html.Small("Mínima do Período", className="text-muted", style={"fontSize": "0.75rem"}),
                                                html.Div([
                                                    html.I(className="bi bi-arrow-down-circle-fill text-danger me-2"),
                                                    html.Span(f"{df['ri_geral'].min()*100:.2f}%", className="fw-bold text-dark")
                                                ], className="d-flex align-items-center mt-1"),
                                                html.Small(df.loc[df['ri_geral'].idxmin()]['x_label'], className="text-muted", style={"fontSize": "0.7rem"})
                                            ], className="p-2 rounded bg-light border h-100")
                                        ], width=4),
                                        dbc.Col([
                                            html.Div([
                                                html.Small("Média Global", className="text-muted", style={"fontSize": "0.75rem"}),
                                                html.Div([
                                                    html.I(className="bi bi-bar-chart-fill text-primary me-2"),
                                                    html.Span(f"{df['ri_geral'].mean()*100:.2f}%", className="fw-bold text-dark")
                                                ], className="d-flex align-items-center mt-1"),
                                                html.Small("Consolidado", className="text-muted", style={"fontSize": "0.7rem"})
                                            ], className="p-2 rounded bg-light border h-100")
                                        ], width=4),
                                    ], className="g-2 mt-3")
                                ])
                            ], className="p-4") 
                        ], className="shadow-sm border-0 rounded-4")
                    ], width=12),
                ], className="mb-4"),

                # Row 2: Comparative Chart (Full Width or Split if needed in future)
                dbc.Row([
                    dbc.Col([
                         html.H3("Comparativo Preventiva vs Corretiva", style={**section_title_style, "borderLeft": "4px solid #64748b"}),
                         dbc.Card([
                            dbc.CardBody(
                                dcc.Graph(figure=fig_comp, config={'displayModeBar': False}, style={"height": "300px"}),
                                className="p-4"
                            )
                         ], className="shadow-sm border-0 rounded-4")
                    ], width=12)
                ], className="mb-5")
            ]),

            # 3. SEÇÃO DE FUGAS (Full Width)
            html.Div([
                html.H3("Fugas de Preventiva", style=section_title_style),
                render_preventiva_section()
            ], className="dashboard-section mb-4"),
            
        ], className="animate__animated animate__fadeIn", style={"padding": "24px", "background": "#F8FAFC", "minHeight": "100vh"})
