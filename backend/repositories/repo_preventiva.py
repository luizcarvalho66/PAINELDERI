# -*- coding: utf-8 -*-
"""
Repository Preventiva - Lógica de Fugas de Preventivas
"""

import warnings
import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize, safe_sql_in_list

# Suprimir warning repetitivo do pandas sobre SQLAlchemy (DuckDB funciona perfeitamente com pd.read_sql)
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*", category=UserWarning)

# ============================================================
# CRITÉRIO DE FUGA DE PREVENTIVA (FIX 2026-03-25)
# STATUS: ✅ ALINHADO COM PBI — Lógica DAX extraída do relatório PBI
# ============================================================
# Fonte: Painel RI-contexto.Report → dMedidas.tmdl + fItens.tmdl
#
# Lógica PBI:
#   1. Item_Preventivo = COUNT de peças em lista fixa POR OS (PARTITION BY MaintenanceId)
#   2. OS com perfil preventivo = Item_Preventivo >= 2
#   3. Fuga = OS com perfil preventivo E IsPreventiveMaintenance = FALSE
#   4. % Fugas = Fugas / (OS com perfil preventivo)
#
# Lista de peças do PBI (PartName via dim_maintenanceparts → descricao_peca no DuckDB):
PECAS_PREVENTIVAS_PBI = [
    'Oleo Motor',
    'Oleo Motor Galao 20l',
    'Filtro De Oleo',
    'Oleo Motor Tonel 200l',
]
# SQL IN list para uso direto nas queries
_PECAS_PBI_IN_LIST = "'" + "', '".join(PECAS_PREVENTIVAS_PBI) + "'"

# Threshold: OS com >= N peças da lista = "perfil preventivo"
THRESHOLD_ITEM_PREVENTIVO = 2

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

def _build_fuga_os_subquery(extra_where=""):
    """
    Gera subquery que identifica OS de fuga de preventiva.
    
    Regra de negócio (FIX 2026-03-25v2 — REPLICANDO DAX EXATO DO PBI):
    Fonte: Painel RI-contexto.Report → dMedidas.tmdl + fItens.tmdl
    
    DAX do PBI:
      Fugas = CALCULATE([Total OS], fItens[Item_Preventivo]>=2)
            - CALCULATE([Total OS], fItens[IsPreventiveMaintenance]=True, fItens[Item_Preventivo]>=2)
    
    Item_Preventivo é calculado via COUNT(...) OVER (PARTITION BY MaintenanceId)
    sobre TODOS os itens (corr+prev juntos numa tabela flat fItens).
    
    Lógica replicada:
      1. UNION ALL itens de corretiva + preventiva (simula fItens flat)
      2. GROUP BY numero_os + HAVING >= 2 peças da lista
      3. Filtra APENAS OS que NÃO estão na preventiva (fuga = corretiva com perfil)
    
    Args:
        extra_where: cláusulas WHERE adicionais (filtros de data, cliente, etc.)
                     Colunas SEM prefixo (ex: data_transacao, nome_cliente).
    
    Retorna: subquery SQL (entre parênteses) que lista numero_os de fugas.
    """
    return f"""
    (
        -- FIX v2: UNION ALL antes do GROUP BY (replica fItens flat do PBI)
        -- Numerador DAX: OS com perfil preventivo que NÃO são preventivas
        SELECT numero_os FROM (
            SELECT numero_os
            FROM (
                SELECT numero_os, descricao_peca
                FROM ri_corretiva_detalhamento
                WHERE status_os != 'CANCELADA'
                  AND data_transacao IS NOT NULL
                  {extra_where}
                UNION ALL
                SELECT numero_os, descricao_peca
                FROM ri_preventiva_detalhamento
                WHERE status_os != 'CANCELADA'
                  AND data_transacao IS NOT NULL
                  {extra_where}
            ) all_items
            GROUP BY numero_os
            HAVING 
              SUM(CASE WHEN descricao_peca IN ({_PECAS_PBI_IN_LIST}) THEN 1 ELSE 0 END) >= {THRESHOLD_ITEM_PREVENTIVO}
        ) perfil
        WHERE numero_os NOT IN (
            SELECT DISTINCT numero_os
            FROM ri_preventiva_detalhamento
            WHERE status_os != 'CANCELADA'
              AND data_transacao IS NOT NULL
              {extra_where}
        )
    )
    """

def _build_perfil_preventivo_subquery(extra_where=""):
    """
    Gera subquery que identifica TODAS as OS com perfil preventivo (>=2 peças da lista PBI).
    Inclui TANTO corretivas QUANTO preventivas — usado como DENOMINADOR do % Fugas.
    
    PBI DAX equivalente: CALCULATE([Total OS], fItens[Item_Preventivo] >= 2)
    
    FIX v2: Faz UNION ALL dos ITENS (não das OS) ANTES do GROUP BY,
    replicando exatamente o PARTITION BY MaintenanceId do PBI que opera
    sobre a tabela flat fItens (todos os itens juntos).
    """
    return f"""
    (
        -- FIX v2: UNION ALL itens → GROUP BY OS → HAVING >=2
        -- Replica CALCULATE([Total OS], fItens[Item_Preventivo] >= 2)
        SELECT numero_os
        FROM (
            SELECT numero_os, descricao_peca
            FROM ri_corretiva_detalhamento
            WHERE status_os != 'CANCELADA'
              AND data_transacao IS NOT NULL
              {extra_where}
            UNION ALL
            SELECT numero_os, descricao_peca
            FROM ri_preventiva_detalhamento
            WHERE status_os != 'CANCELADA'
              AND data_transacao IS NOT NULL
              {extra_where}
        ) all_items
        GROUP BY numero_os
        HAVING 
          SUM(CASE WHEN descricao_peca IN ({_PECAS_PBI_IN_LIST}) THEN 1 ELSE 0 END) >= {THRESHOLD_ITEM_PREVENTIVO}
    )
    """

def _prefix_columns_for_subquery(sql_fragment):
    """
    Remove prefixos de alias (c., d.) das colunas para uso dentro das subqueries de fuga.
    As subqueries não usam alias de tabela.
    """
    result = sql_fragment
    for col in ['data_transacao', 'nome_cliente', 'familia_veiculo', 'status_os', 'uf']:
        result = result.replace(f'c.{col}', col)
        result = result.replace(f'd.{col}', col)
    return result

@safe_memoize(timeout=120)
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
    filter_sql = ""
    if filters:
        if filters.get('clientes'):
            # CORRIGIDO: usar nome_cliente ao invés de codigo_cliente (alinhado com outros repos)
            _client_vals = [str(c) for c in filters['clientes'] if c]
            filter_sql += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
            
        if filters.get('periodos'):
            # Converte lista ['2024-01', '2024-02'] em cláusula SQL
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            
            if period_clauses:
                filter_sql += f" AND ({' OR '.join(period_clauses)})"

        if filters.get('uf'):
             filter_sql += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
             params.extend(filters['uf'])

    # Subquery de fugas PBI (OS corretiva com >=2 peças preventivas)
    fuga_subquery = _build_fuga_os_subquery(extra_where=filter_sql)
    
    final_query = f"""
    SELECT d.*
    FROM ({query}) d
    INNER JOIN {fuga_subquery} fuga_os ON d.numero_os = fuga_os.numero_os
    ORDER BY d.data_transacao DESC LIMIT ?
    """
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
    except Exception:
        return False


@safe_memoize(timeout=120)
def get_fugas_grouped(filters=None, limit=200):
    """
    Retorna fugas agrupadas por codigo_tgm (SourceNumber).
    Fallback: se codigo_tgm não existir no DB, agrupa por codigo_cliente.
    """
    conn = get_connection()
    
    # Detectar qual coluna usar para agrupamento
    has_tgm = _has_column(conn, 'ri_corretiva_detalhamento', 'codigo_tgm')
    group_col = 'codigo_tgm' if has_tgm else 'codigo_cliente'
    
    # Usar subquery PBI para filtrar fugas
    fuga_subquery = _build_fuga_os_subquery()
    
    query = f"""
    SELECT 
        d.{group_col} as codigo_tgm,
        MIN(d.nome_cliente) as cliente_principal,
        COUNT(DISTINCT d.codigo_cliente) as qtd_clientes,
        COUNT(CASE WHEN COALESCE(d.valor_aprovado, 0) > 0 THEN d.numero_os END) as total_os,
        SUM(COALESCE(d.valor_aprovado, 0)) as valor_total,
        COUNT(DISTINCT d.numero_os) as total_os_distintas
    FROM ri_corretiva_detalhamento d
    INNER JOIN {fuga_subquery} fuga_os ON d.numero_os = fuga_os.numero_os
    WHERE 1=1
    """
    
    params = []
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            query += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
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
    
    query += f" GROUP BY d.{group_col} ORDER BY total_os DESC LIMIT {limit}"
    
    try:
        df = pd.read_sql(query, conn, params=params)
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce').fillna(0).round(2)
        if not has_tgm:
            print("[WARN] get_fugas_grouped: coluna 'codigo_tgm' não encontrada, usando 'codigo_cliente' como fallback. Faça um FULL LOAD.")
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro no get_fugas_grouped: {e}")
        return []


@safe_memoize(timeout=120)
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
    
    asset_filter = _get_asset_type_filter(tipo_ativo)
    
    # Build filter SQL
    params = []
    filter_sql = ""
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            filter_sql += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
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
        d.{group_col} as codigo_tgm,
        MIN(d.nome_cliente) as cliente_principal,
        COUNT(DISTINCT d.codigo_cliente) as qtd_clientes,
        COUNT(DISTINCT d.numero_os) as total_os,
        SUM(COALESCE(d.valor_aprovado, 0)) as valor_total
    FROM ri_corretiva_detalhamento d
    INNER JOIN {_build_fuga_os_subquery(extra_where=f"AND CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}' {asset_filter} {filter_sql}")} fuga_os ON d.numero_os = fuga_os.numero_os
    WHERE CAST(d.data_transacao AS DATE) >= '{date_start}' AND CAST(d.data_transacao AS DATE) <= '{date_end}'
      {asset_filter}
      AND COALESCE(d.valor_aprovado, 0) > 0
    GROUP BY d.{group_col} 
    ORDER BY valor_total DESC 
    LIMIT {limit}
    """
    
    try:
        import time as _time
        _t0 = _time.time()
        
        df_master = pd.read_sql(query_master, conn, params=params)
        df_master['valor_total'] = pd.to_numeric(df_master['valor_total'], errors='coerce').fillna(0).round(2)
        pass  # master query done
        
        tgm_codes = df_master['codigo_tgm'].tolist()
        if not tgm_codes:
            return []
        
        # STEP 2: Detail query — APENAS para TGMs do master, max 10 per TGM
        tgm_escaped = ", ".join(["?" for _ in tgm_codes])
        
        query_detail = f"""
        SELECT * FROM (
            SELECT 
                d.{group_col} as _tgm_key,
                MAX(d.codigo_cliente) as codigo_cliente,
                MAX(coalesce(d.nome_cliente, 'Cliente N/A')) as cliente,
                d.numero_os,
                MAX(d.nome_estabelecimento) as nome_ec,
                MAX(d.tipo_mo) as tipo_mo,
                MAX(d.descricao_peca) as descricao_peca,
                MAX(d.nome_aprovador) as nome_aprovador,
                MAX(d.data_transacao) as data_transacao,
                COUNT(CASE WHEN COALESCE(d.valor_aprovado, 0) > 0 THEN 1 END) as qtd_itens,
                SUM(COALESCE(d.valor_aprovado, 0)) as valor_total_os,
                SUM(COALESCE(d.valor_mo, 0)) as valor_mo_os,
                SUM(COALESCE(d.valor_peca, 0)) as valor_peca_os,
                ROW_NUMBER() OVER (PARTITION BY d.{group_col} ORDER BY SUM(COALESCE(d.valor_aprovado, 0)) DESC) as rn
            FROM ri_corretiva_detalhamento d
            INNER JOIN {_build_fuga_os_subquery(extra_where=f"AND CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}' {asset_filter} {filter_sql}")} fuga_os ON d.numero_os = fuga_os.numero_os
            WHERE d.{group_col} IN ({tgm_escaped})
              AND CAST(d.data_transacao AS DATE) >= '{date_start}' AND CAST(d.data_transacao AS DATE) <= '{date_end}'
              {asset_filter}
              AND COALESCE(d.valor_aprovado, 0) > 0
            GROUP BY d.{group_col}, d.numero_os
        ) sub WHERE rn <= 10
        """
        
        _t1 = _time.time()
        df_detail = pd.read_sql(query_detail, conn, params=params + [str(t) for t in tgm_codes])
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
    
    # Usar subquery PBI para filtrar fugas
    fuga_subquery = _build_fuga_os_subquery()
    
    query = f"""
    SELECT 
        codigo_cliente,
        coalesce(d.nome_cliente, 'Cliente N/A') as cliente,
        d.numero_os,
        d.descricao_peca as codigo_item,
        d.nome_estabelecimento as nome_ec,
        d.cidade,
        d.uf,
        d.tipo_mo,
        d.valor_aprovado,
        d.nome_aprovador,
        d.data_transacao
    FROM ri_corretiva_detalhamento d
    INNER JOIN {fuga_subquery} fuga_os ON d.numero_os = fuga_os.numero_os
    WHERE d.{filter_col} = ?
    """
    
    params = [str(codigo_tgm)]
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            query += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
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

@safe_memoize(timeout=120)
def get_fugas_stats(filters=None, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Calcula KPIs: Total de OSs analisadas, Qtde Fugas, % Fuga
    Conta por OS distinta. Default: últimos 30 dias.
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    
    FIX 2026-03-08: Detecção de fuga no nível da OS (ÓLEO AND FILTRO na mesma OS),
    não mais por linha individual.
    """
    conn = get_connection()
    
    # Date range: default últimos 30 dias
    date_filter = ""
    if date_start and date_end:
        date_filter = f"AND CAST(data_transacao AS DATE) BETWEEN '{date_start}' AND '{date_end}'"
    else:
        date_filter = "AND data_transacao >= CURRENT_DATE - INTERVAL 30 DAY"
    
    asset_filter = _get_asset_type_filter(tipo_ativo)
    
    # Build filter SQL
    filter_sql = ""
    params = []
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            filter_sql += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                try:
                    y, m = p.split('-')
                    period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
                except Exception:
                    pass
            if period_clauses:
                filter_sql += f" AND ({' OR '.join(period_clauses)})"
        if filters.get('date_range'):
            start, end = filters['date_range']
            filter_sql += " AND data_transacao BETWEEN ? AND ?"
            params.extend([start, end])
        if filters.get('uf'):
            filter_sql += " AND uf IN (" + ",".join(["?"]*len(filters['uf'])) + ")"
            params.extend(filters['uf'])
    
    # Subquery de fugas PBI: OS corretiva com >=2 peças preventivas
    fuga_extra_where = _prefix_columns_for_subquery(f"{date_filter} {asset_filter} {filter_sql}")
    fuga_subquery = _build_fuga_os_subquery(extra_where=fuga_extra_where)
    
    # Subquery denominador PBI: TODAS as OS com perfil preventivo (>=2 peças)
    perfil_subquery = _build_perfil_preventivo_subquery(extra_where=fuga_extra_where)
    
    # FIX 2026-03-25: Denominador alinhado com PBI
    # PBI usa: % Fugas = Fugas / (OS com perfil preventivo)
    # NÃO Fugas / Total OS corretivas!
    query = f"""
    WITH fuga_os AS {fuga_subquery},
         perfil_os AS {perfil_subquery}
    SELECT 
        COUNT(DISTINCT p.numero_os) as total_perfil_preventivo,
        COUNT(DISTINCT f.numero_os) as qtd_fugas
    FROM perfil_os p
    LEFT JOIN fuga_os f ON p.numero_os = f.numero_os
    """

    try:
        result = conn.execute(query, params).fetchone()
        total_perfil = result[0] or 0
        fugas = result[1] or 0
        pct_fuga = (fugas / total_perfil * 100) if total_perfil > 0 else 0
        
        return {
            "total_os": total_perfil,
            "qtd_fugas": fugas,
            "pct_fuga": round(pct_fuga, 2)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Erro CRÍTICO no get_fugas_stats: {e}")
        return {"total_os": 0, "qtd_fugas": 0, "pct_fuga": 0, "error": str(e)}

@safe_memoize(timeout=120)
def get_fugas_chart_data(filters=None, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Retorna % Fugas agrupado por Ano/Mes para o gráfico.
    Conta por OS distinta (não por item).
    Default: últimos 30 dias se sem date range.
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    
    FIX 2026-03-08: Detecção de fuga no nível da OS (ÓLEO AND FILTRO na mesma OS),
    não mais por linha individual.
    """
    conn = get_connection()
    asset_filter = _get_asset_type_filter(tipo_ativo)

    # Date range: usa todo o histórico se sem filtro (FIX v2: não limitar a 30 dias)
    date_filter = ""
    if date_start and date_end:
        date_filter = f"AND CAST(data_transacao AS DATE) BETWEEN '{date_start}' AND '{date_end}'"
    # Sem filtro de data = usa todos os dados disponíveis (histórico completo)

    # Build filter SQL
    filter_sql = ""
    params = []
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            filter_sql += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
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

    # Subqueries PBI: fugas + perfil preventivo (FIX 2026-03-25)
    fuga_extra_where = _prefix_columns_for_subquery(f"{date_filter} {asset_filter} {filter_sql}")
    fuga_subquery = _build_fuga_os_subquery(extra_where=fuga_extra_where)
    perfil_subquery = _build_perfil_preventivo_subquery(extra_where=fuga_extra_where)

    # FIX 2026-03-25v2: Base = UNION de corr+prev (mesma base flat do PBI)
    # Sem isso, OS preventivas ficam fora do denominador e % infla para ~90%
    query = f"""
    WITH fuga_os AS {fuga_subquery},
         perfil_os AS {perfil_subquery},
         base_os AS (
             -- UNION de OS de ambas tabelas (simula fItens flat)
             SELECT numero_os, data_transacao
             FROM ri_corretiva_detalhamento
             WHERE data_transacao IS NOT NULL AND status_os != 'CANCELADA'
               {date_filter} {asset_filter} {filter_sql}
             UNION
             SELECT numero_os, data_transacao
             FROM ri_preventiva_detalhamento
             WHERE data_transacao IS NOT NULL AND status_os != 'CANCELADA'
               {date_filter} {asset_filter} {filter_sql}
         )
    SELECT 
        strftime(d.data_transacao, '%Y-%m') as mes_ano,
        COUNT(DISTINCT p.numero_os) as total_mensal,
        COUNT(DISTINCT f.numero_os) as fugas_mensal,
        COUNT(DISTINCT CAST(d.data_transacao AS DATE)) as dias_dados
    FROM base_os d
    INNER JOIN perfil_os p ON d.numero_os = p.numero_os
    LEFT JOIN fuga_os f ON d.numero_os = f.numero_os
    WHERE 1=1
    GROUP BY 1 ORDER BY 1
    """
    
    try:
        from datetime import date as _date
        current_month = _date.today().strftime('%Y-%m')
        
        df = pd.read_sql(query, conn, params=params)
        df['fugas_mensal'] = pd.to_numeric(df['fugas_mensal'], errors='coerce').fillna(0)
        df['total_mensal'] = pd.to_numeric(df['total_mensal'], errors='coerce').fillna(0)
        df['pct_fuga'] = (df['fugas_mensal'] / df['total_mensal'].replace(0, 1) * 100).fillna(0).round(2)
        df['is_partial'] = df['mes_ano'] == current_month
        result = df.to_dict('list')
        return result
    except Exception as e:
        print(f"Erro no get_fugas_chart_data: {e}")
        return {}

def get_top_offenders(filters=None, entity='estabelecimento', limit=5, date_start=None, date_end=None, tipo_ativo="VEICULOS"):
    """
    Retorna top X entidades com maior volume/percentual de fugas.
    Entity pode ser: 'estabelecimento', 'aprovador'
    tipo_ativo: VEICULOS | EQUIPAMENTOS | TODOS
    
    FIX 2026-03-25: Denominador = perfil_os (OS com perfil preventivo >=2 peças),
    NÃO total OS corretivas. Alinhado com PBI CALCULATE([Total OS], fItens[Item_Preventivo]>=2).
    """
    conn = get_connection()
    
    col_map = {
        'estabelecimento': 'nome_estabelecimento',
        'aprovador': 'nome_aprovador',
    }
    col = col_map.get(entity, 'nome_estabelecimento')

    asset_filter = _get_asset_type_filter(tipo_ativo)

    # Date range: default últimos 30 dias
    if not date_start or not date_end:
        from datetime import date as _date, timedelta as _td
        date_end = _date.today().isoformat()
        date_start = (_date.today() - _td(days=30)).isoformat()
    
    date_filter = f"AND CAST(data_transacao AS DATE) >= '{date_start}' AND CAST(data_transacao AS DATE) <= '{date_end}'"
    
    # Build filter SQL
    filter_sql = ""
    params = []
    if filters:
        if filters.get('clientes'):
            _client_vals = [str(c) for c in filters['clientes'] if c]
            filter_sql += f" AND nome_cliente IN ({safe_sql_in_list(_client_vals)})"
        if filters.get('periodos'):
            period_clauses = []
            for p in filters['periodos']:
                y, m = p.split('-')
                period_clauses.append(f"(YEAR(data_transacao) = {y} AND MONTH(data_transacao) = {m})")
            if period_clauses:
                filter_sql += f" AND ({' OR '.join(period_clauses)})"
    
    # FIX 2026-03-25: Usar perfil_os como denominador (alinhado PBI)
    fuga_extra_where = _prefix_columns_for_subquery(f"{date_filter} {asset_filter} {filter_sql}")
    fuga_subquery = _build_fuga_os_subquery(extra_where=fuga_extra_where)
    perfil_subquery = _build_perfil_preventivo_subquery(extra_where=fuga_extra_where)
    
    # Base = UNION de corr+prev (mesma base flat do PBI)
    # Agrupamos por entidade sobre as OS com perfil preventivo
    query = f"""
    WITH fuga_os AS {fuga_subquery},
         perfil_os AS {perfil_subquery},
         base_os AS (
             SELECT numero_os, {col}, data_transacao
             FROM ri_corretiva_detalhamento
             WHERE data_transacao IS NOT NULL AND status_os != 'CANCELADA'
               {date_filter} {asset_filter} {filter_sql}
             UNION
             SELECT numero_os, {col}, data_transacao
             FROM ri_preventiva_detalhamento
             WHERE data_transacao IS NOT NULL AND status_os != 'CANCELADA'
               {date_filter} {asset_filter} {filter_sql}
         )
    SELECT 
        COALESCE(NULLIF(d.{col}, ''), 'Não Informado') as entidade,
        COUNT(DISTINCT p.numero_os) as total_os,
        COUNT(DISTINCT f.numero_os) as qtd_fugas
    FROM base_os d
    INNER JOIN perfil_os p ON d.numero_os = p.numero_os
    LEFT JOIN fuga_os f ON d.numero_os = f.numero_os
    GROUP BY 1 HAVING qtd_fugas > 0 ORDER BY qtd_fugas DESC LIMIT {limit}
    """
    
    try:
        df = pd.read_sql(query, conn, params=params)
        df['qtd_fugas'] = pd.to_numeric(df['qtd_fugas'], errors='coerce').fillna(0)
        df['total_os'] = pd.to_numeric(df['total_os'], errors='coerce').fillna(0)
        df['pct_fuga'] = (df['qtd_fugas'] / df['total_os'].replace(0, 1) * 100).fillna(0).round(1)
        
        # Flag interno/externo para aprovadores
        if entity == 'aprovador':
            df['is_internal'] = False  # Default: externo
        
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro top offenders: {e}")
        return []

