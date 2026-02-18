from dash import Input, Output, State, html, dcc, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from backend.repositories.repo_preventiva import (
    get_fugas_stats, 
    get_fugas_chart_data, 
    get_top_offenders, 
    get_fugas_data
)

def register_preventiva_callbacks(app):
    
    # 1. Main Update Callback (KPIs, Chart, Detailed Table)
    @app.callback(
        [
            Output("prev-kpi-total", "children"),
            Output("prev-kpi-fugas", "children"),
            Output("prev-kpi-pct", "children"),
            Output("prev-progress-bar", "value"),
            Output("prev-chart-evolution", "figure"),
            Output("prev-table-detail", "data")
        ],
        [
            Input("processing-complete-store", "data"),  # Dispara 1x quando dados estão prontos
            Input("global-filters-applied-store", "data")
        ],
        prevent_initial_call=False
    )
    def update_preventiva_dashboard(is_processed, filters_state):
        if not is_processed:
            from dash import no_update
            return (no_update,) * 6
        # Extract filters
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        # 1. Get Stats for KPIs
        stats = get_fugas_stats(filters)
        
        # Error Handling for DB Lock
        if stats.get("error"):
            error_icon = html.I(className="bi bi-database-x", style={"color": "red"})
            return (
                error_icon, # Total
                error_icon, # Fugas
                "Erro DB",  # Percent
                0,          # Progress
                {},         # Chart
                []          # Table
            )

        total = stats.get("total_os", 0)
        fugas = stats.get("qtd_fugas", 0)
        pct = stats.get("pct_fuga", 0)
        
        # 2. Get Chart Data
        chart_data = get_fugas_chart_data(filters)
        # chart_data format: {'mes_ano': [...], 'pct_fuga': [...], 'total_mensal': [...], 'fugas_mensal': [...]}
        
        from frontend.components.chart_fugas_preventiva import create_fugas_evolution_chart
        fig = create_fugas_evolution_chart(chart_data)

        # 3. Get Detailed Table Data
        # Limit default view to 100 rows for performance
        table_data = get_fugas_data(filters, limit=100)
        
        return (
            f"{total:,}".replace(",", "."), 
            f"{fugas:,}".replace(",", "."), 
            f"{pct:.1f}%", 
            pct, 
            fig, 
            table_data
        )

    # 2. Ranking Update Callback (Tab Switch)
    @app.callback(
        Output("prev-ranking-content", "children"),
        [Input("prev-tabs-ranking", "active_tab")],
        [State("global-filters-applied-store", "data")]
    )
    def update_preventiva_ranking(active_tab, filters_state):
        filters = filters_state if filters_state and filters_state.get("applied") else {}
        
        # Map tab to entity
        entity_map = {
            "tab-estab": "estabelecimento",
            "tab-aprov": "aprovador",
            "tab-alcada": "alcada"
        }
        entity = entity_map.get(active_tab, "estabelecimento")
        
        ranking_data = get_top_offenders(filters, entity=entity, limit=5)
        
        if not ranking_data:
            return html.Div("Sem dados para exibir.", className="text-muted p-3")
        
        # Create Simple Table
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
        # Get larger dataset for export
        data = get_fugas_data(filters, limit=50000)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        # Renaissance com nomes amigáveis para o CSV final
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
        
        # Selecionar apenas colunas relevantes na ordem correta
        cols_order = [
            "Data Transação", "Número OS", "Código EC", "Nome do EC", 
            "Cidade", "UF", "Código do Cliente", "Cliente", 
            "Tipo MO", "Valor Aprovado", "Nome Aprovador"
        ]
        # Garantir que todas existam (caso o SQL mude)
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
