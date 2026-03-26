/**
 * modals.js — Notion-style tab switching (zero server roundtrips).
 * Listens for clicks on .notion-tab-btn and swaps .notion-pane visibility.
 */
document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("click", function (e) {
        var btn = e.target.closest(".notion-tab-btn");
        if (!btn) return;

        var targetId = btn.getAttribute("data-target");
        var modal = btn.closest(".notion-modal");
        if (!modal) return;

        // Deactivate all tabs
        modal.querySelectorAll(".notion-tab-btn").forEach(function (b) {
            b.classList.remove("active");
        });
        btn.classList.add("active");

        // Hide all panes, show target
        modal.querySelectorAll(".notion-pane").forEach(function (p) {
            p.classList.remove("active");
        });
        var pane = document.getElementById(targetId);
        if (pane) {
            pane.classList.add("active");
        }
    });
});
