# -*- coding: utf-8 -*-
"""
Reports Hub - Export Center
Com Modal de Seleção de Cliente TGM para geração de PPT por cliente.
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


def _build_client_selection_modal():
    """Modal premium de seleção de cliente TGM para exportação PPT. Design Minimalista e Clean."""
    return dbc.Modal(
        [
            # Header Minimalista (Fundo branco/transparente, sem blocos escuros)
            dbc.ModalHeader(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        DashIconify(
                                            icon="ph:presentation-chart-thin",
                                            width=32, height=32,
                                            color="#E20613"
                                        ),
                                        className="modal-icon-wrapper"
                                    ),
                                    html.Div(
                                        [
                                            html.H5(
                                                "Relatório Executivo",
                                                className="modal-minimal-title"
                                            ),
                                            html.P(
                                                "Selecione um cliente para exportar a apresentação segmentada.",
                                                className="modal-minimal-subtitle"
                                            ),
                                        ]
                                    ),
                                ],
                                className="modal-minimal-header-content"
                            ),
                        ],
                        className="modal-minimal-header-wrapper"
                    ),
                ],
                className="modal-minimal-header",
                close_button=True,
            ),
            # Body com Dropdown e design clean
            dbc.ModalBody(
                [
                    html.Div(
                        [
                            html.Label(
                                "CLIENTE TGM",
                                className="modal-minimal-label",
                            ),
                            dcc.Dropdown(
                                id="dropdown-client-tgm",
                                placeholder="Buscar e selecionar cliente...",
                                clearable=True,
                                searchable=True,
                                className="modal-minimal-dropdown",
                            ),
                        ],
                        className="modal-minimal-field",
                    ),
                ],
                className="modal-minimal-body",
            ),
            # Footer Clean
            dbc.ModalFooter(
                [
                    html.Button(
                        "Cancelar",
                        id="btn-cancel-ppt-modal",
                        className="modal-minimal-btn-cancel",
                    ),
                    html.Button(
                        [
                            "Gerar Apresentação",
                            DashIconify(icon="ph:arrow-right-light", width=18, style={"marginLeft": "8px"}),
                        ],
                        id="btn-generate-ppt-confirm",
                        className="modal-minimal-btn-confirm",
                        disabled=True,
                    ),
                ],
                className="modal-minimal-footer",
            ),
        ],
        id="modal-select-client",
        is_open=False,
        centered=True,
        backdrop="static",
        className="modal-minimal-selection",
        size="md",
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
                # Modal Overlay de Loading (Fábrica de Slides 3D)
                html.Div(
                    [
                        html.Div(
                            [
                                # Cena Data Flow Transformação (Dashboard -> PPT)
                                html.Div(
                                    [
                                        # Origem: Ícone Dashboard (Extração)
                                        html.Div(
                                            DashIconify(icon="mynaui:grid", width=56, height=56, className="df-source-icon"),
                                            className="df-source-container"
                                        ),

                                        # Fluxo de Dados (Partículas)
                                        html.Div(
                                            [
                                                html.Div(className="df-particle pt-1"),
                                                html.Div(className="df-particle pt-2"),
                                                html.Div(className="df-particle pt-3")
                                            ],
                                            className="df-stream"
                                        ),

                                        # Destino: Ícone PowerPoint (Recepção)
                                        html.Div(
                                            DashIconify(icon="vscode-icons:file-type-powerpoint", width=64, height=64, className="df-target-icon"),
                                            className="df-target-container"
                                        )
                                    ],
                                    className="data-flow-scene mb-4"
                                ),

                                # Texto Dinâmico que "Digita/Pisca"
                                html.Div(
                                    [
                                        html.Span("Coletando gráficos do painel...", className="ppt-dynamic-text msg-1"),
                                        html.Span("Sintetizando cálculos...", className="ppt-dynamic-text msg-2"),
                                        html.Span("Construindo slides .PPTX...", className="ppt-dynamic-text msg-3"),
                                    ],
                                    className="ppt-message-container mt-2"
                                )
                            ],
                            className="ppt-builder-box"
                        )
                    ],
                    id="ppt-loading-overlay",
                    className="ppt-loading-overlay",
                    style={"display": "none"}  # Controlado via callback
                ),

                    # PPT — ATIVO
                    _build_report_card(
                        variant="ppt",
                        icon_name="vscode-icons:file-type-powerpoint",
                        title="PowerPoint",
                        description="Apresentação executiva com KPIs e gráficos.",
                        button_label="Exportar .PPTX",
                        enabled=True,
                        btn_id="btn-export-ppt",
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
            # Modal de Seleção de Cliente TGM
            _build_client_selection_modal(),
            # Download component (hidden)
            dcc.Download(id="download-ppt"),
            dcc.Store(id="ppt-export-status"),
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
