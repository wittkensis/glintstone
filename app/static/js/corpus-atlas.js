/* Corpus Atlas (Wave 1, #320) — progressive enhancement over the
 * server-rendered all-artifacts page.
 *
 * Every brush target (view-switch link, timeline period row, find-spot row) is
 * already a real <a href> that server-renders the correct slice — this script
 * just makes the interaction *live*: intercept the click, fetch the target URL,
 * and swap the changed regions in place + pushState (shareable, back-safe).
 * With JS off, the links navigate normally and nothing here is needed.
 *
 * Bret Victor's note from the spec: the chart IS the filter control. Clicking a
 * period or a find-spot re-filters the grid below without a full reload. */
(function () {
  'use strict';

  var REGIONS = [
    '[data-atlas-grid]',     // the result grid
    '[data-atlas-timeline]', // the timeline panel (selection state)
    '[data-atlas-sites]',    // the find-spots list
    '[data-atlas-banner]',   // the linked-filter banner
    '[data-atlas-switch]',   // the view switcher (aria-pressed)
    '.active-filters',        // active filter pills
    '.pagination'             // pagination base links
  ];

  var main = document.querySelector('.main-content');
  if (!main) return;

  function isAtlasLink(a) {
    if (!a) return false;
    return a.matches(
      '[data-atlas-switch] a, [data-atlas-timeline] a, [data-atlas-sites] a, [data-atlas-banner] .clear'
    );
  }

  function swapFrom(doc) {
    REGIONS.forEach(function (sel) {
      var incoming = doc.querySelectorAll(sel);
      var current = document.querySelectorAll(sel);
      // Region may appear/disappear (e.g. timeline panel only in timeline view,
      // banner only when a brush is active). Replace 1:1 where both exist;
      // otherwise rebuild the whole main-content as a safe fallback.
      if (incoming.length === current.length && current.length > 0) {
        current.forEach(function (el, i) {
          el.replaceWith(incoming[i]);
        });
      }
    });
  }

  function navigate(url, push) {
    main.setAttribute('aria-busy', 'true');
    fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var newMain = doc.querySelector('.main-content');
        if (!newMain) { window.location.assign(url); return; }
        // Try region-level swap; if region counts diverged, replace wholesale.
        var same = REGIONS.every(function (sel) {
          return doc.querySelectorAll(sel).length === document.querySelectorAll(sel).length;
        });
        if (same) {
          swapFrom(doc);
        } else {
          main.replaceWith(newMain);
          main = document.querySelector('.main-content');
        }
        if (push) { history.pushState({ atlas: true }, '', url); }
        var title = doc.querySelector('title');
        if (title) { document.title = title.textContent; }
      })
      .catch(function () { window.location.assign(url); })
      .finally(function () {
        var m = document.querySelector('.main-content');
        if (m) { m.removeAttribute('aria-busy'); }
      });
  }

  // Delegate: one listener survives DOM swaps.
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a || !isAtlasLink(a)) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    navigate(a.getAttribute('href'), true);
  });

  // Back/forward button: re-fetch the popped URL without pushing again.
  window.addEventListener('popstate', function () {
    navigate(window.location.href, false);
  });
})();
