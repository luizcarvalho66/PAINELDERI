
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
        has_data = check_database_status()
        print(f"[ACTIVATION] n={n}, is_processed={is_processed}, has_data={has_data}", flush=True)
        if has_data:
            return True
            
        return no_update
