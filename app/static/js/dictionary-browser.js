/**
 * Dictionary Detail Panel
 * Handles result card clicks → API fetch → detail panel update → URL sync.
 * Filters are server-side (form submit). Only the detail panel is JS-driven.
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
    loadDetail(selectedLevel, selectedId, params.get('pos'));
    highlightCard(selectedId);
  }

  // Click handler on result cards
  results.addEventListener('click', function (e) {
    var card = e.target.closest('.dict-card');
    if (!card) return;

    var id = card.dataset.id;
    var level = card.dataset.level;
    var pos = card.dataset.pos || null;

    highlightCard(id);
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
      highlightCard(sel);
      loadDetail(p.get('level') || 'lemmas', sel, p.get('selected_pos'));
    } else {
      clearDetail();
      clearHighlight();
    }
  });

  function highlightCard(id) {
    results.querySelectorAll('.dict-card').forEach(function (c) {
      c.classList.toggle('dict-card--active', c.dataset.id === String(id));
    });
  }

  function clearHighlight() {
    results.querySelectorAll('.dict-card--active').forEach(function (c) {
      c.classList.remove('dict-card--active');
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

  function esc(s) {
    if (!s) return '';
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function renderLemmaDetail(data) {
    var l = data.lemma;
    var h = '<div class="dict-detail__content">';
    h += '<h2 class="dict-detail__title">' + esc(l.citation_form);
    if (l.guide_word) h += ' <span class="dict-detail__guide">[' + esc(l.guide_word) + ']</span>';
    h += '</h2>';
    h += '<div class="dict-detail__meta">';
    if (l.pos_label) h += '<span class="badge">' + esc(l.pos_label) + '</span>';
    h += '<span>' + esc(l.language_label) + '</span>';
    h += '<span>' + esc(l.source_label) + '</span>';
    h += '</div>';

    if (data.senses && data.senses.length) {
      h += '<div class="dict-detail__section"><h3>Glosses</h3><ol>';
      data.senses.forEach(function (s) {
        var def = (s.definition_parts || []).join(', ');
        h += '<li>' + esc(def);
        if (s.usage_notes) h += ' <span class="dict-detail__note">(' + esc(s.usage_notes) + ')</span>';
        h += '</li>';
      });
      h += '</ol></div>';
    }

    if (data.signs && data.signs.length) {
      h += '<div class="dict-detail__section"><h3>Signs</h3><ul class="dict-detail__signs">';
      data.signs.forEach(function (s) {
        h += '<li>';
        if (s.unicode_char) h += '<span class="dict-detail__sign-glyph">' + esc(s.unicode_char) + '</span> ';
        h += esc(s.sign_name);
        if (s.reading_type) h += ' <span class="dict-detail__note">(' + esc(s.reading_type) + ')</span>';
        h += '</li>';
      });
      h += '</ul></div>';
    }

    if (l.attestation_count) {
      h += '<div class="dict-detail__section"><h3>Attestations</h3>';
      h += '<p>' + Number(l.attestation_count).toLocaleString() + ' occurrences in corpus</p>';
      h += '</div>';
    }

    h += '</div>';
    panel.innerHTML = h;
  }

  function renderSignDetail(data) {
    var s = data.sign;
    var h = '<div class="dict-detail__content">';
    if (s.unicode_char) h += '<div class="dict-detail__big-glyph">' + esc(s.unicode_char) + '</div>';
    h += '<h2 class="dict-detail__title">' + esc(s.sign_name) + '</h2>';
    h += '<div class="dict-detail__meta">';
    h += '<span>' + esc(s.source_label || s.source) + '</span>';
    if (s.unicode_codepoint) h += '<span>' + esc(s.unicode_codepoint) + '</span>';
    h += '</div>';

    if (s.values && s.values.length) {
      h += '<div class="dict-detail__section"><h3>Readings</h3><ul>';
      s.values.forEach(function (v) { h += '<li>' + esc(v) + '</li>'; });
      h += '</ul></div>';
    }

    if (data.lemmas && data.lemmas.length) {
      h += '<div class="dict-detail__section"><h3>Linked Lemmas</h3><ul>';
      data.lemmas.forEach(function (l) {
        h += '<li>' + esc(l.citation_form);
        if (l.guide_word) h += ' [' + esc(l.guide_word) + ']';
        h += ' <span class="dict-detail__note">' + esc(l.pos_label || l.pos || '') + ' &middot; ' + esc(l.language_label) + '</span>';
        h += '</li>';
      });
      h += '</ul></div>';
    }

    h += '</div>';
    panel.innerHTML = h;
  }

  function renderGlossDetail(data) {
    var h = '<div class="dict-detail__content">';
    h += '<h2 class="dict-detail__title">&ldquo;' + esc(data.guide_word) + '&rdquo;</h2>';
    h += '<div class="dict-detail__meta">';
    if (data.pos_label) h += '<span class="badge">' + esc(data.pos_label) + '</span>';
    h += '<span>' + Number(data.total_attestations || 0).toLocaleString() + ' total attestations</span>';
    h += '</div>';

    if (data.lemmas && data.lemmas.length) {
      h += '<div class="dict-detail__section"><h3>Lemmas</h3><ul>';
      data.lemmas.forEach(function (l) {
        h += '<li><strong>' + esc(l.citation_form) + '</strong>';
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
