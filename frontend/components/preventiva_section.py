import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import html, dcc
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

            # DETAILED TABLE COLUMN — AG GRID MASTER-DETAIL
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col(html.H5("Detalhamento de Fugas", className="fw-bold text-dark font-ubuntu"), width=6),
                            dbc.Col([
                                dbc.Button("Exportar CSV", id="btn-export-preventiva", color="success", size="sm", className="float-end ms-2"),
                            ], width=6)
                        ], className="mb-3 align-items-center"),

                        # MASTER GRID — Agrupado por SourceNumber (Cód. TGM)
                        html.P(
                            [html.I(className="bi bi-hand-index me-1"), "Selecione um segmento TGM para expandir os clientes"],
                            className="text-muted mb-2", style={"fontSize": "0.78rem"}
                        ),
                        dag.AgGrid(
                            id="prev-table-detail",
                            columnDefs=[
                                {
                                    "headerName": "Cód. TGM", "field": "codigo_tgm",
                                    "pinned": "left", "width": 120,
                                    "cellStyle": {"fontWeight": "600", "color": "#333"}
                                },
                                {
                                    "headerName": "Cliente Principal", "field": "cliente_principal",
                                    "flex": 2, "minWidth": 180,
                                    "tooltipField": "cliente_principal",
                                },
                                {
                                    "headerName": "Clientes", "field": "qtd_clientes",
                                    "width": 95, "type": "numericColumn",
                                    "cellStyle": {
                                        "styleConditions": [
                                            {"condition": "params.value > 3", "style": {"backgroundColor": "#fde8e8", "color": "#c0392b", "fontWeight": "bold"}},
                                            {"condition": "params.value > 1", "style": {"backgroundColor": "#fff8e1", "color": "#e67e22", "fontWeight": "600"}},
                                        ],
                                        "defaultStyle": {"color": "#666"}
                                    },
                                },
                                {
                                    "headerName": "Total OS", "field": "total_os",
                                    "width": 100, "type": "numericColumn", "sort": "desc",
                                },
                                {
                                    "headerName": "OS Distintas", "field": "total_os_distintas",
                                    "width": 115, "type": "numericColumn",
                                },
                                {
                                    "headerName": "Valor Total", "field": "valor_total",
                                    "width": 140, "type": "numericColumn",
                                    "valueFormatter": {"function": "d3.format('$,.2f')(params.value)"},
                                    "cellStyle": {"fontWeight": "600"},
                                },
                            ],
                            rowData=[],
                            defaultColDef={
                                "sortable": True,
                                "filter": True,
                                "resizable": True,
                                "floatingFilter": True,
                            },
                            dashGridOptions={
                                "rowSelection": {"mode": "singleRow", "checkboxes": False},
                                "animateRows": True,
                                "pagination": True,
                                "paginationPageSize": 12,
                                "domLayout": "autoHeight",
                                "tooltipShowDelay": 300,
                            },
                            className="ag-theme-alpine",
                            style={"width": "100%"},
                        ),

                        # DETAIL PANEL — Expansível por SourceNumber
                        dbc.Collapse(
                            dbc.Card([
                                dbc.CardHeader([
                                    html.Div([
                                        html.I(className="bi bi-diagram-3-fill me-2 text-danger"),
                                        html.Span("Clientes do Segmento: ", className="fw-bold"),
                                        html.Span(id="prev-detail-tgm-code", className="badge bg-danger ms-1"),
                                        html.Span(" — ", className="mx-1"),
                                        html.Span(id="prev-detail-tgm-name", className="text-muted fst-italic"),
                                    ], className="d-flex align-items-center"),
                                    dbc.Button(
                                        html.I(className="bi bi-x-lg"),
                                        id="btn-close-detail",
                                        color="link", size="sm",
                                        className="text-muted position-absolute end-0 me-3",
                                    )
                                ], className="position-relative py-2",
                                   style={"backgroundColor": "#fff5f5", "borderBottom": "2px solid #E20613"}),
                                dbc.CardBody([
                                    dag.AgGrid(
                                        id="prev-detail-table",
                                        columnDefs=[
                                            {"headerName": "Cód. Cliente", "field": "codigo_cliente", "width": 120, "pinned": "left",
                                             "cellStyle": {"fontWeight": "600"}},
                                            {"headerName": "Cliente", "field": "cliente", "flex": 2, "minWidth": 160},
                                            {"headerName": "OS", "field": "numero_os", "width": 100},
                                            {"headerName": "Peça", "field": "codigo_item", "flex": 1, "minWidth": 100},
                                            {"headerName": "Estabelecimento", "field": "nome_ec", "flex": 1, "minWidth": 130},
                                            {"headerName": "Cidade", "field": "cidade", "width": 110},
                                            {"headerName": "UF", "field": "uf", "width": 65},
                                            {"headerName": "Tipo MO", "field": "tipo_mo", "width": 130},
                                            {"headerName": "Valor", "field": "valor_aprovado", "width": 110,
                                             "type": "numericColumn",
                                             "valueFormatter": {"function": "params.value ? d3.format('$,.2f')(params.value) : 'R$ 0,00'"},
                                             "cellStyle": {"fontWeight": "600", "color": "#c0392b"}},
                                            {"headerName": "Aprovador", "field": "nome_aprovador", "width": 130},
                                            {"headerName": "Data", "field": "data_transacao", "width": 155,
                                             "sort": "desc"},
                                        ],
                                        rowData=[],
                                        defaultColDef={
                                            "sortable": True,
                                            "filter": True,
                                            "resizable": True,
                                        },
                                        dashGridOptions={
                                            "animateRows": True,
                                            "pagination": True,
                                            "paginationPageSize": 10,
                                            "domLayout": "autoHeight",
                                        },
                                        className="ag-theme-alpine",
                                        style={"width": "100%"},
                                    ),
                                ], className="p-2")
                            ], className="border border-danger border-opacity-25 rounded-3 mt-3 shadow-sm"),
                            id="prev-detail-collapse",
                            is_open=False,
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
