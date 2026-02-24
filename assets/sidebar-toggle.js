/**
 * Sidebar Toggle - Pure JavaScript (Zero Dash Callbacks)
 * 
 * Intercepta o clique no botão de toggle e manipula CSS diretamente,
 * sem qualquer envolvimento do Dash callback system.
 * Isso elimina o "UPDATING" que ocorria por event bubbling.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Aguarda o Dash renderizar os componentes
    const observer = new MutationObserver(function(mutations, obs) {
        const toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            obs.disconnect(); // Para de observar após encontrar

            toggleBtn.addEventListener('click', function(e) {
                // CRÍTICO: impede que o clique propague para NavLinks ou qualquer pai
                e.stopPropagation();
                e.preventDefault();

                const sidebar = document.getElementById('sidebar');
                if (!sidebar) return;

                if (sidebar.classList.contains('collapsed')) {
                    sidebar.classList.remove('collapsed');
                } else {
                    sidebar.classList.add('collapsed');
                }
            });
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
