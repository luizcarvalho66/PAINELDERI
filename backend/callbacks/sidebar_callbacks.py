"""
Sidebar Toggle - Desativado.

A lógica do toggle foi movida para JavaScript puro (assets/sidebar-toggle.js)
para evitar qualquer envolvimento do sistema de callbacks do Dash,
eliminando o "UPDATING" causado por event bubbling.

Este arquivo é mantido apenas como placeholder para evitar erros de import.
"""


def register_sidebar_callbacks(app):
    # Nenhum callback registrado.
    # A lógica do toggle está em assets/sidebar-toggle.js (JavaScript puro).
    pass
