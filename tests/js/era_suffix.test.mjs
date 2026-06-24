/**
 * #386 — regression harness for the timeline era-suffix formatters.
 *
 * Two near-identical functions render a `period_canon` year as a human era
 * label, and the dual-era convention behind them (#332) is subtle and easy to
 * invert by accident:
 *
 *   period_canon stores BCE years as POSITIVE integers (2100 → "2100 BCE")
 *   and the few genuinely-CE years as NEGATIVE integers (-224 → "224 CE").
 *   So the era suffix is the INVERSE of the sign.
 *
 *   - app/static/js/transmission-timeline.js   → function formatYear(year)
 *   - app/static/js/lemma-period-timeline.js   → function lptFormatYear(year)
 *
 * These are plain `<script>` globals (no module system, no build step), so the
 * harness reads each source file, lifts the named function out by its source
 * text, and evaluates it in isolation. That means we test the *actually shipped*
 * logic — not a hand-copied duplicate that could itself drift.
 *
 * Run: `node --test tests/js/` (no npm install — uses the built-in test runner).
 * Wired into CI as a dedicated step in .github/workflows/test.yml.
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import test from 'node:test';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

/**
 * Lift a top-level `function NAME(...) { ... }` out of a source file and return
 * it as a callable, balancing braces so we capture the whole body.
 */
function extractFunction(relPath, name) {
  const src = readFileSync(join(ROOT, relPath), 'utf8');
  const signature = `function ${name}(`;
  const start = src.indexOf(signature);
  assert.notStrictEqual(
    start,
    -1,
    `${name} not found in ${relPath} — was it renamed? Update this harness.`,
  );
  // Walk from the first '{' after the signature, balancing braces.
  let i = src.indexOf('{', start);
  assert.notStrictEqual(i, -1, `no opening brace for ${name} in ${relPath}`);
  let depth = 0;
  let end = -1;
  for (; i < src.length; i++) {
    const ch = src[i];
    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) {
        end = i + 1;
        break;
      }
    }
  }
  assert.notStrictEqual(end, -1, `unbalanced braces for ${name} in ${relPath}`);
  const fnSource = src.slice(start, end);
  // eslint-disable-next-line no-new-func
  return new Function(`${fnSource}; return ${name};`)();
}

const formatYear = extractFunction(
  'app/static/js/transmission-timeline.js',
  'formatYear',
);
const lptFormatYear = extractFunction(
  'app/static/js/lemma-period-timeline.js',
  'lptFormatYear',
);

// The two formatters must agree on every case — that's the whole point of
// having a shared convention. Run the identical table against both.
const formatters = [
  ['transmission-timeline:formatYear', formatYear],
  ['lemma-period-timeline:lptFormatYear', lptFormatYear],
];

for (const [label, fmt] of formatters) {
  test(`${label}: positive years are BCE`, () => {
    assert.equal(fmt(2100), '2100 BCE'); // Ur III
    assert.equal(fmt(1), '1 BCE');
    assert.equal(fmt(3500), '3500 BCE');
  });

  test(`${label}: negative years are CE (sign inverted, no minus sign)`, () => {
    assert.equal(fmt(-224), '224 CE'); // end of Parthian
    assert.equal(fmt(-1), '1 CE');
    // The minus sign must be stripped, not rendered.
    assert.ok(!fmt(-224).includes('-'), 'CE label must not show a minus sign');
  });

  test(`${label}: year zero is the bare "0"`, () => {
    assert.equal(fmt(0), '0');
  });

  test(`${label}: the era suffix never disagrees with the sign`, () => {
    assert.ok(fmt(500).endsWith('BCE'));
    assert.ok(fmt(-500).endsWith('CE'));
  });
}
