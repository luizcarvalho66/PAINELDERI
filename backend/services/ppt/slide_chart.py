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

from .config import WHITE, BORDER_GRAY, FONT_FAMILY
from .helpers import add_rounded_rect, add_gradient_header, add_footer_logo


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


def build_slide_chart(prs, fig, title: str):
    """Slide com chart Plotly como imagem."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    add_gradient_header(slide, title)

    # Card branco com borda para o gráfico
    add_rounded_rect(
        slide, Inches(0.6), Inches(1.2),
        Inches(12.1), Inches(5.6),
        WHITE, BORDER_GRAY, radius=0.02
    )

    # Chart como imagem
    img_bytes = fig_to_image_bytes(fig, width=1100, height=520)
    img_stream = io.BytesIO(img_bytes)

    slide.shapes.add_picture(
        img_stream,
        Inches(0.8), Inches(1.35),
        width=Inches(11.7)
    )

    add_footer_logo(slide)
