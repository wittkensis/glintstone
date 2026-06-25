/**
 * cite-modal.js — Cite this button handler (#493)
 *
 * Generates Chicago, SBL, and CDLI citation formats for artifacts and
 * composites. All data is sourced from data-* attributes on the trigger
 * button; no API call needed. Shows a modal with three formatted citations,
 * each with a copy button.
 *
 * SBL Note: The Society of Biblical Literature Handbook of Style (2nd ed.)
 * is the standard for Ancient Near Eastern studies. The CDLI format is the
 * standard for cuneiform corpus citation.
 */
(function () {
    'use strict';

    var year = new Date().getFullYear();

    function pad(n) { return String(n).padStart(5, '0'); }

    /**
     * Build citation strings from data attributes on the trigger button.
     * Works for both artifact pages (data-p-number) and composite pages
     * (data-q-number) — the composites detail page can add the same button.
     */
    function buildCitations(btn) {
        var pNum = btn.dataset.pNumber || '';
        var qNum = btn.dataset.qNumber || '';
        var designation = btn.dataset.designation || pNum || qNum;
        var period = btn.dataset.period || '';
        var provenience = btn.dataset.provenience || '';
        var museum = btn.dataset.museum || '';

        var entityRef = pNum
            ? 'CDLI ' + pNum + ' (https://cdli.earth/artifacts/' + parseInt(pNum.slice(1), 10) + ')'
            : 'CDLI ' + qNum;
        var pageUrl = window.location.href;
        var glinstoneCite = 'Glintstone Cuneiform Research Platform, ' + pageUrl + ' (accessed ' + year + ')';

        var facets = [period, provenience].filter(Boolean).join('; ');
        var museumNote = museum ? ', ' + museum : '';

        // CDLI citation format (most authoritative for the corpus)
        var cdli = entityRef + '. ';
        if (designation && designation !== pNum && designation !== qNum) {
            cdli += '"' + designation + '"' + museumNote + '. ';
        }
        if (facets) cdli += facets + '. ';
        cdli += 'Cuneiform Digital Library Initiative. https://cdli.earth/';

        // Chicago (17th ed.) — used in Assyriology
        var chicago = '"';
        chicago += designation + '"' + (facets ? ' (' + facets + ')' : '') + museumNote + '. ';
        chicago += entityRef + '. ';
        chicago += 'Also available via ' + glinstoneCite + '.';

        // SBL (Handbook of Style, 2nd ed.) — standard for ANE studies
        // Archival sources: Author, "Title/Description," Archive/Museum, Date.
        var sbl = designation;
        if (facets || museum) {
            sbl += '. ' + [museum, facets].filter(Boolean).join(', ');
        }
        sbl += '. ' + entityRef + '.';
        sbl += ' Cited via ' + glinstoneCite + '.';

        return { cdli: cdli, chicago: chicago, sbl: sbl };
    }

    function createModal(citations) {
        var overlay = document.createElement('div');
        overlay.className = 'cite-modal-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'cite-modal-title');

        overlay.innerHTML = [
            '<div class="cite-modal">',
            '  <div class="cite-modal__head">',
            '    <h2 id="cite-modal-title" class="cite-modal__title">Cite this</h2>',
            '    <button class="cite-modal__close" aria-label="Close">',
            '      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">',
            '        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
            '      </svg>',
            '    </button>',
            '  </div>',
            renderFormat('CDLI', citations.cdli),
            renderFormat('Chicago', citations.chicago),
            renderFormat('SBL', citations.sbl),
            '  <p class="cite-modal__note">SBL = Society of Biblical Literature Handbook of Style, the standard for Ancient Near Eastern studies.</p>',
            '</div>',
        ].join('\n');

        return overlay;
    }

    function renderFormat(label, text) {
        var id = 'cite-' + label.toLowerCase();
        return [
            '<div class="cite-format">',
            '  <div class="cite-format__head">',
            '    <span class="cite-format__label">' + label + '</span>',
            '    <button class="cite-format__copy btn btn--sm" data-cite-target="' + id + '">Copy</button>',
            '  </div>',
            '  <p id="' + id + '" class="cite-format__text">' + escHtml(text) + '</p>',
            '</div>',
        ].join('\n');
    }

    function escHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function openModal(btn) {
        var citations = buildCitations(btn);
        var modal = createModal(citations);
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        // Focus management
        var closeBtn = modal.querySelector('.cite-modal__close');
        closeBtn.focus();

        function close() {
            document.body.removeChild(modal);
            document.body.style.overflow = '';
            btn.focus();
        }

        closeBtn.addEventListener('click', close);
        modal.addEventListener('click', function (e) {
            if (e.target === modal) close();
        });
        document.addEventListener('keydown', function onKey(e) {
            if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); }
        });

        // Copy buttons
        modal.querySelectorAll('[data-cite-target]').forEach(function (copyBtn) {
            copyBtn.addEventListener('click', function () {
                var target = document.getElementById(copyBtn.dataset.citeTarget);
                if (!target) return;
                navigator.clipboard.writeText(target.textContent).then(function () {
                    var orig = copyBtn.textContent;
                    copyBtn.textContent = 'Copied!';
                    setTimeout(function () { copyBtn.textContent = orig; }, 1800);
                });
            });
        });
    }

    // Wire up all cite buttons on the page
    document.querySelectorAll('#cite-btn, [data-cite-trigger]').forEach(function (btn) {
        btn.addEventListener('click', function () { openModal(btn); });
    });
}());
