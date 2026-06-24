-- Migration 057: ebl_translations — English translations from eBL corpus.
--
-- Issue #165. The electronic Babylonian Library (eBL, LMU Munich) publishes
-- modern English translations of Babylonian/Assyrian *literary compositions*
-- (Enūma eliš, Atraḫasīs, …) line by line. No Glintstone connector pulls them;
-- this adds English-translation coverage for the literary corpus.
--
-- DATA SHAPE (audited 2026-06 against the live, UNAUTHENTICATED eBL read API):
--   GET https://www.ebl.lmu.de/api/texts/<genre>/<cat>/<index>
--        → the text's metadata + its chapters (stage, name).
--   GET https://www.ebl.lmu.de/api/texts/<g>/<c>/<i>/chapters/<stage>/<name>
--        → the chapter's reconstructed lines; each line carries a `translation`
--          string in eBL ATF translation format:
--             "#tr.en: When on high no word was used for heaven,\n#tr.ar: …"
--          i.e. one or more `#tr.<lang>:` segments. We extract the `en` segment.
--
-- WHY A DEDICATED TABLE (not the existing `translations` table):
--   `translations` is keyed on (p_number, line_id) — it is ARTIFACT-centric
--   (a CDLI tablet and a specific text_line on it). eBL corpus translations are
--   COMPOSITE-centric: they belong to the *reconstructed literary text* at a
--   chapter line number, attested across MANY manuscripts (witnesses), not to a
--   single CDLI p_number. Forcing them onto a p_number they don't belong to
--   would be inventing a false artifact attribution — exactly the kind of wrong
--   scholarly data CLAUDE.md forbids. So we store the eBL identity faithfully
--   (text + chapter + line) and leave any confident link to `composites` /
--   artifacts to a separate, evidence-based step.
--
-- GRANT: NEW table owned by wittkensis; the app reads it as glintstone
-- (composite / literary views), so GRANT the CRUD set + sequence usage.
--
-- Idempotent: CREATE TABLE IF NOT EXISTS + the UNIQUE index backing the
-- connector's ON CONFLICT make re-runs of both migration and connector no-ops.

BEGIN;

CREATE TABLE IF NOT EXISTS ebl_translations (
    id              BIGSERIAL PRIMARY KEY,

    -- eBL text identity (the literary composition). genre/category/index are the
    -- three coordinates of eBL's text catalogue; text_name is denormalised for
    -- display ("Poem of Creation (Enūma eliš)").
    text_genre      TEXT NOT NULL,
    text_category   INTEGER NOT NULL,
    text_index      INTEGER NOT NULL,
    text_name       TEXT,

    -- eBL chapter identity within the text (e.g. stage 'Standard Babylonian',
    -- name 'I'). A text has several chapters; translations live on chapter lines.
    chapter_stage   TEXT NOT NULL,
    chapter_name    TEXT NOT NULL,

    -- The reconstructed line number within the chapter (eBL's `number`, e.g.
    -- '1', '23a'). Stored as text because eBL line labels are not always pure
    -- integers (primes, suffixes).
    line_number     TEXT NOT NULL,

    -- The English translation of this line (the `#tr.en:` segment, unwrapped).
    translation_en  TEXT NOT NULL,

    -- The original reconstructed transliteration of the line, kept for context /
    -- alignment review (informational; eBL is the source of truth).
    reconstruction  TEXT,

    -- Which import run wrote this row (framework provenance).
    run_id          BIGINT REFERENCES import_runs(id),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per (text, chapter, line). This is the ON CONFLICT target the
-- connector uses for idempotent re-runs.
CREATE UNIQUE INDEX IF NOT EXISTS ebl_translations_uq
    ON ebl_translations
       (text_genre, text_category, text_index, chapter_stage, chapter_name, line_number);

-- Fast lookup of all translated lines for one text (composite view).
CREATE INDEX IF NOT EXISTS ebl_translations_text_idx
    ON ebl_translations (text_genre, text_category, text_index);

GRANT SELECT, INSERT, UPDATE, DELETE ON ebl_translations TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE ebl_translations_id_seq TO glintstone;

COMMIT;
