# -*- coding: utf-8 -*-
"""
Repositories Package - Central de acesso a queries modulares

Este pacote agrupa todos os repositórios por sessão do sistema:
- repo_dashboard: Queries do Dashboard principal
- repo_farol_chart: Query do gráfico do Farol
- repo_farol_table: Queries da tabela e cards do Farol
- repo_logs_corretiva: Queries dos logs de não aprovação
- repo_filters: Queries para filtros e dropdowns

Author: Luiz Eduardo Carvalho
"""

# Dashboard
from backend.repositories.repo_dashboard import (
    get_ri_evolution_data,
    refresh_pricing_data,
    check_database_status
)

# Farol - Chart
from backend.repositories.repo_farol_chart import (
    get_ri_corretivas_chart
)

# Farol - Table & Cards
from backend.repositories.repo_farol_table import (
    get_farol_table_data,
    get_farol_resumo,
    get_drill_down_chave
)

# Logs Corretiva (Não Aprovação)
from backend.repositories.repo_logs_corretiva import (
    get_logs_nao_aprovacao,
    get_logs_filter_options
)

# Filters
from backend.repositories.repo_filters import (
    get_distinct_clients_corretiva,
    get_distinct_clients_preventiva,
    get_distinct_months,
    get_distinct_pecas,
    get_distinct_tipo_mo,
    get_distinct_planos,
    get_value_range_stats,
    get_tooltip_data_corretiva,
    get_distinct_chaves
)

# Exports públicos
__all__ = [
    # Dashboard
    'get_ri_evolution_data',
    'refresh_pricing_data',
    'check_database_status',
    # Farol Chart
    'get_ri_corretivas_chart',
    # Farol Table
    'get_farol_table_data',
    'get_farol_resumo',
    'get_drill_down_chave',
    # Logs Corretiva
    'get_logs_nao_aprovacao',
    'get_logs_filter_options',
    # Filters
    'get_distinct_clients_corretiva',
    'get_distinct_clients_preventiva',
    'get_distinct_months',
    'get_distinct_pecas',
    'get_distinct_tipo_mo',
    'get_distinct_planos',
    'get_value_range_stats',
    'get_tooltip_data_corretiva',
    'get_distinct_chaves'
]

