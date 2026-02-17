# -*- coding: utf-8 -*-
"""
Farol Engine - Motor de Scoring para Indicadores de Performance

Este módulo implementa a lógica de classificação do "farol" (semáforo)
para indicar a saúde de cada combinação Peça + Mão de Obra.

Cores:
    🟢 Verde: Performance excelente (≥80% aprovação)
    🟡 Amarelo: Atenção necessária (50-80% aprovação)
    🔴 Vermelho: Ação urgente (<50% ou queda significativa)

Author: Luiz Eduardo Carvalho
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class FarolCor(Enum):
    """Cores possíveis do farol."""
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"


@dataclass
class FarolResult:
    """Resultado da análise do farol para uma chave."""
    cor: FarolCor
    score_prioridade: float  # 0-100, maior = mais prioritário
    sugestao: str
    detalhes: Dict


# =============================================================================
# CONFIGURAÇÕES DO ALGORITMO
# =============================================================================

# Limiares de aprovação (%)
LIMIAR_VERDE = 80.0
LIMIAR_AMARELO = 50.0

# Limiar de queda para alerta vermelho (%)
# Limiar de queda para alerta vermelho (%)
# Limiar de queda para alerta vermelho (%)
LIMIAR_QUEDA_CRITICA = 15.0
# Limiar de Score para ser considerado CRÍTICO (Vermelho)
LIMIAR_SCORE_VERMELHO = 70.0

# Peso para cálculo de prioridade
PESO_APROVACAO = 0.4      # (40%) Aprovação continua sendo o principal
PESO_FINANCEIRO = 0.3     # (30%) Impacto Financeiro (P70)
PESO_VOLUME = 0.2         # (20%) Volume de OSs
PESO_TENDENCIA = 0.1      # (10%) Tendência de queda


# =============================================================================
# FUNÇÕES PRINCIPAIS
# =============================================================================

def calcular_farol(
    pct_aprovacao: float,
    tendencia: float = 0.0,
    qtd_os: int = 0,
    p70: float = 0.0,
    benchmark: float = 0.0
) -> FarolResult:
    """
    Calcula a cor do farol e prioridade para uma chave (Peça + MO).
    """
    # 1. Calcular score de prioridade (Incluindo P70 agora)
    score = calcular_score_prioridade(pct_aprovacao, tendencia, qtd_os, p70)

    # 2. Determinar cor base com Lógica Refinada
    # NOVO: Limiar crítico (abaixo desse % é SEMPRE vermelho, independente de score)
    LIMIAR_CRITICO = 10.0  # Menos de 10% aprovação = Vermelho automático
    
    if pct_aprovacao >= LIMIAR_VERDE:
        cor = FarolCor.VERDE
    elif pct_aprovacao >= LIMIAR_AMARELO:
        cor = FarolCor.AMARELO
    elif pct_aprovacao < LIMIAR_CRITICO:
        # Aprovação crítica (< 10%) - SEMPRE vermelho
        cor = FarolCor.VERMELHO
    else:
        # Aprovação baixa (10-50%): Decidir entre Vermelho e Amarelo pelo Score.
        if score >= LIMIAR_SCORE_VERMELHO:
             cor = FarolCor.VERMELHO  # Crítico: Baixa aprovação + Alto Impacto
        else:
             cor = FarolCor.AMARELO   # Atenção: Baixa aprovação, mas impacto moderado
    
    # Override para vermelho APENAS se houve queda crítica E score alto
    if tendencia <= -LIMIAR_QUEDA_CRITICA and cor != FarolCor.VERMELHO:
        if score >= 60: # Só vira vermelho por queda se tiver relevância
            cor = FarolCor.VERMELHO
    
    # Gerar sugestão
    sugestao = gerar_sugestao(
        cor=cor,
        pct_aprovacao=pct_aprovacao,
        tendencia=tendencia,
        qtd_os=qtd_os,
        p70=p70,
        benchmark=benchmark
    )
    
    return FarolResult(
        cor=cor,
        score_prioridade=score,
        sugestao=sugestao,
        detalhes={
            "pct_aprovacao": round(pct_aprovacao, 2),
            "tendencia": round(tendencia, 2),
            "qtd_os": qtd_os,
            "p70": round(p70, 2),
            "benchmark": round(benchmark, 2)
        }
    )


def calcular_score_prioridade(
    pct_aprovacao: float,
    tendencia: float,
    qtd_os: int,
    p70: float
) -> float:
    """
    Calcula score de 0 a 100 indicando a prioridade de ação.
    Quanto maior, mais urgente.
    
    Fatores:
    - Baixa Aprovação (0% = 100 pts)
    - Alto Custo P70 (> R$ 2000 = 100 pts)
    - Alto Volume (> 500 OSs = 100 pts)
    - Tendência negativa (Queda > 20% = 100 pts)
    """
    # 1. Score Aprovação (Inverso: 0% aprovação = 100 score)
    score_aprovacao = 100.0 - pct_aprovacao
    
    # 2. Score Volume (Logarítmico ou Linear com teto)
    # Assumindo teto de 500 OSs para score maximo de volume
    score_volume = min(100.0, (qtd_os / 500.0) * 100.0)
    
    # 3. Score Tendência (Apenas quedas pontuam)
    if tendencia < 0:
        score_tendencia = min(100.0, (abs(tendencia) / 20.0) * 100.0)
    else:
        score_tendencia = 0.0
        
    # 4. Score Financeiro (P70)
    # Teto R$ 2.000,00 para score máximo
    valor_teto = 2000.0
    score_financeiro = min(100.0, (p70 / valor_teto) * 100.0)
    
    # Média Ponderada
    score_final = (
        (score_aprovacao * PESO_APROVACAO) +
        (score_financeiro * PESO_FINANCEIRO) +
        (score_volume * PESO_VOLUME) +
        (score_tendencia * PESO_TENDENCIA)
    )
    
    return round(max(0.0, min(100.0, score_final)), 1)
    """
    Calcula um score de 0-100 para ordenação por prioridade.
    Maior score = maior prioridade de ação.
    
    Fórmula:
        score = (peso_aprov * score_aprov) + (peso_vol * score_vol) + (peso_tend * score_tend)
    """
    # Score de aprovação: inverso (menor aprovação = maior score)
    score_aprov = max(0, 100 - pct_aprovacao)
    
    # Score de volume: normalizado (assumindo max ~10.000 OSs)
    score_vol = min(100, (qtd_os / 100) * 10)  # Escala logarítmica suave
    
    # Score de tendência: se negativa, contribui para prioridade
    score_tend = max(0, -tendencia) * 2  # Amplifica quedas
    score_tend = min(100, score_tend)
    
    # Combinar com pesos
    score_final = (
        (PESO_APROVACAO * score_aprov) +
        (PESO_VOLUME * score_vol) +
        (PESO_TENDENCIA * score_tend)
    )
    
    return round(min(100, max(0, score_final)), 2)


def gerar_sugestao(
    cor: FarolCor,
    pct_aprovacao: float,
    tendencia: float,
    qtd_os: int,
    p70: float,
    benchmark: float
) -> str:
    """
    Gera uma sugestão de ação textual baseada na análise.
    Estilo profissional sem emojis.
    """
    sugestoes = []
    
    if cor == FarolCor.VERDE:
        return "Performando bem - Manter monitoramento"
    
    if cor == FarolCor.VERMELHO:
        sugestoes.append("Ação urgente necessária")
        
        if pct_aprovacao < 30:
            sugestoes.append("Revisar critérios de aprovação automática")
        
        if tendencia <= -LIMIAR_QUEDA_CRITICA:
            sugestoes.append(f"Investigar queda de {abs(tendencia):.0f}%")
        
        if p70 > benchmark > 0:
            diff_pct = ((p70 - benchmark) / benchmark) * 100
            sugestoes.append(f"P70 {diff_pct:.0f}% acima do benchmark")
    
    elif cor == FarolCor.AMARELO:
        sugestoes.append("Oportunidade de melhoria")
        
        if tendencia < -5:
            sugestoes.append(f"Atenção: tendência de queda ({tendencia:.0f}%)")
        
        if qtd_os > 500:
            sugestoes.append("Alto volume - priorizar análise")
    
    return " | ".join(sugestoes) if sugestoes else "Revisar item"


def processar_dados_farol(dados: List[Dict]) -> List[Dict]:
    """
    Processa uma lista de dados agregados e adiciona classificação do farol.
    
    Args:
        dados: Lista de dicts com campos:
            - chave: str (ex: "PNEU + TROCA")
            - pct_aprovacao: float
            - tendencia: float (opcional)
            - qtd_os: int
            - p70: float
            
    Returns:
        Lista de dicts com campos adicionais: farol_cor, score, sugestao
    """
    resultado = []
    
    # Calcular benchmark como mediana dos P70s
    p70_list = [d.get("p70", 0) for d in dados if d.get("p70", 0) > 0]
    benchmark = sorted(p70_list)[len(p70_list) // 2] if p70_list else 0
    
    for item in dados:
        farol = calcular_farol(
            pct_aprovacao=item.get("pct_aprovacao", 0),
            tendencia=item.get("tendencia", 0),
            qtd_os=item.get("qtd_os", 0),
            p70=item.get("p70", 0),
            benchmark=benchmark
        )
        
        resultado.append({
            **item,
            "farol_cor": farol.cor.value,
            "farol_score": farol.score_prioridade,
            "farol_sugestao": farol.sugestao
        })
    
    # Ordenar por score de prioridade (maior primeiro)
    resultado.sort(key=lambda x: x["farol_score"], reverse=True)
    
    return resultado


def get_resumo_farois(dados_processados: List[Dict]) -> Dict:
    """
    Retorna contagem de cada cor de farol para os cards de resumo.
    """
    contagem = {
        "verde": 0,
        "amarelo": 0,
        "vermelho": 0,
        "total": len(dados_processados)
    }
    
    for item in dados_processados:
        cor = item.get("farol_cor", "amarelo")
        if cor in contagem:
            contagem[cor] += 1
    
    return contagem


# =============================================================================
# LOGICA DE HISTORICO E TENDENCIA (SNAPSHOT MANAGER)
# =============================================================================
try:
    from backend import snapshot_manager
except ImportError:
    # Fallback to avoid import error during direct execution
    snapshot_manager = None

def calculate_kpi_trends(current_counts: Dict) -> Dict:
    """
    Calcula as tendências comparando com o último snapshot.
    Salva o estado atual como novo snapshot.
    
    Args:
        current_counts: Dict com {verde, amarelo, vermelho, total}
        
    Returns:
        Dict enriquecido com chaves '_trend' (ex: verde_trend, total_trend)
        Valores são floats representando a % de mudança.
    """
    if not snapshot_manager:
        return {}
        
    CONTEXT = "farol_kpis"
    
    # 1. Recuperar Penúltimo (O último salvo antes deste)
    # Se salvarmos AGORA, o get_last vai retornar o que acabamos de salvar?
    # R: O snapshot_manager.get_last_snapshot retorna o ULTIMO da lista.
    # Estratégia: Ler -> Comparar -> Salvar.
    
    previous_snapshot = snapshot_manager.get_last_snapshot(CONTEXT)
    
    trends = {}
    
    if previous_snapshot and "metrics" in previous_snapshot:
        prev_metrics = previous_snapshot["metrics"]
        
        for key in ["verde", "amarelo", "vermelho", "total"]:
            val_current = current_counts.get(key, 0)
            val_prev = prev_metrics.get(key, 0)
            
            if val_prev > 0:
                delta = ((val_current - val_prev) / val_prev) * 100.0
            else:
                delta = 0.0 if val_current == 0 else 100.0 # Se era 0 e virou algo, subiu 100% (simbolico)
            
            trends[f"{key}_trend"] = delta
    else:
        # Sem histórico = sem tendência
        trends = {
            "verde_trend": 0.0,
            "amarelo_trend": 0.0,
            "vermelho_trend": 0.0,
            "total_trend": 0.0
        }
    
    # 2. Salvar o Atual (Para ser o 'Previous' da próxima vez)
    snapshot_manager.save_snapshot(CONTEXT, current_counts)
    
    return trends


if __name__ == "__main__":
    # Teste básico
    print("=== Teste Farol Engine ===\n")
    
    # Caso 1: Verde
    r1 = calcular_farol(pct_aprovacao=85, tendencia=5, qtd_os=100)
    print(f"Caso Verde:    {r1.cor.value} | Score: {r1.score_prioridade} | {r1.sugestao}")
    
    # Caso 2: Amarelo
    r2 = calcular_farol(pct_aprovacao=65, tendencia=-3, qtd_os=500)
    print(f"Caso Amarelo:  {r2.cor.value} | Score: {r2.score_prioridade} | {r2.sugestao}")
    
    # Caso 3: Vermelho (baixa aprovação)
    r3 = calcular_farol(pct_aprovacao=35, tendencia=-8, qtd_os=1200, p70=350, benchmark=280)
    print(f"Caso Vermelho: {r3.cor.value} | Score: {r3.score_prioridade} | {r3.sugestao}")
    
    # Caso 4: Vermelho por queda
    r4 = calcular_farol(pct_aprovacao=70, tendencia=-20, qtd_os=800)
    print(f"Queda Crítica: {r4.cor.value} | Score: {r4.score_prioridade} | {r4.sugestao}")
    
    print("\n✅ Engine funcionando!")
