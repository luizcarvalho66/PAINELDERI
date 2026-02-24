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
INDIGO = '#6366F1'
INDIGO_LIGHT = 'rgba(99,102,241,0.12)'
BACKGROUND = '#F8FAFC'
CARD_BG = '#FFFFFF'
GRID_COLOR = 'rgba(0,0,0,0.03)'
TEXT_DARK = '#1e293b'
TEXT_MUTED = '#64748b'
GREY_LINE = '#94a3b8'
GREY_AREA = 'rgba(148,163,184,0.12)'

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
        bgcolor="rgba(255,255,255,0.95)", 
        font_size=13, 
        font_family="Ubuntu", 
        font_color=TEXT_DARK,
        bordercolor="rgba(0,0,0,0.05)"
    ),
    margin=dict(l=50, r=20, t=50, b=40),
)

AXIS_STYLE = dict(
    showgrid=True, 
    gridcolor=GRID_COLOR, 
    zeroline=False, 
    tickfont=dict(color=TEXT_MUTED, size=11, family="Inter, Ubuntu, sans-serif"),
    linecolor=GRID_COLOR
)

def create_ri_geral_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates the main 'Evolução RI Geral' chart.
    """
    fig = go.Figure()
    
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
    
    # Formatar economia
    econ_text = [f"R$ {v/1e6:,.1f}M" for v in economia_total]
    
    # Período real (ex: "01 a 24 de Fevereiro 2026")
    periodo_text = []
    if 'data_min_corr' in df.columns and 'data_max_corr' in df.columns:
        for _, row in df.iterrows():
            try:
                # O Pandas lida bem com NaT no isna() vazio e parsing
                if pd.isna(row['data_min_corr']) or pd.isna(row['data_max_corr']):
                    periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else str(row.get('x_label', '')))
                    continue
                    
                d_min = pd.to_datetime(row['data_min_corr'])
                d_max = pd.to_datetime(row['data_max_corr'])
                mes_nome = _MESES_PTBR.get(d_min.month, d_min.strftime('%B'))
                
                if d_min.month == d_max.month and d_min.year == d_max.year:
                    # Mesmo mês: "01 a 15 de Fevereiro 2026"
                    periodo_text.append(f"{d_min.day:02d} a {d_max.day:02d} de {mes_nome} {d_min.year}")
                else:
                    # Meses diferentes (ex: semanas na virada): "28 Fev a 05 Mar"
                    mes_max = _MESES_PTBR.get(d_max.month, d_max.strftime('%B'))
                    periodo_text.append(f"{d_min.day:02d} {mes_nome[:3]} a {d_max.day:02d} {mes_max[:3]} {d_max.year}")
            except Exception as e:
                # Fallback em caso de erro bizarro de datetime
                periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else str(row.get('x_label', '')))
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

    fig.add_trace(go.Scatter(
        x=x_data, 
        y=y_data, 
        mode='lines+markers', 
        marker=dict(
            size=marker_sizes, 
            color=EDENRED_RED, 
            symbol='circle', 
            opacity=marker_opacities,
            line=dict(color='white', width=2)
        ), 
        fill='tozeroy',
        fillcolor='rgba(226,6,19,0.08)', 
        line=dict(color=EDENRED_RED, width=2.5, shape='spline'),
        name='RI Geral',
        customdata=list(zip(
            periodo_text,
            econ_text,
            os_total,
            os_corr,
            os_prev,
            (df['ri_corretiva'] * 100).round(2),
            (df['ri_preventiva'] * 100).round(2),
            parcial_text
        )),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '<span style="color:#e20613">%{customdata[7]}</span><br>'
            '───────────────<br>'
            '<span style="color:#64748b">RI Geral</span><br>'
            '<b style="font-size:1.1em">%{y:.2f}%</b><br><br>'
            '<span style="color:#e20613">●</span> Corretiva: <b>%{customdata[5]:.2f}%</b><br>'
            '<span style="color:#6366f1">●</span> Preventiva: <b>%{customdata[6]:.2f}%</b><br>'
            '───────────────<br>'
            '<span style="color:#64748b">Economia Gerada</span><br>'
            '<b style="color:#10b981">%{customdata[1]}</b><br>'
            '<span style="color:#64748b">OS Total: %{customdata[2]:,}</span><br>'
            '<span style="color:#94a3b8">Corr: %{customdata[3]:,} · Prev: %{customdata[4]:,}</span>'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Evolução RI Geral</b>", font=dict(size=18, color=TEXT_DARK)),
        xaxis=dict(**AXIS_STYLE), 
        yaxis=dict(
            **AXIS_STYLE, 
            ticksuffix="%", 
            rangemode="tozero"
        ),
        height=380
    )
    
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
    periodo_text = []
    if 'data_min_corr' in df.columns and 'data_max_corr' in df.columns:
        for _, row in df.iterrows():
            try:
                if pd.isna(row['data_min_corr']) or pd.isna(row['data_max_corr']):
                    periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else str(row.get('x_label', '')))
                    continue
                d_min = pd.to_datetime(row['data_min_corr'])
                d_max = pd.to_datetime(row['data_max_corr'])
                mes_nome = _MESES_PTBR.get(d_min.month, d_min.strftime('%B'))
                if d_min.month == d_max.month and d_min.year == d_max.year:
                    periodo_text.append(f"{d_min.day:02d} a {d_max.day:02d} de {mes_nome} {d_min.year}")
                else:
                    mes_max = _MESES_PTBR.get(d_max.month, d_max.strftime('%B'))
                    periodo_text.append(f"{d_min.day:02d} {mes_nome[:3]} a {d_max.day:02d} {mes_max[:3]} {d_max.year}")
            except:
                periodo_text.append(_format_mes_ptbr([row['mes_ref']])[0] if 'mes_ref' in df.columns else str(row.get('x_label', '')))
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
        marker=dict(
            size=marker_size, 
            color=INDIGO, 
            symbol='circle',
            line=dict(color='white', width=2)
        ), 
        fill='tozeroy',
        fillcolor=INDIGO_LIGHT, 
        line=dict(color=INDIGO, width=2.5, shape='spline'), 
        name='Preventiva',
        customdata=list(zip(periodo_text, os_prev)),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '───────────────<br>'
            '<span style="color:#64748b">RI Preventiva</span><br>'
            '<b style="color:#6366f1;font-size:1.1em">%{y:.2f}%</b><br>'
            '<span style="color:#94a3b8">OS Analisadas: %{customdata[1]:,}</span>'
            '<extra></extra>'
        )
    ))

    # Trace 2: Corretiva
    fig.add_trace(go.Scatter(
        x=x_data, 
        y=df['ri_corretiva'] * 100, 
        mode='lines+markers', 
        marker=dict(
            size=marker_size, 
            color=EDENRED_RED, 
            symbol='circle',
            line=dict(color='white', width=2)
        ),
        fill='tozeroy',
        fillcolor='rgba(226,6,19,0.05)',
        line=dict(color=EDENRED_RED, width=2.5, shape='spline'), 
        name='Corretiva',
        customdata=list(zip(periodo_text, os_corr)),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            '───────────────<br>'
            '<span style="color:#64748b">RI Corretiva</span><br>'
            '<b style="color:#e20613;font-size:1.1em">%{y:.2f}%</b><br>'
            '<span style="color:#94a3b8">OS Analisadas: %{customdata[1]:,}</span>'
            '<extra></extra>'
        )
    ))

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="<b>Corretiva vs Preventiva</b>", font=dict(size=16, color=TEXT_DARK, family="Inter, Ubuntu, sans-serif")),
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
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=12, color=TEXT_MUTED, family="Inter, Ubuntu, sans-serif")
        ),
        height=320
    )

    return fig
