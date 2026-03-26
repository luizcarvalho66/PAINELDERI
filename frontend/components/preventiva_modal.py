# -*- coding: utf-8 -*-
"""
Preventiva Modals — Design System Edenred Premium.

Modais de ajuda para a seção de Preventiva:
- Fugas de Preventiva (prev-help-modal) — 5 tabs
- Top Ofensores / Ranking (prev-ranking-help-modal) — 3 tabs

Usa o factory build_help_modal() + componentes premium.

Author: Luiz Eduardo Carvalho
"""

from dash import html
from frontend.components.help_modal import build_help_modal, info_block, formula_code
from frontend.components.modal_components import (
    pipeline, spotlight, timeline_step, annotation, mini_formula
)

# ─── Estilo auxiliar para intro de cada tab ───
_INTRO = {"fontSize": "0.88rem", "color": "#475569", "lineHeight": "1.7"}


def render_preventiva_help_modal():
    """Modal de ajuda: Fugas de Preventiva — 5 tabs premium."""
    return build_help_modal(
        modal_id="prev-help-modal",
        icon_class="bi-shield-exclamation",
        title="Fugas de Preventiva",
        subtitle="Detecção de OS preventivas lançadas como corretivas",
        sections=[
            # ════════════════════════════════════════════
            # TAB 1: O QUE É
            # ════════════════════════════════════════════
            {
                "id": "conceito",
                "label": "O que é",
                "content": html.Div([
                    html.P(
                        "Uma Fuga de Preventiva acontece quando a oficina "
                        "abre uma OS corretiva para fazer um serviço que, "
                        "na verdade, é manutenção preventiva (troca de óleo, "
                        "filtros, etc). Isso distorce todos os indicadores.",
                        style=_INTRO,
                    ),

                    spotlight(
                        "~19.7%", "TAXA DE FUGA ATUAL",
                        "Quase 1 em cada 5 OS corretivas tem perfil preventivo",
                        color="#E20613", bg_var="rgba(226,6,19,0.06)",
                    ),

                    annotation(
                        icon="bi-graph-down-arrow",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Distorce SLA e custos",
                        text="Cada fuga infla o volume corretivo em +1 OS e "
                             "soma o custo na conta errada. Se 200 revisões "
                             "de 60k km caem como corretiva, o custo corretivo "
                             "sobe ~R$ 160k artificialmente.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                    annotation(
                        icon="bi-eye-slash-fill",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Perde histórico de revisões",
                        text="Revisões preventivas programadas ficam invisíveis "
                             "no tracking de manutenção. Isso impede planejar "
                             "a próxima revisão e compromete a vida útil do veículo.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                    annotation(
                        icon="bi-cash-stack",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Impacto financeiro duplo",
                        text="Orçamento corretivo fica inflado e o preventivo "
                             "parece subutilizado. Relatórios executivos mostram "
                             "cenário falso — mais corretivas, menos preventivas "
                             "do que a realidade.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 2: COMO DETECTAMOS
            # ════════════════════════════════════════════
            {
                "id": "deteccao",
                "label": "Detecção",
                "content": html.Div([
                    html.P(
                        "O sistema cruza os itens de OS corretivas com OS "
                        "preventivas para identificar peças que não deveriam "
                        "estar na corretiva:",
                        style=_INTRO,
                    ),

                    # ── Pipeline do fluxo de detecção ──
                    pipeline([
                        {"icon": "bi-wrench-adjustable", "label": "OS Corretiva",
                         "color": "#E20613", "bg": "rgba(226,6,19,0.08)"},
                        {"icon": "bi-plus-circle-fill", "label": "UNION ALL",
                         "color": "#0ea5e9", "bg": "rgba(14,165,233,0.08)"},
                        {"icon": "bi-tools", "label": "OS Preventiva",
                         "color": "#f59e0b", "bg": "rgba(245,158,11,0.08)"},
                        {"icon": "bi-shield-fill-check", "label": "Fuga?",
                         "color": "#10b981", "bg": "rgba(16,185,129,0.08)"},
                    ]),

                    # ── Steps detalhados ──
                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "UNION ALL dos itens corretivos + preventivos",
                            "Juntamos TODOS os itens de ambas as tabelas "
                            "por veículo e período. Isso replica o comportamento "
                            "do Power BI (tabela flat fItens).",
                            formula="UNION ALL itens_corretiva + itens_preventiva",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Contar peças com perfil preventivo por OS",
                            "Verificamos quantas peças de perfil preventivo "
                            "(Óleo Motor, Filtro de Óleo, etc.) cada OS possui. "
                            "Se ≥ 2 peças preventivas → a OS tem perfil.",
                            formula="HAVING COUNT(peças_preventivas) ≥ 2",
                        ),
                        timeline_step(
                            3, "#10b981",
                            "Classificar como fuga",
                            "Se a OS tem perfil preventivo MAS não está na "
                            "tabela de preventivas → é uma fuga. "
                            "A taxa é calculada sobre o total de OS com perfil.",
                            formula="Taxa = OS_fuga / OS_com_perfil × 100",
                        ),
                    ], className="step-timeline"),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-list-check",
                        icon_color="#64748b", icon_bg="rgba(100,116,139,0.1)",
                        title="Peças detectadas como preventivas",
                        text="Óleo Motor, Óleo Motor Galão 20L, Filtro de Óleo, "
                             "Óleo Motor Tonel 200L. Lista fixa validada contra "
                             "o relatório Power BI.",
                        border_color="#64748b", card_bg="rgba(100,116,139,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 3: KPIs MONITORADOS
            # ════════════════════════════════════════════
            {
                "id": "kpis",
                "label": "KPIs",
                "content": html.Div([
                    html.P(
                        "Indicadores que você vê na seção de Fugas e o que "
                        "cada um mede na prática:",
                        style=_INTRO,
                    ),

                    annotation(
                        icon="bi-percent",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Taxa de Fuga (%)",
                        text="De cada 100 OS com perfil preventivo, quantas "
                             "estão lançadas como corretiva. Meta: abaixo de 15%. "
                             "Acima de 20% → reunião de alinhamento com a rede.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                    annotation(
                        icon="bi-bar-chart-fill",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Evolução Mensal",
                        text="Gráfico de barras com a taxa de fuga dos últimos "
                             "6 meses. Observe a tendência: se subir consistentemente, "
                             "há um problema sistêmico na rede de oficinas.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-trophy-fill",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Top Ofensores",
                        text="Os 10 clientes com maior volume absoluto de fugas. "
                             "São os candidatos #1 para ação de campo — contato "
                             "direto, ajuste de contrato ou revisão de SLA.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                    annotation(
                        icon="bi-robot",
                        icon_color="#64748b", icon_bg="rgba(100,116,139,0.1)",
                        title="Silent Orders (SO)",
                        text="OS aprovadas sem intervenção humana (sistema autoarizou). "
                             "Calculado pela lógica do PBI: 1º aprovador = "
                             "'Autorizacao De Servico Programado' ou preventiva "
                             "sem aprovador final.",
                        border_color="#64748b", card_bg="rgba(100,116,139,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 4: COMO AGIR (NOVA)
            # ════════════════════════════════════════════
            {
                "id": "como-agir",
                "label": "Como Agir",
                "content": html.Div([
                    html.P(
                        "A taxa de fuga ideal é abaixo de 15%. "
                        "Veja o que fazer conforme a situação:",
                        style=_INTRO,
                    ),

                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "Taxa acima de 20% → Ação Urgente",
                            "Agendar reunião com os Top 5 Ofensores. "
                            "Apresentar o volume de fugas e negociar "
                            "migração dessas OS para preventivas programadas. "
                            "Usar o ranking como evidência.",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Taxa entre 15–20% → Monitoramento Ativo",
                            "Acompanhar a evolução mensal. Se subir 2 meses "
                            "consecutivos, escalar para reunião com a rede. "
                            "Verificar se novos clientes entraram no ranking.",
                        ),
                        timeline_step(
                            3, "#10b981",
                            "Taxa abaixo de 15% → Meta atingida",
                            "Continuar monitorando. Focar nos Top Ofensores "
                            "remanescentes e alinhar expectativas de SLA "
                            "com a rede para manter o patamar.",
                        ),
                    ], className="step-timeline"),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-people-fill",
                        icon_color="#8b5cf6", icon_bg="rgba(139,92,246,0.08)",
                        title="Quem envolver?",
                        text="Coordenação de Frotas (dono do contrato), "
                             "Equipe RI (dados e evidências), e Gestor da "
                             "Rede de Oficinas (execução do plano de ação).",
                        border_color="#8b5cf6", card_bg="rgba(139,92,246,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 5: FAQ (NOVA)
            # ════════════════════════════════════════════
            {
                "id": "faq",
                "label": "FAQ",
                "content": html.Div([
                    html.P(
                        "Perguntas frequentes sobre fugas de preventiva:",
                        style=_INTRO,
                    ),

                    annotation(
                        icon="bi-question-circle-fill",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Por que a taxa subiu de repente?",
                        text="Geralmente indica entrada de uma nova oficina "
                             "que está classificando preventivas como corretivas. "
                             "Verifique os Top Ofensores — se apareceu um cliente "
                             "novo, esse é o provável causador.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-question-circle-fill",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Por que só 4 peças são detectadas?",
                        text="A lista de peças (Óleo Motor, Filtro de Óleo, etc.) "
                             "foi validada campo a campo contra o relatório Power BI. "
                             "Essas 4 peças cobrem >95% das fugas reais. Incluir mais "
                             "peças geraria falsos positivos.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-question-circle-fill",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Os números batem com o Power BI?",
                        text="Sim. A lógica foi validada contra o PBI com match "
                             "exato nos 5 maiores clientes. Diferenças < 2pp podem "
                             "existir por diferença na lista de clientes (PBI inclui "
                             "alguns públicos que excluímos).",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                    annotation(
                        icon="bi-question-circle-fill",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="O que são Silent Orders nessa seção?",
                        text="São OS que foram aprovadas automaticamente pelo "
                             "sistema, sem nenhuma intervenção humana. Não tem "
                             "relação direta com fugas — é um indicador complementar "
                             "que mostra o nível de automação.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),
                ])
            },
        ]
    )


def render_ranking_help_modal():
    """Modal de ajuda: Top Ofensores / Ranking — 3 tabs premium."""
    return build_help_modal(
        modal_id="prev-ranking-help-modal",
        icon_class="bi-trophy-fill",
        title="Top Ofensores",
        subtitle="Ranking de clientes por volume de fugas",
        sections=[
            # ════════════════════════════════════════════
            # TAB 1: O QUE SÃO
            # ════════════════════════════════════════════
            {
                "id": "definicao",
                "label": "O que são",
                "content": html.Div([
                    html.P(
                        "Os Top Ofensores são os 10 clientes TGM que concentram "
                        "o maior volume de fugas de preventiva. São os principais "
                        "candidatos para ação de campo.",
                        style=_INTRO,
                    ),

                    spotlight(
                        "TOP 10", "CLIENTES COM MAIS FUGAS",
                        "Ordenados por volume absoluto de OS com fuga",
                        color="#f59e0b", bg_var="rgba(245,158,11,0.06)",
                    ),

                    annotation(
                        icon="bi-bullseye",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Por que monitorar?",
                        text="Concentrar ações nos maiores ofensores gera "
                             "o máximo de impacto com o mínimo de esforço. "
                             "Se os Top 5 reduzirem fugas em 30%, "
                             "a taxa geral pode cair 3-5 pontos percentuais.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                    annotation(
                        icon="bi-calculator",
                        icon_color="#0ea5e9", icon_bg="rgba(14,165,233,0.08)",
                        title="Denominador correto",
                        text="O % de cada cliente usa como denominador o total "
                             "de OS com perfil preventivo DAQUELE cliente — "
                             "não o total geral. Isso evita que clientes grandes "
                             "pareçam melhores por diluição.",
                        border_color="#0ea5e9", card_bg="rgba(14,165,233,0.02)",
                    ),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-funnel-fill",
                        icon_color="#64748b", icon_bg="rgba(100,116,139,0.1)",
                        title="Filtros aplicados",
                        text="Auto Gestão (AG) e clientes não-TGM são excluídos. "
                             "O ranking mostra apenas clientes ativos sob gestão TGM.",
                        border_color="#64748b", card_bg="rgba(100,116,139,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 2: COMO É CALCULADO
            # ════════════════════════════════════════════
            {
                "id": "calculo",
                "label": "Cálculo",
                "content": html.Div([
                    html.P(
                        "O ranking combina volume absoluto com taxa individual "
                        "para cada cliente:",
                        style=_INTRO,
                    ),

                    html.Div([
                        timeline_step(
                            1, "#E20613",
                            "Agrupar fugas por cliente",
                            "Para cada cliente TGM, contamos quantas OS "
                            "foram detectadas como fuga no período. "
                            "Exemplo: Cliente ABC com 45 OS de fuga.",
                            formula="GROUP BY cliente → COUNT(os_fuga)",
                        ),
                        timeline_step(
                            2, "#f59e0b",
                            "Calcular taxa individual",
                            "Dividimos as fugas pelo total de OS com perfil "
                            "preventivo daquele cliente. "
                            "Exemplo: 45 fugas ÷ 200 OS com perfil = 22.5%.",
                            formula="Taxa = fugas_cliente / perfil_cliente × 100",
                        ),
                        timeline_step(
                            3, "#10b981",
                            "Ordenar por volume absoluto",
                            "O ranking usa o volume de fugas (não a taxa %) "
                            "para ordenar. Clientes com mais fugas em "
                            "número absoluto ficam no topo — esses geram "
                            "mais impacto se forem corrigidos.",
                        ),
                    ], className="step-timeline"),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-lightbulb-fill",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Exemplo completo",
                        text="Cliente \"Transportadora XYZ\": 78 fugas de "
                             "320 OS com perfil = 24.4%. Está no Top 3. "
                             "Ação: agendar reunião para migrar revisões "
                             "para o contrato preventivo.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 3: COMO LER O RANKING (NOVA)
            # ════════════════════════════════════════════
            {
                "id": "como-ler",
                "label": "Como Ler",
                "content": html.Div([
                    html.P(
                        "Guia para interpretar a tabela de Top Ofensores:",
                        style=_INTRO,
                    ),

                    annotation(
                        icon="bi-sort-numeric-down",
                        icon_color="#E20613", icon_bg="rgba(226,6,19,0.08)",
                        title="Coluna: Fugas (número)",
                        text="Volume absoluto de OS com fuga. "
                             "Esse é o critério de ordenação. "
                             "Clientes com mais fugas = mais impacto potencial.",
                        border_color="#E20613", card_bg="rgba(226,6,19,0.02)",
                    ),
                    annotation(
                        icon="bi-percent",
                        icon_color="#f59e0b", icon_bg="rgba(245,158,11,0.1)",
                        title="Coluna: Taxa (%)",
                        text="Percentual de fugas em relação ao perfil "
                             "preventivo do cliente. Taxa alta (>25%) indica "
                             "que o cliente classificou muitas preventivas "
                             "como corretivas.",
                        border_color="#f59e0b", card_bg="rgba(245,158,11,0.02)",
                    ),
                    annotation(
                        icon="bi-arrow-right-circle-fill",
                        icon_color="#10b981", icon_bg="rgba(16,185,129,0.1)",
                        title="O que fazer com o ranking?",
                        text="Foque nos Top 5. Agende contato individual. "
                             "Leve os números (fugas e taxa) como evidência. "
                             "Proponha migração das OS para preventiva programada. "
                             "Acompanhe mês a mês a evolução.",
                        border_color="#10b981", card_bg="rgba(16,185,129,0.02)",
                    ),

                    html.Hr(style={"borderColor": "#f1f5f9", "margin": "14px 0"}),

                    annotation(
                        icon="bi-file-earmark-code",
                        icon_color="#8b5cf6", icon_bg="rgba(139,92,246,0.08)",
                        title="Alinhamento com Power BI",
                        text="O ranking usa a mesma lógica validada do PBI: "
                             "UNION ALL itens → GROUP BY OS → HAVING ≥2 peças. "
                             "Match confirmado nos 5 maiores clientes.",
                        border_color="#8b5cf6", card_bg="rgba(139,92,246,0.02)",
                    ),
                ])
            },
        ]
    )
