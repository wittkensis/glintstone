-- Glintstone v2 Initial Schema
-- Generated from data-model/v2/glintstone-v2-schema.yaml
-- Engine: PostgreSQL
--
-- Table creation order respects FK dependencies.
-- All enum constraints use CHECK constraints for clarity.

-- ═══════════════════════════════════════════════════════════
-- NORMALIZATION / LOOKUP TABLES (no FKs)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE period_canon (
    raw_period    TEXT PRIMARY KEY,
    canonical     TEXT NOT NULL,
    date_start_bce INTEGER,
    date_end_bce   INTEGER,
    sort_order     INTEGER
);

CREATE TABLE language_map (
    cdli_name  TEXT PRIMARY KEY,
    oracc_code TEXT NOT NULL,
    full_name  TEXT,
    family     TEXT CHECK(family IN ('sumerian', 'semitic', 'elamite', 'hurrian', 'hittite', 'other'))
);

CREATE TABLE genre_canon (
    raw_genre  TEXT PRIMARY KEY,
    canonical  TEXT NOT NULL,
    supergenre TEXT
);

CREATE TABLE provenience_canon (
    raw_provenience TEXT PRIMARY KEY,
    ancient_name    TEXT NOT NULL,
    modern_name     TEXT,
    pleiades_id     TEXT
);

CREATE TABLE surface_canon (
    raw_surface TEXT PRIMARY KEY,
    canonical   TEXT NOT NULL CHECK(canonical IN ('obverse', 'reverse', 'left_edge', 'right_edge', 'top_edge', 'bottom_edge', 'seal', 'unknown'))
);

-- ═══════════════════════════════════════════════════════════
-- REFERENCE TABLES (no FKs)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE museums (
    code    TEXT PRIMARY KEY,
    name    TEXT,
    city    TEXT,
    country TEXT,
    latitude  REAL,
    longitude REAL
);

CREATE TABLE excavation_sites (
    code           TEXT PRIMARY KEY,
    name           TEXT,
    ancient_name   TEXT,
    modern_country TEXT,
    pleiades_id    TEXT,
    latitude       REAL,
    longitude      REAL
);

CREATE TABLE semantic_fields (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE,
    description     TEXT,
    parent_field_id INTEGER REFERENCES semantic_fields(id)
);

-- ═══════════════════════════════════════════════════════════
-- PROVENANCE BACKBONE
-- ═══════════════════════════════════════════════════════════

CREATE TABLE scholars (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    orcid               TEXT UNIQUE,
    institution         TEXT,
    expertise_periods   TEXT, -- JSON array
    expertise_languages TEXT, -- JSON array
    active_since        TEXT
);

CREATE TABLE annotation_runs (
    id              SERIAL PRIMARY KEY,
    source_type     TEXT CHECK(source_type IN ('human', 'model', 'hybrid', 'import')),
    source_name     TEXT,
    model_version   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    corpus_scope    TEXT,
    notes           TEXT,
    scholar_id      INTEGER REFERENCES scholars(id),
    method          TEXT CHECK(method IN ('hand_copy', 'photograph', 'collation', 'autopsy', 'RTI', '3D_scan', 'ML_model', 'import', 'api_fetch', 'web_scrape', 'manual', 'model')),
    publication_ref TEXT,
    publication_id  INTEGER -- FK added after publications table is created
);

-- ═══════════════════════════════════════════════════════════
-- LAYER 0: IDENTITY
-- ═══════════════════════════════════════════════════════════

CREATE TABLE artifacts (
    p_number             TEXT PRIMARY KEY,
    designation          TEXT,
    museum_no            TEXT,
    excavation_no        TEXT,
    material             TEXT,
    object_type          TEXT,
    width                REAL,
    height               REAL,
    thickness            REAL,
    seal_id              TEXT,
    object_preservation  TEXT,
    period               TEXT,
    period_normalized    TEXT,
    provenience          TEXT,
    provenience_normalized TEXT,
    genre                TEXT,
    subgenre             TEXT,
    supergenre           TEXT,
    language             TEXT,
    languages            TEXT, -- JSON array
    pleiades_id          TEXT,
    latitude             REAL,
    longitude            REAL,
    primary_publication  TEXT,
    collection           TEXT,
    dates_referenced     TEXT,
    date_of_origin       TEXT,
    findspot_square      TEXT,
    accounting_period    TEXT,
    acquisition_history  TEXT,
    cdli_updated_at      TIMESTAMPTZ,
    oracc_projects       TEXT, -- JSON array
    annotation_run_id    INTEGER REFERENCES annotation_runs(id)
);

CREATE TABLE composites (
    q_number       TEXT PRIMARY KEY,
    designation    TEXT,
    language       TEXT,
    period         TEXT,
    genre          TEXT,
    exemplar_count INTEGER
);

CREATE TABLE artifact_composites (
    p_number TEXT NOT NULL REFERENCES artifacts(p_number),
    q_number TEXT NOT NULL REFERENCES composites(q_number),
    line_ref TEXT,
    PRIMARY KEY (p_number, q_number)
);

CREATE TABLE artifact_identifiers (
    id                    SERIAL PRIMARY KEY,
    p_number              TEXT NOT NULL REFERENCES artifacts(p_number),
    identifier_type       TEXT NOT NULL CHECK(identifier_type IN ('museum_no', 'excavation_no', 'accession_no', 'publication', 'cdli_designation', 'oracc_project', 'ark', 'collection_no', 'seal_id')),
    identifier_value      TEXT NOT NULL,
    identifier_normalized TEXT NOT NULL,
    authority             TEXT,
    is_current            INTEGER DEFAULT 1,
    annotation_run_id     INTEGER REFERENCES annotation_runs(id),
    confidence            REAL DEFAULT 1.0,
    note                  TEXT,
    UNIQUE(p_number, identifier_type, identifier_value)
);

CREATE INDEX idx_ai_normalized ON artifact_identifiers(identifier_normalized);
CREATE INDEX idx_ai_type_value ON artifact_identifiers(identifier_type, identifier_value);
CREATE INDEX idx_ai_p_number ON artifact_identifiers(p_number);
CREATE INDEX idx_ai_authority ON artifact_identifiers(authority);

CREATE TABLE artifact_identifier_evidence (
    id                      SERIAL PRIMARY KEY,
    artifact_identifier_id  INTEGER NOT NULL REFERENCES artifact_identifiers(id),
    evidence_type           TEXT CHECK(evidence_type IN ('catalog_entry', 'museum_record', 'publication', 'photograph', 'autopsy', 'database_export', 'personal_communication')),
    evidence_ref            TEXT,
    added_by                INTEGER REFERENCES scholars(id),
    added_at                TIMESTAMPTZ DEFAULT NOW(),
    note                    TEXT
);

CREATE TABLE artifact_identifier_decisions (
    id                      SERIAL PRIMARY KEY,
    artifact_identifier_id  INTEGER NOT NULL REFERENCES artifact_identifiers(id),
    decided_by              INTEGER REFERENCES scholars(id),
    decision_method         TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'museum_verification', 'import_default')),
    rationale               TEXT,
    decided_at              TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id           INTEGER REFERENCES artifact_identifier_decisions(id)
);

-- ═══════════════════════════════════════════════════════════
-- LAYER 1: PHYSICAL
-- ═══════════════════════════════════════════════════════════

CREATE TABLE surfaces (
    id                    SERIAL PRIMARY KEY,
    p_number              TEXT NOT NULL REFERENCES artifacts(p_number),
    surface_type          TEXT CHECK(surface_type IN ('obverse', 'reverse', 'left_edge', 'right_edge', 'top_edge', 'bottom_edge', 'seal')),
    surface_preservation  TEXT,
    condition_description TEXT,
    UNIQUE(p_number, surface_type)
);

CREATE TABLE surface_images (
    id                SERIAL PRIMARY KEY,
    surface_id        INTEGER NOT NULL REFERENCES surfaces(id),
    image_path        TEXT NOT NULL,
    image_width       INTEGER,
    image_height      INTEGER,
    image_type        TEXT DEFAULT 'photo' CHECK(image_type IN ('photo', 'line_drawing', '3d_render')),
    lighting          TEXT CHECK(lighting IN ('direct', 'raking', 'ambient', 'infrared')),
    source_url        TEXT,
    is_primary        INTEGER DEFAULT 0,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    UNIQUE(surface_id, image_path)
);

CREATE INDEX idx_si_surface ON surface_images(surface_id);
CREATE INDEX idx_si_primary ON surface_images(surface_id, is_primary) WHERE is_primary = 1;

-- ═══════════════════════════════════════════════════════════
-- LAYER 2: GRAPHEMIC
-- ═══════════════════════════════════════════════════════════

CREATE TABLE signs (
    sign_id               TEXT PRIMARY KEY,
    utf8                  TEXT,
    unicode_hex           TEXT,
    unicode_decimal       INTEGER,
    uname                 TEXT,
    uphase                TEXT,
    sign_type             TEXT CHECK(sign_type IN ('simple', 'compound', 'modified')),
    mzl_number            INTEGER,
    abz_number            TEXT,
    lak_number            INTEGER,
    gdl_definition        TEXT, -- JSON
    most_common_value     TEXT,
    total_corpus_frequency INTEGER
);

CREATE TABLE sign_values (
    id               SERIAL PRIMARY KEY,
    sign_id          TEXT NOT NULL REFERENCES signs(sign_id),
    value            TEXT,
    sub_index        INTEGER,
    value_type       TEXT CHECK(value_type IN ('logographic', 'syllabic', 'determinative', 'numeric')),
    language_context TEXT,
    period_context   TEXT,
    frequency        INTEGER
);

CREATE TABLE sign_variants (
    variant_id    TEXT PRIMARY KEY,
    base_sign     TEXT REFERENCES signs(sign_id),
    modifier_type TEXT CHECK(modifier_type IN ('gunu', 'tenu', 'sheshig', 'nutillu', 'rotated')),
    modifier_code TEXT
);

CREATE TABLE sign_concordance (
    id            SERIAL PRIMARY KEY,
    ogsl_id       TEXT NOT NULL REFERENCES signs(sign_id),
    system        TEXT NOT NULL CHECK(system IN ('mzl', 'abz', 'lak')),
    number        INTEGER NOT NULL,
    confidence    REAL DEFAULT 1.0,
    match_method  TEXT CHECK(match_method IN ('auto_unicode', 'manual', 'reading_overlap')),
    note          TEXT,
    UNIQUE(ogsl_id, system, number)
);

CREATE INDEX idx_sc_system_number ON sign_concordance(system, number);
CREATE INDEX idx_sc_ogsl ON sign_concordance(ogsl_id);

-- sign_annotations depends on surface_images and signs — created here
CREATE TABLE sign_annotations (
    id                SERIAL PRIMARY KEY,
    surface_image_id  INTEGER REFERENCES surface_images(id),
    sign_id           TEXT REFERENCES signs(sign_id),
    bbox_x            REAL,
    bbox_y            REAL,
    bbox_w            REAL,
    bbox_h            REAL,
    line_number       INTEGER,
    position_in_line  INTEGER,
    damage_status     TEXT CHECK(damage_status IN ('intact', 'damaged', 'missing', 'illegible')),
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL
);

CREATE TABLE sign_annotation_evidence (
    id                    SERIAL PRIMARY KEY,
    sign_annotation_id    INTEGER NOT NULL REFERENCES sign_annotations(id),
    evidence_type         TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output')),
    evidence_ref          TEXT,
    added_by              INTEGER REFERENCES scholars(id),
    added_at              TIMESTAMPTZ DEFAULT NOW(),
    note                  TEXT
);

-- ═══════════════════════════════════════════════════════════
-- LAYER 3: READING
-- ═══════════════════════════════════════════════════════════

CREATE TABLE text_lines (
    id            SERIAL PRIMARY KEY,
    p_number      TEXT NOT NULL REFERENCES artifacts(p_number),
    surface_id    INTEGER REFERENCES surfaces(id),
    line_number   INTEGER,
    raw_atf       TEXT,
    is_ruling     INTEGER DEFAULT 0,
    is_blank      INTEGER DEFAULT 0,
    source        TEXT CHECK(source IN ('cdli', 'oracc')),
    UNIQUE(p_number, surface_id, line_number, source)
);

CREATE TABLE tokens (
    id       SERIAL PRIMARY KEY,
    line_id  INTEGER NOT NULL REFERENCES text_lines(id),
    position INTEGER,
    gdl_json TEXT, -- JSON
    lang     TEXT
);

CREATE TABLE token_readings (
    id                SERIAL PRIMARY KEY,
    token_id          INTEGER NOT NULL REFERENCES tokens(id),
    form              TEXT,
    reading           TEXT,
    sign_function     TEXT CHECK(sign_function IN ('logographic', 'syllabographic', 'determinative', 'numeric', 'mixed')),
    damage            TEXT CHECK(damage IN ('intact', 'damaged', 'missing', 'illegible')),
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL,
    is_consensus      INTEGER DEFAULT 0,
    note              TEXT
);

CREATE TABLE token_reading_evidence (
    id                SERIAL PRIMARY KEY,
    token_reading_id  INTEGER NOT NULL REFERENCES token_readings(id),
    evidence_type     TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output')),
    evidence_ref      TEXT,
    added_by          INTEGER REFERENCES scholars(id),
    added_at          TIMESTAMPTZ DEFAULT NOW(),
    note              TEXT
);

CREATE TABLE token_reading_decisions (
    id                SERIAL PRIMARY KEY,
    token_reading_id  INTEGER NOT NULL REFERENCES token_readings(id),
    decided_by        INTEGER REFERENCES scholars(id),
    decision_method   TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale         TEXT,
    decided_at        TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id     INTEGER REFERENCES token_reading_decisions(id)
);

-- ═══════════════════════════════════════════════════════════
-- LAYER 4: LINGUISTIC
-- ═══════════════════════════════════════════════════════════

CREATE TABLE glossary_entries (
    entry_id            TEXT PRIMARY KEY,
    headword            TEXT,
    citation_form       TEXT,
    guide_word          TEXT,
    language            TEXT,
    pos                 TEXT,
    icount              INTEGER,
    project             TEXT,
    normalized_headword TEXT,
    periods             TEXT, -- JSON array
    norms               TEXT, -- JSON array
    annotation_run_id   INTEGER REFERENCES annotation_runs(id)
);

CREATE TABLE glossary_forms (
    id       SERIAL PRIMARY KEY,
    entry_id TEXT NOT NULL REFERENCES glossary_entries(entry_id),
    form     TEXT,
    count    INTEGER,
    norm     TEXT,
    lang     TEXT
);

CREATE TABLE glossary_senses (
    id           SERIAL PRIMARY KEY,
    entry_id     TEXT NOT NULL REFERENCES glossary_entries(entry_id),
    sense_number INTEGER,
    guide_word   TEXT,
    definition   TEXT,
    pos          TEXT,
    signatures   TEXT -- JSON array
);

CREATE TABLE glossary_relationships (
    id                SERIAL PRIMARY KEY,
    from_entry_id     TEXT REFERENCES glossary_entries(entry_id),
    to_entry_id       TEXT REFERENCES glossary_entries(entry_id),
    relationship_type TEXT,
    notes             TEXT,
    confidence        TEXT
);

CREATE TABLE glossary_semantic_fields (
    glossary_entry_id TEXT REFERENCES glossary_entries(entry_id),
    semantic_field_id INTEGER REFERENCES semantic_fields(id),
    PRIMARY KEY (glossary_entry_id, semantic_field_id)
);

CREATE TABLE lemmatizations (
    id                SERIAL PRIMARY KEY,
    token_id          INTEGER NOT NULL REFERENCES tokens(id),
    citation_form     TEXT,
    guide_word        TEXT,
    sense             TEXT,
    pos               TEXT,
    epos              TEXT,
    norm              TEXT,
    base              TEXT,
    signature         TEXT,
    morph_raw         TEXT,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL,
    is_consensus      INTEGER DEFAULT 0,
    entry_id          TEXT REFERENCES glossary_entries(entry_id)
);

CREATE TABLE lemmatization_evidence (
    id                 SERIAL PRIMARY KEY,
    lemmatization_id   INTEGER NOT NULL REFERENCES lemmatizations(id),
    evidence_type      TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output')),
    evidence_ref       TEXT,
    added_by           INTEGER REFERENCES scholars(id),
    added_at           TIMESTAMPTZ DEFAULT NOW(),
    note               TEXT
);

CREATE TABLE lemmatization_decisions (
    id                 SERIAL PRIMARY KEY,
    lemmatization_id   INTEGER NOT NULL REFERENCES lemmatizations(id),
    decided_by         INTEGER REFERENCES scholars(id),
    decision_method    TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale          TEXT,
    decided_at         TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id      INTEGER REFERENCES lemmatization_decisions(id)
);

CREATE TABLE morphology (
    id                     SERIAL PRIMARY KEY,
    lemmatization_id       INTEGER NOT NULL REFERENCES lemmatizations(id),
    language_family        TEXT CHECK(language_family IN ('sumerian', 'akkadian', 'hittite', 'elamite', 'other')),
    -- Akkadian (Semitic templatic)
    root                   TEXT,
    stem                   TEXT,
    tense                  TEXT,
    person                 TEXT,
    number                 TEXT,
    gender                 TEXT,
    -- Sumerian (agglutinative slot-based)
    conjugation_prefix     TEXT,
    dimensional_prefixes   TEXT,
    stem_form              TEXT,
    pronominal_suffix      TEXT,
    aspect                 TEXT,
    transitivity           TEXT,
    -- Shared
    "case"                 TEXT,
    state                  TEXT
);

CREATE TABLE translations (
    id                SERIAL PRIMARY KEY,
    p_number          TEXT NOT NULL REFERENCES artifacts(p_number),
    line_id           INTEGER REFERENCES text_lines(id),
    translation       TEXT,
    language          TEXT DEFAULT 'en',
    source            TEXT,
    annotation_run_id INTEGER REFERENCES annotation_runs(id)
);

CREATE TABLE translation_evidence (
    id              SERIAL PRIMARY KEY,
    translation_id  INTEGER NOT NULL REFERENCES translations(id),
    evidence_type   TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output')),
    evidence_ref    TEXT,
    added_by        INTEGER REFERENCES scholars(id),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    note            TEXT
);

CREATE TABLE translation_decisions (
    id              SERIAL PRIMARY KEY,
    translation_id  INTEGER NOT NULL REFERENCES translations(id),
    decided_by      INTEGER REFERENCES scholars(id),
    decision_method TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale       TEXT,
    decided_at      TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id   INTEGER REFERENCES translation_decisions(id)
);

-- ═══════════════════════════════════════════════════════════
-- LAYER 5: SEMANTIC — Intertextuality
-- ═══════════════════════════════════════════════════════════

CREATE TABLE intertextuality_links (
    id                  SERIAL PRIMARY KEY,
    source_token_start  INTEGER REFERENCES tokens(id),
    source_token_end    INTEGER REFERENCES tokens(id),
    target_token_start  INTEGER REFERENCES tokens(id),
    target_token_end    INTEGER REFERENCES tokens(id),
    link_type           TEXT CHECK(link_type IN ('parallel', 'quotation', 'formula', 'duplicate', 'commentary')),
    confidence          REAL,
    annotation_run_id   INTEGER REFERENCES annotation_runs(id)
);

-- ═══════════════════════════════════════════════════════════
-- CITATION RESOLUTION
-- ═══════════════════════════════════════════════════════════

CREATE TABLE publications (
    id                SERIAL PRIMARY KEY,
    bibtex_key        TEXT UNIQUE,
    doi               TEXT UNIQUE,
    title             TEXT NOT NULL,
    short_title       TEXT,
    publication_type  TEXT NOT NULL CHECK(publication_type IN ('monograph', 'edited_volume', 'journal_article', 'series_volume', 'digital_edition', 'museum_catalog', 'dissertation', 'conference_paper', 'hand_copy_publication', 'chapter', 'proceedings', 'thesis', 'report', 'unpublished', 'other')),
    year              INTEGER,
    series_key        TEXT,
    volume_in_series  TEXT,
    authors           TEXT NOT NULL,
    editors           TEXT,
    publisher         TEXT,
    place             TEXT,
    url               TEXT,
    oracc_project     TEXT,
    supersedes_id     INTEGER REFERENCES publications(id),
    superseded_scope  TEXT,
    period_coverage   TEXT, -- JSON array
    genre_coverage    TEXT, -- JSON array
    cited_by_count    INTEGER,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pub_bibtex ON publications(bibtex_key);
CREATE INDEX idx_pub_short_title ON publications(short_title);
CREATE INDEX idx_pub_series ON publications(series_key, volume_in_series);
CREATE INDEX idx_pub_oracc ON publications(oracc_project);
CREATE INDEX idx_pub_supersedes ON publications(supersedes_id);

-- Now add deferred FK from annotation_runs to publications
ALTER TABLE annotation_runs ADD CONSTRAINT fk_annotation_runs_publication
    FOREIGN KEY (publication_id) REFERENCES publications(id);

CREATE TABLE publication_authors (
    id              SERIAL PRIMARY KEY,
    publication_id  INTEGER NOT NULL REFERENCES publications(id),
    scholar_id      INTEGER NOT NULL REFERENCES scholars(id),
    role            TEXT DEFAULT 'author' CHECK(role IN ('author', 'editor', 'translator', 'contributor')),
    position        INTEGER,
    UNIQUE(publication_id, scholar_id, role)
);

CREATE TABLE artifact_editions (
    id                    SERIAL PRIMARY KEY,
    p_number              TEXT NOT NULL REFERENCES artifacts(p_number),
    publication_id        INTEGER NOT NULL REFERENCES publications(id),
    reference_string      TEXT NOT NULL,
    reference_normalized  TEXT NOT NULL,
    page_start            INTEGER,
    page_end              INTEGER,
    plate_no              TEXT,
    item_no               TEXT,
    edition_type          TEXT NOT NULL CHECK(edition_type IN ('full_edition', 'hand_copy', 'photograph_only', 'catalog_entry', 'brief_mention', 'collation', 'translation_only', 'commentary')),
    is_current_edition    INTEGER DEFAULT 0,
    supersedes_id         INTEGER REFERENCES artifact_editions(id),
    annotation_run_id     INTEGER REFERENCES annotation_runs(id),
    confidence            REAL DEFAULT 1.0,
    note                  TEXT,
    UNIQUE(p_number, publication_id, reference_string)
);

CREATE INDEX idx_ae_p_number ON artifact_editions(p_number);
CREATE INDEX idx_ae_publication ON artifact_editions(publication_id);
CREATE INDEX idx_ae_reference ON artifact_editions(reference_normalized);
CREATE INDEX idx_ae_current ON artifact_editions(p_number, is_current_edition) WHERE is_current_edition = 1;
CREATE INDEX idx_ae_supersedes ON artifact_editions(supersedes_id);

CREATE TABLE artifact_edition_evidence (
    id                   SERIAL PRIMARY KEY,
    artifact_edition_id  INTEGER NOT NULL REFERENCES artifact_editions(id),
    evidence_type        TEXT CHECK(evidence_type IN ('catalog_entry', 'publication_page', 'museum_record', 'cdli_reference', 'personal_communication', 'database_export')),
    evidence_ref         TEXT,
    added_by             INTEGER REFERENCES scholars(id),
    added_at             TIMESTAMPTZ DEFAULT NOW(),
    note                 TEXT
);

CREATE TABLE artifact_edition_decisions (
    id                   SERIAL PRIMARY KEY,
    artifact_edition_id  INTEGER NOT NULL REFERENCES artifact_editions(id),
    decided_by           INTEGER REFERENCES scholars(id),
    decision_method      TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale            TEXT,
    decided_at           TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id        INTEGER REFERENCES artifact_edition_decisions(id)
);

CREATE TABLE publication_citations (
    id        SERIAL PRIMARY KEY,
    citing_id INTEGER NOT NULL REFERENCES publications(id),
    cited_id  INTEGER NOT NULL REFERENCES publications(id),
    UNIQUE(citing_id, cited_id)
);

-- ═══════════════════════════════════════════════════════════
-- ANNOTATION ECOSYSTEM
-- ═══════════════════════════════════════════════════════════

CREATE TABLE join_groups (
    id              SERIAL PRIMARY KEY,
    designation     TEXT,
    fragment_count  INTEGER DEFAULT 2,
    status          TEXT DEFAULT 'partial' CHECK(status IN ('partial', 'complete', 'disputed')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT
);

CREATE TABLE fragment_joins (
    id                    SERIAL PRIMARY KEY,
    fragment_a            TEXT NOT NULL REFERENCES artifacts(p_number),
    fragment_b            TEXT NOT NULL REFERENCES artifacts(p_number),
    join_group_id         INTEGER REFERENCES join_groups(id), -- nullable: NULL = raw CDLI import, non-NULL = curated group
    join_type             TEXT CHECK(join_type IN ('direct', 'indirect', 'uncertain')),
    spatial_description   TEXT,
    annotation_run_id     INTEGER REFERENCES annotation_runs(id),
    confidence            REAL,
    is_accepted           INTEGER DEFAULT 0,
    status                TEXT DEFAULT 'proposed' CHECK(status IN ('proposed', 'verified', 'accepted', 'rejected')),
    proposed_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fragment_a, fragment_b)
);

CREATE INDEX idx_fj_fragment_a ON fragment_joins(fragment_a);
CREATE INDEX idx_fj_fragment_b ON fragment_joins(fragment_b);
CREATE INDEX idx_fj_status ON fragment_joins(status);
CREATE INDEX idx_fj_group ON fragment_joins(join_group_id);

CREATE TABLE fragment_join_evidence (
    id              SERIAL PRIMARY KEY,
    join_id         INTEGER NOT NULL REFERENCES fragment_joins(id),
    evidence_type   TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'physical_inspection', 'textual_continuity')),
    evidence_ref    TEXT,
    supports_join   INTEGER DEFAULT 1,
    added_by        INTEGER REFERENCES scholars(id),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    note            TEXT
);

CREATE TABLE fragment_join_decisions (
    id              SERIAL PRIMARY KEY,
    join_id         INTEGER NOT NULL REFERENCES fragment_joins(id),
    decided_by      INTEGER REFERENCES scholars(id),
    decision_method TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'museum_verification')),
    decision        TEXT CHECK(decision IN ('accept', 'reject', 'defer')),
    rationale       TEXT,
    decided_at      TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id   INTEGER REFERENCES fragment_join_decisions(id)
);

CREATE TABLE scholarly_annotations (
    id                SERIAL PRIMARY KEY,
    -- Strict FK targets: exactly one non-NULL per row
    artifact_id       TEXT REFERENCES artifacts(p_number),
    surface_id        INTEGER REFERENCES surfaces(id),
    line_id           INTEGER REFERENCES text_lines(id),
    token_id          INTEGER REFERENCES tokens(id),
    sign_id           TEXT REFERENCES signs(sign_id),
    composite_id      TEXT REFERENCES composites(q_number),
    -- Range targeting
    token_end_id      INTEGER REFERENCES tokens(id),
    line_end_id       INTEGER REFERENCES text_lines(id),
    -- Content
    annotation_type   TEXT NOT NULL CHECK(annotation_type IN ('textual_criticism', 'parallel_passage', 'historical_context', 'cultural_note', 'linguistic_note', 'paleographic_note', 'prosopographic_note', 'bibliography', 'conservation_note', 'museum_note', 'pedagogy', 'methodology', 'editorial_note')),
    content           TEXT NOT NULL,
    "references"      TEXT, -- JSON array
    tags              TEXT, -- JSON array
    -- Provenance
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL,
    -- Versioning
    supersedes_id     INTEGER REFERENCES scholarly_annotations(id),
    version           INTEGER DEFAULT 1,
    -- Visibility
    visibility        TEXT DEFAULT 'public' CHECK(visibility IN ('public', 'project', 'private')),
    -- Timestamps
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ,
    -- Exactly one target FK must be non-NULL
    CHECK((CASE WHEN artifact_id IS NOT NULL THEN 1 ELSE 0 END +
           CASE WHEN surface_id IS NOT NULL THEN 1 ELSE 0 END +
           CASE WHEN line_id IS NOT NULL THEN 1 ELSE 0 END +
           CASE WHEN token_id IS NOT NULL THEN 1 ELSE 0 END +
           CASE WHEN sign_id IS NOT NULL THEN 1 ELSE 0 END +
           CASE WHEN composite_id IS NOT NULL THEN 1 ELSE 0 END) = 1)
);

CREATE INDEX idx_sa_artifact ON scholarly_annotations(artifact_id);
CREATE INDEX idx_sa_line ON scholarly_annotations(line_id);
CREATE INDEX idx_sa_token ON scholarly_annotations(token_id);
CREATE INDEX idx_sa_type ON scholarly_annotations(annotation_type);
CREATE INDEX idx_sa_run ON scholarly_annotations(annotation_run_id);

CREATE TABLE scholarly_annotation_evidence (
    id              SERIAL PRIMARY KEY,
    annotation_id   INTEGER NOT NULL REFERENCES scholarly_annotations(id),
    evidence_type   TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output', 'personal_communication')),
    evidence_ref    TEXT,
    added_by        INTEGER REFERENCES scholars(id),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    note            TEXT
);

-- ═══════════════════════════════════════════════════════════
-- DISCUSSION THREADS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE token_reading_discussion_threads (
    id                       SERIAL PRIMARY KEY,
    token_reading_id         INTEGER NOT NULL REFERENCES token_readings(id),
    title                    TEXT,
    status                   TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'archived')),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    resolved_at              TIMESTAMPTZ,
    resolution_decision_id   INTEGER REFERENCES token_reading_decisions(id),
    resolution_note          TEXT
);

CREATE TABLE lemmatization_discussion_threads (
    id                       SERIAL PRIMARY KEY,
    lemmatization_id         INTEGER NOT NULL REFERENCES lemmatizations(id),
    title                    TEXT,
    status                   TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'archived')),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    resolved_at              TIMESTAMPTZ,
    resolution_decision_id   INTEGER REFERENCES lemmatization_decisions(id),
    resolution_note          TEXT
);

CREATE TABLE translation_discussion_threads (
    id                       SERIAL PRIMARY KEY,
    translation_id           INTEGER NOT NULL REFERENCES translations(id),
    title                    TEXT,
    status                   TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'archived')),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    resolved_at              TIMESTAMPTZ,
    resolution_decision_id   INTEGER REFERENCES translation_decisions(id),
    resolution_note          TEXT
);

CREATE TABLE fragment_join_discussion_threads (
    id                       SERIAL PRIMARY KEY,
    join_id                  INTEGER NOT NULL REFERENCES fragment_joins(id),
    title                    TEXT,
    status                   TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'archived')),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    resolved_at              TIMESTAMPTZ,
    resolution_decision_id   INTEGER REFERENCES fragment_join_decisions(id),
    resolution_note          TEXT
);

CREATE TABLE scholarly_annotation_discussion_threads (
    id                       SERIAL PRIMARY KEY,
    annotation_id            INTEGER NOT NULL REFERENCES scholarly_annotations(id),
    title                    TEXT,
    status                   TEXT DEFAULT 'open' CHECK(status IN ('open', 'resolved', 'archived')),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    resolved_at              TIMESTAMPTZ,
    resolution_note          TEXT
);

CREATE TABLE discussion_posts (
    id            SERIAL PRIMARY KEY,
    thread_type   TEXT NOT NULL CHECK(thread_type IN ('token_reading', 'lemmatization', 'translation', 'fragment_join', 'scholarly_annotation')),
    thread_id     INTEGER NOT NULL,
    scholar_id    INTEGER NOT NULL REFERENCES scholars(id),
    reply_to_id   INTEGER REFERENCES discussion_posts(id),
    content       TEXT NOT NULL,
    post_type     TEXT CHECK(post_type IN ('observation', 'counterargument', 'evidence', 'question', 'synthesis', 'endorsement')),
    evidence_ref  TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    edited_at     TIMESTAMPTZ
);

-- ═══════════════════════════════════════════════════════════
-- KNOWLEDGE GRAPH
-- ═══════════════════════════════════════════════════════════

CREATE TABLE named_entities (
    id                  SERIAL PRIMARY KEY,
    entity_type         TEXT NOT NULL CHECK(entity_type IN ('person', 'deity', 'place', 'institution', 'work', 'watercourse', 'month', 'ethnonym', 'festival')),
    canonical_name      TEXT NOT NULL,
    guide_word          TEXT,
    alternate_names     TEXT, -- JSON array
    language_names      TEXT, -- JSON object
    primary_language    TEXT,
    glossary_entry_id   TEXT REFERENCES glossary_entries(entry_id),
    description         TEXT
);

CREATE INDEX idx_ne_type ON named_entities(entity_type);
CREATE INDEX idx_ne_name ON named_entities(canonical_name);
CREATE INDEX idx_ne_glossary ON named_entities(glossary_entry_id);

CREATE TABLE entity_aliases (
    id                  SERIAL PRIMARY KEY,
    canonical_entity_id INTEGER NOT NULL REFERENCES named_entities(id),
    alias_entity_id     INTEGER NOT NULL REFERENCES named_entities(id),
    merged_by           INTEGER REFERENCES scholars(id),
    rationale           TEXT,
    merged_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(canonical_entity_id, alias_entity_id)
);

CREATE TABLE entity_mentions (
    id                SERIAL PRIMARY KEY,
    entity_id         INTEGER NOT NULL REFERENCES named_entities(id),
    token_id          INTEGER REFERENCES tokens(id),
    token_end_id      INTEGER REFERENCES tokens(id),
    line_id           INTEGER REFERENCES text_lines(id),
    mention_type      TEXT CHECK(mention_type IN ('explicit', 'epithet', 'implicit', 'restored')),
    role              TEXT,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL,
    is_consensus      INTEGER DEFAULT 0,
    note              TEXT,
    CHECK((token_id IS NOT NULL) OR (line_id IS NOT NULL))
);

CREATE INDEX idx_em_entity ON entity_mentions(entity_id);
CREATE INDEX idx_em_token ON entity_mentions(token_id);
CREATE INDEX idx_em_line ON entity_mentions(line_id);
CREATE INDEX idx_em_run ON entity_mentions(annotation_run_id);

CREATE TABLE entity_mention_evidence (
    id                  SERIAL PRIMARY KEY,
    entity_mention_id   INTEGER NOT NULL REFERENCES entity_mentions(id),
    evidence_type       TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output', 'prosopographic_database')),
    evidence_ref        TEXT,
    added_by            INTEGER REFERENCES scholars(id),
    added_at            TIMESTAMPTZ DEFAULT NOW(),
    note                TEXT
);

CREATE TABLE entity_mention_decisions (
    id                  SERIAL PRIMARY KEY,
    entity_mention_id   INTEGER NOT NULL REFERENCES entity_mentions(id),
    decided_by          INTEGER REFERENCES scholars(id),
    decision_method     TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale           TEXT,
    decided_at          TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id       INTEGER REFERENCES entity_mention_decisions(id)
);

CREATE TABLE relationship_predicates (
    predicate    TEXT PRIMARY KEY,
    category     TEXT CHECK(category IN ('familial', 'political', 'religious', 'geographic', 'institutional', 'textual', 'lexical', 'identity')),
    is_symmetric INTEGER DEFAULT 0,
    description  TEXT
);

-- Seed Tier 1 predicates
INSERT INTO relationship_predicates (predicate, category, is_symmetric, description) VALUES
    ('father_of', 'familial', 0, 'Biological parent'),
    ('successor_of', 'familial', 0, 'Dynastic succession'),
    ('contemporary_of', 'familial', 1, 'Reign overlap'),
    ('spouse_of', 'familial', 1, 'Marriage'),
    ('patron_deity_of', 'religious', 0, 'Primary divine protector of a place or institution'),
    ('dedicated_to', 'religious', 0, 'Temple/offering dedication'),
    ('cult_center_of', 'religious', 0, 'Primary worship location'),
    ('located_in', 'geographic', 0, 'Spatial containment'),
    ('sumerian_equivalent', 'lexical', 1, 'Cross-linguistic equivalence'),
    ('synonym', 'lexical', 1, 'Same-language semantic equivalence'),
    ('hypernym', 'lexical', 0, 'Broader category'),
    ('manuscript_of', 'textual', 0, 'Artifact is witness to literary work'),
    ('same_as', 'identity', 1, 'Cross-system identity assertion');

CREATE TABLE entity_relationships (
    id                  SERIAL PRIMARY KEY,
    subject_id          INTEGER NOT NULL REFERENCES named_entities(id),
    predicate_enum      TEXT REFERENCES relationship_predicates(predicate),
    predicate_custom    TEXT,
    object_id           INTEGER NOT NULL REFERENCES named_entities(id),
    period_start        TEXT,
    period_end          TEXT,
    date_bce            INTEGER,
    source_mention_id   INTEGER REFERENCES entity_mentions(id),
    annotation_run_id   INTEGER REFERENCES annotation_runs(id),
    confidence          REAL,
    is_consensus        INTEGER DEFAULT 0,
    note                TEXT,
    CHECK((predicate_enum IS NOT NULL) != (predicate_custom IS NOT NULL))
);

CREATE INDEX idx_er_subject ON entity_relationships(subject_id);
CREATE INDEX idx_er_object ON entity_relationships(object_id);
CREATE INDEX idx_er_predicate ON entity_relationships(predicate_enum);
CREATE INDEX idx_er_custom ON entity_relationships(predicate_custom);
CREATE INDEX idx_er_period ON entity_relationships(period_start);

CREATE TABLE entity_relationship_evidence (
    id              SERIAL PRIMARY KEY,
    relationship_id INTEGER NOT NULL REFERENCES entity_relationships(id),
    evidence_type   TEXT CHECK(evidence_type IN ('photograph', 'hand_copy', 'collation_note', 'publication', '3d_scan', 'RTI_image', 'ML_output', 'prosopographic_database', 'royal_inscription', 'administrative_text')),
    evidence_ref    TEXT,
    added_by        INTEGER REFERENCES scholars(id),
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    note            TEXT
);

CREATE TABLE entity_relationship_decisions (
    id              SERIAL PRIMARY KEY,
    relationship_id INTEGER NOT NULL REFERENCES entity_relationships(id),
    decided_by      INTEGER REFERENCES scholars(id),
    decision_method TEXT CHECK(decision_method IN ('editorial', 'vote', 'algorithm', 'import_default')),
    rationale       TEXT,
    decided_at      TIMESTAMPTZ DEFAULT NOW(),
    supersedes_id   INTEGER REFERENCES entity_relationship_decisions(id)
);

-- ═══════════════════════════════════════════════════════════
-- AUTHORITY RECONCILIATION
-- ═══════════════════════════════════════════════════════════

CREATE TABLE authority_links (
    id                SERIAL PRIMARY KEY,
    entity_id         INTEGER NOT NULL REFERENCES named_entities(id),
    authority         TEXT NOT NULL,
    external_id       TEXT NOT NULL,
    match_type        TEXT CHECK(match_type IN ('exact', 'broad', 'narrow', 'related', 'uncertain')),
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    confidence        REAL,
    is_accepted       INTEGER DEFAULT 0,
    note              TEXT,
    UNIQUE(entity_id, authority, external_id)
);

CREATE INDEX idx_al_entity ON authority_links(entity_id);
CREATE INDEX idx_al_authority ON authority_links(authority);
CREATE INDEX idx_al_external ON authority_links(external_id);

CREATE TABLE authority_reconciliation_disputes (
    id                     SERIAL PRIMARY KEY,
    authority_link_id      INTEGER NOT NULL REFERENCES authority_links(id),
    alternative_external_id TEXT NOT NULL,
    scholar_id             INTEGER NOT NULL REFERENCES scholars(id),
    rationale              TEXT,
    created_at             TIMESTAMPTZ DEFAULT NOW(),
    resolved               INTEGER DEFAULT 0
);

-- ═══════════════════════════════════════════════════════════
-- PIPELINE / STATUS TRACKING
-- ═══════════════════════════════════════════════════════════

CREATE TABLE pipeline_status (
    p_number             TEXT PRIMARY KEY REFERENCES artifacts(p_number),
    physical_complete    REAL,
    graphemic_complete   REAL,
    reading_complete     REAL,
    linguistic_complete  REAL,
    semantic_complete    REAL,
    has_image            INTEGER DEFAULT 0,
    has_atf              INTEGER DEFAULT 0,
    has_lemmas           INTEGER DEFAULT 0,
    has_translation      INTEGER DEFAULT 0,
    has_sign_annotations INTEGER DEFAULT 0,
    quality_score        REAL,
    last_updated         TIMESTAMPTZ
);

CREATE TABLE import_log (
    id                SERIAL PRIMARY KEY,
    source            TEXT,
    file_path         TEXT,
    records_imported  INTEGER,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    imported_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- USER FEATURES
-- ═══════════════════════════════════════════════════════════

CREATE TABLE collections (
    collection_id SERIAL PRIMARY KEY,
    name          TEXT,
    description   TEXT,
    image_path    TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ
);

CREATE TABLE collection_members (
    collection_id INTEGER NOT NULL REFERENCES collections(collection_id),
    p_number      TEXT NOT NULL REFERENCES artifacts(p_number),
    PRIMARY KEY (collection_id, p_number)
);

-- ═══════════════════════════════════════════════════════════
-- CAD (future, empty tables)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE cad_entries (
    id        SERIAL PRIMARY KEY,
    headword  TEXT,
    volume    TEXT,
    page      TEXT,
    pos       TEXT,
    language  TEXT
);

CREATE TABLE cad_meanings (
    id          SERIAL PRIMARY KEY,
    entry_id    INTEGER REFERENCES cad_entries(id),
    meaning     TEXT,
    sub_meaning TEXT
);

CREATE TABLE cad_examples (
    id         SERIAL PRIMARY KEY,
    meaning_id INTEGER REFERENCES cad_meanings(id),
    text       TEXT,
    reference  TEXT
);

-- ═══════════════════════════════════════════════════════════
-- EXTERNAL RESOURCES (carry forward)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE external_resources (
    id          SERIAL PRIMARY KEY,
    p_number    TEXT REFERENCES artifacts(p_number),
    name        TEXT,
    url         TEXT,
    description TEXT
);

-- ═══════════════════════════════════════════════════════════
-- IMPORT STAGING (for manual review)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE _dedup_candidates (
    id              SERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    record_a_id     INTEGER,
    record_b_id     INTEGER,
    confidence      REAL,
    match_reason    TEXT,
    resolved        INTEGER DEFAULT 0,
    resolution      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE _unparsed_records (
    id                SERIAL PRIMARY KEY,
    source_script     TEXT NOT NULL,
    source_table      TEXT NOT NULL,
    raw_value         TEXT NOT NULL,
    parse_error       TEXT,
    p_number          TEXT,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- VIEWS
-- ═══════════════════════════════════════════════════════════

CREATE VIEW scholarly_annotations_w3c AS
SELECT
    'https://glintstone.app/anno/' || sa.id AS id,
    'Annotation' AS type,
    json_build_object(
        'id', 'https://orcid.org/' || s.orcid,
        'name', s.name,
        'affiliation', s.institution
    ) AS creator,
    sa.created_at AS created,
    sa.updated_at AS modified,
    sa.annotation_type AS motivation,
    json_build_object(
        'source', COALESCE(
            'cuneiform:' || sa.artifact_id,
            'cuneiform:surface:' || sa.surface_id::text,
            'cuneiform:line:' || sa.line_id::text,
            'cuneiform:token:' || sa.token_id::text,
            'cuneiform:sign:' || sa.sign_id,
            'cuneiform:composite:' || sa.composite_id
        )
    ) AS target,
    json_build_object(
        'type', 'TextualBody',
        'value', sa.content,
        'format', 'text/plain'
    ) AS body,
    sa.confidence,
    sa.visibility
FROM scholarly_annotations sa
LEFT JOIN annotation_runs ar ON sa.annotation_run_id = ar.id
LEFT JOIN scholars s ON ar.scholar_id = s.id
WHERE sa.visibility = 'public';

-- ═══════════════════════════════════════════════════════════
-- STAGING TABLES (prefixed with _ to distinguish from schema)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS _unparsed_records (
    id SERIAL PRIMARY KEY,
    source_script TEXT NOT NULL,
    p_number TEXT,
    raw_text TEXT NOT NULL,
    parse_tier TEXT,
    reason TEXT,
    annotation_run_id INTEGER REFERENCES annotation_runs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_unparsed_source ON _unparsed_records(source_script);
CREATE INDEX idx_unparsed_p_number ON _unparsed_records(p_number);

-- ═══════════════════════════════════════════════════════════
-- SCHEMA VERSION
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS _schema_version (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO _schema_version (key, value) VALUES ('version', '2.0.0');
