"""
Sidebar Component - Modern UX/UI Design
Edenred Executive Branding
"""
from dash import html
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
                                ],
                                className="databricks-status-card mb-3"
                            ),
                            
                            # ===== MODAL: Progresso do Sync =====
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(
                                        dbc.ModalTitle(
                                            [
                                                html.I(className="bi bi-database-gear me-2"),
                                            "Sincronização de Dados"
                                            ],
                                        ),
                                        close_button=True,
                                        className="modal-header-databricks",
                                    ),
                                    dbc.ModalBody(
                                        html.Div(
                                            html.P(
                                                [
                                                    html.I(className="bi bi-info-circle me-2"),
                                                    "Clique em 'Sincronizar' para iniciar o processo."
                                                ],
                                                className="sync-idle-msg",
                                            ),
                                            id="sync-progress-container",
                                        ),
                                        className="modal-body-databricks",
                                    ),
                                    dbc.ModalFooter(
                                        html.Div(
                                            [
                                                html.I(className="bi bi-hdd-stack-fill me-1"),
                                                html.Small("hive_metastore.gold • SQL Warehouse • CloudFetch"),
                                            ],
                                            className="modal-footer-info",
                                        ),
                                        className="modal-footer-databricks",
                                    ),
                                ],
                                id="modal-data-consumption",
                                is_open=False,
                                centered=True,
                                size="lg",
                                className="modal-databricks-premium",
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
