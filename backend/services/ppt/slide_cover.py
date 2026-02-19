# -*- coding: utf-8 -*-
"""
Slide 1 — Capa executiva estilo Edenred.

Design split-screen com border radius, ícones profissionais,
cores alinhadas com base.css, sem redundância.
"""

import os
from datetime import datetime
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

from .config import (
    WHITE, EDENRED_RED, EDENRED_RED_DARK, EDENRED_CORAL,
    EDENRED_DARK, TEXT_MUTED, BG_LIGHT, BORDER_GRAY,
    SLIDE_WIDTH, LOGO_PATH, ICONS_DIR,
)
from .helpers import add_text_box


def _add_icon(slide, icon_name, left, top, size=Inches(0.45)):
    """Adiciona ícone PNG ao slide se existir."""
    path = os.path.join(ICONS_DIR, f"{icon_name}.png")
    if os.path.exists(path):
        slide.shapes.add_picture(path, left, top, width=size, height=size)


def build_slide_cover(prs):
    """Capa executiva split-screen com border radius e ícones."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Fundo cinza claro (como o app)
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_LIGHT

    # ============================================
    # BLOCO VERMELHO ESQUERDO (com border radius)
    # ============================================
    red_w = Inches(6.5)
    red_h = Inches(6.0)
    red_margin = Inches(0.4)

    red_block = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        red_margin, red_margin,
        red_w, red_h
    )
    fill = red_block.fill
    fill.gradient()
    fill.gradient_stops[0].color.rgb = EDENRED_RED_DARK   # #C10510
    fill.gradient_stops[0].position = 0.0
    fill.gradient_stops[1].color.rgb = EDENRED_RED         # #E20613
    fill.gradient_stops[1].position = 1.0
    red_block.line.fill.background()
    red_block.adjustments[0] = 0.03  # border radius suave

    # Accent branco fino (barra decorativa)
    accent = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.0), Inches(1.3),
        Inches(0.6), Pt(4)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = WHITE
    accent.line.fill.background()
    accent.adjustments[0] = 0.5

    # Título principal
    add_text_box(
        slide, Inches(1.0), Inches(1.6),
        Inches(5.2), Inches(2.2),
        "Regulação\nInteligente",
        size=46, bold=True, color=WHITE, alignment=PP_ALIGN.LEFT
    )

    # Linha separadora branca fina
    sep = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.0), Inches(3.9),
        Inches(2.5), Pt(1)
    )
    sep.fill.solid()
    sep.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    sep.line.fill.background()

    # Subtítulo
    add_text_box(
        slide, Inches(1.0), Inches(4.2),
        Inches(5.2), Inches(0.5),
        "RELATÓRIO EXECUTIVO",
        size=13, bold=True, color=RGBColor(0xFF, 0xCC, 0xCC),
        alignment=PP_ALIGN.LEFT
    )

    # Descrição
    add_text_box(
        slide, Inches(1.0), Inches(4.8),
        Inches(5.0), Inches(0.8),
        "Análise de Performance\nde Manutenção Automotiva",
        size=12, color=RGBColor(0xFF, 0xBB, 0xBB),
        alignment=PP_ALIGN.LEFT
    )

    # ============================================
    # LADO DIREITO — Card branco com border radius
    # ============================================
    card_x = Inches(7.3)
    card_y = Inches(0.4)
    card_w = Inches(5.6)
    card_h = Inches(6.0)

    white_card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        card_x, card_y,
        card_w, card_h
    )
    white_card.fill.solid()
    white_card.fill.fore_color.rgb = WHITE
    white_card.line.color.rgb = BORDER_GRAY
    white_card.line.width = Pt(1)
    white_card.adjustments[0] = 0.03

    # Ícones profissionais (grid 2x2)
    icon_size = Inches(0.4)
    icon_y = Inches(1.0)
    icon_gap = Inches(0.65)
    icon_start_x = Inches(7.8)

    icons = ["gear", "wrench", "chart", "car"]
    for i, icon_name in enumerate(icons):
        ix = icon_start_x + i * icon_gap
        # Círculo de fundo para o ícone
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            ix, icon_y,
            Inches(0.5), Inches(0.5)
        )
        circle.fill.solid()
        circle.fill.fore_color.rgb = EDENRED_RED
        circle.line.fill.background()
        # Ícone PNG branco por cima
        _add_icon(slide, icon_name, ix + Inches(0.05), icon_y + Inches(0.05), icon_size)

    # Barra vermelha decorativa
    h_accent = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(7.8), Inches(1.8),
        Inches(1.2), Pt(4)
    )
    h_accent.fill.solid()
    h_accent.fill.fore_color.rgb = EDENRED_RED
    h_accent.line.fill.background()
    h_accent.adjustments[0] = 0.5

    # Título do painel
    add_text_box(
        slide, Inches(7.8), Inches(2.1),
        Inches(5.0), Inches(0.8),
        "Painel de Regulação\nInteligente",
        size=22, bold=True, color=EDENRED_DARK
    )

    # Data de geração
    now = datetime.now().strftime("%d/%m/%Y às %H:%M")
    add_text_box(
        slide, Inches(7.8), Inches(3.2),
        Inches(5.0), Inches(0.4),
        f"Gerado em {now}",
        size=11, color=TEXT_MUTED
    )

    # Badge "Edenred Fleet Solutions"
    badge = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(7.8), Inches(4.0),
        Inches(2.8), Inches(0.35)
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = BG_LIGHT
    badge.line.fill.background()
    badge.adjustments[0] = 0.5

    add_text_box(
        slide, Inches(7.85), Inches(4.02),
        Inches(2.7), Inches(0.3),
        "Edenred Fleet Solutions",
        size=9, bold=True, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER
    )

    # ============================================
    # RODAPÉ
    # ============================================

    # Barra vermelha fina
    footer_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(6.7),
        SLIDE_WIDTH, Pt(2)
    )
    footer_bar.fill.solid()
    footer_bar.fill.fore_color.rgb = EDENRED_RED
    footer_bar.line.fill.background()

    # Logo Edenred (rodapé esquerdo, maior)
    if os.path.exists(LOGO_PATH):
        slide.shapes.add_picture(
            LOGO_PATH,
            Inches(0.5), Inches(6.85),
            width=Inches(1.6)
        )

    # Tagline "Mover, para o bem."
    add_text_box(
        slide, Inches(10.3), Inches(6.95),
        Inches(2.7), Inches(0.4),
        "Mover, para o bem.",
        size=10, bold=False, color=TEXT_MUTED, alignment=PP_ALIGN.RIGHT
    )
