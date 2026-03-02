# -*- coding: utf-8 -*-
"""
Farol Table - Componente de tabela interativa do farol

Author: Luiz Eduardo Carvalho
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def render_farol_table_container() -> html.Div:
    """
    Renderiza o container da tabela do farol.
    O conteúdo é preenchido dinamicamente pelo callback.
    """
    return html.Div([
        # Header da seção - Grid Layout para Hierarquia Perfeita
        dbc.Row([
            # Coluna 1: Título (Alinhado à esquerda)
            dbc.Col([
                html.Div([
                    html.Div(style={
                        "width": "4px", "height": "28px",
                        "background": "linear-gradient(180deg, #E20613, #FF4D5A)",
                        "borderRadius": "2px", "marginRight": "12px"
                    }),
                    html.H5([
                        html.I(className="bi bi-grid-3x3-gap-fill me-2", 
                               style={"color": "#E20613", "fontSize": "1.1rem"}),
                        "Análise por Chave",
                        html.Small(" (Peça + MO)", 
                                   className="text-muted fw-normal ms-1",
                                   style={"fontSize": "0.75rem", "letterSpacing": "0.02em"})
                    ], className="mb-0 fw-bold", style={"fontSize": "1.05rem", "color": "#1e293b"}),
                ], className="d-flex align-items-center"),
            ], width=3, className="d-flex align-items-center"),
            
            # Coluna 2: Toggle (Centralizado Absoluto)
            dbc.Col([
                html.Div([
                    html.Div([
                        # Botão Visão Geral
                        html.Div([
                            html.I(className="bi bi-table"),
                            html.Span("Visão Geral")
                        ], 
                        id="toggle-view-geral",
                        className="premium-toggle-btn active", # Initial state
                        n_clicks=0
                        ),
                        
                        # Botão Oportunidades
                        html.Div([
                            html.I(className="bi bi-lightbulb-fill"),
                            html.Span("Oportunidades")
                        ], 
                        id="toggle-view-oportunidades",
                        className="premium-toggle-btn",
                        n_clicks=0
                        ),
                    ], className="premium-toggle-container premium-toggle-compact"),
                    
                    # Botão info (?) com Popover explicativo
                    html.Div([
                        dbc.Button(
                            html.I(className="bi bi-question-circle"),
                            id="btn-info-oportunidades",
                            color="link",
                            className="farol-help-icon ms-2",
                        ),
                        dbc.Popover([
                            dbc.PopoverHeader([
                                html.I(className="bi bi-lightbulb-fill text-warning me-2"),
                                "Lógica de Oportunidades"
                            ]),
                            dbc.PopoverBody([
                                html.P("O modo Oportunidades filtra itens que atendem a DOIS critérios:", 
                                       className="small mb-2 fw-semibold"),
                                
                                # Critério 1
                                html.Div([
                                    html.Span("1", className="badge bg-danger me-2", 
                                             style={"width": "20px", "height": "20px", "borderRadius": "50%", "fontSize": "0.7rem", "lineHeight": "20px", "padding": "0"}),
                                    html.Span("MDO de aprovação automática", className="small fw-semibold")
                                ], className="d-flex align-items-center mb-1"),
                                html.Div([
                                    html.Span("Alinhamento, Balanceamento, Lavagem, Lubrificação, Polir, Rodízio Pneus, Honorário, Camber",
                                             className="small text-muted", style={"fontSize": "0.72rem", "lineHeight": "1.3"})
                                ], className="ms-4 mb-2"),
                                
                                # Critério 2
                                html.Div([
                                    html.Span("2", className="badge bg-danger me-2",
                                             style={"width": "20px", "height": "20px", "borderRadius": "50%", "fontSize": "0.7rem", "lineHeight": "20px", "padding": "0"}),
                                    html.Span("Valor P70 ≤ R$ 1.500", className="small fw-semibold")
                                ], className="d-flex align-items-center mb-1"),
                                html.Div([
                                    html.Span("Percentil 70 dos valores aprovados não ultrapassa R$ 1.500",
                                             className="small text-muted", style={"fontSize": "0.72rem"})
                                ], className="ms-4 mb-2"),
                                
                                # Critério 3
                                html.Div([
                                    html.Span("3", className="badge bg-danger me-2",
                                             style={"width": "20px", "height": "20px", "borderRadius": "50%", "fontSize": "0.7rem", "lineHeight": "20px", "padding": "0"}),
                                    html.Span("OS com até 2 itens", className="small fw-semibold")
                                ], className="d-flex align-items-center mb-1"),
                                html.Div([
                                    html.Span("Apenas ordens de serviço simples (≤ 2 itens) são consideradas",
                                             className="small text-muted", style={"fontSize": "0.72rem"})
                                ], className="ms-4 mb-2"),
                                
                                html.Hr(className="my-2"),
                                html.Div([
                                    html.I(className="bi bi-bullseye me-1", style={"color": "#E20613", "fontSize": "0.75rem"}),
                                    html.Span("Objetivo: serviços padronizáveis onde a TGM pode negociar preços melhores.",
                                             className="small text-muted fst-italic", style={"fontSize": "0.72rem"})
                                ], className="d-flex align-items-start")
                            ])
                        ], target="btn-info-oportunidades", trigger="click", placement="bottom"),
                    ]),
                    
                    # Tooltips
                    dbc.Tooltip("Todas as combinações Peça + MO", target="toggle-view-geral", placement="top"),
                    dbc.Tooltip("MDO pré-definida + P70 ≤ R$ 1.500 + OS ≤ 2 itens", target="toggle-view-oportunidades", placement="top"),
                    
                    # Separador visual e Switch Detalhar por Cliente
                    html.Div(className="farol-header-separator"),
                    html.Div([
                        dbc.Switch(
                            id="farol-group-client-switch",
                            label="Detalhar por Cliente",
                            value=False,
                            className="custom-switch custom-switch-inline mb-0"
                        ),
                    ], className="d-flex align-items-center"),
                    
                    # Store para guardar estado do toggle
                    dcc.Store(id="farol-view-mode-store", data="geral"),
                ], className="d-flex justify-content-center align-items-center w-100 gap-1"),
            ], width=6, className="d-flex justify-content-center align-items-center"),
            
            # Coluna 3: Ações e Info (Alinhado à direita)
            dbc.Col([
                html.Div([
                    html.Small(
                        "Como o farol funciona?",
                        className="text-muted me-2",
                        style={"cursor": "pointer"}
                    ),
                    dbc.Button(
                        html.I(className="bi bi-question-circle"),
                        id="farol-help-btn",
                        color="link",
                        className="farol-help-icon ms-1",
                    ),
                ], className="d-flex align-items-center justify-content-end w-100")
            ], width=3, className="d-flex align-items-center"),
            
        ], className="mb-4 align-items-center"),
        
        # BARRA DE FILTROS DO FAROL
        dbc.Row([
            # Filtro Cliente
            dbc.Col([
                html.Label("Filtrar por Cliente", className="small text-muted mb-1"),
                dcc.Dropdown(
                    id="farol-filter-cliente",
                    placeholder="Todos os clientes",
                    multi=True,
                    className="farol-filter-dropdown"
                ),
            ], md=4, className="mb-3"),
            
            # Filtro Chave
            dbc.Col([
                html.Label("Filtrar por Chave (Peça + MO)", className="small text-muted mb-1"),
                dcc.Dropdown(
                    id="farol-filter-chave",
                    placeholder="Todas as chaves",
                    multi=True,
                    className="farol-filter-dropdown",
                    searchable=True
                ),
            ], md=4, className="mb-3"),
            
            # Filtro Prioridade
            dbc.Col([
                html.Label("Filtrar por Prioridade", className="small text-muted mb-1"),
                dcc.Dropdown(
                    id="farol-filter-prioridade",
                    placeholder="Todas as prioridades",
                    multi=True,
                    options=[
                        {"label": "Vermelho (Ação Prioritária)", "value": "vermelho"},
                        {"label": "Amarelo (Atenção)", "value": "amarelo"},
                        {"label": "Verde (Performando Bem)", "value": "verde"}
                    ],
                    className="farol-filter-dropdown"
                ),
            ], md=4, className="mb-3"),
        ], className="g-2 mb-2"),

        # Container da tabela (populado pelo callback)
        dcc.Loading(
            id="farol-loading-overlay",
            type="default",
            custom_spinner=html.Div([
                html.Img(
                    src="/assets/edenred-minilogo.webp",
                    className="farol-loading-logo"
                ),
                html.Div("Carregando dados...", className="farol-loading-text"),
                html.Div(className="farol-loading-bar-track", children=[
                    html.Div(className="farol-loading-bar-fill")
                ])
            ], className="farol-loading-container"),
            children=html.Div(
                id="farol-table-container",
                className="farol-table-wrapper",
                style={
                    "minHeight": "200px",  # Evitar colapso
                    # Removido bordas manuais pois o CSS .farol-table-macos cuida disso
                }
            ),
            parent_className="farol-loading-parent",
            overlay_style={"visibility": "visible", "backgroundColor": "#ffffff"},
            color="#E20613"
        ),
        
        # Paginação
        html.Div([
            dbc.Pagination(
                id="farol-pagination",
                max_value=1,
                first_last=True,
                previous_next=True,
                fully_expanded=False,
                size="sm",
                className="justify-content-center mb-0"
            )
        ], className="d-flex justify-content-center mt-3"),
        
        # Legenda
        # Legenda
        html.Div([
            html.Small([
                html.I(className="bi bi-check-circle-fill me-1", style={"color": "#10b981", "fontSize": "1.15rem", "verticalAlign": "text-bottom"}),
                html.Span("≥80% aprovação", style={"fontFamily": "DIN, sans-serif", "fontSize": "0.9rem"}),
                
                html.Span(className="mx-3"),
                
                html.I(className="bi bi-exclamation-triangle-fill me-1", style={"color": "#f59e0b", "fontSize": "1.15rem", "verticalAlign": "text-bottom"}),
                html.Span("50-80% aprovação", style={"fontFamily": "DIN, sans-serif", "fontSize": "0.9rem"}),
                
                html.Span(className="mx-3"),
                
                html.I(className="bi bi-x-circle-fill me-1", style={"color": "#E20613", "fontSize": "1.15rem", "verticalAlign": "text-bottom"}),
                html.Span("<50% ou queda crítica", style={"fontFamily": "DIN, sans-serif", "fontSize": "0.9rem"})
            ], className="text-muted d-flex align-items-center justify-content-center")
        ], className="mt-2")
        

    ], className="farol-table-section p-4 bg-white rounded shadow-sm")


def render_farol_table_content(dados):
    """
    Constrói o conteúdo da tabela do farol com o novo design macOS/Minimalista.
    Função chamada pelo callback para popular o html.Div(id='farol-table-container').
    """
    
    # Header Icons & Labels — Edenred Branded
    header = html.Thead(
        html.Tr([
            html.Th("", style={"width": "50px", "textAlign": "center"}),
            html.Th([html.I(className="bi bi-key-fill farol-header-icon"), "Chave"], style={"width": "25%"}),
            html.Th([html.I(className="bi bi-cpu-fill farol-header-icon"), "Auto"], className="text-center"),
            html.Th([html.I(className="bi bi-person-fill farol-header-icon"), "Humana"], className="text-center"),
            html.Th([html.I(className="bi bi-graph-up-arrow farol-header-icon"), "P70"], className="text-end"),
            html.Th([html.I(className="bi bi-hash farol-header-icon"), "OS"], className="text-center"),
            html.Th([html.I(className="bi bi-speedometer farol-header-icon"), "Score"], className="text-center"),
            html.Th([html.I(className="bi bi-lightbulb-fill farol-header-icon"), "Recomendação"], style={"width": "22%"}),
        ], className="farol-table-header-macos")
    )
    
    rows = []
    for item in dados:
        cor = item.get("farol_cor", "amarelo")
        score = item.get("farol_score", 0)
        
        # Ícone de Status + Borda lateral colorida
        if cor == "verde":
            icon = html.Div([
                html.I(className="bi bi-check-circle-fill", style={"color": "#10b981", "fontSize": "1.15rem"})
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            row_style = {"borderLeft": "3px solid #10b981", "cursor": "pointer"}
        elif cor == "amarelo":
            icon = html.Div([
                html.I(className="bi bi-exclamation-triangle-fill", style={"color": "#f59e0b", "fontSize": "1.1rem"})
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            row_style = {"borderLeft": "3px solid #f59e0b", "cursor": "pointer"}
        elif cor == "vermelho":
            icon = html.Div([
                html.I(className="bi bi-x-circle-fill", style={"color": "#E20613", "fontSize": "1.1rem"})
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            row_style = {"borderLeft": "3px solid #E20613", "cursor": "pointer"}
        else:
            icon = html.Div([
                html.I(className="bi bi-dash-circle", style={"color": "#94a3b8", "fontSize": "1.1rem"})
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            row_style = {"borderLeft": "3px solid #94a3b8", "cursor": "pointer"}
            
        # Parse Key for Display (Handle "Key | Client")
        raw_key = item.get("chave", "")
        if " | " in raw_key:
            parts = raw_key.split(" | ")
            display_key = parts[0]
            display_client = parts[1]
            key_content = html.Div([
                html.Span(display_key, className="farol-cell-chave"),
                html.Br(),
                html.Small(html.I(className="bi bi-building me-1"), className="text-muted"),
                html.Small(display_client, className="text-muted fw-normal", style={"fontSize": "0.75rem"})
            ])
        else:
            display_key = raw_key
            key_content = html.Div([
                html.Span(display_key, className="farol-cell-chave")
            ])
            
        # Badge de Score
        if score >= 70:
            badge_class = "farol-badge-score high"
        elif score >= 40:
            badge_class = "farol-badge-score medium"
        else:
            badge_class = "farol-badge-score low"
            
        # Formatar recomendação com tag visual
        sugestao = item.get("farol_sugestao", "")
        if cor == "vermelho":
            rec_tag = html.Span([
                html.I(className="bi bi-exclamation-diamond-fill me-1", style={"fontSize": "0.7rem"}),
                sugestao
            ], className="farol-rec-tag farol-rec-urgente")
        elif cor == "amarelo":
            rec_tag = html.Span([
                html.I(className="bi bi-eye-fill me-1", style={"fontSize": "0.7rem"}),
                sugestao
            ], className="farol-rec-tag farol-rec-atencao")
        else:
            rec_tag = html.Span([
                html.I(className="bi bi-check2 me-1", style={"fontSize": "0.7rem"}),
                sugestao
            ], className="farol-rec-tag farol-rec-ok")
        
        # Formatação de OS com separador de milhar
        qtd_os = item.get("qtd_os", 0)
        qtd_os_fmt = f"{qtd_os:,}".replace(",", ".")
        
        rows.append(
            html.Tr([
                html.Td(icon, className="text-center", style={"width": "50px"}),
                html.Td(key_content),
                html.Td(
                    f"{item.get('pct_aprovacao', 0):.1f}%",
                    className="text-center farol-cell-value-success"
                ),
                html.Td(
                    f"{item.get('pct_aprovacao_humana', 0):.1f}%",
                    className="text-center farol-cell-value-neutral"
                ),
                html.Td(
                    f"R$ {item.get('p70', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    className="text-end farol-cell-money"
                ),
                html.Td(
                    qtd_os_fmt,
                    className="text-center farol-cell-os"
                ),
                html.Td(
                    html.Span(f"{score:.0f}", className=badge_class),
                    className="text-center"
                ),
                html.Td(rec_tag),
            ], className="farol-table-row-macos", style=row_style)
        )
        
    body = html.Tbody(rows)
    
    return dbc.Table(
        [header, body],
        className="farol-table-macos mb-0 w-100",
        hover=True,
        borderless=True, # Remove borders default do Bootstrap para usar os nossos
        responsive=True
    )


def render_logs_table_content(df):
    """
    Constrói a tabela de logs com o design macOS/Minimalista.
    """
    # Header
    header = html.Thead(
        html.Tr([
            html.Th("OS", style={"width": "100px"}),
            html.Th("Cliente"),
            html.Th("Peça"),
            html.Th("Tipo MO"),
            html.Th("Valor", className="text-end"),
            html.Th("Responsável"),
            html.Th("Motivo"),
            html.Th("Data"),
        ], className="farol-table-header-macos")
    )
    
    # Body
    rows = []
    for _, row in df.iterrows():
        rows.append(
            html.Tr([
                html.Td(row.get("numero_os", ""), className="small font-monospace"),
                html.Td(str(row.get("nome_cliente", ""))[:30] if row.get("nome_cliente") else "", 
                       className="small fw-semibold"),
                html.Td(str(row.get("peca", ""))[:25] if row.get("peca") else "", className="small"),
                html.Td(row.get("tipo_mo", ""), className="small"),
                html.Td(
                    f"R$ {row.get('valor_aprovado', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    className="text-end farol-cell-money small"
                ),
                html.Td(
                    html.Span(
                        str(row.get("responsavel_aprovacao", ""))[:20],
                        style={"color": "#3b82f6", "fontWeight": "500"}
                    ),
                    className="small"
                ),
                html.Td(
                    html.Span(
                        str(row.get("motivo", ""))[:40] + "..." if len(str(row.get("motivo", ""))) > 40 else str(row.get("motivo", "")),
                        title=str(row.get("motivo", "")),
                        style={"color": "#E20613", "fontWeight": "500"}
                    ),
                    className="small"
                ),
                html.Td(
                    str(row.get("data_transacao", ""))[:10] if row.get("data_transacao") else "",
                    className="small text-muted"
                ),
            ], className="farol-table-row-macos")
        )
    
    body = html.Tbody(rows)
    
    return dbc.Table(
        [header, body],
        className="farol-table-macos mb-0 w-100",
        hover=True,
        borderless=True,
        responsive=True,
        striped=False # Remove striped default para usar nosso hover clean
    )
