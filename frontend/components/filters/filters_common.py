"""
Componentes Reutilizáveis de Filtro - Edenred RI Dashboard
Estilo Executivo Minimalista com Branding Edenred
"""
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_filter_dropdown(filter_id: str, label: str, placeholder: str = "Selecione...", 
                           multi: bool = False, searchable: bool = True, options: list = None):
    """
    Cria um dropdown estilizado para filtros.
    
    Args:
        filter_id: ID único do componente
        label: Label do filtro
        placeholder: Texto placeholder
        multi: Se permite seleção múltipla
        searchable: Se permite busca
        options: Lista de opções (pode ser populada via callback)
    """
    return html.Div([
        html.Label(label, className="filter-label"),
        dcc.Dropdown(
            id=filter_id,
            placeholder=placeholder,
            multi=multi,
            searchable=searchable,
            options=options or [],
            className="filter-dropdown"
        )
    ], className="filter-field")


def create_filter_range_slider(filter_id: str, label: str, min_val: float = 0, 
                                max_val: float = 50000, step: float = 500,
                                marks: dict = None, value: list = None):
    """
    Cria um range slider para faixas de valor.
    
    Args:
        filter_id: ID único do componente
        label: Label do filtro
        min_val, max_val: Limites do slider
        step: Incremento
        marks: Marcações no slider
        value: Valor inicial [min, max]
    """
    default_marks = marks or {
        0: {'label': 'R$ 0', 'style': {'fontSize': '10px'}},
        10000: {'label': '10k'},
        25000: {'label': '25k'},
        50000: {'label': '50k+'}
    }
    
    return html.Div([
        html.Label(label, className="filter-label"),
        dcc.RangeSlider(
            id=filter_id,
            min=min_val,
            max=max_val,
            step=step,
            marks=default_marks,
            value=value or [min_val, max_val],
            className="filter-range-slider"
        )
    ], className="filter-field filter-field--slider")


def create_filter_input(filter_id: str, label: str, input_type: str = "text", 
                        placeholder: str = "", min_val: int = None):
    """
    Cria um input de texto ou número para filtros.
    
    Args:
        filter_id: ID único do componente
        label: Label do filtro
        input_type: 'text' ou 'number'
        placeholder: Texto placeholder
        min_val: Valor mínimo (para type=number)
    """
    input_props = {
        "id": filter_id,
        "type": input_type,
        "placeholder": placeholder,
        "className": "form-control filter-input"
    }
    
    if input_type == "number" and min_val is not None:
        input_props["min"] = min_val
    
    return html.Div([
        html.Label(label, className="filter-label"),
        dcc.Input(**input_props)
    ], className="filter-field")


def create_export_button(panel_id: str):
    """
    Cria botão de exportação Excel para um painel.
    
    Args:
        panel_id: Identificador do painel (corretiva, preventiva, geral)
    """
    return dbc.Button([
        html.I(className="bi bi-file-earmark-excel me-2"),
        "Exportar"
    ], 
    id=f"btn-export-{panel_id}",
    color="success",
    outline=True,
    size="sm",
    className="filter-export-btn"
    )


def create_filter_card(panel_id: str, title: str, icon_class: str, children: list):
    """
    Cria o card container para um grupo de filtros de painel.
    
    Args:
        panel_id: Identificador do painel
        title: Título do card
        icon_class: Classe do ícone Bootstrap
        children: Componentes de filtro internos
    """
    return html.Div([
        # Header do card de filtros
        html.Div([
            html.Div([
                html.I(className=f"{icon_class} me-2"),
                html.Span(title, className="filter-card-title")
            ], className="filter-card-header-left"),
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-funnel me-1"),
                    "Aplicar"
                ], 
                id=f"btn-apply-{panel_id}",
                color="danger",
                size="sm",
                className="me-2"
                ),
                dbc.Button([
                    html.I(className="bi bi-x-circle")
                ],
                id=f"btn-clear-{panel_id}",
                color="secondary",
                outline=True,
                size="sm",
                className="me-2"
                ),
                create_export_button(panel_id)
            ], className="filter-card-header-right")
        ], className="filter-card-header"),
        
        # Grid de filtros
        html.Div(children, className="filter-card-body")
        
    ], className="filter-card", id=f"filter-card-{panel_id}")
