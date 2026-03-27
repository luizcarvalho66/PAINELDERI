"""
Barra de Filtros Unificada - RI Dashboard
Design profissional e compacto — Apple Glass aesthetic
DatePickerRange para período (calendário interativo)
"""
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import date, timedelta


def render_filter_bar():
    """
    Renderiza uma barra de filtros horizontal unificada.
    Todos os filtros afetam TODOS os gráficos do dashboard.
    
    Layout: [🔍 Filtros] |  [📅 Período (calendar)]  [Cliente ▾]  | [Aplicar] [✕]
    """
    # Defaults: últimos 5 meses completos
    today = date.today()
    default_end = today
    default_start = (today - timedelta(days=150)).replace(day=1)  # Sempre dia 1 do mês

    return html.Div([
        # Container principal
        html.Div([
            # Ícone + Título
            html.Div([
                html.Span([
                    html.I(className="bi bi-sliders2")
                ], className="filter-bar-icon"),
                html.Span("Filtros", className="filter-bar-title")
            ], className="filter-bar-label"),
            
            # Grid de filtros
            html.Div([
                # 1. Período (DatePickerRange — calendário interativo)
                html.Div([
                    html.Label([
                        html.I(className="bi bi-calendar3 me-1"),
                        "Período"
                    ], className="filter-inline-label"),
                    dcc.DatePickerRange(
                        id="global-filter-periodo-range",
                        display_format="DD/MM/YYYY",
                        first_day_of_week=1,  # Segunda-feira
                        start_date_placeholder_text="Data início",
                        end_date_placeholder_text="Data fim",
                        min_date_allowed=default_start,
                        max_date_allowed=default_end,
                        clearable=True,
                        className="filter-datepicker-range",
                    )
                ], className="filter-inline-group filter-inline-group--calendar"),
                
                # Separador vertical sutil
                html.Div(className="filter-separator"),
                
                # 2. Cliente
                html.Div([
                    html.Label([
                        html.I(className="bi bi-building me-1"),
                        "Cliente"
                    ], className="filter-inline-label"),
                    dcc.Dropdown(
                        id="global-filter-cliente",
                        placeholder="Todos os clientes",
                        multi=True,
                        searchable=True,
                        className="filter-inline-dropdown filter-inline-dropdown--wide"
                    )
                ], className="filter-inline-group"),
                
            ], className="filter-bar-fields"),
            
            # Ações
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-funnel-fill me-2"),
                    "Aplicar"
                ], id="btn-apply-global-filters", className="btn-filter-apply"),
                
                dbc.Button([
                    html.I(className="bi bi-x-lg")
                ], id="btn-clear-global-filters", title="Limpar todos os filtros", className="btn-filter-clear ms-2"),
                
                # Botão de Exportar Novo
                dbc.Button([
                    html.I(className="bi bi-file-earmark-excel-fill", style={"fontSize": "1.1rem"}),
                ], id="btn-open-export-modal", title="Exportar dados da visão atual", className="btn-filter-clear ms-3", style={"color": "#107c41", "borderColor": "#107c41", "backgroundColor": "rgba(16,124,65,0.05)"}),
            ], className="filter-bar-actions"),
            
        ], className="filter-bar-inner"),
        
        # Indicador de filtros ativos
        html.Div(id="active-filters-indicator", className="active-filters-indicator"),
        
        # Store para tipo de manutenção (mantido com valor default para não quebrar callbacks)
        dcc.Store(id="filter-tipo-store", data="TODAS"),
        
    ], className="filter-bar", id="global-filter-bar")
