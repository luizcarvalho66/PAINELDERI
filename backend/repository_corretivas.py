# -*- coding: utf-8 -*-
"""
Repository Corretivas - Queries especializadas para RI Corretivas

Este módulo contém as queries SQL otimizadas para:
- Gráfico de % RI (filtrado por até 2 itens e até R$ 1.500)
- Tabela do Farol (agrupado por Peça + MO com P70)
- Logs de não aprovação

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
from database import get_connection
from backend.cache_config import safe_memoize
from backend.repositories.repo_base import MONTH_MAP
from engine.farol_engine import processar_dados_farol, get_resumo_farois


# =============================================================================
# QUERY 1: Dados para Gráfico RI (com filtros de até 2 itens e R$ 1.500)
# =============================================================================

@safe_memoize(timeout=300)
def get_ri_corretivas_chart(filters: dict = None) -> pd.DataFrame:
    """
    Retorna dados para o gráfico de evolução do Farol RI Corretivas.
    
    NOVA LÓGICA:
    - Mostra montante (R$) por mês de OSs FORA da aprovação automática
    - Itens cujo tipo_mo NÃO está na lista ref_aprovacao_automatica
    - Permite comparar com meta de aprovação automática
    
    Returns:
        DataFrame com colunas: ano, mes_num, mes_nome, valor_fora_auto, 
                               valor_total, qtd_os_fora, qtd_os_total, pct_fora
    """
    conn = get_connection()
    
    if conn is None:
        print("[REPO_CORRETIVAS] Sem conexão com banco de dados")
        return pd.DataFrame()
    
    try:
        # Build WHERE clause from filters
        where_clauses = []
        
        if filters:
            if filters.get("periodos"):
                period_clauses = []
                for p in filters["periodos"]:
                    try:
                        year, month = p.split("-")
                        period_clauses.append(f"(ano = {year} AND mes_num = {month})")
                    except Exception:
                        pass
                if period_clauses:
                    where_clauses.append(f"({' OR '.join(period_clauses)})")
            
            if filters.get("clientes"):
                placeholders = ", ".join(["?"] * len(filters["clientes"]))
                where_clauses.append(f"nome_cliente IN ({placeholders})")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        _params = list(filters["clientes"]) if filters and filters.get("clientes") else []
        
        # Query SIMPLIFICADA: Usa COALESCE para escolher entre data_transacao e data_aprovacao_os
        query = f"""
        WITH 
        -- Lista de tipos de MO com aprovação automática (normalizada)
        tipos_auto AS (
            SELECT UPPER(TRIM(tipo_mo)) as tipo_mo_norm 
            FROM ref_aprovacao_automatica
            WHERE tipo_mo IS NOT NULL
        ),
        -- Dados base: extrai ano/mês usando COALESCE entre as duas datas disponíveis
        dados_base AS (
            SELECT 
                numero_os,
                nome_cliente,
                COALESCE(valor_aprovado, 0) as valor,
                COALESCE(UPPER(TRIM(tipo_mo)), 'SEM_TIPO_MO') as tipo_mo_norm,
                YEAR(COALESCE(data_transacao, data_aprovacao_os)) as ano,
                MONTH(COALESCE(data_transacao, data_aprovacao_os)) as mes_num
            FROM ri_corretiva_detalhamento
            WHERE COALESCE(data_transacao, data_aprovacao_os) IS NOT NULL
        )
        SELECT
            d.ano,
            d.mes_num,
            COUNT(DISTINCT d.numero_os) as qtd_os_total,
            COALESCE(SUM(d.valor), 0) as valor_total,
            
            -- Valor de itens FORA da aprovação automática
            COALESCE(SUM(
                CASE WHEN NOT EXISTS (
                    SELECT 1 FROM tipos_auto ta WHERE ta.tipo_mo_norm = d.tipo_mo_norm
                ) THEN d.valor ELSE 0 END
            ), 0) as valor_fora_auto,
            
            -- Qtd de OSs com pelo menos 1 item fora
            COUNT(DISTINCT CASE 
                WHEN NOT EXISTS (
                    SELECT 1 FROM tipos_auto ta WHERE ta.tipo_mo_norm = d.tipo_mo_norm
                ) THEN d.numero_os 
            END) as qtd_os_fora
            
        FROM dados_base d
        WHERE d.ano IS NOT NULL AND d.mes_num IS NOT NULL AND {where_sql}
        GROUP BY d.ano, d.mes_num
        HAVING COUNT(*) > 0
        ORDER BY d.ano, d.mes_num
        """
        
        df = conn.execute(query, _params).fetchdf()
        
        if df.empty:
            print("[REPO_CORRETIVAS] Chart: Sem dados retornados")
            return pd.DataFrame()
        
        # Calcular % fora da aprovação automática
        df['pct_fora'] = (df['valor_fora_auto'].astype(float) / df['valor_total'].replace(0, 1)) * 100
        
        # Adicionar nome do mês
        df['mes_nome'] = df['mes_num'].map(MONTH_MAP)
        
        print(f"[REPO_CORRETIVAS] Chart: {len(df)} meses | Valor fora auto: R$ {df['valor_fora_auto'].sum():,.2f}")
        return df
        
    except Exception as e:
        print(f"[REPO_CORRETIVAS] Erro no chart: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


# =============================================================================
# QUERY 2: Dados para Tabela do Farol (MOVIDO para repo_farol_table.py)
# =============================================================================
# IMPORTANTE: Estas funções foram movidas para backend/repositories/repo_farol_table.py
# Use: from backend.repositories import get_farol_table_data, get_farol_resumo

from backend.repositories.repo_farol_table import get_farol_table_data, get_farol_resumo


# =============================================================================
# QUERY 4: Logs de Não Aprovação
# =============================================================================

@safe_memoize(timeout=300)
def get_logs_nao_aprovacao(filters: dict = None, limit: int = 100) -> pd.DataFrame:
    """
    Retorna logs de OSs que não foram aprovadas automaticamente.
    """
    conn = get_connection()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        where_clauses = [
            "mensagem_log IS NOT NULL",
            "mensagem_log != ''",
            "TRIM(mensagem_log) != ''"
        ]
        params = []
        
        if filters:
            if filters.get("peca"):
                where_clauses.append("peca = ?")
                params.append(filters['peca'])
            if filters.get("tipo_mo"):
                where_clauses.append("tipo_mo = ?")
                params.append(filters['tipo_mo'])
            if filters.get("clientes"):
                placeholders = ", ".join(["?" for _ in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ({placeholders})")
                params.extend(filters["clientes"])
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            numero_os,
            nome_cliente,
            peca,
            tipo_mo,
            valor_aprovado,
            mensagem_log,
            data_transacao
        FROM ri_corretiva_detalhamento
        WHERE {where_sql}
        ORDER BY data_transacao DESC
        LIMIT {int(limit)}
        """
        
        df = conn.execute(query, params).fetchdf()
        print(f"[REPO_CORRETIVAS] Logs: {len(df)} registros retornados")
        return df
        
    except Exception as e:
        print(f"[REPO_CORRETIVAS] Erro nos logs: {e}")
        return pd.DataFrame()


# =============================================================================
# QUERY 5: Drill-Down de uma chave específica
# =============================================================================

@safe_memoize(timeout=180)
def get_drill_down_chave(peca: str, tipo_mo: str, limit: int = 50) -> pd.DataFrame:
    """
    Retorna detalhes de OSs para uma chave específica (Peça + Tipo MO).
    Usado para drill-down na tabela do farol.
    """
    conn = get_connection()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = f"""
        SELECT 
            numero_os,
            nome_cliente,
            valor_aprovado,
            data_transacao,
            mensagem_log,
            CASE 
                WHEN UPPER(TRIM(tipo_mo)) IN (SELECT UPPER(TRIM(tipo_mo)) FROM ref_aprovacao_automatica)
                THEN 'Automática'
                ELSE 'Manual'
            END as tipo_aprovacao
        FROM ri_corretiva_detalhamento
        WHERE peca = ? AND tipo_mo = ?
        ORDER BY data_transacao DESC
        LIMIT {int(limit)}
        """
        
        df = conn.execute(query, [peca, tipo_mo]).fetchdf()
        return df
        
    except Exception as e:
        print(f"[REPO_CORRETIVAS] Erro no drill-down: {e}")
        return pd.DataFrame()

