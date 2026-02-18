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
    trend_value: float = None,  # Nova prop: % de tendência (positivo = up, negativo = down)
    trend_label: str = None,    # Ex: "vs mês anterior"
) -> html.Div:
    """
    Renders a premium executive KPI card with optional trend indicator.
    
    Args:
        title: Título do KPI (ex: "Economia Real")
        value: Valor principal (ex: "R$ 102.916.118")
        subtext: Texto secundário (ex: "Valor economizado")
        icon_class: Classe do ícone Bootstrap (ex: "bi-currency-dollar")
        color_class: Classe de cor (text-danger, text-success, etc)
        trend_value: Percentual de tendência (opcional)
        trend_label: Label da tendência (opcional)
    """
    
    # Mapear cor de acento baseado na classe
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

    # Construir indicador de tendência se fornecido
    trend_indicator = None
    if trend_value is not None:
        is_positive = trend_value >= 0
        trend_icon = "bi-arrow-up-short" if is_positive else "bi-arrow-down-short"
        trend_color = SUCCESS_GREEN if is_positive else EDENRED_RED
        trend_text = f"{abs(trend_value):.1f}%"
        
        trend_indicator = html.Div([
            html.Div([
                html.I(className=trend_icon, style={
                    "fontSize": "1rem",
                    "color": trend_color,
                }),
                html.Span(trend_text, style={
                    "fontSize": "0.85rem",
                    "fontWeight": "600",
                    "color": trend_color,
                    "marginLeft": "2px"
                })
            ], className="d-flex align-items-center"),
            html.Small(trend_label or "", className="text-muted", style={
                "fontSize": "0.65rem",
                "display": "block",
                "marginTop": "-2px"
            }) if trend_label else None
        ], className="text-end")

    return html.Div([
        # Header: Título + Ícone
        html.Div([
            html.Span(title.upper(), style={
                "fontSize": "0.7rem",
                "fontWeight": "700",
                "color": "#94A3B8",
                "letterSpacing": "0.8px",
                "lineHeight": "1"
            }),
            html.Div([
                html.I(className=icon_class, style={
                    "color": accent_color,
                    "fontSize": "1.25rem",
                    "opacity": "0.9"
                })
            ], style={
                "width": "36px",
                "height": "36px",
                "borderRadius": "10px",
                "backgroundColor": f"{accent_color}12",  # 12 = ~7% opacity in hex
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center"
            })
        ], className="d-flex justify-content-between align-items-start mb-3"),
        
        # Main Value Row
        html.Div([
            # Número grande
            html.Div([
                html.Span(value, style={
                    "fontSize": "1.9rem",
                    "fontWeight": "800",
                    "color": "#0F172A",
                    "fontFamily": "Ubuntu, sans-serif",
                    "letterSpacing": "-0.5px",
                    "lineHeight": "1.1"
                })
            ]),
            # Trend (se existir)
            trend_indicator
        ], className="d-flex justify-content-between align-items-end mb-2"),
        
        # Subtext
        html.Div([
            html.Div(style={
                "width": "4px",
                "height": "4px",
                "borderRadius": "50%",
                "backgroundColor": accent_color,
                "marginRight": "8px",
                "flexShrink": "0"
            }),
            html.Small(subtext, style={
                "fontSize": "0.78rem",
                "fontWeight": "500",
                "color": "#64748B"
            })
        ], className="d-flex align-items-center"),
        
        # Accent Bar (bottom)
        html.Div(style={
            "position": "absolute",
            "bottom": "0",
            "left": "0",
            "right": "0",
            "height": "4px",
            "background": f"linear-gradient(90deg, {accent_color} 0%, {accent_color}40 100%)",
            "borderRadius": "0 0 12px 12px"
        })
        
    ], className="kpi-card-premium h-100", style={
        "backgroundColor": "white",
        "borderRadius": "14px",
        "padding": "1.25rem 1.5rem 1.5rem",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03)",
        "border": "1px solid rgba(226, 232, 240, 0.8)",
        "transition": "all 0.25s ease",
        "position": "relative",
        "overflow": "hidden",
        "minHeight": "140px"
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
