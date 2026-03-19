# -*- coding: utf-8 -*-
"""
Sidebar Callbacks - Reset DB com senha de administrador

O toggle do sidebar continua em JS puro (assets/sidebar-toggle.js).
Aqui ficam apenas os callbacks de Reset do banco.
"""

from dash import Input, Output, State, html, no_update, ctx, dcc, clientside_callback
import dash_bootstrap_components as dbc
import os
import glob
import time


# Senha de administrador para reset — via env var (NUNCA hardcoded)
_RESET_PASSWORD = os.environ.get("ADMIN_RESET_PASSWORD", "")


def register_sidebar_callbacks(app):
    
    # 1. Abrir modal de reset quando botão clicado
    @app.callback(
        Output("modal-reset-db", "is_open"),
        [
            Input("btn-reset-db", "n_clicks"),
            Input("btn-reset-cancel", "n_clicks"),
        ],
        State("modal-reset-db", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_reset_modal(n_open, n_cancel, is_open):
        trigger = ctx.triggered_id
        if trigger == "btn-reset-db":
            return True
        if trigger == "btn-reset-cancel":
            return False
        return not is_open
    
    # 2. Executar reset e dar feedback + sinalizar reload
    @app.callback(
        [
            Output("reset-feedback", "children"),
            Output("reset-reload-signal", "data"),
        ],
        Input("btn-reset-confirm", "n_clicks"),
        State("input-reset-password", "value"),
        prevent_initial_call=True,
    )
    def execute_reset(n_clicks, password):
        if not password or password.strip() != _RESET_PASSWORD:
            return (
                html.Div(
                    [
                        html.I(className="bi bi-x-circle-fill text-danger me-2"),
                        html.Span("Senha incorreta.", className="text-danger fw-bold"),
                    ],
                    className="animate__animated animate__shakeX",
                ),
                no_update,  # Não recarregar
            )
        
        # === EXECUTA RESET REAL ===
        try:
            # 1. Fechar conexões DuckDB existentes
            try:
                from database import close_connection
                close_connection()
                print("[RESET] Conexões DuckDB fechadas.")
            except Exception as e:
                print(f"[RESET] Erro ao fechar conexão: {e}")
            
            # 2. Deletar arquivos DuckDB
            db_files = glob.glob("data/dashboard.duckdb*")
            for f in db_files:
                try:
                    os.remove(f)
                    print(f"[RESET] Deletado: {f}")
                except Exception as e:
                    print(f"[RESET] Erro ao deletar {f}: {e}")
            
            # 3. Deletar snapshots JSON
            json_files = [
                "data/farol_stats_snapshot.json",
                "data/kpi_history.json",
            ]
            for f in json_files:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"[RESET] Deletado: {f}")
            
            # 4. Limpar cache in-memory
            try:
                from backend.cache_config import clear_cache
                clear_cache()
                print("[RESET] Cache limpo.")
            except Exception as e:
                print(f"[RESET] Erro ao limpar cache: {e}")
            
            # 5. Recriar DB com schema vazio
            try:
                from database import init_db
                init_db()
                print("[RESET] Schema recriado com sucesso.")
            except Exception as e:
                print(f"[RESET] Erro ao recriar schema: {e}")
            
            print("[RESET] ✅ Reset completo. Página será recarregada.")
            
            return (
                html.Div(
                    [
                        html.I(className="bi bi-check-circle-fill text-success me-2", style={"fontSize": "1.5rem"}),
                        html.Div(
                            [
                                html.Span("Reset realizado com sucesso!", className="text-success fw-bold d-block"),
                                html.Small(
                                    "Recarregando a página...",
                                    className="text-muted",
                                ),
                            ],
                            className="mt-2",
                        ),
                    ],
                ),
                time.time(),  # Sinaliza reload com timestamp
            )
        except Exception as e:
            return (
                html.Div(
                    [
                        html.I(className="bi bi-exclamation-circle-fill text-warning me-2"),
                        html.Span("Erro no reset. Verifique os logs do servidor.", className="text-warning"),
                    ],
                ),
                no_update,
            )
    
    # 3. Limpar input de senha ao abrir o modal
    @app.callback(
        [
            Output("input-reset-password", "value"),
            Output("reset-feedback", "children", allow_duplicate=True),
        ],
        Input("btn-reset-db", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_password_on_open(n_clicks):
        return "", ""
    
    # 4. Clientside callback: recarregar página após reset bem-sucedido
    app.clientside_callback(
        """
        function(data) {
            if (data) {
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("btn-reset-db", "style"),  # dummy output (não usado)
        Input("reset-reload-signal", "data"),
        prevent_initial_call=True,
    )
