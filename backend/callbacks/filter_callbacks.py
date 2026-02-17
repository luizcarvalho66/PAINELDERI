"""
Filter Callbacks - Filtros que REALMENTE funcionam
RI Dashboard - Edenred
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
        
        print("[FILTER_CALLBACKS] Populando dropdowns de filtros globais...")
        
        meses = get_distinct_months()
        clientes = get_distinct_clients_corretiva()
        
        print(f"[FILTER_CALLBACKS] Loaded: {len(clientes)} clientes, {len(meses)} meses")
        
        return meses, clientes
    
    # ==========================================================================
    # CALLBACK: Toggle de tipo de manutenção (visual feedback)
    # ==========================================================================
    @app.callback(
        [
            Output("filter-tipo-todas", "color"),
            Output("filter-tipo-todas", "outline"),
            Output("filter-tipo-corretiva", "color"),
            Output("filter-tipo-corretiva", "outline"),
            Output("filter-tipo-preventiva", "color"),
            Output("filter-tipo-preventiva", "outline"),
            Output("filter-tipo-store", "data"),
        ],
        [
            Input("filter-tipo-todas", "n_clicks"),
            Input("filter-tipo-corretiva", "n_clicks"),
            Input("filter-tipo-preventiva", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_tipo_manutencao(n_todas, n_corr, n_prev):
        """Alterna o toggle visual de tipo de manutenção."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Estado padrão: todos outline secondary
        todas = ("secondary", True)
        corr = ("secondary", True)
        prev = ("secondary", True)
        tipo_valor = "TODAS"
        
        if triggered_id == "filter-tipo-todas":
            todas = ("danger", False)
            tipo_valor = "TODAS"
        elif triggered_id == "filter-tipo-corretiva":
            corr = ("danger", False)
            tipo_valor = "CORRETIVA"
        elif triggered_id == "filter-tipo-preventiva":
            prev = ("danger", False)
            tipo_valor = "PREVENTIVA"
        
        return (
            todas[0], todas[1],
            corr[0], corr[1],
            prev[0], prev[1],
            tipo_valor
        )
    
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
        print("[FILTER_CALLBACKS] Limpando filtros...")
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
            State("filter-tipo-store", "data"),
        ],
        prevent_initial_call=True
    )
    def apply_global_filters(n_clicks, periodos, clientes, tipo):
        """
        Aplica os filtros e dispara atualização dos gráficos.
        Retorna o estado dos filtros para ser consumido pelo dashboard.
        """
        if not n_clicks:
            raise PreventUpdate
        
        filters = {
            "periodos": periodos or [],
            "clientes": clientes or [],
            "tipo_manutencao": tipo or "TODAS",
            "applied": True
        }
        
        print(f"[FILTER_CALLBACKS] Filtros aplicados: {filters}")
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
        """Mostra os filtros ativos como tags."""
        if not filters or not filters.get("applied"):
            return [], "active-filters-indicator"
        
        tags = []
        
        # Tag de período
        if filters.get("periodos"):
            count = len(filters["periodos"])
            tags.append(html.Span([
                html.Span("Período: ", className="filter-tag-label"),
                f"{count} selecionado(s)"
            ], className="filter-tag"))
        
        # Tag de clientes
        if filters.get("clientes"):
            count = len(filters["clientes"])
            tags.append(html.Span([
                html.Span("Clientes: ", className="filter-tag-label"),
                f"{count} selecionado(s)"
            ], className="filter-tag"))
        
        # Tag de tipo
        if filters.get("tipo_manutencao") and filters["tipo_manutencao"] != "TODAS":
            tags.append(html.Span([
                html.Span("Tipo: ", className="filter-tag-label"),
                filters["tipo_manutencao"]
            ], className="filter-tag"))
        
        if tags:
            return tags, "active-filters-indicator has-filters"
        return [], "active-filters-indicator"
    
    # ==========================================================================
    # CALLBACK: Exportar dados filtrados
    # ==========================================================================
    @app.callback(
        Output("download-filtered-data", "data"),
        Input("btn-export-global", "n_clicks"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True
    )
    def export_filtered_data(n_clicks, filters):
        """Exporta dados filtrados para Excel."""
        if not n_clicks:
            raise PreventUpdate
        
        from database import get_connection
        conn = get_connection()
        if conn is None:
            raise PreventUpdate
        
        try:
            query = """
            SELECT 
                nome_cliente, numero_os, peca, tipo_mo, 
                valor_aprovado, data_transacao, uf
            FROM ri_corretiva_detalhamento
            WHERE data_transacao IS NOT NULL
            """
            
            # Aplicar filtros
            if filters:
                if filters.get("clientes"):
                    clients = "', '".join(filters["clientes"])
                    query += f" AND nome_cliente IN ('{clients}')"
                    
                if filters.get("periodos"):
                    period_clauses = []
                    for p in filters["periodos"]:
                        year, month = p.split("-")
                        period_clauses.append(f"(year(data_transacao) = {year} AND month(data_transacao) = {month})")
                    if period_clauses:
                        query += f" AND ({' OR '.join(period_clauses)})"
            
            query += " ORDER BY data_transacao DESC LIMIT 50000"
            
            df = conn.execute(query).fetchdf()
            
            if df.empty:
                raise PreventUpdate
            
            return dcc.send_data_frame(df.to_excel, "ri_dados_filtrados.xlsx", index=False)
        except Exception as e:
            print(f"[EXPORT ERROR] {e}")
            raise PreventUpdate
