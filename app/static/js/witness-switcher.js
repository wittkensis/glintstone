/**
 * Witness-switcher (#404 Concept A).
 *
 * On a composition detail page, the ATF preview opens on the representative
 * witness. Clicking a witness chip fetches that witness's first-N readable ATF
 * lines and swaps the preview block in place — read any witness, no page load.
 * No cross-witness line alignment is claimed; each chip is one witness read
 * end-to-end. Degrades silently when the switcher isn't present (empty/single).
 */
(function () {
    'use strict';

    var switcher = document.getElementById('witness-switcher');
    var section = document.querySelector('.composition-detail__atf-preview');
    if (!switcher || !section) return;

    var chips = Array.prototype.slice.call(
        switcher.querySelectorAll('.witness-chip')
    );
    // Single non-interactive witness: nothing to switch.
    if (chips.length <= 1) return;

    var qNumber = section.dataset.qNumber;
    var apiUrl = section.dataset.apiUrl;
    if (!qNumber || !apiUrl) return;

    var list = document.getElementById('witness-atf-list');
    var hint = document.getElementById('atf-preview-hint');
    var count = document.getElementById('atf-preview-count');
    var fullLink = document.getElementById('atf-preview-full');

    // Cache fetched witnesses so re-clicking a chip is instant.
    var cache = {};

    function esc(s) {
        var d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    function setActive(chip) {
        chips.forEach(function (c) {
            var on = c === chip;
            c.classList.toggle('is-active', on);
            c.setAttribute('aria-selected', on ? 'true' : 'false');
        });
    }

    function renderPreview(p, data) {
        var lines = (data && data.lines) || [];
        if (!lines.length) return; // keep current preview; never blank it

        list.innerHTML = lines.map(function (line) {
            var ref = line.line_number ? 'l. ' + esc(line.line_number) : '—';
            return (
                '<li class="attestation-row">' +
                '<a class="attestation-row__link" href="/tablets/' + esc(p) + '">' +
                '<span class="attestation-row__ref">' +
                '<span class="attestation-row__line">' + ref + '</span></span>' +
                '<span class="attestation-row__main">' +
                '<span class="attestation-row__atf" lang="akk" dir="ltr">' +
                esc(line.raw_atf) + '</span></span></a></li>'
            );
        }).join('');

        if (count && data.total_atf_lines != null) {
            var n = data.total_atf_lines;
            count.textContent =
                'First ' + data.preview_line_count + ' of ' +
                n.toLocaleString() + ' line' + (n === 1 ? '' : 's');
        }
        if (fullLink) fullLink.href = '/tablets/' + p;
    }

    function setHint(chip, data) {
        if (!hint) return;
        var p = chip.dataset.pNumber;
        var desig = chip.dataset.designation || p;
        var period = chip.dataset.period;
        var prov = chip.dataset.provenience;
        var tail = (period ? ', ' + esc(period) : '') +
            (prov ? ' (' + esc(prov) + ')' : '');
        hint.innerHTML =
            'Reading <a href="/tablets/' + esc(p) + '">' + esc(desig) + '</a>' +
            tail + '.';
    }

    function select(chip) {
        var p = chip.dataset.pNumber;
        setActive(chip);
        setHint(chip, null);

        if (cache[p]) {
            renderPreview(p, cache[p]);
            return;
        }

        list.setAttribute('aria-busy', 'true');
        fetch(apiUrl + '/composites/' + encodeURIComponent(qNumber) +
              '/witnesses/' + encodeURIComponent(p) + '/atf-preview')
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (resp) {
                var data = resp && resp.atf_preview;
                if (data) {
                    cache[p] = data;
                    renderPreview(p, data);
                }
            })
            .catch(function (err) {
                console.error('Witness preview load failed:', err);
            })
            .finally(function () {
                list.setAttribute('aria-busy', 'false');
            });
    }

    chips.forEach(function (chip) {
        chip.addEventListener('click', function () {
            if (!chip.classList.contains('is-active')) select(chip);
        });
    });
}());
