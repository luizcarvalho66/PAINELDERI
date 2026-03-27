from dash import Input, Output, State, no_update, html, dcc, ALL
from dash_iconify import DashIconify
import pandas as pd
from backend.repositories.repo_export import get_export_data

# Tabela de referência de ícones para cada categoria premium
CATEGORIAS = {
    "Identificação Essencial": {
        "icon": "ph:fingerprint-light",
        "color": "#86868b",
        "cols": ['Número OS', 'Cliente', 'Estabelecimento (EC)', 'Status O.S']
    },
    "Dados do Veículo": {
        "icon": "ph:car-light",
        "color": "#86868b",
        "cols": ['Placa', 'Chassi', 'Fabricante', 'Modelo do Veículo', 'Família', 'Ano Veículo', 'Hodômetro']
    },
    "Financeiro & Valores": {
        "icon": "ph:currency-circle-dollar-light",
        "color": "#86868b",
        "cols": ['Valor Solicitado Bruto', 'Valor Aprovado Negociado', 'Valor Peça', 'Valor MO']
    },
    "Serviço & Auditoria": {
        "icon": "ph:clipboard-text-light",
        "color": "#86868b",
        "cols": ['Data da Transação', 'Data Criação OS', 'Data Aprovação', 'Tipo de Manutenção', 'Serviço/Peça (Linha)', 'Desc. Serviço', 'Tipo MDO', 'Origem', 'Aprovador TGM', 'Aprovação Automática (SO)', 'Mensagem Log (Regramentos)', 'Detalhe Regulação']
    },
    "Localidade": {
        "icon": "ph:map-pin-light",
        "color": "#86868b",
        "cols": ['UF', 'Cidade']
    }
}

# Colunas que nascem marcadas para facilitar a vida do analista
DEFAULT_COLS = [
    'Número OS', 'Data da Transação', 'Cliente', 'Estabelecimento (EC)',
    'Placa', 'Tipo de Manutenção', 'Serviço/Peça (Linha)', 
    'Valor Solicitado Bruto', 'Valor Aprovado Negociado', 
    'Status O.S', 'Classificação de Análise'
]


def _build_premium_selector(df_columns):
    """Constrói os badget-checklists baseados nas categorias e nas colunas existentes."""
    groups = []
    
    # Adicionar cols categorizadas
    mapped_cols = set()
    for cat_name, cat_data in CATEGORIAS.items():
        valid_cols = [c for c in cat_data['cols'] if c in df_columns]
        if not valid_cols:
            continue
            
        mapped_cols.update(valid_cols)
        
        # O value padrão é as comuns
        cat_default = [c for c in valid_cols if c in DEFAULT_COLS]
        
        group_ui = html.Div(
            [
                html.Div(
                    [
                        DashIconify(icon=cat_data["icon"], width=18, color=cat_data["color"], className="me-2"),
                        cat_name
                    ],
                    className="premium-export-group-title"
                ),
                dcc.Checklist(
                    id={"type": "export-checklist", "category": cat_name},
                    options=[{"label": c, "value": c} for c in valid_cols],
                    value=cat_default,
                    className="premium-checklist"
                )
            ],
            className="premium-export-group"
        )
        groups.append(group_ui)
        
    # Adicionar "Outros" caso existam colunas não mapeadas
    unmapped = [c for c in df_columns if c not in mapped_cols]
    if unmapped:
        group_ui = html.Div(
            [
                html.Div(
                    [DashIconify(icon="ph:dots-three-circle-light", width=18, color="#64748b", className="me-2"), "Outros Campos"],
                    className="premium-export-group-title"
                ),
                dcc.Checklist(
                    id={"type": "export-checklist", "category": "Outros"},
                    options=[{"label": c, "value": c} for c in unmapped],
                    value=[c for c in unmapped if c in DEFAULT_COLS],
                    className="premium-checklist"
                )
            ],
            className="premium-export-group"
        )
        groups.append(group_ui)
        
    return html.Div(groups)


def register_export_callbacks(app):

    @app.callback(
        Output("modal-export-data", "is_open"),
        Output("export-preview-grid", "rowData"),
        Output("export-preview-grid", "columnDefs"),
        Output("export-columns-selector", "children"),
        Input("btn-open-export-modal", "n_clicks"),
        Input("btn-open-export-modal-reports", "n_clicks"),
        Input("btn-close-export-modal", "n_clicks"),
        Input("btn-export-cancel", "n_clicks"),
        State("modal-export-data", "is_open"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True
    )
    def toggle_modal(btn_open, btn_open_reports, btn_close, btn_cancel, is_open, filters):
        if not is_open:
            df_preview = get_export_data(filters, limit=30)
            if df_preview.empty:
                return True, [], [], html.Div("Nenhum dado encontrado para exportar.", className="text-muted p-3")
                
            row_data = df_preview.to_dict('records')
            
            # Initial definitions for AG Grid
            column_defs = [{"field": c, "headerName": c} for c in df_preview.columns]
            
            selector_ui = _build_premium_selector(df_preview.columns)
            
            return True, row_data, column_defs, selector_ui
            
        return False, no_update, no_update, no_update

    # Sync Premium Checklists with AG Grid Column Definitions
    @app.callback(
        Output("export-preview-grid", "columnDefs", allow_duplicate=True),
        Input({"type": "export-checklist", "category": ALL}, "value"),
        State("export-preview-grid", "columnDefs"),
        prevent_initial_call=True
    )
    def update_grid_columns(checklist_values, current_defs):
        if not current_defs:
            return no_update
            
        # checklist_values is a list of lists (one list per category block)
        # flatten it to get exactly which columns are checked right now across all blocks
        selected_cols = []
        for val_list in checklist_values:
            if val_list:
                selected_cols.extend(val_list)
                
        new_defs = []
        for col in current_defs:
            c = col.copy()
            c["hide"] = c["field"] not in selected_cols
            new_defs.append(c)
            
        return new_defs


    @app.callback(
        Output("download-dataframe-xlsx", "data"),
        Output("modal-export-data", "is_open", allow_duplicate=True),
        Input("btn-export-confirm", "n_clicks"),
        State("global-filters-applied-store", "data"),
        State({"type": "export-checklist", "category": ALL}, "value"),
        State("export-row-limit", "value"),
        prevent_initial_call=True
    )
    def download_excel(n_clicks, filters, checklist_values, row_limit):
        if not n_clicks:
            return no_update, no_update

        # Cap de segurança: máximo 300k linhas
        limit = min(int(row_limit or 10000), 300000)
            
        df_full = get_export_data(filters, limit=limit)
        
        if df_full.empty:
            return no_update, no_update
        
        # Extrair colunas selecionadas dos checklists
        selected_cols = []
        if checklist_values:
            for val_list in checklist_values:
                if val_list:
                    selected_cols.extend(val_list)
        
        if selected_cols:
            # Filtrar apenas as colunas marcadas que existem no df
            valid_cols = [c for c in selected_cols if c in df_full.columns]
            if valid_cols:
                df_full = df_full[valid_cols]
                
        return dcc.send_data_frame(df_full.to_excel, "exportacao_painel_ri.xlsx", sheet_name="Dados Brutos", index=False), no_update

    # Clientside: Mostrar overlay NO CLIQUE (instantâneo)
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks) {
                var overlay = document.getElementById('export-loading-overlay');
                if (overlay) {
                    overlay.style.display = 'flex';
                }
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("export-loading-overlay", "style"),
        Input("btn-export-confirm", "n_clicks"),
        prevent_initial_call=True
    )

    # Clientside: Quando o download é disparado (data muda), mostrar sucesso e fechar após delay
    app.clientside_callback(
        """
        function(download_data) {
            if (download_data) {
                var overlay = document.getElementById('export-loading-overlay');
                var statusEl = document.getElementById('export-loading-status');
                var titleEl = overlay ? overlay.querySelector('div > div > div:nth-child(2)') : null;
                
                // Trocar texto para sucesso
                if (statusEl) statusEl.textContent = 'Seu arquivo será baixado em instantes.';
                if (titleEl) titleEl.textContent = 'Arquivo pronto!';
                
                // Fechar modal + overlay após 3 segundos
                setTimeout(function() {
                    if (overlay) overlay.style.display = 'none';
                    // Reset textos
                    if (statusEl) statusEl.textContent = 'Consultando banco de dados e montando Excel';
                    if (titleEl) titleEl.textContent = 'Preparando seu arquivo...';
                    // Fechar o modal clicando no botão de fechar
                    var closeBtn = document.getElementById('btn-close-export-modal');
                    if (closeBtn) closeBtn.click();
                }, 3000);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("export-loading-status", "children"),
        Input("download-dataframe-xlsx", "data"),
        prevent_initial_call=True
    )
