# -*- coding: utf-8 -*-
"""
Repository Preventiva - Lógica de Fugas de Preventivas
"""

import warnings
import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize

# Suprimir warning repetitivo do pandas sobre SQLAlchemy (DuckDB funciona perfeitamente com pd.read_sql)
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*", category=UserWarning)

# ============================================================
# CRITÉRIO DE FUGA DE PREVENTIVA (Atualizado 2026-02-27)
# Metodologia alinhada com SAP BO
# ============================================================
# Uma OS CORRETIVA é "fuga" se contém peças/serviços típicos de
# manutenção preventiva. A detecção usa 2 critérios combinados:
#
# CRITÉRIO 1: Peça de revisão → regex na coluna descricao_peca
# CRITÉRIO 2: MO de substituição → match exato na coluna tipo_mo
# CRITÉRIO 3: Rev preventiva → match parcial no tipo_mo
#
# OS é fuga se (CRITÉRIO 1 AND CRITÉRIO 2) OR CRITÉRIO 3

# --- CRITÉRIO 1: Peças típicas de revisão preventiva ---
# Buscamos na coluna descricao_peca (NamePart do Databricks)
PECAS_FUGA = [
    'OLEO MOTOR',       # Variações: OLEO DE MOTOR, OLEO LUBRIFICANTE MOTOR
    'FILTRO DE OLEO',   # Variações: FILTRO OLEO, FILTRO DE ÓLEO
]
# Regex consolidado para peças (case-insensitive)
_PECA_FUGA_REGEX = r'(OLEO\s*(DE\s*)?MOTOR|FILTRO\s*(DE\s*)?OLEO)'

# --- CRITÉRIO 2: MO de substituição/fornecimento ---
TIPOS_MO_FUGA = [
    'SUBSTITUIR',
    'FORNECIMENTO DE PECAS',
    'FORNECIMENTO PECAS',
    'SUBSTITUIR SEM REVISAO DE CUBO',
    'SUBSTITUIR COM REVISAO DE CUBO',
]
_MO_FUGA_IN_LIST = "'" + "', '".join(TIPOS_MO_FUGA) + "'"

# --- CRITÉRIO 3: Tipo MO = Rev Preventiva (diretamente) ---
_MO_REV_PREVENTIVA_REGEX = r'REV(ISAO|ISÃO)?\s*PREVENTIVA'

# --- LISTA DE OPORTUNIDADES DE RI (uso futuro: toggle no Farol) ---
# NÃO é critério de fuga! São tipos de MDO para análise de oportunidades de RI.
TIPOS_MO_OPORTUNIDADE_RI = [
    'ALINHAMENTO DE SUSPENSAO',
    'BALANCEAMENTO DE RODA',
    'BALANCEAR',
    'CAMBER',
    'HONORARIO',
    'LAVAGEM A SECO COMPLETA',
    'LAVAGEM A SECO EXTERNA',
    'LAVAGEM A SECO INTERNA',
    'LAVAGEM COMPLETA',
    'LAVAGEM COMPLETA COM CERA',
    'LAVAGEM CONVENCIONAL',
    'LAVAGEM EXPRESSA',
    'LAVAGEM EXTERNA',
    'LAVAGEM INTERNA',
    'LUBRIFICACAO GERAL',
    'LUBRIFICAR',
    'POLIR',
    'RODIZIO DE PNEUS',
]

# Famílias de veículo que são equipamentos/implementos (não veículos convencionais)
# Usadas para separar fugas de veículos vs fugas de equipamentos
FAMILIAS_EQUIPAMENTO = [
    'Equipamento', 'Implemento', 'Maquina', 'Maquinas',
    'Empilhadeira', 'Equipamentos Pesados'
]

def _get_asset_type_filter(tipo_ativo="VEICULOS"):
    """
    Retorna cláusula SQL para filtrar por tipo de ativo.
    - VEICULOS: exclui famílias de equipamento
    - EQUIPAMENTOS: inclui apenas famílias de equipamento
    - TODOS: sem filtro
    """
    familias_escaped = "', '".join(FAMILIAS_EQUIPAMENTO)
    if tipo_ativo == "EQUIPAMENTOS":
        return f" AND COALESCE(familia_veiculo, '') IN ('{familias_escaped}')"
    elif tipo_ativo == "VEICULOS":
        return f" AND COALESCE(familia_veiculo, '') NOT IN ('{familias_escaped}')"
    return ""  # TODOS

def _apply_fuga_logic(query_base):
    """
    Injeta a lógica de filtro por Fuga de Preventiva na query SQL.
    Metodologia SAP BO: (peça de revisão + MO substituição) OU rev preventiva.
    """
    where_clause = _get_fuga_conditions()
    return f"SELECT * FROM ({query_base}) WHERE ({where_clause})"

def _get_fuga_conditions():
    """
    Helper: Retorna a condição SQL para detecção de fugas.
    
    Lógica: (peça de revisão AND MO de substituição) OR tipo_mo = rev preventiva
    - Peça: descricao_peca contém OLEO MOTOR ou FILTRO DE OLEO
    - MO: tipo_mo IN (SUBSTITUIR, FORNECIMENTO DE PECAS, etc.)
    - OU: tipo_mo contém REV PREVENTIVA
    """
    peca_cond = f"regexp_matches(UPPER(COALESCE(descricao_peca, '')), '{_PECA_FUGA_REGEX}', 'i')"
    mo_cond = f"UPPER(COALESCE(tipo_mo, '')) IN ({_MO_FUGA_IN_LIST})"
    rev_prev_cond = f"regexp_matches(UPPER(COALESCE(tipo_mo, '')), '{_MO_REV_PREVENTIVA_REGEX}', 'i')"
    return f"(({peca_cond} AND {mo_cond}) OR {rev_prev_cond})"

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
def get_fugas_grouped_with_detail(filters=None, limit=20, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Retorna fugas agrupadas por codigo_tgm COM dados de detalhe embutidos.
    Otimizado: single CTE query em vez de 2 full-scans separados.
    Cada row inclui campo 'detailData' com lista de clientes individuais (max 10 por TGM).
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    """
    conn = get_connection()
    
    has_tgm = _has_column(conn, 'ri_corretiva_detalhamento', 'codigo_tgm')
    group_col = 'codigo_tgm' if has_tgm else 'codigo_cliente'
    
    fuga_cond = _get_fuga_conditions()
    asset_filter = _get_asset_type_filter(tipo_ativo)
    
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
    
    # Date range: default últimos 30 dias
    if not date_start or not date_end:
        from datetime import date as _date, timedelta as _td
        date_end = _date.today().isoformat()
        date_start = (_date.today() - _td(days=30)).isoformat()
    
    query_master = f"""
    SELECT 
        {group_col} as codigo_tgm,
        MIN(nome_cliente) as cliente_principal,
        COUNT(DISTINCT codigo_cliente) as qtd_clientes,
        COUNT(DISTINCT numero_os) as total_os,
        SUM(COALESCE(valor_total, 0)) as valor_total
    FROM ri_corretiva_detalhamento
    WHERE ({fuga_cond})
      AND CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}'
      {asset_filter}
      {filter_sql}
    GROUP BY {group_col} 
    ORDER BY valor_total DESC 
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
                MAX(codigo_cliente) as codigo_cliente,
                MAX(coalesce(nome_cliente, 'Cliente N/A')) as cliente,
                numero_os,
                MAX(nome_estabelecimento) as nome_ec,
                MAX(tipo_mo) as tipo_mo,
                MAX(descricao_peca) as descricao_peca,
                MAX(nome_aprovador) as nome_aprovador,
                MAX(data_transacao) as data_transacao,
                COUNT(*) as qtd_itens,
                SUM(COALESCE(valor_total, 0)) as valor_total_os,
                SUM(COALESCE(valor_mo, 0)) as valor_mo_os,
                SUM(COALESCE(valor_peca, 0)) as valor_peca_os,
                ROW_NUMBER() OVER (PARTITION BY {group_col} ORDER BY SUM(COALESCE(valor_total, 0)) DESC) as rn
            FROM ri_corretiva_detalhamento
            WHERE {group_col} IN ({tgm_escaped})
              AND ({fuga_cond})
              AND CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}'
              {asset_filter}
              {filter_sql}
            GROUP BY {group_col}, numero_os
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
def get_fugas_stats(filters=None, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Calcula KPIs: Total de OSs analisadas, Qtde Fugas, % Fuga
    Conta por OS distinta. Default: últimos 30 dias.
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    """
    conn = get_connection()
    
    # Date range: default últimos 30 dias
    date_filter = ""
    if date_start and date_end:
        date_filter = f"AND CAST(data_transacao AS DATE) BETWEEN '{date_start}' AND '{date_end}'"
    else:
        date_filter = "AND data_transacao >= CURRENT_DATE - INTERVAL 30 DAY"
    
    fuga_conditions = _get_fuga_conditions()
    asset_filter = _get_asset_type_filter(tipo_ativo)
    
    query = f"""
    SELECT 
        COUNT(DISTINCT numero_os) as total_os,
        COUNT(DISTINCT CASE WHEN {fuga_conditions} THEN numero_os END) as qtd_fugas
    FROM ri_corretiva_detalhamento
    WHERE data_transacao IS NOT NULL
      {date_filter}
      {asset_filter}
    """
    
    params = []
    if filters:
        if filters.get('clientes'):
            clients_escaped = "', '".join([str(c).replace("'", "''") for c in filters['clientes'] if c])
            query += f" AND nome_cliente IN ('{clients_escaped}')"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                try:
                    y, m = p.split('-')
                    period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
                except:
                    pass
            if period_clauses:
                query += f" AND ({' OR '.join(period_clauses)})"
        if filters.get('date_range'):
            start, end = filters['date_range']
            query += " AND data_transacao BETWEEN ? AND ?"
            params.extend([start, end])
        if filters.get('uf'):
            query += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
            params.extend(filters['uf'])

    try:
        result = conn.execute(query, params).fetchone()
        total = result[0] or 0
        fugas = result[1] or 0
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
def get_fugas_chart_data(filters=None, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Retorna % Fugas agrupado por Ano/Mes para o gráfico.
    Conta por OS distinta (não por item).
    Default: últimos 30 dias se sem date range.
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    """
    conn = get_connection()
    or_condition = _get_fuga_conditions()
    asset_filter = _get_asset_type_filter(tipo_ativo)

    # Date range: default últimos 30 dias
    date_filter = ""
    if date_start and date_end:
        date_filter = f"AND CAST(data_transacao AS DATE) BETWEEN '{date_start}' AND '{date_end}'"
    else:
        date_filter = "AND data_transacao >= CURRENT_DATE - INTERVAL 30 DAY"

    query = f"""
    SELECT 
        strftime(data_transacao, '%Y-%m') as mes_ano,
        COUNT(DISTINCT numero_os) as total_mensal,
        COUNT(DISTINCT CASE WHEN {or_condition} THEN numero_os END) as fugas_mensal
    FROM ri_corretiva_detalhamento
    WHERE data_transacao IS NOT NULL
      {date_filter}
      {asset_filter}
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

    query += " GROUP BY 1 ORDER BY 1"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        df['pct_fuga'] = (df['fugas_mensal'] / df['total_mensal'] * 100).fillna(0).round(2)
        return df.to_dict('list')
    except Exception as e:
        print(f"Erro no get_fugas_chart_data: {e}")
        return {}

def get_top_offenders(filters=None, entity='estabelecimento', limit=5, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Retorna top X entidades com maior volume/percentual de fugas.
    Entity pode ser: 'nome_estabelecimento', 'nome_aprovador', 'nome_primeira_alcada'
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
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
    asset_filter = _get_asset_type_filter(tipo_ativo)

    # Date range: default últimos 30 dias
    if not date_start or not date_end:
        from datetime import date as _date, timedelta as _td
        date_end = _date.today().isoformat()
        date_start = (_date.today() - _td(days=30)).isoformat()
    
    query = f"""
    SELECT 
        COALESCE(NULLIF({col}, ''), 'Não Informado') as entidade,
        COUNT(DISTINCT numero_os) as total_os,
        COUNT(DISTINCT CASE WHEN {or_condition} THEN numero_os END) as qtd_fugas
    FROM ri_corretiva_detalhamento
    WHERE CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}'
      {asset_filter}
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
