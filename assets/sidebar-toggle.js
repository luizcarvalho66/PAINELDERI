/**
 * Sidebar Toggle - Pure JavaScript (Zero Dash Callbacks)
 * 
 * Intercepta o clique no botão de toggle e manipula CSS diretamente,
 * sem qualquer envolvimento do Dash callback system.
 * Injeta `sidebar-is-collapsed` no <body> para que CSS possa
 * controlar tooltips e outros elementos dependentes do estado.
 */
document.addEventListener('DOMContentLoaded', function() {
    var observer = new MutationObserver(function(mutations, obs) {
        var toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            obs.disconnect();

            toggleBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();

                var sidebar = document.getElementById('sidebar');
                if (!sidebar) return;

                var isCollapsed = sidebar.classList.toggle('collapsed');

                // Sincroniza o estado com o body para CSS global
                if (isCollapsed) {
                    document.body.classList.add('sidebar-is-collapsed');
                } else {
                    document.body.classList.remove('sidebar-is-collapsed');
                }
            });
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
