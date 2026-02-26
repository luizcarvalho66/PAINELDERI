# -*- coding: utf-8 -*-
"""
Reports Callbacks — Exportação de Relatórios

Registra callbacks para download de PPTX com seleção de cliente TGM.

Author: AI Agent
"""

from dash import Input, Output, State, no_update, dcc, clientside_callback, html, callback_context
from datetime import datetime
import traceback

from backend.repositories import (
    get_ri_evolution_data,
    get_farol_table_data,
)
from backend.repositories.repo_dashboard import (
    get_ri_evolution_30d,
    get_distinct_clients,
)
from backend.repositories.repo_farol_table import get_farol_stats_with_trend
from frontend.components.dashboard_charts import create_ri_geral_chart, create_comparative_chart
from backend.services.ppt import generate_ppt


def register_reports_callbacks(app):
    """Registra callbacks da seção de Relatórios."""

    # ── 1. Abrir modal ao clicar no botão de exportar PPT ──
    @app.callback(
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Output("dropdown-client-tgm", "options"),
        Input("btn-export-ppt", "n_clicks"),
        prevent_initial_call=True,
    )
    def open_client_modal(n_clicks):
        """Abre modal e popula dropdown com clientes distintos."""
        if not n_clicks:
            return no_update, no_update

        try:
            clients = get_distinct_clients()
            options = [{"label": c, "value": c} for c in clients]
        except Exception:
            options = []

        return True, options

    # ── 2. Habilitar/desabilitar botão de confirmar baseado na seleção ──
    @app.callback(
        Output("btn-generate-ppt-confirm", "disabled"),
        Input("dropdown-client-tgm", "value"),
        prevent_initial_call=True,
    )
    def toggle_confirm_button(selected_client):
        """Habilita o botão de gerar quando um cliente é selecionado."""
        return not bool(selected_client)

    # ── 3. Fechar modal ao cancelar ──
    @app.callback(
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Input("btn-cancel-ppt-modal", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_client_modal(n_clicks):
        if not n_clicks:
            return no_update
        return False

    # ── 4. Callback clientside para abrir loading overlay IMEDIATAMENTE ──
    clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks) {
                return {"display": "flex"};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("ppt-loading-overlay", "style"),
        Input("btn-generate-ppt-confirm", "n_clicks"),
        prevent_initial_call=True,
    )

    # ── 5. Gerar PPT filtrado pelo cliente selecionado ──
    @app.callback(
        Output("download-ppt", "data"),
        Output("ppt-loading-overlay", "style", allow_duplicate=True),
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Output("dropdown-client-tgm", "value"),
        Input("btn-generate-ppt-confirm", "n_clicks"),
        State("dropdown-client-tgm", "value"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True,
    )
    def download_ppt(n_clicks, selected_client, filters_state):
        """Gera e retorna o PPTX filtrado pelo cliente selecionado."""
        if not n_clicks or not selected_client:
            return no_update, no_update, no_update, no_update

        try:
            # Construir filtros com o cliente selecionado
            filters = None
            if filters_state and filters_state.get("applied"):
                filters = dict(filters_state)
            else:
                filters = {}

            # Forçar filtro pelo cliente selecionado no modal
            filters["clientes"] = [selected_client]
            filters["applied"] = True

            # 1. Dados do dashboard filtrados pelo cliente
            df = get_ri_evolution_data(filters)

            if df.empty or ('error_state' in df.columns and df['error_state'].iloc[0]):
                return no_update, {"display": "none"}, False, None

            total_analisado = int((df['qtd_prev'] + df['qtd_corr']).sum())
            ri_geral_avg = df['ri_geral'].mean() * 100

            econ_corr = df['sum_economia_pricing'].sum() if 'sum_economia_pricing' in df.columns else 0
            econ_prev = (df['sum_total_prev'] - df['sum_aprovado_prev']).clip(lower=0).sum()
            economia_real = econ_corr + econ_prev

            total_prev = int(df['qtd_prev'].sum())
            total_corr = int(df['qtd_corr'].sum())
            ratio_prev_corr = (total_prev / (total_corr + total_prev) * 100) if (total_corr + total_prev) > 0 else 0

            avg_ri_prev = df['ri_preventiva'].mean() * 100
            avg_ri_corr = df['ri_corretiva'].mean() * 100

            kpi_data = {
                "total_analisado": f"{total_analisado:,}",
                "economia_real": f"R$ {economia_real/1000000:,.1f}M",
                "share_preventiva": f"{ratio_prev_corr:.1f}%",
                "ri_geral": f"{ri_geral_avg:.1f}%",
                "ri_preventiva": f"{avg_ri_prev:.1f}%",
                "ri_corretiva": f"{avg_ri_corr:.1f}%",
            }

            # 3. Charts filtrados
            df_30d = get_ri_evolution_30d(filters)
            if not df_30d.empty:
                fig_geral = create_ri_geral_chart(df_30d)
            else:
                fig_geral = create_ri_geral_chart(df)  # fallback

            fig_comp = create_comparative_chart(df)

            # 4. Farol
            try:
                farol_stats = get_farol_stats_with_trend()
            except Exception:
                farol_stats = {
                    "verde": {"value": 0},
                    "amarelo": {"value": 0},
                    "vermelho": {"value": 0},
                    "total": {"value": 0},
                }

            try:
                farol_table = get_farol_table_data(page=1, page_size=15)
            except Exception:
                farol_table = []

            # 5. Top Ofensores 30d filtrado
            try:
                from backend.repositories.repo_dashboard import get_top_ofensores_30d
                ofensores = get_top_ofensores_30d(filters, limite=3)
            except Exception:
                ofensores = []

            # 6. Gerar PPT
            ppt_bytes = generate_ppt(
                kpi_data=kpi_data,
                fig_geral=fig_geral,
                fig_comp=fig_comp,
                farol_stats=farol_stats,
                farol_table_data=farol_table,
                df_30d=df_30d,
                ofensores=ofensores
            )

            # Nome do arquivo inclui o cliente
            now = datetime.now().strftime("%Y%m%d_%H%M")
            # Sanitizar nome do cliente para o filename
            safe_name = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in selected_client
            ).strip().replace(' ', '_')[:30]
            filename = f"Relatorio_RI_{safe_name}_{now}.pptx"

            return (
                dcc.send_bytes(ppt_bytes.getvalue(), filename=filename),
                {"display": "none"},
                False,   # Fechar modal
                None,    # Resetar dropdown
            )

        except Exception as e:
            traceback.print_exc()
            print(f"[REPORTS] Erro ao gerar PPT: {e}", flush=True)
            return no_update, {"display": "none"}, False, None
