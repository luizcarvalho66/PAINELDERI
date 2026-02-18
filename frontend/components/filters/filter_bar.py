"""
Barra de Filtros Unificada - RI Dashboard
Design limpo e intuitivo com filtros que REALMENTE funcionam
"""
from dash import html, dcc
import dash_bootstrap_components as dbc


def render_filter_bar():
    """
    Renderiza uma barra de filtros horizontal unificada.
    Todos os filtros afetam TODOS os gráficos do dashboard.
    
    Layout: [Período] [Cliente] [Tipo Manutenção] [Aplicar] [Limpar] [Exportar]
    """
    return html.Div([
        # Container principal
        html.Div([
            # Título da barra
            html.Div([
                html.I(className="bi bi-sliders me-2"),
                html.Span("Filtros", className="filter-bar-title")
            ], className="filter-bar-label"),
            
            # Grid de filtros
            html.Div([
                # 1. Período (Mês)
                html.Div([
                    html.Label("Período", className="filter-inline-label"),
                    dcc.Dropdown(
                        id="global-filter-periodo",
                        placeholder="Todos os meses",
                        multi=True,
                        className="filter-inline-dropdown"
                    )
                ], className="filter-inline-group"),
                
                # 2. Cliente
                html.Div([
                    html.Label("Cliente", className="filter-inline-label"),
                    dcc.Dropdown(
                        id="global-filter-cliente",
                        placeholder="Todos",
                        multi=True,
                        searchable=True,
                        className="filter-inline-dropdown"
                    )
                ], className="filter-inline-group"),
                
                # 3. Tipo de Manutenção (Toggle visual)
                html.Div([
                    html.Label("Tipo", className="filter-inline-label"),
                    dbc.ButtonGroup([
                        dbc.Button("Todas", id="filter-tipo-todas", color="danger", outline=False, size="sm", className="active"),
                        dbc.Button("Corretiva", id="filter-tipo-corretiva", color="secondary", outline=True, size="sm"),
                        dbc.Button("Preventiva", id="filter-tipo-preventiva", color="secondary", outline=True, size="sm"),
                    ], className="filter-toggle-group")
                ], className="filter-inline-group filter-inline-group--toggle"),
                
            ], className="filter-bar-fields"),
            
            # Ações
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-check2-circle me-2"),
                    "Aplicar Filtros"
                ], id="btn-apply-global-filters", color="danger", className="rounded-pill px-4 fw-bold shadow-sm me-2"),
                
                dbc.Button([
                    html.I(className="bi bi-eraser-fill")
                ], id="btn-clear-global-filters", color="light", outline=False, className="rounded-circle shadow-sm me-2 text-muted", style={"width": "38px", "height": "38px", "padding": "0"}),
                
                dbc.Button([
                    html.I(className="bi bi-file-earmark-excel-fill me-2"),
                    "Exportar"
                ], id="btn-export-global", color="success", outline=True, className="rounded-pill px-3 shadow-none border-0"),
            ], className="filter-bar-actions"),
            
        ], className="filter-bar-inner"),
        
        # Indicador de filtros ativos
        html.Div(id="active-filters-indicator", className="active-filters-indicator"),
        
        # Store para tipo de manutenção selecionado
        dcc.Store(id="filter-tipo-store", data="TODAS"),
        
        # Download component
        dcc.Download(id="download-filtered-data"),
        
    ], className="filter-bar", id="global-filter-bar")
