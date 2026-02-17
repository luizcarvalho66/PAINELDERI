import plotly.graph_objects as go

def create_fugas_evolution_chart(data):
    """
    Creates a Premium Plotly figure for the 'Fugas de Preventiva' evolution chart.
    aligning with Vibe Coding & Edenred Branding.
    Includes fix for tooltips and color variation.
    """
    # 1. Colors & Style Constants
    # Gradient shades of Edenred Red for variation
    # From Darker to Lighter or varying styles
    RED_PALETTE = [
        '#E20613', # Standard
        '#C40511', # Darker
        '#F53642', # Lighter
        '#A1040D', # Even Darker
        '#FA6B74'  # Very Light
    ]
    SLATE_DARK = '#1e293b'
    SLATE_MUTED = '#64748b'
    GRID_COLOR = 'rgba(0,0,0,0.04)'
    FONT_FAMILY = "Ubuntu, sans-serif"

    # 2. Empty State Handling (Beautiful Fallback)
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
    
    # Generate colors cyclicly
    bar_colors = [RED_PALETTE[i % len(RED_PALETTE)] for i in range(len(x_val))]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_val,
        y=y_val,
        name='% Fuga',
        marker=dict(
            color=bar_colors,
            line=dict(width=0),
            # Rounded corners (compatible with newer Plotly, ignored if old)
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
        # Fixed Tooltip: Explicit font color to ensure visibility
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<span style='color: #64748b'>Taxa de Fuga:</span> "
            "<b>%{y:.2f}%</b>"
            "<extra></extra>"
        )
    ))

    # Calculate max Y for dynamic range padding (Prevent label clipping)
    max_y = max(y_val) if y_val else 100
    y_range_max = max_y * 1.2 # Add 20% headroom

    # 4. Premium Layout
    fig.update_layout(
        # Canvas & Font
        font=dict(family=FONT_FAMILY, color=SLATE_MUTED, size=12),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        
        # Sizing
        height=320, 
        margin=dict(l=20, r=20, t=90, b=30), # Increased top margin for labels
        bargap=0.3, 

        # Header
        title=dict(
            text="<span style='font-size: 16px; font-weight: bold; color: #1e293b;'>Evolução de Fugas (%)</span>",
            x=0,
            y=0.95
        ),

        # Axes
        xaxis=dict(
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
            range=[0, y_range_max], # Explicit padded range
            fixedrange=True
        ),

        # Interaction
        hovermode="x unified", # Standard "Edenred" interaction
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="rgba(0,0,0,0.1)",
            font_family=FONT_FAMILY,
            font_size=13,
            font_color=SLATE_DARK # Critical for visibility
        ),
        dragmode=False,
        showlegend=False
    )

    return fig
