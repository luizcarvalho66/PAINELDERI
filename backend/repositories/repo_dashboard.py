# -*- coding: utf-8 -*-
"""
Repository Dashboard - Queries para o Dashboard principal

Responsável por:
- Evolução temporal de RI (Regulação Inteligente)
- Atualização de dados de pricing

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
import numpy as np
from backend.repositories.repo_base import (
    get_connection, get_readonly_connection, safe_memoize, MONTH_MAP
)


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
    try:
        conn = get_readonly_connection()
    except Exception as e:
        print(f"[REPOSITORY CRITICAL] Falha ao obter conexão: {e}")
        return pd.DataFrame({
            'error_state': [True], 
            'message': ["Falha Crítica de Conexão"],
            'technical_details': [str(e)]
        })

    if conn is None:
        print("[REPOSITORY ERROR] Sem conexão com banco de dados")
        return pd.DataFrame({
            'error_state': [True], 
            'message': ["Banco de Dados Indisponível"],
            'technical_details': ["O arquivo do banco de dados não pôde ser aberto. Verifique se não há janelas de 'Salvar Como' ou outros processos bloqueando o arquivo."]
        })

    try:
        # Build dynamic WHERE clauses based on filters
        where_conditions_corr = ["c.data_transacao IS NOT NULL"]
        where_conditions_prev = ["data_transacao IS NOT NULL"]
        

        if filters:
            # Filter by period (month)
            if filters.get("periodos"):
                period_clauses = []
                for p in filters["periodos"]:
                    try:
                        year, month = p.split("-")
                        period_clauses.append(f"(year(c.data_transacao) = {year} AND month(c.data_transacao) = {month})")
                    except:
                        pass
                if period_clauses:
                    where_conditions_corr.append(f"({' OR '.join(period_clauses)})")
                    
                # Also apply to preventiva
                period_clauses_prev = []
                for p in filters["periodos"]:
                    try:
                        year, month = p.split("-")
                        period_clauses_prev.append(f"(year(data_cadastro) = {year} AND month(data_cadastro) = {month})")
                    except:
                        pass
                if period_clauses_prev:
                    where_conditions_prev.append(f"({' OR '.join(period_clauses_prev)})")
            
            # Filter by client - ROBUST SANITIZATION
            if filters.get("clientes"):
                # Remove None, empty strings, or "All" placeholders if any
                raw_clients = filters["clientes"]
                valid_clients = [str(c) for c in raw_clients if c and str(c).strip() != ""]
                
                if valid_clients:
                    clients_escaped = "', '".join([c.replace("'", "''") for c in valid_clients])
                    where_conditions_corr.append(f"c.nome_cliente IN ('{clients_escaped}')")

        
        where_corr = " AND ".join(where_conditions_corr)
        where_prev = " AND ".join(where_conditions_prev)
        
        # Check tipo_manutencao filter
        tipo = filters.get("tipo_manutencao", "TODAS") if filters else "TODAS"
        



        # SIMPLIFIED QUERY STRATEGY: Fetch grouped data and merge in Python
        # This avoids complex CTEs/Calendar behaviors that might fail silently
        
        # DEBUG: Check raw table count


        # 1. Fetch Corretiva Data - RI = (valor_total - valor_aprovado) / valor_total
        query_corr = f"""
        SELECT
            date_trunc('month', c.data_transacao) as mes_ref,
            COUNT(DISTINCT c.numero_os) as total_corr, -- CORRIDO: Ordens, não Itens
            SUM(COALESCE(valor_total, 0)) as sum_total_corr,
            SUM(COALESCE(valor_aprovado, 0)) as sum_aprovado_corr
        FROM ri_corretiva_detalhamento c
        WHERE {where_corr}
        GROUP BY 1
        ORDER BY 1
        """
        


        # 1.1 Fetch Pricing Data - CORRETIVA (Economia Real via Engine)
        query_pricing_corr = f"""
        SELECT
            date_trunc('month', c.data_transacao) as mes_ref,
            SUM(c.economia_total) as sum_economia_pricing
        FROM economia_calculada c
        WHERE {where_corr}
          AND c.tipo_origem = 'CORRETIVA'
        GROUP BY 1
        """
        
        # 1.2 Fetch Pricing Data - PREVENTIVA (Economia Real via Engine)
        query_pricing_prev = """
        SELECT
            date_trunc('month', c.data_transacao) as mes_ref,
            SUM(c.economia_total) as sum_economia_pricing_prev
        FROM economia_calculada c
        WHERE c.data_transacao IS NOT NULL
          AND c.tipo_origem = 'PREVENTIVA'
        GROUP BY 1
        """
        
        # 2. Fetch Preventiva Data - CORRIGIDO: usando ri_preventiva_detalhamento
        query_prev = f"""
        SELECT
            date_trunc('month', data_transacao) as mes_ref,
            COUNT(DISTINCT numero_os) as total_prev, -- CORRIGIDO: Ordens (assumindo numero_os existe)
            SUM(COALESCE(valor_total, 0)) as sum_total_prev,
            SUM(COALESCE(valor_aprovado, 0)) as sum_aprovado_prev
        FROM ri_preventiva_detalhamento
        WHERE data_transacao IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """
        
        df_corr = conn.execute(query_corr).fetchdf()
        try:
            df_pricing_corr = conn.execute(query_pricing_corr).fetchdf()
        except Exception as e:
            print(f"[REPOSITORY WARNING] Could not fetch corretiva pricing data: {e}")
            df_pricing_corr = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing'])
        
        try:
            df_pricing_prev = conn.execute(query_pricing_prev).fetchdf()
        except Exception as e:
            print(f"[REPOSITORY WARNING] Could not fetch preventiva pricing data: {e}")
            df_pricing_prev = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing_prev'])
        
        df_prev = conn.execute(query_prev).fetchdf()
        

        
        # 3. Merge in Pandas (Outer Join on Month)
        if df_corr.empty and df_prev.empty:
            return pd.DataFrame()
            
        # Ensure datetime type for merge (normalize to naive to avoid timezone mismatch)
        if not df_corr.empty:
            df_corr['mes_ref'] = pd.to_datetime(df_corr['mes_ref']).dt.tz_localize(None)
        else:
             df_corr = pd.DataFrame(columns=['mes_ref', 'total_corr', 'sum_total_corr', 'sum_aprovado_corr'])
             
        if not df_pricing_corr.empty:
            df_pricing_corr['mes_ref'] = pd.to_datetime(df_pricing_corr['mes_ref']).dt.tz_localize(None)
        else:
             df_pricing_corr = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing'])

        if not df_pricing_prev.empty:
            df_pricing_prev['mes_ref'] = pd.to_datetime(df_pricing_prev['mes_ref']).dt.tz_localize(None)
        else:
             df_pricing_prev = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing_prev'])

        if not df_prev.empty:
            df_prev['mes_ref'] = pd.to_datetime(df_prev['mes_ref']).dt.tz_localize(None)
        else:
            df_prev = pd.DataFrame(columns=['mes_ref', 'total_prev', 'sum_total_prev', 'sum_aprovado_prev'])
            
        # Merge Corr + Prev
        df = pd.merge(df_corr, df_prev, on='mes_ref', how='outer').fillna(0)
        # Merge Pricing Corretiva
        df = pd.merge(df, df_pricing_corr, on='mes_ref', how='left').fillna(0)
        # Merge Pricing Preventiva
        df = pd.merge(df, df_pricing_prev, on='mes_ref', how='left').fillna(0)
        
        # 4. Feature Engineering
        df['ano'] = df['mes_ref'].dt.year
        df['mes_num'] = df['mes_ref'].dt.month
        df['trimestre'] = df['mes_ref'].dt.quarter
        
        # Metrics Calculation - RI = (Solicitado - Aprovado) / Solicitado
        # IMPORTANTE: Usar max(0, ...) para evitar RI negativo (quando aprovado > solicitado)
        # Metrics Calculation 
        # RI Preventiva — via Pricing Engine (medianas)
        df['sum_economia_pricing_prev'] = df.get('sum_economia_pricing_prev', 0)
        denom_prev = df['sum_aprovado_prev'] + df['sum_economia_pricing_prev']
        df['ri_preventiva'] = np.where(
            denom_prev > 0,
            df['sum_economia_pricing_prev'] / denom_prev,
            0.0
        )
        
        # RI Corretiva — vetorizado com np.where
        denom_corr = df['sum_aprovado_corr'] + df['sum_economia_pricing']
        df['ri_corretiva'] = np.where(
            denom_corr > 0,
            df['sum_economia_pricing'] / denom_corr,
            0.0
        )
        
        # Sorting
        df = df.sort_values('mes_ref')
        
        # Renaming for compatibility
        df['qtd_prev'] = df['total_prev']
        df['qtd_corr'] = df['total_corr']


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
            
        # RI GERAL = Economia Total / Valor Total Solicitado (Corretiva + Preventiva)
        # Preventiva: Delta simples; Corretiva: Pricing Table
        
        economia_total_corr = df['sum_economia_pricing']
        economia_total_prev = df['sum_economia_pricing_prev']
        
        total_aprovado_real = df['sum_aprovado_corr'] + df['sum_aprovado_prev']
        
        # Base de cálculo: Aprovado + Economia (O que seria gasto sem gestão)
        base_calculo = total_aprovado_real + economia_total_corr + economia_total_prev
        
        df['ri_geral'] = ((economia_total_corr + economia_total_prev) / base_calculo.replace(0, 1)).clip(lower=0)
        
        # DEBUG LOGGING TO FILE

        
        # Translate months using map
        df['mes_nome'] = df['mes_num'].map(MONTH_MAP)
        
        # Add labels for Multi-level Axis
        df['trimestre_label'] = df['trimestre'].apply(lambda x: f"Qtr {x}")
        
        # x_label — usado pelas funções de chart como eixo X
        df['x_label'] = df['mes_nome'].str[:3] + ' ' + df['ano'].astype(str)
        
        return df
        
    except Exception as e:
        error_msg = str(e)
        print(f"[REPOSITORY ERROR] {error_msg}")
        
        # Check for Lock/IO Error specifically
        if "IO Error" in error_msg or "locked" in error_msg.lower():
            detailed_msg = "O banco de dados está bloqueado por outro processo. Isso geralmente ocorre quando duas instâncias do painel estão abertas."
        else:
            detailed_msg = f"Erro técnico: {error_msg}"
            
        # Return a special DataFrame that signals error to the frontend
        return pd.DataFrame({
            'error_state': [True], 
            'message': ["Não foi possível acessar os dados."],
            'technical_details': [detailed_msg]
        })


def refresh_pricing_data():
    """
    Atualiza as tabelas de referência (ref_mdo) após sync do Databricks.
    """
    import time
    conn = get_connection(read_only=False)
    
    if conn is None:
        return False
    
    try:
        start_time = time.time()
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_detalhamento_chave ON ri_corretiva_detalhamento (codigo_item)")
        
        # DEBUG: Check source table state


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
    finally:
        if conn:
            conn.close()


def check_database_status() -> bool:
    """
    Verifica se existem dados carregados na tabela principal.
    Utilizado para persistência do Dashboard entre sessões.
    """
    try:
        conn = get_connection()
        if conn is None:
            return False
            
        count = conn.execute("SELECT COUNT(*) FROM ri_corretiva_detalhamento").fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"[PERSISTENCE] Erro ao verificar status do banco: {e}")
        return False

@safe_memoize(timeout=300)
def get_ri_evolution_30d(filters: dict = None):
    """
    Fetches the evolution of RI over the last 30 days, grouped by week.
    Utilizado especificamente para o Slide 3 do Relatório PPT.
    """
    try:
        conn = get_readonly_connection()
    except Exception as e:
        return pd.DataFrame()

    if conn is None:
        return pd.DataFrame()

    try:
        # Usa current_date - 30 (DuckDB syntax)
        where_conditions_corr = ["c.data_transacao >= current_date() - INTERVAL '30' DAY"]
        where_conditions_prev = ["data_transacao >= current_date() - INTERVAL '30' DAY"]
        
        if filters and filters.get("clientes"):
            raw_clients = filters["clientes"]
            valid_clients = [str(c) for c in raw_clients if c and str(c).strip() != ""]
            if valid_clients:
                clients_escaped = "', '".join([c.replace("'", "''") for c in valid_clients])
                where_conditions_corr.append(f"c.nome_cliente IN ('{clients_escaped}')")

        where_corr = " AND ".join(where_conditions_corr)
        where_prev = " AND ".join(where_conditions_prev)
        
        query_corr = f"""
        SELECT
            date_trunc('week', c.data_transacao) as mes_ref,
            COUNT(DISTINCT c.numero_os) as total_corr,
            SUM(COALESCE(valor_total, 0)) as sum_total_corr,
            SUM(COALESCE(valor_aprovado, 0)) as sum_aprovado_corr
        FROM ri_corretiva_detalhamento c
        WHERE {where_corr}
        GROUP BY 1
        ORDER BY 1
        """
        
        query_pricing_corr = f"""
        SELECT
            date_trunc('week', c.data_transacao) as mes_ref,
            SUM(c.economia_total) as sum_economia_pricing
        FROM economia_calculada c
        WHERE {where_corr} AND c.tipo_origem = 'CORRETIVA'
        GROUP BY 1
        """
        
        query_pricing_prev = f"""
        SELECT
            date_trunc('week', c.data_transacao) as mes_ref,
            SUM(c.economia_total) as sum_economia_pricing_prev
        FROM economia_calculada c
        WHERE {where_prev} AND c.tipo_origem = 'PREVENTIVA'
        GROUP BY 1
        """
        
        query_prev = f"""
        SELECT
            date_trunc('week', data_transacao) as mes_ref,
            COUNT(DISTINCT numero_os) as total_prev,
            SUM(COALESCE(valor_total, 0)) as sum_total_prev,
            SUM(COALESCE(valor_aprovado, 0)) as sum_aprovado_prev
        FROM ri_preventiva_detalhamento
        WHERE {where_prev}
        GROUP BY 1
        ORDER BY 1
        """
        
        df_corr = conn.execute(query_corr).fetchdf()
        try: df_pricing_corr = conn.execute(query_pricing_corr).fetchdf()
        except: df_pricing_corr = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing'])
        
        try: df_pricing_prev = conn.execute(query_pricing_prev).fetchdf()
        except: df_pricing_prev = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing_prev'])
        
        df_prev = conn.execute(query_prev).fetchdf()
        
        if df_corr.empty and df_prev.empty:
            return pd.DataFrame()
            
        if not df_corr.empty: df_corr['mes_ref'] = pd.to_datetime(df_corr['mes_ref']).dt.tz_localize(None)
        else: df_corr = pd.DataFrame(columns=['mes_ref', 'total_corr', 'sum_total_corr', 'sum_aprovado_corr'])
             
        if not df_pricing_corr.empty: df_pricing_corr['mes_ref'] = pd.to_datetime(df_pricing_corr['mes_ref']).dt.tz_localize(None)
        else: df_pricing_corr = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing'])

        if not df_pricing_prev.empty: df_pricing_prev['mes_ref'] = pd.to_datetime(df_pricing_prev['mes_ref']).dt.tz_localize(None)
        else: df_pricing_prev = pd.DataFrame(columns=['mes_ref', 'sum_economia_pricing_prev'])

        if not df_prev.empty: df_prev['mes_ref'] = pd.to_datetime(df_prev['mes_ref']).dt.tz_localize(None)
        else: df_prev = pd.DataFrame(columns=['mes_ref', 'total_prev', 'sum_total_prev', 'sum_aprovado_prev'])
            
        df = pd.merge(df_corr, df_prev, on='mes_ref', how='outer').fillna(0)
        df = pd.merge(df, df_pricing_corr, on='mes_ref', how='left').fillna(0)
        df = pd.merge(df, df_pricing_prev, on='mes_ref', how='left').fillna(0)
        
        df['ano'] = df['mes_ref'].dt.year
        df['mes_num'] = df['mes_ref'].dt.month
        
        df['sum_economia_pricing_prev'] = df.get('sum_economia_pricing_prev', 0)
        denom_prev = df['sum_aprovado_prev'] + df['sum_economia_pricing_prev']
        df['ri_preventiva'] = np.where(denom_prev > 0, df['sum_economia_pricing_prev'] / denom_prev, 0.0)
        
        denom_corr = df['sum_aprovado_corr'] + df['sum_economia_pricing']
        df['ri_corretiva'] = np.where(denom_corr > 0, df['sum_economia_pricing'] / denom_corr, 0.0)
        
        df = df.sort_values('mes_ref')
        df['qtd_prev'] = df['total_prev']
        df['qtd_corr'] = df['total_corr']

        economia_total_corr = df['sum_economia_pricing']
        economia_total_prev = df['sum_economia_pricing_prev']
        total_aprovado_real = df['sum_aprovado_corr'] + df['sum_aprovado_prev']
        base_calculo = total_aprovado_real + economia_total_corr + economia_total_prev
        
        df['ri_geral'] = ((economia_total_corr + economia_total_prev) / base_calculo.replace(0, 1)).clip(lower=0)
        
        # Formatar a semana para o X axis em português (dia e mês)
        df['mes_nome'] = df['mes_num'].map(MONTH_MAP)
        df['x_label'] = df['mes_ref'].dt.strftime('%d/') + df['mes_ref'].dt.strftime('%m')
        
        return df
        
    except Exception as e:
        print(f"[REPOSITORY ERROR] get_ri_evolution_30d: {e}")
        return pd.DataFrame()


@safe_memoize(timeout=300)
def get_top_ofensores_30d(filters: dict = None, limite=3):
    """
    Busca os Top Estabelecimentos Ofensores em RI nos últimos 30 dias.
    Ofensor = Alto Volume de Orçamento (R$) com a MENOR % de RI.
    Lógica: RI = Economia / (Aprovado + Economia). Menor RI = pior negociação.
    """
    try:
        conn = get_readonly_connection()
    except:
        return []

    if conn is None: return []

    try:
        where_conditions = ["c.data_transacao >= current_date - INTERVAL 30 DAY"]
        if filters and filters.get("clientes"):
            valid_clients = [str(cl) for cl in filters["clientes"] if cl and str(cl).strip() != ""]
            if valid_clients:
                clients_escaped = "', '".join([cl.replace("'", "''") for cl in valid_clients])
                where_conditions.append(f"c.nome_cliente IN ('{clients_escaped}')")

        where_clause = " AND ".join(where_conditions)
        
        # 1) Agregar por nome_estabelecimento na corretiva
        # 2) Agregar economia via numero_os (chave compartilhada) e depois resumir por estabelecimento
        query = f"""
        WITH base_corr AS (
            SELECT 
                c.nome_estabelecimento,
                c.numero_os,
                SUM(c.valor_total) as valor_total_os,
                SUM(c.valor_aprovado) as valor_aprovado_os
            FROM ri_corretiva_detalhamento c
            WHERE {where_clause}
              AND c.nome_estabelecimento IS NOT NULL
              AND TRIM(c.nome_estabelecimento) != ''
            GROUP BY 1, 2
        ),
        econ_por_os AS (
            SELECT 
                e.numero_os,
                SUM(e.economia_total) as economia_os
            FROM economia_calculada e
            WHERE e.data_transacao >= current_date - INTERVAL 30 DAY
              AND e.tipo_origem = 'CORRETIVA'
            GROUP BY 1
        ),
        joined AS (
            SELECT
                b.nome_estabelecimento,
                b.numero_os,
                b.valor_total_os,
                b.valor_aprovado_os,
                COALESCE(e.economia_os, 0) as economia_os
            FROM base_corr b
            LEFT JOIN econ_por_os e ON b.numero_os = e.numero_os
        )
        SELECT
            nome_estabelecimento,
            SUM(valor_total_os) as volume_solicitado,
            SUM(valor_aprovado_os) as volume_aprovado,
            SUM(economia_os) as economia,
            COUNT(DISTINCT numero_os) as qtd_os
        FROM joined
        GROUP BY 1
        HAVING SUM(valor_total_os) > 5000
        ORDER BY volume_solicitado DESC
        LIMIT 20
        """
        
        df = conn.execute(query).fetchdf()
        if df.empty: return []
        
        # Calcular RI por estabelecimento: Economia / (Aprovado + Economia)
        denom = df['volume_aprovado'] + df['economia']
        df['ri_percent'] = np.where(denom > 0, df['economia'] / denom, 0.0)
        
        # Ordenar pelo Menor RI (pior negociação) com alto volume
        df = df.sort_values(by=['ri_percent', 'volume_solicitado'], ascending=[True, False]).head(limite)
        
        ofensores = []
        for _, row in df.iterrows():
            nome_raw = str(row['nome_estabelecimento']).strip()
            nome = nome_raw[:25] + "..." if len(nome_raw) > 25 else nome_raw
            ri = float(row['ri_percent']) * 100
            vol_solicitado = float(row['volume_solicitado'])
            vol_aprovado = float(row['volume_aprovado'])
            economia = float(row['economia'])
            ofensores.append({
                "nome": nome,
                "ri_percent": ri,
                "volume_solicitado": vol_solicitado,
                "volume_aprovado": vol_aprovado,
                "economia": economia,
                "qtd_os": int(row['qtd_os'])
            })
            
        return ofensores

    except Exception as e:
        print(f"[REPOSITORY ERROR] get_top_ofensores: {e}")
        import traceback
        traceback.print_exc()
        return []


@safe_memoize(timeout=600)
def get_distinct_clients():
    """
    Retorna lista de nomes de clientes distintos disponíveis no DuckDB.
    Usado para popular o dropdown de seleção de cliente no modal de exportação PPT.
    """
    try:
        conn = get_readonly_connection()
    except Exception:
        return []

    if conn is None:
        return []

    try:
        query = """
        SELECT DISTINCT nome_cliente
        FROM ri_corretiva_detalhamento
        WHERE nome_cliente IS NOT NULL
          AND TRIM(nome_cliente) != ''
        ORDER BY nome_cliente
        """
        df = conn.execute(query).fetchdf()
        return df['nome_cliente'].tolist()
    except Exception as e:
        print(f"[REPOSITORY ERROR] get_distinct_clients: {e}")
        return []
