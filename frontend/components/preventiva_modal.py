# -*- coding: utf-8 -*-
"""
Preventiva Help Modal - Modal explicativo estilo "MacOS" para Fugas de Preventiva.
Reutiliza o design system da seção Farol.
"""

from dash import html
import dash_bootstrap_components as dbc

def render_preventiva_help_modal():
    """
    Renderiza o modal de ajuda para a seção de Fugas de Preventiva.
    Design horizontal premium (Grid de 2 colunas).
    """
    return dbc.Modal([
        # HEADER TRANSPARENTE
        dbc.ModalHeader([
            html.Div([
                html.I(className="bi bi-question-circle-fill me-2", style={"color": "#E20613", "fontSize": "1.2rem"}),
                html.Span("Entenda as Fugas de Preventiva", style={
                    "fontFamily": "DIN, sans-serif",
                    "fontWeight": "700",
                    "fontSize": "1.1rem",
                    "color": "#1e293b"
                })
            ], className="d-flex align-items-center")
        ], close_button=True, className="macos-modal-header"),
        
        # BODY COM LAYOUT HORIZONTAL
        dbc.ModalBody([
            dbc.Row([
                # COLUNA ESQUERDA: DEFINIÇÃO E IMPACTO
                dbc.Col([
                    html.Div("O QUE É UMA FUGA?", className="macos-section-title"),
                    
                    # Card de Definição
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#E20613", "fontSize": "1.5rem"}),
                            html.Div([
                                html.Div("Fuga de Preventiva", style={"fontWeight": "700", "fontSize": "0.9rem", "color": "#E20613"}),
                                html.P(
                                    "Manutenção classificada como CORRETIVA, mas com características claras de PREVENTIVA.",
                                    style={"fontSize": "0.85rem", "color": "#64748b", "marginBottom": "0"}
                                )
                            ], className="ms-3")
                        ], className="d-flex align-items-start")
                    ], className="macos-card", style={"borderLeft": "4px solid #E20613"}),
                    
                    html.Div("POR QUE ISSO É RUIM?", className="macos-section-title mt-4"),
                    
                    # Impactos
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-x-circle text-danger me-2"),
                            html.Span("Distorce o SLA de Corretivas", className="text-secondary")
                        ], className="mb-2"),
                        html.Div([
                            html.I(className="bi bi-x-circle text-danger me-2"),
                            html.Span("Infla o custo médio de reparo", className="text-secondary")
                        ], className="mb-2"),
                        html.Div([
                            html.I(className="bi bi-x-circle text-danger me-2"),
                            html.Span("Perde histórico de revisão do veículo", className="text-secondary")
                        ])
                    ], className="macos-card bg-light"),
                    
                ], width=12, lg=5, className="border-end pe-4"),
                
                # COLUNA DIREITA: CRITÉRIOS DE DETECÇÃO
                dbc.Col([
                    html.Div("COMO IDENTIFICAMOS?", className="macos-section-title"),
                    
                    html.P("Nosso algoritmo analisa as descrições de serviços e peças procurando pelos seguintes termos-chave:", 
                           className="text-muted small mb-3"),
                    
                    # Grid de Palavras-Chave
                    html.Div([
                        dbc.Row([
                            dbc.Col(html.Span("REVISÃO", className="badge bg-light text-dark border w-100 p-2"), width=4, className="mb-2"),
                            dbc.Col(html.Span("PREVENTIVA", className="badge bg-light text-dark border w-100 p-2"), width=4, className="mb-2"),
                            dbc.Col(html.Span("CHECK-UP", className="badge bg-light text-dark border w-100 p-2"), width=4, className="mb-2"),
                            dbc.Col(html.Span("LUBRIFICAÇÃO", className="badge bg-light text-dark border w-100 p-2"), width=6, className="mb-2"),
                            dbc.Col(html.Span("INSPEÇÃO", className="badge bg-light text-dark border w-100 p-2"), width=6, className="mb-2"),
                        ], className="text-center font-monospace small")
                    ]),
                    
                    html.Div("KPIs DO DASHBOARD", className="macos-section-title mt-4"),
                    
                    html.Div([
                         html.Div([
                            html.Strong("Taxa de Fuga (%)", className="text-dark"),
                            html.P("Percentual de Corretivas que na verdade são Preventivas.", className="text-muted small mb-1"),
                            html.Div(html.Span("Fórmula: (Fugas / Total Corretivas) * 100", className="badge bg-secondary bg-opacity-10 text-dark"))
                        ], className="mb-3 pb-3 border-bottom"),
                        
                        html.Div([
                            html.Strong("Top Ofensores", className="text-dark"),
                            html.P("Rankings de Estabelecimentos, Aprovadores e Alçadas que mais aprovam fugas. Útil para ações educativas.", 
                                   className="text-muted small")
                        ])
                    ], className="macos-card")
                    
                ], width=12, lg=7, className="ps-4"),
            ]),
            
        ], className="macos-modal-body"),
        
    ], id="prev-help-modal", size="xl", is_open=False, centered=True, contentClassName="macos-modal-content")

def render_ranking_help_modal():
    """
    Renderiza o modal de ajuda ESPECÍFICO para o Ranking de Ofensores.
    """
    return dbc.Modal([
        dbc.ModalHeader([
            html.Div([
                html.I(className="bi bi-trophy-fill me-2", style={"color": "#E20613", "fontSize": "1.2rem"}),
                html.Span("Entenda os Top Ofensores", style={
                    "fontFamily": "DIN, sans-serif",
                    "fontWeight": "700",
                    "fontSize": "1.1rem",
                    "color": "#1e293b"
                })
            ], className="d-flex align-items-center")
        ], close_button=True, className="macos-modal-header"),
        
        dbc.ModalBody([
            dbc.Row([
                # COLUNA ESQUERDA: O QUE SÃO
                dbc.Col([
                    html.Div("O QUE SÃO OFENSORES?", className="macos-section-title"),
                    
                    html.P("São as entidades (Estabelecimentos ou Pessoas) que mais acumulam Fugas de Preventiva, seja em volume absoluto ou percentual.", 
                           className="text-muted small"),

                    html.Div([
                        html.Div([
                            html.Strong("Objetivo da Análise", className="d-block text-dark mb-1"),
                            html.Ul([
                                html.Li("Identificar mecânicas que lançam errado sistematicamente."),
                                html.Li("Encontrar aprovadores que desconhecem a regra."),
                                html.Li("Agir na raiz do problema (educação ou bloqueio).")
                            ], className="text-muted small ps-3 mb-0")
                        ], className="p-3 bg-light rounded border")
                    ], className="mb-4"),

                ], width=12, lg=5, className="border-end pe-4"),
                
                # COLUNA DIREITA: REGRA DE CÁLCULO
                dbc.Col([
                    html.Div("REGRA DE CÁLCULO", className="macos-section-title"),
                    
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-funnel-fill text-secondary me-2"),
                            html.Strong("1. Filtragem", className="text-dark")
                        ], className="mb-1"),
                        html.P("Selecionamos todas as OSs que caíram na regra de Fuga (termos como REVISÃO, etc).", className="text-muted small mb-3"),

                        html.Div([
                            html.I(className="bi bi-layers-fill text-secondary me-2"),
                            html.Strong("2. Agrupamento", className="text-dark")
                        ], className="mb-1"),
                        html.P("Agrupamos por Estabelecimento, Aprovador ou 1ª Alçada (conforme aba selecionada).", className="text-muted small mb-3"),

                        html.Div([
                            html.I(className="bi bi-sort-numeric-down-alt text-secondary me-2"),
                            html.Strong("3. Ordenação", className="text-dark")
                        ], className="mb-1"),
                        html.P("Ordenamos pelo volume TOTAL de fugas (decrescente). O % exibido é apenas informativo.", className="text-muted small")
                    ], className="macos-card"),
                    
                ], width=12, lg=7, className="ps-4"),
            ])
        ], className="macos-modal-body"),
        
    ], id="prev-ranking-help-modal", size="lg", is_open=False, centered=True, contentClassName="macos-modal-content")
