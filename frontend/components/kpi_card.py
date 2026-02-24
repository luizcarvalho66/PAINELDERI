# -*- coding: utf-8 -*-
"""
KPI Card Component - Executive Premium Redesign V3
Padronizado com o estilo macOS Glassmorphism do módulo Farol.

Author: Frontend Specialist Agent
"""
from dash import html
import dash_bootstrap_components as dbc


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
    Layout unificado usando estilo glassmorphism macOS.
    Idêntico à estrutura CSS do `create_farol_card`.
    """
    try:
        if not isinstance(value, str):
            value = str(value)

        # 1. Map Colors
        base_color = "#64748B"
        bg_light = "rgba(100, 116, 139, 0.1)"
        if "danger" in color_class or "red" in color_class:
            base_color = "#E20613" # EDENRED_RED
            bg_light = "rgba(226, 6, 19, 0.1)"
        elif "success" in color_class or "green" in color_class:
            base_color = "#10b981" # SUCCESS_GREEN
            bg_light = "rgba(16, 185, 129, 0.1)"
        elif "primary" in color_class or "blue" in color_class:
            base_color = "#3B82F6" # INFO_BLUE
            bg_light = "rgba(59, 130, 246, 0.1)"
        elif "warning" in color_class or "yellow" in color_class:
            base_color = "#f59e0b" # WARNING_AMBER
            bg_light = "rgba(245, 158, 11, 0.1)"
        elif "info" in color_class:
            base_color = "#6366f1" # INDIGO
            bg_light = "rgba(99, 102, 241, 0.1)"

        # 2. Trend Pill Element
        trend_element = None
        if trend_value is not None and isinstance(trend_value, (int, float)):
            is_positive = trend_value >= 0
            # Removemos "Corretiva" porque índice de RI Corretiva caindo é ruim (vermelho)
            is_negative_metric = "Ação" in title or "Atenção" in title or "Fugas" in title
            
            trend_icon = "bi bi-arrow-up-short" if is_positive else "bi bi-arrow-down-short"
            if is_negative_metric:
                trend_color = "#10b981" if not is_positive else "#E20613"
            else:
                trend_color = "#10b981" if is_positive else "#E20613"
                
            trend_element = html.Div([
                html.I(className=trend_icon, style={"fontSize": "1rem", "marginRight": "4px"}),
                f"{abs(trend_value):.1f}%"
            ], className="farol-trend-pill", style={
                "color": trend_color,
                "backgroundColor": f"{trend_color}15",
                "whiteSpace": "nowrap"
            })
        
        # 3. Subtext Element
        subtext_element = None
        if subtext:
             subtext_element = html.Span(subtext, style={
                 "color": "#94a3b8", 
                 "fontSize": "0.75rem", 
                 "fontWeight": "500", 
                 "marginRight": "8px"
             })

        # Alinhamos subtexto e pill juntos na base do card
        trend_container = html.Div(
            [subtext_element, trend_element] if trend_value is not None else [subtext_element], 
            className="d-flex align-items-center mt-auto pt-2 w-100 flex-wrap gap-2"
        )

        return html.Div([
            # Cabeçalho: Título + Ícone
            html.Div([
                html.H6(title, className="farol-card-title mb-0 pe-2", style={
                    "lineHeight": "1.2", 
                    "whiteSpace": "nowrap", 
                    "overflow": "hidden", 
                    "textOverflow": "ellipsis",
                    "fontSize": "clamp(0.65rem, 1vw, 0.75rem)"
                }),
                html.Div([
                    html.I(className=f"{icon_class} macos-card-icon", style={"color": base_color}),
                ], className="macos-card-icon-container flex-shrink-0", style={"backgroundColor": bg_light})
            ], className="d-flex justify-content-between align-items-center mb-3 w-100"),
            
            # Corpo: Valor
            html.Div(value, className="farol-card-value", style={
                "fontSize": "clamp(1.1rem, 2vw, 2.5rem)", 
                "whiteSpace": "nowrap",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "letterSpacing": "-0.5px"
            }),
            
            # Rodapé: Subtexto e Trend (empurrado para o final)
            trend_container
        ], className="farol-card-macos")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H6(title, className="farol-card-title text-muted"),
            html.Span(str(value), className="farol-card-value fs-4 fw-bold"),
        ], className="farol-card-macos p-3")


def render_kpi_card_compact(
    title: str,
    value: str,
    icon_class: str = "bi-bar-chart",
    color_class: str = "text-dark"
) -> html.Div:
    """
    Versão compacta do KPI card para uso em grids menores.
    Atualizada p/ usar estilo .farol-card-macos mas com layout mais justo.
    """
    base_color = "#64748B"
    bg_light = "rgba(100, 116, 139, 0.1)"
    if "danger" in color_class or "red" in color_class:
        base_color = "#E20613" # EDENRED_RED
        bg_light = "rgba(226, 6, 19, 0.1)"
    elif "success" in color_class or "green" in color_class:
        base_color = "#10b981" # SUCCESS_GREEN
        bg_light = "rgba(16, 185, 129, 0.1)"
    elif "primary" in color_class or "blue" in color_class:
        base_color = "#3B82F6" # INFO_BLUE
        bg_light = "rgba(59, 130, 246, 0.1)"

    return html.Div([
        html.Div([
            html.I(className=icon_class, style={
                "color": base_color,
                "fontSize": "1.2rem",
                "marginRight": "8px"
            }),
            html.Span(title, className="farol-card-title", style={"marginBottom": "0"})
        ], className="d-flex align-items-center mb-2"),
        html.Div(value, className="farol-card-value", style={"fontSize": "1.8rem"})
    ], className="farol-card-macos", style={"padding": "15px", "minHeight": "auto"})
