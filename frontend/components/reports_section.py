"""
Reports Hub - Export Center
"""
from dash import html
from dash_iconify import DashIconify


def _build_report_card(variant, icon_name, title, description, button_label):
    """Card de relatorio com layout horizontal minimalista."""
    return html.Div(
        [
            html.Span("Em breve", className="report-card-badge"),
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
                        className="report-card-btn",
                        disabled=True,
                    ),
                ],
                className="report-card-body",
            ),
        ],
        className=f"report-card report-card-{variant}",
    )


def render_reports_section():
    """Renderiza o Hub de Relatorios."""
    return html.Div(
        [
            html.Div(
                [
                    html.H1(
                        u"Relat\u00f3rios",
                        className="reports-hub-title",
                    ),
                    html.P(
                        u"Exporte dados para apresenta\u00e7\u00f5es e an\u00e1lises.",
                        className="reports-hub-subtitle",
                    ),
                ],
                className="reports-hub-header",
            ),
            html.Div(
                [
                    _build_report_card(
                        variant="ppt",
                        icon_name="vscode-icons:file-type-powerpoint",
                        title="PowerPoint",
                        description=u"Apresenta\u00e7\u00e3o executiva com KPIs e gr\u00e1ficos.",
                        button_label="Exportar .PPTX",
                    ),
                    _build_report_card(
                        variant="excel",
                        icon_name="vscode-icons:file-type-excel",
                        title="Excel",
                        description=u"Planilha com dados detalhados e filtros.",
                        button_label="Exportar .XLSX",
                    ),
                ],
                className="reports-grid",
            ),
            html.Div(
                html.P([
                    html.I(className="bi bi-info-circle"),
                    u"Novos formatos ser\u00e3o adicionados em breve.",
                ]),
                className="reports-hub-footer-note",
            ),
        ],
        className="reports-hub-container",
    )
