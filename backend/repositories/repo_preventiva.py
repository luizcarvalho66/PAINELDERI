# -*- coding: utf-8 -*-
"""
Repository Preventiva - Lógica de Fugas de Preventivas
"""

import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize

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

def _get_fuga_conditions():
    """
    Helper: Retorna a condição para detecção de fugas.
    Busca por termos de preventiva no campo tipo_mo usando LIKE.
    Isso captura valores como 'REV PREVENTIVA', 'REVISAO GERAL', etc.
    """
    # Constrói OR clause para todos os termos de TERMOS_PREVENTIVA
    or_clauses = []
    for termo in TERMOS_PREVENTIVA:
        or_clauses.append(f"UPPER(COALESCE(tipo_mo, '')) LIKE '%{termo}%'")
    
    return " OR ".join(or_clauses)

@safe_memoize
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

@safe_memoize
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

@safe_memoize
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
