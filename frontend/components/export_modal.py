import dash_bootstrap_components as dbc
from dash import html, dcc
import dash_ag_grid as dag
from dash_iconify import DashIconify

def render_export_modal():
    """
    Modal Premium de Exportação — Layout Apple System Preferences.
    Painel esquerdo: seleção de campos por categoria.
    Painel direito: preview AG Grid em tempo real.
    """
    return dbc.Modal([
        # ─── HEADER ───────────────────────────────────────────
        dbc.ModalHeader([
            html.Div([
                # Ícone Excel premium
                html.Div(
                    DashIconify(icon="vscode-icons:file-type-excel", width=28, height=28),
                    style={"width": "44px", "height": "44px", "display": "flex",
                           "alignItems": "center", "justifyContent": "center",
                           "backgroundColor": "rgba(16, 124, 65, 0.06)",
                           "borderRadius": "12px", "marginRight": "16px", "flexShrink": "0"}
                ),
                html.Div([
                    html.Div("Montar exportação", style={
                        "fontWeight": "700", "fontSize": "1.1rem", "color": "#1d1d1f",
                        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                        "letterSpacing": "-0.01em"
                    }),
                    html.Div("Selecione os campos e visualize antes de baixar", style={
                        "fontSize": "0.82rem", "color": "#86868b", "marginTop": "2px",
                        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
                    })
                ])
            ], style={"display": "flex", "alignItems": "center", "flex": "1"}),
            html.Button(
                DashIconify(icon="ph:x", width=18, color="#86868b"),
                id="btn-close-export-modal",
                className="export-modal-close-btn"
            )
        ], close_button=False, style={
            "borderBottom": "1px solid #f0f0f0", "padding": "20px 28px",
            "backgroundColor": "#ffffff", "display": "flex",
            "justifyContent": "space-between", "alignItems": "center"
        }),

        # ─── BODY ─────────────────────────────────────────────
        dbc.ModalBody([
            html.Div([
                # ── PAINEL ESQUERDO: Seleção de Campos ──
                html.Div([
                    # Título do painel
                    html.Div([
                        DashIconify(icon="ph:sliders-horizontal", width=16, color="#86868b"),
                        html.Span("Campos disponíveis", style={
                            "marginLeft": "8px", "fontWeight": "600", "fontSize": "0.78rem",
                            "color": "#86868b", "textTransform": "uppercase",
                            "letterSpacing": "0.04em"
                        })
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

                    # Container de categorias (preenchido via callback)
                    html.Div(
                        id="export-columns-selector",
                        style={"overflowY": "auto", "maxHeight": "420px",
                               "paddingRight": "8px",
                               # Scrollbar thin estilo Apple
                               "scrollbarWidth": "thin", "scrollbarColor": "#d1d1d6 transparent"}
                    ),
                ], className="export-panel-left"),

                # ── Divisor Vertical ──
                html.Div(style={
                    "width": "1px", "backgroundColor": "#f0f0f0",
                    "margin": "0 24px", "alignSelf": "stretch"
                }),

                # ── PAINEL DIREITO: Preview da Planilha ──
                html.Div([
                    # Título do painel
                    html.Div([
                        DashIconify(icon="ph:table", width=16, color="#86868b"),
                        html.Span("Preview da planilha", style={
                            "marginLeft": "8px", "fontWeight": "600", "fontSize": "0.78rem",
                            "color": "#86868b", "textTransform": "uppercase",
                            "letterSpacing": "0.04em"
                        }),
                        # Badge de contagem
                        html.Span("30 linhas de amostra", style={
                            "marginLeft": "auto", "fontSize": "0.7rem", "color": "#aeaeb2",
                            "fontWeight": "500"
                        })
                    ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),

                    # AG Grid container com Coach Mark Overlay
                    html.Div([
                        # ── Coach Mark: Spotlight + Hand Animation ──
                        html.Div([
                            # Fundo escurecido
                            html.Div(className="coach-backdrop"),

                            # Spotlight (área iluminada no topo onde ficam os headers)
                            html.Div(className="coach-spotlight"),

                            # Mão animada que simula o drag
                            html.Div([
                                DashIconify(icon="ph:hand-grabbing-fill", width=32, color="#E20613"),
                            ], className="coach-hand"),

                            # Callout flutuante
                            html.Div([
                                html.Div([
                                    html.Span("Novo", style={
                                        "background": "#E20613", "color": "#fff",
                                        "padding": "2px 8px", "borderRadius": "6px",
                                        "fontSize": "0.65rem", "fontWeight": "700",
                                        "marginRight": "8px", "letterSpacing": "0.04em"
                                    }),
                                    html.Span("Arraste os cabeçalhos para reordenar as colunas", style={
                                        "fontWeight": "600", "color": "#1d1d1f", "fontSize": "0.82rem"
                                    }),
                                ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
                                html.Div("O arquivo Excel será gerado na ordem que você definir aqui.",
                                         style={"fontSize": "0.75rem", "color": "#86868b"}),
                            ], className="coach-callout"),
                        ], className="coach-mark-overlay", id="coach-mark-overlay"),

                        dag.AgGrid(
                            id="export-preview-grid",
                            className="ag-theme-alpine",
                            columnDefs=[],
                            rowData=[],
                            defaultColDef={
                                "resizable": True,
                                "sortable": True,
                                "filter": False,
                                "minWidth": 110
                            },
                            enableEnterpriseModules=False,
                            dashGridOptions={
                                "rowSelection": "multiple",
                                "suppressRowClickSelection": True,
                                "pagination": False,
                                "domLayout": "normal",
                            },
                            style={"height": "100%", "width": "100%"}
                        )
                    ], style={
                        "height": "440px", "borderRadius": "12px",
                        "border": "1px solid #e5e5ea", "overflow": "hidden",
                        "backgroundColor": "#ffffff", "position": "relative"
                    })
                ], className="export-panel-right"),
            ], className="export-panels-container"),

            # ── Loading Overlay (exibido enquanto gera o Excel) ──
            html.Div([
                html.Div([
                    # SVG animado via Iframe invisível (sem dependência extra)
                    html.Iframe(
                        srcDoc='''<svg width="120" height="140" viewBox="0 0 120 140" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:block;margin:auto">
                            <rect x="10" y="10" width="100" height="120" rx="8" fill="#fff" stroke="#e5e5ea" stroke-width="1.5"/>
                            <path d="M80 10 L110 40 L80 40 Z" fill="#f5f5f7" stroke="#e5e5ea" stroke-width="1"/>
                            <rect x="22" y="22" width="24" height="16" rx="3" fill="#107c41"/>
                            <text x="27" y="34" font-size="9" font-weight="700" fill="#fff" font-family="sans-serif">XLS</text>
                            <rect x="22" y="48" width="0" height="6" rx="3" fill="#E20613"><animate attributeName="width" values="0;76" dur="0.4s" begin="0.2s" fill="freeze"/></rect>
                            <rect x="22" y="60" width="0" height="6" rx="3" fill="#fce4e6"><animate attributeName="width" values="0;76" dur="0.4s" begin="0.5s" fill="freeze"/></rect>
                            <rect x="22" y="72" width="0" height="6" rx="3" fill="#E20613"><animate attributeName="width" values="0;76" dur="0.4s" begin="0.8s" fill="freeze"/></rect>
                            <rect x="22" y="84" width="0" height="6" rx="3" fill="#fce4e6"><animate attributeName="width" values="0;76" dur="0.4s" begin="1.1s" fill="freeze"/></rect>
                            <rect x="22" y="96" width="0" height="6" rx="3" fill="#E20613"><animate attributeName="width" values="0;76" dur="0.4s" begin="1.4s" fill="freeze"/></rect>
                            <rect x="22" y="108" width="0" height="6" rx="3" fill="#fce4e6"><animate attributeName="width" values="0;76" dur="0.4s" begin="1.7s" fill="freeze"/></rect>
                            <circle cx="90" cy="110" r="14" fill="#107c41" opacity="0"><animate attributeName="opacity" values="0;1" dur="0.3s" begin="2.2s" fill="freeze"/></circle>
                            <path d="M83 110 L88 115 L97 105" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0"><animate attributeName="opacity" values="0;1" dur="0.3s" begin="2.3s" fill="freeze"/></path>
                        </svg>''',
                        style={"width": "140px", "height": "160px", "border": "none",
                               "marginBottom": "16px", "background": "transparent"}
                    ),
                    html.Div("Preparando seu arquivo...", style={
                        "fontSize": "1rem", "fontWeight": "600", "color": "#1d1d1f",
                        "marginBottom": "6px"
                    }),
                    html.Div(id="export-loading-status", children="Consultando banco de dados e montando Excel",
                             style={"fontSize": "0.82rem", "color": "#86868b"}),
                ], style={
                    "display": "flex", "flexDirection": "column",
                    "alignItems": "center", "justifyContent": "center"
                })
            ], id="export-loading-overlay", className="export-loading-overlay",
               style={"display": "none"}),
        ], style={"padding": "24px 28px 20px", "backgroundColor": "#fafafa", "position": "relative"}),

        # ─── FOOTER ───────────────────────────────────────────
        dbc.ModalFooter([
            # Seletor de linhas à esquerda
            html.Div([
                DashIconify(icon="ph:rows", width=14, color="#86868b"),
                html.Span("Linhas:", style={
                    "marginLeft": "6px", "marginRight": "8px",
                    "fontSize": "0.78rem", "color": "#86868b", "fontWeight": "500"
                }),
                dcc.Input(
                    id="export-row-limit",
                    type="number",
                    min=100, max=300000, step=1000,
                    value=10000,
                    style={
                        "width": "100px", "padding": "5px 10px",
                        "borderRadius": "8px", "border": "1px solid #e5e5ea",
                        "fontSize": "0.78rem", "fontFamily": "-apple-system, sans-serif",
                        "textAlign": "center"
                    }
                ),
                html.Span("máx 300k", style={
                    "marginLeft": "8px", "fontSize": "0.7rem", "color": "#aeaeb2"
                }),
            ], style={"display": "flex", "alignItems": "center", "flex": "1"}),

            # Botões
            html.Button("Cancelar", id="btn-export-cancel", className="export-btn-cancel"),
            html.Button([
                DashIconify(icon="ph:download-simple", width=16, className="me-2"),
                "Baixar .xlsx"
            ], id="btn-export-confirm", className="export-btn-confirm"),

            # Download invisível
            dcc.Download(id="download-dataframe-xlsx")
        ], style={
            "borderTop": "1px solid #f0f0f0", "padding": "16px 28px",
            "backgroundColor": "#ffffff", "display": "flex",
            "alignItems": "center", "gap": "10px"
        }),
    ],
    id="modal-export-data",
    is_open=False,
    centered=True,
    size="xl",
    class_name="notion-modal",
    fade=True,
    style={"fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"}
    )
