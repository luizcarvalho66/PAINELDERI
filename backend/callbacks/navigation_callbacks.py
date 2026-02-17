from dash import Input, Output, State, html, callback_context
import dash_bootstrap_components as dbc
from frontend.pages.dashboard import render_dashboard
from frontend.components.farol_section import render_farol_section

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "padding": "2rem 3rem",
    "minHeight": "100vh",
}

def register_navigation_callbacks(app):
    @app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")]
    )
    def render_page_content(pathname):
        import datetime
        print(f"[DEBUG][{datetime.datetime.now()}] NAVIGATION: Pathname={pathname}")
        if pathname == "/":
            return render_dashboard()
        elif pathname == "/farol":
            return render_farol_section()
            
        return html.Div(
            dbc.Container(
                [
                    html.H1("404: Not Found", className="text-danger"),
                ],
                className="p-3 bg-light rounded-3",
            )
        )
    

