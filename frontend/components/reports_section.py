"""
Reports Hub - Export Center
"""
from dash import html, dcc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc


def _build_report_card(variant, icon_name, title, description, button_label,
                       enabled=False, btn_id=None):
    """Card de relatorio com layout horizontal minimalista."""

    badge = None if enabled else html.Span("Em breve", className="report-card-badge")

    btn_props = {
        "className": "report-card-btn",
        "disabled": not enabled,
    }
    if btn_id:
        btn_props["id"] = btn_id

    card_class = f"report-card report-card-{variant}"
    if enabled:
        card_class += " report-card-active"

    return html.Div(
        [
            badge,
            # Icone
            html.Div(
                DashIconify(icon=icon_name, width=44, height=44),
                className="report-card-icon",
            ),
            # Corpo
            html.Div(
                [
                    html.H3(title, className="report-card-title"),
                    html.P(description, className="report-card-description"),
                    html.Button(
                        [html.I(className="bi bi-download"), button_label],
                        **btn_props,
                    ),
                ],
                className="report-card-body",
            ),
        ],
        className=card_class,
    )


def render_reports_section():
    """Renderiza o Hub de Relatorios."""
    return html.Div(
        [
            html.Div(
                [
                    html.H1(
                        "Relatórios",
                        className="reports-hub-title",
                    ),
                    html.P(
                        "Exporte dados para apresentações e análises.",
                        className="reports-hub-subtitle",
                    ),
                ],
                className="reports-hub-header",
            ),
            html.Div(
                [
                    # PPT — ATIVO
                    dbc.Spinner(
                        _build_report_card(
                            variant="ppt",
                            icon_name="vscode-icons:file-type-powerpoint",
                            title="PowerPoint",
                            description="Apresentação executiva com KPIs e gráficos.",
                            button_label="Exportar .PPTX",
                            enabled=True,
                            btn_id="btn-export-ppt",
                        ),
                        color="#E20613",
                        type="border",
                        size="sm",
                        spinner_class_name="report-spinner",
                    ),
                    # Excel — EM BREVE
                    _build_report_card(
                        variant="excel",
                        icon_name="vscode-icons:file-type-excel",
                        title="Excel",
                        description="Planilha com dados detalhados e filtros.",
                        button_label="Exportar .XLSX",
                    ),
                ],
                className="reports-grid",
            ),
            # Download component (hidden)
            dcc.Download(id="download-ppt"),
            html.Div(
                html.P([
                    html.I(className="bi bi-info-circle"),
                    "Novos formatos serão adicionados em breve.",
                ]),
                className="reports-hub-footer-note",
            ),
        ],
        className="reports-hub-container",
    )
