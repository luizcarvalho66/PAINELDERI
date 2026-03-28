# -*- coding: utf-8 -*-
"""
Reports Hub - Export Center
Com Modal de Seleção de Cliente TGM para geração de PPT por cliente.
"""
from dash import html, dcc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc


def _build_report_card(variant, icon_name, title, description, button_label,
                       button_icon="ph:arrow-right", enabled=False, btn_id=None,
                       accent_color="#E20613"):
    """Card de relatório humanizado com ícone contextual e micro-interações."""

    badge = None if enabled else html.Span(
        [DashIconify(icon="ph:clock-light", width=12, className="me-1"), "Em breve"],
        className="report-card-badge"
    )

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
            # Ícone com fundo contextual suave
            html.Div(
                DashIconify(icon=icon_name, width=40, height=40),
                className="report-card-icon",
                style={"backgroundColor": f"{accent_color}0A", "borderRadius": "12px",
                       "width": "56px", "height": "56px"}
            ),
            # Corpo
            html.Div(
                [
                    html.H3(title, className="report-card-title"),
                    html.P(description, className="report-card-description"),
                    html.Button(
                        [button_label, DashIconify(icon=button_icon, width=16, className="ms-2")],
                        **btn_props,
                    ),
                ],
                className="report-card-body",
            ),
        ],
        className=card_class,
        style={"height": "100%"}
    )


def _build_client_selection_modal():
    """Modal premium — Configuração de Exportação PPT com Design Humanizado."""

    def _content_item(icon, icon_color, title, description, slide_count):
        """Gera um item de conteúdo do checklist com ícone contextual."""
        return html.Div(
            [
                # Ícone contextual do slide
                html.Div(
                    DashIconify(icon=icon, width=24, color=icon_color),
                    style={"width": "40px", "height": "40px", "display": "flex", "alignItems": "center", "justifyContent": "center",
                           "backgroundColor": f"{icon_color}12", "borderRadius": "8px", "marginRight": "12px", "flexShrink": "0"}
                ),
                # Texto
                html.Div([
                    html.Div(title, style={"fontWeight": "600", "color": "#1e293b", "fontSize": "0.85rem", "lineHeight": "1.3"}),
                    html.Div(description, style={"color": "#64748b", "fontSize": "0.75rem", "lineHeight": "1.4", "marginTop": "2px"})
                ], style={"flex": "1"}),
                # Badge de slides
                html.Div(
                    f"{slide_count} slide{'s' if slide_count > 1 else ''}",
                    style={"fontSize": "0.65rem", "color": "#94a3b8", "backgroundColor": "#f1f5f9",
                           "padding": "2px 8px", "borderRadius": "10px", "fontWeight": "500", "whiteSpace": "nowrap"}
                ),
            ],
            style={"display": "flex", "alignItems": "center", "padding": "12px 16px",
                   "border": "1px solid #e2e8f0", "borderRadius": "12px", "marginBottom": "8px",
                   "backgroundColor": "#ffffff", "cursor": "pointer",
                   "transition": "all 0.2s ease"},
            className="ppt-content-item"
        )

    return dbc.Modal(
        [
            # ─── HEADER ─────────────────────────────────────────
            dbc.ModalHeader(
                [
                    html.Div(
                        [
                            # Ícone com fundo suave
                            html.Div(
                                DashIconify(icon="ph:file-ppt-duotone", width=32, height=32, color="#E20613"),
                                style={"width": "48px", "height": "48px", "display": "flex", "alignItems": "center",
                                       "justifyContent": "center", "backgroundColor": "rgba(226, 6, 19, 0.06)",
                                       "borderRadius": "12px", "marginRight": "16px"}
                            ),
                            html.Div(
                                [
                                    html.H4("Montar Apresentação",
                                            style={"margin": "0", "fontWeight": "700", "color": "#1e293b",
                                                   "fontSize": "1.15rem", "letterSpacing": "-0.01em"}),
                                    html.P("Escolha o cliente e defina o que vai no relatório.",
                                           style={"margin": "3px 0 0 0", "color": "#94a3b8", "fontSize": "0.85rem"}),
                                ]
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"}
                    ),
                ],
                style={"borderBottom": "1px solid #f1f5f9", "padding": "24px 32px",
                       "backgroundColor": "#fafbfc"},
                close_button=True,
            ),

            # ─── BODY ───────────────────────────────────────────
            dbc.ModalBody(
                [
                    dbc.Row(
                        [
                            # ── Coluna Esquerda: Cliente + Período ──
                            dbc.Col(
                                [
                                    # Cliente
                                    html.Div(
                                        [
                                            html.Label(
                                                [DashIconify(icon="ph:buildings-light", width=16, className="me-2", color="#94a3b8"),
                                                 "CLIENTE"],
                                                style={"fontWeight": "600", "fontSize": "0.7rem", "color": "#94a3b8",
                                                       "letterSpacing": "0.08em", "marginBottom": "8px",
                                                       "display": "flex", "alignItems": "center"}
                                            ),
                                            dcc.Dropdown(
                                                id="dropdown-client-tgm",
                                                placeholder="Qual cliente deseja analisar?",
                                                clearable=True,
                                                searchable=True,
                                                className="modal-premium-dropdown",
                                                style={"borderRadius": "10px"}
                                            ),
                                        ],
                                        className="mb-4"
                                    ),

                                    # Período
                                    html.Div(
                                        [
                                            html.Label(
                                                [DashIconify(icon="ph:calendar-dots-light", width=16, className="me-2", color="#94a3b8"),
                                                 "PERÍODO"],
                                                style={"fontWeight": "600", "fontSize": "0.7rem", "color": "#94a3b8",
                                                       "letterSpacing": "0.08em", "marginBottom": "8px",
                                                       "display": "flex", "alignItems": "center"}
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [DashIconify(icon="ph:clock-counter-clockwise", width=16, className="me-1"), "30 Dias"],
                                                        id="ppt-pill-30d",
                                                        className="ppt-period-pill ppt-period-active",
                                                        n_clicks=0,
                                                        style={"display": "inline-flex", "alignItems": "center", "whiteSpace": "nowrap",
                                                               "padding": "10px 20px", "backgroundColor": "rgba(226, 6, 19, 0.07)",
                                                               "color": "#E20613", "borderRadius": "22px", "fontWeight": "600",
                                                               "fontSize": "0.8rem", "cursor": "pointer", "transition": "all 0.2s ease"}
                                                    ),
                                                    html.Div(
                                                        [DashIconify(icon="ph:calendar-light", width=16, className="me-1"), "Trimestre"],
                                                        id="ppt-pill-trimestre",
                                                        className="ppt-period-pill",
                                                        n_clicks=0,
                                                        style={"display": "inline-flex", "alignItems": "center", "whiteSpace": "nowrap",
                                                               "padding": "10px 20px", "border": "1px solid #e2e8f0",
                                                               "backgroundColor": "#fff", "color": "#94a3b8", "borderRadius": "22px",
                                                               "fontWeight": "500", "fontSize": "0.8rem", "cursor": "pointer",
                                                               "transition": "all 0.2s ease"}
                                                    ),
                                                    html.Div(
                                                        [DashIconify(icon="ph:calendar-check-light", width=16, className="me-1"), "Anual"],
                                                        id="ppt-pill-anual",
                                                        className="ppt-period-pill",
                                                        n_clicks=0,
                                                        style={"display": "inline-flex", "alignItems": "center", "whiteSpace": "nowrap",
                                                               "padding": "10px 20px", "border": "1px solid #e2e8f0",
                                                               "backgroundColor": "#fff", "color": "#94a3b8", "borderRadius": "22px",
                                                               "fontWeight": "500", "fontSize": "0.8rem", "cursor": "pointer",
                                                               "transition": "all 0.2s ease"}
                                                    ),
                                                ],
                                                style={"display": "flex", "gap": "8px", "flexWrap": "wrap"}
                                            ),
                                            # Store para guardar período selecionado
                                            dcc.Store(id="ppt-period-store", data="30d"),
                                            # Nota contextual sutil
                                            html.Div(
                                                [DashIconify(icon="ph:info", width=12, className="me-1"),
                                                 "Dados baseados na última sincronização"],
                                                style={"marginTop": "10px", "fontSize": "0.7rem", "color": "#cbd5e1",
                                                       "display": "flex", "alignItems": "center"}
                                            ),
                                        ]
                                    ),
                                ],
                                md=5,
                                style={"paddingRight": "24px", "borderRight": "1px solid #f1f5f9"}
                            ),

                            # ── Coluna Direita: Conteúdo ──
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                [DashIconify(icon="ph:stack-light", width=16, className="me-2", color="#94a3b8"),
                                                 "SLIDES DO RELATÓRIO"],
                                                style={"fontWeight": "600", "fontSize": "0.7rem", "color": "#94a3b8",
                                                       "letterSpacing": "0.08em", "marginBottom": "12px",
                                                       "display": "flex", "alignItems": "center"}
                                            ),
                                            # Items com ícones contextuais únicos
                                            _content_item(
                                                "ph:presentation-chart-light", "#E20613",
                                                "Capa e Visão Executiva",
                                                "KPIs consolidados, TCO e saving acumulado",
                                                2
                                            ),
                                            _content_item(
                                                "ph:chart-line-up-light", "#0ea5e9",
                                                "Evolução Silent Order",
                                                "Volume de OS automáticas e Top 3 estabelecimentos",
                                                1
                                            ),
                                            _content_item(
                                                "ph:scales-light", "#8b5cf6",
                                                "Comparativo de Operações",
                                                "Corretiva vs Preventiva em dispersão e boxplot",
                                                1
                                            ),
                                            _content_item(
                                                "ph:traffic-signal-light", "#f59e0b",
                                                "Farol de Regulação",
                                                "Matriz de peças críticas e tabela detalhada",
                                                2
                                            ),
                                        ],
                                    ),
                                ],
                                md=7,
                                style={"paddingLeft": "24px"}
                            ),
                        ]
                    ),
                    # ── Overlay de Loading PPT (dentro do modal) ──
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Iframe(
                                        srcDoc='''<svg width="140" height="110" viewBox="0 0 140 110" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:auto">
                                            <rect x="5" y="5" width="130" height="100" rx="6" fill="#fff" stroke="#e5e5ea" stroke-width="1.5"/>
                                            <rect x="5" y="5" width="130" height="18" rx="6" fill="#E20613"/>
                                            <rect x="5" y="17" width="130" height="6" fill="#E20613"/>
                                            <rect x="14" y="10" width="50" height="6" rx="2" fill="rgba(255,255,255,0.7)"/>
                                            <rect x="14" y="32" width="35" height="28" rx="4" fill="#f5f5f7" stroke="#e5e5ea" stroke-width="0.5"><animate attributeName="fill" values="#f5f5f7;#fce4e6;#fce4e6" dur="0.5s" begin="0.3s" fill="freeze"/></rect>
                                            <rect x="54" y="32" width="35" height="28" rx="4" fill="#f5f5f7" stroke="#e5e5ea" stroke-width="0.5"><animate attributeName="fill" values="#f5f5f7;#fce4e6;#fce4e6" dur="0.5s" begin="0.6s" fill="freeze"/></rect>
                                            <rect x="94" y="32" width="35" height="28" rx="4" fill="#f5f5f7" stroke="#e5e5ea" stroke-width="0.5"><animate attributeName="fill" values="#f5f5f7;#fce4e6;#fce4e6" dur="0.5s" begin="0.9s" fill="freeze"/></rect>
                                            <rect x="14" y="68" width="76" height="30" rx="4" fill="#f5f5f7"><animate attributeName="fill" values="#f5f5f7;#E20613;#fce4e6" dur="1s" begin="1.2s" fill="freeze"/><animate attributeName="width" values="0;76" dur="0.6s" begin="1.2s" fill="freeze"/></rect>
                                            <circle cx="114" cy="88" r="10" fill="#f5f5f7" stroke="#e5e5ea" stroke-width="0.5"><animate attributeName="fill" values="#f5f5f7;#fce4e6;#fce4e6" dur="0.4s" begin="1.8s" fill="freeze"/></circle>
                                            <circle cx="120" cy="16" r="10" fill="#107c41" opacity="0"><animate attributeName="opacity" values="0;1" dur="0.3s" begin="2.2s" fill="freeze"/></circle>
                                            <path d="M115 16 L118 19 L125 12" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0"><animate attributeName="opacity" values="0;1" dur="0.3s" begin="2.3s" fill="freeze"/></path>
                                        </svg>''',
                                        style={"width": "160px", "height": "130px", "border": "none",
                                               "marginBottom": "16px", "background": "transparent"}
                                    ),
                                    html.Div("Montando sua apresentação...", id="ppt-loading-title",
                                             style={"fontSize": "1rem", "fontWeight": "600", "color": "#1d1d1f",
                                                    "marginBottom": "6px"}),
                                    html.Div("Coletando KPIs e gráficos do painel", id="ppt-loading-status",
                                             style={"fontSize": "0.82rem", "color": "#86868b"}),
                                ],
                                style={"display": "flex", "flexDirection": "column",
                                       "alignItems": "center", "justifyContent": "center"}
                            )
                        ],
                        id="ppt-loading-overlay",
                        className="export-loading-overlay",
                        style={"display": "none"}
                    ),
                ],
                style={"padding": "28px 32px 20px 32px", "backgroundColor": "#ffffff", "position": "relative"},
            ),

            # ─── FOOTER ─────────────────────────────────────────
            dbc.ModalFooter(
                [
                    # Indicador de slides à esquerda
                    html.Div(
                        [DashIconify(icon="ph:slides-light", width=16, className="me-1"),
                         "6 slides serão gerados"],
                        style={"fontSize": "0.75rem", "color": "#94a3b8", "display": "flex",
                               "alignItems": "center", "flex": "1"}
                    ),
                    html.Button(
                        "Cancelar",
                        id="btn-cancel-ppt-modal",
                        className="modal-minimal-btn-cancel",
                        style={"padding": "10px 20px", "borderRadius": "10px", "border": "1px solid #e2e8f0",
                               "backgroundColor": "#ffffff", "color": "#64748b", "fontWeight": "500",
                               "fontSize": "0.85rem", "cursor": "pointer", "transition": "all 0.2s ease"}
                    ),
                    html.Button(
                        [
                            DashIconify(icon="ph:file-ppt-light", width=18, className="me-2"),
                            "Gerar Apresentação",
                        ],
                        id="btn-generate-ppt-confirm",
                        className="modal-minimal-btn-confirm",
                        disabled=True,
                        style={"padding": "10px 24px", "borderRadius": "10px", "border": "none",
                               "backgroundColor": "#E20613", "color": "#ffffff", "fontWeight": "600",
                               "fontSize": "0.85rem", "cursor": "pointer",
                               "boxShadow": "0 2px 8px -2px rgba(226,6,19,0.3)",
                               "transition": "all 0.2s ease", "opacity": "0.5"}
                    ),
                ],
                style={"borderTop": "1px solid #f1f5f9", "padding": "16px 32px",
                       "backgroundColor": "#fafbfc", "display": "flex", "alignItems": "center", "gap": "12px"},
            ),
        ],
        id="modal-select-client",
        is_open=False,
        centered=True,
        backdrop="static",
        size="lg",
        style={"borderRadius": "16px", "overflow": "hidden",
               "boxShadow": "0 25px 50px -12px rgba(0, 0, 0, 0.15)"}
    )


def render_reports_section():
    """Renderiza o Hub de Relatórios com design humanizado."""
    return html.Div(
        [
            # ─── HEADER ─────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                DashIconify(icon="ph:export-light", width=28, color="#94a3b8"),
                                style={"width": "44px", "height": "44px", "display": "flex",
                                       "alignItems": "center", "justifyContent": "center",
                                       "backgroundColor": "#f1f5f9", "borderRadius": "10px",
                                       "marginRight": "16px"}
                            ),
                            html.Div(
                                [
                                    html.H1(
                                        "Relatórios",
                                        className="reports-hub-title",
                                    ),
                                    html.P(
                                        "Gere apresentações executivas e exporte dados para análises.",
                                        className="reports-hub-subtitle",
                                    ),
                                ]
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"}
                    ),
                ],
                className="reports-hub-header",
            ),
        html.Div(
            [

                    # PPT — ATIVO (com Badge BETA)
                    html.Div([
                        # Badge BETA flutuante
                        html.Span(
                            [html.I(className="bi bi-stars me-1"), "BETA"],
                            className="report-beta-badge"
                        ),
                        _build_report_card(
                            variant="ppt",
                            icon_name="vscode-icons:file-type-powerpoint",
                            title="Apresentação Executiva",
                            description="Relatório visual com KPIs, gráficos comparativos e farol de regulação.",
                            button_label="Gerar .PPTX",
                            button_icon="ph:file-ppt-light",
                            enabled=True,
                            btn_id="btn-export-ppt",
                            accent_color="#E20613",
                        ),
                    ], style={"position": "relative", "height": "100%"}),
                    # Excel — ATIVO
                    _build_report_card(
                        variant="excel",
                        icon_name="vscode-icons:file-type-excel",
                        title="Dados Detalhados",
                        description="Escolha e arraste colunas na mini-planilha antes de extrair os dados completos.",
                        button_label="Montar Exportação .XLSX",
                        button_icon="ph:file-xls-light",
                        enabled=True,
                        btn_id="btn-open-export-modal-reports",
                        accent_color="#16a34a",
                    ),
                ],
                className="reports-grid",
            ),
            # Modal de Seleção de Cliente TGM
            _build_client_selection_modal(),
            # Download component (hidden)
            dcc.Download(id="download-ppt"),
            dcc.Store(id="ppt-export-status"),
            # ─── FOOTER ─────────────────────────────────────
            html.Div(
                html.P([
                    DashIconify(icon="ph:sparkle-light", width=14, className="me-1"),
                    "Novos formatos de exportação estão sendo preparados.",
                ]),
                className="reports-hub-footer-note",
            ),
        ],
        className="reports-hub-container",
    )
