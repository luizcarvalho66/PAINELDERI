
from .navigation_callbacks import register_navigation_callbacks
from .dashboard_callbacks import register_dashboard_callbacks
from .filter_callbacks import register_filter_callbacks
from .sidebar_callbacks import register_sidebar_callbacks
from .corretivas_callbacks import register_corretivas_callbacks
from .callbacks_preventiva import register_preventiva_callbacks
from .activation_callbacks import register_activation_callbacks
from .callbacks_sync import register_sync_callbacks

def register_all_callbacks(app):

    register_navigation_callbacks(app)
    register_dashboard_callbacks(app)
    register_filter_callbacks(app)
    register_sidebar_callbacks(app)
    register_corretivas_callbacks(app)
    register_preventiva_callbacks(app)
    register_activation_callbacks(app)
    register_sync_callbacks(app)
