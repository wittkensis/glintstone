/**
 * TransmissionTimeline
 * Renders a horizontal SVG timeline of exemplar tablets grouped by historical period.
 *
 * Usage:
 *   <div id="transmission-timeline" data-exemplars="[...]"></div>
 *   const tl = new TransmissionTimeline(document.getElementById('transmission-timeline'));
 *
 * The container's data-exemplars attribute must be a JSON array of:
 *   { p_number, period, pipeline_status, designation, provenience, museum }
 *
 * Emits a 'period-selected' CustomEvent on the container when a period label is clicked.
 * The event detail is: { period: string } — empty string means "all periods".
 *
 * Public methods:
 *   clearSelection() — deselects the active period
 */

'use strict';

// Scholarly consensus date ranges for cuneiform periods (BCE = negative years)
var PERIOD_RANGES = {
    'Archaic': [-3200, -2900],
    'Early Dynastic I-II': [-2900, -2700],
    'Early Dynastic III': [-2700, -2500],
    'Early Dynastic': [-2900, -2500],           // catch-all for unlabelled ED
    'Old Akkadian': [-2340, -2200],
    'Sargonic': [-2340, -2200],                 // synonym
    'Lagash II': [-2200, -2100],
    'Ur III': [-2112, -2004],
    'Early Old Babylonian': [-2000, -1900],
    'Old Babylonian': [-1900, -1600],
    'Middle Babylonian': [-1600, -1000],
    'Middle Assyrian': [-1400, -1000],
    'Old Assyrian': [-1950, -1750],
    'Middle Hittite': [-1500, -1200],
    'Neo-Assyrian': [-900, -612],
    'Neo-Babylonian': [-626, -539],
    'Achaemenid': [-547, -331],
    'Hellenistic': [-330, -64],
    'Seleucid': [-312, -64],
    'Parthian': [-247, 224],
    'Late Babylonian': [-626, -64],
    'Uncertain': null,
};

// Display order for period bands on the timeline (chronological)
var PERIOD_DISPLAY_ORDER = [
    'Archaic',
    'Early Dynastic I-II',
    'Early Dynastic III',
    'Early Dynastic',
    'Old Akkadian',
    'Sargonic',
    'Lagash II',
    'Ur III',
    'Early Old Babylonian',
    'Old Assyrian',
    'Old Babylonian',
    'Middle Babylonian',
    'Middle Assyrian',
    'Middle Hittite',
    'Neo-Assyrian',
    'Neo-Babylonian',
    'Achaemenid',
    'Hellenistic',
    'Seleucid',
    'Parthian',
    'Late Babylonian',
    'Uncertain',
];

var SVG_NS = 'http://www.w3.org/2000/svg';

/**
 * @param {Element} container - The host element with data-exemplars JSON
 */
function TransmissionTimeline(container) {
    this._container = container;
    this._selectedPeriod = '';
    this._init();
}

TransmissionTimeline.prototype._init = function () {
    var raw;
    try {
        raw = JSON.parse(this._container.dataset.exemplars || '[]');
    } catch (e) {
        raw = [];
    }
    this._exemplars = raw;

    if (!this._exemplars.length) {
        this._container.innerHTML = '<p class="timeline-empty">No exemplar data available.</p>';
        return;
    }

    this._render();
};

/**
 * Group exemplars by period, filtering out unknown/missing periods for the
 * main SVG track and collecting stragglers into "Uncertain".
 */
TransmissionTimeline.prototype._groupByPeriod = function () {
    var groups = {};
    var self = this;

    this._exemplars.forEach(function (ex) {
        var period = ex.period || 'Uncertain';
        if (!groups[period]) groups[period] = [];
        groups[period].push(ex);
    });

    return groups;
};

/**
 * Determine the overall date range to display, based on which periods appear.
 */
TransmissionTimeline.prototype._dateRange = function (presentPeriods) {
    var min = Infinity;
    var max = -Infinity;

    presentPeriods.forEach(function (p) {
        var range = PERIOD_RANGES[p];
        if (!range) return;
        if (range[0] < min) min = range[0];
        if (range[1] > max) max = range[1];
    });

    // Fallback if nothing mapped
    if (min === Infinity) { min = -3200; max = -64; }

    return [min, max];
};

TransmissionTimeline.prototype._render = function () {
    var self = this;
    var groups = this._groupByPeriod();
    var presentPeriods = Object.keys(groups);

    // Ordered list of periods that actually appear in the data
    var orderedPeriods = PERIOD_DISPLAY_ORDER.filter(function (p) {
        return groups[p] && groups[p].length > 0;
    });
    // Any periods in data not in our display order list go at end
    presentPeriods.forEach(function (p) {
        if (orderedPeriods.indexOf(p) === -1) orderedPeriods.push(p);
    });

    var dateRange = this._dateRange(orderedPeriods);
    var totalSpan = dateRange[1] - dateRange[0]; // negative values, but diff is positive

    // Layout constants
    var paddingLeft = 16;
    var paddingRight = 16;
    var paddingTop = 12;
    var trackHeight = 80;      // dot area height
    var labelHeight = 28;      // period label area below track
    var svgHeight = paddingTop + trackHeight + labelHeight + 8;

    // We use a viewBox approach so it scales with container width
    var viewBoxWidth = 1000;
    var trackWidth = viewBoxWidth - paddingLeft - paddingRight;

    // Convert a year (BCE = negative) to an x position within the track
    function yearToX(year) {
        var frac = (year - dateRange[0]) / totalSpan;
        return paddingLeft + frac * trackWidth;
    }

    // Build SVG element
    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + viewBoxWidth + ' ' + svgHeight);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Transmission timeline showing ' + this._exemplars.length + ' exemplars across ' + orderedPeriods.length + ' periods');
    svg.style.width = '100%';
    svg.style.height = 'auto';
    svg.style.display = 'block';
    svg.style.overflow = 'visible';

    // ── Period band backgrounds ──────────────────────────────────────────────
    var bandsG = document.createElementNS(SVG_NS, 'g');
    bandsG.setAttribute('class', 'tl-bands');

    orderedPeriods.forEach(function (period, idx) {
        var range = PERIOD_RANGES[period];
        if (!range) return; // Uncertain — no band

        var x1 = yearToX(range[0]);
        var x2 = yearToX(range[1]);
        var w = Math.max(x2 - x1, 2);

        var rect = document.createElementNS(SVG_NS, 'rect');
        rect.setAttribute('x', x1);
        rect.setAttribute('y', paddingTop);
        rect.setAttribute('width', w);
        rect.setAttribute('height', trackHeight);
        rect.setAttribute('class', 'tl-band' + (idx % 2 === 0 ? ' tl-band--alt' : ''));
        rect.setAttribute('rx', '2');
        bandsG.appendChild(rect);
    });

    svg.appendChild(bandsG);

    // ── Baseline ────────────────────────────────────────────────────────────
    var baseline = document.createElementNS(SVG_NS, 'line');
    baseline.setAttribute('x1', paddingLeft);
    baseline.setAttribute('y1', paddingTop + trackHeight);
    baseline.setAttribute('x2', paddingLeft + trackWidth);
    baseline.setAttribute('y2', paddingTop + trackHeight);
    baseline.setAttribute('class', 'tl-baseline');
    svg.appendChild(baseline);

    // ── Dots per period ──────────────────────────────────────────────────────
    // For each period, spread dots horizontally across its date range,
    // stacking vertically if needed (max column height = trackHeight).
    var DOT_R = 4;      // dot radius
    var DOT_GAP = 2;    // gap between dots
    var COL_STEP = DOT_R * 2 + DOT_GAP;

    var dotsG = document.createElementNS(SVG_NS, 'g');
    dotsG.setAttribute('class', 'tl-dots');

    // Tooltip element (single shared, repositioned on hover)
    var tooltip = document.createElementNS(SVG_NS, 'g');
    tooltip.setAttribute('class', 'tl-tooltip');
    tooltip.setAttribute('display', 'none');
    tooltip.setAttribute('pointer-events', 'none');

    var tooltipBg = document.createElementNS(SVG_NS, 'rect');
    tooltipBg.setAttribute('rx', '3');
    tooltipBg.setAttribute('class', 'tl-tooltip__bg');
    tooltip.appendChild(tooltipBg);

    var tooltipText = document.createElementNS(SVG_NS, 'text');
    tooltipText.setAttribute('class', 'tl-tooltip__text');
    tooltip.appendChild(tooltipText);

    orderedPeriods.forEach(function (period) {
        var exs = groups[period];
        if (!exs || !exs.length) return;

        var range = PERIOD_RANGES[period];
        var x1, x2;
        if (range) {
            x1 = yearToX(range[0]);
            x2 = yearToX(range[1]);
        } else {
            // Uncertain: place at far right
            x1 = paddingLeft + trackWidth - 40;
            x2 = paddingLeft + trackWidth;
        }

        var bandW = Math.max(x2 - x1, COL_STEP);
        var maxCols = Math.max(1, Math.floor(bandW / COL_STEP));
        var maxRows = Math.floor(trackHeight / COL_STEP) - 1;
        var baseY = paddingTop + trackHeight - DOT_R - DOT_GAP;

        exs.forEach(function (ex, i) {
            var col = i % maxCols;
            var row = Math.min(Math.floor(i / maxCols), maxRows);

            var cx = x1 + col * COL_STEP + DOT_R + 2;
            var cy = baseY - row * COL_STEP;

            // pipeline_status: non-empty = has transcription = filled dot
            var hasTx = !!(ex.pipeline_status && ex.pipeline_status !== 'none' && ex.pipeline_status !== '');

            var circle = document.createElementNS(SVG_NS, 'circle');
            circle.setAttribute('cx', cx);
            circle.setAttribute('cy', cy);
            circle.setAttribute('r', DOT_R);
            circle.setAttribute('class', 'tl-dot' + (hasTx ? ' tl-dot--filled' : ' tl-dot--hollow') + ' tl-dot--period-' + period.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, ''));
            circle.setAttribute('data-period', period);
            circle.setAttribute('data-p-number', ex.p_number || '');
            circle.setAttribute('tabindex', ex.p_number ? '0' : '-1');
            circle.setAttribute('role', 'link');
            circle.setAttribute('aria-label', (ex.p_number || 'Unknown') + (ex.designation ? ' — ' + ex.designation : '') + (ex.provenience ? ' (' + ex.provenience + ')' : ''));

            // Click: navigate to tablet detail
            if (ex.p_number) {
                (function (pNum) {
                    circle.addEventListener('click', function () {
                        window.location.href = '/tablets/' + pNum;
                    });
                    circle.addEventListener('keydown', function (e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            window.location.href = '/tablets/' + pNum;
                        }
                    });
                }(ex.p_number));
                circle.style.cursor = 'pointer';
            }

            // Hover: show tooltip
            (function (exData, circleEl, dotCx, dotCy) {
                function showTooltip(x, y) {
                    var label = (exData.p_number || '?');
                    if (exData.designation) label += ' — ' + exData.designation;
                    if (exData.provenience) label += ' · ' + exData.provenience;
                    if (exData.museum) label += ' · ' + exData.museum;

                    tooltipText.textContent = label;
                    tooltip.setAttribute('display', 'block');

                    // Measure text (approximate: 7px per char in viewBox units)
                    var textW = Math.min(label.length * 6.5, 300);
                    var textH = 16;
                    var pad = 5;

                    // Position: above the dot, clamp to viewBox
                    var tx = Math.min(Math.max(x - textW / 2, 4), viewBoxWidth - textW - 4);
                    var ty = y - textH - pad * 2 - DOT_R;

                    tooltipBg.setAttribute('x', tx);
                    tooltipBg.setAttribute('y', ty);
                    tooltipBg.setAttribute('width', textW + pad * 2);
                    tooltipBg.setAttribute('height', textH + pad);
                    tooltipText.setAttribute('x', tx + pad);
                    tooltipText.setAttribute('y', ty + textH - 2);
                }

                circleEl.addEventListener('mouseenter', function () { showTooltip(dotCx, dotCy); });
                circleEl.addEventListener('focus', function () { showTooltip(dotCx, dotCy); });
                circleEl.addEventListener('mouseleave', function () { tooltip.setAttribute('display', 'none'); });
                circleEl.addEventListener('blur', function () { tooltip.setAttribute('display', 'none'); });
            }(ex, circle, cx, cy));

            dotsG.appendChild(circle);
        });
    });

    svg.appendChild(dotsG);
    svg.appendChild(tooltip);

    // ── Period labels ────────────────────────────────────────────────────────
    var labelsG = document.createElementNS(SVG_NS, 'g');
    labelsG.setAttribute('class', 'tl-labels');

    orderedPeriods.forEach(function (period) {
        var range = PERIOD_RANGES[period];
        var midX;
        if (range) {
            midX = (yearToX(range[0]) + yearToX(range[1])) / 2;
        } else {
            midX = paddingLeft + trackWidth - 20;
        }

        var labelY = paddingTop + trackHeight + labelHeight - 6;

        var text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', labelY);
        text.setAttribute('class', 'tl-label');
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('tabindex', '0');
        text.setAttribute('role', 'button');
        text.setAttribute('aria-pressed', 'false');
        text.setAttribute('data-period', period);
        // Shorten very long period names
        var shortName = period.length > 14 ? period.substring(0, 13) + '…' : period;
        text.textContent = shortName;
        text.style.cursor = 'pointer';

        (function (p, textEl) {
            function selectPeriod(newPeriod) {
                self._selectedPeriod = newPeriod;
                // Update all label aria-pressed states
                labelsG.querySelectorAll('.tl-label').forEach(function (lbl) {
                    var isSelected = lbl.dataset.period === newPeriod;
                    lbl.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
                    lbl.classList.toggle('tl-label--active', isSelected);
                });
                // Emit event
                self._container.dispatchEvent(new CustomEvent('period-selected', {
                    bubbles: true,
                    detail: { period: newPeriod }
                }));
            }

            textEl.addEventListener('click', function () {
                if (self._selectedPeriod === p) {
                    // Clicking the active period deselects it
                    selectPeriod('');
                } else {
                    selectPeriod(p);
                }
            });
            textEl.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (self._selectedPeriod === p) {
                        selectPeriod('');
                    } else {
                        selectPeriod(p);
                    }
                }
            });
        }(period, text));

        labelsG.appendChild(text);
    });

    svg.appendChild(labelsG);

    // Inject styles into the SVG
    var style = document.createElementNS(SVG_NS, 'style');
    style.textContent = [
        '.tl-band { fill: rgba(255,255,255,0.02); }',
        '.tl-band--alt { fill: rgba(255,255,255,0.05); }',
        '.tl-baseline { stroke: rgba(255,255,255,0.14); stroke-width: 1; }',
        '.tl-dot { transition: r 0.1s ease, opacity 0.1s ease; }',
        '.tl-dot--filled { fill: #c9a962; stroke: #c9a962; }',
        '.tl-dot--hollow { fill: none; stroke: #c9a962; stroke-width: 1.2; }',
        '.tl-dot:hover, .tl-dot:focus { r: 6; outline: none; }',
        '.tl-dot--dimmed { opacity: 0.2; }',
        '.tl-label { font-size: 9px; fill: #a0a0a0; font-family: system-ui, sans-serif; user-select: none; }',
        '.tl-label:hover { fill: #c9a962; }',
        '.tl-label--active { fill: #c9a962; font-weight: 600; }',
        '.tl-tooltip__bg { fill: #141414; stroke: rgba(255,255,255,0.14); stroke-width: 0.5; }',
        '.tl-tooltip__text { font-size: 9px; fill: #e8e6e3; font-family: system-ui, sans-serif; }',
    ].join('\n');
    svg.insertBefore(style, svg.firstChild);

    this._container.innerHTML = '';
    this._container.appendChild(svg);
    this._svg = svg;
    this._labelsG = labelsG;
    this._dotsG = dotsG;
};

/**
 * Deselect any active period and restore all dots to full opacity.
 */
TransmissionTimeline.prototype.clearSelection = function () {
    this._selectedPeriod = '';
    if (this._labelsG) {
        this._labelsG.querySelectorAll('.tl-label').forEach(function (lbl) {
            lbl.setAttribute('aria-pressed', 'false');
            lbl.classList.remove('tl-label--active');
        });
    }
    if (this._dotsG) {
        this._dotsG.querySelectorAll('.tl-dot').forEach(function (dot) {
            dot.classList.remove('tl-dot--dimmed');
        });
    }
    this._container.dispatchEvent(new CustomEvent('period-selected', {
        bubbles: true,
        detail: { period: '' }
    }));
};

// ── Mobile fallback: collapse timeline on very narrow screens ────────────────
// On screens < 480px, we replace the SVG with a compact period-count list.
// The SVG is still rendered (for screen readers / wider screens) but visually
// swapped for an accessible list on narrow viewports.
(function () {
    function isMobile() {
        return window.innerWidth < 480;
    }

    function buildMobileList(container, exemplars) {
        var groups = {};
        exemplars.forEach(function (ex) {
            var period = ex.period || 'Uncertain';
            groups[period] = (groups[period] || 0) + 1;
        });

        var list = document.createElement('ul');
        list.className = 'tl-mobile-list';

        PERIOD_DISPLAY_ORDER.forEach(function (period) {
            if (!groups[period]) return;
            var li = document.createElement('li');
            li.className = 'tl-mobile-list__item';
            li.innerHTML =
                '<span class="tl-mobile-list__period">' + period + '</span>' +
                '<span class="tl-mobile-list__count">' + groups[period] + '</span>';
            li.style.cursor = 'pointer';
            li.addEventListener('click', function () {
                container.dispatchEvent(new CustomEvent('period-selected', {
                    bubbles: true,
                    detail: { period: period }
                }));
            });
            list.appendChild(li);
        });

        return list;
    }

    // Hook into DOMContentLoaded to swap if mobile
    document.addEventListener('DOMContentLoaded', function () {
        var container = document.getElementById('transmission-timeline');
        if (!container || !isMobile()) return;

        var raw;
        try { raw = JSON.parse(container.dataset.exemplars || '[]'); } catch (_) { raw = []; }
        if (!raw.length) return;

        container.innerHTML = '';
        container.appendChild(buildMobileList(container, raw));
    });
}());
