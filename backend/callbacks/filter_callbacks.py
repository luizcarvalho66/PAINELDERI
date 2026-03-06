"""
Filter Callbacks - Filtros Globais do RI Dashboard
Edenred — Sem toggle tipo OS (removido por simplificação UX)
"""
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate

from backend.repositories import (
    get_distinct_clients_corretiva,
    get_distinct_months
)


def register_filter_callbacks(app):
    """Registra callbacks de filtros com lógica funcional."""
    
    # ==========================================================================
    # CALLBACK: Popular dropdowns quando dados são processados
    # ==========================================================================
    @app.callback(
        [
            Output("global-filter-periodo", "options"),
            Output("global-filter-cliente", "options"),
        ],
        Input("processing-complete-store", "data"),
        prevent_initial_call=True
    )
    def populate_filter_dropdowns(is_processed):
        """Popula os dropdowns globais após processamento."""
        if not is_processed:
            raise PreventUpdate
        
        meses = get_distinct_months()
        clientes = get_distinct_clients_corretiva()
        
        return meses, clientes
    
    # ==========================================================================
    # CALLBACK: Limpar todos os filtros
    # ==========================================================================
    @app.callback(
        [
            Output("global-filter-periodo", "value"),
            Output("global-filter-cliente", "value"),
        ],
        Input("btn-clear-global-filters", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_all_filters(n_clicks):
        """Limpa todos os filtros globais."""
        if not n_clicks:
            raise PreventUpdate
        return None, None
    
    # ==========================================================================
    # CALLBACK: Aplicar filtros e atualizar gráficos
    # ==========================================================================
    @app.callback(
        Output("global-filters-applied-store", "data"),
        Input("btn-apply-global-filters", "n_clicks"),
        [
            State("global-filter-periodo", "value"),
            State("global-filter-cliente", "value"),
        ],
        prevent_initial_call=True
    )
    def apply_global_filters(n_clicks, periodos, clientes):
        """
        Aplica os filtros e dispara atualização dos gráficos.
        tipo_manutencao fixado em "TODAS" (toggle removido da UI).
        """
        if not n_clicks:
            raise PreventUpdate
        
        filters = {
            "periodos": periodos or [],
            "clientes": clientes or [],
            "tipo_manutencao": "TODAS",
            "applied": True
        }
        
        return filters
    
    # ==========================================================================
    # CALLBACK: Indicador de filtros ativos
    # ==========================================================================
    @app.callback(
        [
            Output("active-filters-indicator", "children"),
            Output("active-filters-indicator", "className"),
        ],
        Input("global-filters-applied-store", "data"),
        prevent_initial_call=True
    )
    def update_active_filters_indicator(filters):
        """Mostra os filtros ativos como tags visuais."""
        if not filters or not filters.get("applied"):
            return [], "active-filters-indicator"
        
        tags = []
        
        # Tag de período
        if filters.get("periodos"):
            count = len(filters["periodos"])
            label = filters["periodos"][0] if count == 1 else f"{count} meses"
            tags.append(html.Span([
                html.I(className="bi bi-calendar3 me-1"),
                html.Span("Período: ", className="filter-tag-label"),
                label
            ], className="filter-tag"))
        
        # Tag de clientes
        if filters.get("clientes"):
            count = len(filters["clientes"])
            label = filters["clientes"][0][:20] if count == 1 else f"{count} clientes"
            tags.append(html.Span([
                html.I(className="bi bi-building me-1"),
                html.Span("Cliente: ", className="filter-tag-label"),
                label
            ], className="filter-tag"))
        
        if tags:
            return tags, "active-filters-indicator has-filters"
        return [], "active-filters-indicator"
