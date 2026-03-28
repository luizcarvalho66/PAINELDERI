# -*- coding: utf-8 -*-
"""
Repository Farol Chart - Query para o gráfico de evolução do Farol

Author: Luiz  Eduardo Carvalho ( O mestre dos códigos )
"""

import pandas as pd
from backend.repositories.repo_base import (
    get_connection, safe_memoize, MONTH_MAP
)


@safe_memoize(timeout=300)
def get_ri_corretivas_chart(filters: dict = None) -> pd.DataFrame:
    """
    Retorna dados para o gráfico de evolução do Farol RI Corretivas.
    
    LÓGICA:
    - Mostra montante (R$) por mês de OSs FORA da aprovação automática
    - Itens cujo tipo_mo NÃO está na lista ref_aprovacao_automatica
    - Permite comparar com meta de aprovação automática
    
    Returns:
        DataFrame com colunas: ano, mes_num, mes_nome, valor_fora_auto, 
                               valor_total, qtd_os_fora, qtd_os_total, pct_fora
    """
    conn = get_connection()
    
    if conn is None:
        print("[REPO_FAROL_CHART] Sem conexão com banco de dados")
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
              AND status_os != 'CANCELADA'
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
            # DEBUG: Verificar por que retorna vazio
            debug_q = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN data_transacao IS NOT NULL THEN 1 ELSE 0 END) as com_data,
                COUNT(DISTINCT YEAR(data_transacao)) as anos_distintos,
                COUNT(DISTINCT tipo_mo) as tipos_mo_distintos
            FROM ri_corretiva_detalhamento
            """
            debug_df = conn.execute(debug_q).fetchdf()
            if not debug_df.empty:
                r = debug_df.iloc[0]
                print(f"[CHART DEBUG] Total: {r['total']}, Com data_transacao: {r['com_data']}, Anos: {r['anos_distintos']}, Tipos MO: {r['tipos_mo_distintos']}")
            
            # Se não tem data_transacao, usar data_aprovacao_os
            fallback_query = """
            SELECT COUNT(*) as total FROM ri_corretiva_detalhamento 
            WHERE data_transacao IS NOT NULL OR data_aprovacao_os IS NOT NULL
            """
            fallback_df = conn.execute(fallback_query).fetchdf()
            print(f"[CHART DEBUG] Registros com alguma data: {fallback_df.iloc[0]['total'] if not fallback_df.empty else 0}")
            
            print("[REPO_FAROL_CHART] Chart: Sem dados retornados")
            return pd.DataFrame()
        
        # Calcular % fora da aprovação automática
        df['pct_fora'] = (df['valor_fora_auto'].astype(float) / df['valor_total'].replace(0, 1)) * 100
        
        # Adicionar nome do mês
        df['mes_nome'] = df['mes_num'].map(MONTH_MAP)
        
        print(f"[REPO_FAROL_CHART] Chart: {len(df)} meses | Valor fora auto: R$ {df['valor_fora_auto'].sum():,.2f}")
        return df
        
    except Exception as e:
        print(f"[REPO_FAROL_CHART] Erro no chart: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
