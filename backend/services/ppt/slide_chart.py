# -*- coding: utf-8 -*-
"""
Slides 3-4 — Charts Plotly como imagem + helper de conversão.
"""

import io
import os
import tempfile
import subprocess

from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE

from .config import WHITE, BORDER_GRAY, FONT_FAMILY, TEXT_MUTED
from .helpers import add_rounded_rect, add_content_header, add_footer_logo


def fig_to_image_bytes(fig, width=1100, height=520):
    """Converte Plotly Figure para bytes PNG.

    Usa subprocess isolado para evitar conflito asyncio do
    kaleido v1.x + Python 3.14 dentro do Dash.
    """
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family=f"{FONT_FAMILY}, sans-serif"),
    )

    fig_json = fig.to_json()
    json_fd, json_path = tempfile.mkstemp(suffix='.json')
    png_fd, png_path = tempfile.mkstemp(suffix='.png')
    os.close(json_fd)
    os.close(png_fd)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(fig_json)

        script = f"""
import plotly.io as pio
import json

with open(r'{json_path}', 'r', encoding='utf-8') as f:
    fig_dict = json.load(f)

fig = pio.from_json(json.dumps(fig_dict))
fig.write_image(r'{png_path}', format='png', width={width}, height={height}, scale=2)
"""
        result = subprocess.run(
            ['python', '-c', script],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            raise RuntimeError(f"Chart export failed: {result.stderr[:500]}")

        with open(png_path, 'rb') as f:
            return f.read()

    finally:
        for p in (json_path, png_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def build_slide_chart(prs, fig, title: str, df_30d=None, ofensores=None):
    """Slide com chart Plotly como imagem."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    if "Geral" in title:
        add_content_header(slide, title + "  |  Últimos 30 Dias")
    else:
        add_content_header(slide, title)

    # Card branco com borda para o gráfico (agora ocupa apenas a parte esquerda/centro)
    add_rounded_rect(
        slide, Inches(0.4), Inches(1.2),
        Inches(7.7), Inches(5.6), # Reduzida a largura de 8.5 para 7.7
        WHITE, BORDER_GRAY, radius=0.03
    )

    # Chart como imagem (menor largura e altura para dar espaço ao painel lateral)
    img_bytes = fig_to_image_bytes(fig, width=700, height=450) # width reduzido de 750 para 700
    img_stream = io.BytesIO(img_bytes)

    slide.shapes.add_picture(
        img_stream,
        Inches(0.5), Inches(1.8), # Centralizado no card novo
        width=Inches(7.5) # Chart impresso mais estreito
    )

    # Adicionar o Painel de Síntese Executiva na Direita
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Pt
    from .config import LIGHT_GRAY, EDENRED_RED, TEXT_DARK, TEXT_MUTED

    # Fundo do painel de síntese (Movido para X=8.4, Largura = 4.4" para caber mais texto)
    add_rounded_rect(
        slide, Inches(8.4), Inches(1.2),
        Inches(4.4), Inches(5.6),
        LIGHT_GRAY, BORDER_GRAY, radius=0.04
    )

    # Título do painel
    shape_title = slide.shapes.add_textbox(Inches(8.6), Inches(1.4), Inches(4.0), Inches(0.4))
    tf_title = shape_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "🚨  TOP 3 ESTABELECIMENTOS" if "Geral" in title else "SÍNTESE EXECUTIVA"
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(11)
    p_title.font.bold = True
    p_title.font.color.rgb = EDENRED_RED

    # Renderizar Cards de Ofensores ou Placeholder
    if "Geral" in title and ofensores and len(ofensores) > 0:
        from .config import DANGER_BG, WARNING_BG, CARD_RED, CARD_AMBER

        # Subtítulo explicativo
        p_sub = tf_title.add_paragraph()
        p_sub.text = "Estabelecimentos ofensores do período analisado."
        p_sub.font.name = FONT_FAMILY
        p_sub.font.size = Pt(8)
        p_sub.font.color.rgb = TEXT_MUTED

        card_top = 2.1  # Inches - posição inicial do primeiro card deslocado para caber o subtitulo
        card_colors = [
            (DANGER_BG, CARD_RED),     # 1º pior - vermelho
            (WARNING_BG, CARD_AMBER),  # 2º - amarelo
            (LIGHT_GRAY, TEXT_DARK),   # 3º - neutro
        ]

        for i, ofen in enumerate(ofensores[:3]):
            bg_color, accent = card_colors[i] if i < len(card_colors) else card_colors[-1]

            # Card background (Largura aumentada de 3.0 para 4.1)
            add_rounded_rect(
                slide, Inches(8.55), Inches(card_top),
                Inches(4.1), Inches(1.4),
                bg_color, BORDER_GRAY, radius=0.03
            )

            # Barra lateral de acento (4px indica severidade)
            bar = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(8.55), Inches(card_top),
                Inches(0.06), Inches(1.4)
            )
            bar.fill.solid()
            bar.fill.fore_color.rgb = accent
            bar.line.fill.background()

            # Nome do estabelecimento (Largura = 3.8 para caber nomes grandes)
            nome_box = slide.shapes.add_textbox(
                Inches(8.75), Inches(card_top + 0.05),
                Inches(3.8), Inches(0.35)
            )
            tf_nome = nome_box.text_frame
            tf_nome.word_wrap = True
            p_nome = tf_nome.paragraphs[0]
            p_nome.text = f"{i+1}º {ofen['nome']}"
            p_nome.font.name = FONT_FAMILY
            p_nome.font.size = Pt(9)
            p_nome.font.bold = True
            p_nome.font.color.rgb = TEXT_DARK

            # Valor de ofensividade em R$ 
            vol_solic = ofen.get('volume_solicitado', 0)
            economia = ofen.get('economia', 0)
            ofensividade = vol_solic - economia  # Quanto passou sem economia

            valor_box = slide.shapes.add_textbox(
                Inches(8.75), Inches(card_top + 0.38),
                Inches(3.8), Inches(0.35)
            )
            tf_val = valor_box.text_frame
            tf_val.word_wrap = True
            p_val = tf_val.paragraphs[0]
            p_val.text = f"R$ {ofensividade/1000:,.0f}k"
            p_val.font.name = FONT_FAMILY
            p_val.font.size = Pt(18)
            p_val.font.bold = True
            p_val.font.color.rgb = accent

            # Linha de detalhe (RI% | Qtd OS | Economia)
            det_box = slide.shapes.add_textbox(
                Inches(8.75), Inches(card_top + 0.75),
                Inches(3.8), Inches(0.7)
            )
            tf_det = det_box.text_frame
            tf_det.word_wrap = True
            p_det = tf_det.paragraphs[0]
            p_det.text = f"RI: {ofen['ri_percent']:.1f}%  ·  {ofen['qtd_os']} OS"
            p_det.font.name = FONT_FAMILY
            p_det.font.size = Pt(8)
            p_det.font.color.rgb = TEXT_DARK

            # Linha de valores $
            p_det2 = tf_det.add_paragraph()
            vol_aprov = ofen.get('volume_aprovado', 0)
            p_det2.text = f"Solicitado: R${vol_solic/1000:,.0f}k · Economizado: R${economia/1000:,.0f}k"
            p_det2.font.name = FONT_FAMILY
            p_det2.font.size = Pt(7)
            p_det2.font.color.rgb = TEXT_DARK

            card_top += 1.55  # Espaço entre cards menor já que o card abaixou a altura (1.55)
    else:
        # Placeholder genérico
        shape_text = slide.shapes.add_textbox(Inches(8.6), Inches(1.9), Inches(4.0), Inches(4.5))
        tf_text = shape_text.text_frame
        tf_text.word_wrap = True
        p_text = tf_text.paragraphs[0]
        p_text.text = "Sem dados de estabelecimentos ofensores para o período analisado."
        p_text.font.name = FONT_FAMILY
        p_text.font.size = Pt(11)
        p_text.font.color.rgb = TEXT_DARK

    add_footer_logo(slide)
