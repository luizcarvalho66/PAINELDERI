import dash
import dash_bootstrap_components as dbc
import os
import tempfile
from frontend.layout import get_layout
from backend.callbacks import register_all_callbacks
from database import init_db, DB_PATH

# Initialize DB if not exists (Critical for cloud deployment where data.duckdb is gitignored)
try:
    # Always ensure schema is up to date (runs migration logic if needed)
    print(f"Checking database schema at {DB_PATH}...")
    init_db()
except Exception as e:
    print(f"[WARNING] Could not initialize database immediately (likely locked by another worker). Skipping init. Error: {e}")

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], # Use clean Bootstrap
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    title="Painel RI Edenred"
)

server = app.server

# Set Layout
app.layout = get_layout()

# Register Callbacks
register_all_callbacks(app)

# Initialize Cache
from backend.cache_config import cache
# SimpleCache (in-memory): cache morre com o processo — zero dados fantasma entre reinícios
cache_config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300, # 5 minutes default
    "CACHE_THRESHOLD": 50  # Máximo de itens no dict in-memory
}

cache.init_app(app.server, config=cache_config)
from backend.cache_config import mark_cache_initialized
mark_cache_initialized(cache_dir=None)  # SimpleCache não tem diretório

if __name__ == "__main__":
    # Use environment variables for configuration
    host = os.getenv("DASH_SERVER_ADDRESS", "127.0.0.1")
    port = int(os.getenv("DASH_SERVER_PORT", "8080"))
    
    # CRITICAL FIX: Default debug/reloader to FALSE for production stability.
    # The 'IO Error: Conflicting lock' happens because reloader spawns a second process.
    import sys
    
    # Check for --reload arg manually to avoid complex argparse setup for just one flag
    force_reload = "--reload" in sys.argv
    env_debug = os.getenv("DASH_DEBUG", "False").lower() == "true"
    
    debug_mode = env_debug or force_reload
    
    print(f"Starting server on {host}:{port} (Debug: True)")

    # DATA CHECK ON STARTUP (Background Thread)
    # Checks if DB has data and runs pricing pipeline if needed
    def initial_sync_check():
        import time
        from database import get_connection

        time.sleep(5) # Wait for server to start
        try:
            conn = get_connection()
            # Check if main table has data
            try:
                count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
            except:
                count = 0
            
            if count == 0:
                # Database empty — user must sync via sidebar button
                # NOTE: Auto-import de Parquet foi DESABILITADO para evitar dados fantasma.
                # Os arquivos em data/export/ podem conter dados com schema legado.
                print("[APP STARTUP] Database empty. Use o botão 'Sincronizar' no sidebar.", flush=True)
            else:
                 print(f"[APP STARTUP] Database has {count} records. Checking integrity...", flush=True)
                 
                 # INTEGRITY CHECK: Pricing Tables
                 try:
                     pricing_check = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'economia_calculada'").fetchone()[0]
                     if pricing_check == 0:
                         print("[APP STARTUP] Pricing tables missing. Running pricing pipeline...", flush=True)
                         from engine.pricing import run_full_pricing_pipeline
                         run_full_pricing_pipeline()
                 except Exception as e:
                     print(f"[APP STARTUP] Warning: Failed to check/run pricing: {e}", flush=True)
        except Exception as e:
            print(f"[APP STARTUP ERROR] Failed to check/sync data: {e}", flush=True)

    # Run in background to not block server
    import threading
    threading.Thread(target=initial_sync_check, daemon=True).start()

    app.run(host=host, port=port, debug=True, use_reloader=False)
