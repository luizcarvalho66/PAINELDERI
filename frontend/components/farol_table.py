# -*- coding: utf-8 -*-
"""
Farol Table - Componente de tabela interativa do farol

Author: Luiz Eduardo Carvalho
"""

from dash import html, dcc, MATCH
import dash_bootstrap_components as dbc
import json


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
                            html.I(className="bi bi-question-circle-fill"),
                            id="btn-info-oportunidades",
                            color="link",
                            className="text-muted p-0 ms-2",
                            style={"fontSize": "1rem"}
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
                    
                    # Instrução interativa (substituiu switch "Detalhar por Cliente")
                    html.Div(className="farol-header-separator"),
                    html.Div([
                        html.I(className="bi bi-chevron-expand me-1", style={"fontSize": "0.75rem", "color": "#64748b"}),
                        html.Small("Clique em uma chave para expandir", className="text-muted", style={"fontSize": "0.72rem"})
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
                        className="text-muted fw-bold me-1",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-question-circle-fill"),
                        id="farol-help-btn",
                        color="link",
                        className="text-muted p-0 ms-1",
                        style={"fontSize": "1rem"}
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
    for idx, item in enumerate(dados):
        cor = item.get("farol_cor", "amarelo")
        score = item.get("farol_score", 0)
        
        # Extrair peca e tipo_mo para o drill-down
        peca = item.get("peca", "SEM PEÇA")
        tipo_mo_val = item.get("tipo_mo", "SEM MO")
        row_id = json.dumps({"peca": peca, "tipo_mo": tipo_mo_val, "cor": cor})
        
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
            
        # Parse Key for Display
        raw_key = item.get("chave", "")
        display_key = raw_key
        key_content = html.Div([
            html.Span(display_key, className="farol-cell-chave"),
            html.Small([
                html.I(className="bi bi-chevron-down ms-2", style={"fontSize": "0.65rem", "color": "#94a3b8", "transition": "transform 0.2s"}),
            ])
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
        
        # Row clicável com ID para pattern-matching
        master_row = html.Tr([
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
            ], 
            id={"type": "farol-row", "index": row_id},
            className="farol-table-row-macos", 
            style=row_style
        )
        rows.append(master_row)
        
        # Collapse row para drill-down (ini oculta)
        collapse_row = html.Tr([
            html.Td(
                dbc.Collapse(
                    html.Div(
                        [
                            html.Div([
                                html.I(className="bi bi-hourglass-split me-1 text-muted"),
                                html.Small("Carregando detalhes...", className="text-muted")
                            ], className="text-center py-3")
                        ],
                        id={"type": "farol-drill-content", "index": row_id}
                    ),
                    id={"type": "farol-drill-collapse", "index": row_id},
                    is_open=False,
                    className="drill-down-collapse"
                ),
                colSpan=8,
                className="p-0 border-0"
            )
        ], className="drill-down-row-wrapper border-0")
        rows.append(collapse_row)
        
    body = html.Tbody(rows)
    
    return dbc.Table(
        [header, body],
        className="farol-table-macos mb-0 w-100",
        hover=True,
        borderless=True, # Remove borders default do Bootstrap para usar os nossos
        responsive=True
    )


def render_drill_down_content(df, cor_farol="amarelo", chave_nome=""):
    """
    Renderiza a sub-tabela de drill-down com as OS individuais de uma chave.
    Chamada pelo callback quando o usuário clica em uma row do farol.
    """
    if df is None or df.empty:
        return html.Div(
            html.Small("Nenhuma OS encontrada para esta chave.", className="text-muted"),
            className="text-center py-4 px-3"
        )
    
    # Cores por farol
    color_map = {
        "verde": "#10b981",
        "amarelo": "#f59e0b",
        "vermelho": "#E20613",
        "cinza": "#94a3b8"
    }
    hex_color = color_map.get(cor_farol, color_map["cinza"])
    
    icon_map = {
        "verde": "bi-check-circle-fill",
        "amarelo": "bi-exclamation-triangle-fill",
        "vermelho": "bi-x-circle-fill",
        "cinza": "bi-dash-circle"
    }
    icon_class = icon_map.get(cor_farol, icon_map["cinza"])
    
    # ── BRANDED HEADER — Premium Edenred Integrado ──
    drill_header = html.Div([
        # ▸ Left: Accent bar (color farol) + Icon + Chave name
        html.Div([
            # Accent bar vertical
            html.Div(className="drill-down-accent-bar", style={"background": hex_color}),
            html.I(className=f"bi {icon_class} drill-down-header-icon", style={"color": hex_color}),
            html.Span(chave_nome or "Detalhes", className="drill-down-header-title"),
            # Contagem de OS como badge integrado
            html.Span(f"{len(df)} OS", className="drill-down-header-badge"),
        ], className="d-flex align-items-center"),
        
        # ▸ Right: Date filter compact (usando dbc.Input para suporte oficial a HTML5 types no Dash)
        html.Div([
            html.I(className="bi bi-calendar-range me-2 drill-down-date-icon"),
            dbc.Input(
                type="date",
                id="drill-down-date-start",
                className="drill-down-date-input",
                placeholder="Início"
            ),
            html.Span("→", className="drill-down-date-separator"),
            dbc.Input(
                type="date",
                id="drill-down-date-end",
                className="drill-down-date-input",
                placeholder="Fim"
            ),
        ], className="d-flex align-items-center"),
    ], className="drill-down-branded-header")
    
    # Header da sub-tabela
    sub_header = html.Thead(
        html.Tr([
            html.Th("OS", style={"width": "100px"}),
            html.Th("Cliente"),
            html.Th("Solicitado", className="text-end"),
            html.Th("Aprovado", className="text-end"),
            html.Th("Data"),
            html.Th("Negociador"),
            html.Th("Aprovação", className="text-center"),
        ], className="drill-down-header")
    )
    
    sub_rows = []
    for _, row in df.head(50).iterrows():
        # Formatação de valores
        val_total = row.get("valor_total", 0) or 0
        val_aprovado = row.get("valor_aprovado", 0) or 0
        val_total_fmt = f"R$ {val_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        val_aprov_fmt = f"R$ {val_aprovado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Strikethrough style no valor total (solicitado) se diferir do aprovado (com margem de cents)
        val_total_class = "drill-down-cell-money-solicitado text-end"
        if abs(val_total - val_aprovado) > 0.05:
            val_total_class += " drill-down-valor-diff"
        
        # Data formatada
        data_str = ""
        if row.get("data_transacao") is not None:
            try:
                data_str = str(row["data_transacao"])[:10]
            except Exception:
                data_str = ""
        
        # Negociador: quem fez o desconto (se houve redução de preço)
        negociador = str(row.get("negociador", "")) if row.get("negociador") else ""
        if negociador:
            negociador_element = html.Span(negociador, className="drill-down-aprovador-comum")
        else:
            negociador_element = html.Span("—", className="text-muted", style={"fontSize": "0.8rem"})
        
        # Tipo de aprovação: Automática ou Humana (via mensagem_log)
        is_auto = row.get("aprovacao_automatica", False) == True
        aprovador = str(row.get("aprovador", "")) if row.get("aprovador") else ""
        is_internal = row.get("is_internal_user", False) == True
        
        if is_auto:
            aprov_badge = html.Span([
                html.I(className="bi bi-cpu me-1"), "Automática"
            ], className="drill-down-badge-regulado")
        else:
            aprov_children = [html.I(className="bi bi-person me-1"), "Humana"]
            if aprovador:
                aprov_children.append(html.Span(f" · {aprovador}", style={"fontWeight": "500", "fontSize": "0.72rem"}))
            # Pill Interno/Externo
            if is_internal:
                aprov_children.append(html.Span([
                    html.I(className="bi bi-building", style={"fontSize": "0.55rem", "marginRight": "2px"}),
                    "Int"
                ], className="badge rounded-pill ms-1", style={
                    "backgroundColor": "rgba(59,130,246,0.1)", "color": "#2563EB",
                    "fontSize": "0.6rem", "fontWeight": "600", "padding": "2px 5px",
                    "verticalAlign": "middle"
                }))
            elif aprovador:
                aprov_children.append(html.Span([
                    html.I(className="bi bi-person-badge", style={"fontSize": "0.55rem", "marginRight": "2px"}),
                    "Ext"
                ], className="badge rounded-pill ms-1", style={
                    "backgroundColor": "rgba(100,116,139,0.1)", "color": "#64748B",
                    "fontSize": "0.6rem", "fontWeight": "600", "padding": "2px 5px",
                    "verticalAlign": "middle"
                }))
            aprov_badge = html.Span(aprov_children, className="drill-down-badge-original")
        
        sub_rows.append(
            html.Tr([
                html.Td(str(row.get("numero_os", "")), className="drill-down-cell-os"),
                html.Td(str(row.get("nome_cliente", ""))[:25], title=str(row.get("nome_cliente", "")), className="drill-down-cell-cliente"),
                html.Td(val_total_fmt, className=val_total_class),
                html.Td(val_aprov_fmt, className="drill-down-cell-money-aprovado text-end"),
                html.Td(data_str, className="drill-down-cell-data"),
                html.Td(negociador_element),
                html.Td(aprov_badge, className="text-center"),
            ], className="drill-down-row")
        )
    
    sub_body = html.Tbody(sub_rows)
    
    total_rows = len(df)
    footer_text = f"Mostrando {min(50, total_rows)} de {total_rows} OS" if total_rows > 50 else f"{total_rows} OS encontradas"
    
    return html.Div([
        drill_header,
        html.Div([
            dbc.Table(
                [sub_header, sub_body],
                className="mb-0 w-100",
                hover=False,
                borderless=True,
                size="sm"
            )
        ], className="drill-down-table-wrapper"),
        html.Div([
            html.I(className="bi bi-list-ul me-2 text-muted"),
            html.Span(footer_text, className="drill-down-footer-text")
        ], className="drill-down-footer")
    ], className="drill-down-panel")



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
