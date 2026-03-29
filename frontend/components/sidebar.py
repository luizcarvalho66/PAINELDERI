"""
Sidebar Component - Modern UX/UI Design
Edenred Executive Branding
"""
import os
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify



def create_nav_item(icon_class: str, label: str, href: str, tooltip_id: str):
    """Create a navigation item with CSS-only tooltip (no dbc.Tooltip)."""
    return html.Div(
        dbc.NavLink(
            [
                html.I(className=f"{icon_class} nav-icon"),
                html.Span(label, className="nav-label"),
            ],
            href=href,
            active="exact",
            className="sidebar-nav-link",
        ),
        id=tooltip_id,
        className="nav-item-wrapper",
        **{"data-tooltip": label},
    )


def render_sidebar():
    """Render the premium sidebar component."""
    return html.Aside(
        [
            # Store para sinal de reload após reset
            dcc.Store(id="reset-reload-signal", data=None),
            # Toggle Button — html.Div (NÃO html.Button) para evitar
            # que o Dash rastreie n_clicks e dispare round-trips ao servidor.
            # O clique é processado por assets/sidebar-toggle.js (JS puro).
            html.Div(
                html.I(className="bi bi-chevron-left toggle-icon"),
                id="sidebar-toggle",
                className="sidebar-toggle-btn",
                role="button",
                tabIndex="0",
                **{"aria-label": "Toggle sidebar"},
            ),
            
            # Sidebar Content Container
            html.Div(
                [
                    # ===== HEADER ZONE =====
                    html.Div(
                        [
                            # Full Logo (visible when expanded)
                            html.Div(
                                [
                                    html.Img(
                                        src="/assets/logo.png",
                                        className="sidebar-logo-full",
                                        alt="Edenred Logo",
                                    ),
                                ],
                                className="logo-expanded",
                            ),
                            # Mini Logo (visible when collapsed)
                            html.Div(
                                [
                                    html.Img(
                                        src="/assets/edenred-minilogo.webp",
                                        className="sidebar-logo-mini-img",
                                        alt="Edenred",
                                    ),
                                ],
                                className="logo-collapsed",
                            ),
                        ],
                        className="sidebar-header",
                    ),
                    
                    # ===== NAVIGATION ZONE =====
                    html.Nav(
                        [
                            html.Div(
                                "MENU PRINCIPAL",
                                className="nav-section-label",
                            ),
                            dbc.Nav(
                                [
                                    create_nav_item(
                                        "bi bi-grid-1x2-fill",
                                        "Dashboard",
                                        "/",
                                        "nav-tooltip-dashboard",
                                    ),
                                    create_nav_item(
                                        "bi bi-stoplights-fill",
                                        "Farol RI",
                                        "/farol",
                                        "nav-tooltip-farol",
                                    ),
                                    create_nav_item(
                                        "bi bi-file-earmark-bar-graph",
                                        "Relatórios",
                                        "/relatorios",
                                        "nav-tooltip-relatorios",
                                    ),
                                    (
                                        html.Div(
                                            dbc.NavLink(
                                                [
                                                    html.I(className="bi bi-gear-fill nav-icon"),
                                                    html.Span("Configurações", className="nav-label"),
                                                    html.Span("Em breve", className="report-card-badge", style={"position": "absolute", "right": "12px", "top": "50%", "transform": "translateY(-50%)", "padding": "0.15rem 0.5rem", "fontSize": "0.55rem"})
                                                ],
                                                href="#",
                                                active=False,
                                                className="sidebar-nav-link",
                                                style={"pointerEvents": "none", "opacity": "0.5"}
                                            ),
                                            id="nav-tooltip-config",
                                            className="nav-item-wrapper",
                                            **{"data-tooltip": "Em breve"}
                                        )
                                        if os.environ.get("DASH_DEBUG", "False").lower() in ("false", "0")
                                        else create_nav_item(
                                            "bi bi-gear-fill",
                                            "Configurações",
                                            "/config",
                                            "nav-tooltip-config",
                                        )
                                    ),
                                ],
                                vertical=True,
                                className="sidebar-nav",
                            ),
                        ],
                        className="sidebar-navigation",
                    ),
                    
                    # ===== FOOTER ZONE =====
                    html.Div(
                        [
                            html.Hr(className="sidebar-divider"),
                            
                            # DATABRICKS SYNC STATUS
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            DashIconify(
                                                icon="simple-icons:databricks",
                                                width=18, height=18,
                                                style={"color": "#FF3621", "marginRight": "8px"},
                                            ),
                                            html.Span("Databricks Direct", className="connection-label"),
                                        ],
                                        className="connection-header"
                                    ),
                                    html.Div(
                                        [
                                            html.Small("Status: ", className="status-label"),
                                            html.Span("Conectado", id="db-connection-status", className="status-value text-success"),
                                        ],
                                        className="connection-details"
                                    ),
                                    html.Div(
                                        "Última sync: --:--",
                                        id="last-sync-label",
                                        className="last-sync-text"
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="bi bi-arrow-repeat me-2"),
                                            "Sincronizar"
                                        ],
                                        id="btn-manual-sync",
                                        color="danger",
                                        size="sm",
                                        className="btn-sync mt-2 w-100",
                                        outline=True
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="bi bi-activity me-2"),
                                            "Acompanhar Sync"
                                        ],
                                        id="btn-data-consumption",
                                        color="light",
                                        size="sm",
                                        className="btn-data-consumption mt-2 w-100",
                                        outline=True
                                    ),
                                    # Botão Reset Completo (protegido por senha)
                                    dbc.Button(
                                        [
                                            html.I(className="bi bi-trash3-fill me-2"),
                                            "Reset Completo"
                                        ],
                                        id="btn-reset-db",
                                        color="danger",
                                        size="sm",
                                        className="btn-reset-db mt-2 w-100",
                                        outline=True,
                                        style={"fontSize": "0.75rem", "opacity": "0.7"}
                                    ),
                                ],
                                className="databricks-status-card mb-3"
                            ),
                            
                            # ===== MODAL: Reset DB — Notion Style =====
                            dbc.Modal(
                                [
                                    dbc.ModalHeader([
                                        html.Div([
                                            html.Div(
                                                html.I(className="bi bi-shield-exclamation", style={"color": "#E20613"}),
                                                className="notion-header-icon",
                                                style={"backgroundColor": "rgba(226, 6, 19, 0.08)"},
                                            ),
                                            html.Div([
                                                html.Div("Reset Completo do Banco", className="notion-header-title"),
                                                html.Div("Ação irreversível — dados locais serão removidos", className="notion-header-subtitle"),
                                            ])
                                        ], className="notion-header-row")
                                    ], close_button=True, class_name="notion-modal-header"),
                                    dbc.ModalBody(
                                        [
                                            # Alerta visual limpo
                                            html.Div([
                                                html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#E20613", "fontSize": "1.4rem"}),
                                                html.Div([
                                                    html.Div("Ação Destrutiva", style={"fontWeight": "700", "color": "#191919", "fontSize": "0.9rem"}),
                                                    html.P(
                                                        "Isso irá excluir TODOS os dados locais (DuckDB + cache). "
                                                        "Um novo sync completo será necessário após o reset.",
                                                        style={"fontSize": "0.82rem", "color": "#6b6b6b", "lineHeight": "1.5", "marginBottom": "0", "marginTop": "4px"}
                                                    )
                                                ]),
                                            ], className="notion-card", style={"borderColor": "rgba(226,6,19,0.2)", "marginBottom": "20px"}),

                                            # Campo de senha
                                            html.Label([
                                                html.I(className="bi bi-key-fill me-2", style={"color": "#9b9b9b"}),
                                                "SENHA DE ADMINISTRADOR"
                                            ], style={"fontWeight": "600", "fontSize": "0.7rem", "color": "#9b9b9b",
                                                     "letterSpacing": "0.08em", "marginBottom": "8px",
                                                     "display": "flex", "alignItems": "center"}),
                                            dbc.Input(
                                                id="input-reset-password",
                                                type="password",
                                                placeholder="Digite a senha para confirmar",
                                                style={"borderRadius": "8px", "border": "1px solid #e5e5e5",
                                                       "padding": "10px 14px", "fontSize": "0.88rem"}
                                            ),
                                            html.Div(id="reset-feedback", className="text-center mt-3"),
                                        ],
                                        class_name="notion-modal-body",
                                        style={"padding": "24px 32px"},
                                    ),
                                    dbc.ModalFooter([
                                        html.Button(
                                            "Cancelar",
                                            id="btn-reset-cancel",
                                            style={"padding": "8px 18px", "borderRadius": "8px", "border": "1px solid #e5e5e5",
                                                   "backgroundColor": "#ffffff", "color": "#6b6b6b", "fontWeight": "500",
                                                   "fontSize": "0.85rem", "cursor": "pointer", "transition": "all 0.15s ease"}
                                        ),
                                        html.Button(
                                            [
                                                html.I(className="bi bi-trash3-fill me-2"),
                                                "Confirmar Reset"
                                            ],
                                            id="btn-reset-confirm",
                                            style={"padding": "8px 20px", "borderRadius": "8px", "border": "none",
                                                   "backgroundColor": "#E20613", "color": "#ffffff", "fontWeight": "600",
                                                   "fontSize": "0.85rem", "cursor": "pointer",
                                                   "transition": "all 0.15s ease"}
                                        ),
                                    ], style={"borderTop": "1px solid #e8e8e8", "padding": "14px 32px",
                                              "backgroundColor": "#ffffff", "display": "flex", "alignItems": "center",
                                              "justifyContent": "flex-end", "gap": "10px"}),
                                ],
                                id="modal-reset-db",
                                is_open=False,
                                centered=True,
                                backdrop="static",
                                class_name="notion-modal",
                                fade=True,
                                style={"fontFamily": "Ubuntu, sans-serif"},
                            ),

                            # ===== MODAL: Progresso do Sync — Notion Style =====
                            dbc.Modal(
                                [
                                    dbc.ModalHeader([
                                        html.Div([
                                            html.Div(
                                                DashIconify(
                                                    icon="simple-icons:databricks",
                                                    width=18, height=18,
                                                    style={"color": "#FF3621"},
                                                ),
                                                className="notion-header-icon",
                                                style={"backgroundColor": "rgba(255, 54, 33, 0.08)"},
                                            ),
                                            html.Div([
                                                html.Div("Sincronização de Dados", className="notion-header-title"),
                                                html.Div("Acompanhe o progresso em tempo real", className="notion-header-subtitle"),
                                            ])
                                        ], className="notion-header-row"),

                                        # Botão de fechar customizado (mantém o ID para callback)
                                        html.Button(
                                            html.I(className="bi bi-x-lg"),
                                            id="btn-close-sync-modal",
                                            style={
                                                "background": "transparent", "border": "none",
                                                "color": "#9b9b9b", "cursor": "pointer",
                                                "fontSize": "1rem", "padding": "4px 8px",
                                                "borderRadius": "6px", "transition": "all 0.15s ease",
                                            }
                                        )
                                    ], close_button=False, class_name="notion-modal-header d-flex justify-content-between align-items-center"),

                                    dbc.ModalBody(
                                        html.Div(
                                            html.P(
                                                [
                                                    html.I(className="bi bi-info-circle me-2", style={"color": "#9b9b9b"}),
                                                    "Clique em 'Sincronizar' para iniciar o processo."
                                                ],
                                                style={"fontSize": "0.9rem", "color": "#6b6b6b", "margin": "0"}
                                            ),
                                            id="sync-progress-container",
                                        ),
                                        class_name="notion-modal-body",
                                        style={"padding": "28px 32px"},
                                    ),

                                    dbc.ModalFooter([
                                        html.Div([
                                            DashIconify(
                                                icon="simple-icons:databricks",
                                                width=12, height=12,
                                                style={"color": "#9b9b9b", "marginRight": "6px"},
                                            ),
                                            html.Small("hive_metastore.gold · SQL Warehouse · CloudFetch",
                                                       style={"color": "#9b9b9b", "fontSize": "0.72rem"}),
                                        ], className="d-flex align-items-center")
                                    ], style={"borderTop": "1px solid #e8e8e8", "padding": "12px 32px",
                                              "backgroundColor": "#ffffff"}),
                                ],
                                id="modal-data-consumption",
                                is_open=False,
                                centered=True,
                                size="lg",
                                class_name="notion-modal",
                                fade=True,
                                style={"fontFamily": "Ubuntu, sans-serif"},
                            ),

                            html.Div(
                                html.Span(
                                    "v2.0.0",
                                    className="version-badge",
                                ),
                                className="sidebar-footer-content",
                                style={"justifyContent": "center"},
                            ),
                        ],
                        className="sidebar-footer",
                    ),
                ],
                id="sidebar-content",
                className="sidebar-content",
            ),
        ],
        id="sidebar",
        className="sidebar-premium",
    )
