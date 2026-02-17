# -*- coding: utf-8 -*-
"""
Corretivas Callbacks - Callbacks para a seção exclusiva do Farol

Este módulo registra os callbacks do Dash para:
- Atualização dos cards de resumo
- Atualização da tabela do farol
- Atualização do gráfico de linha
- Drill-down interativo

Author: Luiz Eduardo Carvalho
"""

from dash import Input, Output, State, html, dcc, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from backend.repositories import (
    get_ri_corretivas_chart,
    get_farol_table_data,
    get_farol_resumo,
    get_logs_nao_aprovacao,
    get_drill_down_chave,
    # Filtros
    get_distinct_clients_corretiva,
    get_distinct_chaves
)


def register_corretivas_callbacks(app):
    """Registra todos os callbacks da seção Farol/Corretivas."""
    
    # =========================================================================
    # CALLBACK 1: Atualizar Cards de Resumo
    # =========================================================================
    @app.callback(
        [
            Output("farol-card-verde", "children"),
            Output("farol-card-amarelo", "children"),
            Output("farol-card-vermelho", "children"),
            Output("farol-card-total", "children"),
        ],
        [Input("farol-interval-refresh", "n_intervals")],
        prevent_initial_call=False
    )
    def update_farol_cards(n_intervals):
        """Atualiza os cards de resumo com contagem de cada cor e indicadores de tendência."""
        try:
            # NOVA LÓGICA: Buscar stats com tendência (comparado ao snapshot anterior)
            from backend.repositories.repo_farol_table import get_farol_stats_with_trend
            from frontend.components.farol_cards import create_card_inner_content
            
            stats = get_farol_stats_with_trend()
            
            # Helper para extrair dados limpos
            def get_data(key):
                item = stats.get(key, {})
                return {
                    "value": str(item.get("value", 0)),
                    "trend": item.get("trend", 0.0),
                    "dir": item.get("direction", "neutral")
                }

            s_verde = get_data("verde")
            s_amarelo = get_data("amarelo")
            s_vermelho = get_data("vermelho")
            s_total = get_data("total")
            
            # Formatar numeros
            val_verde = f"{int(s_verde['value']):,}".replace(",", ".")
            val_amarelo = f"{int(s_amarelo['value']):,}".replace(",", ".")
            val_vermelho = f"{int(s_vermelho['value']):,}".replace(",", ".")
            val_total = f"{int(s_total['value']):,}".replace(",", ".")
            
            # Gerar conteúdos internos (H2 + Seta)
            content_verde = create_card_inner_content(val_verde, s_verde["trend"], s_verde["dir"], "Performando Bem")
            content_amarelo = create_card_inner_content(val_amarelo, s_amarelo["trend"], s_amarelo["dir"], "Atenção Necessária")
            content_vermelho = create_card_inner_content(val_vermelho, s_vermelho["trend"], s_vermelho["dir"], "Ação Prioritária")
            content_total = create_card_inner_content(val_total, s_total["trend"], s_total["dir"], "Total Analisado")
            
            return content_verde, content_amarelo, content_vermelho, content_total

        except Exception as e:
            print(f"[FAROL CARDS ERROR] Falha ao atualizar KPIs: {e}")
            import traceback
            traceback.print_exc()
            # Retorno de fallback (perde a formatação bonita, mas evita crash)
            return "0", "0", "0", "0"

    # =========================================================================
    # CALLBACK: MODAL DE AJUDA
    # =========================================================================
    @app.callback(
        Output("farol-help-modal", "is_open"),
        [Input("farol-help-btn", "n_clicks")],
        [State("farol-help-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_farol_help_modal(n_clicks, is_open):
        """Abre/fecha o modal de ajuda do Farol."""
        if n_clicks:
            return not is_open
        return is_open

    # =========================================================================
    # CALLBACK: Toggle Visão Geral / Oportunidades
    # =========================================================================
    @app.callback(
        [
            Output("farol-view-mode-store", "data"),
            Output("toggle-view-geral", "className"),
            Output("toggle-view-oportunidades", "className")
        ],
        [
            Input("toggle-view-geral", "n_clicks"),
            Input("toggle-view-oportunidades", "n_clicks")
        ],
        [State("farol-view-mode-store", "data")],
        prevent_initial_call=True
    )
    def toggle_view_mode(n_geral, n_oport, current_mode):
        """Alterna entre Visão Geral e Oportunidades."""
        try:
            ctx = callback_context
            
            # Classes base
            base_class = "premium-toggle-btn"
            active_class = "premium-toggle-btn active"
            
            if not ctx.triggered:
                return no_update, no_update, no_update
            
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if triggered_id == "toggle-view-geral":
                return "geral", active_class, base_class
            elif triggered_id == "toggle-view-oportunidades":
                return "oportunidades", base_class, active_class
                
            return no_update, no_update, no_update
        except Exception as e:

            return no_update, no_update, no_update


    # =========================================================================
    # CALLBACK: Popular Filtros do Farol
    # =========================================================================
    @app.callback(
        [
            Output("farol-filter-cliente", "options"),
            Output("farol-filter-chave", "options")
        ],
        [Input("farol-interval-refresh", "n_intervals")],
        [State("farol-filter-cliente", "options")],
        prevent_initial_call=False
    )
    def populate_farol_filters(n, current_clientes):
        """Popula os dropdowns de filtro se estiverem vazios."""
        if current_clientes and len(current_clientes) > 0:
            return no_update, no_update
            
        clientes = get_distinct_clients_corretiva()
        chaves = get_distinct_chaves()
        
        return clientes, chaves

    # =========================================================================
    # CALLBACK 2: Atualizar Tabela do Farol
    # =========================================================================
    @app.callback(
        [
            Output("farol-table-container", "children"),
            Output("farol-pagination", "max_value"),
            Output("farol-pagination", "style"),
            Output("farol-pagination", "active_page") # Resetar pagina ao filtrar
        ],
        [
            Input("farol-interval-refresh", "n_intervals"),
            Input("farol-pagination", "active_page"),
            # Filtros
            Input("farol-filter-cliente", "value"),
            Input("farol-filter-chave", "value"),
            Input("farol-filter-prioridade", "value"),
            # Toggle Visão Geral / Oportunidades
            Input("farol-view-mode-store", "data"),
            # Novo Toggle Agrupar por Cliente
            Input("farol-group-client-switch", "value")
        ],
        prevent_initial_call=False
    )
    def update_farol_table(n_intervals, active_page, f_clientes, f_chaves, f_prioridade, view_mode, group_by_client):
        """Atualiza a tabela principal do farol com paginação e filtros."""
        try:
            # Contexto para saber quem disparou
            ctx = callback_context
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
            
            # Se disparado por filtro OU toggle de view, reseta para página 1
            if triggered_id and ("filter" in triggered_id or "view-mode" in triggered_id or "toggle" in triggered_id):
                page = 1
                should_reset_page = 1
            else:
                page = active_page if active_page else 1
                should_reset_page = no_update
            
            page_size = 10  # Itens por página
            
            # Montar objeto de filtros
            filters = {}
            if f_clientes: filters["clientes"] = f_clientes
            if f_chaves: filters["chaves"] = f_chaves
            if f_prioridade: filters["prioridade"] = f_prioridade
            
            # Determinar se é modo oportunidades
            only_opportunities = (view_mode == "oportunidades")
            
            # Buscar dados da página atual COM FILTROS
            dados = get_farol_table_data(
                filters=filters, 
                page=page, 
                page_size=page_size,
                only_opportunities=only_opportunities,
                group_by_client=group_by_client
            )
            
            # Calcular total de páginas de forma dinâmica
            from backend.repositories.repo_farol_table import get_farol_total_count
            total_count = get_farol_total_count(
                filters=filters, 
                only_opportunities=only_opportunities, 
                group_by_client=group_by_client
            )
            total_pages = max(1, (total_count + page_size - 1) // page_size)  # Ceiling division
            
            pagination_style = {"display": "flex"}
            
            if not dados:
                return (
                    html.Div(
                        "Nenhum dado encontrado com os filtros selecionados.",
                        className="text-muted text-center p-4"
                    ),
                    1,
                    {"display": "none"},
                    should_reset_page
                )
            
            # Importar função de renderização do componente
            from frontend.components.farol_table import render_farol_table_content
            return render_farol_table_content(dados), total_pages, pagination_style, should_reset_page
            
        except Exception as e:

            return (
                html.Div(f"Erro: {str(e)}", className="text-danger"),
                1,
                {"display": "none"},
                1
            )
    
    
    # _build_farol_table REMOVIDO PARA frontend/components/farol_table.py
    
    # =========================================================================
    # CALLBACK: TOGGLE DA SEÇÃO DE LOGS
    # =========================================================================
    @app.callback(
        [
            Output("logs-collapse", "is_open"),
            Output("logs-toggle-btn", "children")
        ],
        [Input("logs-toggle-btn", "n_clicks")],
        [State("logs-collapse", "is_open")],
        prevent_initial_call=True
    )
    def toggle_logs_section(n_clicks, is_open):
        """Abre/fecha a seção de logs."""
        if n_clicks:
            new_state = not is_open
            if new_state:
                btn_content = [html.I(className="bi bi-chevron-up me-1"), "Recolher"]
            else:
                btn_content = [html.I(className="bi bi-chevron-down me-1"), "Expandir"]
            return new_state, btn_content
        return is_open, no_update

    # =========================================================================
    # CALLBACK: POPULAR FILTROS DOS LOGS
    # =========================================================================
    @app.callback(
        [
            Output("logs-filter-peca", "options"),
            Output("logs-filter-tipo-mo", "options"),
            Output("logs-filter-motivo", "options"),
            Output("logs-filter-cliente", "options")
        ],
        [Input("logs-collapse", "is_open")],
        prevent_initial_call=True
    )
    def populate_logs_filters(is_open):
        """Popula os dropdowns de filtro quando a seção é aberta."""
        if not is_open:
            return no_update, no_update, no_update, no_update
        
        try:
            from backend.repositories.repo_logs_corretiva import get_logs_filter_options, get_logs_nao_aprovacao
            
            # Buscar opções disponíveis para os filtros
            options = get_logs_filter_options()
            
            

            
            pecas = [{"label": p, "value": p} for p in options.get("pecas", [])]
            tipos_mo = [{"label": t, "value": t} for t in options.get("tipos_mo", [])]
            
            # Motivos ainda precisamos pegar dos logs recentes ou implementar full scan também
            # Por enquanto, mantemos a lógica de pegar 500 mais recentes para os motivos (texto livre)
            df_motivos = get_logs_nao_aprovacao(page=1, page_size=500)
            motivos_raw = df_motivos["motivo"].dropna().unique() if not df_motivos.empty else []
            motivos = [{"label": str(m)[:50] + "..." if len(str(m)) > 50 else str(m), "value": str(m)} 
                      for m in motivos_raw if m and str(m).strip()][:20]
            
            # Clientes
            clientes = [{"label": c, "value": c} for c in options.get("clientes", [])]
            


            return pecas, tipos_mo, motivos, clientes
            
        except Exception as e:

            return [], [], [], []

    # =========================================================================
    # CALLBACK: ATUALIZAR TABELA DE LOGS COM PAGINAÇÃO
    # =========================================================================
    @app.callback(
        [
            Output("logs-table-container", "children"),
            Output("logs-pagination", "max_value"),
            Output("logs-pagination", "style"),
            Output("logs-count-info", "children"),
            Output("logs-pagination", "active_page")
        ],
        [
            Input("logs-collapse", "is_open"),
            Input("logs-pagination", "active_page"),
            Input("logs-filter-peca", "value"),
            Input("logs-filter-tipo-mo", "value"),
            Input("logs-filter-motivo", "value"),
            Input("logs-filter-cliente", "value")
        ],
        prevent_initial_call=False  # CORREÇÃO: Permitir carga inicial
    )
    def update_logs_table(is_open, active_page, f_peca, f_tipo_mo, f_motivo, f_cliente):
        """Atualiza a tabela de logs com base nos filtros e paginação."""
        # Se seção fechada, não renderiza nada
        if not is_open:
            return no_update, no_update, no_update, no_update, no_update
        
        try:
            from backend.repositories.repo_logs_corretiva import get_logs_nao_aprovacao, get_logs_total_count
            
            # Contexto para saber quem disparou
            ctx = callback_context
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
            
            # Se disparado por filtro, reseta para página 1
            if triggered_id and "filter" in triggered_id:
                page = 1
                should_reset_page = 1
            else:
                page = active_page if active_page else 1
                should_reset_page = no_update
            
            page_size = 15  # Itens por página
            
            # Montar filtros
            filters = {}
            if f_peca: filters["peca"] = f_peca
            if f_tipo_mo: filters["tipo_mo"] = f_tipo_mo
            if f_cliente: filters["clientes"] = [f_cliente]
            
            # Carregar dados paginados
            df = get_logs_nao_aprovacao(filters=filters if filters else None, page=page, page_size=page_size)
            
            # Filtrar por motivo no Python (pois é texto livre)
            if f_motivo and not df.empty:
                df = df[df["motivo"] == f_motivo]
            
            # Calcular total de páginas
            total_count = get_logs_total_count(filters=filters if filters else None)
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            
            # Info de contagem
            start_item = (page - 1) * page_size + 1
            end_item = min(page * page_size, total_count)
            count_info = f"Exibindo {start_item:,} - {end_item:,} de {total_count:,} registros"
            
            pagination_style = {"display": "flex"} if total_pages > 1 else {"display": "none"}
            
            if df.empty:
                return (
                    html.Div(
                        "Nenhum log encontrado com os filtros selecionados.",
                        className="text-muted text-center p-4"
                    ),
                    1,
                    {"display": "none"},
                    "",
                    should_reset_page
                )
            
            from frontend.components.farol_table import render_logs_table_content
            return render_logs_table_content(df), total_pages, pagination_style, count_info, should_reset_page
            
        except Exception as e:

            return html.Div(f"Erro: {str(e)}", className="text-danger p-3"), 1, {"display": "none"}, "", 1




# =============================================================================
# REGISTRO DE CALLBACKS
# =============================================================================

def init_corretivas_callbacks(app):
    """Função de inicialização para ser chamada do app.py"""
    register_corretivas_callbacks(app)

