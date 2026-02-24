# -*- coding: utf-8 -*-
"""
Reports Callbacks — Exportação de Relatórios

Registra callbacks para download de PPTX e futuros formatos.

Author: AI Agent
"""

from dash import Input, Output, State, no_update, dcc
from datetime import datetime
import traceback

from backend.repositories import (
    get_ri_evolution_data,
    get_farol_table_data,
)
from backend.repositories.repo_farol_table import get_farol_stats_with_trend
from frontend.components.dashboard_charts import create_ri_geral_chart, create_comparative_chart
from backend.services.ppt import generate_ppt


def register_reports_callbacks(app):
    """Registra callbacks da seção de Relatórios."""

    @app.callback(
        Output("download-ppt", "data"),
        Input("btn-export-ppt", "n_clicks"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True,
    )
    def download_ppt(n_clicks, filters_state):
        """Gera e retorna o PPTX para download."""
        if not n_clicks:
            return no_update

        try:

            # 1. Dados do dashboard (com filtros se houver)
            filters = None
            if filters_state and filters_state.get("applied"):
                filters = filters_state

            df = get_ri_evolution_data(filters)

            if df.empty or ('error_state' in df.columns and df['error_state'].iloc[0]):
                return no_update

            # x_label já gerado pelo repositório (suporta granularidades)

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

            # 3. Charts
            fig_geral = create_ri_geral_chart(df)
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

            # 5. Gerar PPT
            ppt_bytes = generate_ppt(
                kpi_data=kpi_data,
                fig_geral=fig_geral,
                fig_comp=fig_comp,
                farol_stats=farol_stats,
                farol_table_data=farol_table,
            )

            now = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"Relatorio_RI_Edenred_{now}.pptx"


            return dcc.send_bytes(ppt_bytes.getvalue(), filename=filename)

        except Exception as e:
            traceback.print_exc()
            print(f"[REPORTS] Erro ao gerar PPT: {e}", flush=True)
            return no_update
