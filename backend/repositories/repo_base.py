# -*- coding: utf-8 -*-
"""
Repository Base - Funções auxiliares compartilhadas entre repositories

Author: Luiz Eduardo Carvalho
"""

from database import get_connection, get_readonly_connection
from backend.cache_config import cache, safe_memoize

# Mapa de meses em português (compartilhado)
MONTH_MAP = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março',
    4: 'abril', 5: 'maio', 6: 'junho',
    7: 'julho', 8: 'agosto', 9: 'setembro',
    10: 'outubro', 11: 'novembro', 12: 'dezembro'
}

MONTH_NAMES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março',
    4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro',
    10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}



def safe_sql_in_list(values):
    """Gera IN clause segura com validacao anti-injection.
    Usado quando ? placeholders sao impraticaveis (subqueries replicadas).
    Valores vem de dropdowns internos - defense-in-depth."""
    safe = []
    for v in values:
        s = str(v).strip()
        if not s:
            continue
        # Bloqueia tentativas obvias de injection
        if any(ch in s for ch in [';', '--', '/*', '*/']):
            continue
        safe.append(s.replace("'", "''"))
    if not safe:
        return "'__NEVER_MATCH__'"
    return "'" + "', '".join(safe) + "'"


def build_in_clause(values: list) -> tuple:
    """
    Gera placeholders parametrizados para clausula IN do DuckDB.
    Retorna (sql_fragment, params_list).
    Exemplo: build_in_clause(["A", "B"]) -> ("?, ?", ["A", "B"])
    Se lista vazia, retorna fragmento que nunca da match (1=0 guard).
    """
    if not values:
        return "NULL", []  # IN (NULL) = nunca match (safe empty guard)
    placeholders = ", ".join(["?"] * len(values))
    return placeholders, list(values)


def build_where_clause(filters: dict, table_alias: str = "") -> str:
    """
    Constrói cláusula WHERE baseada nos filtros.
    
    Args:
        filters: dict com 'periodos', 'clientes', etc.
        table_alias: prefixo de tabela para colunas (ex: 'c.')
    
    Returns:
        String com cláusula WHERE (sem o 'WHERE')
    """
    where_clauses = []
    prefix = f"{table_alias}." if table_alias else ""
    
    if filters:
        if filters.get("periodos"):
            period_clauses = []
            for p in filters["periodos"]:
                try:
                    year, month = p.split("-")
                    period_clauses.append(
                        f"(YEAR({prefix}data_transacao) = {int(year)} AND MONTH({prefix}data_transacao) = {int(month)})"
                    )
                except Exception:
                    pass
            if period_clauses:
                where_clauses.append(f"({' OR '.join(period_clauses)})")
        
        if filters.get("clientes"):
            placeholders, params = build_in_clause(filters["clientes"])
            where_clauses.append(f"{prefix}nome_cliente IN ({placeholders})")
            # NOTA: params devem ser passados ao execute() pelo chamador
    
    return " AND ".join(where_clauses) if where_clauses else "1=1"


# Re-export para conveniência
__all__ = [
    'get_connection',
    'get_readonly_connection',
    'cache',
    'safe_memoize',
    'MONTH_MAP',
    'MONTH_NAMES',
    'safe_sql_in_list',
    'build_in_clause',
    'build_where_clause',
]
