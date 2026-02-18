# -*- coding: utf-8 -*-
"""
Repository Farol Table - Queries para a tabela e cards do Farol

Author: Luiz Eduardo Carvalho
"""

import pandas as pd
from backend.repositories.repo_base import get_connection, safe_memoize
from engine.farol_engine import processar_dados_farol, get_resumo_farois


# NOTA: Cache reativado após correções. Monitorar comportamento com filtros vazios.
@safe_memoize(timeout=300)
def get_farol_table_data(filters: dict = None, page: int = 1, page_size: int = 10, only_opportunities: bool = False, group_by_client: bool = False) -> list:
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
        
        # Verifica se tem filtro de prioridade -> Se sim, precisamos buscar TUDO para filtrar no Python
        filter_prioridade = filters.get("prioridade") if filters else None
        
        # Se tem filtro de prioridade, removemos paginação SQL para aplicar depois
        use_sql_pagination = filter_prioridade is None
        
        limit_clause = ""
        if use_sql_pagination:
             limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        
        # Decide Key Logic
        if group_by_client:
            # Group by Key AND Client
            key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'), ' | ', COALESCE(nome_cliente, 'N/A'))"
            group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO'), COALESCE(nome_cliente, 'N/A')"
        else:
            # Standard Grouping
            key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'))"
            group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')"

        # Query base para calcular "Real Approval" usando nome_aprovador
        query = f"""
        WITH 
        agg_chave AS (
            SELECT
                {key_expr} as chave,
                COALESCE(peca, 'SEM PEÇA') as peca,
                COALESCE(tipo_mo, 'SEM MO') as tipo_mo,
                COUNT(DISTINCT numero_os) as qtd_os,
                COUNT(*) as total_itens,
                
                -- CRITÉRIO CORRETO: Itens com status_os APROVADA
                -- Mede a taxa real de aprovação dos itens
                SUM(CASE WHEN status_os = 'APROVADA' THEN 1 ELSE 0 END) as itens_aprovacao_auto,
                
                -- ITENS NÃO APROVADOS: Reprovados, Cancelados ou Pendentes
                SUM(CASE WHEN status_os != 'APROVADA' OR status_os IS NULL THEN 1 ELSE 0 END) as itens_aprovacao_humana,
                
                PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) as p70,
                AVG(COALESCE(valor_aprovado, 0)) as valor_medio
            FROM ri_corretiva_detalhamento c
            WHERE {where_sql}
            GROUP BY {group_by_expr}
            {"HAVING PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) <= 1500" if only_opportunities else ""}
        )
        
        SELECT 
            chave,
            peca,
            tipo_mo,
            qtd_os,
            total_itens,
            itens_aprovacao_auto as itens_automaticos,
            
            -- Compatibilidade com colunas antigas (zeradas pois não usamos mais)
            0 as itens_tipo_mo_auto,
            0 as itens_peca_intercambiavel,
            0 as itens_cliente_pacote,
            
            CASE 
                WHEN total_itens > 0 
                THEN (itens_aprovacao_auto::FLOAT / total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao,
            
            -- % Aprovação Humana
            CASE 
                WHEN total_itens > 0 
                THEN (itens_aprovacao_humana::FLOAT / total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao_humana,
            
            p70,
            valor_medio
        FROM agg_chave
        ORDER BY qtd_os DESC -- Ordenação Inicial (depois reordenamos por Score)
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
def get_farol_total_count(filters: dict = None, only_opportunities: bool = False, group_by_client: bool = False) -> int:
    """
    Retorna o total de chaves (Peça + MO) agregadas para calcular paginação.
    
    Args:
        filters: Dicionário de filtros
        only_opportunities: Se True, conta apenas chaves com P70 <= R$ 1.500
        group_by_client: Se True, agrupa também por cliente
    
    Returns:
        Total de chaves únicas
    """
    conn = get_connection()
    
    if conn is None:
        return 0
    
    try:
        cursor = conn.cursor()
        
        where_clauses = ["COALESCE(data_transacao, data_aprovacao_os) IS NOT NULL"]
        
        if filters:
            if filters.get("clientes"):
                clients_escaped = "', '".join([c.replace("'", "''") for c in filters["clientes"]])
                where_clauses.append(f"nome_cliente IN ('{clients_escaped}')")
            
            if filters.get("chaves"):
                chaves_escaped = "', '".join([c.replace("'", "''") for c in filters["chaves"]])
                where_clauses.append(f"CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) IN ('{chaves_escaped}')")
        
        where_sql = " AND ".join(where_clauses)
        
        having_clause = ""
        if only_opportunities:
            having_clause = "HAVING PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) <= 1500"
        
        # Decide Grouping Logic
        if group_by_client:
            group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO'), COALESCE(nome_cliente, 'N/A')"
            # Note: The key construction in inner SELECT matters less for COUNT(*), 
            # but GROUP BY must match to count unique groups
            key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'), ' | ', COALESCE(nome_cliente, 'N/A'))"
        else:
            group_by_expr = "COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')"
            key_expr = "CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO'))"

        query = f"""
        SELECT COUNT(*) as total FROM (
            SELECT 
                {key_expr} as chave
            FROM ri_corretiva_detalhamento
            WHERE {where_sql}
            GROUP BY {group_by_expr}
            {having_clause}
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
        
        # Query usando a MESMA lógica da tabela (baseada em nome_aprovador)
        query = f"""
        WITH 
        agg_chave AS (
            SELECT
                CONCAT(COALESCE(peca, 'SEM PEÇA'), ' + ', COALESCE(tipo_mo, 'SEM MO')) as chave,
                COUNT(DISTINCT numero_os) as qtd_os,
                COUNT(*) as total_itens,
                
                -- CRITÉRIO CORRETO: Itens com status_os APROVADA
                SUM(CASE WHEN status_os = 'APROVADA' THEN 1 ELSE 0 END) as itens_aprovacao_auto,
                
                PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY COALESCE(valor_aprovado, 0)) as p70,
                AVG(COALESCE(valor_aprovado, 0)) as valor_medio
            FROM ri_corretiva_detalhamento c
            WHERE {where_sql}
            GROUP BY COALESCE(peca, 'SEM PEÇA'), COALESCE(tipo_mo, 'SEM MO')
        )
        SELECT 
            chave,
            qtd_os,
            total_itens,
            itens_aprovacao_auto as itens_automaticos,
            CASE 
                WHEN total_itens > 0 THEN (itens_aprovacao_auto::FLOAT / total_itens) * 100 
                ELSE 0 
            END as pct_aprovacao,
            p70,
            valor_medio
        FROM agg_chave
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
    em relação ao snapshot anterior.
    
    Returns:
        Dict com estrutura:
        {
            "verde": {"value": 100, "trend": 5.2, "direction": "up"},
            "amarelo": {"value": 50, "trend": -2.0, "direction": "down"},
            ...
        }
    """
    # 0. Initial check: If no snapshot exists, create one now to serve as baseline
    _initialize_snapshot_if_missing()

    # 1. Obter stats atuais
    current = get_farol_stats_full()
    
    # 2. Carregar stats anteriores
    previous = {}
    has_valid_previous = False
    
    if os.path.exists(STATS_SNAPSHOT_FILE):
        try:
            with open(STATS_SNAPSHOT_FILE, 'r') as f:
                previous = json.load(f)
                # Verificar se o snapshot tem dados válidos (não vazio, com total > 0)
                if previous.get("total", 0) > 0:
                    has_valid_previous = True
        except Exception as e:
            print(f"[TRENDS] Erro ao ler snapshot: {e}")
    
    # 3. Calcular deltas
    result = {}
    keys = ["verde", "amarelo", "vermelho", "total"]
    
    for k in keys:
        curr_val = current.get(k, 0)
        prev_val = previous.get(k, 0)
        
        trend_pct = 0.0
        direction = "neutral"
        
        # Só calcula tendência se houver snapshot anterior válido
        if has_valid_previous and prev_val > 0:
            trend_pct = ((curr_val - prev_val) / prev_val) * 100
            
            if trend_pct > 0.5:  # Threshold mínimo para considerar "movimento"
                direction = "up"
            elif trend_pct < -0.5:
                direction = "down"
        # Se não tem histórico válido, fica neutro (não mostra seta)
            
        result[k] = {
            "value": curr_val,
            "trend": round(trend_pct, 1),
            "direction": direction
        }
        
    return result

def _initialize_snapshot_if_missing():
    """
    Internal helper: checks if snapshot exists. If not, creates one from current DB.
    This ensures we have a baseline for the NEXT sync.
    """
    if not os.path.exists(STATS_SNAPSHOT_FILE):
        print("[TRENDS] Snapshot missing. Initializing baseline from current DB...")
        save_current_stats_as_previous()



# =============================================================================
# DRILL-DOWN (Detalhes de uma chave específica)
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
        WHERE peca = '{peca}' AND tipo_mo = '{tipo_mo}'
        ORDER BY data_transacao DESC
        LIMIT {limit}
        """
        
        df = conn.execute(query).fetchdf()
        return df
        
    except Exception as e:
        print(f"[REPO_FAROL_TABLE] Erro no drill-down: {e}")
        return pd.DataFrame()
