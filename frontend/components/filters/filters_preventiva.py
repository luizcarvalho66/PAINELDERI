"""
Filtros Específicos para RI Preventiva
Baseado em logs_regulacao_preventiva_header
"""
from dash import html
import dash_bootstrap_components as dbc

from .filters_common import (
    create_filter_dropdown,
    create_filter_range_slider,
    create_filter_input,
    create_filter_card
)


def render_filters_preventiva():
    """
    Renderiza o card de filtros para o painel de RI Preventiva.
    
    Filtros disponíveis:
    - Nome do cliente (dropdown multi-select) - via join se necessário
    - Código do cliente (input text)
    - Mês (dropdown multi-select)
    - Faixa de valor limite (range slider)
    - Plano de Manutenção (dropdown)
    """
    
    filter_components = [
        # Linha 1: Cliente e Código
        html.Div([
            create_filter_dropdown(
                filter_id="filter-prev-cliente",
                label="Cliente",
                placeholder="Todos os clientes",
                multi=True
            ),
            create_filter_input(
                filter_id="filter-prev-cod-cliente",
                label="Cód. Cliente",
                input_type="text",
                placeholder="Ex: 1234"
            ),
        ], className="filter-row"),
        
        # Linha 2: Mês e Plano
        html.Div([
            create_filter_dropdown(
                filter_id="filter-prev-mes",
                label="Mês",
                placeholder="Todos os meses",
                multi=True
            ),
            create_filter_dropdown(
                filter_id="filter-prev-plano",
                label="Plano de Manutenção",
                placeholder="Todos os planos",
                multi=True
            ),
        ], className="filter-row"),
        
        # Linha 3: Faixa de Valor
        html.Div([
            create_filter_range_slider(
                filter_id="filter-prev-valor",
                label="Faixa de Valor Limite (R$)",
                min_val=0,
                max_val=50000,
                marks={
                    0: {'label': 'R$ 0'},
                    10000: {'label': '10k'},
                    25000: {'label': '25k'},
                    50000: {'label': '50k+'}
                }
            ),
        ], className="filter-row filter-row--full"),
    ]
    
    return create_filter_card(
        panel_id="preventiva",
        title="Filtros — RI Preventiva",
        icon_class="bi bi-calendar-check",
        children=filter_components
    )
