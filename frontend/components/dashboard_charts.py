# -*- coding: utf-8 -*-
"""
Dashboard Charts - Specialized Plotting Logic

Implements strict Edenred branding and visibility rules:
- Markers for all line charts (visibility of low values).
- Hover precision (2 decimal places).
- Dynamic Y-Axis (tozero).
- Edenred Color Palette.

Author: AI Agent (Refactoring)
"""

import plotly.graph_objects as go
import pandas as pd

# --- CONSTANTS & STYLES ---
EDENRED_RED = '#E20613'
EDENRED_RED_LIGHT = 'rgba(226,6,19,0.15)'
BACKGROUND = '#F8FAFC'
CARD_BG = '#FFFFFF'
GRID_COLOR = 'rgba(0,0,0,0.06)'
TEXT_DARK = '#1e293b'
TEXT_MUTED = '#64748b'
GREY_LINE = '#94a3b8'
GREY_AREA = 'rgba(148,163,184,0.12)'

# Base Layout adhering to chart_plotter.md
BASE_LAYOUT = dict(
    font=dict(family="Ubuntu, sans-serif"),
    plot_bgcolor=CARD_BG,
    paper_bgcolor=CARD_BG,
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor=CARD_BG, 
        font_size=13, 
        font_family="Ubuntu", 
        font_color=TEXT_DARK,
        bordercolor=GRID_COLOR
    ),
    margin=dict(l=50, r=20, t=50, b=40),
    # Height is controlled by container, can be unset or default
)

AXIS_STYLE = dict(
    showgrid=True, 
    gridcolor=GRID_COLOR, 
    zeroline=False, 
    tickfont=dict(color=TEXT_MUTED),
    linecolor=GRID_COLOR
)

def create_ri_geral_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates the main 'Evolução RI Geral' chart.
    """
    fig = go.Figure()
    
    # Data Preparation (Ensuring X is present - caller must guarantee 'x_label')
    x_data = df.get('x_label', [])
    y_data = df['ri_geral'] * 100 # Convert to percentage
    
    # Markers maiores quando há poucos pontos para garantir visibilidade
    marker_size = 10 if len(df) <= 3 else 6

    fig.add_trace(go.Scatter(
        x=x_data, 
        y=y_data, 
        mode='lines+markers', 
        marker=dict(size=marker_size, color=EDENRED_RED, symbol='circle'), 
        fill='tozeroy',
        fillcolor=EDENRED_RED_LIGHT, 
        line=dict(color=EDENRED_RED, width=3, shape='spline'),
        name='RI Geral', 
        hovertemplate='%{y:.2f}%<extra></extra>' # <extra> removes trace name from box
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Evolução RI Geral</b>", font=dict(size=18, color=TEXT_DARK)),
        xaxis=dict(**AXIS_STYLE), 
        yaxis=dict(
            **AXIS_STYLE, 
            ticksuffix="%", 
            rangemode="tozero" # CRITICAL for low values
        ),
        height=380
    )
    
    return fig


def create_comparative_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates the 'Corretiva vs Preventiva' comparative chart.
    """
    fig = go.Figure()
    
    x_data = df.get('x_label', [])
    
    # Markers maiores quando há poucos pontos
    marker_size = 10 if len(df) <= 3 else 6

    # Trace 1: Preventiva (Grey/Neutral)
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=df['ri_preventiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_size, color=GREY_LINE, symbol='circle'), 
        fill='tozeroy',
        fillcolor=GREY_AREA, 
        line=dict(color=GREY_LINE, width=3, shape='spline'), 
        name='Preventiva', 
        hovertemplate='Prev: %{y:.2f}%<extra></extra>'
    ))

    # Trace 2: Corretiva (Hero Color)
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=df['ri_corretiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_size, color=EDENRED_RED, symbol='circle'),
        line=dict(color=EDENRED_RED, width=3, shape='spline'), 
        name='Corretiva', 
        hovertemplate='Corr: %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Corretiva vs Preventiva</b>", font=dict(size=16, color=TEXT_DARK)),
        xaxis=dict(**AXIS_STYLE), 
        yaxis=dict(
            **AXIS_STYLE, 
            ticksuffix="%", 
            rangemode="tozero"
        ),
        legend=dict(
            orientation="h", 
            y=1.1, 
            x=0, 
            bgcolor='rgba(0,0,0,0)'
        ),
        height=250 # Smaller height for side stack
    )

    return fig
