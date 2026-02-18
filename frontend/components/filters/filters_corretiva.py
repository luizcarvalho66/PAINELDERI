"""
Filtros Específicos para RI Corretiva
Baseado em ri_corretiva_detalhamento
"""
from dash import html
import dash_bootstrap_components as dbc

from .filters_common import (
    create_filter_dropdown,
    create_filter_range_slider,
    create_filter_input,
    create_filter_card
)


def render_filters_corretiva():
    """
    Renderiza o card de filtros para o painel de RI Corretiva.
    
    Filtros disponíveis:
    - Nome do cliente (dropdown multi-select)
    - Código do cliente (input text)
    - Mês (dropdown multi-select)
    - Faixa de valor OS (range slider)
    - Quantidade de itens (input number)
    - Peça (dropdown searchable multi-select)
    - Mão de obra / tipo_mo (dropdown)
    """
    
    filter_components = [
        # Linha 1: Cliente e Código
        html.Div([
            create_filter_dropdown(
                filter_id="filter-corr-cliente",
                label="Cliente",
                placeholder="Todos os clientes",
                multi=True
            ),
            create_filter_input(
                filter_id="filter-corr-cod-cliente",
                label="Cód. Cliente",
                input_type="text",
                placeholder="Ex: 1234"
            ),
        ], className="filter-row"),
        
        # Linha 2: Mês e Valor
        html.Div([
            create_filter_dropdown(
                filter_id="filter-corr-mes",
                label="Mês",
                placeholder="Todos os meses",
                multi=True
            ),
            create_filter_range_slider(
                filter_id="filter-corr-valor",
                label="Faixa de Valor OS (R$)",
                min_val=0,
                max_val=50000
            ),
        ], className="filter-row"),
        
        # Linha 3: Peça e Tipo MO
        html.Div([
            create_filter_dropdown(
                filter_id="filter-corr-peca",
                label="Peça",
                placeholder="Buscar peça...",
                multi=True,
                searchable=True
            ),
            create_filter_dropdown(
                filter_id="filter-corr-tipo-mo",
                label="Mão de Obra",
                placeholder="Todos os tipos",
                multi=True
            ),
        ], className="filter-row"),
        
        # Linha 4: Quantidade de itens
        html.Div([
            create_filter_input(
                filter_id="filter-corr-qtd-itens",
                label="Qtd. Mínima de Itens",
                input_type="number",
                placeholder="Ex: 5",
                min_val=0
            ),
        ], className="filter-row filter-row--single"),
    ]
    
    return create_filter_card(
        panel_id="corretiva",
        title="Filtros — RI Corretiva",
        icon_class="bi bi-wrench-adjustable",
        children=filter_components
    )
