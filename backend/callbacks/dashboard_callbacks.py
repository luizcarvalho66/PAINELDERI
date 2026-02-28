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
        ],
        prevent_initial_call=True
    )
    def update_dashboard_charts(is_processed, filters_state, granularidade):
        if not is_processed:
            return html.Div(), html.Div()
        
        # Evitar re-render quando filtros são populados inicialmente (None → None)
        triggered_id = ctx.triggered_id
        if triggered_id == 'global-filters-applied-store' and not filters_state:
            return no_update, no_update
        
        try:
            return _build_dashboard_content(is_processed, filters_state, granularidade or 'mensal')
        except Exception as e:
            traceback.print_exc()
            error_div = html.Div([
                html.I(className="bi bi-exclamation-triangle-fill text-warning mb-3", style={"fontSize": "2rem"}),
                html.H4("Erro ao carregar o dashboard", className="text-center text-muted"),
                html.P(f"Detalhes: {str(e)[:200]}", className="text-center text-secondary small"),
                html.P("Tente recarregar a página.", className="text-center text-muted mt-2")
            ], className="p-5 d-flex flex-column align-items-center justify-content-center h-100")
            return html.Div(), error_div
    
    def _build_dashboard_content(is_processed, filters_state, granularidade='mensal'):
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
        fig_geral = create_ri_geral_chart(df, granularidade=granularidade)
        fig_comp = create_comparative_chart(df, granularidade=granularidade)

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
                    "RI Geral", 
                    f"{_fmt_br(ri_geral_avg, 1)}%", 
                    "Média do período", 
                    "bi-graph-up-arrow", 
                    "text-danger",
                    trend_value=trend_ri_geral,
                    trend_label="vs mês anterior"
                ), width=12, sm=6, md=6, lg=4, xl=2),

                dbc.Col(render_kpi_card(
                    "RI Preventiva", 
                    f"{_fmt_br(avg_ri_prev, 1)}%", 
                    "Manutenção programada", 
                    "bi-shield-check", 
                    "text-success",
                    trend_value=trend_ri_prev,
                    trend_label="vs mês anterior"
                ), width=12, sm=6, md=6, lg=4, xl=2),
                
                dbc.Col(render_kpi_card(
                    "RI Corretiva", 
                    f"{_fmt_br(avg_ri_corr, 1)}%", 
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
            # Chart 1: Evolução RI Geral
            dcc.Graph(
                id="fig-ri-geral",
                figure=fig_geral, 
                config={'displayModeBar': False},
                style={"height": "400px"},
                clear_on_unhover=True
            ),
            dcc.Tooltip(
                id="tooltip-ri-geral",
                direction="top",
                style={
                    "backgroundColor": "#ffffff", 
                    "color": "#1e293b", 
                    "borderRadius": "12px", 
                    "border": "1px solid #e2e8f0", 
                    "boxShadow": "0 8px 30px rgba(0,0,0,0.12)",
                    "padding": "0",
                    "fontFamily": "Ubuntu, sans-serif",
                    "zIndex": "9999",
                    "overflow": "visible"
                }
            ),
            
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
                        dcc.Tooltip(
                            id="tooltip-comp-ri",
                            direction="top",
                            style={
                                "backgroundColor": "#ffffff", 
                                "color": "#1e293b", 
                                "borderRadius": "12px", 
                                "border": "1px solid #e2e8f0", 
                                "boxShadow": "0 8px 30px rgba(0,0,0,0.12)",
                                "padding": "0",
                                "fontFamily": "Ubuntu, sans-serif",
                                "zIndex": "9999",
                                "overflow": "visible"
                            }
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

    # =========================================================================
    # TOOLTIP CALLBACKS - 100% CLIENT-SIDE (JavaScript puro, sem round-trip)
    # =========================================================================
    app.clientside_callback(
        """
        function(hoverData) {
            if (!hoverData) return [false, window.dash_clientside.no_update, window.dash_clientside.no_update];
            
            var pt = hoverData.points[0];
            var bbox = pt.bbox;
            var c = pt.customdata;
            if (!c || c.length < 10) return [false, window.dash_clientside.no_update, window.dash_clientside.no_update];
            
            var riGeral = parseFloat(c[9]).toFixed(2);
            var riCorr = parseFloat(c[5]).toFixed(2);
            var riPrev = parseFloat(c[6]).toFixed(2);
            var parcial = c[7] || '';
            var osTotal = Number(c[2]).toLocaleString('pt-BR');
            
            var html = '<div style="width:240px;font-family:Ubuntu,sans-serif">'
                + '<div style="padding:10px 14px;border-bottom:2px solid #E20613;background:linear-gradient(135deg,#fef2f2,#fff);">'
                + '<i class="bi bi-calendar3" style="color:#E20613;margin-right:6px"></i>'
                + '<b style="color:#1e293b;font-size:13px">' + c[0] + '</b>'
                + (parcial ? '<span style="color:#94a3b8;font-size:10px;margin-left:5px">' + parcial + '</span>' : '')
                + '</div>'
                + '<div style="padding:12px 14px">'
                + '<div style="margin-bottom:10px">'
                + '<div style="display:flex;align-items:center;margin-bottom:4px">'
                + '<i class="bi bi-graph-up-arrow" style="color:#E20613;font-size:12px;margin-right:6px"></i>'
                + '<span style="color:#64748b;font-size:11px">RI Geral</span></div>'
                + '<span style="color:#1e293b;font-size:20px;font-weight:700">' + riGeral + '%</span>'
                + '<div style="margin-top:4px;margin-left:2px;border-left:2px solid #e2e8f0;padding-left:8px">'
                + '<div style="display:flex;justify-content:space-between;margin-bottom:2px">'
                + '<span style="color:#64748b;font-size:11px">Corretiva</span>'
                + '<span style="color:#1e293b;font-size:11px;font-weight:600">' + riCorr + '%</span></div>'
                + '<div style="display:flex;justify-content:space-between">'
                + '<span style="color:#64748b;font-size:11px">Preventiva</span>'
                + '<span style="color:#1e293b;font-size:11px;font-weight:600">' + riPrev + '%</span></div>'
                + '</div></div>'
                + '<div style="border-top:1px solid #f1f5f9;padding-top:8px;margin-top:4px">'
                + '<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                + '<span style="color:#64748b;font-size:11px"><i class="bi bi-bar-chart-fill" style="margin-right:4px;font-size:10px"></i>Vol. Analisado</span>'
                + '<b style="color:#1e293b;font-size:11px">' + c[8] + '</b></div>'
                + '<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                + '<span style="color:#64748b;font-size:11px"><i class="bi bi-cash-stack" style="margin-right:4px;font-size:10px;color:#16a34a"></i>Economia</span>'
                + '<b style="color:#16a34a;font-size:11px">' + c[1] + '</b></div>'
                + '<div style="display:flex;justify-content:space-between">'
                + '<span style="color:#64748b;font-size:11px"><i class="bi bi-file-earmark-text" style="margin-right:4px;font-size:10px"></i>OS Genu\u00ednas</span>'
                + '<span style="color:#1e293b;font-size:11px;font-weight:500">' + osTotal + '</span></div>'
                + '</div></div></div>';
            
            return [true, bbox, {props: {children: [{props: {dangerouslySetInnerHTML: {__html: html}}, type: 'Div', namespace: 'dash_html_components'}]}, type: 'Div', namespace: 'dash_html_components'}];
        }
        """,
        Output("tooltip-ri-geral", "show"),
        Output("tooltip-ri-geral", "bbox"),
        Output("tooltip-ri-geral", "children"),
        Input("fig-ri-geral", "hoverData"),
        prevent_initial_call=True
    )

    app.clientside_callback(
        """
        function(hoverData) {
            if (!hoverData) return [false, window.dash_clientside.no_update, window.dash_clientside.no_update];
            
            var pt = hoverData.points[0];
            var bbox = pt.bbox;
            var c = pt.customdata;
            if (!c || c.length < 2) return [false, window.dash_clientside.no_update, window.dash_clientside.no_update];
            
            var isCorr = pt.curveNumber === 1;
            var title = isCorr ? 'RI Corretiva' : 'RI Preventiva';
            var color = isCorr ? '#E20613' : '#64748b';
            var icon = isCorr ? 'bi-tools' : 'bi-shield-check';
            var yVal = parseFloat(pt.y).toFixed(2);
            var osVal = Number(c[1]).toLocaleString('pt-BR');
            
            var html = '<div style="width:200px;font-family:Ubuntu,sans-serif">'
                + '<div style="padding:8px 12px;border-bottom:2px solid ' + color + ';background:linear-gradient(135deg,#fafafa,#fff)">'
                + '<i class="bi bi-calendar3" style="color:' + color + ';margin-right:6px;font-size:12px"></i>'
                + '<b style="color:#1e293b;font-size:12px">' + c[0] + '</b></div>'
                + '<div style="padding:10px 12px">'
                + '<div style="display:flex;align-items:center;margin-bottom:3px">'
                + '<i class="bi ' + icon + '" style="color:' + color + ';font-size:11px;margin-right:6px"></i>'
                + '<span style="color:#64748b;font-size:11px">' + title + '</span></div>'
                + '<span style="color:#1e293b;font-size:18px;font-weight:700">' + yVal + '%</span>'
                + '<div style="border-top:1px solid #f1f5f9;margin-top:8px;padding-top:6px;display:flex;justify-content:space-between">'
                + '<span style="color:#64748b;font-size:11px"><i class="bi bi-file-earmark-text" style="margin-right:4px;font-size:10px"></i>OS Analisadas</span>'
                + '<span style="color:#1e293b;font-size:11px;font-weight:600">' + osVal + '</span></div>'
                + '</div></div>';
            
            return [true, bbox, {props: {children: [{props: {dangerouslySetInnerHTML: {__html: html}}, type: 'Div', namespace: 'dash_html_components'}]}, type: 'Div', namespace: 'dash_html_components'}];
        }
        """,
        Output("tooltip-comp-ri", "show"),
        Output("tooltip-comp-ri", "bbox"),
        Output("tooltip-comp-ri", "children"),
        Input("fig-comp-ri", "hoverData"),
        prevent_initial_call=True
    )

