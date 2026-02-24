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
        result = sync_all_data(days=150)
        _sync_state["result"] = result
        _sync_state["error"] = None
    except Exception as e:
        _sync_state["result"] = None
        _sync_state["error"] = str(e)
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
                True,
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
    # CALLBACK 4: Check novos dados (startup) — NON-BLOCKING
    # =============================================
    _check_result = {"data": None, "done": False}
    _CHECK_TIMEOUT_SECONDS = 15  # Timeout máximo para não bloquear o UI

    def _run_check_new_data():
        """Executa check_new_data em thread separada para não bloquear o Dash."""
        try:
            result = check_new_data()
            _check_result["data"] = result
        except Exception as e:
            print(f"[CHECK] Erro na thread: {e}", flush=True)
            _check_result["data"] = {"has_new_data": False, "error": str(e)}
        finally:
            _check_result["done"] = True

    @app.callback(
        Output("new-data-poll-interval", "disabled", allow_duplicate=True),
        [Input("new-data-check-interval", "n_intervals")],
        prevent_initial_call=True
    )
    def check_new_data_on_startup(n_intervals):
        """Dispara thread de verificação de novos dados (NÃO bloqueia).
        
        Apenas inicia a thread e ativa o polling interval.
        O resultado é lido pelo callback poll_new_data_check.
        """
        if n_intervals == 0:
            return True  # Mantém polling desabilitado
        
        # Reset e dispara thread
        _check_result["data"] = None
        _check_result["done"] = False
        
        check_thread = threading.Thread(target=_run_check_new_data, daemon=True)
        check_thread.start()
        # NÃO faz thread.join() — retorna imediatamente
        return False  # Ativa o polling interval

    # =============================================
    # CALLBACK 5: Polling não-bloqueante para check de novos dados
    # =============================================
    @app.callback(
        [
            Output("sync-new-data-toast", "is_open"),
            Output("new-data-toast-body", "children"),
            Output("new-data-poll-interval", "disabled"),
        ],
        [Input("new-data-poll-interval", "n_intervals")],
        prevent_initial_call=True
    )
    def poll_new_data_check(n_intervals):
        """Polling não-bloqueante para o resultado do check de novos dados.
        
        Verifica a cada 3s se a thread de check terminou.
        Quando terminar, mostra toast (se houver novos dados) e desativa polling.
        Suporta resultado do fallback local (quando Databricks está inacessível).
        """
        if _check_result.get("done"):
            result = _check_result.get("data", {})
            if result and result.get("has_new_data"):
                is_fallback = result.get("fallback", False)
                local_date = result.get("local_max_date", "?")
                
                if is_fallback:
                    # Fallback local: não temos a data remota, mas sabemos que está atrasado
                    days_behind = result.get("days_behind", "?")
                    msg = f"Dados locais com {days_behind} dias de atraso (último: {local_date}). Sincronize para atualizar."
                else:
                    # Check remoto normal
                    remote_date = result.get("remote_max_date", "?")
                    msg = f"Dados disponíveis até {remote_date} (local: até {local_date})."
                
                return True, msg, True  # Mostra toast + desativa polling
            
            if result and not result.get("error"):
                pass
            
            return False, "", True  # Sem dados novos + desativa polling
        
        # Thread ainda rodando — retorna sem atualizar
        return no_update, no_update, no_update
