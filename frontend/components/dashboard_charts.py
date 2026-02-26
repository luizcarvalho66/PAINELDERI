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
BAR_COLOR = 'rgba(226, 6, 19, 0.18)' # Edenred Red com baixa opacidade para barras de fundo

# Meses em PT-BR
_MESES_PTBR = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

def _format_mes_ptbr(dt_series):
    """Formata série de datas para 'Mês YYYY' em PT-BR."""
    return [f"{_MESES_PTBR.get(d.month, d.strftime('%B'))} {d.year}" for d in dt_series]

# Base Layout adhering to chart_plotter.md
BASE_LAYOUT = dict(
    font=dict(family="Ubuntu, sans-serif"),
    plot_bgcolor=CARD_BG,
    paper_bgcolor=CARD_BG,
    hovermode="closest",
    hoverlabel=dict(
        bgcolor=CARD_BG, 
        font_size=13, 
        font_family="Ubuntu", 
        font_color=TEXT_DARK,
        bordercolor=GRID_COLOR
    ),
    margin=dict(l=50, r=20, t=50, b=40),
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
    Agora inclui um Eixo Duplo (Dual-Axis) com o Volume Solicitado em Barras ao fundo.
    """
    from plotly.subplots import make_subplots
    
    # Criar figura com eixo Y secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Data Preparation
    if 'x_label' in df.columns:
        x_data = df['x_label']
    elif 'mes_ref' in df.columns:
        x_data = _format_mes_ptbr(df['mes_ref'])
    else:
        x_data = list(range(len(df)))
    y_data = df['ri_geral'] * 100
    
    # Dados extras para tooltip
    economia_corr = df.get('sum_economia_pricing', pd.Series([0]*len(df)))
    economia_prev = df.get('sum_economia_pricing_prev', pd.Series([0]*len(df)))
    economia_total = economia_corr + economia_prev
    os_corr = df.get('qtd_corr', pd.Series([0]*len(df))).astype(int)
    os_prev = df.get('qtd_prev', pd.Series([0]*len(df))).astype(int)
    os_total = os_corr + os_prev
    
    # Volume Solicitado (Para as barras de fundo)
    vol_corr = df.get('sum_total_corr', pd.Series([0]*len(df)))
    vol_prev = df.get('sum_total_prev', pd.Series([0]*len(df)))
    vol_total = vol_corr + vol_prev
    vol_text = [f"R$ {v/1e6:,.1f}M" for v in vol_total]
    
    # Formatar economia
    econ_text = [f"R$ {v/1e6:,.1f}M" for v in economia_total]
    
    # Período real (ex: "01 a 24 de Fevereiro 2026")
    if 'data_min_corr' in df.columns and 'data_max_corr' in df.columns:
        periodo_text = []
        for _, row in df.iterrows():
            try:
                d_min = pd.to_datetime(row['data_min_corr'])
                d_max = pd.to_datetime(row['data_max_corr'])
                mes_nome = _MESES_PTBR.get(d_min.month, d_min.strftime('%B'))
                periodo_text.append(f"{d_min.day:02d} a {d_max.day:02d} de {mes_nome} {d_min.year}")
            except:
                periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else '')
    elif 'mes_ref' in df.columns:
        periodo_text = _format_mes_ptbr(df['mes_ref'])
    else:
        periodo_text = list(x_data)
    
    # Markers: maiores quando poucos pontos, menores se dados parciais
    marker_size = 10 if len(df) <= 3 else 6
    
    # Dados parciais: marker menor + opacidade
    parciais = df.get('dados_parciais', pd.Series([False]*len(df)))
    marker_sizes = [max(3, marker_size - 3) if p else marker_size for p in parciais]
    marker_opacities = [0.4 if p else 1.0 for p in parciais]
    
    # Texto de aviso para dados parciais
    parcial_text = ["(dados parciais)" if p else "" for p in parciais]

    # Trace 1: Barras de Volume Solicitado (Fundo / Eixo Secundário)
    fig.add_trace(go.Bar(
        x=x_data,
        y=vol_total,
        name='Volume Solicitado',
        marker_color=BAR_COLOR,
        marker_line_width=0,
        customdata=list(zip(periodo_text, vol_text)),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'Volume Solicitado: <b>%{customdata[1]}</b><br>'
            '<extra></extra>'
        )
    ), secondary_y=True)

    # Trace 2: Linha de RI Geral (Frente / Eixo Principal)
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=y_data, 
        mode='lines+markers', 
        marker=dict(size=marker_sizes, color=EDENRED_RED, symbol='circle', opacity=marker_opacities), 
        # Removendo area under curve (fill tozeroy) para não tampar as barras
        line=dict(color=EDENRED_RED, width=3, shape='spline'),
        name='RI Geral',
        customdata=list(zip(
            periodo_text,
            econ_text,
            os_total,
            os_corr,
            os_prev,
            (df['ri_corretiva'] * 100).round(2),
            (df['ri_preventiva'] * 100).round(2),
            parcial_text,
            vol_text # index 8
        )),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '%{customdata[7]}<br>'
            '―――――――――――――――――<br>'
            'RI Geral:  <b>%{y:.2f}%</b><br>'
            'Corretiva:  %{customdata[5]:.2f}%<br>'
            'Preventiva:  %{customdata[6]:.2f}%<br>'
            '―――――――――――――――――<br>'
            'Vol. Analisado: <b>%{customdata[8]}</b><br>'
            'Economia Gerada:  <b>%{customdata[1]}</b><br>'
            'OS Genuínas:  %{customdata[2]:,}<br>'
            '<extra></extra>'
        )
    ), secondary_y=False)

    # Merge AXIS_STYLE with specific yaxis overrides
    yaxis_config = AXIS_STYLE.copy()
    yaxis_config.update(dict(
        title=dict(text="RI (%)", font=dict(color=EDENRED_RED, size=12)),
        ticksuffix="%", 
        rangemode="tozero",
        showgrid=False # Sobrescreve AXIS_STYLE pra evitar grelha dupla
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Evolução RI Geral</b> vs. Vol. Solicitado", font=dict(size=18, color=TEXT_DARK)),
        xaxis=dict(**AXIS_STYLE), 
        yaxis=yaxis_config,
        yaxis2=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            title=dict(text="Vol. Solicitado (R$)", font=dict(color=TEXT_MUTED, size=12)),
            tickfont=dict(color=TEXT_MUTED),
            rangemode="tozero",
            showline=False
        ),
        height=380,
        showlegend=False
    )
    
    # Elevar a linha e abaixar as barras visualmente para que a linha flutue lá em cima.
    # Opcional mas comum em dual-axis
    max_ri = y_data.max() if not y_data.empty else 100
    if max_ri > 0: fig.update_yaxes(range=[0, max_ri * 1.5], secondary_y=False)
    
    max_vol = vol_total.max() if not vol_total.empty else 1000000
    if max_vol > 0: fig.update_yaxes(range=[0, max_vol * 1.5], secondary_y=True)
    
    return fig


def create_comparative_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates the 'Corretiva vs Preventiva' comparative chart.
    """
    fig = go.Figure()
    
    if 'x_label' in df.columns:
        x_data = df['x_label']
    elif 'mes_ref' in df.columns:
        x_data = _format_mes_ptbr(df['mes_ref'])
    else:
        x_data = list(range(len(df)))
    marker_size = 10 if len(df) <= 3 else 6
    
    # Período com dias
    if 'data_min_corr' in df.columns and 'data_max_corr' in df.columns:
        periodo_text = []
        for _, row in df.iterrows():
            try:
                d_min = pd.to_datetime(row['data_min_corr'])
                d_max = pd.to_datetime(row['data_max_corr'])
                mes_nome = _MESES_PTBR.get(d_min.month, d_min.strftime('%B'))
                periodo_text.append(f"{d_min.day:02d} a {d_max.day:02d} de {mes_nome} {d_min.year}")
            except:
                periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else '')
    elif 'mes_ref' in df.columns:
        periodo_text = _format_mes_ptbr(df['mes_ref'])
    else:
        periodo_text = list(x_data)
        
    os_prev = df.get('qtd_prev', pd.Series([0]*len(df))).astype(int)
    os_corr = df.get('qtd_corr', pd.Series([0]*len(df))).astype(int)

    # Trace 1: Preventiva
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=df['ri_preventiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_size, color=GREY_LINE, symbol='circle'), 
        fill='tozeroy',
        fillcolor=GREY_AREA, 
        line=dict(color=GREY_LINE, width=3, shape='spline'), 
        name='Preventiva',
        customdata=list(zip(periodo_text, os_prev)),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '―――――――――――――――――<br>'
            'RI Preventiva:  <b>%{y:.2f}%</b><br>'
            'OS Analisadas:  %{customdata[1]:,}'
            '<extra></extra>'
        )
    ))

    # Trace 2: Corretiva
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=df['ri_corretiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_size, color=EDENRED_RED, symbol='circle'),
        line=dict(color=EDENRED_RED, width=3, shape='spline'), 
        name='Corretiva',
        customdata=list(zip(periodo_text, os_corr)),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '―――――――――――――――――<br>'
            'RI Corretiva:  <b>%{y:.2f}%</b><br>'
            'OS Analisadas:  %{customdata[1]:,}'
            '<extra></extra>'
        )
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
        height=250
    )

    return fig
