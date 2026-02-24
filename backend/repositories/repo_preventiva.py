# -*- coding: utf-8 -*-
"""
Repository Preventiva - Lógica de Fugas de Preventivas
"""

import warnings
import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize

# Suprimir warning repetitivo do pandas sobre SQLAlchemy (DuckDB funciona perfeitamente com pd.read_sql)
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*", category=UserWarning)

# Lista de termos que indicam que uma manutenção DEVERIA ser preventiva
# Se aparecerem nas colunas de tipo da tabela CORRETIVA, consideramos "Fuga"
TERMOS_PREVENTIVA = [
    'REVISAO', 'REVISÃO', 
    'PREVENTIVA', 'PREVENTIVO',
    'CHECK-UP', 'CHECK UP',
    'LUBRIFICACAO', 'LUBRIFICAÇÃO',
    'INSPECAO', 'INSPEÇÃO',
    'LAVAGEM', 'CALIBRAGEM', 'ALINHAR', 'BALANCEAR',
    # Termos adicionados para dados de mapadeparadas
    'PS -', 'PLANO', 'PERIÓDIC', 'PERIODIC'
]

# Colunas onde buscar os termos de fuga (adaptado para fact_maintenanceitem)
# NOTA: descricao_servico contém ID (não texto), então não é útil para busca textual
COLUNAS_BUSCA_FUGA = [
    'tipo_mo',                    # Campo original (pode ter 'N/A')
    'tipo_manutencao_oficina',    # Indica a fonte
    'plano_manutencao'            # Nome do plano de manutenção (pode ser NULL)
]

def _apply_fuga_logic(query_base):
    """
    Injeta a lógica de filtro por Fuga de Preventiva na query SQL.
    Filtra registros onde tipo_mo = 'PREVENTIVA' (dados já classificados pelo Databricks).
    """
    where_clause = _get_fuga_conditions()
    return f"SELECT * FROM ({query_base}) WHERE ({where_clause})"

# Regex compilado a partir de TERMOS_PREVENTIVA — usado por _get_fuga_conditions()
# DuckDB regexp_matches é ~10x mais rápido que 14 LIKE separados com UPPER+COALESCE
_FUGA_REGEX = '(' + '|'.join(TERMOS_PREVENTIVA) + ')'

def _get_fuga_conditions():
    """
    Helper: Retorna a condição para detecção de fugas.
    Usa regexp_matches do DuckDB (case-insensitive) — single pass em vez de 14 LIKE.
    """
    return f"regexp_matches(COALESCE(tipo_mo, ''), '{_FUGA_REGEX}', 'i')"

@safe_memoize(timeout=600)
def get_fugas_data(filters=None, limit=100):
    """
    Retorna a lista detalhada de Fugas de Preventiva.
    """
    conn = get_connection()
    
    # Query Base - Trazendo colunas relevantes da tabela detalhada
    query = f"""
    SELECT 
        nome_estabelecimento as nome_ec,
        codigo_estabelecimento as codigo_ec,
        cidade,
        uf,
        numero_os,
        descricao_peca as codigo_item,
        coalesce(nome_cliente, 'Cliente N/A') as cliente,
        codigo_cliente,
        nome_aprovador,
        tipo_mo,
        tipo_manutencao_oficina,
        valor_aprovado,
        data_transacao
    FROM ri_corretiva_detalhamento
    WHERE 1=1
    """
    
    # Aplica filtros globais (Cliente, Data, UF, etc) - Implementação simplificada
    params = []
    if filters:
        if filters.get('clientes'):
            # CORRIGIDO: usar nome_cliente ao invés de codigo_cliente (alinhado com outros repos)
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
            
        if filters.get('periodos'):
            # Converte lista ['2024-01', '2024-02'] em cláusula SQL
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"

        if filters.get('uf'):
             query += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
             params.extend(filters['uf'])

    # Aplica lógica de Fuga (Só queremos as que deram match)
    final_query = _apply_fuga_logic(query)
    
    # Ordenação e Limite
    final_query += " ORDER BY data_transacao DESC LIMIT ?"
    params.append(limit)
    
    try:
        df = pd.read_sql(final_query, conn, params=params)
        # Fix Datetime Serialization for Dash
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        return df.to_dict('records')
    except Exception as e:
        print(f"Erro no get_fugas_data: {e}")
        return []

def _has_column(conn, table, column):
    """Verifica se uma coluna existe numa tabela do DuckDB."""
    try:
        result = conn.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'"
        ).fetchone()
        return result is not None
    except:
        return False


@safe_memoize(timeout=600)
def get_fugas_grouped(filters=None, limit=200):
    """
    Retorna fugas agrupadas por codigo_tgm (SourceNumber).
    Fallback: se codigo_tgm não existir no DB, agrupa por codigo_cliente.
    """
    conn = get_connection()
    
    # Detectar qual coluna usar para agrupamento
    has_tgm = _has_column(conn, 'ri_corretiva_detalhamento', 'codigo_tgm')
    group_col = 'codigo_tgm' if has_tgm else 'codigo_cliente'
    
    or_condition = _get_fuga_conditions()
    
    query = f"""
    SELECT 
        {group_col} as codigo_tgm,
        MIN(nome_cliente) as cliente_principal,
        COUNT(DISTINCT codigo_cliente) as qtd_clientes,
        COUNT(*) as total_os,
        SUM(valor_aprovado) as valor_total,
        COUNT(DISTINCT numero_os) as total_os_distintas
    FROM ri_corretiva_detalhamento
    WHERE ({or_condition})
    """
    
    params = []
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"
        if filters.get('uf'):
            query += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
            params.extend(filters['uf'])
    
    query += f" GROUP BY {group_col} ORDER BY total_os DESC LIMIT {limit}"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        df['valor_total'] = df['valor_total'].fillna(0).round(2)
        if not has_tgm:
            print("[WARN] get_fugas_grouped: coluna 'codigo_tgm' não encontrada, usando 'codigo_cliente' como fallback. Faça um FULL LOAD.")
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro no get_fugas_grouped: {e}")
        return []


@safe_memoize(timeout=600)
def get_fugas_grouped_with_detail(filters=None, limit=20):
    """
    Retorna fugas agrupadas por codigo_tgm COM dados de detalhe embutidos.
    Otimizado: single CTE query em vez de 2 full-scans separados.
    Cada row inclui campo 'detailData' com lista de clientes individuais (max 10 por TGM).
    """
    conn = get_connection()
    
    has_tgm = _has_column(conn, 'ri_corretiva_detalhamento', 'codigo_tgm')
    group_col = 'codigo_tgm' if has_tgm else 'codigo_cliente'
    
    fuga_cond = _get_fuga_conditions()
    
    # Build filter SQL
    params = []
    filter_sql = ""
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            filter_sql += f" AND nome_cliente IN ('{clients_escaped}')"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            if period_clauses:
                filter_sql += f" AND ({' OR '.join(period_clauses)})"
        if filters.get('uf'):
            filter_sql += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
            params.extend(filters['uf'])
    
    # STEP 1: Master query (agregação) — single scan
    query_master = f"""
    SELECT 
        {group_col} as codigo_tgm,
        MIN(nome_cliente) as cliente_principal,
        COUNT(DISTINCT codigo_cliente) as qtd_clientes,
        COUNT(*) as total_os,
        SUM(valor_aprovado) as valor_total
    FROM ri_corretiva_detalhamento
    WHERE ({fuga_cond}) {filter_sql}
    GROUP BY {group_col} 
    ORDER BY total_os DESC 
    LIMIT {limit}
    """
    
    try:
        import time as _time
        _t0 = _time.time()
        
        df_master = pd.read_sql(query_master, conn, params=params)
        df_master['valor_total'] = df_master['valor_total'].fillna(0).round(2)
        pass  # master query done
        
        tgm_codes = df_master['codigo_tgm'].tolist()
        if not tgm_codes:
            return []
        
        # STEP 2: Detail query — APENAS para TGMs do master, max 10 per TGM
        tgm_escaped = ",".join([f"'{str(c).replace(chr(39), chr(39)+chr(39))}'" for c in tgm_codes])
        
        query_detail = f"""
        SELECT * FROM (
            SELECT 
                {group_col} as _tgm_key,
                codigo_cliente,
                coalesce(nome_cliente, 'Cliente N/A') as cliente,
                numero_os,
                nome_estabelecimento as nome_ec,
                cidade, uf, tipo_mo, valor_aprovado, nome_aprovador,
                data_transacao,
                ROW_NUMBER() OVER (PARTITION BY {group_col} ORDER BY data_transacao DESC) as rn
            FROM ri_corretiva_detalhamento
            WHERE {group_col} IN ({tgm_escaped})
              AND ({fuga_cond}) {filter_sql}
        ) sub WHERE rn <= 10
        """
        
        _t1 = _time.time()
        df_detail = pd.read_sql(query_detail, conn, params=params)
        pass  # detail query done
        
        # Formatar datas
        for col in df_detail.columns:
            if pd.api.types.is_datetime64_any_dtype(df_detail[col]):
                df_detail[col] = df_detail[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Agrupar detalhes por TGM key
        detail_by_tgm = {}
        for tgm_code in tgm_codes:
            mask = df_detail['_tgm_key'] == tgm_code
            details = df_detail[mask].drop(columns=['_tgm_key', 'rn']).to_dict('records')
            detail_by_tgm[tgm_code] = details
        
        # Montar resultado final
        records = df_master.to_dict('records')
        for row in records:
            row['detailData'] = detail_by_tgm.get(row['codigo_tgm'], [])
        
        pass  # total done
        return records
    except Exception as e:
        print(f"Erro no get_fugas_grouped_with_detail: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_fugas_detail_by_tgm(codigo_tgm, filters=None, limit=500):
    """
    Retorna detalhes granulares para um SourceNumber (ou codigo_cliente) específico.
    Resiliente: funciona mesmo antes do re-sync.
    """
    conn = get_connection()
    
    # Detectar qual coluna usar para filtro
    has_tgm = _has_column(conn, 'ri_corretiva_detalhamento', 'codigo_tgm')
    filter_col = 'codigo_tgm' if has_tgm else 'codigo_cliente'
    
    or_condition = _get_fuga_conditions()
    
    query = f"""
    SELECT 
        codigo_cliente,
        coalesce(nome_cliente, 'Cliente N/A') as cliente,
        numero_os,
        descricao_peca as codigo_item,
        nome_estabelecimento as nome_ec,
        cidade,
        uf,
        tipo_mo,
        valor_aprovado,
        nome_aprovador,
        data_transacao
    FROM ri_corretiva_detalhamento
    WHERE {filter_col} = ?
      AND ({or_condition})
    """
    
    params = [str(codigo_tgm)]
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"
    
    query += f" ORDER BY data_transacao DESC LIMIT {limit}"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro no get_fugas_detail_by_tgm: {e}")
        return []

@safe_memoize(timeout=600)
def get_fugas_stats(filters=None):
    """
    Calcula KPIs: Total de OSs analisadas, Qtde Fugas, % Fuga
    """
    conn = get_connection()
    
    # 1. Query Total (Universo de análise - Corretivas)
    query_total = f"SELECT COUNT(*) as total_os FROM ri_corretiva_detalhamento WHERE 1=1"
    
    # 2. Query Fugas (Subconjunto)
    query_fugas = f"""
    SELECT COUNT(*) as qtd_fugas 
    FROM ri_corretiva_detalhamento 
    WHERE 1=1 AND (
    """
    
    # Monta OR clause para os termos (usando função helper)
    fuga_conditions = _get_fuga_conditions()
    query_fugas += fuga_conditions + ")"
    
    
    params = []
    # Replicar filtros para ambas as queries
    if filters:
        filter_sql = ""
        # Filtro de clientes (usa nome_cliente como os outros repos)
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            filter_sql += f" AND nome_cliente IN ('{clients_escaped}')"
        
        # Filtro de períodos (formato: ['2026-01', '2026-02'])
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                try:
                    y, m = p.split('-')
                    period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
                except:
                    pass
            if period_clauses:
                filter_sql += f" AND ({' OR '.join(period_clauses)})"
        
        # Filtro date_range (fallback para compatibilidade)
        if filters.get('date_range'):
            start, end = filters['date_range']
            filter_sql += " AND data_transacao BETWEEN ? AND ?"
            params.extend([start, end])
        
        # Filtro de UF
        if filters.get('uf'):
            filter_sql += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
            params.extend(filters['uf'])
             
        query_total += filter_sql
        query_fugas += filter_sql

    try:
        # Params duplicados pois rodamos 2 queries com mesmos filtros
        total = conn.execute(query_total, params).fetchone()[0]
        fugas = conn.execute(query_fugas, params).fetchone()[0]
        
        pct_fuga = (fugas / total * 100) if total > 0 else 0
        
        return {
            "total_os": total,
            "qtd_fugas": fugas,
            "pct_fuga": round(pct_fuga, 2)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Erro CRÍTICO no get_fugas_stats: {e}")
        return {"total_os": 0, "qtd_fugas": 0, "pct_fuga": 0, "error": str(e)}

@safe_memoize(timeout=600)
def get_fugas_chart_data(filters=None):
    """
    Retorna % Fugas agrupado por Ano/Mes para o gráfico.
    """
    conn = get_connection()
    
    # Precisamos agrupar por mes e calcular (fugas/total)
    # DuckDB facilita isso
    
    # Usa função helper para condições de fuga
    or_condition = _get_fuga_conditions()

    query = f"""
    SELECT 
        strftime(data_transacao, '%Y-%m') as mes_ano,
        COUNT(*) as total_mensal,
        SUM(CASE WHEN {or_condition} THEN 1 ELSE 0 END) as fugas_mensal
    FROM ri_corretiva_detalhamento
    WHERE 1=1
    """
    
    params = []
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
            # params.extend(filters['clientes']) # REMOVIDO: Injetado na query
        if filters.get('periodos'):
            # Converte lista ['2024-01', '2024-02'] em cláusula SQL
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"
        if filters.get('uf'):
             query += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
             params.extend(filters['uf'])

    query += " GROUP BY 1 ORDER BY 1"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        
        # Calcular % no pandas
        df['pct_fuga'] = (df['fugas_mensal'] / df['total_mensal'] * 100).fillna(0).round(2)
        
        return df.to_dict('list') # {mes_ano: [...], pct_fuga: [...]}
    except Exception as e:
        print(f"Erro no get_fugas_chart_data: {e}")
        return {}

def get_top_offenders(filters=None, entity='estabelecimento', limit=5):
    """
    Retorna top X entidades com maior volume/percentual de fugas.
    Entity pode ser: 'nome_estabelecimento', 'nome_aprovador', 'nome_primeira_alcada'
    """
    conn = get_connection()
    
    col_map = {
        'estabelecimento': 'nome_estabelecimento',
        'aprovador': 'nome_aprovador',
        'alcada': 'nome_primeira_alcada'
    }
    col = col_map.get(entity, 'nome_estabelecimento')

    # Usa função helper para condições de fuga
    or_condition = _get_fuga_conditions()

    query = f"""
    SELECT 
        {col} as entidade,
        COUNT(*) as total_os,
        SUM(CASE WHEN {or_condition} THEN 1 ELSE 0 END) as qtd_fugas
    FROM ri_corretiva_detalhamento
    WHERE 1=1
    """
    # Filtros (repetir lógica padrão - idealmente extrair para helper)
    params = []
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
            # params.extend(filters['clientes']) # REMOVIDO: Injetado na query
        if filters.get('periodos'):
            # Converte lista ['2024-01', '2024-02'] em cláusula SQL
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"
    
    query += f" GROUP BY 1 HAVING qtd_fugas > 0 ORDER BY qtd_fugas DESC LIMIT {limit}"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        df['pct_fuga'] = (df['qtd_fugas'] / df['total_os'] * 100).fillna(0).round(1)
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro top offenders: {e}")
        return []
