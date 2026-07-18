// Behavior-lock tests for the timeline era-suffix date formatters (task #745).
//
// The timeline widgets format a "period_canon year" into a human era label.
// The convention (see the source doc-comments) is deliberately INVERTED from
// the usual astronomical sign convention:
//
//   * BCE years are stored as POSITIVE integers  (2100  -> "2100 BCE")
//   * CE  years are stored as NEGATIVE integers  (-224  -> "224 CE")
//   * the exact boundary value 0 is a special sentinel -> "0"
//
// These tests LOCK the current behavior so the dual-era logic cannot silently
// regress. They do NOT assert what the behavior *should* be — only what it *is*
// today. If a deliberate change is made, update the expectations here in the
// same commit.
//
// The two formatters (`formatYear` in transmission-timeline.js and
// `lptFormatYear` in lemma-period-timeline.js) are module-scoped, browser-only
// functions that are not exported and whose host modules reference `window` /
// `document` at load time. Rather than shim a DOM, we extract each function's
// source text straight from the shipped file and evaluate just that function.
// This runs against the REAL current code; if the function's declaration shape
// changes, the extractor throws loudly instead of testing stale copy-paste.

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');

/**
 * Pull a single top-level `function <name>(...) { ... }` declaration out of a
 * source file and return it as a callable. Balances braces so the exact body
 * ships into the test with no edits.
 */
function loadFunction(relFile, fnName) {
  const src = fs.readFileSync(path.join(REPO_ROOT, relFile), 'utf8');
  const marker = 'function ' + fnName;
  const start = src.indexOf(marker);
  assert.notEqual(
    start,
    -1,
    `Could not find "${marker}" in ${relFile} — did the formatter get renamed/moved? ` +
      `Update tests/js/timeline-formatters.test.js in the same commit.`,
  );
  // Walk from the first "{" after the signature, matching braces.
  const bodyStart = src.indexOf('{', start);
  assert.notEqual(bodyStart, -1, `No function body found for ${fnName} in ${relFile}`);
  let depth = 0;
  let end = -1;
  for (let i = bodyStart; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') {
      depth--;
      if (depth === 0) {
        end = i + 1;
        break;
      }
    }
  }
  assert.notEqual(end, -1, `Unbalanced braces extracting ${fnName} from ${relFile}`);
  const source = src.slice(start, end);
  // eslint-disable-next-line no-new-func
  return new Function(`${source}; return ${fnName};`)();
}

const formatYear = loadFunction('app/static/js/transmission-timeline.js', 'formatYear');
const lptFormatYear = loadFunction('app/static/js/lemma-period-timeline.js', 'lptFormatYear');

// Both widgets are documented to share the identical convention, so we run the
// same matrix against each. If they ever diverge, this table makes it obvious.
const FORMATTERS = [
  { name: 'formatYear (transmission-timeline.js)', fn: formatYear },
  { name: 'lptFormatYear (lemma-period-timeline.js)', fn: lptFormatYear },
];

for (const { name, fn } of FORMATTERS) {
  test(`${name}: positive years render as BCE`, () => {
    assert.equal(fn(2100), '2100 BCE'); // Ur III
    assert.equal(fn(1), '1 BCE'); // smallest positive -> still BCE
    assert.equal(fn(3200), '3200 BCE'); // early Uruk-era range
  });

  test(`${name}: negative years render as CE (sign stripped)`, () => {
    assert.equal(fn(-224), '224 CE'); // end of Parthian period
    assert.equal(fn(-1), '1 CE'); // smallest magnitude CE
    assert.equal(fn(-651), '651 CE');
  });

  test(`${name}: the year-0 sentinel renders as bare "0" (no era suffix)`, () => {
    // There is no historical year 0; the formatter deliberately emits "0"
    // with no era. Locking this prevents an accidental "0 BCE"/"0 CE".
    assert.equal(fn(0), '0');
  });

  test(`${name}: the BCE<->CE boundary flips exactly at the sign change`, () => {
    assert.equal(fn(1), '1 BCE'); // last BCE step before the sentinel
    assert.equal(fn(0), '0'); // the sentinel itself
    assert.equal(fn(-1), '1 CE'); // first CE step after the sentinel
  });

  test(`${name}: large years keep full magnitude with correct era`, () => {
    assert.equal(fn(9999), '9999 BCE');
    assert.equal(fn(-9999), '9999 CE');
    assert.equal(fn(1000000), '1000000 BCE'); // no grouping/abbreviation today
  });

  test(`${name}: output is always a string`, () => {
    for (const y of [2100, -224, 0, 1, -1, 9999, -9999]) {
      assert.equal(typeof fn(y), 'string');
    }
  });
}

// The formatter itself does not sort; ordering is driven by the raw stored
// integer (BCE positive, CE negative), which the timeline sorts DESCENDING so
// older-BCE comes first and CE comes last. Lock that the numeric key a caller
// would sort on lines up with chronological order, so a future refactor that
// (wrongly) sorts on the formatted string is caught.
test('chronology: sorting the stored integer keys descending is oldest-first', () => {
  // 3200 BCE (oldest) ... 2100 BCE ... 1 BCE ... 1 CE (-1) ... 224 CE (-224) (newest)
  const stored = [-224, 2100, -1, 3200, 1];
  const chronological = stored.slice().sort((a, b) => b - a);
  assert.deepEqual(chronological, [3200, 2100, 1, -1, -224]);
  assert.deepEqual(
    chronological.map(formatYear),
    ['3200 BCE', '2100 BCE', '1 BCE', '1 CE', '224 CE'],
  );
});

test('chronology: sorting on the formatted STRING would be wrong (guard note)', () => {
  // This documents WHY callers must sort the integer, not the label:
  // lexical order of the labels does not match chronological order.
  const labels = [2100, 1, -224].map(formatYear); // ['2100 BCE','1 BCE','224 CE']
  const lexical = labels.slice().sort();
  assert.notDeepEqual(lexical, ['2100 BCE', '1 BCE', '224 CE']);
});
