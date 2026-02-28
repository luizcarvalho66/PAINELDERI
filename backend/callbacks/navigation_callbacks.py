from dash import Input, Output, State, html, callback_context, no_update
import dash_bootstrap_components as dbc


def register_navigation_callbacks(app):
    @app.callback(
        [Output("page-dashboard", "style"),
         Output("page-farol", "style"),
         Output("page-reports", "style"),
         Output("page-config", "style")],
        [Input("url", "pathname")],
        prevent_initial_call=True
    )
    def toggle_page_visibility(pathname):
        """
        Navegação show/hide: alterna display dos containers de página.
        O dashboard nunca é destruído, preservando charts e KPIs.
        """
        show = {"display": "block"}
        hide = {"display": "none"}

        if pathname == "/farol":
            return hide, show, hide, hide
        elif pathname == "/relatorios":
            return hide, hide, show, hide
        elif pathname == "/config":
            return hide, hide, hide, show
        
        # Default: dashboard (pathname == "/" ou qualquer outro)
        return show, hide, hide, hide
