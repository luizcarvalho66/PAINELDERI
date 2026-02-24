from dash import Input, Output, State, html, callback_context, no_update
import dash_bootstrap_components as dbc
from frontend.pages.dashboard import render_dashboard
from frontend.components.farol_section import render_farol_section
from frontend.components.reports_section import render_reports_section

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "padding": "2rem 3rem",
    "minHeight": "100vh",
}

def register_navigation_callbacks(app):
    @app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")],
        prevent_initial_call=True
    )
    def render_page_content(pathname):
        if pathname == "/":
            return no_update
        elif pathname == "/farol":
            return render_farol_section()
        elif pathname == "/relatorios":
            return render_reports_section()
            
        return html.Div(
            dbc.Container(
                [
                    html.H1("404: Not Found", className="text-danger"),
                ],
                className="p-3 bg-light rounded-3",
            )
        )
    

