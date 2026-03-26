# -*- coding: utf-8 -*-
"""
Notion-Style Help Modal — Factory & Components.

Gera modais de documentação ultra-limpos seguindo a linguagem visual do Notion:
- Fundo branco puro, sem glassmorphism
- Tabs com underline vermelha Edenred
- Cards com bordas sutis (#efefef)
- Tipografia limpa (Ubuntu + system)
- Troca de abas 100% client-side via JS (zero lag)

Uso:
    from frontend.components.help_modal import build_help_modal, notion_card, notion_metric, notion_pipeline, notion_timeline_step
"""

from dash import html
import dash_bootstrap_components as dbc


# ═══════════════════════════════════════════════════════════════════
# FACTORY — Gera modal completo com tabs Notion
# ═══════════════════════════════════════════════════════════════════

def build_help_modal(modal_id, icon_class, title, subtitle, sections, default_section=None):
    """Factory para modais de help estilo Notion com branding Edenred."""
    if not default_section:
        default_section = sections[0]["id"]

    # Tab buttons
    tab_buttons = []
    content_panes = []

    for s in sections:
        is_active = (s["id"] == default_section)
        active_cls = " active" if is_active else ""

        tab_buttons.append(
            html.Button(
                s["label"],
                className=f"notion-tab-btn{active_cls}",
                **{"data-target": f"pane-{modal_id}-{s['id']}"}
            )
        )

        content_panes.append(
            html.Div(
                s["content"],
                id=f"pane-{modal_id}-{s['id']}",
                className=f"notion-pane{active_cls}"
            )
        )

    return dbc.Modal([
        # ── Header ──
        dbc.ModalHeader([
            html.Div([
                html.Div(
                    html.I(className=f"bi {icon_class}"),
                    className="notion-header-icon"
                ),
                html.Div([
                    html.Div(title, className="notion-header-title"),
                    html.Div(subtitle, className="notion-header-subtitle"),
                ])
            ], className="notion-header-row")
        ], close_button=True, class_name="notion-modal-header"),

        # ── Tabs ──
        html.Div(tab_buttons, className="notion-tabs"),

        # ── Body ──
        dbc.ModalBody([
            html.Div(content_panes, className="notion-content-area")
        ], class_name="notion-modal-body"),

    ], id=modal_id, size="lg", is_open=False, centered=True,
       scrollable=True, class_name="notion-modal", fade=True)


# ═══════════════════════════════════════════════════════════════════
# COMPONENTS — Blocos de conteúdo reutilizáveis
# ═══════════════════════════════════════════════════════════════════

def notion_metric(value, label, desc="", color="#E20613"):
    """KPI grande centralizado com fundo sutil."""
    children = [
        html.Div(value, className="notion-metric-value", style={"color": color}),
        html.Div(label, className="notion-metric-label"),
    ]
    if desc:
        children.append(html.Div(desc, className="notion-metric-desc"))
    return html.Div(children, className="notion-metric")


def notion_card(icon, icon_color, icon_bg, title, text):
    """Card informativo com ícone lateral."""
    return html.Div([
        html.Div(
            html.I(className=f"bi {icon}", style={"color": icon_color}),
            className="notion-card-icon",
            style={"backgroundColor": icon_bg}
        ),
        html.Div([
            html.Div(title, className="notion-card-title"),
            html.Div(text, className="notion-card-text"),
        ])
    ], className="notion-card")


def notion_pipeline(nodes):
    """Pipeline horizontal com dots conectados (versão limpa)."""
    return html.Div([
        html.Div([
            html.Div(
                html.I(className=f"bi {n['icon']}", style={"color": n["color"]}),
                className="notion-pipeline-dot",
                style={"backgroundColor": n.get("bg", "#f5f5f5")}
            ),
            html.Div(n["label"], className="notion-pipeline-label")
        ], className="notion-pipeline-node")
        for n in nodes
    ], className="notion-pipeline")


def notion_timeline_step(number, color, title, desc, formula=None):
    """Step na timeline vertical com dot numerado."""
    children = [
        html.Div(title, className="notion-timeline-title"),
        html.Div(desc, className="notion-timeline-desc"),
    ]
    if formula:
        children.append(html.Code(formula, className="notion-timeline-code"))

    return html.Div([
        html.Div(str(number), className="notion-timeline-dot", style={"backgroundColor": color}),
        html.Div(children)
    ], className="notion-timeline-step")


def notion_divider():
    """Linha divisória sutil."""
    return html.Hr(className="notion-divider")


# ═══════════════════════════════════════════════════════════════════
# LEGACY COMPAT — Mantém imports antigos funcionando
# ═══════════════════════════════════════════════════════════════════

def info_block(title, text, color="#1e293b"):
    """Compat: redireciona para notion_card."""
    return notion_card("bi-info-circle", color, f"rgba(0,0,0,0.04)", title, text)


def stat_value(value, label, color="#E20613"):
    """Compat: redireciona para notion_metric."""
    return notion_metric(value, label, color=color)


def formula_code(text):
    """Bloco de fórmula monospace inline."""
    return html.Code(text, className="notion-timeline-code")
