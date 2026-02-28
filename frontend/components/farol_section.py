# -*- coding: utf-8 -*-
"""
Farol Section - Layout completo da seção exclusiva do Farol

Esta é a página principal do módulo RI Corretivas com:
- Cards de resumo
- Gráfico de evolução
- Tabela interativa com farol

Estilo executivo premium Edenred.

Author: Luiz Eduardo Carvalho
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from frontend.components.farol_cards import render_farol_cards
from frontend.components.farol_table import render_farol_table_container


def render_farol_section() -> html.Div:
    """
    Renderiza a seção completa do Farol RI com estilo executivo.
    """
    return html.Div([
        # Interval para refresh automático (a cada 5 minutos para evitar reset frequente)
        dcc.Interval(
            id="farol-interval-refresh",
            interval=300000,  # 5 minutos
            n_intervals=0
        ),
        
        # =====================================================================
        # HEADER DA PÁGINA - Estilo Executivo
        # =====================================================================
        html.Div([
            html.Div([
                # Título com ícone profissional
                html.Div([
                    html.Div([
                        html.I(className="bi bi-stoplights-fill", style={
                            "fontSize": "1.25rem",
                            "color": "#E20613"
                        }),
                    ], style={
                        "width": "44px",
                        "height": "44px",
                        "borderRadius": "10px",
                        "backgroundColor": "rgba(226, 6, 19, 0.1)",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "marginRight": "16px"
                    }),
                    html.Div([
                        html.Div([
                            html.H4(
                                "Farol de Performance",
                                className="mb-0 fw-bold",
                                style={"color": "#1a1a2e", "letterSpacing": "-0.01em"}
                            ),
                        ], className="d-flex align-items-center"),
                        html.P(
                            "Regulação Inteligente • Corretivas",
                            className="mb-0",
                            style={"color": "#64748b", "fontSize": "0.85rem"}
                        )
                    ])
                ], className="d-flex align-items-center"),
            ], className="flex-grow-1"),
            
            # Badge informativo
            html.Div([
                html.Span([
                    html.I(className="bi bi-funnel-fill me-1", style={"fontSize": "0.7rem"}),
                    "Até 2 itens • Até R$ 1.500"
                ], className="badge", style={
                    "backgroundColor": "#f1f5f9",
                    "color": "#475569",
                    "fontWeight": "500",
                    "fontSize": "0.75rem",
                    "padding": "8px 12px",
                    "borderRadius": "6px"
                })
            ])
            
        ], className="d-flex justify-content-between align-items-center mb-4 pb-3", 
           style={"borderBottom": "1px solid #e2e8f0"}),
        
        # =====================================================================
        # CARDS DE RESUMO
        # =====================================================================
        render_farol_cards(),
        
        # =====================================================================
        # GRÁFICO DE EVOLUÇÃO - TEMPORARIAMENTE DESABILITADO
        # =====================================================================
        # TODO: Reativar quando dados estiverem consistentes
        html.Div(id="farol-chart-placeholder", style={"display": "none"}),
        
        # =====================================================================
        # TABELA DO FAROL
        # =====================================================================
        render_farol_table_container(),
        
        # =====================================================================
        # SEÇÃO DE LOGS CORRETIVAS - Visão de Não Aprovações
        # =====================================================================
        html.Div([
            # Header da seção
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="bi bi-journal-text me-2", style={"color": "#E20613"}),
                        "Logs de Não Aprovação"
                    ], className="mb-0 fw-bold"),
                    html.Small("Filtro por item e motivo da não aprovação das ordens", 
                              className="text-muted")
                ], width=6),
                
                # Toggle para expandir/colapsar
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-chevron-down me-1", id="logs-toggle-icon"),
                        "Expandir"
                    ], id="logs-toggle-btn", color="light", size="sm", className="float-end")
                ], width=6, className="d-flex justify-content-end align-items-center"),
            ], className="mb-3"),
            
            # Conteúdo colapsável
            dbc.Collapse([
                # Filtros
                dbc.Row([
                    dbc.Col([
                        html.Label("Filtrar por Peça", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="logs-filter-peca",
                            placeholder="Todas as peças",
                            className="farol-filter-dropdown"
                        ),
                    ], md=3, className="mb-2"),
                    
                    dbc.Col([
                        html.Label("Filtrar por Tipo MO", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="logs-filter-tipo-mo",
                            placeholder="Todos os tipos",
                            className="farol-filter-dropdown"
                        ),
                    ], md=3, className="mb-2"),
                    
                    dbc.Col([
                        html.Label("Filtrar por Motivo", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="logs-filter-motivo",
                            placeholder="Todos os motivos",
                            className="farol-filter-dropdown"
                        ),
                    ], md=3, className="mb-2"),
                    
                    dbc.Col([
                        html.Label("Filtrar por Cliente", className="small text-muted mb-1"),
                        dcc.Dropdown(
                            id="logs-filter-cliente",
                            placeholder="Todos os clientes",
                            className="farol-filter-dropdown"
                        ),
                    ], md=3, className="mb-2"),
                ], className="g-2 mb-3"),
                
                # Container da tabela de logs
                html.Div(
                    id="logs-table-container",
                    className="logs-table-wrapper",
                    style={
                        "maxHeight": "400px",
                        "overflowY": "auto",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "8px"
                    }
                ),
                
                # Paginação dos logs
                html.Div([
                    dbc.Pagination(
                        id="logs-pagination",
                        max_value=1,
                        first_last=True,
                        previous_next=True,
                        fully_expanded=False,
                        size="sm",
                        className="justify-content-center mb-0"
                    ),
                    html.Small(
                        id="logs-count-info",
                        className="text-muted d-block text-center mt-2"
                    )
                ], className="d-flex flex-column align-items-center mt-3"),
                
            ], id="logs-collapse", is_open=False),
            
        ], className="logs-section p-4 bg-white rounded shadow-sm mt-4"),
        
        # =====================================================================
        # NOTA DE RODAPÉ
        # =====================================================================
        html.Div([
            html.Hr(style={"borderColor": "#e2e8f0", "margin": "24px 0"}),
            html.Div([
                html.I(className="bi bi-info-circle me-2", style={"color": "#94a3b8"}),
                html.Span(
                    "Atualização automática a cada 60s • P70 = Percentil 70 dos valores aprovados",
                    style={"color": "#94a3b8", "fontSize": "0.8rem"}
                )
            ], className="d-flex align-items-center")
        ]),

        # =====================================================================
        # MODAL DE AJUDA - REDESIGN "MACOS STYLE" (HORIZONTAL)
        # =====================================================================
        dbc.Modal([
            # HEADER
            dbc.ModalHeader([
                html.Div([
                    html.I(className="bi bi-stoplights-fill me-2", style={"color": "#E20613", "fontSize": "1.2rem"}),
                    html.Span("Como o Farol funciona?", style={
                        "fontFamily": "DIN, sans-serif",
                        "fontWeight": "700",
                        "fontSize": "1.1rem",
                        "color": "#1e293b"
                    })
                ], className="d-flex align-items-center")
            ], close_button=True, className="macos-modal-header"),
            
            # BODY
            dbc.ModalBody([
                dbc.Row([
                    # COLUNA ESQUERDA: CORES DO FAROL
                    dbc.Col([
                        html.Div("ENTENDA AS CORES", className="macos-section-title"),
                        
                        # Verde
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-check-circle-fill", style={"color": "#10b981", "fontSize": "1.5rem"}),
                                html.Div([
                                    html.Div("Performando Bem", style={"fontWeight": "700", "fontSize": "0.9rem", "color": "#10b981"}),
                                    html.Div("≥ 80% de aprovação", style={"fontSize": "0.8rem", "color": "#64748b"})
                                ], className="ms-3")
                            ], className="d-flex align-items-center")
                        ], className="macos-card"),
                        
                        # Amarelo
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#f59e0b", "fontSize": "1.5rem"}),
                                html.Div([
                                    html.Div("Atenção Necessária", style={"fontWeight": "700", "fontSize": "0.9rem", "color": "#f59e0b"}),
                                    html.Div("50% a 80% de aprovação", style={"fontSize": "0.8rem", "color": "#64748b"})
                                ], className="ms-3")
                            ], className="d-flex align-items-center")
                        ], className="macos-card"),
                        
                        # Vermelho
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-x-circle-fill", style={"color": "#E20613", "fontSize": "1.5rem"}),
                                html.Div([
                                    html.Div("Ação Prioritária", style={"fontWeight": "700", "fontSize": "0.9rem", "color": "#E20613"}),
                                    html.Div("< 50% de aprovação ou queda ≥ 15%", style={"fontSize": "0.8rem", "color": "#64748b"})
                                ], className="ms-3")
                            ], className="d-flex align-items-center")
                        ], className="macos-card"),
                        
                        # Nota crítica
                        html.Div([
                            html.I(className="bi bi-exclamation-diamond-fill me-2", style={"color": "#E20613", "fontSize": "0.8rem"}),
                            html.Span("Itens com < 10% de aprovação são sempre Vermelho.",
                                     style={"fontSize": "0.75rem", "color": "#E20613", "fontWeight": "600"})
                        ], className="d-flex align-items-center mt-2 p-2 rounded",
                           style={"backgroundColor": "rgba(226, 6, 19, 0.05)"}),
                        
                    ], width=12, lg=5, className="border-end pe-4"),
                    
                    # COLUNA DIREITA: O QUE ANALISAMOS + OPORTUNIDADES
                    dbc.Col([
                        html.Div("O QUE ANALISAMOS", className="macos-section-title"),
                        
                        html.P("Cada linha é uma combinação Peça + Mão de Obra:",
                               style={"fontSize": "0.85rem", "color": "#475569", "marginBottom": "12px"}),
                        
                        html.Div([
                            html.Div([html.Span("% Auto", className="fw-bold", style={"color": "#10b981", "fontSize": "0.82rem"}),
                                      html.Span(" — Taxa de aprovação dos itens", className="text-muted", style={"fontSize": "0.8rem"})], className="mb-1"),
                            html.Div([html.Span("% Humana", className="fw-bold", style={"color": "#64748b", "fontSize": "0.82rem"}),
                                      html.Span(" — Itens reprovados, cancelados ou pendentes", className="text-muted", style={"fontSize": "0.8rem"})], className="mb-1"),
                            html.Div([html.Span("P70", className="fw-bold", style={"color": "#E20613", "fontSize": "0.82rem"}),
                                      html.Span(" — Percentil 70 dos valores aprovados", className="text-muted", style={"fontSize": "0.8rem"})], className="mb-1"),
                            html.Div([html.Span("OS", className="fw-bold", style={"color": "#0ea5e9", "fontSize": "0.82rem"}),
                                      html.Span(" — Quantidade de ordens de serviço distintas", className="text-muted", style={"fontSize": "0.8rem"})], className="mb-1"),
                            html.Div([html.Span("Score", className="fw-bold", style={"color": "#1e293b", "fontSize": "0.82rem"}),
                                      html.Span(" — Prioridade de ação (0-100)", className="text-muted", style={"fontSize": "0.8rem"})]),
                        ], className="macos-card", style={"backgroundColor": "#f8fafc"}),
                        
                        html.Div("MODO OPORTUNIDADES", className="macos-section-title mt-4"),
                        
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-lightbulb-fill text-warning me-2"),
                                html.Strong("Foco em Ganhos Rápidos", className="text-dark")
                            ], className="mb-2"),
                            html.P("Filtra a tabela com 3 critérios:", style={"fontSize": "0.83rem", "color": "#475569", "marginBottom": "8px"}),
                            html.Div([
                                html.Div([html.Span("❶ ", style={"color": "#E20613", "fontWeight": "700"}),
                                          html.Span("MDO pré-definida", className="fw-semibold"),
                                          html.Span(" — Alinhamento, Lavagem, Lubrificação, etc.", className="text-muted", style={"fontSize": "0.78rem"})], className="mb-1"),
                                html.Div([html.Span("❷ ", style={"color": "#E20613", "fontWeight": "700"}),
                                          html.Span("P70 ≤ R$ 1.500", className="fw-semibold"),
                                          html.Span(" — Valor até R$ 1.500", className="text-muted", style={"fontSize": "0.78rem"})], className="mb-1"),
                                html.Div([html.Span("❸ ", style={"color": "#E20613", "fontWeight": "700"}),
                                          html.Span("OS ≤ 2 itens", className="fw-semibold"),
                                          html.Span(" — Apenas OS simples", className="text-muted", style={"fontSize": "0.78rem"})]),
                            ], style={"fontSize": "0.83rem"}),
                        ], className="macos-card", style={"backgroundColor": "#fffbeb", "border": "1px solid #fef3c7"})
                        
                    ], width=12, lg=7, className="ps-4"),
                ]),
                
                # SEÇÃO: REGRA DE NEGÓCIO DO SCORE
                html.Hr(style={"margin": "24px 0", "borderColor": "#e2e8f0"}),
                
                html.Div([
                    html.Div("SCORE DE PRIORIDADE", className="macos-section-title mb-3"),
                    
                    html.P([
                        "O ",
                        html.Strong("Score de Prioridade"),
                        " (0-100) define a urgência de ação. ",
                        "Calculado automaticamente com 4 fatores:"
                    ], style={"fontSize": "0.9rem", "color": "#475569", "marginBottom": "16px"}),
                    
                    # Fórmula Visual
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-calculator me-2", style={"color": "#E20613"}),
                            html.Strong("Fórmula do Score:")
                        ], className="mb-2"),
                        html.Code(
                            "Score = (Aprovação × 40%) + (P70 × 30%) + (Volume × 20%) + (Tendência × 10%)",
                            style={
                                "display": "block",
                                "backgroundColor": "#f1f5f9",
                                "padding": "12px 16px",
                                "borderRadius": "8px",
                                "fontSize": "0.85rem",
                                "fontFamily": "monospace",
                                "color": "#1e293b"
                            }
                        )
                    ], className="mb-4"),
                    
                    # Tabela de Pesos
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.Span("40%", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#E20613"}),
                                    html.Div("Aprovação", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#64748b"})
                                ], className="text-center"),
                                html.Small("Menor % = Maior score", style={"color": "#94a3b8", "fontSize": "0.7rem"})
                            ], className="text-center p-3 bg-light rounded")
                        ], width=6, md=3, className="mb-2"),
                        
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.Span("30%", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#E20613"}),
                                    html.Div("P70 (Custo)", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#64748b"})
                                ], className="text-center"),
                                html.Small("Teto R$ 2.000", style={"color": "#94a3b8", "fontSize": "0.7rem"})
                            ], className="text-center p-3 bg-light rounded")
                        ], width=6, md=3, className="mb-2"),
                        
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.Span("20%", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#0ea5e9"}),
                                    html.Div("Volume OS", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#64748b"})
                                ], className="text-center"),
                                html.Small("Teto 500 OS", style={"color": "#94a3b8", "fontSize": "0.7rem"})
                            ], className="text-center p-3 bg-light rounded")
                        ], width=6, md=3, className="mb-2"),
                        
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.Span("10%", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#f59e0b"}),
                                    html.Div("Tendência", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#64748b"})
                                ], className="text-center"),
                                html.Small("Queda > 15% = Alerta", style={"color": "#94a3b8", "fontSize": "0.7rem"})
                            ], className="text-center p-3 bg-light rounded")
                        ], width=6, md=3, className="mb-2"),
                    ], className="g-2"),
                    
                    # Nota de ordenação
                    html.Div([
                        html.I(className="bi bi-sort-down me-2", style={"color": "#64748b"}),
                        html.Span("Tabela ordenada por Score (maior primeiro) — itens que requerem ação imediata ficam no topo.",
                                  style={"fontSize": "0.8rem", "color": "#64748b"})
                    ], className="mt-3 p-2 border-start border-3", style={"borderColor": "#E20613 !important"})
                    
                ]),
                
                # SEÇÃO: BENCHMARK DE MERCADO
                html.Hr(style={"margin": "24px 0", "borderColor": "#e2e8f0"}),
                
                html.Div([
                    html.Div("BENCHMARK DE MERCADO", className="macos-section-title mb-3"),
                    
                    html.P([
                        "A coluna ",
                        html.Strong("Recomendação"),
                        " pode exibir o desvio do P70 em relação ao ",
                        html.Strong("benchmark de mercado"),
                        " — um valor de referência calculado pelo ",
                        html.Strong("Motor de Pricing"),
                        "."
                    ], style={"fontSize": "0.9rem", "color": "#475569", "marginBottom": "16px"}),
                    
                    # Fórmula
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-graph-up-arrow me-2", style={"color": "#0ea5e9"}),
                            html.Strong("Como é calculado:")
                        ], className="mb-2"),
                        html.Code(
                            "Benchmark = P70 de mercado para o mesmo tipo de Mão de Obra (ref_total)",
                            style={
                                "display": "block",
                                "backgroundColor": "#f1f5f9",
                                "padding": "12px 16px",
                                "borderRadius": "8px",
                                "fontSize": "0.85rem",
                                "fontFamily": "monospace",
                                "color": "#1e293b"
                            }
                        )
                    ], className="mb-3"),
                    
                    # Explicação
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-bar-chart-fill me-2", style={"color": "#0ea5e9", "fontSize": "1.2rem"}),
                            html.Div([
                                html.Div("Valor de Mercado (P70)", style={"fontWeight": "700", "fontSize": "0.85rem", "color": "#0ea5e9"}),
                                html.Div("Percentil 70 do valor total aprovado para o mesmo tipo de MO no mercado nacional", style={"fontSize": "0.78rem", "color": "#64748b"})
                            ], className="ms-2")
                        ], className="d-flex align-items-center")
                    ], className="macos-card mb-3"),
                    
                    # Como interpretar
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-info-circle-fill me-2", style={"color": "#64748b"}),
                            html.Strong("Como interpretar:", style={"color": "#1e293b"})
                        ], className="mb-2"),
                        html.Div([
                            html.Div([
                                html.Span("+20% vs benchmark", style={"fontFamily": "monospace", "fontSize": "0.8rem", "color": "#E20613", "fontWeight": "600"}),
                                html.Span(" — P70 está 20% acima do valor de referência do mercado", style={"fontSize": "0.8rem", "color": "#64748b"})
                            ], className="mb-1"),
                            html.Div([
                                html.Span("-15% vs benchmark", style={"fontFamily": "monospace", "fontSize": "0.8rem", "color": "#10b981", "fontWeight": "600"}),
                                html.Span(" — P70 está 15% abaixo do mercado (bom)", style={"fontSize": "0.8rem", "color": "#64748b"})
                            ]),
                        ], className="ps-4")
                    ], className="p-3 rounded", style={"backgroundColor": "#f8fafc", "border": "1px solid #e2e8f0"})
                    
                ])
                
            ], className="macos-modal-body"),
            
        ], id="farol-help-modal", size="xl", is_open=False, centered=True, contentClassName="macos-modal-content"),
        
    ], className="farol-section p-4", style={
        "backgroundColor": "#f8fafc",
        "minHeight": "calc(100vh - 60px)"
    })


def get_farol_page_layout() -> html.Div:
    """
    Retorna o layout da página do Farol para ser usado no router.
    """
    return html.Div([
        render_farol_section()
    ], id="farol-page-content")
