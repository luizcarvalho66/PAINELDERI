from dash import Input, Output, State, html, dcc, ctx, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import traceback
from backend.repositories import get_ri_evolution_data, check_database_status
from frontend.components.filters.filter_bar import render_filter_bar

from frontend.components.kpi_card import render_kpi_card
from frontend.components.dashboard_charts import create_ri_geral_chart, create_comparative_chart
from frontend.components.error_display import render_error_display

def _fmt_br(value, decimals=0):
    """Formata número no padrão brasileiro: 1.082.022 ou 223,0"""
    try:
        v_float = float(value)
    except (ValueError, TypeError):
        return value
        
    if decimals > 0:
        formatted = f"{v_float:,.{decimals}f}"
    else:
        formatted = f"{v_float:,.0f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

def register_dashboard_callbacks(app):
    # Callback 1: Toggle Visibility of Onboarding, Charts and Filters
    @app.callback(
        [Output("onboarding-container", "children"),
         Output("dashboard-charts-container", "style"),
         Output("dashboard-kpis-container", "style"),
         Output("filter-bar-container", "style"),
         Output("granularity-header", "style")],
        Input("processing-complete-store", "data"),
        prevent_initial_call=True
    )
    def toggle_dashboard_sections(is_processed):
        if not is_processed:
            # Show onboarding, hide charts and filters
            charts_style = {"display": "none"}
            kpis_style = {"display": "none"}
            filters_style = {"display": "none"}
            granularity_style = {"display": "none"}
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
            return onboarding_content, charts_style, kpis_style, filters_style, granularity_style
        else:
            # Show charts and filters, hide onboarding
            return None, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}

    @app.callback(
        [
            Output("dashboard-kpis-container", "children"),
            Output("dashboard-charts-container", "children"),
        ],
        [
            Input("processing-complete-store", "data"),
            Input("global-filters-applied-store", "data"),
            Input("chart-granularity-store", "data"),
            Input("ri-mode-store", "data"),
        ],
        prevent_initial_call=True
    )
    def update_dashboard_charts(is_processed, filters_state, granularidade, ri_mode):
        if not is_processed:
            return html.Div(), html.Div()
        
        # Evitar re-render quando filtros são populados inicialmente (None → None)
        triggered_id = ctx.triggered_id
        if triggered_id == 'global-filters-applied-store' and not filters_state:
            return no_update, no_update
        
        # Safety net: verificar se banco tem dados antes de processar
        # Após reset, tabelas existem mas estão vazias → evita crash
        try:
            has_data = check_database_status()  # retorna bool
            if not has_data:
                empty_msg = html.Div([
                    html.I(className="bi bi-database-slash text-muted mb-3", style={"fontSize": "2.5rem"}),
                    html.H4("Base de dados vazia", className="text-center text-muted"),
                    html.P("Sincronize os dados para visualizar o dashboard.", 
                           className="text-center text-secondary small"),
                ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
                return html.Div(), empty_msg
        except Exception:
            pass  # Se check falhar, tenta renderizar normalmente
        
        try:
            return _build_dashboard_content(is_processed, filters_state, granularidade or 'mensal', ri_mode or 'ri')
        except Exception as e:
            traceback.print_exc()
            error_div = html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-warning mb-3", style={"fontSize": "2rem"}),
                html.H4("Erro ao carregar o dashboard", className="text-center text-muted"),
                html.P("Algo deu errado ao processar os dados. Tente recarregar a página.", className="text-center text-secondary small"),
                html.P("Tente recarregar a página.", className="text-center text-muted mt-2")
            ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
            return html.Div(), error_div
    
    def _build_dashboard_content(is_processed, filters_state, granularidade='mensal', ri_mode='ri'):
        """Lógica interna do dashboard, separada para facilitar try/except."""
        import time as _time
        _t0 = _time.time()
        
        # Extract filters from state
        filters = None
        if filters_state and filters_state.get("applied"):
            filters = filters_state
        else:
            filters = None
        
        # Injetar granularidade nos filters
        if filters is None:
            filters = {'granularidade': granularidade}
        else:
            filters['granularidade'] = granularidade
        
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
            
        # x_label já gerado no repositório baseado na granularidade
        
        # --- CALCULATE METRICS FOR KPIs ---
        # 1. Total Analisado — usa contagem UNION para evitar dupla contagem
        # OS pode ter itens em AMBAS tabelas (corretiva + preventiva)
        if 'total_os_distinct' in df.columns and df['total_os_distinct'].sum() > 0:
            total_analisado = int(df['total_os_distinct'].sum())
        else:
            # Fallback: soma separada (pode contar OS duplicadas)
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
        
        # SO Metrics — TAXA GLOBAL (sum SO / sum OS), alinhado com TGM bignumbers
        # FIX 2026-03-23: Migrado de .mean() (média de médias mensais) para taxa global
        _so_corr_sum = df['so_count_corr'].sum() if 'so_count_corr' in df.columns else 0
        _so_prev_sum = df['so_count_prev'].sum() if 'so_count_prev' in df.columns else 0
        _tot_corr = df['total_corr'].sum() if 'total_corr' in df.columns else 0
        _tot_prev = df['total_prev'].sum() if 'total_prev' in df.columns else 0
        avg_so_geral = ((_so_corr_sum + _so_prev_sum) / (_tot_corr + _tot_prev) * 100) if (_tot_corr + _tot_prev) > 0 else 0
        avg_so_prev = (_so_prev_sum / _tot_prev * 100) if _tot_prev > 0 else 0
        avg_so_corr = (_so_corr_sum / _tot_corr * 100) if _tot_corr > 0 else 0
        
        # Selecionar métricas conforme modo
        is_so_mode = (ri_mode == 'so')
        display_geral = avg_so_geral if is_so_mode else ri_geral_avg
        display_prev = avg_so_prev if is_so_mode else avg_ri_prev
        display_corr = avg_so_corr if is_so_mode else avg_ri_corr
        mode_label = "SO" if is_so_mode else "RI"
        
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
        # Se modo SO, trocar as colunas que os charts usam
        if is_so_mode:
            df_chart = df.copy()
            df_chart['ri_geral'] = df_chart.get('so_geral', 0)
            df_chart['ri_corretiva'] = df_chart.get('so_corretiva', 0)
            df_chart['ri_preventiva'] = df_chart.get('so_preventiva', 0)
        else:
            df_chart = df
        
        fig_geral = create_ri_geral_chart(df_chart, granularidade=granularidade, is_so_mode=is_so_mode)
        fig_comp = create_comparative_chart(df_chart, granularidade=granularidade, is_so_mode=is_so_mode)
        
        # Atualizar títulos conforme modo
        if is_so_mode:
            fig_geral.update_layout(title=dict(text="<b>Evolução Silent Order</b> vs. Vol. Solicitado"))
            fig_comp.update_layout(title=dict(text="<b>SO Corretiva vs Preventiva</b>"))
            # Trocar label do eixo Y
            fig_geral.update_yaxes(title=dict(text="SO (%)"), secondary_y=False)
            fig_comp.update_yaxes(title=dict(text="SO (%)"))

        section_title_style = {
            "fontFamily": "Ubuntu", 
            "color": "#1e293b", 
            "fontWeight": "600", 
            "borderLeft": "4px solid #E20613", 
            "paddingLeft": "12px", 
            "marginBottom": "20px"
        }

        # --- Construir RETORNO separado: (KPIs, Charts) ---
        
        # KPIs ribbon
        kpis_section = html.Div([
            dbc.Row([
                # Group 1: Volumetria & Financeiro
                dbc.Col(render_kpi_card(
                    "Análise Total", 
                    _fmt_br(total_analisado), 
                    "Ordens processadas", 
                    "bi-layers", 
                    "text-primary"
                ), width=12, sm=6, md=6, lg=4, xl=2),
                
                dbc.Col(render_kpi_card(
                    "Economia Real", 
                    f"R$ {_fmt_br(economia_real/1000000, 1)}M", 
                    "Valor economizado", 
                    "bi-cash-stack", 
                    "text-success"
                ), width=12, sm=6, md=6, lg=4, xl=2),
                
                dbc.Col(render_kpi_card(
                    "Share Preventiva", 
                    f"{_fmt_br(ratio_prev_corr, 1)}%", 
                    "Mix de manutenções", 
                    "bi-pie-chart-fill", 
                    "text-info"
                ), width=12, sm=6, md=6, lg=4, xl=2),

                # Group 2: Performance (RI) com Tendências
                dbc.Col(render_kpi_card(
                    f"{mode_label} Geral", 
                    f"{_fmt_br(display_geral, 1)}%", 
                    "Média do período", 
                    "bi-graph-up-arrow" if not is_so_mode else "bi-shield-check", 
                    "text-danger",
                    trend_value=trend_ri_geral,
                    trend_label="vs mês anterior"
                ), width=12, sm=6, md=6, lg=4, xl=2),

                dbc.Col(render_kpi_card(
                    f"{mode_label} Preventiva", 
                    f"{_fmt_br(display_prev, 1)}%", 
                    "Manutenção programada", 
                    "bi-shield-check", 
                    "text-success",
                    trend_value=trend_ri_prev,
                    trend_label="vs mês anterior"
                ), width=12, sm=6, md=6, lg=4, xl=2),
                
                dbc.Col(render_kpi_card(
                    f"{mode_label} Corretiva", 
                    f"{_fmt_br(display_corr, 1)}%", 
                    "Manutenção sob demanda", 
                    "bi-tools", 
                    "text-danger",
                    trend_value=trend_ri_corr,
                    trend_label="vs mês anterior"
                ), width=12, sm=6, md=6, lg=4, xl=2),
                
            ], className="g-3 mb-4 ps-2")
        ], className="dashboard-top-kpis animate__animated animate__fadeIn")
        
        # Charts section
        charts_section = html.Div([
            # Chart 1: Evolução RI Geral (com botão de ajuda [?])
            html.Div([
                # Botão [?] — posicionado no canto superior direito do chart
                html.Button(
                    html.I(className="bi bi-question-circle"),
                    id="btn-help-ri-chart",
                    className="btn btn-sm",
                    style={
                        "position": "absolute",
                        "top": "8px",
                        "right": "12px",
                        "zIndex": "10",
                        "background": "transparent",
                        "border": "1px solid #e2e8f0",
                        "borderRadius": "50%",
                        "width": "28px",
                        "height": "28px",
                        "padding": "0",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "color": "#94a3b8",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                    },
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader(
                            html.Span([
                                html.I(className="bi bi-info-circle-fill me-2", style={"color": "#E20613"}),
                                "Sobre os Indicadores"
                            ]),
                            style={"fontFamily": "Ubuntu", "fontWeight": "600", "fontSize": "14px"}
                        ),
                        dbc.PopoverBody([
                            html.P([
                                html.Strong("RI Geral"), " é um ", html.Strong("percentual"), 
                                " — a proporção de economia sobre o total solicitado."
                            ], style={"fontSize": "13px", "marginBottom": "8px"}),
                            html.Div([
                                html.Span("📊 ", style={"fontSize": "14px"}),
                                html.Span("Exemplo: ", style={"fontWeight": "600", "fontSize": "12px"}),
                            ]),
                            html.P(
                                "Se em 5 dias o workshop cobrou R$ 100 e economizamos R$ 35, "
                                "o RI = 35%. Em 30 dias, cobraria R$ 600 e economizaríamos R$ 210 — "
                                "ainda 35%. O percentual não muda com mais dias.",
                                style={"fontSize": "12px", "color": "#64748b", "marginBottom": "10px",
                                       "borderLeft": "3px solid #E20613", "paddingLeft": "8px",
                                       "backgroundColor": "rgba(226,6,19,0.03)", "padding": "8px",
                                       "borderRadius": "4px"}
                            ),
                            html.P([
                                html.I(className="bi bi-exclamation-triangle-fill me-1", style={"color": "#f59e0b", "fontSize": "11px"}),
                                html.Span(
                                    "Meses marcados como (parcial) têm menos dados. "
                                    "O volume (R$, OS) será menor, mas o % de RI permanece representativo.",
                                    style={"fontSize": "12px", "color": "#64748b"}
                                ),
                            ], style={"marginBottom": "0"}),
                        ], style={"fontFamily": "Ubuntu, sans-serif"})
                    ],
                    target="btn-help-ri-chart",
                    trigger="click",
                    placement="left",
                    style={"maxWidth": "340px"},
                ),
                dcc.Graph(
                    id="fig-ri-geral",
                    figure=fig_geral, 
                    config={'displayModeBar': False},
                    style={"height": "400px"},
                    clear_on_unhover=True
                ),
            ], style={"position": "relative"}),
            
            # Chart 2: Comparativo Preventiva vs Corretiva
            html.Div([
                html.H3("Comparativo Preventiva vs Corretiva", style={**section_title_style, "borderLeft": "4px solid #64748b"}),
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            id="fig-comp-ri", 
                            figure=fig_comp, 
                            config={'displayModeBar': False}, 
                            style={"height": "300px"},
                            clear_on_unhover=True
                        ),
                    ], className="p-4")
                ], className="shadow-sm border-0 rounded-4")
            ], className="mt-4 mb-5")
        ])
        
        return kpis_section, charts_section

    # Callback: Toggle de Granularidade (premium-toggle → store + visual)
    @app.callback(
        [
            Output("chart-granularity-store", "data"),
            Output("btn-gran-mensal", "className"),
            Output("btn-gran-quinzenal", "className"),
            Output("btn-gran-semanal", "className"),
        ],
        [
            Input("btn-gran-mensal", "n_clicks"),
            Input("btn-gran-quinzenal", "n_clicks"),
            Input("btn-gran-semanal", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def update_granularity(n_mensal, n_quinzenal, n_semanal):
        triggered = ctx.triggered_id
        if triggered == "btn-gran-quinzenal":
            return "quinzenal", "premium-toggle-btn", "premium-toggle-btn active", "premium-toggle-btn"
        elif triggered == "btn-gran-semanal":
            return "semanal", "premium-toggle-btn", "premium-toggle-btn", "premium-toggle-btn active"
        return "mensal", "premium-toggle-btn active", "premium-toggle-btn", "premium-toggle-btn"

    # Callback: Toggle de Modo RI ↔ Silent Order
    @app.callback(
        [
            Output("ri-mode-store", "data"),
            Output("btn-mode-ri", "className"),
            Output("btn-mode-so", "className"),
        ],
        [
            Input("btn-mode-ri", "n_clicks"),
            Input("btn-mode-so", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_ri_mode(n_ri, n_so):
        triggered = ctx.triggered_id
        if triggered == "btn-mode-so":
            return "so", "premium-toggle-btn", "premium-toggle-btn active"
        return "ri", "premium-toggle-btn active", "premium-toggle-btn"
