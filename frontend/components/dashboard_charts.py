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
        bgcolor='rgba(15, 23, 42, 0.95)', # Dark Glassmorphism
        font_size=13, 
        font_family="Ubuntu", 
        font_color='#f8fafc',
        bordercolor='#E20613'
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

def create_ri_geral_chart(df: pd.DataFrame, granularidade: str = 'mensal', is_so_mode: bool = False) -> go.Figure:
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
    
    # Período real formatado conforme granularidade
    if 'mes_ref' in df.columns:
        periodo_text = []
        for d in pd.to_datetime(df['mes_ref']):
            mes_nome = _MESES_PTBR.get(d.month, d.strftime('%B'))
            if granularidade == 'semanal':
                d_end = d + pd.Timedelta(days=6)
                periodo_text.append(f"Sem. {d.day:02d}/{d.month:02d} a {d_end.day:02d}/{d_end.month:02d}")
            elif granularidade == 'quinzenal':
                d_end = d + pd.Timedelta(days=14)
                periodo_text.append(f"Qz. {d.day:02d}/{d.month:02d} a {d_end.day:02d}/{d_end.month:02d}")
            else:
                periodo_text.append(f"{mes_nome} {d.year}")
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
    
    # Cores das barras: parcial com opacidade menor
    bar_colors = ['rgba(226, 6, 19, 0.08)' if p else BAR_COLOR for p in parciais]
    
    # X labels: adicionar indicação "(parcial)" no mês corrente
    x_data_display = []
    for i, x in enumerate(x_data):
        if parciais.iloc[i] if hasattr(parciais, 'iloc') else (parciais[i] if i < len(parciais) else False):
            x_data_display.append(f"{x}<br><span style='font-size:9px;color:#E20613'>(parcial)</span>")
        else:
            x_data_display.append(str(x))

    # Unificar CustomData para ambos os traços garantindo que o callback do dcc.Tooltip 
    # não quebre independente se o hover for na barra ou na linha
    mode_label_list = ["SO" if is_so_mode else "RI"] * len(df)
    
    # Posição 1: Economia (RI) ou contagem de OS automáticas (SO)
    if is_so_mode:
        so_count_corr = df.get('so_count_corr', pd.Series([0]*len(df)))
        so_count_prev = df.get('so_count_prev', pd.Series([0]*len(df)))
        so_count_total = (so_count_corr + so_count_prev).astype(int)
        slot1_data = so_count_total  # posição 1 = contagem real de OS automáticas
    else:
        slot1_data = econ_text       # posição 1 = economia formatada (R$ XM)
    
    customdata_unificado = list(zip(
        periodo_text,                          # 0: Período
        slot1_data,                            # 1: Economia (RI) ou SO Count (SO)
        os_total,                              # 2: OS Totais
        os_corr,                               # 3: OS Corretiva
        os_prev,                               # 4: OS Preventiva
        (df['ri_corretiva'] * 100).round(2),   # 5: RI/SO Corretiva %
        (df['ri_preventiva'] * 100).round(2),  # 6: RI/SO Preventiva %
        parcial_text,                          # 7: Aviso Parcial
        vol_text,                              # 8: Vol. Solicitado
        y_data.round(2),                       # 9: RI/SO Geral % (y_data)
        mode_label_list,                       # 10: Modo (RI ou SO)
    ))

    # Trace 1: Barras de Volume Solicitado (Fundo / Eixo Secundário)
    fig.add_trace(go.Bar(
        x=x_data_display,
        y=vol_total,
        name='Volume Solicitado',
        marker_color=bar_colors,
        marker_line_width=[1 if p else 0 for p in parciais],
        marker_line_color=['rgba(226, 6, 19, 0.3)' if p else 'rgba(0,0,0,0)' for p in parciais],
        customdata=customdata_unificado,
        hoverinfo="none",
    ), secondary_y=True)

    # Trace 2: Linha de RI Geral (Frente / Eixo Principal)
    fig.add_trace(go.Scatter(
        x=x_data_display, 
        y=y_data, 
        mode='lines+markers', 
        marker=dict(size=marker_sizes, color=EDENRED_RED, symbol='circle', opacity=marker_opacities), 
        # Removendo area under curve (fill tozeroy) para não tampar as barras
        line=dict(color=EDENRED_RED, width=3, shape='spline'),
        name='RI Geral',
        customdata=customdata_unificado,
        hoverinfo="none",
    ), secondary_y=False)
    
    # Annotation para mês parcial
    for i in range(len(df)):
        is_partial = parciais.iloc[i] if hasattr(parciais, 'iloc') else (parciais[i] if i < len(parciais) else False)
        if is_partial:
            fig.add_annotation(
                x=x_data_display[i],
                y=float(y_data.iloc[i]) + (float(y_data.max()) * 0.12 if not y_data.empty else 5),
                text="<b>PARCIAL</b>",
                showarrow=False,
                font=dict(family="Ubuntu, sans-serif", size=9, color="#E20613"),
                bgcolor="rgba(226, 6, 19, 0.08)",
                bordercolor="#E20613",
                borderwidth=1,
                borderpad=3,
                opacity=0.9,
            )

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
        xaxis=dict(**AXIS_STYLE, type='category'), 
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


def create_comparative_chart(df: pd.DataFrame, granularidade: str = 'mensal', is_so_mode: bool = False) -> go.Figure:
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
    
    # Período formatado dinamicamente
    if 'mes_ref' in df.columns:
        periodo_text = []
        for d in pd.to_datetime(df['mes_ref']):
            mes_nome = _MESES_PTBR.get(d.month, d.strftime('%B'))
            if granularidade == 'semanal':
                d_end = d + pd.Timedelta(days=6)
                periodo_text.append(f"Sem. {d.day:02d}/{d.month:02d} a {d_end.day:02d}/{d_end.month:02d}")
            elif granularidade == 'quinzenal':
                d_end = d + pd.Timedelta(days=14)
                periodo_text.append(f"Qz. {d.day:02d}/{d.month:02d} a {d_end.day:02d}/{d_end.month:02d}")
            else:
                periodo_text.append(f"{mes_nome} {d.year}")
    else:
        periodo_text = list(x_data)
        
    os_prev = df.get('qtd_prev', pd.Series([0]*len(df))).astype(int)
    os_corr = df.get('qtd_corr', pd.Series([0]*len(df))).astype(int)
    
    # Dados parciais
    parciais = df.get('dados_parciais', pd.Series([False]*len(df)))
    marker_sizes = [max(3, marker_size - 3) if p else marker_size for p in parciais]
    marker_opacities = [0.4 if p else 1.0 for p in parciais]
    
    # X labels com indicação parcial
    x_data_display = []
    for i, x in enumerate(x_data):
        is_p = parciais.iloc[i] if hasattr(parciais, 'iloc') else (parciais[i] if i < len(parciais) else False)
        if is_p:
            x_data_display.append(f"{x}<br><span style='font-size:9px;color:#E20613'>(parcial)</span>")
        else:
            x_data_display.append(str(x))

    # Trace 1: Preventiva
    fig.add_trace(go.Scatter(
        x=x_data_display, 
        y=df['ri_preventiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_sizes, color=GREY_LINE, symbol='circle', opacity=marker_opacities), 
        fill='tozeroy',
        fillcolor=GREY_AREA, 
        line=dict(color=GREY_LINE, width=3, shape='spline'), 
        name='Preventiva',
        customdata=list(zip(periodo_text, os_prev)),
        hoverinfo="none",
    ))

    # Trace 2: Corretiva
    fig.add_trace(go.Scatter(
        x=x_data_display, 
        y=df['ri_corretiva'] * 100, 
        mode='lines+markers', 
        marker=dict(size=marker_sizes, color=EDENRED_RED, symbol='circle', opacity=marker_opacities),
        line=dict(color=EDENRED_RED, width=3, shape='spline'), 
        name='Corretiva',
        customdata=list(zip(periodo_text, os_corr)),
        hoverinfo="none",
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Corretiva vs Preventiva</b>", font=dict(size=16, color=TEXT_DARK)),
        xaxis=dict(**AXIS_STYLE, type='category'), 
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
