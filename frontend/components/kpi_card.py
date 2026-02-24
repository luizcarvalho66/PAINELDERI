# -*- coding: utf-8 -*-
"""
KPI Card Component - Executive Premium Redesign V2

Design Pattern: Clean Executive with Accent Bar
- Indicator de tendência (↑ ↓)
- Barra de cor na base para identificação visual
- Tipografia impactante
- Micro-animações de hover

Author: Frontend Specialist Agent
"""
from dash import html
import dash_bootstrap_components as dbc

# Paleta Edenred
EDENRED_RED = "#E20613"
SUCCESS_GREEN = "#10B981"
WARNING_AMBER = "#F59E0B"
INFO_BLUE = "#3B82F6"
NEUTRAL_SLATE = "#64748B"


def render_kpi_card(
    title: str,
    value: str,
    subtext: str,
    icon_class: str = "bi-bar-chart",
    color_class: str = "text-dark",
    trend_value: float = None,  
    trend_label: str = None,    
    group: str = None,          
) -> html.Div:
    """
    Novo Layout Exclusivo (V4) - Ultra Minimalista e Premium
    Sem bordas duras, focando na tipografia gigantesca, "watermark" de fundo, e labels em pílula.
    """
    
    # 1. Mapeamento de Cores
    accent_color = NEUTRAL_SLATE
    if "danger" in color_class or "red" in color_class:
        accent_color = EDENRED_RED
    elif "success" in color_class or "green" in color_class:
        accent_color = SUCCESS_GREEN
    elif "primary" in color_class or "blue" in color_class:
        accent_color = INFO_BLUE
    elif "warning" in color_class or "yellow" in color_class:
        accent_color = WARNING_AMBER
    elif "info" in color_class:
        accent_color = INFO_BLUE

    # 2. Indicador de Tendência (Super delicado)
    trend_indicator = None
    if trend_value is not None:
        is_positive = trend_value >= 0
        trend_icon = "bi-arrow-up-right" if is_positive else "bi-arrow-down-right"
        trend_color = SUCCESS_GREEN if is_positive else EDENRED_RED
        
        # Cria uma pílula minúscula ao lado do subtexto
        trend_indicator = html.Span([
            html.I(className=trend_icon, style={"marginRight": "3px", "fontSize": "0.75rem"}),
            html.Span(f"{abs(trend_value):.1f}%", style={"fontWeight": "600", "fontSize": "0.75rem"})
        ], style={
            "color": trend_color,
            "backgroundColor": f"{trend_color}12",
            "padding": "2px 8px",
            "borderRadius": "4px",
            "marginLeft": "8px"
        })

    # 3. Construção do Layout Premium
    return html.Div([
        
        # A. Ícone Gigante de Fundo (Watermark)
        html.I(className=icon_class, style={
            "position": "absolute",
            "right": "-10px",
            "bottom": "-15px",
            "fontSize": "8rem",
            "color": accent_color,
            "opacity": "0.03",
            "zIndex": "0",
            "transform": "rotate(-10deg)",
            "pointerEvents": "none"
        }),
        
        # Container do conteúdo real (Z-index superior)
        html.Div([
            
            # HEADER: Pílula elegante com ícone e título
            html.Div([
                html.Div([
                    html.I(className=icon_class, style={"fontSize": "0.80rem", "marginRight": "6px", "color": accent_color}),
                    html.Span(title.upper(), style={
                        "fontSize": "0.65rem",
                        "fontWeight": "700",
                        "color": "#64748B",
                        "letterSpacing": "1.2px"
                    })
                ], style={
                    "display": "inline-flex",
                    "alignItems": "center",
                    "padding": "4px 10px 4px 6px",
                    "borderRadius": "8px",
                    "backgroundColor": "#F8FAFC",
                    "border": "1px solid #E2E8F0"
                })
            ], style={"marginBottom": "16px"}),
            
            # MIDDLE: Valor do KPI - Monstruoso e Impactante (responsivo)
            html.Div(value, style={
                "fontSize": "clamp(1.6rem, 2vw, 2.4rem)",
                "fontWeight": "800",
                "color": "#0F172A",
                "fontFamily": "Ubuntu, sans-serif",
                "letterSpacing": "-1px",
                "lineHeight": "1",
                "marginBottom": "12px",
                "whiteSpace": "nowrap"
            }),
            
            # BOTTOM: Subtexto integrado com a tendência
            html.Div([
                html.Small(subtext, style={
                    "color": "#94A3B8",
                    "fontSize": "0.80rem",
                    "fontWeight": "500"
                }),
                trend_indicator if trend_indicator else None
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginTop": "auto" # Push para o final
            })
            
        ], style={"position": "relative", "zIndex": "1", "display": "flex", "flexDirection": "column", "height": "100%"})
        
    ], className="kpi-card-premium h-100", style={
        "backgroundColor": "white",
        "borderRadius": "16px",
        "padding": "1.5rem",
        "border": "1px solid rgba(226, 232, 240, 0.8)",
        "boxShadow": "0 2px 10px rgba(0, 0, 0, 0.02)",
        "transition": "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        "position": "relative",
        "overflow": "hidden",
        "minHeight": "145px",
        "display": "flex",
        "flexDirection": "column",
        "height": "100%"
    })


def render_kpi_card_compact(
    title: str,
    value: str,
    icon_class: str = "bi-bar-chart",
    color_class: str = "text-dark"
) -> html.Div:
    """
    Versão compacta do KPI card para uso em grids menores.
    """
    accent_color = NEUTRAL_SLATE
    if "danger" in color_class:
        accent_color = EDENRED_RED
    elif "success" in color_class:
        accent_color = SUCCESS_GREEN
    elif "primary" in color_class:
        accent_color = INFO_BLUE

    return html.Div([
        html.Div([
            html.I(className=icon_class, style={
                "color": accent_color,
                "fontSize": "1rem",
                "marginRight": "8px"
            }),
            html.Span(title, style={
                "fontSize": "0.75rem",
                "fontWeight": "600",
                "color": "#64748B",
                "textTransform": "uppercase",
                "letterSpacing": "0.5px"
            })
        ], className="d-flex align-items-center mb-1"),
        html.Div(value, style={
            "fontSize": "1.4rem",
            "fontWeight": "700",
            "color": "#0F172A"
        })
    ], style={
        "backgroundColor": "white",
        "borderRadius": "10px",
        "padding": "1rem 1.25rem",
        "borderLeft": f"3px solid {accent_color}"
    })
