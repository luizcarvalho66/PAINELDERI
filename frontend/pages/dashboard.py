from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from backend.repositories import get_ri_evolution_data
from frontend.components.filters.filter_bar import render_filter_bar

import datetime

def render_dashboard():
    print(f"[DEBUG][{datetime.datetime.now()}] DASHBOARD PAGE: render_dashboard() called")
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
        
        # Main Content Area
        dcc.Loading(
            id="dashboard-loading",
            type="default",
            color="#E20613",
            children=[
                # Container for Onboarding (Steps)
                html.Div(id="onboarding-container"),
                
                # Container for Charts
                html.Div(id="dashboard-charts-container")
            ]
        )
    ], className="p-2")


