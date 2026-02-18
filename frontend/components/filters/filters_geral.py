"""
Filtros para Visão Geral (RI Geral)
Toggle entre Corretiva/Preventiva + filtros consolidados
"""
from dash import html, dcc
import dash_bootstrap_components as dbc

from .filters_common import (
    create_filter_dropdown,
    create_filter_card
)


def render_filters_geral():
    """
    Renderiza o card de filtros para o painel de RI Geral.
    
    Filtros disponíveis:
    - Toggle Corretiva/Preventiva (segmented control)
    - Período / Mês
    - Cliente
    """
    
    filter_components = [
        # Linha 1: Toggle de Tipo de Manutenção
        html.Div([
            html.Div([
                html.Label("Tipo de Manutenção", className="filter-label"),
                dbc.RadioItems(
                    id="filter-geral-tipo",
                    options=[
                        {"label": "Ambos", "value": "AMBOS"},
                        {"label": "Corretiva", "value": "CORRETIVA"},
                        {"label": "Preventiva", "value": "PREVENTIVA"},
                    ],
                    value="AMBOS",
                    inline=True,
                    className="filter-radio-group"
                )
            ], className="filter-field filter-field--radio"),
        ], className="filter-row filter-row--center"),
        
        # Linha 2: Período e Cliente
        html.Div([
            create_filter_dropdown(
                filter_id="filter-geral-mes",
                label="Período",
                placeholder="Todos os meses",
                multi=True
            ),
            create_filter_dropdown(
                filter_id="filter-geral-cliente",
                label="Cliente",
                placeholder="Todos os clientes",
                multi=True
            ),
        ], className="filter-row"),
    ]
    
    return create_filter_card(
        panel_id="geral",
        title="Filtros — Visão Geral",
        icon_class="bi bi-speedometer2",
        children=filter_components
    )
