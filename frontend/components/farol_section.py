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
from frontend.components.help_modal import build_help_modal, info_block, formula_code
from frontend.components.modal_components import (
    pipeline, spotlight, timeline_step, annotation, mini_formula
)


# ─── Estilo auxiliar para intro de cada tab ───
_INTRO = {"fontSize": "0.88rem", "color": "#475569", "lineHeight": "1.7"}


def _build_farol_help_modal():
    """Gera o modal de help do Farol usando o design system Edenred Premium."""
    return build_help_modal(
        modal_id="farol-help-modal",
        icon_class="bi-stoplights-fill",
        title="Guia do Farol",
        subtitle="Performance da Regulação Inteligente",
        sections=[
            # ════════════════════════════════════════════
            # TAB 1: CORES DO FAROL
            # ════════════════════════════════════════════
            {
                "id": "cores",
                "label": "Cores",
                "content": html.Div([
                    html.P(
                        "O farol classifica a performance de cada combinação "
                        "Peça + Tipo de Serviço em 3 zonas. Pense como um "
                        "semáforo: verde é \"seguro\", vermelho é \"parar e agir\".",
                        style=_INTRO,
                    ),

                    # ── Spotlight: conceito visual do limiar ──
                    spotlight(
                        "80%", "LIMIAR VERDE", "8 de cada 10 itens aprovados pela RI",
                        color="#10b981", bg_var="rgba(16,185,129,0.06)",
                    ),

                    # ── Zonas detalhadas ──
                    annotation(
                        icon="bi-check-circle-fill",
                        icon_color="#10b981", icon_bg="rgba(16,185,129,0.1)",
                        title="Verde — RI ≥ 80%",
                        text="A automática negociou preço em pelo menos 8 de "
                             "cada 10 itens. Exemplo: Filtro de Óleo Motor com "
                             "150 OS e 85% Auto — performando bem, sem ação necessária.",
                        border_color="#10b981", card_bg="rgba(16,185,129,0.02)",
                    ),
                    annotation(
                        icon="bi-exclamation-triangle-fill",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Amarelo — RI 50–80%",
                        text="Entre 5 e 8 itens aprovados automaticamente. "
                             "Há espaço para melhoria. Exemplo: Pastilha de Freio "
                             "com 63% Auto e 200 OS — vale negociar referências com o fornecedor.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                    annotation(
                        icon="bi-x-circle-fill",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Vermelho — RI < 50%",
                        text="Mais da metade exige aprovação humana. "
                             "Exemplo: Correia Dentada com 28% Auto e 90 OS — "
                             "preço de referência provavelmente desatualizado. Ação urgente.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-shield-exclamation",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Regra Crítica: Hard Limit < 10%",
                        text="Se a taxa RI for menor que 10%, o item é SEMPRE "
                             "vermelho — independente de volume ou valor. "
                             "Isso evita mascarar peças que quase nunca passam pela automática.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 2: O QUE SIGNIFICAM AS COLUNAS
            # ════════════════════════════════════════════
            {
                "id": "colunas",
                "label": "Colunas",
                "content": html.Div([
                    html.P(
                        "Cada linha da tabela é uma combinação única de "
                        "Peça + Tipo de Serviço. As colunas mostram a saúde "
                        "dessa combinação:",
                        style=_INTRO,
                    ),

                    # ── Fluxo: de onde vêm os dados ──
                    pipeline([
                        {"icon": "bi-database-fill", "label": "Databricks",
                         "color": "#E20613", "bg": "rgba(226,6,19,0.08)"},
                        {"icon": "bi-arrow-repeat", "label": "Sync 6 meses",
                         "color": "#0ea5e9", "bg": "rgba(14,165,233,0.08)"},
                        {"icon": "bi-hdd-fill", "label": "DuckDB",
                         "color": "#f59e0b", "bg": "rgba(245,158,11,0.08)"},
                        {"icon": "bi-table", "label": "Tabela Farol",
                         "color": "#10b981", "bg": "rgba(16,185,129,0.08)"},
                    ]),

                    # ── Colunas detalhadas ──
                    annotation(
                        icon="bi-robot", icon_color="#10b981",
                        icon_bg="rgba(16,185,129,0.1)",
                        title="AUTO (%)",
                        text="Percentual de itens aprovados automaticamente "
                             "pela Regulação Inteligente. Se mostra 72%, "
                             "significa que 72 de cada 100 itens dessa peça "
                             "passaram sem intervenção humana.",
                        border_color="#10b981", card_bg="rgba(16,185,129,0.02)",
                    ),
                    annotation(
                        icon="bi-person-fill", icon_color="#64748b",
                        icon_bg="rgba(100,116,139,0.1)",
                        title="HUMANA (%)",
                        text="Complemento da AUTO. Se AUTO = 72%, "
                             "HUMANA = 28%. São os itens que exigiram que "
                             "um analista revisasse e aprovasse manualmente o preço.",
                        border_color="#64748b", card_bg="rgba(100,116,139,0.02)",
                    ),
                    annotation(
                        icon="bi-currency-dollar", icon_color="#E20613",
                        icon_bg="rgba(226,6,19,0.08)",
                        title="P70 (R$)",
                        text="Percentil 70 do valor aprovado. Ou seja, "
                             "70% dos itens custam até esse valor. "
                             "É a referência de preço de mercado. "
                             "Exemplo: P70 = R$ 350 → a maioria das peças "
                             "dessa combinação custa até R$ 350.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                    annotation(
                        icon="bi-clipboard2-data", icon_color="#0ea5e9",
                        icon_bg="rgba(14,165,233,0.08)",
                        title="OS (qtd)",
                        text="Total de Ordens de Serviço com essa combinação "
                             "no período selecionado. Quanto maior o número, "
                             "maior o impacto financeiro se o RI não estiver performando.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-speedometer2", icon_color="#1e293b",
                        icon_bg="rgba(30,41,59,0.08)",
                        title="SCORE (0–100)",
                        text="Nota de urgência que combina 4 fatores: "
                             "Negociação (40%) + Valor P70 (30%) + Volume (20%) "
                             "+ Tendência (10%). Score alto = ação prioritária.",
                        border_color="#1e293b", card_bg="rgba(30,41,59,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 3: SCORE — COMO É CALCULADO
            # ════════════════════════════════════════════
            {
                "id": "score",
                "label": "Score",
                "content": html.Div([
                    html.P(
                        "O Score é uma nota de 0 a 100 que prioriza quais "
                        "combinações Peça + MO merecem atenção primeiro. "
                        "Quanto maior o score, mais urgente a intervenção.",
                        style=_INTRO,
                    ),

                    # ── Timeline visual dos 4 componentes ──
                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "Negociação — Peso 40%",
                            "Quanto menor a taxa AUTO, maior a pontuação. "
                            "Item com 20% AUTO recebe score ~80. "
                            "Item com 90% AUTO recebe score ~10.",
                            formula="Score_Neg = 100 - pct_auto",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Valor P70 — Peso 30%",
                            "Peças caras pesam mais. O teto é R$ 2.000 para "
                            "evitar distorções. Peça de R$ 1.500 = score 75. "
                            "Peça de R$ 200 = score 10.",
                            formula="Score_P70 = min(100, (P70/2000) × 100)",
                        ),
                        timeline_step(
                            3, "#0ea5e9",
                            "Volume — Peso 20%",
                            "Mais OS = mais impacto. O teto é 500 OS para "
                            "normalizar. Combinação com 300 OS = score 60. "
                            "Combinação com 50 OS = score 10.",
                            formula="Score_Vol = min(100, (OS/500) × 100)",
                        ),
                        timeline_step(
                            4, "#64748b",
                            "Tendência — Peso 10%",
                            "Quedas de performance > 15% entre meses disparam "
                            "alerta. Meses parciais são ignorados para "
                            "evitar falsos alarmes.",
                            formula="Score_Tend = min(100, (|queda|/20) × 100)",
                        ),
                    ], className="step-timeline"),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    # ── Fórmula final ──
                    html.Div([
                        html.Span("Fórmula final: ", style={
                            "fontWeight": "700", "fontSize": "0.82rem",
                            "color": "#1e293b",
                        }),
                        formula_code(
                            "SCORE = 0.4×Neg + 0.3×P70 + 0.2×Vol + 0.1×Tend"
                        ),
                    ], style={
                        "display": "flex", "alignItems": "center", "gap": "8px",
                    }),

                    # ── Exemplo prático ──
                    annotation(
                        icon="bi-lightbulb-fill",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Exemplo prático",
                        text="Correia Dentada + Troca: AUTO 25%, P70 R$ 480, "
                             "180 OS, queda -18%. "
                             "Score = 0.4×75 + 0.3×24 + 0.2×36 + 0.1×90 = "
                             "30 + 7.2 + 7.2 + 9 = 53.4 → Score 53.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 4: OPORTUNIDADES
            # ════════════════════════════════════════════
            {
                "id": "oportunidades",
                "label": "Oportunidades",
                "content": html.Div([
                    html.P(
                        "Oportunidades mostram onde há dinheiro na mesa. "
                        "São combinações com RI abaixo de 80% — ou seja, "
                        "a automática não está conseguindo negociar preço.",
                        style=_INTRO,
                    ),

                    spotlight(
                        "RI < 80%", "CRITÉRIO DE SELEÇÃO",
                        "Apenas chaves amarelas e vermelhas",
                        color="#f59e0b", bg_var="rgba(245,158,11,0.06)",
                    ),

                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "Filtrar por RI < 80%",
                            "Exclui tudo que já está verde (performando bem). "
                            "Foca apenas nas combinações onde a automática "
                            "está falhando em negociar.",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Rankear por Impacto Financeiro",
                            "Impacto = Volume de OS × Valor P70. "
                            "Peças caras com alto volume vêm primeiro. "
                            "Exemplo: Filtro de Ar com 300 OS e P70 R$ 180 "
                            "= impacto de R$ 54k.",
                            formula="Impacto = qtd_os × P70",
                        ),
                        timeline_step(
                            3, "#10b981",
                            "Priorizar ações nas Top 10",
                            "O topo da lista = maior economia potencial "
                            "se conseguir elevar o RI para 80%+. "
                            "Foque nas primeiras 10 chaves para máximo retorno.",
                        ),
                    ], className="step-timeline"),

                    annotation(
                        icon="bi-graph-up-arrow",
                        icon_color="#10b981", icon_bg="rgba(16,185,129,0.1)",
                        title="Meta: transformar Amarelo em Verde",
                        text="Se uma chave sai de 60% para 80% AUTO, os itens "
                             "passam a ser negociados automaticamente pela RI — "
                             "reduzindo tempo de aprovação e custo operacional.",
                        border_color="#10b981", card_bg="rgba(16,185,129,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 5: COMO AGIR (NOVA)
            # ════════════════════════════════════════════
            {
                "id": "como-agir",
                "label": "Como Agir",
                "content": html.Div([
                    html.P(
                        "Guia rápido de ação baseado na cor do farol. "
                        "O objetivo final é mover itens de Vermelho → Amarelo → Verde.",
                        style=_INTRO,
                    ),

                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "Vermelho (RI < 50%) → Ação Imediata",
                            "Revisar referências de preço no Pricing Engine. "
                            "Provavelmente a tabela de referência está "
                            "desatualizada ou o fornecedor mudou de faixa de preço. "
                            "Abrir chamado com a equipe de Pricing.",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Amarelo (RI 50–80%) → Ajuste Fino",
                            "Analisar os motivos de reprovação nos Logs de "
                            "Intervenção Humana (seção abaixo da tabela). "
                            "Verificar se o P70 está calibrado. "
                            "Conversar com o fornecedor sobre preço de mercado.",
                        ),
                        timeline_step(
                            3, "#10b981",
                            "Verde (RI ≥ 80%) → Monitorar",
                            "Não precisa de ação. Acompanhar a tendência — "
                            "se a pill de tendência mostrar queda > 15%, "
                            "o item vai para amarelo automaticamente.",
                        ),
                    ], className="step-timeline"),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-journal-text",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Dica: Use os Logs de Intervenção",
                        text="Expanda a seção \"Logs de Intervenção Humana\" "
                             "abaixo da tabela para ver exatamente quais "
                             "itens foram aprovados manualmente e por qual motivo. "
                             "Isso revela padrões de reprovação.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-file-earmark-code",
                        icon_color="#8b5cf6", icon_bg="rgba(139,92,246,0.08)",
                        title="Referência Power BI",
                        text="Os dados do Farol são calculados com a mesma lógica "
                             "do relatório Power BI corporativo (mensagem_log com "
                             "padrão 'Aprovação Automática'). Em caso de dúvida, "
                             "compare os números com o PBI.",
                        border_color="#8b5cf6", card_bg="rgba(139,92,246,0.02)",
                    ),
                ])
            },
        ]
    )


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
        # MODAL DE AJUDA — EDENRED PREMIUM (via factory)
        # =====================================================================
        _build_farol_help_modal(),
        
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
