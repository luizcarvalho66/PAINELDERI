# -*- coding: utf-8 -*-
"""
Slide 2 — KPIs com pills estilo Edenred.
"""

from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from .config import (
    WHITE, EDENRED_RED, TEXT_DARK, TEXT_MUTED, BORDER_GRAY,
    CARD_GREEN, CARD_PURPLE, DANGER_BG, SUCCESS_BG, PURPLE_BG,
)
from .helpers import add_text_box, add_rounded_rect, add_gradient_header, add_footer_logo, add_pill_badge


def build_slide_kpis(prs, kpi_data: dict):
    """KPIs em grid 3x2 com pills coloridos."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    add_gradient_header(slide, "Indicadores-Chave de Performance")

    kpis = [
        ("Análise Total", kpi_data.get("total_analisado", "—"), "Ordens processadas", CARD_PURPLE, PURPLE_BG),
        ("Economia Real", kpi_data.get("economia_real", "—"), "Valor economizado", CARD_GREEN, SUCCESS_BG),
        ("Share Preventiva", kpi_data.get("share_preventiva", "—"), "Mix de manutenções", RGBColor(0x3B, 0x82, 0xF6), RGBColor(0xEF, 0xF6, 0xFF)),
        ("RI Geral", kpi_data.get("ri_geral", "—"), "Média do período", EDENRED_RED, DANGER_BG),
        ("RI Preventiva", kpi_data.get("ri_preventiva", "—"), "Manutenção programada", CARD_GREEN, SUCCESS_BG),
        ("RI Corretiva", kpi_data.get("ri_corretiva", "—"), "Manutenção sob demanda", EDENRED_RED, DANGER_BG),
    ]

    card_w = Inches(3.6)
    card_h = Inches(2.4)
    start_x = Inches(0.95)
    start_y = Inches(1.4)
    gap_x = Inches(0.45)
    gap_y = Inches(0.5)

    for idx, (title, value, desc, accent, accent_bg) in enumerate(kpis):
        col = idx % 3
        row = idx // 3
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)

        add_rounded_rect(slide, x, y, card_w, card_h, WHITE, BORDER_GRAY, radius=0.04)

        add_pill_badge(
            slide, x + Inches(0.3), y + Inches(0.25),
            Inches(2.2), Inches(0.38),
            title, bg_color=accent, font_size=10
        )

        add_text_box(
            slide, x + Inches(0.3), y + Inches(0.85),
            card_w - Inches(0.6), Inches(0.9),
            str(value), size=32, bold=True, color=TEXT_DARK, alignment=PP_ALIGN.LEFT
        )

        add_text_box(
            slide, x + Inches(0.3), y + Inches(1.8),
            card_w - Inches(0.6), Inches(0.4),
            desc, size=11, color=TEXT_MUTED
        )

    add_footer_logo(slide)
