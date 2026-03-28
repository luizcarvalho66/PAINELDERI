from dash import Input, Output, State, html, dcc, callback_context, no_update, MATCH, ALL
import json
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from backend.repositories.repo_preventiva import (
    get_fugas_stats, 
    get_fugas_chart_data, 
    get_top_offenders, 
    get_fugas_data,
    get_fugas_grouped_with_detail,
)


def _format_brl(value):
    """Formata valor como R$ 1.234,56"""
    if not value:
        return "R$ 0,00"
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def _build_accordion_table(table_data):
    """
    Gera um dbc.Accordion com os TGMs como items.
    Cada item tem: header com resumo, body com sub-tabela de clientes.
    """
    if not table_data:
        return html.Div(
            [html.I(className="bi bi-inbox me-2"), "Nenhuma fuga encontrada no período."],
            className="text-muted text-center py-5", style={"fontSize": "0.9rem"}
        )

    accordion_items = []
    for i, row in enumerate(table_data):
        tgm = str(row.get('codigo_tgm', ''))
        cliente_principal = row.get('cliente_principal', 'N/A')
        qtd_clientes = row.get('qtd_clientes', 0)
        total_os = row.get('total_os', 0)
        valor_total = row.get('valor_total', 0)
        detail_data = row.get('detailData', [])

        # Header customizado — TGM code + cliente principal + badges + valor
        title_content = html.Div([
            html.Div([
                html.Span(tgm, style={
                    "fontWeight": "700", "color": "#1E293B",
                    "backgroundColor": "#F1F5F9", "padding": "2px 8px",
                    "borderRadius": "6px", "fontSize": "0.8rem", "marginRight": "10px",
                    "fontFamily": "monospace"
                }),
                html.Span(cliente_principal, style={
                    "fontWeight": "500", "color": "#334155",
                    "fontSize": "0.85rem", "flex": "1",
                    "overflow": "hidden", "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap", "maxWidth": "200px"
                }),
            ], className="d-flex align-items-center", style={"flex": "1"}),
            html.Div([
                html.Span([
                    html.I(className="bi bi-people-fill me-1", style={"fontSize": "0.7rem"}),
                    f"{qtd_clientes}"
                ], className="badge", style={
                    "backgroundColor": "rgba(226,6,19,0.08)" if qtd_clientes > 3 else "rgba(100,116,139,0.1)",
                    "color": "#C10510" if qtd_clientes > 3 else "#64748B",
                    "fontWeight": "600", "marginRight": "8px", "fontSize": "0.75rem"
                }),
                html.Span(f"{total_os} OS", style={
                    "color": "#64748B", "fontSize": "0.78rem", "marginRight": "12px"
                }),
                html.Span(_format_brl(valor_total), style={
                    "fontWeight": "700", "color": "#1E293B", "fontSize": "0.85rem"
                }),
            ], className="d-flex align-items-center"),
        ], className="d-flex justify-content-between align-items-center w-100 pe-2")

        # Sub-tabela agrupada por OS (body do accordion)
        if detail_data:
            detail_header = html.Thead(html.Tr([
                html.Th("Cód. Cliente", style={"width": "90px"}),
                html.Th("Cliente"),
                html.Th("OS", style={"width": "90px"}),
                html.Th("Tipo MO", style={"width": "120px"}),
                html.Th("Estabelecimento"),
                html.Th("Aprovador"),
                html.Th("Itens", className="text-center", style={"width": "55px"}),
                html.Th("Valor Total", className="text-end", style={"width": "110px"}),
                html.Th("Data", style={"width": "85px"}),
                html.Th("", style={"width": "75px"}),
            ], className="prev-detail-header"))

            detail_rows = []
            for d in detail_data:
                qtd = d.get('qtd_itens', 1)
                valor = d.get('valor_total_os', 0) or 0
                valor_mo = d.get('valor_mo_os', 0) or 0
                valor_peca = d.get('valor_peca_os', 0) or 0
                tipo_mo = d.get('tipo_mo', '')
                peca = d.get('descricao_peca', '') or ''
                
                os_num = str(d.get('numero_os', ''))

                # Coluna de valor — destaque vermelho para valores altos
                valor_style = {"fontSize": "0.78rem", "fontWeight": "600"}
                if valor > 10000:
                    valor_style["color"] = "#C10510"
                else:
                    valor_style["color"] = "#1E293B"

                valor_cell = html.Td(
                    _format_brl(valor),
                    className="text-end",
                    style=valor_style
                )

                # Botão de detalhes — TODAS as linhas
                detail_btn = html.Td(
                    html.Button(
                        [html.I(className="bi bi-search me-1", style={"fontSize": "0.6rem"}), "Detalhes"],
                        id={"type": "prev-val-info", "index": os_num},
                        className="prev-detail-badge",
                    ),
                    className="text-center"
                )
                
                detail_rows.append(html.Tr([
                    html.Td(d.get('codigo_cliente', ''), className="fw-semibold",
                            style={"fontFamily": "monospace", "fontSize": "0.78rem"}),
                    html.Td(d.get('cliente', ''), style={
                        "maxWidth": "150px", "overflow": "hidden",
                        "textOverflow": "ellipsis", "whiteSpace": "nowrap",
                        "fontSize": "0.78rem"
                    }),
                    html.Td(d.get('numero_os', ''), className="fw-semibold",
                            style={"fontFamily": "monospace", "fontSize": "0.78rem"}),
                    html.Td(d.get('tipo_mo', ''), style={"fontSize": "0.78rem"}),
                    html.Td(d.get('nome_ec', ''), style={
                        "maxWidth": "160px", "overflow": "hidden",
                        "textOverflow": "ellipsis", "whiteSpace": "nowrap",
                        "fontSize": "0.78rem"
                    }),
                    html.Td(d.get('nome_aprovador', 'N/A'), style={
                        "maxWidth": "140px", "overflow": "hidden",
                        "textOverflow": "ellipsis", "whiteSpace": "nowrap",
                        "fontSize": "0.78rem"
                    }),
                    html.Td(
                        html.Span(str(qtd), className="badge bg-secondary bg-opacity-25 text-dark rounded-pill",
                                  style={"fontSize": "0.72rem"}),
                        className="text-center"
                    ),
                    valor_cell,
                    html.Td(str(d.get('data_transacao', ''))[:10], 
                            style={"fontSize": "0.75rem", "color": "#64748b"}),
                    detail_btn,
                ], className="prev-detail-row"))

            body_content = html.Div(
                dbc.Table(
                    [detail_header, html.Tbody(detail_rows)],
                    hover=True, bordered=False, size="sm",
                    className="mb-0 prev-detail-subtable"
                ),
                style={"overflowX": "auto"}
            )
        else:
            body_content = html.Div(
                "Sem detalhes disponíveis para este segmento.",
                className="text-muted py-3 text-center", style={"fontSize": "0.8rem"}
            )

        accordion_items.append(
            dbc.AccordionItem(
                body_content,
                title=title_content,
                item_id=f"tgm-{i}",
                className="prev-accordion-item",
            )
        )

    return dbc.Accordion(
        accordion_items,
        id="prev-fugas-accordion",
        start_collapsed=True,
        flush=True,
        className="prev-fugas-accordion",
    )


def register_preventiva_callbacks(app):
    
    # 0. Toggle Veículos / Equipamentos (visual + store) — Premium Toggle
    @app.callback(
        [
            Output("prev-toggle-veiculos", "className"),
            Output("prev-toggle-equipamentos", "className"),
            Output("prev-tipo-ativo-store", "data"),
        ],
        [
            Input("prev-toggle-veiculos", "n_clicks"),
            Input("prev-toggle-equipamentos", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def toggle_tipo_ativo(n_veic, n_equip):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == "prev-toggle-equipamentos":
            return "premium-toggle-btn", "premium-toggle-btn active", "EQUIPAMENTOS"
        # Default: veículos
        return "premium-toggle-btn active", "premium-toggle-btn", "VEICULOS"
    
    # 1. Main Update Callback (KPIs, Chart, Accordion Table)
    @app.callback(
        [
            Output("prev-kpi-total", "children"),
            Output("prev-kpi-fugas", "children"),
            Output("prev-kpi-pct", "children"),
            Output("prev-progress-bar", "value"),
            Output("prev-chart-evolution", "figure"),
            Output("prev-accordion-table", "children"),
        ],
        [
            Input("processing-complete-store", "data"),
            Input("global-filters-applied-store", "data"),
            Input("prev-tipo-ativo-store", "data"),
        ],
        prevent_initial_call=True
    )
    def update_preventiva_dashboard(is_processed, filters_state, tipo_ativo):
        if not is_processed:
            return (no_update,) * 6
        
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        # Datas derivadas do filtro global (periodos YYYY-MM)
        ds = None
        de = None
        periodos = filters.get("periodos", [])
        if periodos:
            ds = f"{periodos[0]}-01"
            from dateutil.relativedelta import relativedelta
            from datetime import datetime as _dt
            last_month = _dt.strptime(f"{periodos[-1]}-01", "%Y-%m-%d")
            de = (last_month + relativedelta(months=1, days=-1)).strftime("%Y-%m-%d")
        
        tipo = tipo_ativo or "VEICULOS"
        
        stats = get_fugas_stats(filters, date_start=ds, date_end=de, tipo_ativo=tipo)
        
        if stats.get("error"):
            error_icon = html.I(className="bi bi-database-x", style={"color": "red"})
            return (error_icon, error_icon, "Erro DB", 0, {}, [])

        total = stats.get("total_os", 0)
        fugas = stats.get("qtd_fugas", 0)
        pct = stats.get("pct_fuga", 0)
        
        chart_data = get_fugas_chart_data(filters, date_start=ds, date_end=de, tipo_ativo=tipo)
        from frontend.components.chart_fugas_preventiva import create_fugas_evolution_chart
        fig = create_fugas_evolution_chart(chart_data)

        # Buscar dados agrupados COM detalhes — usando mesmas datas do filtro global
        table_data = get_fugas_grouped_with_detail(filters, limit=50, date_start=ds, date_end=de, tipo_ativo=tipo)
        
        # Gerar tabela accordion HTML
        accordion = _build_accordion_table(table_data)
        
        return (
            f"{total:,}".replace(",", "."), 
            f"{fugas:,}".replace(",", "."), 
            f"{pct:.1f}%", 
            pct, 
            fig, 
            accordion,
        )

    # 2. Ranking Update Callback (Tab Switch)
    @app.callback(
        Output("prev-ranking-content", "children"),
        [
            Input("prev-tabs-ranking", "active_tab"),
            Input("global-filters-applied-store", "data"),
            Input("processing-complete-store", "data"),
            Input("prev-tipo-ativo-store", "data"),
        ],
        prevent_initial_call=True
    )
    def update_preventiva_ranking(active_tab, filters_state, is_processed, tipo_ativo):
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        # Datas derivadas do filtro global (periodos YYYY-MM)
        ds = None
        de = None
        periodos = filters.get("periodos", [])
        if periodos:
            ds = f"{periodos[0]}-01"
            from dateutil.relativedelta import relativedelta
            from datetime import datetime as _dt
            last_month = _dt.strptime(f"{periodos[-1]}-01", "%Y-%m-%d")
            de = (last_month + relativedelta(months=1, days=-1)).strftime("%Y-%m-%d")
        
        entity_map = {
            "tab-estab": "estabelecimento",
            "tab-aprov": "aprovador",
        }
        entity = entity_map.get(active_tab, "estabelecimento")
        tipo = tipo_ativo or "VEICULOS"
        ranking_data = get_top_offenders(filters, entity=entity, limit=5, date_start=ds, date_end=de, tipo_ativo=tipo)
        
        if not ranking_data:
            return html.Div("Sem dados para exibir.", className="text-muted p-3")
        
        header = [html.Thead(html.Tr([
            html.Th("Nome", className="text-secondary fs-8"),
            html.Th("Tipo", className="text-secondary fs-8 text-center"),
            html.Th("Fugas", className="text-secondary fs-8 text-center"),
            html.Th("% Fuga", className="text-secondary fs-8 text-end")
        ]))]
        
        rows = []
        for row in ranking_data:
            fugas_display = html.Div([
                html.Span(f"{row['qtd_fugas']:,}".replace(",", "."), className="fw-bold"),
                html.Br(),
                html.Small(f"de {row['total_os']:,}".replace(",", ".") + " OS", 
                          className="text-muted", style={"fontSize": "0.7rem"})
            ])
            
            # Pill Interno/Externo (somente para aba aprovador)
            tipo_pill = html.Span()
            if entity == "aprovador":
                is_internal = row.get('is_internal', False)
                if is_internal:
                    tipo_pill = html.Span([
                        html.I(className="bi bi-building me-1", style={"fontSize": "0.6rem"}),
                        "Interno"
                    ], className="badge rounded-pill", style={
                        "backgroundColor": "rgba(59,130,246,0.1)", "color": "#2563EB",
                        "fontSize": "0.68rem", "fontWeight": "600", "padding": "3px 8px"
                    })
                else:
                    tipo_pill = html.Span([
                        html.I(className="bi bi-person-badge me-1", style={"fontSize": "0.6rem"}),
                        "Externo"
                    ], className="badge rounded-pill", style={
                        "backgroundColor": "rgba(100,116,139,0.1)", "color": "#64748B",
                        "fontSize": "0.68rem", "fontWeight": "600", "padding": "3px 8px"
                    })
            
            rows.append(html.Tr([
                html.Td(row['entidade'], className="fw-bold fs-7 text-truncate", style={"maxWidth": "150px"}),
                html.Td(tipo_pill, className="text-center"),
                html.Td(fugas_display, className="text-center fs-7"),
                html.Td(
                    html.Span(f"{row['pct_fuga']}%", className="badge bg-danger bg-opacity-10 text-danger rounded-pill"), 
                    className="text-end"
                )
            ]))
            
        return dbc.Table(header + [html.Tbody(rows)], hover=True, borderless=True, className="mb-0")



    # 4. Help Modal Toggle Callback (General)
    @app.callback(
        Output("prev-help-modal", "is_open"),
        [Input("btn-help-prev-chart", "n_clicks"), Input("btn-help-prev-kpi", "n_clicks"), Input("btn-help-prev-table", "n_clicks")],
        [State("prev-help-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_preventiva_help_modal(n1, n2, n3, is_open):
        if n1 or n2 or n3:
            return not is_open
        return is_open

    # 5. Ranking Help Modal Toggle Callback (Specific)
    @app.callback(
        Output("prev-ranking-help-modal", "is_open"),
        [Input("btn-help-prev-ranking", "n_clicks")],
        [State("prev-ranking-help-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_ranking_help_modal(n, is_open):
        if n:
            return not is_open
        return is_open

    # 6. Modal de Breakdown de Valor — Versão Bespoke com Classes CSS
    @app.callback(
        [Output("prev-valor-modal", "is_open"),
         Output("prev-valor-modal-body", "children")],
        Input({"type": "prev-val-info", "index": ALL}, "n_clicks"),
        prevent_initial_call=True
    )
    def open_valor_detail_modal(all_clicks):
        ctx = callback_context
        if not ctx.triggered or not any(all_clicks):
            return False, no_update
        
        try:
            triggered = ctx.triggered[0]
            btn_id = json.loads(triggered["prop_id"].rsplit(".", 1)[0])
            os_num = btn_id["index"]
        except Exception:
            return False, no_update

        # ── Buscar dados da OS ──
        try:
            from backend.repositories.repo_base import get_connection
            conn = get_connection()
            
            row = conn.execute("""
                SELECT 
                    numero_os, MAX(nome_cliente) as cliente,
                    MAX(nome_estabelecimento) as ec,
                    MAX(familia_veiculo) as familia,
                    MAX(modelo_veiculo) as modelo,
                    MAX(placa) as placa,
                    SUM(COALESCE(valor_aprovado, 0)) as valor,
                    SUM(COALESCE(valor_mo, 0)) as valor_mo,
                    SUM(COALESCE(valor_peca, 0)) as valor_peca,
                    COUNT(CASE WHEN COALESCE(valor_aprovado, 0) > 0 THEN 1 END) as qtd_itens,
                    SUM(COALESCE(valor_total, 0)) as valor_solicitado
                FROM ri_corretiva_detalhamento
                WHERE numero_os = ?
                  AND COALESCE(valor_aprovado, 0) > 0
                GROUP BY numero_os
            """, [os_num]).fetchone()
            if not row:
                return False, no_update
            
            items_df = conn.execute("""
                SELECT 
                    descricao_peca,
                    tipo_mo,
                    COALESCE(valor_aprovado, 0) as valor_total,
                    COALESCE(valor_mo, 0) as valor_mo,
                    COALESCE(valor_peca, 0) as valor_peca,
                    COALESCE(complemento_peca, '') as complemento,
                    COALESCE(valor_total, 0) as valor_solicitado
                FROM ri_corretiva_detalhamento
                WHERE numero_os = ? AND COALESCE(valor_aprovado, 0) > 0
                ORDER BY COALESCE(valor_aprovado, 0) DESC
            """, [os_num]).fetchdf()
            
            # Itens preventivos da mesma OS
            try:
                prev_items_df = conn.execute("""
                    SELECT 
                        descricao_peca,
                        tipo_mo,
                        COALESCE(valor_aprovado, 0) as valor_total,
                        tipo_manutencao
                    FROM ri_preventiva_detalhamento
                    WHERE numero_os = ?
                    ORDER BY COALESCE(valor_aprovado, 0) DESC
                """, [os_num]).fetchdf()
                prev_count = len(prev_items_df)
                prev_valor = float(prev_items_df['valor_total'].sum()) if not prev_items_df.empty else 0
            except Exception:
                prev_items_df = pd.DataFrame()
                prev_count = 0
                prev_valor = 0
            
            valor = float(row[6] or 0)
            valor_mo = float(row[7] or 0)
            valor_peca = float(row[8] or 0)
            
            if valor_peca == 0 and valor > valor_mo:
                valor_peca = round(valor - valor_mo, 2)
            
            cliente = row[1] or ''
            ec = row[2] or ''
            familia = row[3] or 'N/A'
            modelo = row[4] or 'N/A'
            placa = row[5] or 'N/A'
            qtd_itens = row[9] or 1
            valor_solicitado = float(row[10] or 0)
        except Exception as e:
            return False, no_update
        
        pct_mo = round(valor_mo / valor * 100) if valor > 0 else 0
        pct_peca = 100 - pct_mo
        bar_mo_color = "#E20613" if pct_mo >= 80 else "#F59E0B"
        bar_peca_color = "#3B82F6"
        
        # ═══════════════════════════════════════════════
        # PAINEL ESQUERDO: Resumo + Composição + Flags
        # ═══════════════════════════════════════════════
        
        header_info = html.Div([
            html.Div([
                html.Span(f"OS {os_num}", className="os-badge"),
                html.Span(f" — {cliente}", className="os-client"),
            ], className="mb-1"),
            html.Div([
                html.I(className="bi bi-shop me-1"),
                html.Span(ec),
            ], className="os-meta"),
            html.Div([
                html.I(className="bi bi-truck me-1"),
                html.Span(f"{familia} • {modelo}"),
                html.Span(f" • Placa: {placa}") if placa != 'N/A' else None,
            ], className="os-meta"),
        ], className="eden-detail-osinfo")
        
        valor_display = html.Div([
            html.Div("VALOR TOTAL DA OS", className="eden-detail-valor-label"),
            html.Div(_format_brl(valor), className="eden-detail-valor-amount"),
            html.Div(f"{qtd_itens} {'item' if qtd_itens == 1 else 'itens'}", className="eden-detail-valor-count"),
        ], className="eden-detail-valor")
        
        # Barra de composição
        composition_bar = html.Div([
            html.Div(style={
                "width": f"{max(pct_mo, 2)}%", "height": "8px",
                "backgroundColor": bar_mo_color, 
                "borderRadius": "4px 0 0 4px" if pct_peca > 0 else "4px",
            }),
            html.Div(style={
                "width": f"{max(pct_peca, 0)}%", "height": "8px",
                "backgroundColor": bar_peca_color, 
                "borderRadius": "0 4px 4px 0" if pct_mo > 0 else "4px",
            }) if pct_peca > 0 else None,
        ], className="eden-detail-bar")
        
        composition_legend = html.Div([
            html.Div([
                html.Span(className="eden-detail-legend-dot", style={"backgroundColor": bar_mo_color}),
                html.Span(f"Mão de Obra: {_format_brl(valor_mo)} ({pct_mo}%)"),
            ], className="eden-detail-legend-item"),
            html.Div([
                html.Span(className="eden-detail-legend-dot", style={"backgroundColor": bar_peca_color}),
                html.Span(f"Peças: {_format_brl(valor_peca)} ({pct_peca}%)"),
            ], className="eden-detail-legend-item"),
        ], className="eden-detail-legend")
        
        # Flags de anomalia
        flags = []
        if valor > 30000:
            flags.append(html.Div([
                html.I(className="bi bi-exclamation-triangle-fill"),
                html.Span("Valor acima de R$ 30 mil"),
            ], className="eden-detail-flag flag-warning"))
        
        if pct_mo >= 95 and valor > 15000:
            flags.append(html.Div([
                html.I(className="bi bi-info-circle-fill"),
                html.Span("100% MO, sem peças — possível serviço integrado"),
            ], className="eden-detail-flag flag-info"))
        
        if valor_peca == 0 and valor_mo > 0 and abs(valor - valor_mo) < 1:
            flags.append(html.Div([
                html.I(className="bi bi-wrench-adjustable"),
                html.Span("EC lançou tudo como MO — peças não separadas"),
            ], className="eden-detail-flag flag-purple"))
        
        if familia in ('Equipamento', 'Implemento', 'Maquina', 'Empilhadeira', 'Equipamentos Pesados', 'Maquinas'):
            flags.append(html.Div([
                html.I(className="bi bi-gear-wide-connected"),
                html.Span(f"Ativo classificado como {familia} (não veículo)"),
            ], className="eden-detail-flag flag-orange"))

        # Seção itens preventivos
        prev_section = []
        if prev_count > 0:
            prev_table_rows = []
            if not prev_items_df.empty:
                for _, p_item in prev_items_df.head(5).iterrows():
                    prev_table_rows.append(html.Tr([
                        html.Td(
                            str(p_item.get('descricao_peca', 'N/A'))[:35],
                            style={"fontSize": "0.72rem", "padding": "2px 6px",
                                   "maxWidth": "150px", "overflow": "hidden", 
                                   "textOverflow": "ellipsis", "whiteSpace": "nowrap"}
                        ),
                        html.Td(
                            _format_brl(float(p_item.get('valor_total', 0))),
                            style={"fontSize": "0.72rem", "fontWeight": "600", 
                                   "padding": "2px 6px", "textAlign": "right"}
                        ),
                    ]))
            
            prev_section = [
                html.Div([
                    html.Div([
                        html.I(className="bi bi-shield-exclamation me-2", style={"fontSize": "0.85rem"}),
                        html.Span(
                            f"{prev_count} {'item' if prev_count == 1 else 'itens'} preventivo{'s' if prev_count > 1 else ''} nesta OS", 
                            style={"fontSize": "0.82rem", "fontWeight": "600"}
                        ),
                    ], className="d-flex align-items-center mb-2"),
                    html.Div([
                        html.Span("Valor:", style={"fontSize": "0.75rem", "fontWeight": "500"}),
                        html.Span(f" {_format_brl(prev_valor)}", style={"fontSize": "0.82rem", "fontWeight": "700"}),
                    ], className="mb-2"),
                    html.Div(
                        "Estes itens foram classificados como manutenção preventiva e não entraram na análise corretiva.",
                        style={"fontSize": "0.72rem", "lineHeight": "1.4"}
                    ),
                    html.Div([
                        html.Table([html.Tbody(prev_table_rows)], style={"width": "100%"}),
                        html.Div(f"+ {prev_count - 5} mais...", style={
                            "fontSize": "0.68rem", "marginTop": "2px"
                        }) if prev_count > 5 else None,
                    ], className="mt-2") if prev_table_rows else None,
                ], className="eden-detail-prev-section"),
            ]

        left_panel = html.Div([
            header_info,
            valor_display,
            composition_bar,
            composition_legend,
            *flags,
            *prev_section,
        ], className="eden-detail-panel-left")
        
        # ═══════════════════════════════════════════════
        # PAINEL DIREITO: Tabela de Itens Individuais
        # ═══════════════════════════════════════════════
        
        if not items_df.empty:
            items_header = html.Thead(html.Tr([
                html.Th("#", style={"width": "34px"}),
                html.Th("Peça / Serviço"),
                html.Th("Tipo", style={"width": "110px"}),
                html.Th("Valor", className="text-end", style={"width": "110px"}),
                html.Th("MO", className="text-end", style={"width": "95px"}),
                html.Th("Peça", className="text-end", style={"width": "95px"}),
                html.Th("Class.", className="text-center", style={"width": "65px"}),
            ]))
            
            items_rows = []
            for idx, item in items_df.iterrows():
                v_total = float(item['valor_total'] or 0)
                v_mo = float(item['valor_mo'] or 0)
                v_peca = float(item['valor_peca'] or 0)
                desc = str(item['descricao_peca'] or 'N/A')
                tipo = str(item['tipo_mo'] or '')
                
                if v_mo > 0 and v_peca == 0:
                    class_badge = html.Span("MO", className="badge", style={
                        "backgroundColor": "rgba(226,6,19,0.1)", "color": "#C10510"})
                elif v_peca > 0 and v_mo == 0:
                    class_badge = html.Span("Peça", className="badge", style={
                        "backgroundColor": "rgba(59,130,246,0.1)", "color": "#2563EB"})
                elif v_mo > 0 and v_peca > 0:
                    class_badge = html.Span("Misto", className="badge", style={
                        "backgroundColor": "rgba(139,92,246,0.1)", "color": "#7C3AED"})
                else:
                    class_badge = html.Span("—", className="badge", style={
                        "backgroundColor": "rgba(148,163,184,0.1)", "color": "#94A3B8"})
                
                items_rows.append(html.Tr([
                    html.Td(str(idx + 1), className="row-idx"),
                    html.Td(desc, style={"fontWeight": "500", "color": "#1E293B"}),
                    html.Td(tipo, style={"color": "#64748B"}),
                    html.Td(_format_brl(v_total), className="text-end fw-semibold", 
                             style={"color": "#1E293B"}),
                    html.Td(
                        _format_brl(v_mo) if v_mo > 0 else "—",
                        className="text-end", 
                        style={"color": bar_mo_color if v_mo > 0 else "#CBD5E1"}
                    ),
                    html.Td(
                        _format_brl(v_peca) if v_peca > 0 else "—",
                        className="text-end", 
                        style={"color": "#2563EB" if v_peca > 0 else "#CBD5E1"}
                    ),
                    html.Td(class_badge, className="text-center"),
                ]))
            
            items_table = html.Div(
                dbc.Table(
                    [items_header, html.Tbody(items_rows)],
                    hover=True, bordered=False, size="sm", 
                    className="mb-0 eden-detail-table"
                ),
                className="eden-detail-scroll"
            )
            
            legend = html.Div([
                html.Div("Classificação dos itens:", className="legend-title"),
                html.Div([
                    html.Span("MO", className="badge", style={
                        "backgroundColor": "rgba(226,6,19,0.1)", "color": "#C10510"}),
                    html.Span("Mão de Obra"),
                ], className="legend-entry"),
                html.Div([
                    html.Span("Peça", className="badge", style={
                        "backgroundColor": "rgba(59,130,246,0.1)", "color": "#2563EB"}),
                    html.Span("Componente"),
                ], className="legend-entry"),
                html.Div([
                    html.Span("Misto", className="badge", style={
                        "backgroundColor": "rgba(139,92,246,0.1)", "color": "#7C3AED"}),
                    html.Span("MO + Peça"),
                ], className="legend-entry"),
            ], className="eden-detail-legend-section")
        else:
            items_table = html.Div(
                [html.I(className="bi bi-inbox", style={"fontSize": "1.5rem", "color": "#CBD5E1"}),
                 html.Div("Sem itens detalhados", style={"fontSize": "0.82rem", "color": "#94A3B8", "marginTop": "8px"})],
                className="text-center py-5", style={"display": "flex", "flexDirection": "column", "alignItems": "center"}
            )
            legend = html.Div()
        
        right_panel = html.Div([
            html.Div([
                html.Div(
                    html.I(className="bi bi-list-columns-reverse"),
                    className="items-icon"
                ),
                html.Span("Itens da Ordem de Serviço", className="items-title"),
                html.Span(f"{qtd_itens}", className="items-count"),
            ], className="eden-detail-items-header"),
            items_table,
            legend,
        ], className="eden-detail-panel-right")
        
        # Layout: grid 2 painéis
        body = html.Div([left_panel, right_panel], className="eden-detail-grid")
        
        return True, body
