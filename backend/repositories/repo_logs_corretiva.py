# -*- coding: utf-8 -*-
"""
Repository Logs Corretiva - Queries para a seção de Logs de Não Aprovação

Responsabilidade: Gerenciar dados da tabela de logs de não aprovação automática.

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize


@safe_memoize(timeout=600)
def get_logs_filter_options() -> dict:
    """
    Retorna opções ÚNICAS para todos os filtros da seção de logs.
    Apenas clientes/peças/tipos que constam em itens de não aprovação automática.
    
    Returns:
        Dict com listas de opções para cada filtro:
        - clientes: Lista de nomes de clientes
        - pecas: Lista de peças
        - tipos_mo: Lista de tipos de mão de obra
    """
    
    conn = get_connection()
    if conn is None:
        print("[REPO_LOGS] ERRO: Conexão é None")
        return {"clientes": [], "pecas": [], "tipos_mo": []}
    
    try:
        # Critério: Aprovação HUMANA (não passou na automática)
        # Quando nome_aprovador é uma pessoa real (não SISTEMA, NAO INFORMADO, etc.)
        where_cond = """
            nome_aprovador IS NOT NULL 
            AND TRIM(nome_aprovador) != ''
            AND UPPER(TRIM(nome_aprovador)) NOT IN ('NAO INFORMADO', 'SISTEMA')
        """
        
        # 1. Clientes que têm logs de não aprovação (usar cursor isolado)
        q_cli = f"SELECT DISTINCT nome_cliente FROM ri_corretiva_detalhamento WHERE {where_cond} AND nome_cliente IS NOT NULL ORDER BY nome_cliente"
        cursor1 = conn.cursor()
        clientes = [r[0] for r in cursor1.execute(q_cli).fetchall() if r[0]]
        cursor1.close()
        
        
        # 2. Peças (usar cursor isolado)
        q_peca = f"SELECT DISTINCT peca FROM ri_corretiva_detalhamento WHERE {where_cond} AND peca IS NOT NULL ORDER BY peca"
        cursor2 = conn.cursor()
        pecas = [r[0] for r in cursor2.execute(q_peca).fetchall() if r[0]]
        cursor2.close()
        
        # 3. Tipos MO (usar cursor isolado)
        q_mo = f"SELECT DISTINCT tipo_mo FROM ri_corretiva_detalhamento WHERE {where_cond} AND tipo_mo IS NOT NULL ORDER BY tipo_mo"
        cursor3 = conn.cursor()
        tipos_mo = [r[0] for r in cursor3.execute(q_mo).fetchall() if r[0]]
        cursor3.close()
        
        
        
        return {
            "clientes": clientes,
            "pecas": pecas,
            "tipos_mo": tipos_mo
        }
        
    except Exception as e:
        print(f"[REPO_LOGS] Erro ao carregar filtros: {e}")
        import traceback
        traceback.print_exc()
        return {"clientes": [], "pecas": [], "tipos_mo": []}


@safe_memoize(timeout=300)
def get_logs_total_count(filters: dict = None) -> int:
    """
    Retorna o total de logs de não aprovação para calcular paginação.
    
    Args:
        filters: Dicionário opcional com filtros
    
    Returns:
        Total de registros
    """
    conn = get_connection()
    
    if conn is None:
        return 0
    
    try:
        # Critério: Aprovação por HUMANO (não automática)
        where_clauses = [
            "nome_aprovador IS NOT NULL",
            "UPPER(TRIM(nome_aprovador)) NOT IN ('NAO INFORMADO', 'SISTEMA', '')"
        ]
        
        if filters:
            if filters.get("peca"):
                peca_escaped = filters['peca'].replace("'", "''")
                where_clauses.append(f"peca = '{peca_escaped}'")
            if filters.get("tipo_mo"):
                tipo_escaped = filters['tipo_mo'].replace("'", "''")
                where_clauses.append(f"tipo_mo = '{tipo_escaped}'")
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"SELECT COUNT(*) FROM ri_corretiva_detalhamento WHERE {where_sql}"
        
        # Usar cursor isolado
        cursor = conn.cursor()
        result = cursor.execute(query).fetchone()
        cursor.close()
        
        total = result[0] if result else 0
        
        return total
        
    except Exception as e:
        print(f"[REPO_LOGS] Erro ao contar logs: {e}")
        return 0


@safe_memoize(timeout=300)
def get_logs_nao_aprovacao(filters: dict = None, page: int = 1, page_size: int = 15) -> pd.DataFrame:
    """
    Retorna logs de OSs que NÃO passaram na aprovação automática.
    (Itens que exigiram intervenção humana)
    
    Args:
        filters: Dicionário opcional com filtros:
            - peca: Nome da peça
            - tipo_mo: Tipo de mão de obra
            - clientes: Lista de nomes de clientes
        page: Número da página (1-based)
        page_size: Itens por página (default: 15)
    
    Returns:
        DataFrame com colunas: numero_os, nome_cliente, peca, tipo_mo, 
                               valor_aprovado, responsavel_aprovacao, motivo, data_transacao
    """
    conn = get_connection()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        # Calcular offset
        offset = (page - 1) * page_size
        
        # Critério: Aprovação por HUMANO (não automática)
        where_clauses = [
            "nome_aprovador IS NOT NULL",
            "UPPER(TRIM(nome_aprovador)) NOT IN ('NAO INFORMADO', 'SISTEMA', '')"
        ]
        
        if filters:
            if filters.get("peca"):
                peca_escaped = filters['peca'].replace("'", "''")
                where_clauses.append(f"peca = '{peca_escaped}'")
            if filters.get("tipo_mo"):
                tipo_escaped = filters['tipo_mo'].replace("'", "''")
                where_clauses.append(f"tipo_mo = '{tipo_escaped}'")
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            numero_os,
            nome_cliente,
            peca,
            tipo_mo,
            valor_aprovado,
            nome_aprovador as responsavel_aprovacao,
            COALESCE(mensagem_log, 'Aprovação Manual') as motivo,
            data_transacao
        FROM ri_corretiva_detalhamento
        WHERE {where_sql}
        ORDER BY data_transacao DESC
        LIMIT {page_size} OFFSET {offset}
        """
        
        # Usar cursor isolado para thread-safety (evita race condition)
        cursor = conn.cursor()
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        
        return df
        
    except Exception as e:
        print(f"[REPO_LOGS] Erro ao buscar logs: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

