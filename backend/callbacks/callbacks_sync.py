import dash
from dash import Input, Output, State, html, no_update, dcc
import dash_bootstrap_components as dbc
import threading
from backend.services.databricks_sync import sync_all_data, get_sync_progress, check_new_data, _get_local_date_range
from datetime import datetime

# Timeout maximo para o sync (segundos) - Alinhado com socket_timeout da conexão (900s)
SYNC_TIMEOUT_SECONDS = 900

# Estado global do sync (thread-safe via GIL para leitura simples)
_sync_state = {
    "running": False,
    "result": None,
    "error": None,
    "started_at": None
}
_sync_thread = None


def _run_sync_background():
    """Executa o sync em background thread."""
    global _sync_state
    try:
        result = sync_all_data(days=450)
        _sync_state["result"] = result
        _sync_state["error"] = None
    except Exception as e:
        _sync_state["result"] = None
        _sync_state["error"] = "Erro interno na sincronização. Verifique os logs."
        print(f"[SYNC] Erro: {e}", flush=True)
    finally:
        _sync_state["running"] = False


def _build_step_row(step, is_last=False):
    """Constroi uma linha visual de step para o modal de progresso — Design Premium."""
    status = step.get("status", "pending")
    detail = step.get("detail", "")
    icon = step.get("icon", "bi-circle")
    label = step.get("label", "")

    # Status icon + color mapping
    if status == "done":
        status_icon = "bi-check-lg"
        icon_bg = "#22c55e"
        icon_color = "#fff"
        row_class = "sync-step-done"
    elif status == "running":
        status_icon = "bi-arrow-repeat"
        icon_bg = "#E20613"
        icon_color = "#fff"
        row_class = "sync-step-running"
    elif status == "error":
        status_icon = "bi-x-lg"
        icon_bg = "#ef4444"
        icon_color = "#fff"
        row_class = "sync-step-error"
    else:
        status_icon = "bi-circle"
        icon_bg = "#f1f5f9"
        icon_color = "#94a3b8"
        row_class = "sync-step-pending"

    # Animated class for running icon
    icon_extra_class = " spin-icon" if status == "running" else ""

    return html.Div(
        html.Div(
            [
                # Status circle badge
                html.Div(
                    html.I(className=f"bi {status_icon}{icon_extra_class}",
                           style={"fontSize": "12px", "color": icon_color}),
                    className="step-badge",
                    style={
                        "background": icon_bg,
                        "width": "28px", "height": "28px",
                        "borderRadius": "50%",
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                        "flexShrink": "0",
                        "boxShadow": f"0 2px 8px {icon_bg}33" if status in ("done", "running") else "none",
                    },
                ),
                # Label
                html.Span(label, className="step-label"),
                # Detail (right side)
                html.Span(detail, className="step-detail") if detail else None,
            ],
            className="step-content",
        ),
        className=f"sync-step {row_class}",
    )


def _build_progress_ui(progress, elapsed=0):
    """Monta o layout completo do modal de progresso — Design Premium Edenred."""
    steps = progress.get("steps", [])
    total = progress.get("total_records", 0)
    corr = progress.get("corretiva_count", 0)
    prev = progress.get("preventiva_count", 0)
    sync_mode = progress.get("sync_mode", "")
    sync_desc = progress.get("sync_description", "")
    queries_info = progress.get("queries_info", [])

    if not steps:
        return html.Div(
            [
                html.Div(
                    html.I(className="bi bi-cloud-arrow-down",
                           style={"fontSize": "2.5rem", "color": "#cbd5e1"}),
                    style={"textAlign": "center", "marginBottom": "12px"},
                ),
                html.P("Inicie uma sincronização para ver o progresso aqui.",
                       style={"textAlign": "center", "color": "#94a3b8", "fontSize": "14px", "margin": "0"}),
            ],
            style={"padding": "40px 20px"},
        )

    # Count completed steps
    done_count = sum(1 for s in steps if s["status"] == "done")
    total_steps = len(steps)
    pct = int((done_count / total_steps) * 100) if total_steps else 0

    # ===== SECTION 1: Hero — Percentage + Progress =====
    hero_section = html.Div(
        [
            html.Div(
                [
                    html.Span(f"{pct}", style={
                        "fontSize": "3rem", "fontWeight": "800", "color": "#192038", "lineHeight": "1",
                    }),
                    html.Span("%", style={
                        "fontSize": "1.5rem", "fontWeight": "600", "color": "#94a3b8", "marginLeft": "2px",
                    }),
                ],
                style={"textAlign": "center", "marginBottom": "8px"},
            ),
            # Slim progress bar
            dbc.Progress(
                value=pct, color="danger",
                style={"height": "6px", "borderRadius": "3px", "background": "#e2e8f0"},
                className="sync-progress-bar",
            ),
            # Time elapsed (right aligned)
            html.Div(
                [
                    html.I(className="bi bi-clock me-1", style={"fontSize": "11px"}),
                    html.Span(f"{elapsed}s"),
                ],
                style={
                    "textAlign": "right", "fontSize": "12px", "color": "#94a3b8",
                    "fontWeight": "500", "marginTop": "6px",
                },
            ),
        ],
        className="sync-hero-section",
    )

    # ===== SECTION 2: Context Banner (Smart Sync Info) =====
    banner = None
    if sync_mode:
        badge_items = []
        for q_info in queries_info:
            badge_items.append(
                html.Div(q_info, style={
                    "fontSize": "12px", "padding": "6px 12px",
                    "background": "#f8fafc", "borderRadius": "8px",
                    "marginBottom": "4px", "color": "#475569",
                })
            )

        banner = html.Div(
            [
                # Red accent bar on left
                html.Div(style={
                    "width": "3px", "background": "#E20613",
                    "borderRadius": "3px", "flexShrink": "0",
                }),
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(className="bi bi-lightning-charge-fill me-2",
                                       style={"color": "#E20613", "fontSize": "14px"}),
                                html.Strong(sync_mode, style={"fontSize": "13px", "color": "#192038"}),
                            ],
                            style={"marginBottom": "4px", "display": "flex", "alignItems": "center"},
                        ),
                        html.P(sync_desc, style={
                            "fontSize": "11px", "color": "#64748b", "margin": "0 0 8px 0",
                            "lineHeight": "1.4",
                        }) if sync_desc else None,
                        *badge_items,
                    ],
                    style={"flex": "1", "minWidth": "0"},
                ),
            ],
            className="sync-context-banner",
        )

    # ===== SECTION 3: Stats Cards (show after download) =====
    stats_row = None
    if total > 0:
        stats_data = [
            {"icon": "bi-database-fill", "value": f"{total:,}", "label": "Total", "color": "#192038",
             "bg": "rgba(25,32,56,0.06)"},
            {"icon": "bi-wrench-adjustable", "value": f"{corr:,}", "label": "Corretivas", "color": "#E20613",
             "bg": "rgba(226,6,19,0.06)"},
            {"icon": "bi-shield-check", "value": f"{prev:,}", "label": "Preventivas", "color": "#3b82f6",
             "bg": "rgba(59,130,246,0.06)"},
        ]
        stats_cards = []
        for s in stats_data:
            stats_cards.append(
                html.Div(
                    [
                        html.Div(
                            html.I(className=f"bi {s['icon']}", style={"color": s['color'], "fontSize": "16px"}),
                            style={
                                "width": "32px", "height": "32px", "borderRadius": "8px",
                                "background": s['bg'], "display": "flex",
                                "alignItems": "center", "justifyContent": "center",
                                "marginBottom": "8px",
                            },
                        ),
                        html.Div(s['value'], className="stat-number", style={"color": s['color']}),
                        html.Div(s['label'], className="stat-label"),
                    ],
                    className="stat-card",
                )
            )
        stats_row = html.Div(stats_cards, className="sync-stats-row")

    # ===== SECTION 4: Steps Timeline =====
    step_rows = [_build_step_row(s, is_last=(i == len(steps) - 1)) for i, s in enumerate(steps)]

    return html.Div([
        hero_section,
        banner,
        stats_row,
        html.Div(step_rows, className="sync-steps-timeline"),
    ])


def register_sync_callbacks(app):

    # =============================================
    # CALLBACK 1: Dispara o sync (click no botao sidebar OU empty state)
    # =============================================
    @app.callback(
        [
            Output("db-connection-status", "children", allow_duplicate=True),
            Output("db-connection-status", "className", allow_duplicate=True),
            Output("last-sync-label", "children", allow_duplicate=True),
            Output("btn-manual-sync", "disabled", allow_duplicate=True),
            Output("btn-manual-sync", "children", allow_duplicate=True),
            Output("sync-poll-interval", "disabled", allow_duplicate=True),
            Output("modal-data-consumption", "is_open", allow_duplicate=True),
        ],
        [
            Input("btn-manual-sync", "n_clicks"),
            Input("btn-sync-empty-state", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def start_sync(n_clicks_sidebar, n_clicks_empty):
        """Dispara o sync em background, ativa polling e abre o modal."""
        global _sync_state, _sync_thread

        # Verifica qual botão foi clicado
        triggered = dash.ctx.triggered_id
        if triggered not in ("btn-manual-sync", "btn-sync-empty-state"):
            return dash.no_update

        # Evita duplo click
        if _sync_state["running"]:
            return dash.no_update

        # Marca como rodando e dispara thread
        _sync_state["running"] = True
        _sync_state["result"] = None
        _sync_state["error"] = None
        _sync_state["started_at"] = datetime.now()

        _sync_thread = threading.Thread(target=_run_sync_background, daemon=True)
        _sync_thread.start()

        return (
            "Sincronizando...",
            "status-value text-warning",
            "Em andamento...",
            True,  # Desabilita botao
            [html.I(className="bi bi-arrow-repeat me-2 spin-icon"), "Sincronizando..."],
            False,  # Ativa o polling interval
            True,   # Abre o modal automaticamente
        )

    # =============================================
    # CALLBACK 2: Polling - verifica status + atualiza modal
    # =============================================
    @app.callback(
        [
            Output("db-connection-status", "children", allow_duplicate=True),
            Output("db-connection-status", "className", allow_duplicate=True),
            Output("last-sync-label", "children", allow_duplicate=True),
            Output("btn-manual-sync", "disabled", allow_duplicate=True),
            Output("btn-manual-sync", "children", allow_duplicate=True),
            Output("sync-poll-interval", "disabled", allow_duplicate=True),
            Output("processing-complete-store", "data", allow_duplicate=True),
            Output("sync-progress-container", "children"),
        ],
        [Input("sync-poll-interval", "n_intervals")],
        prevent_initial_call=True
    )
    def poll_sync_status(n_intervals):
        """Verifica periodicamente o sync e atualiza o modal de progresso."""
        global _sync_state, _sync_thread

        # Calcula tempo decorrido
        elapsed = 0
        if _sync_state.get("started_at"):
            elapsed = (datetime.now() - _sync_state["started_at"]).seconds

        # Obtem progresso ao vivo
        progress = get_sync_progress()
        progress_ui = _build_progress_ui(progress, elapsed)

        # ---- TIMEOUT ----
        if _sync_state["running"] and elapsed > SYNC_TIMEOUT_SECONDS:
            _sync_state["running"] = False
            _sync_state["error"] = f"Timeout ({SYNC_TIMEOUT_SECONDS}s)"

        if _sync_state["running"]:
            return (
                f"Sincronizando... ({elapsed}s)",
                "status-value text-warning",
                f"Em andamento... ({elapsed}s)",
                True,
                [html.I(className="bi bi-arrow-repeat me-2 spin-icon"), "Sincronizando..."],
                False,   # Mantem polling ativo
                dash.no_update,
                progress_ui,
            )

        # ==== Sync acabou ou deu timeout ====
        now_str = datetime.now().strftime("%d/%m %H:%M")

        if _sync_state["error"]:
            error_msg = str(_sync_state["error"])[:40]
            return (
                "Erro ao Sync",
                "status-value text-danger",
                f"Falha: {error_msg}",
                False,
                [html.I(className="bi bi-exclamation-triangle me-2"), "Tentar Novamente"],
                True,
                dash.no_update,
                progress_ui,
            )

        result = _sync_state.get("result", {})
        if result and result.get("success"):
            return (
                "Sincronizado",
                "status-value text-success",
                f"Sync: {now_str}",
                False,
                [html.I(className="bi bi-arrow-repeat me-2"), "Sincronizar"],
                True,
                datetime.now().isoformat(),  # Timestamp único → força re-render dos charts
                progress_ui,
            )
        else:
            errors = result.get("errors", ["Erro desconhecido"]) if result else ["Sem resultado"]
            error_msg = str(errors[0])[:40] if errors else "Desconhecido"
            return (
                "Erro ao Sync",
                "status-value text-danger",
                f"Falha: {error_msg}",
                False,
                [html.I(className="bi bi-exclamation-triangle me-2"), "Tentar Novamente"],
                True,
                dash.no_update,
                progress_ui,
            )

    # =============================================
    # CALLBACK 3: Toggle modal (botao Acompanhar)
    # =============================================
    @app.callback(
        Output("modal-data-consumption", "is_open"),
        [Input("btn-data-consumption", "n_clicks")],
        [State("modal-data-consumption", "is_open")],
        prevent_initial_call=True
    )
    def toggle_data_consumption_modal(n_clicks, is_open):
        """Abre/fecha o modal de progresso."""
        if n_clicks:
            return not is_open
        return is_open

    # =============================================
    # CALLBACK 4: Check novos dados (startup) — NON-BLOCKING TOAST
    # =============================================
    _check_result = {"data": None, "done": False}

    def _run_check_new_data():
        """Executa check_new_data em thread separada (conecta ao Databricks automaticamente)."""
        try:
            print("[CHECK] Iniciando verificação de novos dados...", flush=True)
            result = check_new_data()
            _check_result["data"] = result
        except Exception as e:
            print(f"[CHECK][ERROR] Erro crítico na thread: {e}", flush=True)
            _check_result["data"] = {"has_new_data": False, "error": "Falha na verificação. Tente reconectar.", "warehouse_off": False}
        finally:
            _check_result["done"] = True

    @app.callback(
        [
            Output("new-data-poll-interval", "disabled", allow_duplicate=True),
            Output("sync-new-data-toast", "is_open", allow_duplicate=True),
            Output("new-data-toast-body", "children", allow_duplicate=True),
            Output("sync-new-data-toast", "icon", allow_duplicate=True),
            Output("sync-new-data-toast", "header", allow_duplicate=True),
            Output("sync-new-data-toast", "duration", allow_duplicate=True),
        ],
        [
            Input("new-data-check-interval", "n_intervals"),
            Input("btn-retry-databricks-check", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def check_new_data_on_startup(n_intervals, retry_clicks):
        """Dispara thread de verificação + mostra toast de loading (NON-BLOCKING).
        
        NÃO abre modal — o app fica 100% usável. Apenas mostra um toast
        discreto no canto informando que está verificando.
        
        Também é disparado pelo botão 'Reconectar' no toast de erro.
        """
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        
        # No startup, pula o primeiro intervalo
        if triggered_id == 'new-data-check-interval' and n_intervals == 0:
            return True, False, no_update, no_update, no_update, no_update
        
        # Se é retry, limpa conexão cacheada para forçar novo OAuth
        if triggered_id == 'btn-retry-databricks-check':
            try:
                from backend.services.databricks_sync import _clear_cached_connection
                _clear_cached_connection()
                print("[RETRY] Conexão cacheada limpa. Re-tentando OAuth...", flush=True)
            except Exception as e:
                print(f"[RETRY] Erro ao limpar cache de conexão: {e}", flush=True)
        
        # Reset e dispara thread
        _check_result["data"] = None
        _check_result["done"] = False
        
        check_thread = threading.Thread(target=_run_check_new_data, daemon=True)
        check_thread.start()
        
        # Toast de loading discreto (não bloqueia nada)
        loading_msg = html.Div([
            html.Div([
                html.I(className="bi bi-cloud-check me-2", style={"color": "#0ea5e9"}),
                html.Span("Verificando dados no Databricks...",
                    style={"fontSize": "0.85rem", "color": "#475569"}),
            ], className="d-flex align-items-center"),
            html.Div([
                html.I(className="bi bi-info-circle me-1", style={"color": "#94a3b8", "fontSize": "0.7rem"}),
                html.Small("Se necessário, o navegador abrirá para autenticar.",
                    style={"color": "#94a3b8", "fontSize": "0.75rem"}),
            ], className="d-flex align-items-center mt-1"),
        ])
        
        return False, True, loading_msg, "info", "Conectando...", 30000  # Ativa polling + toast

    # =============================================
    # CALLBACK 5: Polling — mostra toast com resultado
    # =============================================
    @app.callback(
        [
            Output("sync-new-data-toast", "is_open"),
            Output("new-data-toast-body", "children"),
            Output("new-data-poll-interval", "disabled"),
            Output("sync-new-data-toast", "icon", allow_duplicate=True),
            Output("sync-new-data-toast", "header", allow_duplicate=True),
            Output("sync-new-data-toast", "duration"),
            Output("warehouse-retry-interval", "disabled"),
        ],
        [Input("new-data-poll-interval", "n_intervals")],
        prevent_initial_call=True
    )
    def poll_new_data_check(n_intervals):
        """Polling não-bloqueante: mostra toast com comparação real.
        
        Prioridades:
        0. warehouse_off → toast persistente + ativa retry interval
        1. has_new_data → Databricks tem dados mais novos que o local
        2. is_stale → dados locais defasados vs data atual do usuário
        3. tudo OK → dados em dia
        """
        if _check_result.get("done"):
            result = _check_result.get("data", {})
            
            # CASO 0: Warehouse OFF — toast persistente + retry automático
            if result and result.get("warehouse_off"):
                msg = html.Div([
                    html.Div([
                        html.I(className="bi bi-power me-2 warehouse-pulse-icon",
                            style={"color": "#f59e0b", "fontSize": "1.1rem"}),
                        html.Strong("Warehouse desligada", style={"color": "#92400e"}),
                    ], className="mb-2"),
                    html.Div([
                        html.Span("Usando dados locais enquanto aguardamos.",
                            style={"fontSize": "0.85rem", "color": "#78716c"}),
                    ], className="mb-2"),
                    html.Div([
                        html.Div(className="warehouse-waiting-bar", style={
                            "height": "3px", "borderRadius": "2px", "width": "100%",
                            "background": "linear-gradient(90deg, #fbbf24 0%, #f59e0b 50%, #fbbf24 100%)",
                            "backgroundSize": "200% 100%",
                            "animation": "warehouse-shimmer 2s ease-in-out infinite",
                        }),
                    ], className="mb-2"),
                    html.Small("Tentando reconectar automaticamente a cada 15s...",
                        className="text-muted", style={"fontSize": "0.75rem"}),
                ])
                # Toast sem duration (persistente), ativa warehouse-retry-interval
                return True, msg, True, "warning", "⚡ Warehouse Offline", 0, False
            
            # CASO 1: Erro genérico de conexão — com botão de retry
            if result and result.get("error"):
                error_msg = str(result['error'])[:100]
                msg = html.Div([
                    html.Div([
                        html.I(className="bi bi-wifi-off me-2"),
                        html.Span(f"Não foi possível verificar: {error_msg}",
                            style={"fontSize": "0.85rem"}),
                    ], className="mb-2"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="bi bi-arrow-clockwise me-2"), "Reconectar"],
                            id="btn-retry-databricks-check",
                            color="danger",
                            size="sm",
                            className="me-2",
                        ),
                        html.Small("Tenta refazer a autenticação OAuth.",
                            className="text-muted", style={"fontSize": "0.75rem"}),
                    ], className="d-flex align-items-center"),
                ])
                return True, msg, True, "danger", "Erro na Verificação", 15000, True
            
            remote_date = result.get("remote_max_date", "?")
            local_date = result.get("local_max_date", "?")
            local_count = result.get("local_count", 0)
            days_behind = result.get("days_behind", 0)
            today = result.get("today", "?")
            has_new = result.get("has_new_data", False)
            is_stale = result.get("is_stale", False)
            pipeline_lag = result.get("pipeline_lag", False)
            new_records = result.get("new_records_count", 0)
            
            # Formatar datas para DD/MM
            def fmt(d):
                if d and len(d) >= 10:
                    return f"{d[8:10]}/{d[5:7]}"
                return d or "?"
            
            # CASO 2: Databricks tem dados mais novos que o local → SINCRONIZAR
            if has_new:
                msg = html.Div([
                    html.Div([
                        html.I(className="bi bi-cloud-arrow-down-fill me-2"),
                        html.Strong(f"{new_records:,} novos registros disponíveis!"),
                    ], className="mb-2"),
                    html.Div([
                        html.Span("Databricks: ", style={"color": "#64748b"}),
                        html.Strong(fmt(remote_date), style={"color": "#E20613"}),
                        html.Span(" | Local: ", style={"color": "#64748b"}),
                        html.Strong(fmt(local_date), style={"color": "#192038"}),
                    ], className="mb-2"),
                    html.Small("Clique em 'Sincronizar' para atualizar.",
                        className="text-muted"),
                ])
                return True, msg, True, "warning", "Atualização Disponível", 15000, True
            
            # CASO 3: Dados defasados — local em dia com Databricks mas pipeline atrasado
            if is_stale and pipeline_lag:
                msg = html.Div([
                    html.Div([
                        html.I(className="bi bi-clock-history me-2"),
                        html.Strong(f"Pipeline Databricks com {days_behind} dia(s) de atraso"),
                    ], className="mb-2"),
                    html.Div([
                        html.Span("Hoje: ", style={"color": "#64748b"}),
                        html.Strong(fmt(today), style={"color": "#E20613"}),
                        html.Span(" | Último dado: ", style={"color": "#64748b"}),
                        html.Strong(fmt(local_date), style={"color": "#f59e0b"}),
                    ], className="mb-2"),
                    html.Small(f"Base local sincronizada com Databricks ({fmt(remote_date)}). Aguardando atualização do pipeline.",
                        className="text-muted"),
                ])
                return True, msg, True, "info", "Pipeline Databricks Atrasado", 12000, True
            
            # CASO 4: Dados defasados — local atrás do Databricks
            if is_stale:
                records_msg = f"{new_records:,} registros pendentes" if new_records > 0 else "0 registros pendentes"
                msg = html.Div([
                    html.Div([
                        html.I(className="bi bi-calendar-x me-2"),
                        html.Strong(f"Dados com {days_behind} dia(s) de atraso"),
                    ], className="mb-2"),
                    html.Div([
                        html.Span("Hoje: ", style={"color": "#64748b"}),
                        html.Strong(fmt(today), style={"color": "#E20613"}),
                        html.Span(" | Último dado: ", style={"color": "#64748b"}),
                        html.Strong(fmt(local_date), style={"color": "#f59e0b"}),
                    ], className="mb-2"),
                    html.Small(f"{records_msg} — Databricks até {fmt(remote_date)}.",
                        className="text-muted"),
                ])
                return True, msg, True, "warning", "Dados Desatualizados", 12000, True
            
            # CASO 5: Tudo atualizado (sem defasagem significativa)
            msg = html.Div([
                html.Div([
                    html.Span("Hoje: ", style={"color": "#64748b"}),
                    html.Strong(fmt(today), style={"color": "#22c55e"}),
                    html.Span(" | Dados até: ", style={"color": "#64748b"}),
                    html.Strong(fmt(local_date), style={"color": "#22c55e"}),
                ], className="mb-1"),
                html.Small(f"{local_count:,} registros sincronizados. Base atualizada!",
                    className="text-muted"),
            ])
            return True, msg, True, "success", "Dados Atualizados", 8000, True
        
        # Thread ainda rodando — retorna sem atualizar
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update

    # =============================================
    # CALLBACK 6: Retry quando warehouse off — re-dispara check automaticamente
    # =============================================
    @app.callback(
        [
            Output("new-data-poll-interval", "disabled", allow_duplicate=True),
            Output("warehouse-retry-interval", "disabled", allow_duplicate=True),
            Output("sync-new-data-toast", "is_open", allow_duplicate=True),
            Output("new-data-toast-body", "children", allow_duplicate=True),
            Output("sync-new-data-toast", "header", allow_duplicate=True),
            Output("sync-new-data-toast", "duration", allow_duplicate=True),
        ],
        [Input("warehouse-retry-interval", "n_intervals")],
        prevent_initial_call=True
    )
    def warehouse_retry_check(n_intervals):
        """Re-dispara check_new_data quando warehouse estava off.
        
        Roda a cada 15s. Se a warehouse já ligou, o check normal obtém sucesso
        e o CALLBACK 5 mostra o resultado. Se continua off, atualiza o toast.
        """
        if n_intervals is None or n_intervals == 0:
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # Re-limpar e re-disparar check
        _check_result["data"] = None
        _check_result["done"] = False
        
        check_thread = threading.Thread(target=_run_check_new_data, daemon=True)
        check_thread.start()
        
        # Atualizar toast com tentativa N
        retry_msg = html.Div([
            html.Div([
                html.I(className="bi bi-power me-2 warehouse-pulse-icon",
                    style={"color": "#f59e0b", "fontSize": "1.1rem"}),
                html.Strong("Warehouse desligada", style={"color": "#92400e"}),
            ], className="mb-2"),
            html.Div([
                html.Span("Usando dados locais enquanto aguardamos.",
                    style={"fontSize": "0.85rem", "color": "#78716c"}),
            ], className="mb-2"),
            html.Div([
                html.Div(className="warehouse-waiting-bar", style={
                    "height": "3px", "borderRadius": "2px", "width": "100%",
                    "background": "linear-gradient(90deg, #fbbf24 0%, #f59e0b 50%, #fbbf24 100%)",
                    "backgroundSize": "200% 100%",
                    "animation": "warehouse-shimmer 2s ease-in-out infinite",
                }),
            ], className="mb-2"),
            html.Small(f"Tentativa {n_intervals}/40 — reconectando a cada 15s...",
                className="text-muted", style={"fontSize": "0.75rem"}),
        ])
        
        # Ativa polling normal para capturar resultado do novo check
        return False, no_update, True, retry_msg, "⚡ Warehouse Offline", 0


