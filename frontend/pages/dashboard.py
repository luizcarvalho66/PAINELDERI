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
                
                # Container for Charts (RI Geral + Comparativo APENAS)
                html.Div(id="dashboard-charts-container")
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
