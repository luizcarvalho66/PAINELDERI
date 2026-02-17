"""
Sidebar Toggle Callback - Modern UX/UI Design
Handles expand/collapse state transitions
"""
from dash import Input, Output, State


def register_sidebar_callbacks(app):
    @app.callback(
        [
            Output("sidebar", "className"),
            Output("page-content", "style"),
        ],
        [Input("sidebar-toggle", "n_clicks")],
        [
            State("page-content", "style"),
            State("sidebar", "className"),
        ],
        prevent_initial_call=True,
    )
    def toggle_sidebar(n_clicks, content_style, sidebar_classname):
        """Toggle sidebar between expanded (260px) and collapsed (72px) states."""
        if sidebar_classname is None:
            sidebar_classname = "sidebar-premium"

        if content_style is None:
            content_style = {"marginLeft": "260px"}

        if "collapsed" in sidebar_classname:
            # Expand
            content_style["marginLeft"] = "260px"
            sidebar_classname = sidebar_classname.replace(" collapsed", "")
        else:
            # Collapse
            content_style["marginLeft"] = "72px"
            sidebar_classname += " collapsed"

        return sidebar_classname, content_style
