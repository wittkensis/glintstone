-- Migration 062: project_contributors — ORACC project-team scholar source.
--
-- Issue #1612. The existing artifact_contributors junction (migration 050)
-- is fed by parsing per-TEXT credits prose, which only ever names the small,
-- repeated set of project directors/lemmatizers cited on individual editions
-- (~59-63 distinct scholars total across the whole corpus). This table adds a
-- second, complementary source: the project-level "About the Project" pages
-- ORACC publishes, which list each project's real team / editorial board /
-- contributors roster — names that never appear in any single text's credit
-- line. The oracc-project-team connector is the writer.
--
-- WHY a separate table (not more rows in artifact_contributors):
--   artifact_contributors links a SPECIFIC ARTIFACT to a scholar+role, keyed
--   on (p_number, scholar_id, role, oracc_project). A project-team roster has
--   no per-artifact granularity — a person is credited to the PROJECT, not to
--   any one edition — so forcing it into that table would require a fake
--   p_number. This table keys on (oracc_project, scholar_id, role) instead.
--
-- ACCURACY OVER COVERAGE (CLAUDE.md): scholar linking mirrors the credits
-- pipeline's conservative match — a scraped name is attributed to an existing
-- scholar ONLY when its surname_initials normalized form is globally unique
-- across `scholars`; an ambiguous or unparseable name is refused (dead-
-- lettered), never guessed. A name with no existing match becomes a new
-- `scholars` row (see the connector), so this table's scholar_id is always a
-- confirmed link, never a raw string guess.

BEGIN;

CREATE TABLE IF NOT EXISTS project_contributors (
    id             BIGSERIAL PRIMARY KEY,

    -- ORACC top-level project slug this roster page belongs to (e.g. "dcclt",
    -- "ribo", "saao"). Free TEXT, not an FK — ORACC project slugs aren't
    -- modeled as a Glintstone table.
    oracc_project  TEXT    NOT NULL,

    scholar_id     INTEGER NOT NULL REFERENCES scholars(id),

    -- The exact display name lifted from the page before normalization, kept
    -- for audit ("did we match/create the right person?"). Never displayed
    -- in place of scholars.name.
    person_name    TEXT    NOT NULL,

    -- The section heading the entry was scraped from (e.g. "Project Team",
    -- "RIBo Contributors", "OIMEA Editorial Board"). Free TEXT rather than a
    -- controlled vocabulary like artifact_contributors.role: project-team
    -- page headings are far more varied ORACC-project-to-ORACC-project than
    -- the small, stable set of credit-prose role phrasings, and collapsing
    -- them into a fixed enum would lose real information (which board /
    -- team a person actually belongs to) for no matching benefit.
    role           TEXT    NOT NULL,

    -- The scraped person's own homepage link, when the roster entry carried
    -- one (nullable — plain-text entries have none).
    profile_url    TEXT,

    -- The About-page URL this row was scraped from (audit / re-scrape trace).
    source_url     TEXT    NOT NULL,

    -- Which import run wrote this row (provenance, consistent with the rest
    -- of the ingestion framework — see entity_wikidata_links, migration 053).
    run_id         BIGINT  REFERENCES import_runs(id),

    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One link per (project x scholar x role). Re-running the connector is
-- idempotent (ON CONFLICT DO UPDATE against this constraint refreshes the
-- scraped display name / profile / source / run on a re-scrape without
-- creating a duplicate).
CREATE UNIQUE INDEX IF NOT EXISTS uq_project_contributors_link
    ON project_contributors (oracc_project, scholar_id, role);

-- Reverse lookup: "what projects has this scholar been credited on".
CREATE INDEX IF NOT EXISTS idx_project_contributors_scholar
    ON project_contributors (scholar_id);

CREATE INDEX IF NOT EXISTS idx_project_contributors_project
    ON project_contributors (oracc_project);

-- IMPORTANT: app connects as glintstone; tables are owned by wittkensis.
GRANT SELECT, INSERT, UPDATE, DELETE ON project_contributors TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE project_contributors_id_seq TO glintstone;

COMMIT;
