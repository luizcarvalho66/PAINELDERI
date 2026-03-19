# -*- coding: utf-8 -*-
"""
Reports Callbacks — Exportação de Relatórios

Registra callbacks para download de PPTX com seleção de cliente TGM e período.

Author: AI Agent
"""

from dash import Input, Output, State, no_update, dcc, clientside_callback, html, callback_context
from datetime import datetime
import traceback

from backend.repositories import (
    get_ri_evolution_data,
    get_farol_table_data,
)
from backend.repositories.repo_dashboard import (
    get_ri_evolution_30d,
    get_distinct_clients,
)
from backend.repositories.repo_farol_table import get_farol_stats_with_trend
from frontend.components.dashboard_charts import create_ri_geral_chart, create_comparative_chart
from backend.services.ppt import generate_ppt


def register_reports_callbacks(app):
    """Registra callbacks da seção de Relatórios."""

    # ── Estilos reutilizáveis para pílulas ──
    PILL_ACTIVE = {
        "display": "inline-flex", "alignItems": "center", "whiteSpace": "nowrap",
        "padding": "10px 20px", "backgroundColor": "rgba(226, 6, 19, 0.07)",
        "color": "#E20613", "borderRadius": "22px", "fontWeight": "600",
        "fontSize": "0.8rem", "cursor": "pointer", "transition": "all 0.2s ease",
    }
    PILL_INACTIVE = {
        "display": "inline-flex", "alignItems": "center", "whiteSpace": "nowrap",
        "padding": "10px 20px", "border": "1px solid #e2e8f0",
        "backgroundColor": "#fff", "color": "#94a3b8", "borderRadius": "22px",
        "fontWeight": "500", "fontSize": "0.8rem", "cursor": "pointer",
        "transition": "all 0.2s ease",
    }

    # ── 1. Abrir modal ao clicar no botão de exportar PPT ──
    @app.callback(
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Output("dropdown-client-tgm", "options"),
        Input("btn-export-ppt", "n_clicks"),
        prevent_initial_call=True,
    )
    def open_client_modal(n_clicks):
        """Abre modal e popula dropdown com clientes distintos."""
        if not n_clicks:
            return no_update, no_update

        try:
            clients = get_distinct_clients()
            options = [{"label": c, "value": c} for c in clients]
        except Exception:
            options = []

        return True, options

    # ── 2. Habilitar/desabilitar botão de confirmar baseado na seleção ──
    @app.callback(
        Output("btn-generate-ppt-confirm", "disabled"),
        Input("dropdown-client-tgm", "value"),
        prevent_initial_call=True,
    )
    def toggle_confirm_button(selected_client):
        """Habilita o botão de gerar quando um cliente é selecionado."""
        return not bool(selected_client)

    # ── 3. Fechar modal ao cancelar ──
    @app.callback(
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Input("btn-cancel-ppt-modal", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_client_modal(n_clicks):
        if not n_clicks:
            return no_update
        return False

    # ── 3.5. Toggle visual das pílulas de período ──
    @app.callback(
        Output("ppt-pill-30d", "style"),
        Output("ppt-pill-trimestre", "style"),
        Output("ppt-pill-anual", "style"),
        Output("ppt-period-store", "data"),
        Input("ppt-pill-30d", "n_clicks"),
        Input("ppt-pill-trimestre", "n_clicks"),
        Input("ppt-pill-anual", "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_period_pills(n_30d, n_tri, n_anual):
        """Alterna visualmente a pílula ativa e salva no store."""
        triggered = callback_context.triggered_id
        if triggered == "ppt-pill-trimestre":
            return PILL_INACTIVE, PILL_ACTIVE, PILL_INACTIVE, "trimestre"
        elif triggered == "ppt-pill-anual":
            return PILL_INACTIVE, PILL_INACTIVE, PILL_ACTIVE, "anual"
        else:  # default: 30d
            return PILL_ACTIVE, PILL_INACTIVE, PILL_INACTIVE, "30d"

    # ── 4. Callback clientside para abrir loading overlay IMEDIATAMENTE ──
    clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks) {
                return {"display": "flex"};
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("ppt-loading-overlay", "style"),
        Input("btn-generate-ppt-confirm", "n_clicks"),
        prevent_initial_call=True,
    )

    # ── 5. Gerar PPT filtrado pelo cliente e período selecionados ──
    @app.callback(
        Output("download-ppt", "data"),
        Output("ppt-loading-overlay", "style", allow_duplicate=True),
        Output("modal-select-client", "is_open", allow_duplicate=True),
        Output("dropdown-client-tgm", "value"),
        Input("btn-generate-ppt-confirm", "n_clicks"),
        State("dropdown-client-tgm", "value"),
        State("ppt-period-store", "data"),
        State("global-filters-applied-store", "data"),
        prevent_initial_call=True,
    )
    def download_ppt(n_clicks, selected_client, selected_period, filters_state):
        """Gera e retorna o PPTX filtrado pelo cliente e período selecionados."""
        if not n_clicks or not selected_client:
            return no_update, no_update, no_update, no_update

        try:
            # Construir filtros com o cliente selecionado
            filters = None
            if filters_state and filters_state.get("applied"):
                filters = dict(filters_state)
            else:
                filters = {}

            # Forçar filtro pelo cliente selecionado no modal
            filters["clientes"] = [selected_client]
            filters["applied"] = True

            # ── Calcular períodos com base na seleção ──
            from datetime import date as _date
            from dateutil.relativedelta import relativedelta

            today = _date.today()
            if selected_period == "trimestre":
                months_back = 3
            elif selected_period == "anual":
                months_back = 12
            else:  # "30d" (default)
                months_back = 1

            period_list = []
            for i in range(months_back):
                dt = today - relativedelta(months=i)
                period_list.append(f"{dt.year}-{dt.month:02d}")

            filters["periodos"] = period_list
            print(f"[REPORTS] Gerando PPT: cliente={selected_client}, periodo={selected_period}, meses={period_list}", flush=True)

            # 1. Dados do dashboard filtrados pelo cliente e período
            df = get_ri_evolution_data(filters)

            if df.empty or ('error_state' in df.columns and df['error_state'].iloc[0]):
                return no_update, {"display": "none"}, False, None

            total_analisado = int((df['qtd_prev'] + df['qtd_corr']).sum())
            ri_geral_avg = df['ri_geral'].mean() * 100

            econ_corr = df['sum_economia_pricing'].sum() if 'sum_economia_pricing' in df.columns else 0
            econ_prev = (df['sum_total_prev'] - df['sum_aprovado_prev']).clip(lower=0).sum()
            economia_real = econ_corr + econ_prev

            total_prev = int(df['qtd_prev'].sum())
            total_corr = int(df['qtd_corr'].sum())
            ratio_prev_corr = (total_prev / (total_corr + total_prev) * 100) if (total_corr + total_prev) > 0 else 0

            avg_ri_prev = df['ri_preventiva'].mean() * 100
            avg_ri_corr = df['ri_corretiva'].mean() * 100

            kpi_data = {
                "total_analisado": f"{total_analisado:,}",
                "economia_real": f"R$ {economia_real/1000000:,.1f}M",
                "share_preventiva": f"{ratio_prev_corr:.1f}%",
                "ri_geral": f"{ri_geral_avg:.1f}%",
                "ri_preventiva": f"{avg_ri_prev:.1f}%",
                "ri_corretiva": f"{avg_ri_corr:.1f}%",
            }

            # 2.1 Dados detalhados — depende do período
            if selected_period == "30d":
                # Para 30 dias: detalhamento semanal
                df_30d = get_ri_evolution_30d(filters)
            else:
                # Para trimestre/anual: usar dados mensais já filtrados
                df_30d = df.copy()

            # 3. Chart PPT — Usar modo Silent Order
            # Para 30d: últimos 5 períodos semanais; para trimestre/anual: todos os meses filtrados
            if selected_period == "30d":
                df_so = df_30d.tail(5).copy() if not df_30d.empty else df.tail(5).copy()
            else:
                df_so = df.copy()  # Todos os meses do período selecionado
            
            if 'so_geral' in df_so.columns:
                df_so['ri_geral'] = df_so['so_geral']
                df_so['ri_corretiva'] = df_so.get('so_corretiva', 0)
                df_so['ri_preventiva'] = df_so.get('so_preventiva', 0)
            # Barras: trocar Volume R$ por Total OS
            df_so['sum_total_corr'] = df_so['qtd_corr']
            df_so['sum_total_prev'] = df_so['qtd_prev']
            fig_geral = create_ri_geral_chart(df_so, is_so_mode=True)

            fig_comp = create_comparative_chart(df)

            # 4. Farol
            try:
                farol_stats = get_farol_stats_with_trend()
            except Exception:
                farol_stats = {
                    "verde": {"value": 0},
                    "amarelo": {"value": 0},
                    "vermelho": {"value": 0},
                    "total": {"value": 0},
                }

            try:
                # Buscar top chaves de cada cor para garantir exemplos de todas as categorias
                farol_table = []
                for cor in ["verde", "amarelo", "vermelho"]:
                    try:
                        items = get_farol_table_data(
                            filters={**filters, "prioridade": [cor]},
                            page=1, page_size=5,
                        )
                        farol_table.extend(items)
                    except Exception:
                        pass
                # Adicionar itens gerais para a tabela do Slide 6 (top 15)
                try:
                    general = get_farol_table_data(filters=filters, page=1, page_size=15)
                    # Evitar duplicatas
                    existing_keys = {item.get("chave") for item in farol_table}
                    for item in general:
                        if item.get("chave") not in existing_keys:
                            farol_table.append(item)
                except Exception:
                    pass
            except Exception:
                farol_table = []

            # 5. Top Ofensores — ECs com mais fugas de preventiva (5 meses)
            try:
                from backend.repositories.repo_preventiva import get_top_offenders
                from datetime import date as _dt, timedelta as _td
                _end = _dt.today().isoformat()
                _start = (_dt.today() - _td(days=150)).isoformat()
                top_offenders_raw = get_top_offenders(
                    filters, entity='estabelecimento', limit=3,
                    date_start=_start, date_end=_end
                )
                # Adaptar formato para os cards do slide
                silent_orders = [
                    {
                        "nome": row.get("entidade", "N/A")[:30],
                        "so_percent": row.get("pct_fuga", 0),
                        "total_os": row.get("total_os", 0),
                        "so_count": row.get("qtd_fugas", 0),
                    }
                    for row in top_offenders_raw
                ]
            except Exception:
                silent_orders = []

            # 6. Período real dos dados
            period_start = None
            period_end = None
            if 'ref_date' in df.columns and not df['ref_date'].isna().all():
                period_start = df['ref_date'].min()
                period_end = df['ref_date'].max()
            elif 'mes_ref' in df.columns and not df['mes_ref'].isna().all():
                period_start = df['mes_ref'].min()
                period_end = df['mes_ref'].max()

            # 7. Gerar PPT
            ppt_bytes = generate_ppt(
                kpi_data=kpi_data,
                fig_geral=fig_geral,
                fig_comp=fig_comp,
                farol_stats=farol_stats,
                farol_table_data=farol_table,
                df_30d=df_30d,
                silent_orders=silent_orders,
                client_name=selected_client,
                period_start=period_start,
                period_end=period_end,
                period_label=selected_period or "30d",
            )

            # Nome do arquivo inclui o cliente e período
            now = datetime.now().strftime("%Y%m%d_%H%M")
            period_label = {"30d": "30d", "trimestre": "3m", "anual": "12m"}.get(selected_period, "30d")
            # Sanitizar nome do cliente para o filename
            safe_name = "".join(
                c if c.isalnum() or c in (' ', '-', '_') else '_'
                for c in selected_client
            ).strip().replace(' ', '_')[:30]
            filename = f"Relatorio_RI_{safe_name}_{period_label}_{now}.pptx"

            return (
                dcc.send_bytes(ppt_bytes.getvalue(), filename=filename),
                {"display": "none"},
                False,   # Fechar modal
                None,    # Resetar dropdown
            )

        except Exception as e:
            traceback.print_exc()
            print(f"[REPORTS] Erro ao gerar PPT: {e}", flush=True)
            return no_update, {"display": "none"}, False, None
