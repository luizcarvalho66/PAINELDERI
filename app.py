import dash
import dash_bootstrap_components as dbc
import os
import sys
import signal
import atexit

# Carregar .env para dev local (em produção, app.yaml injeta as env vars)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opcional — em produção não precisa
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
    """Salva PID atual no lock file com file locking atomico."""
    try:
        fd = os.open(PID_FILE, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        try:
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except (ImportError, OSError):
            pass  # Em Linux/prod, gunicorn gerencia processos
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except Exception:
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

# Executar lock + limpeza — APENAS em modo dev local
# Em gunicorn (produção), o master gerencia signals. Sobrescrever SIGTERM mata o worker.
_is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
if not _is_gunicorn:
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

# ============================================================
# DIAGNÓSTICO DE PRODUÇÃO — /health e /diag endpoints
# Rodam no Flask puro (bypassam Dash), ultra-leves.
# Se /health responder → proxy está roteando OK.
# Se não responder → problema é proxy/rede, não código.
# ============================================================
import json
from datetime import datetime

@server.route('/health')
def health_check():
    """Endpoint mínimo. Se responder, o proxy está OK."""
    return json.dumps({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }), 200, {'Content-Type': 'application/json'}

@server.route('/diag')
def diagnostics():
    """Diagnóstico completo de produção — protegido por SSO Databricks."""
    from flask import request
    # SECURITY: Só responde se autenticado via SSO Databricks ou acesso local
    is_databricks = os.path.exists("/app/python")
    has_sso_header = request.headers.get('X-Databricks-User') or request.headers.get('X-Forwarded-Access-Token')
    is_localhost = request.remote_addr in ('127.0.0.1', '::1')
    
    if not (is_databricks or has_sso_header or is_localhost):
        return json.dumps({"error": "Unauthorized"}), 403, {'Content-Type': 'application/json'}
    
    diag = {
        "timestamp": datetime.utcnow().isoformat(),
        "is_databricks_app": is_databricks,
    }
    
    # 1. Environment Variables (sensíveis mascaradas)
    diag["env"] = {
        "DATABRICKS_HOST": os.getenv("DATABRICKS_HOST", "NOT SET"),
        "DATABRICKS_CLIENT_ID": "SET ✅" if os.getenv("DATABRICKS_CLIENT_ID") else "NOT SET ❌",
        "DATABRICKS_CLIENT_SECRET": "SET ✅" if os.getenv("DATABRICKS_CLIENT_SECRET") else "NOT SET ❌",
        "DATABRICKS_TOKEN": "SET ✅" if os.getenv("DATABRICKS_TOKEN") else "NOT SET ❌",
        "DASH_DEBUG": os.getenv("DASH_DEBUG", "NOT SET"),
        "SERVER_SOFTWARE": os.getenv("SERVER_SOFTWARE", "NOT SET"),
    }
    
    # 2. DuckDB local status
    try:
        from database import get_connection, DB_PATH
        diag["duckdb"] = {"path": DB_PATH, "exists": os.path.exists(DB_PATH)}
        try:
            conn = get_connection()
            count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
            diag["duckdb"]["status"] = "OK ✅"
            diag["duckdb"]["records"] = count
        except Exception as e:
            diag["duckdb"]["status"] = f"ERROR ❌: {str(e)[:200]}"
    except Exception as e:
        diag["duckdb"] = {"status": f"IMPORT ERROR: {str(e)[:200]}"}

    # 3. Databricks SDK Config test (auth do Service Principal)
    try:
        from databricks.sdk.core import Config
        cfg = Config()
        diag["databricks_auth"] = {
            "host": cfg.host or "NOT SET",
            "auth_type": str(cfg.auth_type) if hasattr(cfg, 'auth_type') else "unknown",
            "config_ok": True,
        }
        # Tenta autenticar de verdade
        try:
            headers = cfg.authenticate()
            diag["databricks_auth"]["headers_returned"] = bool(headers)
            diag["databricks_auth"]["status"] = "AUTH OK ✅"
        except Exception as auth_e:
            diag["databricks_auth"]["status"] = f"AUTH FAILED ❌: {str(auth_e)[:300]}"
    except Exception as e:
        diag["databricks_auth"] = {"status": f"SDK ERROR ❌: {str(e)[:300]}"}
    
    # 4. Request headers (para ver se X-Forwarded-Access-Token chega)
    from flask import request
    diag["request_headers"] = {
        k: v for k, v in request.headers
        if k.lower() in [
            'host', 'x-forwarded-for', 'x-forwarded-proto',
            'x-forwarded-access-token', 'x-real-ip', 'user-agent',
            'x-databricks-user', 'x-databricks-org-id',
        ]
    }
    
    print(f"[DIAG] Diagnostics requested at {diag['timestamp']}", flush=True)
    return json.dumps(diag, indent=2, default=str), 200, {'Content-Type': 'application/json'}

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
            except Exception:
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

    app.run(host=host, port=port, debug=debug_mode, use_reloader=False)
