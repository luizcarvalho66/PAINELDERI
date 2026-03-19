# -*- coding: utf-8 -*-
"""
PPT Generator — Orquestra a geração de todos os slides.
"""

import io
from pptx import Presentation

from .config import SLIDE_WIDTH, SLIDE_HEIGHT
from .slide_cover import build_slide_cover
from .slide_kpis import build_slide_kpis
from .slide_chart import build_slide_chart
from .slide_farol_resumo import build_slide_farol_resumo
from .slide_farol_table import build_slide_farol_table

# Mapeamento de período para label legível
PERIOD_LABELS = {
    "30d": "Últimos 30 Dias",
    "trimestre": "Último Trimestre",
    "anual": "Últimos 12 Meses",
}


def generate_ppt(kpi_data: dict, fig_geral, fig_comp,
                 farol_stats: dict, farol_table_data: list, df_30d=None, silent_orders=None,
                 client_name=None, period_start=None, period_end=None,
                 farol_insights: dict | None = None,
                 period_label: str = "30d") -> io.BytesIO:
    """
    Gera a apresentação PPT completa e retorna como BytesIO.

    Args:
        kpi_data: Dict com KPIs formatados
        fig_geral: Plotly Figure do RI Geral
        fig_comp: Plotly Figure do Comparativo
        farol_stats: Dict com stats do farol
        farol_table_data: Lista de dicts da tabela do farol
        df_30d: DataFrame com os dados detalhados
        silent_orders: Lista de dicts com Top 3 Silent Order
        farol_insights: Insights por categoria (verde/amarelo/vermelho)
        period_label: Chave do período ("30d", "trimestre", "anual")

    Returns:
        BytesIO com .pptx
    """
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # Label legível para headers dos slides
    label = PERIOD_LABELS.get(period_label, "Últimos 30 Dias")

    # Slide 1: Capa
    build_slide_cover(prs, client_name=client_name, period_start=period_start, period_end=period_end)
    # Slide 2: KPIs
    build_slide_kpis(prs, kpi_data, period_label=label)
    # Slide 3: Chart RI Geral (Silent Order)
    build_slide_chart(prs, fig_geral, f"Evolução Silent Order  |  {label}", df_30d=df_30d, silent_orders=silent_orders, is_so_mode=True)
    # Slide 4: Chart Comparativo
    build_slide_chart(prs, fig_comp, f"Corretiva vs Preventiva  |  {label}")
    # Slide 5: Farol Resumo
    build_slide_farol_resumo(prs, farol_stats, insights=farol_insights, farol_table_data=farol_table_data)
    # Slide 6: Farol Tabela
    build_slide_farol_table(prs, farol_table_data)

    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output
