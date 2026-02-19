# -*- coding: utf-8 -*-
"""
Slide 5 — Farol de Corretivas — Resumo com cards coloridos.
"""

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from .config import (
    WHITE, BORDER_GRAY, SLIDE_WIDTH,
    CARD_GREEN, CARD_AMBER, CARD_RED, CARD_PURPLE,
    SUCCESS_BG, WARNING_BG, DANGER_BG, PURPLE_BG,
)
from .helpers import add_text_box, add_rounded_rect, add_gradient_header, add_footer_logo, add_pill_badge


def build_slide_farol_resumo(prs, stats: dict):
    """Farol resumo com cards coloridos."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    add_gradient_header(slide, "Farol de Corretivas — Resumo")

    cards = [
        ("Performando Bem", stats.get("verde", {}).get("value", 0), CARD_GREEN, SUCCESS_BG),
        ("Atenção Necessária", stats.get("amarelo", {}).get("value", 0), CARD_AMBER, WARNING_BG),
        ("Ação Prioritária", stats.get("vermelho", {}).get("value", 0), CARD_RED, DANGER_BG),
        ("Total Analisado", stats.get("total", {}).get("value", 0), CARD_PURPLE, PURPLE_BG),
    ]

    card_w = Inches(2.7)
    card_h = Inches(4.2)
    total_w = 4 * card_w + 3 * Inches(0.5)
    start_x = int((SLIDE_WIDTH - total_w) / 2)
    start_y = Inches(1.5)
    gap = Inches(0.5)

    for idx, (title, value, accent, bg_color) in enumerate(cards):
        x = start_x + idx * (card_w + gap)

        add_rounded_rect(slide, x, start_y, card_w, card_h, WHITE, BORDER_GRAY, radius=0.04)

        # Accent bar no topo
        accent_bar = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            x, start_y, card_w, Pt(6)
        )
        accent_bar.fill.solid()
        accent_bar.fill.fore_color.rgb = accent
        accent_bar.line.fill.background()
        accent_bar.adjustments[0] = 0.5

        # Círculo decorativo
        circle_size = Inches(1.0)
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            x + (card_w - circle_size) // 2,
            start_y + Inches(0.6),
            circle_size, circle_size
        )
        circle.fill.solid()
        circle.fill.fore_color.rgb = bg_color
        circle.line.fill.background()

        # Valor grande
        add_text_box(
            slide, x + Inches(0.1), start_y + Inches(1.85),
            card_w - Inches(0.2), Inches(1.0),
            str(value), size=52, bold=True, color=accent, alignment=PP_ALIGN.CENTER
        )

        # Pill com título
        pill_w = Inches(2.2)
        add_pill_badge(
            slide, x + (card_w - pill_w) // 2, start_y + Inches(3.1),
            pill_w, Inches(0.38),
            title, bg_color=accent, font_size=10
        )

    add_footer_logo(slide)
