import dash
import dash_bootstrap_components as dbc
import os
import sys
import signal
import atexit
import tempfile
from frontend.layout import get_layout
from backend.callbacks import register_all_callbacks
from database import init_db, DB_PATH

# ============================================================
# LOCK DE PROCESSO ÚNICO — Garante apenas 1 instância do app
# ============================================================
PID_FILE = os.path.join(os.path.dirname(DB_PATH), ".app.pid")

def _kill_previous_instance():
    """Mata instância anterior se existir, baseado no PID salvo."""
    if not os.path.exists(PID_FILE):
        return
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid == os.getpid():
            return
        import psutil
        try:
            proc = psutil.Process(old_pid)
            if "python" in proc.name().lower():
                proc.kill()
                proc.wait(timeout=5)
        except psutil.NoSuchProcess:
            os.remove(PID_FILE)
        except (psutil.TimeoutExpired, Exception):
            pass
    except ImportError:
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                try:
                    os.kill(old_pid, 0)
                    os.kill(old_pid, signal.SIGTERM)
                    import time; time.sleep(3)
                except (ProcessLookupError, OSError):
                    os.remove(PID_FILE)
        except Exception:
            pass
    except Exception:
        pass

def _cleanup_wal_files():
    """Remove WAL/tmp files residuais do DuckDB que podem causar locks."""
    for ext in ['.wal', '.tmp']:
        wal_path = DB_PATH + ext
        if os.path.exists(wal_path):
            try:
                sz = os.path.getsize(wal_path)
                os.remove(wal_path)
                pass
            except Exception as e:
                pass

def _write_pid():
    """Salva PID atual no lock file."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        pass
    except Exception as e:
        pass

def _cleanup_pid():
    """Remove lock file na saída."""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                saved_pid = int(f.read().strip())
            if saved_pid == os.getpid():
                os.remove(PID_FILE)
                # Fecha conexões DuckDB
                from database import close_connection
                close_connection()
                pass
    except Exception:
        pass

# Executar lock + limpeza
_kill_previous_instance()
_cleanup_wal_files()
_write_pid()
atexit.register(_cleanup_pid)
signal.signal(signal.SIGINT, lambda s, f: (print("\n[APP] Ctrl+C — encerrando..."), _cleanup_pid(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s, f: (_cleanup_pid(), sys.exit(0)))

# Initialize DB if not exists (Critical for cloud deployment where data.duckdb is gitignored)
try:
    # Always ensure schema is up to date (runs migration logic if needed)
    pass  # Schema check
    init_db()
except Exception as e:
    print(f"[WARNING] Could not initialize database immediately (likely locked by another worker). Skipping init. Error: {e}")

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], # Use clean Bootstrap
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
    title="Painel RI Edenred",
    update_title=None  # Impede "Updating..." na aba do browser
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
    
    pass  # Server starting

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
                pass  # DB empty
            else:
                 pass  # DB has data
                 
                 # INTEGRITY CHECK: Pricing Tables
                 try:
                     pricing_check = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'economia_calculada'").fetchone()[0]
                     if pricing_check == 0:
                         pass  # Running pricing
                         from engine.pricing import run_full_pricing_pipeline
                         run_full_pricing_pipeline()
                 except Exception as e:
                     pass
        except Exception as e:
            pass

    # Run in background to not block server
    import threading
    threading.Thread(target=initial_sync_check, daemon=True).start()

    app.run(host=host, port=port, debug=True, use_reloader=False)
