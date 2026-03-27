from database import get_connection
import pandas as pd
from backend.cache_config import safe_memoize
from backend.repositories.repo_base import MONTH_MAP

@safe_memoize(timeout=300)  # Cache for 5 minutes
def get_ri_evolution_data(filters: dict = None):
    """
    Fetches the evolution of Regulation Intelligence (RI) % over time.
    Aggregated by Year, Quarter, Month using a Continuous Calendar Spine.
    
    Args:
        filters: Optional dict with filter parameters:
            - periodos: list of 'YYYY-MM' strings
            - clientes: list of client names
            - tipo_manutencao: 'TODAS', 'CORRETIVA', or 'PREVENTIVA'
    
    Returns a Pandas DataFrame.
    """
    conn = get_connection()
    
    if conn is None:
        print("[REPOSITORY ERROR] Sem conexão com banco de dados")
        return pd.DataFrame()
    
    try:
        # Build dynamic WHERE clauses based on filters
        where_conditions_corr = ["c.data_transacao IS NOT NULL"]
        where_conditions_prev = ["data_cadastro IS NOT NULL"]
        
        if filters:
            # Filter by period (month)
            if filters.get("periodos"):
                period_clauses = []
                for p in filters["periodos"]:
                    try:
                        year, month = p.split("-")
                        period_clauses.append(f"(year(c.data_transacao) = {year} AND month(c.data_transacao) = {month})")
                    except Exception:
                        pass
                if period_clauses:
                    where_conditions_corr.append(f"({' OR '.join(period_clauses)})")
                    
                # Also apply to preventiva
                period_clauses_prev = []
                for p in filters["periodos"]:
                    try:
                        year, month = p.split("-")
                        period_clauses_prev.append(f"(year(data_cadastro) = {year} AND month(data_cadastro) = {month})")
                    except Exception:
                        pass
                if period_clauses_prev:
                    where_conditions_prev.append(f"({' OR '.join(period_clauses_prev)})")
            
            # Filter by client
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_conditions_corr.append(f"c.nome_cliente IN ('{clients_escaped}')")
        
        where_corr = " AND ".join(where_conditions_corr)
        where_prev = " AND ".join(where_conditions_prev)
        
        # Check tipo_manutencao filter
        tipo = filters.get("tipo_manutencao", "TODAS") if filters else "TODAS"
        
        print(f"[REPOSITORY] Fetching data with filters: {filters}")

        # QUERY CORRETA: RI = % de OSs que podem ser aprovadas automaticamente
        # Baseado no match entre tipo_mo e ref_aprovacao_automatica
        query = f"""
        WITH range_dates AS (
            SELECT 
                MIN(data_transacao) as min_date,
                MAX(data_transacao) as max_date
            FROM ri_corretiva_detalhamento
            WHERE data_transacao IS NOT NULL
        ),
        calendar AS (
            SELECT unnest(generate_series(
                date_trunc('month', min_date), 
                date_trunc('month', max_date), 
                INTERVAL 1 MONTH
            )) as mes_ref
            FROM range_dates
            WHERE min_date IS NOT NULL
        ),
        
        -- Agregação de Preventiva (se houver dados)
        agg_prev AS (
            SELECT
                date_trunc('month', data_cadastro) as mes,
                COUNT(*) as total_prev,
                SUM(CASE 
                    WHEN valor_limite_chamado_mult > 0 
                         AND valor_limite_chamado_conc < valor_limite_chamado_mult 
                    THEN 1 ELSE 0 
                END) as automaticas_prev
            FROM logs_regulacao_preventiva_header
            WHERE {where_prev}
            GROUP BY 1
        ),
        
        -- Agregação de Corretiva: RI = tipos de serviço com aprovação automática
        agg_corr AS (
            SELECT
                date_trunc('month', c.data_transacao) as mes,
                COUNT(*) as total_corr,
                SUM(CASE WHEN ra.tipo_mo IS NOT NULL THEN 1 ELSE 0 END) as automaticas_corr
            FROM ri_corretiva_detalhamento c
            LEFT JOIN ref_aprovacao_automatica ra 
                ON UPPER(TRIM(c.tipo_mo)) = UPPER(TRIM(ra.tipo_mo))
            WHERE {where_corr}
            GROUP BY 1
        )
        
        SELECT
            year(c.mes_ref) as ano,
            quarter(c.mes_ref) as trimestre,
            month(c.mes_ref) as mes_num,
            
            -- Preventiva Metrics
            COALESCE(p.total_prev, 0) as qtd_prev,
            COALESCE(p.automaticas_prev, 0) as automaticas_prev,
            CASE 
                WHEN COALESCE(p.total_prev, 0) > 0 
                THEN COALESCE(p.automaticas_prev, 0)::DOUBLE / p.total_prev 
                ELSE 0 
            END as ri_preventiva,
            
            -- Corretiva Metrics
            COALESCE(cr.total_corr, 0) as qtd_corr,
            COALESCE(cr.automaticas_corr, 0) as automaticas_corr,
            CASE 
                WHEN COALESCE(cr.total_corr, 0) > 0 
                THEN COALESCE(cr.automaticas_corr, 0)::DOUBLE / cr.total_corr 
                ELSE 0 
            END as ri_corretiva
            
        FROM calendar c
        LEFT JOIN agg_prev p ON c.mes_ref = p.mes
        LEFT JOIN agg_corr cr ON c.mes_ref = cr.mes
        ORDER BY 1, 3
        """
        
        df = conn.execute(query).fetchdf()
        
        if df.empty:
            return df
        
        # Apply tipo_manutencao filter (zero out columns not requested)
        if tipo == "CORRETIVA":
            df['qtd_prev'] = 0
            df['automaticas_prev'] = 0
            df['ri_preventiva'] = 0
        elif tipo == "PREVENTIVA":
            df['qtd_corr'] = 0
            df['automaticas_corr'] = 0
            df['ri_corretiva'] = 0
            
        total_qtd = (df['qtd_prev'] + df['qtd_corr']).replace(0, 1)
        df['ri_geral'] = (
            (df['ri_preventiva'] * df['qtd_prev']) + 
            (df['ri_corretiva'] * df['qtd_corr'])
        ) / total_qtd
        
        # Translate months using map
        df['mes_nome'] = df['mes_num'].map(MONTH_MAP)
        
        # Add labels for Multi-level Axis
        df['trimestre_label'] = df['trimestre'].apply(lambda x: f"Qtr {x}")
        
        print(f"[REPOSITORY] Returned {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"[REPOSITORY ERROR] {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def refresh_pricing_data():
    """
    Atualiza as tabelas de referência (ref_mdo) após sync do Databricks.
    """
    import time
    conn = get_connection()
    
    if conn is None:
        return False
    
    try:
        start_time = time.time()
        print("[REPOSITORY] Atualizando tabelas de referência (Pricing Engine)...")
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_detalhamento_chave ON ri_corretiva_detalhamento (cod_item)")
        
        # DEBUG: Check source table state
        try:
            count_det = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
            print(f"[REPOSITORY DEBUG] ri_corretiva_detalhamento count: {count_det}")
            if count_det > 0:
                 print("[REPOSITORY DEBUG] Sample Detalhamento:")
                 print(conn.execute("SELECT nome_cliente, valor_aprovado FROM ri_corretiva_detalhamento LIMIT 5").fetchdf())
        except Exception as e:
            print(f"[REPOSITORY DEBUG] Failed to inspect detail table: {e}")

        conn.execute("""
        CREATE OR REPLACE TABLE ref_mdo AS
        SELECT
            UPPER(TRIM(peca)) as tipo_mdo_peca,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY valor_aprovado) as mediana_valor,
            COUNT(*) as qtd_registros
        FROM ri_corretiva_detalhamento
        WHERE valor_aprovado > 0 
          AND peca IS NOT NULL 
          AND peca != ''
        GROUP BY 1
        """)
        
        count = conn.execute("SELECT COUNT(*) FROM ref_mdo").fetchone()[0]
        elapsed = time.time() - start_time
        print(f"[REPOSITORY] ref_mdo atualizada com {count} tipos de MO em {elapsed:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"[REPOSITORY] Erro ao atualizar pricing: {e}")
        return False
