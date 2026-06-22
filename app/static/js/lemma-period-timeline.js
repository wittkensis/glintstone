/**
 * LemmaPeriodTimeline
 * Renders a proportional-BCE histogram of how often a single dictionary lemma
 * is attested across canonical historical periods. Each period that the lemma
 * appears in becomes a vertical band, positioned on a real BCE axis by its
 * scholarly-consensus date range and sized (height) by the number of attesting
 * tablets of that period. This is the chronological *spread* of a word's
 * usage — e.g. a word peaking in the Old Babylonian period — read directly off
 * the axis (#201).
 *
 * It reuses the #195 transmission-timeline machinery: the period canon is
 * fetched live from the app's /_periods proxy (backed by period_canon), and
 * the same proportional year-to-x projection and "nice" BCE axis ticks place
 * everything on a real timeline rather than equal-width buckets. The visual
 * differs from #195 — bars sized by attestation count, not individual dots.
 *
 * Usage:
 *   <div id="lemma-period-timeline"
 *        data-periods='[{"period","date_start_bce","date_end_bce","tablet_count"}]'>
 *   </div>
 *   new LemmaPeriodTimeline(document.getElementById('lemma-period-timeline'));
 *
 * The container's data-periods attribute is the API's `periods` array (already
 * filtered to datable periods server-side). An empty array renders nothing —
 * the server template owns the empty state, so this class no-ops in that case.
 */

'use strict';

var LPT_SVG_NS = 'http://www.w3.org/2000/svg';
var LPT_PERIODS_ENDPOINT = '/_periods';

// Shared promise so the chronological order is fetched at most once per page.
var _lptPeriodsPromise = null;

/**
 * Fetch the canonical period order from /_periods (BCE ranges live in the
 * per-lemma data already; we only need the chronological ordering for
 * left-to-right layout fallback). Resolves to { order: [...] } even on
 * failure, so the timeline degrades gracefully.
 */
function lptFetchOrder() {
    if (_lptPeriodsPromise) return _lptPeriodsPromise;

    _lptPeriodsPromise = fetch(LPT_PERIODS_ENDPOINT, { credentials: 'same-origin' })
        .then(function (resp) {
            if (!resp.ok) throw new Error('periods HTTP ' + resp.status);
            return resp.json();
        })
        .then(function (data) {
            var rows = (data && data.items) || [];
            var order = [];
            rows.forEach(function (row) {
                if (row.canonical) order.push(row.canonical);
            });
            return { order: order };
        })
        .catch(function () {
            return { order: [] };
        });

    return _lptPeriodsPromise;
}

/** Format a BCE year (negative integer) as a human label: -2000 -> "2000". */
function lptFormatYear(year) {
    if (year < 0) return String(-year);
    if (year === 0) return '0';
    return year + ' CE';
}

/**
 * @param {Element} container - host element with data-periods JSON
 */
function LemmaPeriodTimeline(container) {
    this._container = container;
    this._order = [];
    this._init();
}

LemmaPeriodTimeline.prototype._init = function () {
    var self = this;
    var raw;
    try {
        raw = JSON.parse(this._container.dataset.periods || '[]');
    } catch (e) {
        raw = [];
    }
    // Keep only datable periods with a positive count (server already filters,
    // but be defensive so a stray row never throws off the axis).
    this._periods = raw.filter(function (p) {
        return p
            && typeof p.date_start_bce === 'number'
            && typeof p.date_end_bce === 'number'
            && (p.tablet_count || 0) > 0;
    });

    // The server template owns the empty state (#189); render nothing here.
    if (!this._periods.length) return;

    this._container.innerHTML = '<p class="lpt-empty">Loading timeline…</p>';

    lptFetchOrder().then(function (res) {
        self._order = res.order;
        self._render();
    });
};

/** "Nice" axis tick years across a BCE span (mirrors #195's _axisTicks). */
LemmaPeriodTimeline.prototype._axisTicks = function (min, max) {
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
    for (var y = first; y <= max; y += step) ticks.push(y);
    if (ticks[0] !== min) ticks.unshift(min);
    if (ticks[ticks.length - 1] !== max) ticks.push(max);
    return ticks;
};

LemmaPeriodTimeline.prototype._render = function () {
    var self = this;

    // Order periods chronologically by canon, falling back to start year for
    // any not present in the canon order list.
    var periods = this._periods.slice();
    periods.sort(function (a, b) {
        var ia = self._order.indexOf(a.period);
        var ib = self._order.indexOf(b.period);
        if (ia !== -1 && ib !== -1) return ia - ib;
        if (ia !== -1) return -1;
        if (ib !== -1) return 1;
        return a.date_start_bce - b.date_start_bce;
    });

    // BCE extent across present periods + the busiest period (for bar scaling).
    var min = Infinity, max = -Infinity, maxCount = 0;
    periods.forEach(function (p) {
        if (p.date_start_bce < min) min = p.date_start_bce;
        if (p.date_end_bce > max) max = p.date_end_bce;
        if (p.tablet_count > maxCount) maxCount = p.tablet_count;
    });
    if (min === Infinity) { min = -3200; max = -64; }
    var totalSpan = (max - min) || 1;

    // Layout (viewBox units; scales to container width).
    var paddingLeft = 16, paddingRight = 16, paddingTop = 12;
    var trackHeight = 96;      // max bar height
    var axisHeight = 18;       // BCE tick axis below the track
    var labelHeight = 30;      // period name + count below the axis
    var svgHeight = paddingTop + trackHeight + axisHeight + labelHeight + 8;
    var viewBoxWidth = 1000;
    var trackWidth = viewBoxWidth - paddingLeft - paddingRight;
    var axisY = paddingTop + trackHeight;

    function yearToX(year) {
        return paddingLeft + ((year - min) / totalSpan) * trackWidth;
    }

    var svg = document.createElementNS(LPT_SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + viewBoxWidth + ' ' + svgHeight);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('role', 'img');
    svg.setAttribute(
        'aria-label',
        'Attestation timeline: this lemma occurs across ' + periods.length
        + ' historical periods on a proportional BCE axis, '
        + 'bar height showing how many tablets of each period carry the word.'
    );
    svg.style.width = '100%';
    svg.style.height = 'auto';
    svg.style.display = 'block';
    svg.style.overflow = 'visible';

    // ── Histogram bars: one per period, height ∝ tablet_count ────────────────
    var barsG = document.createElementNS(LPT_SVG_NS, 'g');
    barsG.setAttribute('class', 'lpt-bars');
    var MIN_BAR_H = 3;   // floor so a 1-tablet period is still visible

    // Tooltip (single shared element, repositioned on hover/focus).
    var tooltip = document.createElementNS(LPT_SVG_NS, 'g');
    tooltip.setAttribute('class', 'lpt-tooltip');
    tooltip.setAttribute('display', 'none');
    tooltip.setAttribute('pointer-events', 'none');
    var tipBg = document.createElementNS(LPT_SVG_NS, 'rect');
    tipBg.setAttribute('rx', '3');
    tipBg.setAttribute('class', 'lpt-tooltip__bg');
    tooltip.appendChild(tipBg);
    var tipText = document.createElementNS(LPT_SVG_NS, 'text');
    tipText.setAttribute('class', 'lpt-tooltip__text');
    tooltip.appendChild(tipText);

    periods.forEach(function (p, idx) {
        var x1 = yearToX(p.date_start_bce);
        var x2 = yearToX(p.date_end_bce);
        var w = Math.max(x2 - x1, 6);
        var h = MIN_BAR_H + (p.tablet_count / maxCount) * (trackHeight - MIN_BAR_H);
        var y = axisY - h;

        var rect = document.createElementNS(LPT_SVG_NS, 'rect');
        rect.setAttribute('x', x1);
        rect.setAttribute('y', y);
        rect.setAttribute('width', w);
        rect.setAttribute('height', h);
        rect.setAttribute('rx', '2');
        rect.setAttribute('class', 'lpt-bar' + (idx === maxIndex(periods) ? ' lpt-bar--peak' : ''));
        rect.setAttribute('tabindex', '0');
        rect.setAttribute('role', 'img');
        rect.setAttribute(
            'aria-label',
            p.period + ': ' + p.tablet_count + ' tablet'
            + (p.tablet_count === 1 ? '' : 's') + ' ('
            + lptFormatYear(p.date_start_bce) + '–' + lptFormatYear(p.date_end_bce)
            + ' BCE)'
        );

        // Count label centred above the bar (skipped if the bar is too narrow).
        if (w >= 22) {
            var cnt = document.createElementNS(LPT_SVG_NS, 'text');
            cnt.setAttribute('x', x1 + w / 2);
            cnt.setAttribute('y', y - 3);
            cnt.setAttribute('text-anchor', 'middle');
            cnt.setAttribute('class', 'lpt-bar__count');
            cnt.textContent = p.tablet_count.toLocaleString();
            barsG.appendChild(cnt);
        }

        (function (period, barEl, bx, by, bw) {
            function show() {
                var label = period.period + ' · ' + period.tablet_count
                    + ' tablet' + (period.tablet_count === 1 ? '' : 's')
                    + ' · ' + lptFormatYear(period.date_start_bce) + '–'
                    + lptFormatYear(period.date_end_bce) + ' BCE';
                tipText.textContent = label;
                tooltip.setAttribute('display', 'block');
                var textW = Math.min(label.length * 6.0, 360);
                var textH = 16, pad = 5;
                var tx = Math.min(Math.max(bx + bw / 2 - textW / 2, 4), viewBoxWidth - textW - 4);
                var ty = Math.max(by - textH - pad * 2, 2);
                tipBg.setAttribute('x', tx);
                tipBg.setAttribute('y', ty);
                tipBg.setAttribute('width', textW + pad * 2);
                tipBg.setAttribute('height', textH + pad);
                tipText.setAttribute('x', tx + pad);
                tipText.setAttribute('y', ty + textH - 2);
            }
            barEl.addEventListener('mouseenter', show);
            barEl.addEventListener('focus', show);
            barEl.addEventListener('mouseleave', function () { tooltip.setAttribute('display', 'none'); });
            barEl.addEventListener('blur', function () { tooltip.setAttribute('display', 'none'); });
        }(p, rect, x1, y, w));

        barsG.appendChild(rect);
    });
    svg.appendChild(barsG);

    // ── Baseline ─────────────────────────────────────────────────────────────
    var baseline = document.createElementNS(LPT_SVG_NS, 'line');
    baseline.setAttribute('x1', paddingLeft);
    baseline.setAttribute('y1', axisY);
    baseline.setAttribute('x2', paddingLeft + trackWidth);
    baseline.setAttribute('y2', axisY);
    baseline.setAttribute('class', 'lpt-baseline');
    svg.appendChild(baseline);

    // ── Proportional BCE axis: ticks + year labels ───────────────────────────
    var axisG = document.createElementNS(LPT_SVG_NS, 'g');
    axisG.setAttribute('class', 'lpt-axis');

    var caption = document.createElementNS(LPT_SVG_NS, 'text');
    caption.setAttribute('x', paddingLeft - 2);
    caption.setAttribute('y', axisY + axisHeight - 2);
    caption.setAttribute('text-anchor', 'start');
    caption.setAttribute('class', 'lpt-axis__caption');
    caption.textContent = 'BCE';
    axisG.appendChild(caption);

    var ticks = this._axisTicks(min, max);
    var lastTickX = paddingLeft + 16;
    ticks.forEach(function (year) {
        var tx = yearToX(year);
        var crowded = (tx - lastTickX) < 48;
        var tick = document.createElementNS(LPT_SVG_NS, 'line');
        tick.setAttribute('x1', tx);
        tick.setAttribute('y1', axisY);
        tick.setAttribute('x2', tx);
        tick.setAttribute('y2', axisY + 5);
        tick.setAttribute('class', 'lpt-axis__tick');
        axisG.appendChild(tick);
        if (!crowded) {
            var lbl = document.createElementNS(LPT_SVG_NS, 'text');
            lbl.setAttribute('x', tx);
            lbl.setAttribute('y', axisY + axisHeight - 2);
            lbl.setAttribute('text-anchor', 'middle');
            lbl.setAttribute('class', 'lpt-axis__year');
            lbl.textContent = lptFormatYear(year);
            axisG.appendChild(lbl);
            lastTickX = tx;
        }
    });
    svg.appendChild(axisG);

    // ── Period labels (centred under each band) ──────────────────────────────
    var labelsG = document.createElementNS(LPT_SVG_NS, 'g');
    labelsG.setAttribute('class', 'lpt-labels');
    var labelY = axisY + axisHeight + labelHeight - 8;
    var lastLabelX = -Infinity;
    periods.forEach(function (p) {
        var midX = (yearToX(p.date_start_bce) + yearToX(p.date_end_bce)) / 2;
        // Drop a label only if it would collide with the previous one.
        if (midX - lastLabelX < 42) return;
        var text = document.createElementNS(LPT_SVG_NS, 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', labelY);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('class', 'lpt-label');
        var short = p.period.length > 13 ? p.period.substring(0, 12) + '…' : p.period;
        text.textContent = short;
        labelsG.appendChild(text);
        lastLabelX = midX;
    });
    svg.appendChild(labelsG);

    svg.appendChild(tooltip);

    // Tokenized styles (CSS custom properties cascade into inline SVG), with
    // literal fallbacks for the rare out-of-document render.
    var style = document.createElementNS(LPT_SVG_NS, 'style');
    style.textContent = [
        '.lpt-bar { fill: var(--color-accent-muted, #6b5a36); transition: fill 0.1s ease; }',
        '.lpt-bar--peak { fill: var(--color-accent, #c9a962); }',
        '.lpt-bar:hover, .lpt-bar:focus { fill: var(--color-accent, #c9a962); outline: none; }',
        '.lpt-bar__count { font-size: 8px; fill: var(--color-text-muted, #a0a0a0); font-family: var(--font-sans, system-ui, sans-serif); }',
        '.lpt-baseline { stroke: var(--color-border, #404040); stroke-width: 1; }',
        '.lpt-axis__tick { stroke: var(--color-border, #404040); stroke-width: 1; }',
        '.lpt-axis__year { font-size: 8px; fill: var(--color-text-subtle, #707070); font-family: var(--font-sans, system-ui, sans-serif); }',
        '.lpt-axis__caption { font-size: 8px; fill: var(--color-text-secondary, #888888); font-family: var(--font-sans, system-ui, sans-serif); letter-spacing: 0.05em; }',
        '.lpt-label { font-size: 9px; fill: var(--color-text-muted, #a0a0a0); font-family: var(--font-sans, system-ui, sans-serif); user-select: none; }',
        '.lpt-tooltip__bg { fill: var(--color-bg-deep, #141414); stroke: var(--color-border, #404040); stroke-width: 0.5; }',
        '.lpt-tooltip__text { font-size: 9px; fill: var(--color-text, #e8e6e3); font-family: var(--font-sans, system-ui, sans-serif); }',
    ].join('\n');
    svg.insertBefore(style, svg.firstChild);

    this._container.innerHTML = '';
    this._container.appendChild(svg);
};

/** Index of the busiest period (for the --peak highlight). */
function maxIndex(periods) {
    var best = 0, bestVal = -1;
    periods.forEach(function (p, i) {
        if (p.tablet_count > bestVal) { bestVal = p.tablet_count; best = i; }
    });
    return best;
}

document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('lemma-period-timeline');
    if (el) new LemmaPeriodTimeline(el);
});
