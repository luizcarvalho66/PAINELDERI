/**
 * Premium Chart Tooltip — Edenred RI Dashboard
 * 
 * Tooltip JS puro que escuta plotly_hover diretamente no DOM.
 * NÃO usar dcc.Tooltip (causa ~200ms de delay).
 * 
 * Os charts usam hoverinfo="none" + customdata para passar dados.
 * Z-index: 999999 (acima de tudo)
 */

(function () {
    'use strict';

    // =========================================================================
    // CONFIG
    // =========================================================================
    const TOOLTIP_ID = 'premium-chart-tooltip';
    const OFFSET_X = 15;
    const OFFSET_Y = -10;

    // =========================================================================
    // CREATE TOOLTIP ELEMENT
    // =========================================================================
    function getOrCreateTooltip() {
        let tooltip = document.getElementById(TOOLTIP_ID);
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = TOOLTIP_ID;
            tooltip.style.cssText = `
                position: fixed;
                z-index: 999999;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.15s ease, transform 0.15s ease;
                transform: translateY(4px);
                background: #ffffff;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                padding: 14px 18px;
                font-family: 'Ubuntu', sans-serif;
                font-size: 13px;
                color: #1e293b;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(226, 6, 19, 0.05);
                max-width: 360px;
                line-height: 1.5;
            `;
            document.body.appendChild(tooltip);
        }
        return tooltip;
    }

    // =========================================================================
    // FORMAT HELPERS
    // =========================================================================
    function escapeHTML(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function formatCurrency(value) {
        if (value == null || isNaN(value)) return 'R$ 0';
        const num = Number(value);
        if (Math.abs(num) >= 1e6) return `R$ ${(num / 1e6).toFixed(1)}M`;
        if (Math.abs(num) >= 1e3) return `R$ ${(num / 1e3).toFixed(1)}K`;
        return `R$ ${num.toFixed(0)}`;
    }

    function formatNumber(value) {
        if (value == null || isNaN(value)) return '0';
        return Number(value).toLocaleString('pt-BR');
    }

    function formatPercent(value) {
        if (value == null || isNaN(value)) return '0.00%';
        return `${Number(value).toFixed(2)}%`;
    }

    // =========================================================================
    // BUILD TOOLTIP HTML (RI GERAL — dual-axis chart)
    // =========================================================================
    function buildRIGeralHTML(customdata) {
        // customdata layout:
        //   [0] periodo, [1] economia_text (RI) ou so_count (SO),
        //   [2] os_total, [3] os_corr, [4] os_prev,
        //   [5] ri/so_corr%, [6] ri/so_prev%, [7] parcial,
        //   [8] vol_text, [9] ri/so_geral%, [10] mode ("RI"|"SO")
        const periodo   = escapeHTML(customdata[0] || '');
        const slot1     = escapeHTML(customdata[1]);         // economia (string) ou so_count (int)
        const osTotal   = escapeHTML(customdata[2] || 0);
        const osCorr    = escapeHTML(customdata[3] || 0);
        const osPrev    = escapeHTML(customdata[4] || 0);
        const pctCorr   = escapeHTML(customdata[5]);
        const pctPrev   = escapeHTML(customdata[6]);
        const parcial   = escapeHTML(customdata[7] || '');
        const volText   = escapeHTML(customdata[8] || 'R$ 0');
        const pctGeral  = escapeHTML(customdata[9]);
        const mode      = escapeHTML(customdata[10] || 'RI');

        // ── Header (compartilhado) ──
        const headerHTML = `
            <div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,0.06)">
                <div style="display:flex;align-items:center;gap:6px">
                    <i class="bi bi-calendar2-range" style="color:#64748b;font-size:14px"></i>
                    <span style="font-weight:700;font-size:14px;color:#1e293b">${periodo}</span>
                    ${parcial ? `<span style="color:#f59e0b;font-size:11px;margin-left:auto;background:rgba(245,158,11,0.1);padding:2px 6px;border-radius:4px">${parcial}</span>` : ''}
                </div>
            </div>`;

        if (mode === 'SO') {
            // ══════════════════════════════════════════════
            //  TOOLTIP — SILENT ORDER
            // ══════════════════════════════════════════════
            const soCount = Number(slot1) || 0;
            return `${headerHTML}
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;background:rgba(16,185,129,0.06);padding:6px 10px;border-radius:8px">
                <i class="bi bi-shield-check" style="color:#10b981;font-size:14px"></i>
                <span style="color:#475569;font-weight:600">Silent Order</span>
                <span style="font-weight:800;color:#10b981;margin-left:auto;font-size:15px">${formatPercent(pctGeral)}</span>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(0,0,0,0.06)">
                <div style="flex:1">
                    <div style="color:#64748b;font-size:11px;margin-bottom:2px">Corretiva</div>
                    <div style="font-weight:700;color:#1e293b">${formatPercent(pctCorr)}</div>
                </div>
                <div style="flex:1">
                    <div style="color:#64748b;font-size:11px;margin-bottom:2px">Preventiva</div>
                    <div style="font-weight:700;color:#64748b">${formatPercent(pctPrev)}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr auto;gap:4px 16px;font-size:12px;align-items:center">
                <div style="color:#64748b">OS Automáticas</div>
                <div style="text-align:right;font-weight:700;color:#10b981">${formatNumber(soCount)}</div>
                <div style="color:#64748b;margin-top:4px">OS Total</div>
                <div style="text-align:right;font-weight:600;color:#1e293b;margin-top:4px">${formatNumber(osTotal)}</div>
                <div style="color:#64748b">OS Corretiva</div>
                <div style="text-align:right;color:#475569">${formatNumber(osCorr)}</div>
                <div style="color:#64748b">OS Preventiva</div>
                <div style="text-align:right;color:#475569">${formatNumber(osPrev)}</div>
            </div>`;
        }

        // ══════════════════════════════════════════════
        //  TOOLTIP — RI (SAVING PRICE) — original
        // ══════════════════════════════════════════════
        const economia = slot1 || 'R$ 0';
        return `${headerHTML}
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;background:rgba(226,6,19,0.04);padding:6px 10px;border-radius:8px">
                <i class="bi bi-graph-up-arrow" style="color:#E20613;font-size:14px"></i>
                <span style="color:#475569;font-weight:600">RI Geral</span>
                <span style="font-weight:800;color:#E20613;margin-left:auto;font-size:15px">${formatPercent(pctGeral)}</span>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(0,0,0,0.06)">
                <div style="flex:1">
                    <div style="color:#64748b;font-size:11px;margin-bottom:2px">Corretiva</div>
                    <div style="font-weight:700;color:#1e293b">${formatPercent(pctCorr)}</div>
                </div>
                <div style="flex:1">
                    <div style="color:#64748b;font-size:11px;margin-bottom:2px">Preventiva</div>
                    <div style="font-weight:700;color:#64748b">${formatPercent(pctPrev)}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr auto;gap:4px 16px;font-size:12px;align-items:center">
                <div style="color:#64748b">Vol. Solicitado</div>
                <div style="text-align:right;font-weight:600;color:#1e293b">${volText}</div>
                <div style="color:#64748b">Economia</div>
                <div style="text-align:right;font-weight:600;color:#10b981">${economia}</div>
                <div style="color:#64748b;margin-top:4px">OS Total</div>
                <div style="text-align:right;font-weight:600;color:#1e293b;margin-top:4px">${formatNumber(osTotal)}</div>
                <div style="color:#64748b">OS Corretiva</div>
                <div style="text-align:right;color:#475569">${formatNumber(osCorr)}</div>
                <div style="color:#64748b">OS Preventiva</div>
                <div style="text-align:right;color:#475569">${formatNumber(osPrev)}</div>
            </div>
        `;
    }

    // =========================================================================
    // BUILD TOOLTIP HTML (COMPARATIVO — corretiva vs preventiva)
    // =========================================================================
    function buildComparativoHTML(point) {
        // customdata: [periodo, os_count]
        const customdata = point.customdata || [];
        const periodo = escapeHTML(customdata[0] || '');
        const osCount = escapeHTML(customdata[1] || 0);
        const traceName = escapeHTML(point.data ? (point.data.name || '') : '');
        const yValue = point.y;
        const isCorretiva = traceName.toLowerCase().includes('corretiva');
        const dotColor = isCorretiva ? '#E20613' : '#94a3b8';

        return `
            <div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,0.06)">
                <div style="display:flex;align-items:center;gap:6px">
                    <i class="bi bi-calendar2-range" style="color:#64748b;font-size:14px"></i>
                    <span style="font-weight:700;font-size:14px;color:#1e293b">${periodo}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <span style="width:8px;height:8px;border-radius:50%;background:${dotColor};display:inline-block"></span>
                <span style="color:#475569;font-weight:600">${traceName}</span>
                <span style="font-weight:800;color:${dotColor};margin-left:auto;font-size:15px">${formatPercent(yValue)}</span>
            </div>
            <div style="font-size:12px;color:#64748b;display:flex;justify-content:space-between;align-items:center;margin-top:6px;padding-top:6px;border-top:1px dashed rgba(0,0,0,0.05)">
                <span>Volume de OS:</span>
                <span style="color:#1e293b;font-weight:600">${formatNumber(osCount)}</span>
            </div>
        `;
    }

    // =========================================================================
    // BUILD TOOLTIP HTML (FUGAS)
    // =========================================================================
    function buildFugasHTML(point) {
        // customdata: [mes_ano, pct_fuga]
        const customdata = point.customdata || [];
        const periodo = escapeHTML(customdata[0] || '');
        const pctFuga = escapeHTML(customdata[1] || 0);
        
        return `
            <div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,0.06)">
                <div style="display:flex;align-items:center;gap:6px">
                    <i class="bi bi-calendar2-range" style="color:#64748b;font-size:14px"></i>
                    <span style="font-weight:700;font-size:14px;color:#1e293b">${periodo}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                <span style="width:8px;height:8px;border-radius:50%;background:#E20613;display:inline-block"></span>
                <span style="color:#475569;font-weight:600">Taxa de Fugas</span>
                <span style="font-weight:800;color:#E20613;margin-left:auto;font-size:15px">${formatPercent(pctFuga)}</span>
            </div>
        `;
    }

    // =========================================================================
    // DETECT CHART TYPE FROM POINT
    // =========================================================================
    function detectChartType(point) {
        const customdata = point.customdata || [];
        // RI Geral has 11 items in customdata now
        if (customdata.length >= 10) return 'ri_geral';
        // Fugas has 2 items but uses name '% Fuga', Comparativo has 2 items
        const traceName = point.data ? (point.data.name || '') : '';
        if (traceName.includes('Fuga')) return 'fugas';
        return 'comparativo';
    }

    // =========================================================================
    // EVENT HANDLERS
    // =========================================================================
    function showTooltip(event) {
        const tooltip = getOrCreateTooltip();
        const points = event.points;
        if (!points || points.length === 0) return;

        const point = points[0];
        const customdata = point.customdata || [];
        const chartType = detectChartType(point);

        let html = '';
        if (chartType === 'ri_geral') {
            html = buildRIGeralHTML(customdata);
        } else if (chartType === 'fugas') {
            html = buildFugasHTML(point);
        } else {
            html = buildComparativoHTML(point);
        }

        tooltip.innerHTML = html;

        // Position near cursor
        const mouseX = event.event ? event.event.clientX : 0;
        const mouseY = event.event ? event.event.clientY : 0;

        let leftPos = mouseX + OFFSET_X;
        let topPos = mouseY + OFFSET_Y;

        // Prevent overflow right
        const tooltipWidth = tooltip.offsetWidth || 300;
        if (leftPos + tooltipWidth > window.innerWidth - 20) {
            leftPos = mouseX - tooltipWidth - OFFSET_X;
        }
        // Prevent overflow bottom
        const tooltipHeight = tooltip.offsetHeight || 200;
        if (topPos + tooltipHeight > window.innerHeight - 20) {
            topPos = mouseY - tooltipHeight - OFFSET_Y;
        }
        // Prevent overflow top
        if (topPos < 10) topPos = 10;

        tooltip.style.left = leftPos + 'px';
        tooltip.style.top = topPos + 'px';
        tooltip.style.opacity = '1';
        tooltip.style.transform = 'translateY(0)';
    }

    function hideTooltip() {
        const tooltip = document.getElementById(TOOLTIP_ID);
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(4px)';
        }
    }

    // =========================================================================
    // ATTACH TO ALL PLOTLY CHARTS (MutationObserver for dynamic loading)
    // =========================================================================
    const attached = new WeakSet();

    function attachToPlotlyCharts() {
        const charts = document.querySelectorAll('.js-plotly-plot');
        charts.forEach(function (chart) {
            if (attached.has(chart)) return;
            attached.add(chart);

            chart.on('plotly_hover', showTooltip);
            chart.on('plotly_unhover', hideTooltip);
        });
    }

    // Initial attach
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            setTimeout(attachToPlotlyCharts, 1000);
        });
    } else {
        setTimeout(attachToPlotlyCharts, 1000);
    }

    // Re-attach when DOM changes (Dash re-renders)
    const observer = new MutationObserver(function () {
        setTimeout(attachToPlotlyCharts, 300);
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();
