"""
Filter Callbacks - Filtros Globais do RI Dashboard
Edenred — DatePickerRange para período (calendário interativo)
"""
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from backend.repositories import (
    get_distinct_clients_corretiva,
    get_distinct_months
)


def _generate_month_list(start_date_str, end_date_str):
    """
    Converte um range de datas (YYYY-MM-DD) em lista de YYYY-MM.
    Ex: ('2025-10-23', '2026-01-15') → ['2025-10', '2025-11', '2025-12', '2026-01']
    
    Isso mantém o backend inalterado — ele continua recebendo periodos: ['YYYY-MM', ...]
    """
    if not start_date_str or not end_date_str:
        return []
    
    try:
        start = datetime.strptime(str(start_date_str)[:10], "%Y-%m-%d").date()
        end = datetime.strptime(str(end_date_str)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return []
    
    months = []
    current = start.replace(day=1)
    end_month = end.replace(day=1)
    
    while current <= end_month:
        months.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)
    
    return months


def register_filter_callbacks(app):
    """Registra callbacks de filtros com DatePickerRange."""
    
    # ==========================================================================
    # CALLBACK: Popular filtros quando dados são processados
    # ==========================================================================
    @app.callback(
        [
            Output("global-filter-periodo-range", "min_date_allowed"),
            Output("global-filter-periodo-range", "max_date_allowed"),
            Output("global-filter-cliente", "options"),
        ],
        Input("processing-complete-store", "data"),
        prevent_initial_call=True
    )
    def populate_filter_options(is_processed):
        """Popula o range de datas e dropdown de clientes após processamento."""
        if not is_processed:
            raise PreventUpdate
        
        meses = get_distinct_months()
        clientes = get_distinct_clients_corretiva()
        
        # Extrair min/max date dos meses disponíveis
        if meses:
            # meses é lista de {"label": "Jan/2026", "value": "2026-01"}
            values = sorted([m["value"] for m in meses if isinstance(m, dict) and "value" in m])
            if values:
                min_date = f"{values[0]}-01"
                # Max date: último dia do último mês
                last_month = datetime.strptime(f"{values[-1]}-01", "%Y-%m-%d")
                next_month = last_month + relativedelta(months=1)
                max_date = (next_month - relativedelta(days=1)).strftime("%Y-%m-%d")
            else:
                min_date = (date.today() - relativedelta(months=5)).strftime("%Y-%m-%d")
                max_date = date.today().strftime("%Y-%m-%d")
        else:
            min_date = (date.today() - relativedelta(months=5)).strftime("%Y-%m-%d")
            max_date = date.today().strftime("%Y-%m-%d")
        
        return min_date, max_date, clientes
    
    # ==========================================================================
    # CALLBACK: Limpar todos os filtros
    # ==========================================================================
    @app.callback(
        [
            Output("global-filter-periodo-range", "start_date"),
            Output("global-filter-periodo-range", "end_date"),
            Output("global-filter-cliente", "value"),
        ],
        Input("btn-clear-global-filters", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_all_filters(n_clicks):
        """Limpa todos os filtros globais."""
        if not n_clicks:
            raise PreventUpdate
        return None, None, None
    
    # ==========================================================================
    # CALLBACK: Aplicar filtros e atualizar gráficos
    # ==========================================================================
    @app.callback(
        Output("global-filters-applied-store", "data"),
        Input("btn-apply-global-filters", "n_clicks"),
        [
            State("global-filter-periodo-range", "start_date"),
            State("global-filter-periodo-range", "end_date"),
            State("global-filter-cliente", "value"),
        ],
        prevent_initial_call=True
    )
    def apply_global_filters(n_clicks, start_date, end_date, clientes):
        """
        Aplica os filtros e dispara atualização dos gráficos.
        Converte DatePickerRange → lista de YYYY-MM para manter backend inalterado.
        """
        if not n_clicks:
            raise PreventUpdate
        
        # Converter range de datas para lista de meses (compatível com backend)
        periodos = _generate_month_list(start_date, end_date)
        
        filters = {
            "periodos": periodos,
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
        
        # Tag de período (mostra range formatado)
        if filters.get("periodos"):
            meses = filters["periodos"]
            if len(meses) == 1:
                label = meses[0]
            else:
                # Formatar início → fim
                try:
                    start = datetime.strptime(f"{meses[0]}-01", "%Y-%m-%d")
                    end = datetime.strptime(f"{meses[-1]}-01", "%Y-%m-%d")
                    label = f"{start.strftime('%b/%Y')} → {end.strftime('%b/%Y')}"
                except (ValueError, TypeError):
                    label = f"{len(meses)} meses"
            
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
