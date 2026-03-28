import dash_bootstrap_components as dbc
from dash import html, dcc
from frontend.components.preventiva_modal import render_preventiva_help_modal, render_ranking_help_modal
from datetime import date

def render_preventiva_section(initial_data=None):
    """
    Renderiza a seção de Preventiva.
    Args:
        initial_data: dict opcional com chaves:
            - total_os, qtd_fugas, pct_fuga: KPI values
            - figure: plotly figure para o chart
            - accordion: componente Accordion já montado
    """
    today = date.today()
    
    return html.Div([
        # ROW 1: Main Chart (Left 8) + KPIs Stacked (Right 4)
        dbc.Row([
            # CHART COLUMN (Big Visual)
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H5("Evolução de Fugas (Ano, Trimestre, Mês)", className="fw-bold mb-0 text-dark font-ubuntu"),
                                dbc.Button(
                                    html.I(className="bi bi-question-circle-fill"),
                                    id="btn-help-prev-chart",
                                    color="link",
                                    className="text-muted p-0 ms-2",
                                    style={"fontSize": "1rem"}
                                )
                            ], className="d-flex align-items-center"),
                        ], className="d-flex align-items-center justify-content-between mb-4"),
                        dcc.Graph(
                            id="prev-chart-evolution",
                            figure=initial_data.get('figure', {}) if initial_data else {},
                            config={"displayModeBar": False},
                            style={"height": "450px"}
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
                            html.Span(
                                id="prev-kpi-fugas", className="farol-card-value",
                                children=f"{initial_data.get('qtd_fugas', 0):,}".replace(',', '.') if initial_data else "",
                                style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}
                            ),
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
                            html.Span(
                                id="prev-kpi-pct", className="farol-card-value",
                                children=f"{initial_data.get('pct_fuga', 0):.1f}%" if initial_data else "",
                                style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}
                            ),
                        ]),
                        
                        html.Div([
                            dbc.Progress(
                                id="prev-progress-bar",
                                value=initial_data.get('pct_fuga', 0) if initial_data else 0,
                                color="danger", className="mt-2",
                                style={"height": "6px", "borderRadius": "3px"}
                            )
                        ]),

                        html.Div([
                            html.Small("% sobre OS com perfil preventivo", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "8px", "display": "block"})
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
                            html.Span(
                                id="prev-kpi-total", className="farol-card-value",
                                children=f"{initial_data.get('total_os', 0):,}".replace(',', '.') if initial_data else "",
                                style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#1e293b", "lineHeight": "1.2"}
                            ),
                        ]),
                        
                        html.Div([
                            html.Small("Total ordens no período", className="text-muted", style={"fontSize": "0.75rem", "marginTop": "4px", "display": "block"})
                        ], className="mt-2")
                    ])
                ], className="farol-card-macos", style={"padding": "20px", "borderRadius": "16px", "backgroundColor": "#FFFFFF", "border": "1px solid #f1f5f9"}),

            ], width=4, className="d-flex flex-column justify-content-between"),
        ], className="mb-4"),

        # Store para tipo de ativo selecionado (veiculos/equipamentos)
        dcc.Store(id="prev-tipo-ativo-store", data="VEICULOS"),

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
                        
                        html.Div(id="prev-ranking-content", style={"minHeight": "250px", "maxHeight": "420px", "overflowY": "auto"})
                    ])
                ], className="shadow-sm border-0 rounded-4 h-100")
            ], width=4),

            # DETAILED TABLE COLUMN — TABELA ACCORDION HTML PURA
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Título e Help (Esquerda)
                            dbc.Col([
                                html.Div([
                                    html.H5("Detalhamento de Fugas", className="fw-bold text-dark font-ubuntu mb-0"),
                                    dbc.Button(
                                        html.I(className="bi bi-question-circle-fill"),
                                        id="btn-help-prev-table",
                                        color="link",
                                        className="text-muted p-0 ms-2",
                                        style={"fontSize": "1rem"}
                                    ),
                                    dbc.Tooltip(
                                        "Clique para entender os critérios de detecção de fugas",
                                        target="btn-help-prev-table",
                                        placement="top"
                                    ),
                                ], className="d-flex align-items-center"),
                            ], width=4),
                            
                            # Toggle Premium (Centro)
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-truck"),
                                            html.Span("Veículos")
                                        ], 
                                        id="prev-toggle-veiculos",
                                        className="premium-toggle-btn active",
                                        n_clicks=0
                                        ),
                                        
                                        html.Div([
                                            html.I(className="bi bi-gear"),
                                            html.Span("Equipamentos")
                                        ], 
                                        id="prev-toggle-equipamentos",
                                        className="premium-toggle-btn",
                                        n_clicks=0
                                        ),
                                    ], className="premium-toggle-container"),
                                ], className="d-flex justify-content-center w-100"),
                            ], width=4, className="d-flex justify-content-center"),

                            # Espaço vazio à direita removido, pois o DatePicker foi movido para fora.
                            dbc.Col([], width=4),
                        ], className="mb-3 align-items-center"),

                        html.P(
                            [html.I(className="bi bi-chevron-expand me-1"), "Clique em um segmento TGM para expandir os clientes"],
                            className="text-muted mb-2", style={"fontSize": "0.78rem"}
                        ),
                        # Container dinâmico — callback gera tabela accordion aqui
                        html.Div(
                            id="prev-accordion-table",
                            children=initial_data.get('accordion', []) if initial_data else [],
                            style={"maxHeight": "420px", "overflowY": "auto"}
                        ),

                        dcc.Download(id="download-preventiva-csv")
                    ])
                ], className="shadow-sm border-0 rounded-4 h-100")
            ], width=8)
        ]),
        
        # Modais de Ajuda
        render_preventiva_help_modal(),
        render_ranking_help_modal(),
        
        # Modal Bespoke — Composição de Valor da OS
        dcc.Store(id="prev-valor-detail-store", data={}),
        dbc.Modal([
            dbc.ModalHeader([
                html.Div([
                    html.Div(
                        html.I(className="bi bi-receipt-cutoff"),
                        className="eden-detail-header-icon"
                    ),
                    html.Div([
                        html.Div("Composição de Valor", className="eden-detail-header-title"),
                        html.Div("Breakdown detalhado por peça e mão de obra", className="eden-detail-header-subtitle"),
                    ]),
                ], className="eden-detail-header"),
            ], close_button=True),
            dbc.ModalBody(id="prev-valor-modal-body"),
        ], id="prev-valor-modal", is_open=False, centered=True, size="xl",
           class_name="eden-detail-modal")
    ])
