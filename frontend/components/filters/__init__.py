# Filtros Modulares por Painel - RI Dashboard
# Cada painel possui seu próprio conjunto de filtros dedicados

from .filters_common import (
    create_filter_dropdown,
    create_filter_range_slider,
    create_filter_input,
    create_export_button,
    create_filter_card
)

from .filters_corretiva import render_filters_corretiva
from .filters_preventiva import render_filters_preventiva
from .filters_geral import render_filters_geral
