# -*- coding: utf-8 -*-
"""
Edenred Help Modal — Premium Design System.

Factory function para criar modais de help consistentes com identidade de marca.
Header dark (#192038), accent strip vermelho, tabs premium horizontais.

Uso:
    from frontend.components.help_modal import build_help_modal, info_block, stat_value, formula_code
"""

from dash import html
import dash_bootstrap_components as dbc


def build_help_modal(modal_id, icon_class, title, subtitle, sections, default_section=None):
    """
    Factory para modais de help premium Edenred.
    """
    if not default_section:
        default_section = sections[0]["id"]

    tabs = [
        dbc.Tab(
            html.Div(s["content"], className="edenred-tab-panel"),
            label=s["label"],
            tab_id=s["id"],
            label_class_name="edenred-tab-label",
            active_label_class_name="edenred-tab-active",
        )
        for s in sections
    ]

    return dbc.Modal([
        # ─── HEADER DARK + ACCENT ───
        dbc.ModalHeader([
            html.Div([
                html.Div([
                    html.I(className=f"bi {icon_class}"),
                ], className="edenred-header-icon"),
                html.Div([
                    html.Div(title, className="edenred-header-title"),
                    html.Div(subtitle, className="edenred-header-subtitle"),
                ]),
            ], className="edenred-header-row"),
        ], close_button=True, class_name="edenred-modal-header"),

        # ─── BODY ───
        dbc.ModalBody([
            dbc.Tabs(
                tabs,
                id=f"{modal_id}-tabs",
                active_tab=default_section,
                class_name="edenred-tabs-nav",
            ),
        ], class_name="edenred-modal-body"),

    ], id=modal_id, size="lg", is_open=False, centered=True,
       scrollable=True, content_class_name="edenred-help-modal", fade=True)


# ═══════════════════════════════════════════════════════════════════
# HELPERS — Blocos de conteúdo reutilizáveis
# ═══════════════════════════════════════════════════════════════════

def info_block(title, text, color="#1e293b"):
    """Bloco informativo com borda lateral colorida."""
    return html.Div([
        html.Div(title, style={
            "fontWeight": "700", "fontSize": "0.88rem", "color": "#1e293b",
            "marginBottom": "4px", "fontFamily": "Ubuntu, sans-serif"
        }),
        html.Div(text, style={
            "fontSize": "0.82rem", "color": "#64748b", "lineHeight": "1.6"
        }),
    ], className="edenred-info-block", style={"--block-color": color})


def stat_value(value, label, color="#E20613"):
    """Número grande de KPI com label."""
    return html.Div([
        html.Div(value, style={
            "fontSize": "2.2rem", "fontWeight": "800", "color": color,
            "letterSpacing": "-0.03em", "lineHeight": "1",
            "fontFamily": "Ubuntu, sans-serif"
        }),
        html.Div(label, style={
            "fontSize": "0.72rem", "fontWeight": "600", "color": "#94a3b8",
            "textTransform": "uppercase", "letterSpacing": "0.5px",
            "marginTop": "6px"
        }),
    ], className="edenred-stat-value")


def formula_code(text):
    """Bloco de fórmula monospace inline."""
    return html.Code(text, className="edenred-formula")
