# -*- coding: utf-8 -*-
"""
Repository Filters - Queries para popular dropdowns dinamicamente

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
import pandas as pd
from backend.repositories.repo_base import (
    get_connection, get_readonly_connection, safe_memoize, MONTH_NAMES
)


@safe_memoize(timeout=600)  # Cache for 10 minutes
def get_distinct_clients_corretiva():
    """
    Retorna lista de clientes distintos da tabela ri_corretiva_detalhamento.
    Formato: [{"label": "Nome Cliente", "value": "Nome Cliente"}, ...]
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT nome_cliente
        FROM ri_corretiva_detalhamento
        WHERE nome_cliente IS NOT NULL AND nome_cliente != ''
        ORDER BY nome_cliente
        LIMIT 500
        """
        # CURSOR FIX
        cursor = conn.cursor()
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        print(f"[REPO_FILTERS] Clientes corretiva encontrados: {len(df)}")
        return [{"label": c, "value": c} for c in df['nome_cliente'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar clientes corretiva: {e}")
        return []


@safe_memoize(timeout=600)  # Cache for 10 minutes
def get_distinct_clients_preventiva():
    """
    Retorna lista de clientes distintos da tabela logs_regulacao_preventiva_header.
    Nota: Esta tabela pode não ter nome_cliente diretamente, usa cod_cliente se necessário.
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        # Tenta buscar da tabela de detalhamento que tem nome_cliente
        query = """
        SELECT DISTINCT nome_cliente
        FROM ri_corretiva_detalhamento
        WHERE nome_cliente IS NOT NULL AND nome_cliente != ''
        ORDER BY nome_cliente
        LIMIT 500
        """
        cursor = conn.cursor()
        df = cursor.execute(query).fetchdf()
        cursor.close()
        return [{"label": c, "value": c} for c in df['nome_cliente'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar clientes preventiva: {e}")
        return []


@safe_memoize(timeout=600)  # Cache for 10 minutes
def get_distinct_months():
    """
    Retorna meses distintos com dados, formatados como opções de dropdown.
    Formato: [{"label": "Janeiro 2024", "value": "2024-01"}, ...]
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT 
            year(data_transacao) as ano,
            month(data_transacao) as mes
        FROM ri_corretiva_detalhamento
        WHERE data_transacao IS NOT NULL
        UNION
        SELECT DISTINCT 
            year(data_cadastro) as ano,
            month(data_cadastro) as mes
        FROM logs_regulacao_preventiva_header
        WHERE data_cadastro IS NOT NULL
        ORDER BY 1 DESC, 2 DESC
        """
        cursor = conn.cursor()
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        print(f"[REPO_FILTERS] Meses encontrados: {len(df)}")
        
        options = []
        for _, row in df.iterrows():
            try:
                ano = int(row['ano'])
                mes = int(row['mes'])
                label = f"{MONTH_NAMES.get(mes, mes)} {ano}"
                value = f"{ano}-{mes:02d}"
                options.append({"label": label, "value": value})
            except Exception as row_err:
                print(f"[REPO_FILTERS] Erro ao processar linha de mês: {row_err}")
                continue
        
        return options
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar meses: {e}")
        return []


def get_distinct_pecas():
    """
    Retorna lista de peças distintas da tabela ri_corretiva_detalhamento.
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT peca, COUNT(*) as qtd
        FROM ri_corretiva_detalhamento
        WHERE peca IS NOT NULL AND peca != ''
        GROUP BY peca
        ORDER BY qtd DESC
        LIMIT 200
        """
        df = conn.execute(query).fetchdf()
        return [{"label": p, "value": p} for p in df['peca'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar peças: {e}")
        return []


def get_distinct_chaves():
    """
    Retorna lista de chaves (Peça + MO) distintas para filtro do Farol.
    Formato: [{"label": "Peca + MO", "value": "Peca + MO"}, ...]
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) as chave
        FROM ri_corretiva_detalhamento
        WHERE peca IS NOT NULL OR tipo_mo IS NOT NULL
        ORDER BY 1
        LIMIT 500
        """
        cursor = conn.cursor()
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        return [{"label": c, "value": c} for c in df['chave'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar chaves: {e}")
        return []


def get_distinct_tipo_mo():
    """
    Retorna lista de tipos de mão de obra distintos.
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT tipo_mo, COUNT(*) as qtd
        FROM ri_corretiva_detalhamento
        WHERE tipo_mo IS NOT NULL AND tipo_mo != ''
        GROUP BY tipo_mo
        ORDER BY qtd DESC
        LIMIT 100
        """
        df = conn.execute(query).fetchdf()
        return [{"label": t, "value": t} for t in df['tipo_mo'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar tipo_mo: {e}")
        return []


def get_distinct_planos():
    """
    Retorna lista de planos de manutenção distintos (preventiva).
    """
    conn = get_readonly_connection()
    if conn is None:
        return []
    
    try:
        query = """
        SELECT DISTINCT plano_manutencao
        FROM logs_regulacao_preventiva_header
        WHERE plano_manutencao IS NOT NULL AND plano_manutencao != ''
        ORDER BY plano_manutencao
        LIMIT 100
        """
        df = conn.execute(query).fetchdf()
        return [{"label": p, "value": p} for p in df['plano_manutencao'].tolist()]
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar planos: {e}")
        return []


def get_value_range_stats():
    """
    Retorna estatísticas de faixa de valor para calibrar o range slider.
    Returns: {"min": float, "max": float, "median": float}
    """
    conn = get_readonly_connection()
    if conn is None:
        return {"min": 0, "max": 50000, "median": 5000}
    
    try:
        query = """
        SELECT 
            MIN(valor_aprovado) as min_val,
            MAX(valor_aprovado) as max_val,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY valor_aprovado) as median_val
        FROM ri_corretiva_detalhamento
        WHERE valor_aprovado > 0
        """
        result = conn.execute(query).fetchone()
        return {
            "min": float(result[0] or 0),
            "max": float(result[1] or 50000),
            "median": float(result[2] or 5000)
        }
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar range de valores: {e}")
        return {"min": 0, "max": 50000, "median": 5000}


def get_tooltip_data_corretiva(mes: str = None):
    """
    Retorna dados agregados para tooltips do gráfico corretiva.
    
    Args:
        mes: Filtro de mês no formato 'YYYY-MM' (opcional)
    
    Returns:
        {
            "top_clientes": [{"nome": str, "qtd": int}, ...],
            "top_pecas": [{"nome": str, "qtd": int}, ...],
            "top_tipo_mo": [{"nome": str, "qtd": int}, ...]
        }
    """
    conn = get_readonly_connection()
    if conn is None:
        return {"top_clientes": [], "top_pecas": [], "top_tipo_mo": []}
    
    try:
        where_clause = ""
        if mes:
            year, month = mes.split('-')
            where_clause = f"WHERE year(data_transacao) = {year} AND month(data_transacao) = {month}"
        
        # Top 5 Clientes
        q_clientes = f"""
        SELECT nome_cliente as nome, COUNT(*) as qtd
        FROM ri_corretiva_detalhamento
        {where_clause}
        {"AND" if where_clause else "WHERE"} nome_cliente IS NOT NULL
        GROUP BY nome_cliente
        ORDER BY qtd DESC
        LIMIT 5
        """
        
        # Top 5 Peças
        q_pecas = f"""
        SELECT peca as nome, COUNT(*) as qtd
        FROM ri_corretiva_detalhamento
        {where_clause}
        {"AND" if where_clause else "WHERE"} peca IS NOT NULL AND peca != ''
        GROUP BY peca
        ORDER BY qtd DESC
        LIMIT 5
        """
        
        # Top 3 Tipos MO
        q_tipo_mo = f"""
        SELECT tipo_mo as nome, COUNT(*) as qtd
        FROM ri_corretiva_detalhamento
        {where_clause}
        {"AND" if where_clause else "WHERE"} tipo_mo IS NOT NULL AND tipo_mo != ''
        GROUP BY tipo_mo
        ORDER BY qtd DESC
        LIMIT 3
        """
        
        df_clientes = conn.execute(q_clientes).fetchdf()
        df_pecas = conn.execute(q_pecas).fetchdf()
        df_tipo_mo = conn.execute(q_tipo_mo).fetchdf()
        
        return {
            "top_clientes": df_clientes.to_dict('records') if not df_clientes.empty else [],
            "top_pecas": df_pecas.to_dict('records') if not df_pecas.empty else [],
            "top_tipo_mo": df_tipo_mo.to_dict('records') if not df_tipo_mo.empty else []
        }
    except Exception as e:
        print(f"[REPO_FILTERS] Erro ao buscar tooltip data: {e}")
        return {"top_clientes": [], "top_pecas": [], "top_tipo_mo": []}
