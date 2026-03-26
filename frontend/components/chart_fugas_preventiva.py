import plotly.graph_objects as go

def create_fugas_evolution_chart(data):
    """
    Creates a Premium Plotly figure for the 'Fugas de Preventiva' evolution chart.
    aligning with Vibe Coding & Edenred Branding.
    Includes fix for tooltips and color variation.
    Suporta indicação visual de meses parciais (is_partial).
    """
    # 1. Colors & Style Constants
    RED_PALETTE = [
        '#E20613', # Standard
        '#C40511', # Darker
        '#F53642', # Lighter
        '#A1040D', # Even Darker
        '#FA6B74'  # Very Light
    ]
    PARTIAL_COLOR = 'rgba(226, 6, 19, 0.35)'  # Mês parcial: opacidade reduzida
    SLATE_DARK = '#1e293b'
    SLATE_MUTED = '#64748b'
    GRID_COLOR = 'rgba(0,0,0,0.04)'
    FONT_FAMILY = "Ubuntu, sans-serif"

    # 2. Empty State Handling
    if not data or not data.get('mes_ano'):
        fig = go.Figure()
        fig.add_annotation(
            text="<span style='font-size: 20px; font-weight: bold;'>⚠️ Sem dados Recentes</span><br><span style='font-size: 14px; color: #94a3b8;'>Não há fugas registradas para o período selecionado.</span>",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(family=FONT_FAMILY, color=SLATE_MUTED)
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig

    # 3. Data Preparation
    x_val = data['mes_ano']
    y_val = data['pct_fuga']
    is_partial = data.get('is_partial', [False] * len(x_val))
    dias_dados = data.get('dias_dados', [0] * len(x_val))
    
    # Cores: parcial usa cor com opacidade reduzida, completo usa paleta
    bar_colors = []
    x_labels = []
    for i in range(len(x_val)):
        if is_partial[i]:
            bar_colors.append(PARTIAL_COLOR)
        else:
            bar_colors.append(RED_PALETTE[i % len(RED_PALETTE)])
        
        # Labels com indicação de parcial
        if is_partial[i]:
            dias = dias_dados[i] if i < len(dias_dados) else 0
            x_labels.append(f"{x_val[i]}<br><span style='font-size:9px;color:#94a3b8'>({dias} dias)</span>")
        else:
            x_labels.append(x_val[i])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_labels,
        y=y_val,
        name='% Fuga',
        marker=dict(
            color=bar_colors,
            line=dict(
                width=[2 if p else 0 for p in is_partial],
                color=['#E20613' if p else 'rgba(0,0,0,0)' for p in is_partial],
            ),
            cornerradius=6
        ),
        text=[f"{v:.1f}%" for v in y_val],
        textposition='outside', 
        textfont=dict(
            family=FONT_FAMILY, 
            size=13, 
            color=SLATE_DARK, 
            weight='bold'
        ),
        customdata=list(zip(x_val, y_val)),
        hoverinfo="none"
    ))

    # Annotation para mês parcial
    for i in range(len(x_val)):
        if is_partial[i]:
            fig.add_annotation(
                x=x_labels[i],
                y=y_val[i] + (max(y_val) * 0.18 if y_val else 5),
                text="<b>PARCIAL</b>",
                showarrow=False,
                font=dict(family=FONT_FAMILY, size=9, color="#E20613"),
                bgcolor="rgba(226, 6, 19, 0.08)",
                bordercolor="#E20613",
                borderwidth=1,
                borderpad=3,
                opacity=0.9,
            )

    # Calculate max Y for dynamic range padding
    max_y = max(y_val) if y_val else 100
    y_range_max = max_y * 1.3  # 30% headroom (extra for annotation)

    # 4. Premium Layout
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=SLATE_MUTED, size=12),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        
        height=450, 
        margin=dict(l=20, r=20, t=90, b=50),
        bargap=0.3, 

        title=dict(
            text="<span style='font-size: 16px; font-weight: bold; color: #1e293b;'>Evolução de Fugas (%)</span>",
            x=0,
            y=0.95
        ),

        xaxis=dict(
            type='category',
            showgrid=False,
            showline=True,
            linecolor='#e2e8f0',
            tickfont=dict(color=SLATE_MUTED, size=12),
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR, 
            zeroline=False, 
            showticklabels=True,
            tickfont=dict(color=SLATE_MUTED, size=11),
            ticksuffix="%",
            range=[0, y_range_max],
            fixedrange=True
        ),

        dragmode=False,
        showlegend=False
    )

    return fig
