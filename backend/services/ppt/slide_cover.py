# -*- coding: utf-8 -*-
"""
Slide 1 — Capa executiva estilo Edenred.

Design split-screen com border radius, ícone profissional,
círculo vermelho gigante e posicionamento perfeito.
"""

import os
from datetime import datetime
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

from .config import (
    WHITE, EDENRED_RED, EDENRED_RED_DARK, EDENRED_CORAL,
    EDENRED_DARK, TEXT_MUTED, BG_LIGHT, BORDER_GRAY,
    SLIDE_WIDTH, LOGO_PATH, ICONS_DIR, COVER_PATH, MINILOGO_PATH,
    SLIDE_HEIGHT
)
from .helpers import add_text_box


def _add_icon(slide, icon_name, left, top, size=Inches(0.45)):
    """Adiciona ícone PNG ao slide se existir."""
    path = os.path.join(ICONS_DIR, f"{icon_name}.png")
    if os.path.exists(path):
        slide.shapes.add_picture(path, left, top, width=size, height=size)

def _add_svg_fallback_icon(slide, icon_name, left, top, size=Inches(0.45)):
    """Se não tiver PNG, tenta SVG."""
    pass


def build_slide_cover(prs):
    """Capa executiva com foto arredondada e círculo vermelho gigante."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Fundo Branco
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    # Dimensões da composição unificada
    margin_x = Inches(1.0)
    img_top = Inches(0.8)
    img_height = Inches(5.9)
    img_width = Inches(9.5) # Imagem bem larga para o círculo cortar ela no meio

    # ============================================
    # BLOCO IMAGEM ESQUERDA (com border radius suave)
    # ============================================
    img_left = margin_x

    if os.path.exists(COVER_PATH):
        pic = slide.shapes.add_picture(COVER_PATH, img_left, img_top, img_width, img_height)
        spPr = pic.element.spPr
        prstGeom = spPr.find(qn('a:prstGeom'))
        if prstGeom is not None:
            prstGeom.set('prst', 'roundRect')
            # 20000 = radius 20% nas bordas (cantos arredondados, não pílula total)
            avLst = parse_xml('<a:avLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:gd name="adj" fmla="val 20000"/></a:avLst>')
            prstGeom.append(avLst)
    else:
        # Fallback se não tiver imagem
        red_block = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            img_left, img_top,
            img_width, img_height
        )
        fill = red_block.fill
        fill.solid()
        fill.fore_color.rgb = TEXT_MUTED
        red_block.line.fill.background()
        red_block.adjustments[0] = 0.20

    # ============================================
    # LADO DIREITO — Círculo Vermelho Gigante (Cortando a imagem)
    # ============================================
    circle_radius = Inches(3.0)  # Diametro 6" — proporcional ao slide 7.5"
    center_y = SLIDE_HEIGHT / 2
    # Círculo com centro mais pra direita, sobrepondo parcialmente a imagem
    center_x = SLIDE_WIDTH - Inches(3.8)

    circle_left = center_x - circle_radius
    circle_top = center_y - circle_radius

    red_circle = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        circle_left, circle_top,
        circle_radius * 2, circle_radius * 2
    )
    red_circle.fill.solid()
    red_circle.fill.fore_color.rgb = EDENRED_RED
    red_circle.line.fill.background()

    # ============================================
    # CONTEÚDO (DENTRO DO CÍRCULO)
    # ============================================
    # Ícone no topo do círculo
    icon_size = Inches(0.55)
    icon_left = center_x - (icon_size / 2)
    icon_top = center_y - Inches(1.1)
    _add_icon(slide, "wrench", icon_left, icon_top, icon_size)

    # Textos centralizados no círculo
    text_width = Inches(4.5)
    text_left = center_x - (text_width / 2)

    # MTBF
    add_text_box(
        slide, text_left, center_y - Inches(0.35),
        text_width, Inches(0.7),
        "MTBF",
        size=40, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER
    )

    # Análise Crítica
    add_text_box(
        slide, text_left, center_y + Inches(0.25),
        text_width, Inches(0.5),
        "Análise Crítica",
        size=30, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER
    )

    # ============================================
    # RODAPÉ
    # ============================================
    
    # Logo Edenred (esquerda)
    if os.path.exists(LOGO_PATH):
        # A logo original costuma ser bem grande, redimensionada para a altura correta
        # Vamos usar um tamanho padrão: h=0.4
        slide.shapes.add_picture(
            LOGO_PATH,
            margin_x, Inches(6.8),
            height=Inches(0.4)
        )

    # Tagline (direita)
    add_text_box(
        slide, Inches(9.8), Inches(6.8),
        Inches(2.5), Inches(0.4),
        "Mover, para o bem.",
        size=11, bold=True, color=RGBColor(0x1A, 0x1A, 0x2E), alignment=PP_ALIGN.RIGHT
    )
