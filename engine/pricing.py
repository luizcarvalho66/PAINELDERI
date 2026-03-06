# -*- coding: utf-8 -*-
"""
Motor de Pricing - Cálculo de Medianas para Comparação de Preços

Conforme regras de negócio documentadas em regrasdenegocio.md:
- MDO (Mão de Obra): Chave = tipo_mo + uf + familia_veiculo
- Peças Intercambiáveis: Chave = descricao_peca + complemento_peca + uf
- Peças Não-Intercambiáveis: Chave = descricao_peca + complemento_peca + codigo_veiculo + uf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection

# Configuração mínima de amostras para calcular mediana
MIN_SAMPLES = 3


def generate_pricing_metrics():
    """
    Gera tabelas de referência (medianas) usando DuckDB.
    Deve ser executado após cada sync do Databricks.
    
    Tabelas criadas:
    - ref_mdo: Mediana de valores de Mão de Obra
    - ref_pecas: Mediana de valores de Peças
    """
    print("[PRICING] Gerando tabelas de referência (medianas)...")
    
    conn = get_connection(read_only=False)
    if conn is None:
        print("[PRICING] ERRO: Não foi possível conectar ao banco")
        return False
    
    try:
        # 1. ref_mdo: Mediana de Mão de Obra
        # Chave: tipo_mo + uf + familia_veiculo
        print("[PRICING] Criando ref_mdo (Mão de Obra)...")
        conn.execute("""
            CREATE OR REPLACE TABLE ref_mdo AS
            SELECT
                tipo_mo,
                uf,
                familia_veiculo,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY valor_mo) as mediana_mo,
                percentile_cont(0.7) WITHIN GROUP (ORDER BY valor_mo) as p70_mo,
                AVG(valor_mo) as media_mo,
                COUNT(*) as qtd_registros
            FROM (
                SELECT tipo_mo, uf, familia_veiculo, valor_mo FROM ri_corretiva_detalhamento
                UNION ALL
                SELECT tipo_mo, uf, familia_veiculo, valor_mo FROM ri_preventiva_detalhamento
            ) combined
            WHERE valor_mo IS NOT NULL AND valor_mo > 0
              AND tipo_mo IS NOT NULL AND tipo_mo != 'N/A'
              AND uf IS NOT NULL
            GROUP BY tipo_mo, uf, familia_veiculo
            HAVING COUNT(*) >= ?
        """, [MIN_SAMPLES])
        
        result_mdo = conn.execute("SELECT COUNT(*) FROM ref_mdo").fetchone()[0]
        print(f"[PRICING] ref_mdo: {result_mdo} combinações de referência")
        
        # 2. ref_pecas: Mediana de Peças (Intercambiáveis - sem código veículo)
        # Chave: descricao_peca + complemento_peca + uf
        print("[PRICING] Criando ref_pecas (Peças)...")
        conn.execute("""
            CREATE OR REPLACE TABLE ref_pecas AS
            SELECT
                descricao_peca,
                complemento_peca,
                uf,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY valor_peca) as mediana_peca,
                percentile_cont(0.7) WITHIN GROUP (ORDER BY valor_peca) as p70_peca,
                AVG(valor_peca) as media_peca,
                COUNT(*) as qtd_registros
            FROM (
                SELECT descricao_peca, complemento_peca, uf, valor_peca FROM ri_corretiva_detalhamento
                UNION ALL
                SELECT descricao_peca, complemento_peca, uf, valor_peca FROM ri_preventiva_detalhamento
            ) combined
            WHERE valor_peca IS NOT NULL AND valor_peca > 0
              AND descricao_peca IS NOT NULL
              AND uf IS NOT NULL
            GROUP BY descricao_peca, complemento_peca, uf
            HAVING COUNT(*) >= ?
        """, [MIN_SAMPLES])
        
        result_pecas = conn.execute("SELECT COUNT(*) FROM ref_pecas").fetchone()[0]
        print(f"[PRICING] ref_pecas: {result_pecas} combinações de referência")
        
        # 3. ref_total: Mediana de valor total por tipo_mo + uf + familia
        # Útil para comparação geral
        print("[PRICING] Criando ref_total (Valor Total)...")
        conn.execute("""
            CREATE OR REPLACE TABLE ref_total AS
            SELECT
                tipo_mo,
                uf,
                familia_veiculo,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY valor_aprovado) as mediana_total,
                percentile_cont(0.7) WITHIN GROUP (ORDER BY valor_aprovado) as p70_total,
                AVG(valor_aprovado) as media_total,
                SUM(valor_aprovado) as soma_total,
                COUNT(*) as qtd_registros
            FROM (
                SELECT tipo_mo, uf, familia_veiculo, valor_aprovado FROM ri_corretiva_detalhamento
                UNION ALL
                SELECT tipo_mo, uf, familia_veiculo, valor_aprovado FROM ri_preventiva_detalhamento
            ) combined
            WHERE valor_aprovado IS NOT NULL AND valor_aprovado > 0
              AND uf IS NOT NULL
            GROUP BY tipo_mo, uf, familia_veiculo
            HAVING COUNT(*) >= ?
        """, [MIN_SAMPLES])
        
        result_total = conn.execute("SELECT COUNT(*) FROM ref_total").fetchone()[0]
        print(f"[PRICING] ref_total: {result_total} combinações de referência")
        
        conn.close()
        print("[PRICING] Tabelas de referência geradas com sucesso!")
        return True
        
    except Exception as e:
        print(f"[PRICING] ERRO: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return False


def calcular_economia_os():
    """
    Calcula a economia real por OS comparando valor_aprovado vs mediana.
    A economia é a diferença entre o que seria cobrado (mediana) e o que foi aprovado.
    
    Economia = mediana - valor_aprovado (quando valor_aprovado < mediana)
    """
    print("[PRICING] Calculando economia por OS...")
    
    conn = get_connection(read_only=False)
    if conn is None:
        print("[PRICING] ERRO: Não foi possível conectar ao banco")
        return False
    
    try:
        conn.execute("""
            CREATE OR REPLACE TABLE economia_calculada AS
            SELECT
                c.numero_os,
                c.data_transacao,
                c.tipo_mo,
                c.uf,
                c.familia_veiculo,
                c.nome_cliente,
                c.descricao_peca,
                c.complemento_peca,
                c.valor_mo,
                c.valor_peca,
                c.valor_aprovado,
                c.valor_total,
                c.status_os,
                c.tipo_origem,
                
                -- Referências de MO
                rm.mediana_mo as ref_mediana_mo,
                rm.p70_mo as ref_p70_mo,
                
                -- Referências de Peça
                rp.mediana_peca as ref_mediana_peca,
                rp.p70_peca as ref_p70_peca,
                
                -- Economia de MO (valor de referência - valor cobrado)
                GREATEST(0, COALESCE(rm.mediana_mo, 0) - COALESCE(c.valor_mo, 0)) as economia_mo,
                
                -- Economia de Peça
                GREATEST(0, COALESCE(rp.mediana_peca, 0) - COALESCE(c.valor_peca, 0)) as economia_peca,
                
                -- Economia Total (Negociada + Pricing)
                (
                    GREATEST(0, COALESCE(c.valor_total, 0) - COALESCE(c.valor_aprovado, 0)) + 
                    GREATEST(0, COALESCE(rm.mediana_mo, 0) - COALESCE(c.valor_mo, 0)) + 
                    GREATEST(0, COALESCE(rp.mediana_peca, 0) - COALESCE(c.valor_peca, 0))
                ) as economia_total,
                
                -- Flag: estava acima da mediana?
                CASE WHEN c.valor_mo > COALESCE(rm.mediana_mo, 0) THEN 1 ELSE 0 END as flag_mo_acima_mediana,
                CASE WHEN c.valor_peca > COALESCE(rp.mediana_peca, 0) THEN 1 ELSE 0 END as flag_peca_acima_mediana
                
            FROM (
                SELECT *, 'CORRETIVA' as tipo_origem FROM ri_corretiva_detalhamento
                UNION ALL
                SELECT *, 'PREVENTIVA' as tipo_origem FROM ri_preventiva_detalhamento
            ) c
            LEFT JOIN ref_mdo rm 
                ON COALESCE(c.tipo_mo, '') = COALESCE(rm.tipo_mo, '')
                AND c.uf = rm.uf 
                AND COALESCE(c.familia_veiculo, '') = COALESCE(rm.familia_veiculo, '')
            LEFT JOIN ref_pecas rp 
                ON COALESCE(c.descricao_peca, '') = COALESCE(rp.descricao_peca, '')
                AND COALESCE(c.complemento_peca, '') = COALESCE(rp.complemento_peca, '')
                AND c.uf = rp.uf
            WHERE c.status_os = 'APROVADA'
              AND (COALESCE(c.valor_mo, 0) > 0 OR COALESCE(c.valor_peca, 0) > 0)
        """)
        
        # Estatísticas
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total_os,
                SUM(economia_mo) as total_economia_mo,
                SUM(economia_peca) as total_economia_peca,
                SUM(economia_total) as total_economia,
                AVG(economia_total) as media_economia
            FROM economia_calculada
        """).fetchone()
        
        print(f"[PRICING] Economia calculada para {stats[0]} OS")
        print(f"[PRICING] Economia Total MO: R$ {stats[1]:,.2f}" if stats[1] else "[PRICING] Economia MO: R$ 0,00")
        print(f"[PRICING] Economia Total Peças: R$ {stats[2]:,.2f}" if stats[2] else "[PRICING] Economia Peças: R$ 0,00")
        print(f"[PRICING] Economia Total: R$ {stats[3]:,.2f}" if stats[3] else "[PRICING] Economia Total: R$ 0,00")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[PRICING] ERRO: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return False


def get_economia_agregada(periodo='mensal'):
    """
    Retorna a economia agregada por período.
    
    Args:
        periodo: 'diario', 'semanal', 'mensal', 'anual'
    
    Returns:
        Lista de dicts com {data, economia_total, economia_mo, economia_peca, qtd_os}
    """
    conn = get_connection(read_only=True)
    if conn is None:
        return []
    
    # Definir a truncagem de data conforme período
    date_trunc = {
        'diario': 'day',
        'semanal': 'week',
        'mensal': 'month',
        'anual': 'year'
    }.get(periodo, 'month')
    
    try:
        result = conn.execute(f"""
            SELECT 
                DATE_TRUNC('{date_trunc}', data_transacao) as periodo,
                SUM(economia_total) as economia_total,
                SUM(economia_mo) as economia_mo,
                SUM(economia_peca) as economia_peca,
                COUNT(*) as qtd_os
            FROM economia_calculada
            WHERE data_transacao IS NOT NULL
            GROUP BY 1
            ORDER BY 1 DESC
            LIMIT 12
        """).fetchall()
        
        conn.close()
        
        return [
            {
                'periodo': str(row[0]),
                'economia_total': float(row[1]) if row[1] else 0,
                'economia_mo': float(row[2]) if row[2] else 0,
                'economia_peca': float(row[3]) if row[3] else 0,
                'qtd_os': int(row[4])
            }
            for row in result
        ]
        
    except Exception as e:
        print(f"[PRICING] ERRO ao buscar economia agregada: {e}")
        if conn:
            conn.close()
        return []


def get_reference_value_mdo(tipo_mo, uf, familia_veiculo=None):
    """
    Retorna o valor de referência (mediana) para Mão de Obra.
    """
    conn = get_connection(read_only=True)
    if conn is None:
        return None
    
    try:
        if familia_veiculo:
            result = conn.execute("""
                SELECT mediana_mo FROM ref_mdo
                WHERE tipo_mo = ? AND uf = ? AND familia_veiculo = ?
            """, [tipo_mo, uf, familia_veiculo]).fetchone()
        else:
            result = conn.execute("""
                SELECT AVG(mediana_mo) FROM ref_mdo
                WHERE tipo_mo = ? AND uf = ?
            """, [tipo_mo, uf]).fetchone()
        
        conn.close()
        return float(result[0]) if result and result[0] else None
        
    except Exception as e:
        print(f"[PRICING] ERRO: {e}")
        if conn:
            conn.close()
        return None


def get_reference_value_peca(descricao_peca, complemento_peca, uf):
    """
    Retorna o valor de referência (mediana) para Peça.
    """
    conn = get_connection(read_only=True)
    if conn is None:
        return None
    
    try:
        result = conn.execute("""
            SELECT mediana_peca FROM ref_pecas
            WHERE descricao_peca = ? 
              AND COALESCE(complemento_peca, '') = COALESCE(?, '')
              AND uf = ?
        """, [descricao_peca, complemento_peca, uf]).fetchone()
        
        conn.close()
        return float(result[0]) if result and result[0] else None
        
    except Exception as e:
        print(f"[PRICING] ERRO: {e}")
        if conn:
            conn.close()
        return None


def run_full_pricing_pipeline():
    """
    Executa o pipeline completo de pricing:
    1. Gera tabelas de referência (medianas)
    2. Calcula economia por OS
    
    Deve ser chamado após cada sync do Databricks.
    """
    print("=" * 60)
    print("[PRICING] Iniciando Pipeline de Pricing")
    print("=" * 60)
    
    # Passo 1: Gerar medianas
    if not generate_pricing_metrics():
        print("[PRICING] FALHA ao gerar métricas de referência")
        return False
    
    # Passo 2: Calcular economia
    if not calcular_economia_os():
        print("[PRICING] FALHA ao calcular economia")
        return False
    
    print("=" * 60)
    print("[PRICING] Pipeline concluído com sucesso!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # Teste standalone
    run_full_pricing_pipeline()
