from dash import html, dcc
import dash_bootstrap_components as dbc

def render_error_display(error_message=None, technical_details=None):
    """
    Renders a professional error state component.
    
    Args:
        error_message (str): User-friendly error message. e.g. "Não foi possível carregar os dados."
        technical_details (str): Technical explanation. e.g. "Database Locked"
    """
    
    if not error_message:
        error_message = "Ocorreu um erro ao carregar os dados."
        
    return dbc.Container([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.I(className="bi bi-exclamation-octagon-fill", style={"fontSize": "4rem", "color": "#E20613"})
                    ], className="mb-4"),
                    
                    html.H3("Erro de Conexão", className="fw-bold mb-3", style={"color": "#1e293b"}),
                    
                    html.P(error_message, className="text-muted fs-5 mb-4", style={"maxWidth": "600px", "margin": "0 auto"}),
                    
                    # Technical details section (collapsible or small)
                    html.Div([
                        html.Small("Detalhes Técnicos:", className="fw-bold text-uppercase text-secondary", style={"fontSize": "0.7rem"}),
                        html.Pre(technical_details, className="mt-2 p-3 bg-light rounded text-start text-danger border", style={"fontSize": "0.8rem", "overflowX": "auto"})
                    ], className="mb-4", style={"display": "block" if technical_details else "none"}),
                    
                    html.Div([
                        dbc.Button([
                            html.I(className="bi bi-arrow-clockwise me-2"),
                            "Tentar Novamente"
                        ], href="/", external_link=True, color="danger", className="px-4 py-2 rounded-pill fw-bold shadow-sm")
                    ])
                ], className="text-center p-5")
            ])
        ], className="shadow-lg border-0 rounded-4")
    ], fluid=True, className="d-flex align-items-center justify-content-center h-100 py-5")
