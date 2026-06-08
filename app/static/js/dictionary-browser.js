/**
 * Dictionary Detail Panel
 * Handles result row clicks → API fetch → detail panel update → URL sync.
 * Filters are server-side (link navigation). Only the detail panel is JS-driven.
 */
(function () {
  var panel = document.getElementById('dict-detail');
  var results = document.getElementById('dict-results');
  var apiUrl = document.querySelector('.dict-layout')?.dataset.apiUrl || '';

  if (!panel || !results) return;

  // Restore selection from URL on load
  var params = new URLSearchParams(location.search);
  var selectedId = params.get('selected');
  var selectedLevel = params.get('level') || 'lemmas';
  if (selectedId) {
    loadDetail(selectedLevel, selectedId, params.get('selected_pos'));
    highlightRow(selectedId);
  }

  // Click handler — works for both .dict-row (new dense list) and .dict-card (legacy)
  results.addEventListener('click', function (e) {
    var row = e.target.closest('.dict-row, .dict-card');
    if (!row) return;

    var id = row.dataset.id;
    var level = row.dataset.level;
    var pos = row.dataset.pos || null;

    highlightRow(id);
    loadDetail(level, id, pos);

    // Update URL without reload
    var url = new URL(location);
    url.searchParams.set('selected', id);
    if (pos) url.searchParams.set('selected_pos', pos);
    else url.searchParams.delete('selected_pos');
    history.pushState({ selected: id, level: level, pos: pos }, '', url);
  });

  // Back/forward button
  window.addEventListener('popstate', function () {
    var p = new URLSearchParams(location.search);
    var sel = p.get('selected');
    if (sel) {
      highlightRow(sel);
      loadDetail(p.get('level') || 'lemmas', sel, p.get('selected_pos'));
    } else {
      clearDetail();
      clearHighlight();
    }
  });

  function highlightRow(id) {
    results.querySelectorAll('.dict-row, .dict-card').forEach(function (r) {
      var active = r.dataset.id === String(id);
      // Apply correct active class depending on element type
      if (r.classList.contains('dict-row')) {
        r.classList.toggle('dict-row--active', active);
      } else {
        r.classList.toggle('dict-card--active', active);
      }
    });
  }

  function clearHighlight() {
    results.querySelectorAll('.dict-row--active, .dict-card--active').forEach(function (r) {
      r.classList.remove('dict-row--active', 'dict-card--active');
    });
  }

  function clearDetail() {
    panel.innerHTML =
      '<div class="dict-detail__placeholder">' +
      '<h3>Select an entry</h3>' +
      '<p>Click a result to view its details</p></div>';
  }

  function loadDetail(level, id, pos) {
    panel.innerHTML = '<div class="dict-detail__loading">Loading&hellip;</div>';

    var url;
    if (level === 'signs') {
      url = apiUrl + '/dictionary/signs/' + encodeURIComponent(id);
    } else if (level === 'glosses') {
      url = apiUrl + '/dictionary/glosses/' + encodeURIComponent(id);
      if (pos) url += '?pos=' + encodeURIComponent(pos);
    } else {
      url = apiUrl + '/dictionary/lemmas/' + encodeURIComponent(id);
    }

    fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then(function (data) {
        if (level === 'signs') renderSignDetail(data);
        else if (level === 'glosses') renderGlossDetail(data);
        else renderLemmaDetail(data);
      })
      .catch(function () {
        panel.innerHTML =
          '<div class="dict-detail__placeholder">' +
          '<h3>Error loading details</h3>' +
          '<p>Could not load the selected entry.</p></div>';
      });
  }

  // Safe HTML escape
  function esc(s) {
    if (s === null || s === undefined) return '';
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  // Locale-formatted number
  function fmt(n) {
    return Number(n || 0).toLocaleString();
  }

  // ── Lemma Detail ──────────────────────────────────────────────────────────

  function renderLemmaDetail(data) {
    var l = data.lemma;
    var h = '<div class="dict-detail__content">';

    // Title — citation form in italics per Assyriology convention
    h += '<h2 class="dict-detail__title">';
    h += '<em>' + esc(l.citation_form) + '</em>';
    if (l.guide_word) h += ' <span class="dict-detail__guide">[' + esc(l.guide_word) + ']</span>';
    h += '</h2>';

    // Metadata badges
    h += '<div class="dict-detail__meta">';
    if (l.pos_label) h += '<span class="badge">' + esc(l.pos_label) + '</span>';
    h += '<span>' + esc(l.language_label) + '</span>';
    if (l.source_label) h += '<span class="source-badge">' + esc(l.source_label) + '</span>';
    h += '</div>';

    // Attestation count — prominent summary line
    if (l.attestation_count) {
      h += '<p class="dict-detail__attestation-count">';
      h += '<strong>' + fmt(l.attestation_count) + '</strong> attestations in corpus';
      h += '</p>';
    }

    // Definition variants — group senses by source for multi-source datasets
    if (data.senses && data.senses.length) {
      var hasSources = data.senses.some(function (s) { return s.source_label || s.source; });

      h += '<div class="dict-detail__section"><h3>Definition Variants</h3>';

      if (hasSources) {
        // Group by source label to show "ORACC/oimea  in, on, at…" rows
        var bySource = {};
        var sourceOrder = [];
        data.senses.forEach(function (s) {
          var src = s.source_label || s.source || 'Unknown';
          if (!bySource[src]) {
            bySource[src] = [];
            sourceOrder.push(src);
          }
          var def = (s.definition_parts || []).join(', ');
          if (def) bySource[src].push(def);
        });
        sourceOrder.forEach(function (src) {
          if (bySource[src].length) {
            h += '<div class="detail-variant">';
            h += '<span class="detail-variant__source">' + esc(src) + '</span>';
            h += '<span class="detail-variant__text">' + bySource[src].map(esc).join('; ') + '</span>';
            h += '</div>';
          }
        });
      } else {
        // No source grouping — flat numbered list
        h += '<ol>';
        data.senses.forEach(function (s) {
          var def = (s.definition_parts || []).join(', ');
          h += '<li>' + esc(def);
          if (s.usage_notes) h += ' <span class="dict-detail__note">(' + esc(s.usage_notes) + ')</span>';
          h += '</li>';
        });
        h += '</ol>';
      }
      h += '</div>';
    }

    // Written forms — chips row
    if (data.forms && data.forms.length) {
      h += '<div class="dict-detail__section"><h3>Forms</h3>';
      h += '<ul class="detail-forms">';
      data.forms.forEach(function (f) {
        h += '<li class="detail-forms__chip">' + esc(f) + '</li>';
      });
      h += '</ul></div>';
    }

    // Signs that write this lemma
    if (data.signs && data.signs.length) {
      h += '<div class="dict-detail__section"><h3>Signs</h3><ul class="dict-detail__signs">';
      data.signs.forEach(function (s) {
        h += '<li>';
        if (s.unicode_char) h += '<span class="dict-detail__sign-glyph">' + esc(s.unicode_char) + '</span>';
        h += ' ' + esc(s.sign_name);
        if (s.reading_type) h += ' <span class="dict-detail__note">(' + esc(s.reading_type) + ')</span>';
        h += '</li>';
      });
      h += '</ul></div>';
    }

    // Top attested artifacts — honest stub until PRD-012 indexes at artifact level
    if (l.attestation_count && l.attestation_count > 0) {
      h += '<div class="dict-detail__section"><h3>Top Attested Artifacts</h3>';
      h += '<p class="dict-detail__note">Artifact-level attestation index coming soon.</p>';
      h += '</div>';
    }

    // Related lemmas — included when API returns them
    if (data.related && data.related.length) {
      h += '<div class="dict-detail__section"><h3>Related Lemmas</h3><ul>';
      data.related.forEach(function (r) {
        h += '<li><em>' + esc(r.citation_form) + '</em>';
        if (r.guide_word) h += ' [' + esc(r.guide_word) + ']';
        if (r.pos_label) h += ' <span class="dict-detail__note">' + esc(r.pos_label) + '</span>';
        h += '</li>';
      });
      h += '</ul></div>';
    }

    h += '</div>';
    panel.innerHTML = h;
  }

  // ── Sign Detail ───────────────────────────────────────────────────────────

  function renderSignDetail(data) {
    var s = data.sign;
    var h = '<div class="dict-detail__content">';
    if (s.unicode_char) h += '<div class="dict-detail__big-glyph">' + esc(s.unicode_char) + '</div>';
    h += '<h2 class="dict-detail__title">' + esc(s.sign_name) + '</h2>';
    h += '<div class="dict-detail__meta">';
    h += '<span class="source-badge">' + esc(s.source_label || s.source) + '</span>';
    if (s.unicode_codepoint) h += '<span class="dict-detail__note">' + esc(s.unicode_codepoint) + '</span>';
    h += '</div>';

    if (s.values && s.values.length) {
      h += '<div class="dict-detail__section"><h3>Readings</h3>';
      h += '<ul class="detail-forms">';
      s.values.forEach(function (v) {
        h += '<li class="detail-forms__chip">' + esc(v) + '</li>';
      });
      h += '</ul></div>';
    }

    if (data.lemmas && data.lemmas.length) {
      h += '<div class="dict-detail__section"><h3>Linked Lemmas</h3><ul>';
      data.lemmas.forEach(function (l) {
        h += '<li><em>' + esc(l.citation_form) + '</em>';
        if (l.guide_word) h += ' [' + esc(l.guide_word) + ']';
        h += ' <span class="dict-detail__note">' +
          esc(l.pos_label || l.pos || '') + ' &middot; ' + esc(l.language_label) +
          '</span>';
        h += '</li>';
      });
      h += '</ul></div>';
    }

    h += '</div>';
    panel.innerHTML = h;
  }

  // ── Gloss Detail ──────────────────────────────────────────────────────────

  function renderGlossDetail(data) {
    var h = '<div class="dict-detail__content">';
    h += '<h2 class="dict-detail__title">&ldquo;' + esc(data.guide_word) + '&rdquo;</h2>';
    h += '<div class="dict-detail__meta">';
    if (data.pos_label) h += '<span class="badge">' + esc(data.pos_label) + '</span>';
    h += '<span>' + fmt(data.total_attestations || 0) + ' total attestations</span>';
    h += '</div>';

    if (data.lemmas && data.lemmas.length) {
      h += '<div class="dict-detail__section"><h3>Lemmas</h3><ul>';
      data.lemmas.forEach(function (l) {
        h += '<li><em>' + esc(l.citation_form) + '</em>';
        if (l.guide_word) h += ' [' + esc(l.guide_word) + ']';
        h += ' <span class="dict-detail__note">' + esc(l.language_label) + ' &middot; ' + esc(l.source_label) + '</span>';
        if (l.glosses && l.glosses.length) {
          h += '<br><span class="dict-detail__sub">' + l.glosses.map(esc).join(', ') + '</span>';
        }
        h += '</li>';
      });
      h += '</ul></div>';
    }

    h += '</div>';
    panel.innerHTML = h;
  }

})();
