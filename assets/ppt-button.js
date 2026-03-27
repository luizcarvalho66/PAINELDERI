/**
 * PPT Button — Feedback imediato ao clicar em "Gerar Apresentação"
 * Mostra overlay de loading e desabilita botão ANTES do round-trip ao servidor.
 * Substitui o clientside_callback que causava "Duplicate callback outputs".
 */
(function () {
    "use strict";

    document.addEventListener("click", function (e) {
        var btn = e.target.closest("#btn-generate-ppt-confirm");
        if (!btn || btn.disabled) return;

        // 1. Desabilitar botão e trocar texto
        btn.disabled = true;
        btn.textContent = "Gerando...";

        // 2. Mostrar overlay de loading
        var overlay = document.getElementById("ppt-loading-overlay");
        if (overlay) {
            overlay.style.display = "flex";
        }
    });
})();
