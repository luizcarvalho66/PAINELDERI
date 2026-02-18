from dash import Input, Output, State, html, dcc, callback_context, no_update
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

        # Sub-tabela de clientes (body do accordion)
        if detail_data:
            detail_header = html.Thead(html.Tr([
                html.Th("Cód. Cliente", style={"width": "100px"}),
                html.Th("Cliente"),
                html.Th("OS", style={"width": "80px"}),
                html.Th("Estabelecimento"),
                html.Th("Cidade", style={"width": "90px"}),
                html.Th("UF", style={"width": "45px"}),
                html.Th("Tipo MO", style={"width": "100px"}),
                html.Th("Valor", className="text-end", style={"width": "100px"}),
                html.Th("Aprovador"),
            ], className="prev-detail-header"))

            detail_rows = []
            for d in detail_data:
                detail_rows.append(html.Tr([
                    html.Td(d.get('codigo_cliente', ''), className="fw-semibold",
                            style={"fontFamily": "monospace", "fontSize": "0.78rem"}),
                    html.Td(d.get('cliente', ''), style={
                        "maxWidth": "180px", "overflow": "hidden",
                        "textOverflow": "ellipsis", "whiteSpace": "nowrap"
                    }),
                    html.Td(d.get('numero_os', ''), style={"fontSize": "0.78rem"}),
                    html.Td(d.get('nome_ec', ''), style={
                        "maxWidth": "150px", "overflow": "hidden",
                        "textOverflow": "ellipsis", "whiteSpace": "nowrap"
                    }),
                    html.Td(d.get('cidade', ''), style={"fontSize": "0.78rem"}),
                    html.Td(d.get('uf', ''), style={"fontSize": "0.78rem"}),
                    html.Td(d.get('tipo_mo', ''), style={"fontSize": "0.78rem"}),
                    html.Td(_format_brl(d.get('valor_aprovado')),
                            className="text-end fw-semibold",
                            style={"color": "#C10510", "fontSize": "0.78rem"}),
                    html.Td(d.get('nome_aprovador', ''), style={"fontSize": "0.78rem"}),
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
    
    # 1. Main Update Callback (KPIs, Chart, Accordion Table)
    # Escuta processing-complete-store para carga inicial E
    # global-filters-applied-store para atualização via filtros
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
            Input("global-filters-applied-store", "data")
        ],
        prevent_initial_call=True
    )
    def update_preventiva_dashboard(is_processed, filters_state):
        if not is_processed:
            return (no_update,) * 6
        
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        stats = get_fugas_stats(filters)
        
        if stats.get("error"):
            error_icon = html.I(className="bi bi-database-x", style={"color": "red"})
            return (error_icon, error_icon, "Erro DB", 0, {}, [])

        total = stats.get("total_os", 0)
        fugas = stats.get("qtd_fugas", 0)
        pct = stats.get("pct_fuga", 0)
        
        chart_data = get_fugas_chart_data(filters)
        from frontend.components.chart_fugas_preventiva import create_fugas_evolution_chart
        fig = create_fugas_evolution_chart(chart_data)

        # Buscar dados agrupados COM detalhes embutidos
        table_data = get_fugas_grouped_with_detail(filters, limit=50)
        
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
        [Input("prev-tabs-ranking", "active_tab")],
        [State("global-filters-applied-store", "data")]
    )
    def update_preventiva_ranking(active_tab, filters_state):
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        entity_map = {
            "tab-estab": "estabelecimento",
            "tab-aprov": "aprovador",
            "tab-alcada": "alcada"
        }
        entity = entity_map.get(active_tab, "estabelecimento")
        ranking_data = get_top_offenders(filters, entity=entity, limit=5)
        
        if not ranking_data:
            return html.Div("Sem dados para exibir.", className="text-muted p-3")
        
        header = [html.Thead(html.Tr([
            html.Th("Nome", className="text-secondary fs-8"),
            html.Th("Total OS", className="text-secondary fs-8 text-center"),
            html.Th("% Fuga", className="text-secondary fs-8 text-end")
        ]))]
        
        rows = []
        for row in ranking_data:
            rows.append(html.Tr([
                html.Td(row['entidade'], className="fw-bold fs-7 text-truncate", style={"maxWidth": "150px"}),
                html.Td(row['total_os'], className="text-center fs-7"),
                html.Td(
                    html.Span(f"{row['pct_fuga']}%", className="badge bg-danger bg-opacity-10 text-danger rounded-pill"), 
                    className="text-end"
                )
            ]))
            
        return dbc.Table(header + [html.Tbody(rows)], hover=True, borderless=True, className="mb-0")

    # 3. Export CSV Callback
    @app.callback(
        Output("download-preventiva-csv", "data"),
        Input("btn-export-preventiva", "n_clicks"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True
    )
    def export_preventiva_csv(n_clicks, filters_state):
        if not n_clicks:
            return None
            
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        data = get_fugas_data(filters, limit=50000)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        rename_map = {
            "nome_ec": "Nome do EC",
            "codigo_ec": "Código EC",
            "cidade": "Cidade",
            "uf": "UF",
            "numero_os": "Número OS",
            "cliente": "Cliente",
            "codigo_cliente": "Código do Cliente",
            "nome_aprovador": "Nome Aprovador",
            "tipo_mo": "Tipo MO",
            "valor_aprovado": "Valor Aprovado",
            "data_transacao": "Data Transação"
        }
        df = df.rename(columns=rename_map)
        
        cols_order = [
            "Data Transação", "Número OS", "Código EC", "Nome do EC", 
            "Cidade", "UF", "Código do Cliente", "Cliente", 
            "Tipo MO", "Valor Aprovado", "Nome Aprovador"
        ]
        final_cols = [c for c in cols_order if c in df.columns]
        
        return dcc.send_data_frame(df[final_cols].to_csv, "fugas_preventiva_export.csv", index=False)

    # 4. Help Modal Toggle Callback (General)
    @app.callback(
        Output("prev-help-modal", "is_open"),
        [Input("btn-help-prev-chart", "n_clicks"), Input("btn-help-prev-kpi", "n_clicks")],
        [State("prev-help-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_preventiva_help_modal(n1, n2, is_open):
        if n1 or n2:
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
