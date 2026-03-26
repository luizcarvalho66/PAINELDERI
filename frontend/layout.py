from dash import dcc, html
import dash_bootstrap_components as dbc
from frontend.components.sidebar import render_sidebar


CONTENT_STYLE = {
    "padding": "2rem 3rem",
    "minHeight": "100vh",
}

from frontend.pages.dashboard import render_dashboard
from frontend.components.farol_section import render_farol_section
from frontend.components.reports_section import render_reports_section

# Navegação show/hide: todas as seções existem permanentemente no DOM.
# A navegação apenas alterna display: block/none, preservando o estado dos charts/KPIs.
content = html.Div([
    html.Div(render_dashboard(), id="page-dashboard", style={"display": "block"}),
    html.Div(render_farol_section(), id="page-farol", style={"display": "none"}),
    html.Div(render_reports_section(), id="page-reports", style={"display": "none"}),
    html.Div(
        html.Div([
            html.Div([
                html.I(className="bi bi-cone-striped", style={
                    "fontSize": "4rem", "color": "#f59e0b",
                    "filter": "drop-shadow(0 4px 12px rgba(245, 158, 11, 0.3))"
                }),
                html.H3("Seção em Construção", style={
                    "fontFamily": "DIN, sans-serif", "fontWeight": "700",
                    "color": "#1e293b", "marginTop": "1.5rem", "marginBottom": "0.5rem"
                }),
                html.P("Esta funcionalidade está sendo desenvolvida e estará disponível em breve.",
                       style={"color": "#94A3B8", "fontSize": "0.95rem", "maxWidth": "400px"}),
            ], className="text-center", style={
                "display": "flex", "flexDirection": "column", "alignItems": "center",
                "justifyContent": "center", "minHeight": "60vh"
            })
        ], className="p-4", style={"backgroundColor": "#f8fafc", "minHeight": "calc(100vh - 60px)"}),
        id="page-config", style={"display": "none"}
    ),
], id="page-content")

def get_layout():
    return html.Div([
        dcc.Location(id="url"),
        dcc.Store(id="processing-complete-store", data=False, storage_type="session"),
        # Store para estado dos filtros aplicados - DEVE ESTAR NO LAYOUT PRINCIPAL
        dcc.Store(id="global-filters-applied-store", data={}),
        dcc.Store(id="chart-granularity-store", data="mensal"),
        dcc.Store(id="side_click"), 
        
        # Store para resultado do check de novos dados
        dcc.Store(id="new-data-check-store", data=None),
        
        # Interval Global para verificar persistência de dados (necessário estar no layout root para callbacks globais)
        dcc.Interval(
            id="dashboard-persistence-check",
            interval=2000,  # Reduzido de 3000 para 2000ms para inicialização mais rápida
            max_intervals=10,  # Aumentado de 3 para 10 (20 segundos de tentativas)
            n_intervals=0
        ),
        
        # Interval para polling do sync (ativado pelo botão Sincronizar)
        dcc.Interval(
            id="sync-poll-interval",
            interval=2000,  # Verifica a cada 2 segundos
            disabled=True,  # Inicia desabilitado, ativado ao clicar em Sincronizar
            n_intervals=0
        ),
        
        # Interval one-shot para verificar novos dados (roda 10s após startup)
        dcc.Interval(
            id="new-data-check-interval",
            interval=10000,  # 10 segundos
            max_intervals=1,  # Roda apenas 1 vez
            n_intervals=0
        ),
        
        # Interval para polling do check de novos dados (ativado pelo check_new_data_on_startup)
        # Aumentado: 40 tentativas a cada 5s (~3.3 min) — suporta warehouse iniciando
        dcc.Interval(
            id="new-data-poll-interval",
            interval=5000,      # Verifica a cada 5 segundos
            max_intervals=40,   # Máximo ~3.3 min de polling
            disabled=True,      # Inicia desabilitado
            n_intervals=0
        ),

        # Interval para retry quando warehouse está off (backoff 15s, ~10 min)
        dcc.Interval(
            id="warehouse-retry-interval",
            interval=15000,     # Verifica a cada 15 segundos
            max_intervals=40,   # Máximo ~10 min de polling
            disabled=True,      # Inicia desabilitado
            n_intervals=0
        ),

        # Placeholder oculto — o modal foi removido mas o ID precisa existir para callbacks
        html.Div(id="modal-databricks-auth", style={"display": "none"}),

        # Toast de verificação de dados (canto superior direito) — ÚNICO FEEDBACK
        dbc.Toast(
            [
                html.P(id="new-data-toast-body", className="mb-0 small"),
            ],
            id="sync-new-data-toast",
            header="Verificando Dados...",
            icon="info",
            is_open=False,
            dismissable=True,
            duration=12000,  # 12 segundos (override dinâmico para warehouse off)
            style={
                "position": "fixed",
                "top": 20,
                "right": 20,
                "zIndex": 9999,
                "minWidth": "360px",
                "maxWidth": "420px",
                "borderRadius": "14px",
                "boxShadow": "0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06)",
                "fontFamily": "Ubuntu, sans-serif",
            },
            header_style={"color": "#1A1A2E", "fontWeight": "700", "fontSize": "0.9rem"},
            body_style={"background": "#fff", "borderRadius": "0 0 14px 14px"},
        ),

        # Placeholders ocultos: IDs precisam existir no layout root para que
        # o Dash não lance erro de ID inexistente (são renderizados dinamicamente).
        html.Div(id="btn-sync-empty-state", style={"display": "none"}),
        html.Div(id="btn-retry-databricks-check", style={"display": "none"}),

        render_sidebar(),
        content,

    ])


