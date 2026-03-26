# -*- coding: utf-8 -*-
"""
Preventiva Modals — Notion Design System + Edenred Branding.

Modais de ajuda para a seção de Preventiva:
- Fugas de Preventiva (prev-help-modal) — 5 tabs
- Top Ofensores / Ranking (prev-ranking-help-modal) — 3 tabs

Author: Luiz Eduardo Carvalho
"""

from dash import html
from frontend.components.help_modal import (
    build_help_modal, notion_card, notion_metric,
    notion_pipeline, notion_timeline_step, notion_divider
)

# ─── Estilo auxiliar para intro de cada tab ───
_INTRO = {"fontSize": "0.9rem", "color": "#37352f", "lineHeight": "1.7"}


def render_preventiva_help_modal():
    """Modal de ajuda: Fugas de Preventiva — 5 tabs Notion."""
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

                    notion_metric(
                        "~19.7%", "TAXA DE FUGA ATUAL",
                        "Quase 1 em cada 5 OS corretivas tem perfil preventivo",
                    ),

                    notion_card(
                        "bi-graph-down-arrow", "#E20613", "rgba(226,6,19,0.06)",
                        "Distorce SLA e custos",
                        "Cada fuga infla o volume corretivo em +1 OS e "
                        "soma o custo na conta errada. Se 200 revisões "
                        "de 60k km caem como corretiva, o custo corretivo "
                        "sobe ~R$ 160k artificialmente.",
                    ),
                    notion_card(
                        "bi-eye-slash-fill", "#f59e0b", "rgba(245,158,11,0.06)",
                        "Perde histórico de revisões",
                        "Revisões preventivas programadas ficam invisíveis "
                        "no tracking de manutenção. Isso impede planejar "
                        "a próxima revisão e compromete a vida útil do veículo.",
                    ),
                    notion_card(
                        "bi-cash-stack", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Impacto financeiro duplo",
                        "Orçamento corretivo fica inflado e o preventivo "
                        "parece subutilizado. Relatórios executivos mostram "
                        "cenário falso — mais corretivas, menos preventivas "
                        "do que a realidade.",
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

                    notion_pipeline([
                        {"icon": "bi-wrench-adjustable", "label": "OS Corretiva",
                         "color": "#E20613", "bg": "rgba(226,6,19,0.06)"},
                        {"icon": "bi-plus-circle-fill", "label": "UNION ALL",
                         "color": "#0ea5e9", "bg": "rgba(14,165,233,0.06)"},
                        {"icon": "bi-tools", "label": "OS Preventiva",
                         "color": "#f59e0b", "bg": "rgba(245,158,11,0.06)"},
                        {"icon": "bi-shield-fill-check", "label": "Fuga?",
                         "color": "#10b981", "bg": "rgba(16,185,129,0.06)"},
                    ]),

                    html.Div([
                        notion_timeline_step(
                            1, "#E20613",
                            "UNION ALL dos itens corretivos + preventivos",
                            "Juntamos TODOS os itens de ambas as tabelas "
                            "por veículo e período. Isso replica o comportamento "
                            "do Power BI (tabela flat fItens).",
                            formula="UNION ALL itens_corretiva + itens_preventiva",
                        ),
                        notion_timeline_step(
                            2, "#f59e0b",
                            "Contar peças com perfil preventivo por OS",
                            "Verificamos quantas peças de perfil preventivo "
                            "(Óleo Motor, Filtro de Óleo, etc.) cada OS possui. "
                            "Se ≥ 2 peças preventivas → a OS tem perfil.",
                            formula="HAVING COUNT(peças_preventivas) ≥ 2",
                        ),
                        notion_timeline_step(
                            3, "#10b981",
                            "Classificar como fuga",
                            "Se a OS tem perfil preventivo MAS não está na "
                            "tabela de preventivas → é uma fuga. "
                            "A taxa é calculada sobre o total de OS com perfil.",
                            formula="Taxa = OS_fuga / OS_com_perfil × 100",
                        ),
                    ], className="notion-timeline"),

                    notion_divider(),

                    notion_card(
                        "bi-list-check", "#64748b", "rgba(100,116,139,0.06)",
                        "Peças detectadas como preventivas",
                        "Óleo Motor, Óleo Motor Galão 20L, Filtro de Óleo, "
                        "Óleo Motor Tonel 200L. Lista fixa validada contra "
                        "o relatório Power BI.",
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

                    notion_card(
                        "bi-percent", "#E20613", "rgba(226,6,19,0.06)",
                        "Taxa de Fuga (%)",
                        "De cada 100 OS com perfil preventivo, quantas "
                        "estão lançadas como corretiva. Meta: abaixo de 15%. "
                        "Acima de 20% → reunião de alinhamento com a rede.",
                    ),
                    notion_card(
                        "bi-bar-chart-fill", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Evolução Mensal",
                        "Gráfico de barras com a taxa de fuga dos últimos "
                        "6 meses. Observe a tendência: se subir consistentemente, "
                        "há um problema sistêmico na rede de oficinas.",
                    ),
                    notion_card(
                        "bi-trophy-fill", "#f59e0b", "rgba(245,158,11,0.06)",
                        "Top Ofensores",
                        "Os 10 clientes com maior volume absoluto de fugas. "
                        "São os candidatos #1 para ação de campo — contato "
                        "direto, ajuste de contrato ou revisão de SLA.",
                    ),
                    notion_card(
                        "bi-robot", "#64748b", "rgba(100,116,139,0.06)",
                        "Silent Orders (SO)",
                        "OS aprovadas sem intervenção humana (sistema autorizou). "
                        "Calculado pela lógica do PBI: 1º aprovador = "
                        "'Autorizacao De Servico Programado' ou preventiva "
                        "sem aprovador final.",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 4: COMO AGIR
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
                        notion_timeline_step(
                            1, "#E20613",
                            "Taxa acima de 20% → Ação Urgente",
                            "Agendar reunião com os Top 5 Ofensores. "
                            "Apresentar o volume de fugas e negociar "
                            "migração dessas OS para preventivas programadas. "
                            "Usar o ranking como evidência.",
                        ),
                        notion_timeline_step(
                            2, "#f59e0b",
                            "Taxa entre 15–20% → Monitoramento Ativo",
                            "Acompanhar a evolução mensal. Se subir 2 meses "
                            "consecutivos, escalar para reunião com a rede. "
                            "Verificar se novos clientes entraram no ranking.",
                        ),
                        notion_timeline_step(
                            3, "#10b981",
                            "Taxa abaixo de 15% → Meta atingida",
                            "Continuar monitorando. Focar nos Top Ofensores "
                            "remanescentes e alinhar expectativas de SLA "
                            "com a rede para manter o patamar.",
                        ),
                    ], className="notion-timeline"),

                    notion_divider(),

                    notion_card(
                        "bi-people-fill", "#8b5cf6", "rgba(139,92,246,0.06)",
                        "Quem envolver?",
                        "Coordenação de Frotas (dono do contrato), "
                        "Equipe RI (dados e evidências), e Gestor da "
                        "Rede de Oficinas (execução do plano de ação).",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 5: FAQ
            # ════════════════════════════════════════════
            {
                "id": "faq",
                "label": "FAQ",
                "content": html.Div([
                    html.P(
                        "Perguntas frequentes sobre fugas de preventiva:",
                        style=_INTRO,
                    ),

                    notion_card(
                        "bi-question-circle-fill", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Por que a taxa subiu de repente?",
                        "Geralmente indica entrada de uma nova oficina "
                        "que está classificando preventivas como corretivas. "
                        "Verifique os Top Ofensores — se apareceu um cliente "
                        "novo, esse é o provável causador.",
                    ),
                    notion_card(
                        "bi-question-circle-fill", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Por que só 4 peças são detectadas?",
                        "A lista de peças (Óleo Motor, Filtro de Óleo, etc.) "
                        "foi validada campo a campo contra o relatório Power BI. "
                        "Essas 4 peças cobrem >95% das fugas reais. Incluir mais "
                        "peças geraria falsos positivos.",
                    ),
                    notion_card(
                        "bi-question-circle-fill", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Os números batem com o Power BI?",
                        "Sim. A lógica foi validada contra o PBI com match "
                        "exato nos 5 maiores clientes. Diferenças < 2pp podem "
                        "existir por diferença na lista de clientes (PBI inclui "
                        "alguns públicos que excluímos).",
                    ),
                    notion_card(
                        "bi-question-circle-fill", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "O que são Silent Orders nessa seção?",
                        "São OS que foram aprovadas automaticamente pelo "
                        "sistema, sem nenhuma intervenção humana. Não tem "
                        "relação direta com fugas — é um indicador complementar "
                        "que mostra o nível de automação.",
                    ),
                ])
            },
        ]
    )


def render_ranking_help_modal():
    """Modal de ajuda: Top Ofensores / Ranking — 3 tabs Notion."""
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

                    notion_metric(
                        "TOP 10", "CLIENTES COM MAIS FUGAS",
                        "Ordenados por volume absoluto de OS com fuga",
                        color="#f59e0b",
                    ),

                    notion_card(
                        "bi-bullseye", "#E20613", "rgba(226,6,19,0.06)",
                        "Por que monitorar?",
                        "Concentrar ações nos maiores ofensores gera "
                        "o máximo de impacto com o mínimo de esforço. "
                        "Se os Top 5 reduzirem fugas em 30%, "
                        "a taxa geral pode cair 3-5 pontos percentuais.",
                    ),
                    notion_card(
                        "bi-calculator", "#0ea5e9", "rgba(14,165,233,0.06)",
                        "Denominador correto",
                        "O % de cada cliente usa como denominador o total "
                        "de OS com perfil preventivo DAQUELE cliente — "
                        "não o total geral. Isso evita que clientes grandes "
                        "pareçam melhores por diluição.",
                    ),

                    notion_divider(),

                    notion_card(
                        "bi-funnel-fill", "#64748b", "rgba(100,116,139,0.06)",
                        "Filtros aplicados",
                        "Auto Gestão (AG) e clientes não-TGM são excluídos. "
                        "O ranking mostra apenas clientes ativos sob gestão TGM.",
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
                        notion_timeline_step(
                            1, "#E20613",
                            "Agrupar fugas por cliente",
                            "Para cada cliente TGM, contamos quantas OS "
                            "foram detectadas como fuga no período. "
                            "Exemplo: Cliente ABC com 45 OS de fuga.",
                            formula="GROUP BY cliente → COUNT(os_fuga)",
                        ),
                        notion_timeline_step(
                            2, "#f59e0b",
                            "Calcular taxa individual",
                            "Dividimos as fugas pelo total de OS com perfil "
                            "preventivo daquele cliente. "
                            "Exemplo: 45 fugas ÷ 200 OS com perfil = 22.5%.",
                            formula="Taxa = fugas_cliente / perfil_cliente × 100",
                        ),
                        notion_timeline_step(
                            3, "#10b981",
                            "Ordenar por volume absoluto",
                            "O ranking usa o volume de fugas (não a taxa %) "
                            "para ordenar. Clientes com mais fugas em "
                            "número absoluto ficam no topo — esses geram "
                            "mais impacto se forem corrigidos.",
                        ),
                    ], className="notion-timeline"),

                    notion_divider(),

                    notion_card(
                        "bi-lightbulb-fill", "#f59e0b", "rgba(245,158,11,0.06)",
                        "Exemplo completo",
                        "Cliente \"Transportadora XYZ\": 78 fugas de "
                        "320 OS com perfil = 24.4%. Está no Top 3. "
                        "Ação: agendar reunião para migrar revisões "
                        "para o contrato preventivo.",
                    ),
                ])
            },

            # ════════════════════════════════════════════
            # TAB 3: COMO LER O RANKING
            # ════════════════════════════════════════════
            {
                "id": "como-ler",
                "label": "Como Ler",
                "content": html.Div([
                    html.P(
                        "Guia para interpretar a tabela de Top Ofensores:",
                        style=_INTRO,
                    ),

                    notion_card(
                        "bi-sort-numeric-down", "#E20613", "rgba(226,6,19,0.06)",
                        "Coluna: Fugas (número)",
                        "Volume absoluto de OS com fuga. "
                        "Esse é o critério de ordenação. "
                        "Clientes com mais fugas = mais impacto potencial.",
                    ),
                    notion_card(
                        "bi-percent", "#f59e0b", "rgba(245,158,11,0.06)",
                        "Coluna: Taxa (%)",
                        "Percentual de fugas em relação ao perfil "
                        "preventivo do cliente. Taxa alta (>25%) indica "
                        "que o cliente classificou muitas preventivas "
                        "como corretivas.",
                    ),
                    notion_card(
                        "bi-arrow-right-circle-fill", "#10b981", "rgba(16,185,129,0.06)",
                        "O que fazer com o ranking?",
                        "Foque nos Top 5. Agende contato individual. "
                        "Leve os números (fugas e taxa) como evidência. "
                        "Proponha migração das OS para preventiva programada. "
                        "Acompanhe mês a mês a evolução.",
                    ),

                    notion_divider(),

                    notion_card(
                        "bi-file-earmark-code", "#8b5cf6", "rgba(139,92,246,0.06)",
                        "Alinhamento com Power BI",
                        "O ranking usa a mesma lógica validada do PBI: "
                        "UNION ALL itens → GROUP BY OS → HAVING ≥2 peças. "
                        "Match confirmado nos 5 maiores clientes.",
                    ),
                ])
            },
        ]
    )
