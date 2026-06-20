/**
 * TransmissionTimeline
 * Renders a horizontal SVG timeline of exemplar tablets positioned on a real,
 * proportional BCE axis. Period date ranges are fetched live from the app's
 * /_periods proxy (which calls the API's /api/v2/periods, backed by the
 * period_canon table) rather than hardcoded, so the axis stays in sync with
 * the canonical chronology the rest of the app uses for filtering. Per the
 * two-tier rule the browser must hit the app, never the API host directly.
 *
 * Usage:
 *   <div id="transmission-timeline" data-exemplars="[...]"></div>
 *   const tl = new TransmissionTimeline(document.getElementById('transmission-timeline'));
 *
 * The container's data-exemplars attribute must be a JSON array of:
 *   { p_number, period, pipeline_status, designation, provenience, museum }
 *
 * Emits a 'period-selected' CustomEvent on the container when a period label is
 * clicked. The event detail is: { period: string } — empty string means "all".
 *
 * Public methods:
 *   clearSelection() — deselects the active period
 */

'use strict';

var SVG_NS = 'http://www.w3.org/2000/svg';
var PERIODS_ENDPOINT = '/_periods';

// Shared promise so the constructor and the mobile fallback fetch the period
// canon at most once per page load.
var _periodsPromise = null;

/**
 * Fetch canonical periods from the app's /_periods proxy and reshape into the structures the
 * timeline needs: a {canonical -> [start, end]} range map (BCE = negative,
 * null when a period has no agreed range) and a chronological display order.
 * Resolves to { ranges, order } even on failure (empty structures), so callers
 * can fall back gracefully rather than throwing.
 */
function fetchPeriods() {
    if (_periodsPromise) return _periodsPromise;

    _periodsPromise = fetch(PERIODS_ENDPOINT, { credentials: 'same-origin' })
        .then(function (resp) {
            if (!resp.ok) throw new Error('periods HTTP ' + resp.status);
            return resp.json();
        })
        .then(function (data) {
            var rows = (data && data.items) || [];
            var ranges = {};
            var order = [];
            rows.forEach(function (row) {
                var name = row.canonical;
                if (!name) return;
                order.push(name);
                var start = row.date_start_bce;
                var end = row.date_end_bce;
                // A usable range needs both endpoints; otherwise treat the
                // period as undated (e.g. "Uncertain") and render no band.
                if (typeof start === 'number' && typeof end === 'number') {
                    ranges[name] = [start, end];
                } else {
                    ranges[name] = null;
                }
            });
            return { ranges: ranges, order: order };
        })
        .catch(function () {
            return { ranges: {}, order: [] };
        });

    return _periodsPromise;
}

/**
 * @param {Element} container - The host element with data-exemplars JSON
 */
function TransmissionTimeline(container) {
    this._container = container;
    this._selectedPeriod = '';
    this._ranges = {};
    this._order = [];
    this._init();
}

TransmissionTimeline.prototype._init = function () {
    var self = this;
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

    // Show a lightweight placeholder while the period canon loads.
    this._container.innerHTML = '<p class="timeline-empty">Loading timeline…</p>';

    fetchPeriods().then(function (periods) {
        self._ranges = periods.ranges;
        self._order = periods.order;
        self._render();
    });
};

/**
 * Group exemplars by period.
 */
TransmissionTimeline.prototype._groupByPeriod = function () {
    var groups = {};

    this._exemplars.forEach(function (ex) {
        var period = ex.period || 'Uncertain';
        if (!groups[period]) groups[period] = [];
        groups[period].push(ex);
    });

    return groups;
};

/**
 * Determine the overall BCE date range to display, based on which dated
 * periods actually appear in the data.
 */
TransmissionTimeline.prototype._dateRange = function (presentPeriods) {
    var self = this;
    var min = Infinity;
    var max = -Infinity;

    presentPeriods.forEach(function (p) {
        var range = self._ranges[p];
        if (!range) return;
        if (range[0] < min) min = range[0];
        if (range[1] > max) max = range[1];
    });

    // Fallback if nothing mapped (no dated periods present, or API failed).
    if (min === Infinity) { min = -3200; max = -64; }

    return [min, max];
};

/**
 * Build "nice" axis tick years across a BCE span. Picks a round step so the
 * axis shows ~6-9 labels regardless of how wide the span is.
 */
TransmissionTimeline.prototype._axisTicks = function (dateRange) {
    var min = dateRange[0];
    var max = dateRange[1];
    var span = max - min;
    if (span <= 0) return [min];

    var rawStep = span / 7;
    var steps = [100, 200, 250, 500, 1000];
    var step = steps[steps.length - 1];
    for (var i = 0; i < steps.length; i++) {
        if (rawStep <= steps[i]) { step = steps[i]; break; }
    }

    var ticks = [];
    var first = Math.ceil(min / step) * step;
    for (var y = first; y <= max; y += step) {
        ticks.push(y);
    }
    // Always anchor the visible extremes.
    if (ticks[0] !== min) ticks.unshift(min);
    if (ticks[ticks.length - 1] !== max) ticks.push(max);
    return ticks;
};

/**
 * Format a BCE year (negative integer) as a human label, e.g. -2000 -> "2000".
 * Positive years (rare, e.g. Parthian end) are suffixed CE.
 */
function formatYear(year) {
    if (year < 0) return String(-year);
    if (year === 0) return '0';
    return year + ' CE';
}

TransmissionTimeline.prototype._render = function () {
    var self = this;
    var groups = this._groupByPeriod();
    var presentPeriods = Object.keys(groups);

    // Ordered list of periods that actually appear in the data, using the
    // chronological order returned by the API.
    var orderedPeriods = this._order.filter(function (p) {
        return groups[p] && groups[p].length > 0;
    });
    // Any periods in data not present in the canon order go at the end.
    presentPeriods.forEach(function (p) {
        if (orderedPeriods.indexOf(p) === -1) orderedPeriods.push(p);
    });

    var dateRange = this._dateRange(orderedPeriods);
    var totalSpan = dateRange[1] - dateRange[0]; // positive diff

    // Layout constants
    var paddingLeft = 16;
    var paddingRight = 16;
    var paddingTop = 12;
    var trackHeight = 80;      // dot area height
    var axisHeight = 18;       // BCE tick axis below the track
    var labelHeight = 28;      // period label area below the axis
    var svgHeight = paddingTop + trackHeight + axisHeight + labelHeight + 8;

    // viewBox approach so it scales with container width
    var viewBoxWidth = 1000;
    var trackWidth = viewBoxWidth - paddingLeft - paddingRight;

    var axisY = paddingTop + trackHeight;

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
    svg.setAttribute('aria-label', 'Transmission timeline showing ' + this._exemplars.length + ' exemplars across ' + orderedPeriods.length + ' periods, on a proportional BCE axis');
    svg.style.width = '100%';
    svg.style.height = 'auto';
    svg.style.display = 'block';
    svg.style.overflow = 'visible';

    // ── Period band backgrounds ──────────────────────────────────────────────
    var bandsG = document.createElementNS(SVG_NS, 'g');
    bandsG.setAttribute('class', 'tl-bands');

    orderedPeriods.forEach(function (period, idx) {
        var range = self._ranges[period];
        if (!range) return; // undated period — no band

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
    baseline.setAttribute('y1', axisY);
    baseline.setAttribute('x2', paddingLeft + trackWidth);
    baseline.setAttribute('y2', axisY);
    baseline.setAttribute('class', 'tl-baseline');
    svg.appendChild(baseline);

    // ── Proportional BCE axis: ticks + year labels ───────────────────────────
    var axisG = document.createElementNS(SVG_NS, 'g');
    axisG.setAttribute('class', 'tl-axis');

    // Axis caption — make the "BCE" framing explicit for the reader. Sits in
    // the left padding gutter, below the baseline, on the year-label row. The
    // tick loop reserves space for it so year labels never collide with it.
    var axisCaption = document.createElementNS(SVG_NS, 'text');
    axisCaption.setAttribute('x', paddingLeft - 2);
    axisCaption.setAttribute('y', axisY + axisHeight - 2);
    axisCaption.setAttribute('text-anchor', 'start');
    axisCaption.setAttribute('class', 'tl-axis__caption');
    axisCaption.textContent = 'BCE';
    axisG.appendChild(axisCaption);

    var ticks = this._axisTicks(dateRange);
    // Reserve the caption's footprint so the first year label is dropped only
    // if it would overlap "BCE"; later labels still render normally.
    var lastTickX = paddingLeft + 16;
    ticks.forEach(function (year) {
        var tx = yearToX(year);
        // Skip labels that would overlap the previous one.
        var crowded = (tx - lastTickX) < 48;

        var tick = document.createElementNS(SVG_NS, 'line');
        tick.setAttribute('x1', tx);
        tick.setAttribute('y1', axisY);
        tick.setAttribute('x2', tx);
        tick.setAttribute('y2', axisY + 5);
        tick.setAttribute('class', 'tl-axis__tick');
        axisG.appendChild(tick);

        if (!crowded) {
            var lbl = document.createElementNS(SVG_NS, 'text');
            lbl.setAttribute('x', tx);
            lbl.setAttribute('y', axisY + axisHeight - 2);
            lbl.setAttribute('text-anchor', 'middle');
            lbl.setAttribute('class', 'tl-axis__year');
            lbl.textContent = formatYear(year);
            axisG.appendChild(lbl);
            lastTickX = tx;
        }
    });

    svg.appendChild(axisG);

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

        var range = self._ranges[period];
        var x1, x2;
        if (range) {
            x1 = yearToX(range[0]);
            x2 = yearToX(range[1]);
        } else {
            // Undated period: place at far right of the track.
            x1 = paddingLeft + trackWidth - 40;
            x2 = paddingLeft + trackWidth;
        }

        var bandW = Math.max(x2 - x1, COL_STEP);
        var maxCols = Math.max(1, Math.floor(bandW / COL_STEP));
        var maxRows = Math.floor(trackHeight / COL_STEP) - 1;
        var baseY = axisY - DOT_R - DOT_GAP;

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

                    // Measure text (approximate: 6.5px per char in viewBox units)
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
        var range = self._ranges[period];
        var midX;
        if (range) {
            midX = (yearToX(range[0]) + yearToX(range[1])) / 2;
        } else {
            midX = paddingLeft + trackWidth - 20;
        }

        var labelY = axisY + axisHeight + labelHeight - 6;

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

    // Inject styles into the SVG. Colors reference the app's design tokens
    // (CSS custom properties cascade into inline SVG) with literal fallbacks
    // for the rare case the timeline renders outside the tokenized document.
    var style = document.createElementNS(SVG_NS, 'style');
    style.textContent = [
        '.tl-band { fill: rgba(255,255,255,0.02); }',
        '.tl-band--alt { fill: rgba(255,255,255,0.05); }',
        '.tl-baseline { stroke: var(--color-border, #404040); stroke-width: 1; }',
        '.tl-axis__tick { stroke: var(--color-border, #404040); stroke-width: 1; }',
        '.tl-axis__year { font-size: 8px; fill: var(--color-text-subtle, #707070); font-family: var(--font-sans, system-ui, sans-serif); }',
        '.tl-axis__caption { font-size: 8px; fill: var(--color-text-secondary, #888888); font-family: var(--font-sans, system-ui, sans-serif); letter-spacing: 0.05em; }',
        '.tl-dot { transition: r 0.1s ease, opacity 0.1s ease; }',
        '.tl-dot--filled { fill: var(--color-accent, #c9a962); stroke: var(--color-accent, #c9a962); }',
        '.tl-dot--hollow { fill: none; stroke: var(--color-accent, #c9a962); stroke-width: 1.2; }',
        '.tl-dot:hover, .tl-dot:focus { r: 6; outline: none; }',
        '.tl-dot--dimmed { opacity: 0.2; }',
        '.tl-label { font-size: 9px; fill: var(--color-text-muted, #a0a0a0); font-family: var(--font-sans, system-ui, sans-serif); user-select: none; }',
        '.tl-label:hover { fill: var(--color-accent, #c9a962); }',
        '.tl-label--active { fill: var(--color-accent, #c9a962); font-weight: 600; }',
        '.tl-tooltip__bg { fill: var(--color-bg-deep, #141414); stroke: var(--color-border, #404040); stroke-width: 0.5; }',
        '.tl-tooltip__text { font-size: 9px; fill: var(--color-text, #e8e6e3); font-family: var(--font-sans, system-ui, sans-serif); }',
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
// Ordering uses the same canonical chronology fetched from the API; on fetch
// failure we fall back to whatever order the exemplar groups appear in.
(function () {
    function isMobile() {
        return window.innerWidth < 480;
    }

    function buildMobileList(container, exemplars, order) {
        var groups = {};
        exemplars.forEach(function (ex) {
            var period = ex.period || 'Uncertain';
            groups[period] = (groups[period] || 0) + 1;
        });

        // Order periods chronologically per the canon, then append any
        // leftover periods that weren't in the canon list.
        var ordered = (order || []).filter(function (p) { return groups[p]; });
        Object.keys(groups).forEach(function (p) {
            if (ordered.indexOf(p) === -1) ordered.push(p);
        });

        var list = document.createElement('ul');
        list.className = 'tl-mobile-list';

        ordered.forEach(function (period) {
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

        fetchPeriods().then(function (periods) {
            container.innerHTML = '';
            container.appendChild(buildMobileList(container, raw, periods.order));
        });
    });
}());
