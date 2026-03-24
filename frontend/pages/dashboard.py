from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from backend.repositories import get_ri_evolution_data
from frontend.components.filters.filter_bar import render_filter_bar
from frontend.components.preventiva_section import render_preventiva_section


def render_dashboard():
    """
    Renders the Dashboard container.
    Content is populated by callback based on processing state.
    """
    return html.Div([
        # Dashboard Header with Import Button - Always visible
        html.Div([
            html.H1("Painel de Regulação Inteligente", className="executive-title", style={"fontWeight": "700"}),
        ], className="dashboard-header mb-4"),
        
        # ========== BARRA DE FILTROS - SEMPRE VISÍVEL ==========
        # Precisa estar aqui para que os IDs existam antes dos callbacks
        html.Div([
            render_filter_bar()
        ], id="filter-bar-container", style={"display": "none"}),
        
        # Main Content Area — Loading overlay profissional
        # Wrapper APENAS para os gráficos principais (RI Geral, Comparativo)
        dcc.Loading(
            id="dashboard-loading",
            type="circle",
            color="#E20613",
            fullscreen=False,
            style={"position": "relative"},
            parent_style={"position": "relative", "minHeight": "60vh"},
            overlay_style={
                "visibility": "visible",
                "opacity": 0.3,
                "backgroundColor": "rgba(248,250,252,0.4)",
                "filter": "none",
            },
            children=[
                # Container for Onboarding (Steps)
                html.Div(id="onboarding-container"),
                
                # ========== KPIs — container próprio, ACIMA do card de Visão Geral ==========
                html.Div(id="dashboard-kpis-container"),
                
                # ========== Card Visão Geral (Header + Charts) — ABAIXO dos KPIs ==========
                dbc.Card([
                    # Cabeçalho do Card (Estático): Título + Toggle de Granularidade
                    dbc.CardHeader([
                        html.Div([
                            html.Div([
                                html.H3("Visão Geral", className="mb-0", style={
                                    "fontFamily": "Ubuntu", "color": "#1e293b", "fontWeight": "600",
                                    "borderLeft": "4px solid #E20613", "paddingLeft": "12px"
                                }),
                                # Toggle de Modo: RI SO (ativo) ↔ Análise Financeira (em breve)
                                html.Div([
                                    html.Div([
                                        html.I(className="bi bi-clipboard2-check"),
                                        html.Span("RI SO")
                                    ], id="btn-mode-so", className="premium-toggle-btn active", n_clicks=0),
                                    html.Div([
                                        html.I(className="bi bi-currency-dollar"),
                                        html.Span("Análise Financeira"),
                                        html.Span("Em breve", className="badge-coming-soon ms-2"),
                                    ], id="btn-mode-ri", className="premium-toggle-btn disabled", n_clicks=0,
                                       style={"opacity": "0.5", "pointerEvents": "none"}),
                                ], className="premium-toggle-container ms-3"),
                            ], className="d-flex align-items-center"),
                            # Toggle de Granularidade (premium-toggle estático)
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-calendar-month"),
                                    html.Span("Mensal")
                                ], id="btn-gran-mensal", className="premium-toggle-btn active", n_clicks=0),
                                html.Div([
                                    html.I(className="bi bi-calendar-week"),
                                    html.Span("Quinzenal")
                                ], id="btn-gran-quinzenal", className="premium-toggle-btn", n_clicks=0),
                                html.Div([
                                    html.I(className="bi bi-calendar-day"),
                                    html.Span("Semanal")
                                ], id="btn-gran-semanal", className="premium-toggle-btn", n_clicks=0),
                            ], className="premium-toggle-container")
                        ], className="d-flex justify-content-between align-items-center"),
                        # Store para persistir modo RI/SO
                        dcc.Store(id="ri-mode-store", data="so"),
                    ], id="granularity-header", className="bg-transparent border-0 pt-4 px-4 pb-0", style={"display": "none"}),
                    
                    # Corpo do Card (Dinâmico - Charts injetados aqui)
                    dbc.CardBody([
                        html.Div(id="dashboard-charts-container")
                    ], className="p-4")
                ], className="shadow-sm border-0 rounded-4 mb-4"),
            ]
        ),
        
        # ========== SEÇÃO PREVENTIVA — FORA do dcc.Loading ==========
        # Container separado para que o loading da preventiva não bloqueie
        # os gráficos principais. Tem seu próprio dcc.Loading.
        dcc.Loading(
            id="preventiva-loading",
            type="circle",
            color="#94a3b8",
            fullscreen=False,
            overlay_style={
                "visibility": "visible",
                "opacity": 0.2,
                "backgroundColor": "rgba(248,250,252,0.3)",
                "filter": "none",
            },
            children=[
                html.Div(
                    render_preventiva_section(initial_data=None),
                    id="preventiva-section-container",
                    className="dashboard-section mb-4"
                )
            ]
        ),
        
    ], className="p-2")
