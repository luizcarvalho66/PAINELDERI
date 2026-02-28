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
                html.Span([
                    html.I(className="bi bi-sliders2")
                ], className="filter-bar-icon"),
                html.Span("Filtros", className="filter-bar-title")
            ], className="filter-bar-label"),
            
            # Grid de filtros
            html.Div([
                # 1. Período (Mês)
                html.Div([
                    html.Label([
                        html.I(className="bi bi-calendar-event me-1 text-muted"),
                        "Período"
                    ], className="filter-inline-label"),
                    dcc.Dropdown(
                        id="global-filter-periodo",
                        placeholder="Todos os meses",
                        multi=True,
                        className="filter-inline-dropdown"
                    )
                ], className="filter-inline-group"),
                
                # 2. Cliente
                html.Div([
                    html.Label([
                        html.I(className="bi bi-building me-1 text-muted"),
                        "Cliente"
                    ], className="filter-inline-label"),
                    dcc.Dropdown(
                        id="global-filter-cliente",
                        placeholder="Todos",
                        multi=True,
                        searchable=True,
                        className="filter-inline-dropdown"
                    )
                ], className="filter-inline-group"),
                
                # 3. Tipo de Manutenção (Toggle Premium)
                html.Div([
                    html.Label([
                        html.I(className="bi bi-tools me-1 text-muted"),
                        "Tipo de OS"
                    ], className="filter-inline-label mx-1"),
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-layers"),
                            html.Span("Todas")
                        ], 
                        id="filter-tipo-todas",
                        className="premium-toggle-btn active",
                        n_clicks=0
                        ),
                        
                        html.Div([
                            html.I(className="bi bi-wrench-adjustable"),
                            html.Span("Corretiva")
                        ], 
                        id="filter-tipo-corretiva",
                        className="premium-toggle-btn",
                        n_clicks=0
                        ),
                        
                        html.Div([
                            html.I(className="bi bi-shield-check"),
                            html.Span("Preventiva")
                        ], 
                        id="filter-tipo-preventiva",
                        className="premium-toggle-btn",
                        n_clicks=0
                        ),
                    ], className="premium-toggle-container")
                ], className="filter-inline-group filter-inline-group--toggle"),
                
            ], className="filter-bar-fields"),
            
            # Ações
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-check2-circle me-2"),
                    "Aplicar Filtros"
                ], id="btn-apply-global-filters", className="btn-filter-apply me-2"),
                
                dbc.Button([
                    html.I(className="bi bi-eraser-fill")
                ], id="btn-clear-global-filters", title="Limpar Filtros", className="btn-filter-clear me-2"),
                
            ], className="filter-bar-actions"),
            
        ], className="filter-bar-inner"),
        
        # Indicador de filtros ativos
        html.Div(id="active-filters-indicator", className="active-filters-indicator"),
        
        # Store para tipo de manutenção selecionado
        dcc.Store(id="filter-tipo-store", data="TODAS"),
        
        
    ], className="filter-bar", id="global-filter-bar")
