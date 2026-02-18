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
                html.H5([
                    html.I(className="bi bi-table me-2"),
                    "Análise por Chave (Peça + Mão de Obra)"
                ], className="mb-0 fw-bold"),
            ], width=4, className="d-flex align-items-center"),
            
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
                    ], className="premium-toggle-container"),
                    
                    # Tooltips
                    dbc.Tooltip("Todas as combinações Peça + MO", target="toggle-view-geral", placement="top"),
                    dbc.Tooltip("Ordens com valor até R$ 1.500 (P70)", target="toggle-view-oportunidades", placement="top"),
                    
                    # Store para guardar estado do toggle
                    dcc.Store(id="farol-view-mode-store", data="geral"),
                ], className="d-flex justify-content-center w-100"),
            ], width=4, className="d-flex justify-content-center align-items-center"),
            
            # Coluna 3: Ações e Info (Alinhado à direita)
            dbc.Col([
                html.Div([
                    html.Small(
                        "Como o farol funciona?",
                        className="text-muted me-2",
                        style={"cursor": "pointer"}
                    ),
                    dbc.Button(
                        html.I(className="bi bi-question-circle-fill"),
                        id="farol-help-btn",
                        color="link",
                        className="p-0 text-decoration-none",
                        style={"color": "#E20613", "fontSize": "1rem", "verticalAlign": "middle"}
                    ),
                ], className="d-flex align-items-center justify-content-end w-100")
            ], width=4, className="d-flex align-items-center"),
            
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
            ], md=3, className="mb-3"),
            
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
            ], md=3, className="mb-3"),

            # Switch Agrupar por Cliente
            dbc.Col([
                html.Label("Opções de Visualização", className="small text-muted mb-1"),
                html.Div([
                    dbc.Switch(
                        id="farol-group-client-switch",
                        label="Detalhar por Cliente",
                        value=False,
                        className="custom-switch"
                    ),
                ], className="d-flex align-items-center h-100 pt-1")
            ], md=2, className="mb-3"),
        ], className="g-2 mb-2"),

        # Container da tabela (populado pelo callback)
        html.Div(
            id="farol-table-container",
            className="farol-table-wrapper",
            style={
                "minHeight": "200px",  # Evitar colapso
                # Removido bordas manuais pois o CSS .farol-table-macos cuida disso
            }
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
    
    # Header Icons & Labels
    header = html.Thead(
        html.Tr([
            html.Th("", style={"width": "50px", "textAlign": "center"}),
            html.Th([html.I(className="bi bi-key farol-header-icon"), "Chave"], style={"width": "25%"}),
            html.Th([html.I(className="bi bi-cpu farol-header-icon"), "Auto"], className="text-center"),
            html.Th([html.I(className="bi bi-person farol-header-icon"), "Humana"], className="text-center"),
            html.Th([html.I(className="bi bi-graph-up farol-header-icon"), "P70"], className="text-end"),
            html.Th([html.I(className="bi bi-list-ol farol-header-icon"), "OS"], className="text-center"),
            html.Th([html.I(className="bi bi-speedometer2 farol-header-icon"), "Score"], className="text-center"),
            html.Th([html.I(className="bi bi-chat-text farol-header-icon"), "Recomendação"], style={"width": "20%"}),
        ], className="farol-table-header-macos")
    )
    
    rows = []
    for item in dados:
        cor = item.get("farol_cor", "amarelo")
        score = item.get("farol_score", 0)
        
        # Ícone de Status (Ponto colorido ou ícone minimalista)
        if cor == "verde":
            icon = html.I(className="bi bi-check-circle-fill text-success", style={"fontSize": "1.2rem"})
            row_border_color = "3px solid #10b981"
        elif cor == "amarelo":
            icon = html.I(className="bi bi-exclamation-triangle-fill text-warning", style={"fontSize": "1.1rem"})
            row_border_color = "3px solid #f59e0b"
            icon = html.I(className="bi bi-x-circle-fill text-danger", style={"fontSize": "1.1rem"})
            row_border_color = "3px solid #E20613" # Edenred Red
            
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
            
        rows.append(
            html.Tr([
                html.Td(icon, className="text-center"),
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
                    str(item.get("qtd_os", 0)),
                    className="text-center font-weight-bold text-muted"
                ),
                html.Td(
                    html.Span(f"{score:.0f}", className=badge_class),
                    className="text-center"
                ),
                html.Td(
                    html.Span(
                        item.get("farol_sugestao", ""),
                        style={"fontSize": "0.8rem", "color": "#64748b"}
                    )
                ),
            ], className="farol-table-row-macos", style={"cursor": "pointer"})
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
