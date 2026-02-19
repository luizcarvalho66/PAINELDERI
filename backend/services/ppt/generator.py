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


def generate_ppt(kpi_data: dict, fig_geral, fig_comp,
                 farol_stats: dict, farol_table_data: list) -> io.BytesIO:
    """
    Gera a apresentação PPT completa e retorna como BytesIO.

    Args:
        kpi_data: Dict com KPIs formatados
        fig_geral: Plotly Figure do RI Geral
        fig_comp: Plotly Figure do Comparativo
        farol_stats: Dict com stats do farol
        farol_table_data: Lista de dicts da tabela do farol

    Returns:
        BytesIO com .pptx
    """
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # Slide 1: Capa
    build_slide_cover(prs)
    # Slide 2: KPIs
    build_slide_kpis(prs, kpi_data)
    # Slide 3: Chart RI Geral
    build_slide_chart(prs, fig_geral, "Evolução RI Geral")
    # Slide 4: Chart Comparativo
    build_slide_chart(prs, fig_comp, "Corretiva vs Preventiva")
    # Slide 5: Farol Resumo
    build_slide_farol_resumo(prs, farol_stats)
    # Slide 6: Farol Tabela
    build_slide_farol_table(prs, farol_table_data)

    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    return output
