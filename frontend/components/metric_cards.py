from dash import html

def make_metric_card(title, value, delta, color="edenred-red"):
    is_positive = "+" in delta
    delta_color = "success" if is_positive else "danger"
    icon = "bi bi-graph-up-arrow" if is_positive else "bi bi-graph-down-arrow"
    
    return html.Div(
        [
            html.Div([
                html.H6(title, className="text-muted mb-0", style={"font-size": "0.875rem", "text-transform": "uppercase", "letter-spacing": "0.05em"}),
                html.I(className=f"bi bi-question-circle-fill text-muted ms-2", style={"font-size": "0.9rem", "cursor": "help"})
            ], className="d-flex justify-content-between align-items-center mb-3"),
            
            html.H2(value, className="executive-title mb-2", style={"font-size": "1.75rem"}),
            
            html.Div([
                html.Span([
                    html.I(className=f"{icon} me-1"),
                    delta
                ], className=f"badge rounded-pill bg-{delta_color}-subtle text-{delta_color} px-2 py-1"),
                html.Small(" vs mês ant.", className="text-muted ms-2", style={"font-size": "0.75rem"})
            ], className="d-flex align-items-center")
        ],
        className="metric-card"
    )
