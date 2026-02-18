import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from frontend.components.preventiva_modal import render_preventiva_help_modal, render_ranking_help_modal

def render_preventiva_section():
    return html.Div([
        # ROW 1: Main Chart (Left 8) + KPIs Stacked (Right 4)
        dbc.Row([
            # CHART COLUMN (Big Visual)
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Evolução de Fugas (Ano, Trimestre, Mês)", className="fw-bold mb-0 text-dark font-ubuntu"),
                            dbc.Button(
                                html.I(className="bi bi-question-circle-fill"),
                                id="btn-help-prev-chart",
                                color="link",
                                className="text-muted p-0 ms-2",
                                style={"fontSize": "1rem"}
                            )
                        ], className="d-flex align-items-center mb-4"),
                        dcc.Loading(
                            dcc.Graph(id="prev-chart-evolution", config={"displayModeBar": False}, style={"height": "400px"})
                        )
                    ])
                ], className="shadow-sm border-0 rounded-4 h-100")
            ], width=8),

            # KPIS COLUMN (Vertical Stack)
            dbc.Col([
                # KPI 1: Total Fugas
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H6("Total Fugas", className="farol-card-title", style={"fontSize": "0.85rem", "marginBottom": "0"}),
                                dbc.Button(html.I(className="bi bi-question-circle-fill"), id="btn-help-prev-kpi", color="link", className="text-muted p-0 ms-2", style={"fontSize": "0.8rem"})
                            ], className="d-flex align-items-center"),
                            html.Div([
                                html.I(className=f"bi bi-exclamation-triangle-fill macos-card-icon", style={"color": "#E20613", "fontSize": "1.2rem"}),
                            ], className="macos-card-icon-container", style={"backgroundColor": "rgba(226, 6, 19, 0.1)", "width": "36px", "height": "36px", "borderRadius": "8px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                        ], className="d-flex justify-content-between align-items-center mb-3"),
                        
                        html.Div([
                            html.Span(id="prev-kpi-fugas", className="farol-card-value", style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}),
                        ]),
                        
                        html.Div([
                            html.Small("Preventivas lançadas incorretamente", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "4px", "display": "block"})
                        ], className="mt-2")
                    ])
                ], className="farol-card-macos mb-3", style={"padding": "20px", "borderRadius": "16px", "backgroundColor": "#FFFFFF", "border": "1px solid #f1f5f9"}),

                # KPI 2: Taxa de Fuga
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6("Taxa de Fuga", className="farol-card-title", style={"fontSize": "0.85rem", "marginBottom": "0"}),
                            html.Div([
                                html.I(className=f"bi bi-percent macos-card-icon", style={"color": "#1e293b", "fontSize": "1.2rem"}),
                            ], className="macos-card-icon-container", style={"backgroundColor": "rgba(30, 41, 59, 0.1)", "width": "36px", "height": "36px", "borderRadius": "8px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                        ], className="d-flex justify-content-between align-items-center mb-3"),
                        
                        html.Div([
                            html.Span(id="prev-kpi-pct", className="farol-card-value", style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}),
                        ]),
                        
                        html.Div([
                            dbc.Progress(id="prev-progress-bar", value=0, color="danger", className="mt-2", style={"height": "6px", "borderRadius": "3px"})
                        ]),

                        html.Div([
                            html.Small("% sobre total de corretivas", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "8px", "display": "block"})
                        ], className="mt-2")
                    ])
                ], className="farol-card-macos mb-3", style={"padding": "20px", "borderRadius": "16px", "backgroundColor": "#FFFFFF", "border": "1px solid #f1f5f9"}),

                # KPI 3: Total Analisado
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6("Total Analisado", className="farol-card-title", style={"fontSize": "0.85rem", "marginBottom": "0"}),
                            html.Div([
                                html.I(className=f"bi bi-search macos-card-icon", style={"color": "#0d6efd", "fontSize": "1.2rem"}),
                            ], className="macos-card-icon-container", style={"backgroundColor": "rgba(13, 110, 253, 0.1)", "width": "36px", "height": "36px", "borderRadius": "8px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
                        ], className="d-flex justify-content-between align-items-center mb-3"),
                        
                        html.Div([
                            html.Span(id="prev-kpi-total", className="farol-card-value", style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}),
                        ]),
                        
                        html.Div([
                            html.Small("Total ordens no período", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "4px", "display": "block"})
                        ], className="mt-2")
                    ])
                ], className="farol-card-macos", style={"padding": "20px", "borderRadius": "16px", "backgroundColor": "#FFFFFF", "border": "1px solid #f1f5f9"}),

            ], width=4, className="d-flex flex-column justify-content-between"),
        ], className="mb-4"),

        # ROW 2: Rankings (Left 4) + Detailed Table (Right 8)
        dbc.Row([
             # RANKINGS COLUMN
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Top Ofensores", className="fw-bold mb-0 text-dark font-ubuntu"),
                            dbc.Button(html.I(className="bi bi-question-circle-fill"), id="btn-help-prev-ranking", color="link", className="text-muted p-0 ms-2", style={"fontSize": "1rem"})
                        ], className="d-flex align-items-center mb-3"),
                        
                        dbc.Tabs([
                            dbc.Tab(label="Estabelecimento", tab_id="tab-estab"),
                            dbc.Tab(label="Aprovador", tab_id="tab-aprov"),
                            dbc.Tab(label="1ª Alçada", tab_id="tab-alcada"),
                        ], id="prev-tabs-ranking", active_tab="tab-estab", className="mb-3 nav-fill"),
                        
                        dcc.Loading(
                            html.Div(id="prev-ranking-content", style={"minHeight": "250px"})
                        )
                    ])
                ], className="shadow-sm border-0 rounded-4 h-100")
            ], width=4),

            # DETAILED TABLE COLUMN
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(html.H5("Detalhamento de Fugas", className="fw-bold text-dark font-ubuntu"), width=8),
                            dbc.Col(
                                dbc.Button("Exportar CSV", id="btn-export-preventiva", color="success", size="sm", className="float-end"),
                                width=4
                            )
                        ], className="mb-3 align-items-center"),

                        dcc.Loading(
                            dash_table.DataTable(
                                id="prev-table-detail",
                                columns=[
                                    {"name": "Data", "id": "data_transacao"},
                                    {"name": "OS", "id": "numero_os"},
                                    {"name": "Cód. Item", "id": "codigo_item"},
                                    {"name": "Cód. EC", "id": "codigo_ec"},
                                    {"name": "Estabelecimento", "id": "nome_ec"},
                                    {"name": "Cidade", "id": "cidade"},
                                    {"name": "UF", "id": "uf"},
                                    {"name": "Cód. Cliente", "id": "codigo_cliente"},
                                    {"name": "Cliente", "id": "cliente"},
                                    {"name": "Tipo MO", "id": "tipo_mo"},
                                    {"name": "Valor", "id": "valor_aprovado", "type": "numeric", "format": {"specifier": "$.2f"}},
                                    {"name": "Aprovador", "id": "nome_aprovador"},
                                ],
                                page_size=8,
                                style_table={'overflowX': 'auto'},
                                style_header={
                                    'backgroundColor': '#f8f9fa',
                                    'fontWeight': 'bold',
                                    'borderBottom': '1px solid #dee2e6'
                                },
                                style_cell={
                                    'fontFamily': 'Ubuntu, sans-serif',
                                    'padding': '10px',
                                    'fontSize': '0.85rem'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 250, 252)'
                                    }
                                ]
                            )
                        ),
                        dcc.Download(id="download-preventiva-csv")
                    ])
                ], className="shadow-sm border-0 rounded-4 h-100")
            ], width=8)
        ]),
        
        # Modais de Ajuda
        render_preventiva_help_modal(),
        render_ranking_help_modal()
    ])
