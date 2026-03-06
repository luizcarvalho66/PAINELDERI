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
                    html.I(className="bi bi-bar-chart-line-fill me-1", style={"fontSize": "0.7rem"}),
                    "Regulação Inteligente • Corretivas"
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
            # Header da seção - Alinhado com branding Edenred
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Barra lateral vermelha (accent)
                        html.Div(style={
                            "width": "4px", "height": "28px",
                            "background": "linear-gradient(180deg, #E20613, #FF4D5A)",
                            "borderRadius": "2px", "marginRight": "12px"
                        }),
                        html.Div([
                            html.H5([
                                html.I(className="bi bi-journal-text me-2", 
                                       style={"color": "#E20613", "fontSize": "1.1rem"}),
                                "Logs de Intervenção Humana",
                            ], className="mb-0 fw-bold", style={"fontSize": "1.05rem", "color": "#1e293b"}),
                            html.Small(
                                "Itens aprovados manualmente • Não passaram na automática", 
                                className="text-muted",
                                style={"fontSize": "0.78rem", "letterSpacing": "0.02em"}
                            )
                        ])
                    ], className="d-flex align-items-center"),
                ], width=8),
                
                # Toggle para expandir/colapsar (estilo premium)
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-chevron-down me-1", id="logs-toggle-icon"),
                        "Expandir"
                    ], id="logs-toggle-btn", 
                       className="btn btn-sm",
                       style={
                           "backgroundColor": "#f1f5f9",
                           "color": "#64748b",
                           "border": "1px solid #e2e8f0",
                           "borderRadius": "8px",
                           "fontFamily": "Ubuntu, sans-serif",
                           "fontWeight": "600",
                           "fontSize": "0.82rem",
                           "padding": "6px 14px",
                           "transition": "all 0.2s ease"
                       })
                ], width=4, className="d-flex justify-content-end align-items-center"),
            ], className="mb-3 align-items-center"),
            
            # Conteúdo colapsável
            dbc.Collapse([
                # Filtros com classe premium
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
                
                # Container da tabela de logs com loading Edenred
                dcc.Loading(
                    id="logs-loading-overlay",
                    type="default",
                    custom_spinner=html.Div([
                        html.Img(
                            src="/assets/edenred-minilogo.webp",
                            className="farol-loading-logo"
                        ),
                        html.Div("Carregando logs...", className="farol-loading-text"),
                        html.Div(className="farol-loading-bar-track", children=[
                            html.Div(className="farol-loading-bar-fill")
                        ])
                    ], className="farol-loading-container"),
                    children=html.Div(
                        id="logs-table-container",
                        className="logs-table-wrapper",
                        style={
                            "maxHeight": "400px",
                            "overflowY": "auto",
                            "minHeight": "100px",
                        }
                    ),
                    parent_className="farol-loading-parent",
                    overlay_style={"visibility": "visible", "backgroundColor": "#ffffff"},
                    color="#E20613"
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
                        className="text-muted d-block text-center mt-2",
                        style={"fontSize": "0.78rem", "fontFamily": "Ubuntu, sans-serif"}
                    )
                ], className="d-flex flex-column align-items-center mt-3"),
                
            ], id="logs-collapse", is_open=False),
            
        ], className="farol-table-section p-4 bg-white rounded shadow-sm mt-4"),
        
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
        # MODAL DE AJUDA - REDESIGN "APPLE/MACOS STYLE"
        # =====================================================================
        dbc.Modal([
            # HEADER APPLE-LIKE
            dbc.ModalHeader([
                html.Div([
                    html.Div([
                        html.I(className="bi bi-stoplights-fill", style={"color": "#E20613", "fontSize": "1.2rem"}),
                    ], style={
                        "width": "42px", "height": "42px", "borderRadius": "12px",
                        "backgroundColor": "rgba(226, 6, 19, 0.08)",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "marginRight": "16px"
                    }),
                    html.Div([
                        html.Span("Guia do Farol de Performance", style={
                            "fontWeight": "700", "fontSize": "1.15rem", "color": "#1e293b",
                            "fontFamily": "Ubuntu, sans-serif", "letterSpacing": "-0.02em",
                            "display": "block", "marginBottom": "2px"
                        }),
                        html.Div("Entenda como analisamos a performance da Regulação Inteligente", style={
                            "fontSize": "0.85rem", "color": "#64748b", "fontWeight": "400"
                        })
                    ])
                ], className="d-flex align-items-center")
            ], close_button=True, class_name="macos-modal-header"),
            
            # BODY CLASSY
            dbc.ModalBody([
                dbc.Tabs([
                    
                    # ===================== TAB 1: CORES =====================
                    dbc.Tab([
                        html.Div([
                            # Intro amigável
                            html.P([
                                "O Farol analisa cada combinação ",
                                html.Strong("Peça + Tipo de Serviço", style={"color": "#1e293b"}),
                                " e avalia se o time de RI está conseguindo ",
                                html.Strong("negociar os preços", style={"color": "#1e293b"}),
                                " com sucesso."
                            ], style={"fontSize": "0.95rem", "color": "#475569", "marginBottom": "24px", "lineHeight": "1.6"}),
                            
                            # 3 Cards Apple-glass
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-check-circle-fill", style={"color": "#10b981", "fontSize": "1.8rem"}),
                                        ], className="text-center mb-3"),
                                        html.Div("Performando Bem", style={"fontWeight": "700", "color": "#1e293b", "fontSize": "0.95rem", "textAlign": "center"}),
                                        html.Div("RI ≥ 80%", style={"fontSize": "1.4rem", "fontWeight": "800", "color": "#10b981", "textAlign": "center", "margin": "8px 0 12px"}),
                                        html.P("O time de RI conseguiu negociar o preço em 8 ou mais de cada 10 itens. Excelente performance!", 
                                               style={"fontSize": "0.85rem", "color": "#64748b", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "0"})
                                    ], className="apple-glass-card success-tint h-100")
                                ], md=4, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#f59e0b", "fontSize": "1.8rem"}),
                                        ], className="text-center mb-3"),
                                        html.Div("Atenção Necessária", style={"fontWeight": "700", "color": "#1e293b", "fontSize": "0.95rem", "textAlign": "center"}),
                                        html.Div("RI 50–80%", style={"fontSize": "1.4rem", "fontWeight": "800", "color": "#f59e0b", "textAlign": "center", "margin": "8px 0 12px"}),
                                        html.P("O RI negocia entre 5 e 8 de cada 10 itens. Há espaço para melhorar — vale investigar a causa.", 
                                               style={"fontSize": "0.85rem", "color": "#64748b", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "0"})
                                    ], className="apple-glass-card warning-tint h-100")
                                ], md=4, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-x-circle-fill", style={"color": "#E20613", "fontSize": "1.8rem"}),
                                        ], className="text-center mb-3"),
                                        html.Div("Ação Prioritária", style={"fontWeight": "700", "color": "#1e293b", "fontSize": "0.95rem", "textAlign": "center"}),
                                        html.Div("RI < 50%", style={"fontSize": "1.4rem", "fontWeight": "800", "color": "#E20613", "textAlign": "center", "margin": "8px 0 12px"}),
                                        html.P("O RI negocia menos da metade. Ação urgente necessária para reverter essa tendência crítica.", 
                                               style={"fontSize": "0.85rem", "color": "#64748b", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "0"})
                                    ], className="apple-glass-card danger-tint h-100")
                                ], md=4, className="mb-3"),
                            ], className="g-3 mt-1"),
                            
                            # Nota sobre regra crítica
                            html.Div([
                                html.I(className="bi bi-exclamation-diamond-fill me-2", style={"color": "#E20613"}),
                                html.Span("Itens com menos de 10% de negociação são ", style={"fontSize": "0.8rem", "color": "#475569"}),
                                html.Strong("sempre Vermelho", style={"color": "#E20613"}),
                                html.Span(", independente de outros fatores.", style={"fontSize": "0.8rem", "color": "#475569"})
                            ], className="d-flex align-items-center p-3 rounded mt-3",
                               style={"backgroundColor": "rgba(226, 6, 19, 0.05)", "border": "1px solid rgba(226,6,19,0.15)"}),
                            
                        ], style={"padding": "8px 0"})
                    ], label="Cores do Farol", tab_id="tab-cores",
                       label_style={"fontWeight": "600", "fontSize": "0.85rem"},
                       active_label_style={"color": "#E20613", "borderBottomColor": "#E20613"}),
                    
                    # ===================== TAB 2: COLUNAS =====================
                    dbc.Tab([
                        html.Div([
                            html.P([
                                "Cada linha da tabela representa uma combinação única de ",
                                html.Strong("Peça + Tipo de Serviço"),
                                ". As colunas mostram:"
                            ], style={"fontSize": "0.9rem", "color": "#475569", "marginBottom": "16px", "lineHeight": "1.6"}),
                            
                            # Visualização em Colunas Verticais com Artefatos (Ícones)
                            dbc.Row([
                                # COLUNA: AUTO
                                dbc.Col([
                                    html.Div([
                                        html.Div("AUTO", className="apple-column-header col-header-auto"),
                                        html.Div([
                                            html.Div(html.I(className="bi bi-robot", style={"color": "#10b981"}), className="apple-column-body-icon"),
                                            html.Div("% dos itens onde o RI conseguiu negociar reduzindo o valor.", className="apple-column-body-desc")
                                        ], className="apple-column-body")
                                    ], className="apple-vertical-column")
                                ], width=5, md=2, className="mb-3 px-1"),
                                
                                # COLUNA: HUMANA
                                dbc.Col([
                                    html.Div([
                                        html.Div("HUMANA", className="apple-column-header col-header-humana"),
                                        html.Div([
                                            html.Div(html.I(className="bi bi-person", style={"color": "#64748b"}), className="apple-column-body-icon"),
                                            html.Div("% dos itens mantidos sem conseguir negociação.", className="apple-column-body-desc")
                                        ], className="apple-column-body")
                                    ], className="apple-vertical-column")
                                ], width=5, md=2, className="mb-3 px-1"),
                                
                                # COLUNA: P70 (Valor monetário)
                                dbc.Col([
                                    html.Div([
                                        html.Div("P70", className="apple-column-header col-header-p70"),
                                        html.Div([
                                            html.Div(html.I(className="bi bi-tag", style={"color": "#E20613"}), className="apple-column-body-icon"),
                                            html.Div("Valor onde 70% dos itens da peça custam até este limite.", className="apple-column-body-desc")
                                        ], className="apple-column-body")
                                    ], className="apple-vertical-column")
                                ], width=5, md=3, className="mb-3 px-1"),
                                
                                # COLUNA: OS (Volume)
                                dbc.Col([
                                    html.Div([
                                        html.Div("OS", className="apple-column-header col-header-os"),
                                        html.Div([
                                            html.Div(html.I(className="bi bi-files", style={"color": "#0ea5e9"}), className="apple-column-body-icon"),
                                            html.Div("Quantidade total de O.S. com essa combinação.", className="apple-column-body-desc")
                                        ], className="apple-column-body")
                                    ], className="apple-vertical-column")
                                ], width=5, md=2, className="mb-3 px-1"),
                                
                                # COLUNA: SCORE (Prioridade)
                                dbc.Col([
                                    html.Div([
                                        html.Div("SCORE", className="apple-column-header col-header-score"),
                                        html.Div([
                                            html.Div(html.I(className="bi bi-star", style={"color": "#1e293b"}), className="apple-column-body-icon"),
                                            html.Div("Nota (0-100) da inteligência que define a urgência de ação.", className="apple-column-body-desc")
                                        ], className="apple-column-body")
                                    ], className="apple-vertical-column")
                                ], width=5, md=3, className="mb-3 px-1"),
                                
                            ], className="g-1 justify-content-center"),
                            
                            # Dica
                            html.Div([
                                html.I(className="bi bi-lightbulb-fill me-2", style={"color": "#f59e0b"}),
                                html.Span("A tabela vem ordenada por Score (maior primeiro). Os itens do topo são os que mais precisam de ação.", 
                                          style={"fontSize": "0.8rem", "color": "#64748b"})
                            ], className="d-flex align-items-center p-3 rounded mt-3",
                               style={"backgroundColor": "#fffbeb", "border": "1px solid #fef3c7"}),
                            
                        ], style={"padding": "8px 0"})
                    ], label="Colunas da Tabela", tab_id="tab-colunas",
                       label_style={"fontWeight": "600", "fontSize": "0.85rem"},
                       active_label_style={"color": "#E20613", "borderBottomColor": "#E20613"}),
                    
                    # ===================== TAB 3: OPORTUNIDADES =====================
                    dbc.Tab([
                        html.Div([
                            html.P([
                                "O modo ",
                                html.Strong("Oportunidades"),
                                " filtra automaticamente as chaves onde o RI ",
                                html.Strong("pode melhorar"),
                                ", priorizadas pelo impacto financeiro."
                            ], style={"fontSize": "0.9rem", "color": "#475569", "marginBottom": "20px", "lineHeight": "1.6"}),
                            
                            # Card principal
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#f59e0b", "fontSize": "1.8rem"}),
                                        ], className="text-center mb-3"),
                                        html.Div("Atenção Necessária", style={"fontWeight": "700", "color": "#1e293b", "fontSize": "0.95rem", "textAlign": "center"}),
                                        html.Div("RI 50–80%", style={"fontSize": "1.4rem", "fontWeight": "800", "color": "#f59e0b", "textAlign": "center", "margin": "8px 0 12px"}),
                                        html.P("Representam 70% ou mais do valor financeiro das oportunidades.", 
                                               style={"fontSize": "0.85rem", "color": "#475569", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "8px"}),
                                        html.Div("Foco principal da operação. Agir rápido.", style={"textAlign": "center", "fontSize": "0.78rem", "fontWeight": "600", "color": "#b91c1c"})
                                    ], className="apple-glass-card danger-tint h-100")
                                ], md=6, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.I(className="bi bi-info-circle-fill", style={"color": "#10b981", "fontSize": "1.8rem"}),
                                        ], className="text-center mb-3"),
                                        html.Div("Baixa Priorização", style={"fontWeight": "700", "color": "#1e293b", "fontSize": "0.95rem", "textAlign": "center"}),
                                        html.P("Correspondem a 30% ou menos do valor de oportunidade total.", 
                                               style={"fontSize": "0.85rem", "color": "#475569", "textAlign": "center", "lineHeight": "1.5", "marginBottom": "8px"}),
                                        html.Div("Ações de refinamento pontuais.", style={"textAlign": "center", "fontSize": "0.78rem", "fontWeight": "600", "color": "#059669"})
                                    ], className="apple-glass-card success-tint h-100")
                                ], md=6, className="mb-3"),
                            ], className="g-3 mt-1"),
                            
                            # Nota sobre regra crítica
                            html.Div([
                                html.I(className="bi bi-chat-square-text-fill me-2", style={"color": "#0ea5e9"}),
                                html.Strong("Na prática: ", style={"color": "#1e293b"}),
                                html.Span(
                                    "Se uma peça cara aparece com RI de 74%, significa que em 26% dos casos o preço original foi mantido. Quanto mais OS e maior o valor, maior a economia potencial.",
                                    style={"fontSize": "0.8rem", "color": "#64748b"}
                                )
                            ], className="d-flex align-items-start p-3 rounded mt-2",
                               style={"backgroundColor": "#f0f9ff", "border": "1px solid #bae6fd"}),
                            
                        ], style={"padding": "8px 0"})
                    ], label="Oportunidades", tab_id="tab-oportunidades",
                       label_style={"fontWeight": "600", "fontSize": "0.85rem"},
                       active_label_style={"color": "#E20613", "borderBottomColor": "#E20613"}),
                    
                    # ===================== TAB 4: SCORE =====================
                    dbc.Tab([
                        html.Div([
                            html.P([
                                "O ",
                                html.Strong("Score de Prioridade"),
                                " (0 a 100) combina 4 fatores para dizer ",
                                html.Strong("quais itens merecem atenção primeiro"),
                                "."
                            ], style={"fontSize": "0.9rem", "color": "#475569", "marginBottom": "20px", "lineHeight": "1.6"}),
                            
                            # 4 cards horizontais com os pesos
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Div("40%", style={"fontSize": "2rem", "fontWeight": "800", "color": "#E20613", "lineHeight": "1", "letterSpacing": "-0.03em"}),
                                        html.Div("Itens de alto valor financeiro que estão sendo aprovados sem variação de custo pelo RI. Precisidão do modelo ao indicar 'ação imediata' justificada pela criticidade.", 
                                                 style={"fontSize": "0.8rem", "color": "#64748b", "lineHeight": "1.5"})
                                    ], className="apple-glass-card danger-tint text-center h-100")
                                ], xs=6, md=3, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div("3: Vermelhos (E)", className="badge bg-danger mb-2", style={"fontSize": "0.75rem"}),
                                        html.P(html.Strong("Oportunidades de Valor Baixo"), style={"fontSize": "0.85rem", "color": "#1e293b", "marginBottom": "8px"}),
                                        html.Div("Mesmo padrão de ausência de negociação, porém o impacto marginal por peça é reduzido (Abaixo de P70). Demanda ação posterior para refinamento.", 
                                                 style={"fontSize": "0.8rem", "color": "#64748b", "lineHeight": "1.5"})
                                    ], className="apple-glass-card danger-tint text-center h-100")
                                ], xs=6, md=3, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div("2: Amarelos (A)", className="badge mb-2", style={"backgroundColor": "#0ea5e9", "color": "#fff", "fontSize": "0.75rem"}),
                                        html.P(html.Strong("Prioridade Laranja - Elevado"), style={"fontSize": "0.85rem", "color": "#1e293b", "marginBottom": "8px"}),
                                        html.Div("Itens caros (> P70) e o RI oscila na taxa de desconto (50%-80%). Mostra um gargalo em peças estratégicas. Requer atenção para voltar aos eixos.", 
                                                 style={"fontSize": "0.8rem", "color": "#64748b", "lineHeight": "1.5"})
                                    ], className="apple-glass-card info-tint text-center h-100")
                                ], xs=6, md=3, className="mb-3"),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Div("1: Amarelos (E)", className="badge bg-warning text-dark mb-2", style={"fontSize": "0.75rem"}),
                                        html.P(html.Strong("Radar Moderado"), style={"fontSize": "0.85rem", "color": "#1e293b", "marginBottom": "8px"}),
                                        html.Div("Preço baixo (< P70) mas volume em oscilação (50%-80%). Costumam indicar serviços frequentes e repetitivos, como substituições secundárias.", 
                                                 style={"fontSize": "0.8rem", "color": "#64748b", "lineHeight": "1.5"})
                                    ], className="apple-glass-card warning-tint text-center h-100")
                                ], xs=6, md=3, className="mb-3"),
                            ], className="g-2 mt-1"),
                            
                            # Resumo de leitura
                            html.Div([
                                html.I(className="bi bi-sort-down me-2", style={"color": "#E20613"}),
                                html.Span([
                                    "Score alto = ",
                                    html.Strong("agir primeiro"),
                                    ". A tabela já vem ordenada do maior para o menor."
                                ], style={"fontSize": "0.8rem", "color": "#475569"})
                            ], className="d-flex align-items-center p-3 rounded mt-3",
                               style={"backgroundColor": "#f1f5f9", "border": "1px solid #e2e8f0"}),
                            
                        ], style={"padding": "8px 0"})
                    ], label="Score", tab_id="tab-score",
                       label_style={"fontWeight": "600", "fontSize": "0.85rem"},
                       active_label_style={"color": "#E20613", "borderBottomColor": "#E20613"}),
                    
                ], id="farol-help-tabs", active_tab="tab-cores",
                   className="apple-tabs"),
                
            ], class_name="macos-modal-body"),
            
        ], id="farol-help-modal", size="lg", is_open=False, centered=True, 
           class_name="macos-modal-content", fade=True,
           style={"fontFamily": "Ubuntu, sans-serif"}),
        
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
