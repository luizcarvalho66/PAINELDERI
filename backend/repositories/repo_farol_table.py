# -*- coding: utf-8 -*-
"""
Repository Farol Table - Queries para a tabela e cards do Farol

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize
from engine.farol_engine import processar_dados_farol, get_resumo_farois
from backend.repositories.repo_preventiva import TIPOS_MO_OPORTUNIDADE_RI

# Gera cláusula IN para filtro de oportunidades por tipo_mo
_OPORTUNIDADE_MO_IN = "'" + "', '".join(TIPOS_MO_OPORTUNIDADE_RI) + "'"

def _benchmark_cte(conn) -> str:
    """Gera CTE benchmark_total de forma segura.
    Se ref_total não existe (pricing pipeline ainda não rodou), retorna SELECT vazio.
    """
    try:
        exists = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ref_total'"
        ).fetchone()[0]
    except Exception:
        exists = 0
    if exists:
        return "benchmark_total AS (SELECT tipo_mo, AVG(p70_total) as avg_p70_total FROM ref_total GROUP BY tipo_mo)"
    else:
        return "benchmark_total AS (SELECT NULL::VARCHAR as tipo_mo, 0::DOUBLE as avg_p70_total WHERE FALSE)"


# NOTA: Cache reativado após correções. Monitorar comportamento com filtros vazios.
@safe_memoize(timeout=300)
def get_farol_table_data(filters: dict = None, page: int = 1, page_size: int = 10, only_opportunities: bool = False) -> list:
    """
    Retorna dados agregados por Peça + Tipo MO para a tabela do farol.
    Suporta paginação via OFFSET/LIMIT.
    
    Args:
        filters: Dicionário de filtros (clientes, periodo, chaves, prioridade)
        page: Número da página atual (1-based)
        page_size: Itens por página
        only_opportunities: Se True, filtra apenas chaves com P70 <= R$ 1.500
    
    Returns:
        Lista de dicts com: chave, pct_aprovacao, p70, qtd_os, tendencia, farol_cor, sugestao
    """
    conn = get_connection()
    
    if conn is None:
        print("[REPO_FAROL_TABLE] ERRO CRÍTICO: Conexão DuckDB é None. Abortando query.")
        return []
    
    try:
        # Calcular offset
        offset = (page - 1) * page_size
        
        # Criar cursor isolado para thread-safety
        cursor = conn.cursor()

        where_clauses = []
        
        if filters:
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
            
            # Filtro por Chave (Peça + MO) - Aplicado no SQL para performance
            if filters.get("chaves"):
                chaves_escaped = "', '".join([c.replace("'", "''") for c in filters["chaves"]])
                where_clauses.append(f"CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) IN ('{chaves_escaped}')")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Filtro de oportunidades: chaves com RI < 80% (onde ha espaco de melhoria)
        # Ordenadas por impacto financeiro (volume x valor)
        opp_cte = ""
        source_table = "ri_corretiva_detalhamento"
        opp_having = ""
        opp_order = "a.qtd_os DESC"  # default: por volume
        if only_opportunities:
            # Filtrar chaves onde regulacao RI < 80% (Amarelo + Vermelho)
            opp_having = """HAVING (SUM(CASE WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                                                   OR LOWER(mensagem_log) LIKE '%aprovacao automatica%' THEN 1 ELSE 0 END)::FLOAT 
                           / NULLIF(COUNT(*), 0)) * 100 < 80"""
            # Ordenar por impacto financeiro (OS x P70 = dinheiro em jogo)
            opp_order = "(a.qtd_os * a.p70) DESC"
        
        # Verifica se tem filtro de prioridade -> Se sim, precisamos buscar TUDO para filtrar no Python
        filter_prioridade = filters.get("prioridade") if filters else None
        
        # Se tem filtro de prioridade, removemos paginação SQL para aplicar depois
        use_sql_pagination = filter_prioridade is None
        
        limit_clause = ""
        if use_sql_pagination:
             limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        
        # Standard Grouping (group_by_client removido — drill-down substitui)
        key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'))"
        group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')"

        # Query base
        query = f"""
        WITH {opp_cte}
        agg_chave AS (
            SELECT
                {key_expr} as chave,
                COALESCE(peca, 'SEM PEÇA') as peca,
                COALESCE(tipo_mo, 'SEM MO') as tipo_mo,
                COUNT(DISTINCT numero_os) as qtd_os,
                COUNT(*) as total_itens,
                
                -- Taxa de regulação RI: mensagem_log indica aprovação automática
                SUM(CASE WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                              OR LOWER(mensagem_log) LIKE '%aprovacao automatica%' THEN 1 ELSE 0 END) as itens_aprovacao_auto,
                
                -- SEM REGULAÇÃO: aprovação não-automática (humana)
                SUM(CASE WHEN NOT (LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                                   OR LOWER(mensagem_log) LIKE '%aprovacao automatica%') THEN 1 ELSE 0 END) as itens_aprovacao_humana,
                
                PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) as p70,
                AVG(COALESCE(valor_aprovado, 0)) as valor_medio
            FROM {source_table} c
            WHERE {where_sql}
            GROUP BY {group_by_expr}
            {opp_having}
        ),
        -- Benchmark via Pricing Engine (P70 do valor total por tipo_mo)
        {_benchmark_cte(conn)}
        
        SELECT 
            a.chave,
            a.peca,
            a.tipo_mo,
            a.qtd_os,
            a.total_itens,
            a.itens_aprovacao_auto as itens_automaticos,
            
            -- Compatibilidade com colunas antigas (zeradas pois não usamos mais)
            0 as itens_tipo_mo_auto,
            0 as itens_peca_intercambiavel,
            0 as itens_cliente_pacote,
            
            CASE 
                WHEN a.total_itens > 0 
                THEN (a.itens_aprovacao_auto::FLOAT / a.total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao,
            
            -- % Aprovação Humana
            CASE 
                WHEN a.total_itens > 0 
                THEN (a.itens_aprovacao_humana::FLOAT / a.total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao_humana,
            
            a.p70,
            a.valor_medio,
            
            -- Benchmark do Pricing Engine (P70 total por tipo_mo)
            COALESCE(bt.avg_p70_total, 0) as benchmark,
            CASE WHEN bt.avg_p70_total IS NOT NULL THEN true ELSE false END as has_ref_mo,
            true as has_ref_peca
        FROM agg_chave a
        LEFT JOIN benchmark_total bt ON a.tipo_mo = bt.tipo_mo
        ORDER BY {opp_order}
        {limit_clause}
        """
        
        # Executar com cursor isolado
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        if df.empty:
            
            return []
        
        # Converter para lista de dicts
        dados = df.to_dict('records')
        
        # Processar com o farol engine (adiciona cor, score, sugestão)
        dados_com_farol = processar_dados_farol(dados)
        
        # ORDENAÇÃO: Ordenar por prioridade (Score DESC)
        try:
            dados_com_farol.sort(key=lambda x: x.get('score_prioridade', 0), reverse=True)
        except Exception as sort_err:
            print(f"[REPO_FAROL_TABLE] Erro ao ordenar: {sort_err}")
            
        # FILTRO DE PRIORIDADE (Pós-processamento)
        if filter_prioridade:
            # Normalizar input (lista ou string)
            if isinstance(filter_prioridade, str):
                filter_prioridade = [filter_prioridade]
            
            # Formatar para lowercase para comparação (vermelho, amarelo, verde)
            target_colors = [c.lower() for c in filter_prioridade]
            
            # Filtrar
            dados_com_farol = [d for d in dados_com_farol if d.get("farol_cor", "").lower() in target_colors]
            
            
            # Aplicar paginação manual agora (já que não foi feita no SQL)
            # Nota: O total_pages no callback vai precisar considerar isso se quiser ser preciso, 
            # mas para MVP vamos paginar o resultado filtrado.
            start = (page - 1) * page_size
            end = start + page_size
            dados_com_farol = dados_com_farol[start:end]
        
        
        return dados_com_farol
        
    except Exception as e:
        print(f"[REPO_FAROL_TABLE] Erro na tabela farol: {e}")
        import traceback
        traceback.print_exc()
        return []


@safe_memoize(timeout=300)
def get_farol_total_count(filters: dict = None, only_opportunities: bool = False) -> int:
    """
    Retorna o total de chaves (Peça + MO) agregadas para calcular paginação.
    
    Args:
        filters: Dicionário de filtros
        only_opportunities: Se True, conta apenas chaves com P70 <= R$ 1.500

    
    Returns:
        Total de chaves únicas
    """
    conn = get_connection()
    
    if conn is None:
        return 0
    
    try:
        cursor = conn.cursor()
        
        where_clauses = ["COALESCE(data_transacao, data_aprovacao_os) IS NOT NULL", "status_os != 'CANCELADA'"]
        
        if filters:
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
            
            if filters.get("chaves"):
                chaves_escaped = "', '".join([c.replace("'", "''") for c in filters["chaves"]])
                where_clauses.append(f"CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) IN ('{chaves_escaped}')")
        
        where_sql = " AND ".join(where_clauses)
        
        having_clause = ""
        opp_cte = ""
        source_table = "ri_corretiva_detalhamento"
        if only_opportunities:
            # Contar chaves com regulacao RI < 80% (Amarelo + Vermelho)
            having_clause = """HAVING (SUM(CASE WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                                                    OR LOWER(mensagem_log) LIKE '%aprovacao automatica%' THEN 1 ELSE 0 END)::FLOAT 
                              / NULLIF(COUNT(*), 0)) * 100 < 80"""
        
        # Standard Grouping (group_by_client removido — drill-down substitui)
        group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')"
        key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'))"

        query = f"""
        SELECT COUNT(*) as total FROM (
            WITH {opp_cte}
            src AS (
                SELECT 
                    {key_expr} as chave
                FROM {source_table}
                WHERE {where_sql}
                GROUP BY {group_by_expr}
                {having_clause}
            )
            SELECT * FROM src
        ) subq
        """
        
        result = cursor.execute(query).fetchone()
        cursor.close()
        
        total = result[0] if result else 0
        
        return total
        
    except Exception as e:
        print(f"[REPO_FAROL_TABLE] Erro ao contar chaves: {e}")
        return 0


@safe_memoize(timeout=300)
def get_farol_stats_full(filters: dict = None) -> dict:
    """
    Calcula as estatísticas de Farol (Verde/Amarelo/Vermelho) sobre TODO o dataset.
    NÃO POSSUI LIMIT, diferente da tabela que limita a 100.
    
    Returns:
        Dict com {verde: int, amarelo: int, vermelho: int, total: int}
    """
    conn = get_connection()
    if conn is None:
        return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}

    try:
        cursor = conn.cursor()
        
        # Reutiliza lógica de filtros
        where_clauses = []
        if filters and filters.get("clientes"):
            clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
            where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Query usando peca_aprovada (peca_aprovada=FALSE = RI negociou = BOM)
        query = f"""
        WITH 
        agg_chave AS (
            SELECT
                CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) as chave,
                COALESCE(peca, 'SEM PEÇA') as peca,
                COALESCE(tipo_mo, 'SEM MO') as tipo_mo,
                COUNT(DISTINCT numero_os) as qtd_os,
                COUNT(*) as total_itens,
                
                -- Taxa de regulação RI: mensagem_log indica aprovação automática
                SUM(CASE WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                              OR LOWER(mensagem_log) LIKE '%aprovacao automatica%' THEN 1 ELSE 0 END) as itens_aprovacao_auto,
                
                PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) as p70,
                AVG(COALESCE(valor_aprovado, 0)) as valor_medio
            FROM ri_corretiva_detalhamento c
            WHERE {where_sql}
            GROUP BY COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')
        ),
        -- Benchmark via Pricing Engine (P70 total por tipo_mo)
        {_benchmark_cte(conn)}
        SELECT 
            a.chave,
            a.qtd_os,
            a.total_itens,
            a.itens_aprovacao_auto as itens_automaticos,
            CASE 
                WHEN a.total_itens > 0 THEN (a.itens_aprovacao_auto::FLOAT / a.total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao,
            a.p70,
            a.valor_medio,
            COALESCE(bt.avg_p70_total, 0) as benchmark,
            CASE WHEN bt.avg_p70_total IS NOT NULL THEN true ELSE false END as has_ref_mo,
            true as has_ref_peca
        FROM agg_chave a
        LEFT JOIN benchmark_total bt ON a.tipo_mo = bt.tipo_mo
        """
        
        df = cursor.execute(query).fetchdf()
        cursor.close()
        
        if df.empty:
            return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}
            
        dados = df.to_dict('records')
        
        # Processar engine para classificar cada linha
        dados_processados = processar_dados_farol(dados)
        
        # Calcular resumo
        resumo = get_resumo_farois(dados_processados)
        
        
        return resumo

    except Exception as e:
        print(f"[REPO_FAROL_TABLE] Erro ao calcular stats full: {e}")
        return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}


def get_farol_resumo(filters: dict = None) -> dict:
    """
    Retorna contagem de farois para os cards de resumo.
    """
    dados = get_farol_table_data(filters)
    
    
    # Verificar se os dados têm a chave farol_cor
    if not dados:
        return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}

    return get_resumo_farois(dados)


# =============================================================================
# LÓGICA DE TENDÊNCIAS (TREND INDICATORS)
# =============================================================================

import os
import json
import tempfile

# Arquivo para persistir o estado anterior (snapshot)
# Arquivo para persistir o estado anterior (snapshot)
# MODIFICATION: Use persistent data directory instead of tempfile for reliable history
VOLUME_PATH = "/Volumes/main/default/ri_dashboard_data"
LOCAL_DATA_DIR = os.path.join(os.getcwd(), "data")

if os.path.exists("/Volumes"):
    DATA_DIR = VOLUME_PATH
else:
    DATA_DIR = LOCAL_DATA_DIR

try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

STATS_SNAPSHOT_FILE = os.path.join(DATA_DIR, "farol_stats_snapshot.json")

def save_current_stats_as_previous():
    """
    Salva o estado ATUAL das estatísticas como 'anterior' para comparação futura.
    Deve ser chamado ANTES de processar novos arquivos.
    """
    try:
        # Obter stats atuais (full)
        current_stats = get_farol_stats_full()
        
        # Salvar em JSON
        with open(STATS_SNAPSHOT_FILE, 'w') as f:
            json.dump(current_stats, f)
            
            
        return True
    except Exception as e:
        print(f"[TRENDS] Erro ao salvar snapshot: {e}")
        return False

def get_farol_stats_with_trend() -> dict:
    """
    Retorna as estatísticas atuais enriquecidas com a tendência (delta %)
    comparando o mês mais recente com o mês anterior.
    
    Returns:
        Dict com estrutura:
        {
            "verde": {"value": 100, "trend": 5.2, "direction": "up"},
            "amarelo": {"value": 50, "trend": -2.0, "direction": "down"},
            ...
        }
    """
    conn = get_connection()
    if conn is None:
        return {k: {"value": 0, "trend": 0.0, "direction": "neutral"} for k in ["verde", "amarelo", "vermelho", "total"]}
    
    try:
        cursor = conn.cursor()
        
        # 1. Descobrir os meses com dados (excluindo mês corrente = parcial)
        from datetime import date as _date
        import pandas as pd
        today = _date.today()
        current_month_start = pd.Timestamp(today.year, today.month, 1)
        
        months_query = """
        SELECT DISTINCT date_trunc('month', data_transacao) as mes
        FROM ri_corretiva_detalhamento
        WHERE data_transacao IS NOT NULL
        ORDER BY mes DESC
        LIMIT 5
        """
        df_months = cursor.execute(months_query).fetchdf()
        cursor.close()
        
        if df_months.empty:
            return {k: {"value": 0, "trend": 0.0, "direction": "neutral"} for k in ["verde", "amarelo", "vermelho", "total"]}
        
        # Normalizar timezone para comparação
        df_months['mes'] = pd.to_datetime(df_months['mes']).dt.tz_localize(None)
        
        # Filtrar meses COMPLETOS (excluir mês corrente que é parcial)
        meses_completos = df_months[df_months['mes'] < current_month_start]
        
        # Stats totais (todos os meses — valor exibido no card)
        current = get_farol_stats_full()
        
        # 2. Comparar os 2 últimos meses COMPLETOS para trend justo
        has_valid_previous = False
        previous = {}
        current_month_stats = {}
        
        if len(meses_completos) >= 2:
            mes_recente = meses_completos.iloc[0]['mes']
            mes_anterior = meses_completos.iloc[1]['mes']
            current_month_stats = _get_farol_stats_for_period(conn, mes_recente)
            previous = _get_farol_stats_for_period(conn, mes_anterior)
            if previous.get("total", 0) > 0:
                has_valid_previous = True
        elif len(meses_completos) == 1:
            mes_recente = meses_completos.iloc[0]['mes']
            current_month_stats = _get_farol_stats_for_period(conn, mes_recente)
        
        # 3. Calcular deltas (mês completo recente vs mês completo anterior)
        result = {}
        keys = ["verde", "amarelo", "vermelho", "total"]
        
        for k in keys:
            # O VALUE exibido é o TOTAL (todos os meses)
            total_val = current.get(k, 0)
            # TREND compara os 2 últimos meses COMPLETOS (ignora mês parcial)
            curr_month_val = current_month_stats.get(k, 0)
            prev_val = previous.get(k, 0)
            
            trend_pct = 0.0
            direction = "neutral"
            
            if has_valid_previous and prev_val > 0:
                trend_pct = ((curr_month_val - prev_val) / prev_val) * 100
                
                if trend_pct > 0.5:
                    direction = "up"
                elif trend_pct < -0.5:
                    direction = "down"
                
            result[k] = {
                "value": total_val,
                "trend": round(trend_pct, 1),
                "direction": direction
            }
            
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback: retornar stats sem trend
        current = get_farol_stats_full()
        return {k: {"value": current.get(k, 0), "trend": 0.0, "direction": "neutral"} for k in ["verde", "amarelo", "vermelho", "total"]}


def _get_farol_stats_for_period(conn, mes_ref) -> dict:
    """
    Calcula stats de farol (verde/amarelo/vermelho) para um mês específico.
    
    Args:
        conn: Conexão DuckDB
        mes_ref: datetime do mês de referência (primeiro dia do mês)
    """
    try:
        cursor = conn.cursor()
        
        query = f"""
        WITH 
        agg_chave AS (
            SELECT
                CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) as chave,
                COALESCE(peca, 'SEM PEÇA') as peca,
                COALESCE(tipo_mo, 'SEM MO') as tipo_mo,
                COUNT(DISTINCT numero_os) as qtd_os,
                COUNT(*) as total_itens,
                -- Taxa de regulação RI: mensagem_log indica aprovação automática
                SUM(CASE WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                              OR LOWER(mensagem_log) LIKE '%aprovacao automatica%' THEN 1 ELSE 0 END) as itens_aprovacao_auto,
                PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) as p70,
                AVG(COALESCE(valor_aprovado, 0)) as valor_medio
            FROM ri_corretiva_detalhamento
            WHERE date_trunc('month', data_transacao) = ?
            GROUP BY COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')
        ),
        -- Benchmark via Pricing Engine (P70 total por tipo_mo)
        {_benchmark_cte(conn)}
        SELECT 
            a.chave,
            a.qtd_os,
            a.total_itens,
            a.itens_aprovacao_auto as itens_automaticos,
            CASE 
                WHEN a.total_itens > 0 THEN (a.itens_aprovacao_auto::FLOAT / a.total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao,
            a.p70,
            a.valor_medio,
            COALESCE(bt.avg_p70_total, 0) as benchmark,
            CASE WHEN bt.avg_p70_total IS NOT NULL THEN true ELSE false END as has_ref_mo,
            true as has_ref_peca
        FROM agg_chave a
        LEFT JOIN benchmark_total bt ON a.tipo_mo = bt.tipo_mo
        """
        
        df = cursor.execute(query, [mes_ref]).fetchdf()
        cursor.close()
        
        if df.empty:
            return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}
            
        dados = df.to_dict('records')
        dados_processados = processar_dados_farol(dados)
        resumo = get_resumo_farois(dados_processados)
        
        return resumo
        
    except Exception as e:
        return {"verde": 0, "amarelo": 0, "vermelho": 0, "total": 0}


def _initialize_snapshot_if_missing():
    """Legacy: mantido para compatibilidade mas não mais necessário."""
    pass



# =============================================================================
# DRILL-DOWN (Detalhes de uma chave específica)
# =============================================================================

@safe_memoize(timeout=180)
def get_drill_down_chave(peca: str, tipo_mo: str, clientes: tuple = None, data_inicio: str = None, data_fim: str = None, limit: int = 50) -> pd.DataFrame:
    """
    Retorna detalhes de OSs para uma chave específica (Peça + Tipo MO).
    
    Args:
        clientes: tupla de nomes de clientes (hashable para cache).
        data_inicio: filtro data início (YYYY-MM-DD). Se None, sem filtro.
        data_fim: filtro data fim (YYYY-MM-DD). Se None, sem filtro.
    """
    conn = get_connection()
    
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = f"""
        SELECT 
            numero_os,
            nome_cliente,
            valor_total,
            valor_aprovado,
            data_transacao,
            -- Aprovador (nome real, NULL se não informado)
            CASE 
                WHEN nome_aprovador IS NULL 
                  OR TRIM(nome_aprovador) = '' 
                  OR UPPER(TRIM(nome_aprovador)) IN ('NAO INFORMADO', 'NÃO INFORMADO')
                THEN NULL
                ELSE nome_aprovador
            END as aprovador,
            -- Negociador: quem fez o desconto (se houve redução de preço)
            CASE 
                WHEN COALESCE(valor_aprovado, 0) < COALESCE(valor_total, 0) - 0.01
                THEN COALESCE(NULLIF(TRIM(nome_aprovador), ''), 'Sistema')
                ELSE NULL
            END as negociador,
            -- Aprovação automática (via silent_order_pbi — lógica PBI)
            -- FIX 2026-03-25: Migrado de mensagem_log → silent_order_pbi
            CASE 
                WHEN COALESCE(silent_order_pbi, '') = 'Sim' THEN TRUE
                WHEN LOWER(mensagem_log) LIKE '%aprova__o autom_tica%'
                  OR LOWER(mensagem_log) LIKE '%aprovacao automatica%'
                THEN TRUE
                ELSE FALSE
            END as aprovacao_automatica,
            mensagem_log
        FROM ri_corretiva_detalhamento
        WHERE peca = '{peca}' AND tipo_mo = '{tipo_mo}'
          AND status_os != 'CANCELADA'
          AND COALESCE(valor_aprovado, 0) > 0
        """
        # Filtrar por clientes se fornecido
        if clientes:
            placeholders = ", ".join([f"'{c}'" for c in clientes])
            query += f" AND nome_cliente IN ({placeholders})"
        
        # Filtrar por período
        if data_inicio:
            query += f" AND data_transacao >= '{data_inicio}'"
        if data_fim:
            query += f" AND data_transacao <= '{data_fim}'"
        
        query += f"""
        ORDER BY data_transacao DESC
        LIMIT {limit}
        """
        
        df = conn.execute(query).fetchdf()
        return df
        
    except Exception as e:
        print(f"[REPO_FAROL_TABLE] Erro no drill-down: {e}")
        return pd.DataFrame()

