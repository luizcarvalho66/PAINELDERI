"""
Sidebar Component - Modern UX/UI Design
Edenred Executive Branding
"""
from dash import html, dcc
import dash_bootstrap_components as dbc



def create_nav_item(icon_class: str, label: str, href: str, tooltip_id: str):
    """Create a navigation item with tooltip support for collapsed mode."""
    return html.Div(
        [
            dbc.NavLink(
                [
                    html.I(className=f"{icon_class} nav-icon"),
                    html.Span(label, className="nav-label"),
                ],
                href=href,
                active="exact",
                className="sidebar-nav-link",
            ),
            dbc.Tooltip(
                label,
                target=tooltip_id,
                placement="right",
                className="sidebar-tooltip",
            ),
        ],
        id=tooltip_id,
        className="nav-item-wrapper",
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
                                    create_nav_item(
                                        "bi bi-gear-fill",
                                        "Configurações",
                                        "/config",
                                        "nav-tooltip-config",
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
                                            html.I(className="bi bi-database-check-fill connection-icon"),
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
                            
                            # ===== MODAL: Reset DB (protegido por senha) — MacOS Style =====
                            dbc.Modal(
                                [
                                    dbc.ModalHeader([
                                        html.Div([
                                            html.Div([
                                                html.I(className="bi bi-shield-exclamation", style={"color": "#E20613", "fontSize": "1.2rem"}),
                                            ], style={
                                                "width": "42px", "height": "42px", "borderRadius": "12px",
                                                "backgroundColor": "rgba(226, 6, 19, 0.08)",
                                                "display": "flex", "alignItems": "center", "justifyContent": "center",
                                                "marginRight": "16px"
                                            }),
                                            html.Div([
                                                html.Span("Reset Completo do Banco", style={
                                                    "fontWeight": "700", "fontSize": "1.15rem", "color": "#1e293b",
                                                    "fontFamily": "Ubuntu, sans-serif", "letterSpacing": "-0.02em",
                                                    "display": "block", "marginBottom": "2px"
                                                }),
                                                html.Div("Ação irreversível — todos os dados locais serão removidos", style={
                                                    "fontSize": "0.85rem", "color": "#64748b", "fontWeight": "400"
                                                })
                                            ])
                                        ], className="d-flex align-items-center")
                                    ], close_button=True, class_name="macos-modal-header"),
                                    dbc.ModalBody(
                                        [
                                            # Alerta visual
                                            html.Div([
                                                html.Div([
                                                    html.I(className="bi bi-exclamation-diamond-fill", style={"color": "#E20613", "fontSize": "1.6rem"}),
                                                ], className="text-center mb-3"),
                                                html.Div("Ação Destrutiva", style={"fontWeight": "700", "color": "#E20613", "fontSize": "0.95rem", "textAlign": "center", "marginBottom": "8px"}),
                                                html.P(
                                                    "Isso irá excluir TODOS os dados locais (DuckDB + cache). "
                                                    "Um novo sync completo será necessário após o reset.",
                                                    style={"fontSize": "0.85rem", "color": "#64748b", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "0"}
                                                )
                                            ], className="apple-glass-card danger-tint mb-4"),
                                            # Campo de senha
                                            html.Label([
                                                html.I(className="bi bi-key-fill me-2", style={"color": "#94a3b8"}),
                                                "SENHA DE ADMINISTRADOR"
                                            ], style={"fontWeight": "600", "fontSize": "0.7rem", "color": "#94a3b8",
                                                     "letterSpacing": "0.08em", "marginBottom": "8px",
                                                     "display": "flex", "alignItems": "center"}),
                                            dbc.Input(
                                                id="input-reset-password",
                                                type="password",
                                                placeholder="Digite a senha para confirmar",
                                                style={"borderRadius": "10px", "border": "1px solid #e2e8f0",
                                                       "padding": "12px 16px", "fontSize": "0.9rem"}
                                            ),
                                            html.Div(id="reset-feedback", className="text-center mt-3"),
                                        ],
                                        class_name="macos-modal-body"
                                    ),
                                    dbc.ModalFooter([
                                        html.Button(
                                            "Cancelar",
                                            id="btn-reset-cancel",
                                            className="modal-minimal-btn-cancel",
                                            style={"padding": "10px 20px", "borderRadius": "10px", "border": "1px solid #e2e8f0",
                                                   "backgroundColor": "#ffffff", "color": "#64748b", "fontWeight": "500",
                                                   "fontSize": "0.85rem", "cursor": "pointer", "transition": "all 0.2s ease"}
                                        ),
                                        html.Button(
                                            [
                                                html.I(className="bi bi-trash3-fill me-2"),
                                                "Confirmar Reset"
                                            ],
                                            id="btn-reset-confirm",
                                            className="modal-minimal-btn-confirm",
                                            style={"padding": "10px 24px", "borderRadius": "10px", "border": "none",
                                                   "backgroundColor": "#E20613", "color": "#ffffff", "fontWeight": "600",
                                                   "fontSize": "0.85rem", "cursor": "pointer",
                                                   "boxShadow": "0 2px 8px -2px rgba(226,6,19,0.3)",
                                                   "transition": "all 0.2s ease"}
                                        ),
                                    ], style={"borderTop": "1px solid #f1f5f9", "padding": "16px 32px",
                                              "backgroundColor": "#fafbfc", "display": "flex", "alignItems": "center",
                                              "justifyContent": "flex-end", "gap": "12px"}),
                                ],
                                id="modal-reset-db",
                                is_open=False,
                                centered=True,
                                backdrop="static",
                                class_name="macos-modal-content",
                                fade=True,
                                style={"fontFamily": "Ubuntu, sans-serif"},
                            ),

                            # ===== MODAL: Progresso do Sync — MacOS Style =====
                            dbc.Modal(
                                [
                                    dbc.ModalHeader([
                                        html.Div([
                                            html.Div([
                                                html.I(className="bi bi-database-gear", style={"color": "#0ea5e9", "fontSize": "1.2rem"}),
                                            ], style={
                                                "width": "42px", "height": "42px", "borderRadius": "12px",
                                                "backgroundColor": "rgba(14, 165, 233, 0.08)",
                                                "display": "flex", "alignItems": "center", "justifyContent": "center",
                                                "marginRight": "16px"
                                            }),
                                            html.Div([
                                                html.Span("Sincronização de Dados", style={
                                                    "fontWeight": "700", "fontSize": "1.15rem", "color": "#1e293b",
                                                    "fontFamily": "Ubuntu, sans-serif", "letterSpacing": "-0.02em",
                                                    "display": "block", "marginBottom": "2px"
                                                }),
                                                html.Div("Acompanhe o progresso da sincronização em tempo real", style={
                                                    "fontSize": "0.85rem", "color": "#64748b", "fontWeight": "400"
                                                })
                                            ])
                                        ], className="d-flex align-items-center")
                                    ], close_button=True, class_name="macos-modal-header"),
                                    dbc.ModalBody(
                                        html.Div(
                                            html.P(
                                                [
                                                    html.I(className="bi bi-info-circle me-2", style={"color": "#0ea5e9"}),
                                                    "Clique em 'Sincronizar' para iniciar o processo."
                                                ],
                                                className="sync-idle-msg",
                                                style={"fontSize": "0.9rem", "color": "#64748b"}
                                            ),
                                            id="sync-progress-container",
                                        ),
                                        class_name="macos-modal-body",
                                    ),
                                    dbc.ModalFooter([
                                        html.Div([
                                            html.I(className="bi bi-info-circle-fill me-2", style={"color": "#94a3b8", "fontSize": "0.75rem"}),
                                            html.Small("hive_metastore.gold • SQL Warehouse • CloudFetch",
                                                       style={"color": "#94a3b8", "fontSize": "0.75rem"}),
                                        ], className="d-flex align-items-center")
                                    ], style={"borderTop": "1px solid #f1f5f9", "padding": "12px 32px",
                                              "backgroundColor": "#fafbfc"}),
                                ],
                                id="modal-data-consumption",
                                is_open=False,
                                centered=True,
                                size="lg",
                                class_name="macos-modal-content",
                                fade=True,
                                style={"fontFamily": "Ubuntu, sans-serif"},
                            ),

                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(className="status-dot status-online"),
                                            html.Span(
                                                "Sistemas Operacionais",
                                                className="status-text",
                                            ),
                                        ],
                                        className="status-indicator",
                                    ),
                                    html.Span(
                                        "v2.0.0",
                                        className="version-badge",
                                    ),
                                ],
                                className="sidebar-footer-content",
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
