
from dash import Input, Output, State, no_update
from backend.repositories import check_database_status

def register_activation_callbacks(app):
    @app.callback(
        Output("processing-complete-store", "data", allow_duplicate=True),
        [Input("dashboard-persistence-check", "n_intervals")],
        [State("processing-complete-store", "data")],
        prevent_initial_call='initial_duplicate'
    )
    def check_persistence_activation(n, is_processed):
        """
        Verifica se o banco já tem dados na inicialização.
        Se sim, ativa o Dashboard automaticamente.
        """
        # Se já estiver processado, não faz nada
        if is_processed:
            return no_update
            
        # Verifica banco
        if check_database_status():
            print("[ACTIVATION] Dados detectados no banco. Ativando dashboard...")
            return True
            
        return no_update
