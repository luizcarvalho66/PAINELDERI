# -*- coding: utf-8 -*-
"""
Componentes Premium Reutilizáveis para Modais — Design System.
Pipeline Flow, Metric Spotlight, Step Timeline, Annotation Card.

Uso:
    from frontend.components.modal_components import pipeline, spotlight, timeline_step, annotation, mini_formula
"""

from dash import html


def pipeline(nodes):
    """
    Pipeline visual horizontal animado com dots conectados por linha gradiente.

    Args:
        nodes: lista de dicts com: icon, label, color, bg
               Ex: [{"icon": "bi-database-fill", "label": "Databricks", "color": "#E20613", "bg": "rgba(226,6,19,0.08)"}]
    """
    return html.Div([
        html.Div([
            html.Div(
                html.I(className=f"bi {n['icon']}", style={"color": n["color"], "fontSize": "0.9rem"}),
                className="pipeline-dot",
                style={"backgroundColor": n.get("bg", "#fff")}
            ),
            html.Div(n["label"], className="pipeline-label")
        ], className="pipeline-node")
        for n in nodes
    ], className="pipeline-flow")


def spotlight(value, label, desc, color="#E20613", bg_var="rgba(226,6,19,0.06)"):
    """
    Metric Spotlight — número grande com gradiente radial de fundo.

    Args:
        value: texto do KPI (ex: "~19.7%")
        label: label uppercase (ex: "TAXA DE FUGA ATUAL")
        desc: descrição menor
        color: cor do número
        bg_var: cor do gradiente radial
    """
    return html.Div([
        html.Div(value, className="metric-spotlight-value", style={"color": color}),
        html.Div(label, className="metric-spotlight-label"),
        html.Div(desc, className="metric-spotlight-desc"),
    ], className="metric-spotlight apple-glass-card",
       style={"--spotlight-color": bg_var})


def timeline_step(number, color, title, desc, formula=None):
    """
    Step na timeline vertical com dot numerado e linha conectora.

    Args:
        number: número do step (1, 2, 3)
        color: cor do dot (#E20613, #f59e0b, #10b981)
        title: título do step
        desc: descrição
        formula: fórmula SQL/código (opcional)
    """
    content_children = [
        html.Div(title, className="step-timeline-title"),
        html.Div(desc, className="step-timeline-desc"),
    ]
    if formula:
        content_children.append(
            html.Code(formula, style={
                "display": "inline-block", "marginTop": "4px",
                "fontSize": "0.65rem", "color": color,
                "backgroundColor": "rgba(0,0,0,0.03)", "padding": "2px 8px",
                "borderRadius": "4px", "fontFamily": "'Cascadia Code', monospace"
            })
        )

    return html.Div([
        html.Div(str(number), className="step-timeline-dot",
                 style={"backgroundColor": color}),
        html.Div(content_children, className="step-timeline-content")
    ], className="step-timeline-item")


def annotation(icon, icon_color, icon_bg, title, text, border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)"):
    """
    Annotation Card — nota lateral com borda colorida e ícone.

    Args:
        icon: classe do ícone Bootstrap (ex: "bi-database")
        icon_color: cor do ícone
        icon_bg: cor de fundo do ícone
        title: título da nota
        text: texto descritivo
        border_color: cor da borda lateral esquerda
        card_bg: cor de fundo gradiente
    """
    return html.Div([
        html.Div(
            html.I(className=f"bi {icon}", style={"color": icon_color, "fontSize": "0.85rem"}),
            className="annotation-icon",
            style={"backgroundColor": icon_bg}
        ),
        html.Div([
            html.Div(title, className="annotation-title"),
            html.Div(text, className="annotation-text"),
        ], className="annotation-content")
    ], className="annotation-card",
       style={"--annotation-color": border_color, "--annotation-bg": card_bg})


def mini_formula(text):
    """Code inline compacto para fórmulas."""
    return html.Code(text, style={
        "fontSize": "0.68rem", "color": "#475569",
        "fontFamily": "'Cascadia Code', 'Fira Code', monospace",
        "backgroundColor": "#f1f5f9", "padding": "2px 6px",
        "borderRadius": "4px", "border": "1px solid #e2e8f0",
    })
