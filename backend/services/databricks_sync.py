import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import time
import warnings
import logging
import pandas as pd
from databricks import sql
from database import get_connection

# Suprimir warnings repetitivos que poluem o terminal
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*State not equal in request and response.*")
warnings.filterwarnings("ignore", message=".*CloudFetch download slower.*")
logging.getLogger("databricks.sql").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Apache Arrow para download 2-3x mais rápido
try:
    import pyarrow as pa
    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False
    print("[SYNC WARNING] PyArrow não instalado. Usando fetchmany() padrão (mais lento).", flush=True)
    print("[SYNC WARNING] Instale com: pip install pyarrow", flush=True)

try:
    from backend.services.tgm_client_config import TGM_CLIENT_IDS
except ImportError:
    from tgm_client_config import TGM_CLIENT_IDS

try:
    from backend.cache_config import clear_cache
except ImportError:
    def clear_cache(): pass

try:
    from engine.pricing import run_full_pricing_pipeline
except ImportError:
    def run_full_pricing_pipeline():
        print("[SYNC WARNING] Pricing engine not found.", flush=True)
        return False

# SECURITY: Sem defaults hardcoded — em producao, env vars sao injetadas pelo Service Principal
# Em dev local, devem ser configuradas no .env
HOST = os.environ.get("DATABRICKS_HOST", "")
HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
PROFILE = os.environ.get("DATABRICKS_PROFILE", "")

# Detecta se estamos dentro de um Databricks App
IS_DATABRICKS_APP = os.path.exists("/app/python")

# =============================================
# PROGRESSO COMPARTILHADO (lido pelo callback)
# =============================================
_sync_progress = {
    "steps": [],
    "current_step": 0,
    "total_records": 0,
    "corretiva_count": 0,
    "preventiva_count": 0,
    "sync_mode": "",
    "sync_description": "",
    "queries_info": [],
}

SYNC_STEPS = [
    {"id": "connect",   "label": "Conectando ao Databricks",            "icon": "bi-plug-fill"},
    {"id": "query",     "label": "Consultando dados no Warehouse",      "icon": "bi-search"},
    {"id": "download",  "label": "Baixando registros",                  "icon": "bi-cloud-arrow-down-fill"},
    {"id": "process",   "label": "Classificando manutenções",           "icon": "bi-cpu-fill"},
    {"id": "save_db",   "label": "Atualizando base local",              "icon": "bi-database-fill-down"},
    {"id": "pricing",   "label": "Calculando economia e medianas",      "icon": "bi-calculator-fill"},
    {"id": "cache",     "label": "Atualizando painel",                  "icon": "bi-arrow-repeat"},
]

def _init_progress():
    """Reseta o progresso para um novo sync."""
    global _sync_progress
    _sync_progress["steps"] = [
        {**step, "status": "pending", "detail": ""} for step in SYNC_STEPS
    ]
    _sync_progress["current_step"] = 0
    _sync_progress["total_records"] = 0
    _sync_progress["corretiva_count"] = 0
    _sync_progress["preventiva_count"] = 0
    _sync_progress["sync_mode"] = ""
    _sync_progress["sync_description"] = ""
    _sync_progress["queries_info"] = []

def _update_step(step_id, status, detail=""):
    """Atualiza o status de uma etapa do sync."""
    global _sync_progress
    for i, step in enumerate(_sync_progress["steps"]):
        if step["id"] == step_id:
            step["status"] = status
            step["detail"] = detail
            if status == "running":
                _sync_progress["current_step"] = i
            break

def get_sync_progress():
    """Retorna o progresso atual (chamado pelo callback)."""
    return _sync_progress.copy()


def check_new_data():
    """
    Verificação LEVE: compara dados locais vs Databricks vs data atual.
    
    Lógica de comparação:
    - has_new_data: Databricks tem dados MAIS NOVOS que o local
    - days_behind: quantos dias os dados locais estão defasados vs HOJE
    - is_stale: dados locais estão defasados (> 1 dia atrás)
    
    Conecta ao Databricks automaticamente (OAuth U2M abre browser se necessário).
    """
    from datetime import datetime, date
    
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    try:
        # Data mais recente local
        local_count = 0
        local_max_date = None
        try:
            conn_local = get_connection()
            local_count = conn_local.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
            try:
                row = conn_local.execute(
                    "SELECT MAX(data_transacao) FROM ri_corretiva_detalhamento"
                ).fetchone()
                if row and row[0]:
                    local_max_date = str(row[0])[:10]  # YYYY-MM-DD
            except Exception:
                pass
        except Exception:
            pass

        # Conectar ao Databricks (OAuth U2M — abre browser se necessário)
        print("[CHECK] Conectando ao Databricks...", flush=True)
        conn_db = get_databricks_conn()
        cursor = conn_db.cursor()
        
        # Query 1: MAX date remota (FIX 2026-03-05: JOINs corretos fi+fs+fc)
        client_ids = ", ".join([str(int(x)) for x in TGM_CLIENT_IDS])  # int() valida numerico
        query_max = f"""
        SELECT MAX(CAST(fi.TransactionTimestamp AS DATE)) as max_date
        FROM hive_metastore.gold.fact_maintenanceitems fi
        INNER JOIN hive_metastore.gold.fact_maintenanceservices fs
            ON fi.Sk_MaintenanceServices = fs.Sk_MaintenanceServices
        INNER JOIN hive_metastore.gold.dim_fuelcustomers fc
            ON fs.Sk_FuelCustomer = fc.Sk_FuelCustomer
        WHERE CAST(fi.TransactionTimestamp AS DATE) >= date_add(current_date(), -150)
          AND fc.CustomerSourceCode IN ({client_ids})
        """
        cursor.execute(query_max)
        row = cursor.fetchone()
        remote_max_date = str(row[0])[:10] if row and row[0] else None
        cursor.close()

        # Query 2: COUNT de registros novos (após local_max_date)
        new_records_count = 0
        if local_max_date:
            try:
                cursor2 = conn_db.cursor()
                query_count = f"""
                SELECT COUNT(*) as new_count
                FROM hive_metastore.gold.fact_maintenanceitems fi
                INNER JOIN hive_metastore.gold.fact_maintenanceservices fs
                    ON fi.Sk_MaintenanceServices = fs.Sk_MaintenanceServices
                INNER JOIN hive_metastore.gold.dim_fuelcustomers fc
                    ON fs.Sk_FuelCustomer = fc.Sk_FuelCustomer
                WHERE CAST(fi.TransactionTimestamp AS DATE) > '{local_max_date}'
                  AND CAST(fi.TransactionTimestamp AS DATE) >= date_add(current_date(), -150)
                  AND fc.CustomerSourceCode IN ({client_ids})
                """
                cursor2.execute(query_count)
                row2 = cursor2.fetchone()
                new_records_count = row2[0] if row2 and row2[0] else 0
                cursor2.close()
            except Exception as e:
                print(f"[CHECK] Erro no COUNT de novos: {e}", flush=True)

        # === Lógica de comparação ===
        # 1. Databricks tem dados mais novos que o local?
        has_new = False
        if remote_max_date and local_max_date:
            has_new = remote_max_date > local_max_date
        elif remote_max_date and not local_max_date:
            has_new = True  # Banco vazio, tem dados remotos

        # 2. Dados locais estão defasados vs HOJE
        days_behind = 0
        is_stale = False
        if local_max_date:
            local_date_obj = datetime.strptime(local_max_date, "%Y-%m-%d").date()
            days_behind = (today - local_date_obj).days
            is_stale = days_behind > 1  # Mais de 1 dia atrás = defasado

        # 3. Pipeline lag: local em dia com Databricks, mas Databricks está atrás
        # Diferencia "precisa sincronizar" de "pipeline Databricks atrasado"
        pipeline_lag = False
        if is_stale and not has_new and remote_max_date and local_max_date:
            # Local == Remote, mas ambos atrás de hoje → culpa do pipeline
            pipeline_lag = remote_max_date <= local_max_date

        print(f"[CHECK] Hoje: {today_str} | Databricks: {remote_max_date} | Local: {local_max_date} | Defasagem: {days_behind}d | Pipeline lag: {pipeline_lag} | Novos registros: {new_records_count:,}", flush=True)

        return {
            "has_new_data": has_new,
            "is_stale": is_stale,
            "pipeline_lag": pipeline_lag,
            "days_behind": days_behind,
            "today": today_str,
            "remote_max_date": remote_max_date,
            "local_max_date": local_max_date,
            "local_count": local_count,
            "new_records_count": new_records_count,
        }
    except Exception as e:
        error_str = str(e).lower()
        # Detectar warehouse desligada/iniciando (SQL Warehouse stopped, starting, etc.)
        warehouse_keywords = ["warehouse", "endpoint", "cluster"]
        warehouse_states = ["stopped", "stopping", "starting", "not running", "terminated", "unavailable"]
        warehouse_off = any(kw in error_str for kw in warehouse_keywords) and any(st in error_str for st in warehouse_states)
        
        if warehouse_off:
            print(f"[CHECK][WAREHOUSE OFF] Warehouse detectada como desligada/iniciando: {e}", flush=True)
        else:
            print(f"[CHECK][ERROR] Erro ao verificar novos dados: {e}", flush=True)
        
        return {"has_new_data": False, "error": str(e), "warehouse_off": warehouse_off}


# Cache de conexão (evita múltiplos U2M)
_cached_conn = None
_conn_created_at = None
_CONN_TTL_SECONDS = 2700  # 45 min (tokens U2M duram ~1h)

def _close_cached_conn():
    """Fecha explicitamente a conexão cached, útil se der erro de socket"""
    global _cached_conn, _conn_created_at
    if _cached_conn:
        try:
            _cached_conn.close()
        except Exception:
            pass
    _cached_conn = None
    _conn_created_at = None

# Alias público para uso no callback de retry OAuth
_clear_cached_connection = _close_cached_conn

def get_databricks_conn():
    """
    Cria conexão com Databricks SQL Warehouse ou retorna do cache.
    Detecta automaticamente o ambiente:
    - Databricks App: usa credentials_provider (OAuth M2M via Service Principal)
      → Delega autenticação ao SDK — robusto entre versões
    - Local: usa CLI profile (~/.databrickscfg) com OAuth U2M
    """
    global _cached_conn, _conn_created_at
    import traceback
    
    # Tentar reusar conexão existente para evitar prompt OAuth (U2M)
    if _cached_conn and _conn_created_at:
        age_seconds = time.time() - _conn_created_at
        if age_seconds < _CONN_TTL_SECONDS:
            try:
                # Teste simples (ping)
                cursor = _cached_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                cursor.close()
                return _cached_conn
            except Exception as e:
                _close_cached_conn()
        else:
            _close_cached_conn()
    
    conn = None
    
    if IS_DATABRICKS_APP:
        
        # Log de diagnóstico: quais variáveis de ambiente existem?
        env_vars = {
            'DATABRICKS_HOST': os.getenv('DATABRICKS_HOST', 'NOT SET'),
            'DATABRICKS_CLIENT_ID': 'SET' if os.getenv('DATABRICKS_CLIENT_ID') else 'NOT SET',
            'DATABRICKS_CLIENT_SECRET': 'SET' if os.getenv('DATABRICKS_CLIENT_SECRET') else 'NOT SET',
            'DATABRICKS_TOKEN': 'SET' if os.getenv('DATABRICKS_TOKEN') else 'NOT SET',
        }
        print(f"[SYNC] Ambiente Databricks App detectado. ENV: {env_vars}", flush=True)
        
        # MÉTODO 1 (RECOMENDADO): credentials_provider via SDK Config
        # Delega toda a autenticação ao SDK — robusto entre versões do SDK.
        # O SP do app precisa ter CAN USE no SQL Warehouse.
        try:
            from databricks.sdk.core import Config
            cfg = Config()
            host = (cfg.host or HOST).replace("https://", "").replace("http://", "").rstrip("/")
            
            def credential_provider():
                """HeaderFactory que o SQL connector usa para obter headers de auth."""
                return cfg.authenticate
            
            conn = sql.connect(
                server_hostname=host,
                http_path=HTTP_PATH,
                credentials_provider=credential_provider,
            )
            print(f"[SYNC] ✅ Conectado via credentials_provider (SDK Config) — host: {host}", flush=True)
                
        except Exception as e:
            print(f"[SYNC] ⚠️ credentials_provider falhou: {e}", flush=True)
            traceback.print_exc()
            
            # MÉTODO 2 (FALLBACK): DATABRICKS_TOKEN env var (app.yaml)
            token = os.getenv('DATABRICKS_TOKEN')
            if token:
                host = os.getenv('DATABRICKS_HOST', HOST).replace("https://", "").replace("http://", "").rstrip("/")
                conn = sql.connect(
                    server_hostname=host,
                    http_path=HTTP_PATH,
                    access_token=token,
                )
                print(f"[SYNC] ✅ Conectado via DATABRICKS_TOKEN env var (fallback)", flush=True)
            else:
                raise
    else:
        # AMBIENTE LOCAL: OAuth U2M via CLI profile (abre browser se necessário)
        conn = sql.connect(
            server_hostname=HOST,
            http_path=HTTP_PATH,
            auth_type="databricks-cli",
            profile=PROFILE,
            _socket_timeout=900,  # 15min — precisa esperar queries grandes
        )
        print(f"[SYNC] ✅ Conectado via OAuth U2M (CLI profile: {PROFILE})", flush=True)
        
    # Salvar no cache antes de retornar
    if conn:
        _cached_conn = conn
        _conn_created_at = time.time()
        
    return conn

def _get_local_date_range():
    """
    Retorna (min_date, max_date, count) dos dados locais.
    Retorna (None, None, 0) se não houver dados.
    """
    try:
        conn = get_connection(read_only=True)
        result = conn.execute("""
            SELECT 
                MIN(data_transacao)::DATE as min_date, 
                MAX(data_transacao)::DATE as max_date,
                COUNT(*) as total
            FROM ri_corretiva_detalhamento
            WHERE data_transacao IS NOT NULL
        """).fetchone()
        if result and result[0]:
            return result[0], result[1], result[2]
    except Exception as e:
        pass
    return None, None, 0


def _build_query(days=150, date_from=None, date_to=None, watermark=None):
    """
    Constrói a query SQL otimizada.
    
    Modos:
    - FULL: date_from=None, date_to=None, watermark=None → últimos {days} dias
    - GAP FILL: date_from + date_to → busca intervalo específico
    - INCREMENTAL: watermark → busca dados mais recentes que watermark
    """
    # SECURITY: Validar formato de datas para prevenir injection
    import re
    _date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    def _safe_date(d):
        """Valida e retorna date string no formato YYYY-MM-DD."""
        d_str = str(d)[:10]
        if not _date_pattern.match(d_str):
            raise ValueError(f"Formato de data invalido: {d_str}")
        return d_str
    
    if watermark:
        date_filter = f"CAST(fi.TransactionTimestamp AS DATE) > '{_safe_date(watermark)}'"
    elif date_from and date_to:
        date_filter = f"CAST(fi.TransactionTimestamp AS DATE) >= '{_safe_date(date_from)}' AND CAST(fi.TransactionTimestamp AS DATE) < '{_safe_date(date_to)}'"
    else:
        date_filter = f"CAST(fi.TransactionTimestamp AS DATE) >= date_add(current_date(), -{int(days)})"
    
    client_ids = ", ".join([str(x) for x in TGM_CLIENT_IDS])
    
    return f"""
    WITH base AS (
        -- Subquery filtrada: aplica filtros de data + cliente ANTES dos JOINs dimensionais
        SELECT /*+ BROADCAST(fc) */
            fi.MaintenanceId,
            fi.MaintenanceItemSourceCode,
            fi.PartComplement,
            fi.QuotedPrice,
            fi.PriceApproved,
            fi.PartPriceApproved,
            fi.LaborPriceApproved,
            fi.Sk_MaintenanceLabor,
            fi.TransactionTimestamp,
            fi.WasPartApproved,
            fi.ReviewTimestamp,
            fs.ApprovalTimestamp,
            fs.CancellationTimestamp,
            fs.DisapprovalTimestamp,
            fi.IsPreventiveMaintenance,
            fi.PartId,
            fi.Sk_MaintenancePart,
            fs.OrderServiceCode,
            fs.VehicleSourceCode as IdVehicle,
            fs.Sk_MaintenanceVehicle,
            fs.Sk_MaintenanceMerchant,
            fs.Sk_ServiceOrderApprover,
            fs.Sk_FirstApprover,
            fs.Sk_ServiceOrderApprovalHistory,
            fs.MileageNumber,
            fs.MaintenanceTypeCode,
            fs.ManagerReport,
            COALESCE(fs.IsAutomaticApproval, false) as IsAutomaticApproval,
            cast(fc.CustomerSourceCode as string) as codigo_cliente,
            cast(fc.CustomerSourceCode as string) as codigo_tgm,
            COALESCE(fc.CustomerShortName, CONCAT('Cliente ', cast(fc.CustomerSourceCode as string))) as nome_cliente
        FROM hive_metastore.gold.fact_maintenanceitems fi
        INNER JOIN hive_metastore.gold.fact_maintenanceservices fs
            ON fi.Sk_MaintenanceServices = fs.Sk_MaintenanceServices
        INNER JOIN hive_metastore.gold.dim_fuelcustomers fc
            ON fs.Sk_FuelCustomer = fc.Sk_FuelCustomer
        WHERE {date_filter}
          AND fc.CustomerSourceCode IN ({client_ids})
          AND fi.CancellationTimestamp IS NULL
    )
    SELECT 
        cast(b.OrderServiceCode as string) as numero_os,
        cast(b.MaintenanceItemSourceCode as string) as codigo_item,
        
        b.codigo_cliente,
        b.codigo_tgm,
        cast(b.Sk_MaintenanceMerchant as string) as codigo_estabelecimento,
        b.nome_cliente,
        COALESCE(mm.MerchantShortenedName, mm.CorporateName, 'Não Informado') as nome_estabelecimento,
        
        COALESCE(mv.LicensePlate, v.VehiclePlate, 'N/A') as placa,
        COALESCE(mv.VehicleManufacturer, v.NameVehicleManuFacturer, 'N/A') as fabricante,
        COALESCE(v.NameVehicleModel, 'N/A') as modelo_veiculo,
        COALESCE(mv.VehicleFamilyName, v.NameVehicleFamily, 'N/A') as familia_veiculo,
        COALESCE(mv.InitialsState, mm.StateName, 'N/A') as uf,
        COALESCE(mv.NameCity, mm.CityName, 'N/A') as cidade,
        'N/A' as chassi,
        COALESCE(cast(mv.VehicleYear as string), 'N/A') as ano_veiculo,
        
        dmp.PartName as descricao_peca,
        COALESCE(b.PartComplement, 'GENERICA') as complemento_peca,
        
        CASE 
            WHEN b.IsPreventiveMaintenance = true THEN 'PREVENTIVA'
            ELSE 'CORRETIVA'
        END as tipo_manutencao,
        
        CASE 
            WHEN b.CancellationTimestamp IS NOT NULL THEN 'CANCELADA'
            WHEN b.DisapprovalTimestamp IS NOT NULL THEN 'REPROVADA'
            WHEN b.ApprovalTimestamp IS NOT NULL THEN 'APROVADA'
            ELSE 'PENDENTE'
        END as status_os,
        
        try_cast(b.QuotedPrice as double) as valor_total,
        try_cast(b.PriceApproved as double) as valor_aprovado,
        try_cast(b.PartPriceApproved as double) as valor_peca,
        try_cast(COALESCE(b.LaborPriceApproved, (b.PriceApproved - b.PartPriceApproved), 0) as double) as valor_mo,
        
        b.TransactionTimestamp as data_transacao,
        b.ReviewTimestamp as data_atualizacao,
        b.TransactionTimestamp as data_criacao_os,
        b.ApprovalTimestamp as data_aprovacao_os,
        
        COALESCE(wu.WebUserName, 'SISTEMA (Automático)') as nome_aprovador,
        COALESCE(wu.WebUserFullName, 'SISTEMA (Automático)') as nome_aprovador_completo,
        COALESCE(wu.IsInternalUser, false) as is_internal_user,
        
        COALESCE(cast(ml.LaborName as string), 'SEM MO') as tipo_mo,
        try_cast(b.MileageNumber as double) as hodometro,
        COALESCE(sah.ApprovalHistoryName, b.ManagerReport, 'Aprovação Automática') as mensagem_log,
        COALESCE(sah.DetailName, '') as detalhe_regulacao,
        COALESCE(b.WasPartApproved, false) as peca_aprovada,
        b.IsAutomaticApproval as aprovacao_automatica_os,
        
        -- Silent Order PBI: lógica idêntica ao Power BI (FIX 2026-03-25)
        CASE 
            WHEN wu_first.WebUserName = 'Autorizacao De Servico Programado' THEN 'Sim'
            WHEN wu.WebUserName IS NULL AND b.IsPreventiveMaintenance = true THEN 'Sim'
            ELSE 'Não'
        END as silent_order_pbi
        
    FROM base b
    LEFT JOIN hive_metastore.gold.dim_vehicle v 
        ON b.IdVehicle = v.IdVehicle
    LEFT JOIN hive_metastore.gold.dim_maintenancevehicles mv
        ON b.Sk_MaintenanceVehicle = mv.Sk_MaintenanceVehicle
    LEFT JOIN hive_metastore.gold.dim_maintenancemerchants mm
        ON b.Sk_MaintenanceMerchant = mm.Sk_MaintenanceMerchant
    LEFT JOIN hive_metastore.gold.dim_maintenanceparts dmp
        ON b.Sk_MaintenancePart = dmp.Sk_MaintenancePart
    LEFT JOIN hive_metastore.gold.dim_maintenancelabors ml
        ON b.Sk_MaintenanceLabor = ml.Sk_MaintenanceLabor
    LEFT JOIN hive_metastore.gold.dim_webusers wu
        ON b.Sk_ServiceOrderApprover = wu.Sk_WebUser
    LEFT JOIN hive_metastore.gold.dim_webusers wu_first
        ON b.Sk_FirstApprover = wu_first.Sk_WebUser
    LEFT JOIN hive_metastore.gold.dim_serviceordersapprovalhistory sah
        ON b.Sk_ServiceOrderApprovalHistory = sah.Sk_ServiceOrderApprovalHistory
        AND sah.IsLastServiceOrderApproval = true
    """


# Timeout máximo para o download de dados (segundos)
DOWNLOAD_TIMEOUT_SECONDS = 900  # 15 minutos — suporta 2M+ linhas em redes corporativas

def _download_with_arrow(cursor_db, chunk_size=50000):
    """
    Download otimizado usando PyArrow (2-3x mais rápido).
    Inclui timeout graceful: se passar de DOWNLOAD_TIMEOUT_SECONDS,
    para o download e usa os dados já baixados.
    Chunk size de 100K para maximizar throughput.
    """
    total_rows = 0
    download_start = time.time()
    is_partial = False
    
    if HAS_ARROW:
        # MODO ARROW: Muito mais rápido para grandes volumes
        batches = []
        while True:
            # Verificar timeout do download
            elapsed = time.time() - download_start
            if elapsed > DOWNLOAD_TIMEOUT_SECONDS:
                is_partial = True
                _update_step("download", "running", f"Timeout! Usando {total_rows:,} registros parciais...")
                break
            
            try:
                arrow_batch = cursor_db.fetchmany_arrow(chunk_size)
            except Exception as e:
                # Fallback: algumas versões do connector não suportam fetchmany_arrow
                print(f"[SYNC] fetchmany_arrow falhou ({e}), usando fallback...", flush=True)
                return _download_legacy(cursor_db, chunk_size), False
            
            if arrow_batch is None or len(arrow_batch) == 0:
                break
            batches.append(arrow_batch)
            total_rows += len(arrow_batch)
            _sync_progress["total_records"] = total_rows
            elapsed = time.time() - download_start
            rows_per_sec = int(total_rows / elapsed) if elapsed > 0 else 0
            _update_step("download", "running", f"{total_rows:,} registros (Arrow, {elapsed:.0f}s, ~{rows_per_sec:,}/s)...")
        
        if not batches:
            return pd.DataFrame(), False
        
        full_table = pa.concat_tables(batches)
        df = full_table.to_pandas()
    else:
        df = _download_legacy(cursor_db, chunk_size)
    
    return df, is_partial


def _download_legacy(cursor_db, chunk_size=50000):
    """
    Download legado usando fetchmany() puro (sem Arrow).
    """
    cols = [c[0] for c in cursor_db.description]
    all_rows = []
    while True:
        chunk = cursor_db.fetchmany(chunk_size)
        if not chunk:
            break
        all_rows.extend(chunk)
        _sync_progress["total_records"] = len(all_rows)
        _update_step("download", "running", f"{len(all_rows):,} registros...")
    
    return pd.DataFrame(all_rows, columns=cols) if all_rows else pd.DataFrame()


def sync_all_data(days=450):
    """
    Sync híbrido inteligente:
    - FULL: Primeiro sync → baixa todos os {days} dias
    - INCREMENTAL: Dados novos via watermark (rápido)
    - GAP FILL: Dados antigos faltantes (só o intervalo que falta)
    
    Nunca baixa todos os 2M+ registros desnecessariamente.
    """
    
    _init_progress()
    start_total = time.time()
    results = {"success": False, "steps": [], "errors": [], "sync_type": "FULL", "records": 0}
    
    try:
        # STEP 1: Conectar
        _update_step("connect", "running", "Autenticando via CLI profile...")
        conn_db = get_databricks_conn()
        cursor_db = conn_db.cursor()
        _update_step("connect", "done", "Conectado ao SQL Warehouse")
        
        # Analisar dados locais para decidir estratégia
        min_date, max_date, local_count = _get_local_date_range()
        
        import datetime as dt
        today = dt.date.today()
        expected_min = today - dt.timedelta(days=days)
        
        queries_to_run = []  # Lista de (label, query) a executar
        queries_info_list = []  # Info amigável para o modal
        
        if min_date is None:
            # SEM DADOS LOCAIS → FULL LOAD
            sync_type = "FULL"
            query = _build_query(days=days)
            queries_to_run.append(("FULL LOAD", query))
            queries_info_list.append(f"Primeira sincronização — baixando últimos {days} dias")
            _sync_progress["sync_mode"] = "Primeira Sincronização"
            _sync_progress["sync_description"] = f"Baixando todos os dados dos últimos {days} dias para construir a base local."
        else:
            # TEM DADOS LOCAIS → verificar gaps + novos
            sync_type = "SMART"
            _sync_progress["sync_mode"] = "Atualização Inteligente"
            desc_parts = []
            
            # Formatar datas para exibição
            min_str = min_date.strftime("%d/%m/%Y") if hasattr(min_date, 'strftime') else str(min_date)
            max_str = max_date.strftime("%d/%m/%Y") if hasattr(max_date, 'strftime') else str(max_date)
            exp_str = expected_min.strftime("%d/%m/%Y") if hasattr(expected_min, 'strftime') else str(expected_min)
            
            # 1. GAP FILL: dados antigos faltantes?
            if min_date > expected_min:
                gap_days = (min_date - expected_min).days
                query_gap = _build_query(date_from=str(expected_min), date_to=str(min_date))
                queries_to_run.append((f"GAP FILL ({gap_days}d)", query_gap))
                queries_info_list.append(f"Buscando dados históricos: {exp_str} até {min_str} ({gap_days} dias)")
                desc_parts.append(f"Recuperando {gap_days} dias de dados históricos faltantes")
            else:
                desc_parts.append(f"Dados históricos desde {min_str} ✅")
            
            # 2. INCREMENTAL: dados novos após max_date?
            watermark_str = str(max_date)
            query_new = _build_query(watermark=watermark_str)
            queries_to_run.append((f"INCREMENTAL (após {max_date})", query_new))
            queries_info_list.append(f"Buscando novos dados a partir de {max_str}")
            desc_parts.append(f"busca de dados novos após {max_str}")
            
            _sync_progress["sync_description"] = " + ".join(desc_parts) + f". Base local: {local_count:,} registros."
        
        results["sync_type"] = sync_type
        _sync_progress["queries_info"] = queries_info_list
        
        if not queries_to_run:
            results['success'] = True
            return results
        
        # STEP 2-3: Executar queries e baixar dados
        all_dfs = []
        for i, (label, query) in enumerate(queries_to_run):
            _update_step("query", "running", f"Query {i+1}/{len(queries_to_run)}: {label}...")
            cursor_db.execute(query)
            _update_step("query", "done", f"Query {label} executada")
            
            _update_step("download", "running", f"Download {label}...")
            df_part, is_partial = _download_with_arrow(cursor_db, chunk_size=100000)
            partial_label = " ⚠️ PARCIAL" if is_partial else ""
            
            if len(df_part) > 0:
                all_dfs.append(df_part)
        
        # Fechar conexão Databricks (libera recursos no Warehouse)
        try:
            cursor_db.close()
            # NÃO fechamos conn_db pois estamos usando cache (singleton) 
            # e ele poderá ser reusado nos próximos minutos.
        except Exception:
            pass
        
        # Concatenar todos os resultados
        if not all_dfs:
            _update_step("download", "done", "Sem dados novos")
            _update_step("process", "done", "Sem dados")
            _update_step("save_db", "done", "Sem alterações")
            _update_step("pricing", "done", "Pulado")
            _update_step("cache", "done", "Sem alterações")
            results['success'] = True
            elapsed = time.time() - start_total
            return results
        
        df = pd.concat(all_dfs, ignore_index=True)
        # Deduplicar por numero_os + codigo_item (pode ter overlap entre gap fill e incremental)
        df = df.drop_duplicates(subset=['numero_os', 'codigo_item'], keep='last')
        
        _sync_progress["total_records"] = len(df)
        _update_step("download", "done", f"{len(df):,} registros totais")
        results["records"] = len(df)
        
        # STEP 4: Processar dados
        _update_step("process", "running", "Transformando colunas...")
        df['tipo_mo'] = df['tipo_mo'].astype(str)
        df['tipo_manutencao_oficina'] = 'FACT_MAINTENANCE'
        df['peca'] = df['descricao_peca'].fillna('SEM PEÇA')
        df['descricao_servico'] = df['tipo_mo']
        
        for c in ['data_transacao', 'data_atualizacao', 'data_criacao_os', 'data_aprovacao_os']:
            df[c] = pd.to_datetime(df[c], errors='coerce')
        
        df_corretiva = df[df['tipo_manutencao'] == 'CORRETIVA'].copy()
        df_preventiva = df[df['tipo_manutencao'] == 'PREVENTIVA'].copy()
        _sync_progress["corretiva_count"] = len(df_corretiva)
        _sync_progress["preventiva_count"] = len(df_preventiva)
        _update_step("process", "done", f"{len(df_corretiva):,} corretivas, {len(df_preventiva):,} preventivas")
        
        # STEP 5: Salvar no DuckDB — Merge inteligente
        _update_step("save_db", "running", f"Merge {sync_type}...")
        from database import close_connection, get_connection
        try:
            from database import set_maintenance_mode
            set_maintenance_mode(True)
        except ImportError:
            try: close_connection() 
            except Exception: pass
            
        time.sleep(1)
        conn_local = get_connection(read_only=False)
        
        conn_local.register('stg_corretiva', df_corretiva)
        conn_local.register('stg_preventiva', df_preventiva)
        
        if min_date is not None:
            # MERGE: DELETE duplicatas + INSERT (dados existiam antes)
            
            # Mapear colunas do staging para auto-migração
            stg_map = {
                'stg_corretiva': df_corretiva,
                'stg_preventiva': df_preventiva,
            }
            
            for table, stg in [
                ('ri_corretiva_detalhamento', 'stg_corretiva'),
                ('ri_preventiva_detalhamento', 'stg_preventiva'),
                ('logs_corretiva', 'stg_corretiva'),
                ('logs_regulacao_preventiva', 'stg_preventiva'),
            ]:
                try:
                    # Auto-migração: adicionar colunas faltantes na tabela existente
                    try:
                        stg_df = stg_map[stg]
                        stg_cols = list(stg_df.columns)
                        tbl_info = conn_local.execute(f"PRAGMA table_info('{table}')").fetchall()
                        tbl_cols = [r[1] for r in tbl_info]
                        missing = [c for c in stg_cols if c not in tbl_cols]
                        if missing:
                            # Inferir tipos via DESCRIBE do staging registrado
                            stg_types = {}
                            try:
                                desc = conn_local.execute(f"DESCRIBE {stg}").fetchall()
                                stg_types = {r[0]: r[1] for r in desc}
                            except Exception:
                                # Fallback: inferir do pandas dtype
                                for col in missing:
                                    dtype = str(stg_df[col].dtype)
                                    if 'int' in dtype:
                                        stg_types[col] = 'BIGINT'
                                    elif 'float' in dtype:
                                        stg_types[col] = 'DOUBLE'
                                    else:
                                        stg_types[col] = 'VARCHAR'
                            
                            for col in missing:
                                col_type = stg_types.get(col, 'VARCHAR')
                                conn_local.execute(f"ALTER TABLE {table} ADD COLUMN \"{col}\" {col_type}")
                    except Exception as schema_err:
                        pass

                    # Deletar registros que serão atualizados (merge seguro)
                    conn_local.execute(f"""
                        DELETE FROM {table} 
                        WHERE numero_os IN (SELECT DISTINCT numero_os FROM {stg})
                    """)
                    # Inserir novos/atualizados
                    conn_local.execute(f"INSERT INTO {table} SELECT * FROM {stg}")
                    count = conn_local.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                except Exception as e:
                    # Tabela pode não existir — cria. Ou schema ainda incompatível — DROP+CREATE
                    try:
                        conn_local.execute(f"DROP TABLE IF EXISTS {table}")
                        conn_local.execute(f"CREATE TABLE {table} AS SELECT * FROM {stg}")
                        count = conn_local.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    except Exception as e2:
                        pass
            
            # Cleanup: remover dados fora da janela de {days} dias
            for table in ['ri_corretiva_detalhamento', 'ri_preventiva_detalhamento',
                          'logs_corretiva', 'logs_regulacao_preventiva']:
                try:
                    conn_local.execute(f"""
                        DELETE FROM {table}
                        WHERE data_transacao < current_date - INTERVAL '{days} days'
                    """)
                    count_after = conn_local.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                except Exception as e:
                    pass
            
            # Header preventiva: recria (é derivada)
            conn_local.execute("DROP TABLE IF EXISTS logs_regulacao_preventiva_header")
            conn_local.execute("""
                CREATE TABLE logs_regulacao_preventiva_header AS 
                SELECT 
                    numero_os as cod_chamado_manutencao,
                    data_transacao as data_cadastro,
                    NULL as valor_limite_chamado_mult,
                    NULL as valor_limite_chamado_conc,
                    tipo_manutencao as plano_manutencao
                FROM logs_regulacao_preventiva
            """)
        else:
            # FULL LOAD: Drop + Create (primeiro sync)
            
            conn_local.execute("DROP TABLE IF EXISTS ri_corretiva_detalhamento")
            conn_local.execute("CREATE TABLE ri_corretiva_detalhamento AS SELECT * FROM stg_corretiva")
            
            conn_local.execute("DROP TABLE IF EXISTS ri_preventiva_detalhamento")
            conn_local.execute("CREATE TABLE ri_preventiva_detalhamento AS SELECT * FROM stg_preventiva")
            
            conn_local.execute("CREATE OR REPLACE TABLE logs_corretiva AS SELECT * FROM stg_corretiva")
            conn_local.execute("CREATE OR REPLACE TABLE logs_regulacao_preventiva AS SELECT * FROM stg_preventiva")
            
            conn_local.execute("DROP TABLE IF EXISTS logs_regulacao_preventiva_header")
            conn_local.execute("""
                CREATE TABLE logs_regulacao_preventiva_header AS 
                SELECT 
                    numero_os as cod_chamado_manutencao,
                    data_transacao as data_cadastro,
                    NULL as valor_limite_chamado_mult,
                    NULL as valor_limite_chamado_conc,
                    tipo_manutencao as plano_manutencao
                FROM stg_preventiva
            """)
        
        # Atualizar metadata
        new_max = df['data_transacao'].max()
        watermark_final = str(new_max) if pd.notna(new_max) else str(today)
        conn_local.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                last_sync TIMESTAMP, 
                status VARCHAR, 
                sync_type VARCHAR,
                records INTEGER,
                watermark VARCHAR
            );
            DELETE FROM sync_metadata;
        """)
        conn_local.execute("""
            INSERT INTO sync_metadata VALUES (current_timestamp, 'SUCCESS', ?, ?, ?)
        """, [sync_type, len(df), watermark_final])
        
        conn_local.close()
        _update_step("save_db", "done", f"6 tabelas ({sync_type})")
        
        # STEP 6: Pricing
        _update_step("pricing", "running", "Gerando medianas e economia...")
        try:
            run_full_pricing_pipeline()
            _update_step("pricing", "done", "Pipeline de pricing concluido")
        except Exception as e:
            _update_step("pricing", "done", f"Falhou: {str(e)[:40]}")
            print(f"[SYNC][WARN] Pricing falhou: {e}")

        # STEP 7: Cache
        _update_step("cache", "running", "Invalidando cache...")
        try:
            clear_cache()
            _update_step("cache", "done", "Cache atualizado")
        except Exception as e:
            _update_step("cache", "done", f"Falhou: {str(e)[:40]}")
            print(f"[SYNC][WARN] Cache falhou: {e}")

        elapsed = time.time() - start_total
        results['success'] = True
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
    finally:
        try:
            from database import set_maintenance_mode
            set_maintenance_mode(False)
        except Exception:
            pass
        
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Databricks Sync — Híbrido Inteligente")
    parser.add_argument("--days", type=int, default=150, help="Janela de dias (default 150)")
    args = parser.parse_args()
    sync_all_data(days=args.days)

