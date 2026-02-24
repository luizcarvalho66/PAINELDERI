# -*- coding: utf-8 -*-
"""
Farol Cards - Cards de resumo com contagem de farois

Estilo executivo premium com ícones Bootstrap profissionais.

Author: Luiz Eduardo Carvalho
"""

from dash import html
import dash_bootstrap_components as dbc


def create_card_inner_content(value: str, trend_value: float, trend_direction: str, title: str) -> list:
    """
    Gera o conteúdo interno (Número + Seta) para o card.
    Usado tanto na criação inicial quanto no callback de atualização.
    """
    is_negative_metric = "Ação" in title or "Atenção" in title
    
    trend_color = "#64748b" # Neutro default
    trend_icon = ""
    
    if trend_direction == "up":
        trend_icon = "bi bi-arrow-up-short"
        trend_color = "#E20613" if is_negative_metric else "#10b981"
    elif trend_direction == "down":
        trend_icon = "bi bi-arrow-down-short"
        trend_color = "#10b981" if is_negative_metric else "#E20613"
        
    trend_element = None
    if trend_direction != "neutral":
        trend_element = html.Div([
            html.I(className=trend_icon, style={"fontSize": "1rem", "marginRight": "4px"}),
            f"{abs(trend_value):.1f}%"
        ], className="farol-trend-pill", style={
            "color": trend_color,
            "backgroundColor": f"{trend_color}15",
        })
    else:
        # VISIBLE NEUTRAL INDICATOR (Gray)
        trend_element = html.Div([
            html.I(className="bi bi-dash", style={"fontSize": "1rem", "marginRight": "4px"}),
            "0.0%"
        ], className="farol-trend-pill", style={
            "color": "#94a3b8", # Slate 400
            "backgroundColor": "#f1f5f9", # Slate 100
        })
        
    return [
        html.Span(
            value,
            className="farol-card-value",
            style={
                "fontSize": "clamp(1.1rem, 2vw, 2.5rem)", 
                "whiteSpace": "nowrap",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "letterSpacing": "-0.5px"
            }
        ),
        html.Div(trend_element, className="d-flex align-items-center mt-auto pt-2 w-100 flex-wrap gap-2")
    ]


def create_farol_card(title: str, icon_class: str, card_id: str, color: str, bg_light: str, trend_value: float = 0.0, trend_direction: str = "neutral") -> html.Div:
    """
    Cria um card de resumo individual para o farol com estilo macOS minimalist.
    """
    # Gera conteúdo inicial
    inner_content = create_card_inner_content("0", trend_value, trend_direction, title)

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
                html.I(className=f"{icon_class} macos-card-icon", style={"color": color}),
            ], className="macos-card-icon-container flex-shrink-0", style={"backgroundColor": bg_light})
        ], className="d-flex justify-content-between align-items-center mb-3 w-100"),
        
        # Corpo: Valor + Trend (Target do Callback)
        html.Div(
            inner_content,
            id=card_id,
            className="d-flex flex-column align-items-start h-100 w-100"
        )
    ], className="farol-card-macos")


def render_farol_cards() -> html.Div:
    """
    Renderiza a linha de cards de resumo do farol com estilo executivo.
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                create_farol_card(
                    title="Performando Bem",
                    icon_class="bi bi-check-circle-fill",
                    card_id="farol-card-verde",
                    color="#10b981",
                    bg_light="rgba(16, 185, 129, 0.1)"
                )
            ], md=3, sm=6, className="mb-3"),
            
            dbc.Col([
                create_farol_card(
                    title="Atenção Necessária",
                    icon_class="bi bi-exclamation-triangle-fill",
                    card_id="farol-card-amarelo",
                    color="#f59e0b",
                    bg_light="rgba(245, 158, 11, 0.1)"
                )
            ], md=3, sm=6, className="mb-3"),
            
            dbc.Col([
                create_farol_card(
                    title="Ação Prioritária",
                    icon_class="bi bi-x-circle-fill",
                    card_id="farol-card-vermelho",
                    color="#E20613",
                    bg_light="rgba(226, 6, 19, 0.1)"
                )
            ], md=3, sm=6, className="mb-3"),
            
            dbc.Col([
                create_farol_card(
                    title="Total Analisado",
                    icon_class="bi bi-bar-chart-fill",
                    card_id="farol-card-total",
                    color="#6366f1",
                    bg_light="rgba(99, 102, 241, 0.1)"
                )
            ], md=3, sm=6, className="mb-3"),
        ], className="g-3")
    ], className="farol-cards-container mb-4")
