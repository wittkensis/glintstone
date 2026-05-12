--
-- PostgreSQL database dump
--


-- Dumped from database version 17.8 (Homebrew)
-- Dumped by pg_dump version 17.8 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _dedup_candidates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public._dedup_candidates (
    id integer NOT NULL,
    table_name text NOT NULL,
    record_a_id integer,
    record_b_id integer,
    confidence real,
    match_reason text,
    resolved integer DEFAULT 0,
    resolution text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: _dedup_candidates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public._dedup_candidates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: _dedup_candidates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public._dedup_candidates_id_seq OWNED BY public._dedup_candidates.id;


--
-- Name: _schema_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public._schema_version (
    key text NOT NULL,
    value text NOT NULL
);


--
-- Name: _unparsed_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public._unparsed_records (
    id integer NOT NULL,
    source_script text NOT NULL,
    source_table text NOT NULL,
    raw_value text NOT NULL,
    parse_error text,
    p_number text,
    annotation_run_id integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: _unparsed_records_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public._unparsed_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: _unparsed_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public._unparsed_records_id_seq OWNED BY public._unparsed_records.id;


--
-- Name: annotation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.annotation_runs (
    id integer NOT NULL,
    source_type text,
    source_name text,
    model_version text,
    created_at timestamp with time zone DEFAULT now(),
    corpus_scope text,
    notes text,
    scholar_id integer,
    method text,
    publication_ref text,
    publication_id integer,
    CONSTRAINT annotation_runs_method_check CHECK ((method = ANY (ARRAY['hand_copy'::text, 'photograph'::text, 'collation'::text, 'autopsy'::text, 'RTI'::text, '3D_scan'::text, 'ML_model'::text, 'import'::text, 'api_fetch'::text, 'web_scrape'::text, 'manual'::text, 'model'::text]))),
    CONSTRAINT annotation_runs_source_type_check CHECK ((source_type = ANY (ARRAY['human'::text, 'model'::text, 'hybrid'::text, 'import'::text])))
);


--
-- Name: annotation_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.annotation_runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: annotation_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.annotation_runs_id_seq OWNED BY public.annotation_runs.id;


--
-- Name: artifact_composites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_composites (
    p_number text NOT NULL,
    q_number text NOT NULL,
    line_ref text
);


--
-- Name: artifact_credits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_credits (
    id integer NOT NULL,
    p_number text NOT NULL,
    oracc_project text NOT NULL,
    credits_text text NOT NULL
);


--
-- Name: artifact_credits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_credits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_credits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_credits_id_seq OWNED BY public.artifact_credits.id;


--
-- Name: artifact_edition_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_edition_decisions (
    id integer NOT NULL,
    artifact_edition_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT artifact_edition_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: artifact_edition_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_edition_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_edition_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_edition_decisions_id_seq OWNED BY public.artifact_edition_decisions.id;


--
-- Name: artifact_edition_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_edition_evidence (
    id integer NOT NULL,
    artifact_edition_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT artifact_edition_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['catalog_entry'::text, 'publication_page'::text, 'museum_record'::text, 'cdli_reference'::text, 'personal_communication'::text, 'database_export'::text])))
);


--
-- Name: artifact_edition_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_edition_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_edition_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_edition_evidence_id_seq OWNED BY public.artifact_edition_evidence.id;


--
-- Name: artifact_editions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_editions (
    id integer NOT NULL,
    p_number text NOT NULL,
    publication_id integer NOT NULL,
    reference_string text NOT NULL,
    reference_normalized text NOT NULL,
    page_start integer,
    page_end integer,
    plate_no text,
    item_no text,
    edition_type text NOT NULL,
    is_current_edition integer DEFAULT 0,
    supersedes_id integer,
    annotation_run_id integer,
    confidence real DEFAULT 1.0,
    note text,
    CONSTRAINT artifact_editions_edition_type_check CHECK ((edition_type = ANY (ARRAY['full_edition'::text, 'hand_copy'::text, 'photograph_only'::text, 'catalog_entry'::text, 'brief_mention'::text, 'collation'::text, 'translation_only'::text, 'commentary'::text])))
);


--
-- Name: artifact_editions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_editions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_editions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_editions_id_seq OWNED BY public.artifact_editions.id;


--
-- Name: artifact_genres; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_genres (
    p_number text NOT NULL,
    genre_id integer NOT NULL,
    confidence real DEFAULT 1.0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL
);


--
-- Name: artifact_identifier_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_identifier_decisions (
    id integer NOT NULL,
    artifact_identifier_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT artifact_identifier_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'museum_verification'::text, 'import_default'::text])))
);


--
-- Name: artifact_identifier_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_identifier_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_identifier_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_identifier_decisions_id_seq OWNED BY public.artifact_identifier_decisions.id;


--
-- Name: artifact_identifier_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_identifier_evidence (
    id integer NOT NULL,
    artifact_identifier_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT artifact_identifier_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['catalog_entry'::text, 'museum_record'::text, 'publication'::text, 'photograph'::text, 'autopsy'::text, 'database_export'::text, 'personal_communication'::text])))
);


--
-- Name: artifact_identifier_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_identifier_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_identifier_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_identifier_evidence_id_seq OWNED BY public.artifact_identifier_evidence.id;


--
-- Name: artifact_identifiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_identifiers (
    id integer NOT NULL,
    p_number text NOT NULL,
    identifier_type text NOT NULL,
    identifier_value text NOT NULL,
    identifier_normalized text NOT NULL,
    authority text,
    is_current integer DEFAULT 1,
    annotation_run_id integer,
    confidence real DEFAULT 1.0,
    note text,
    CONSTRAINT artifact_identifiers_identifier_type_check CHECK ((identifier_type = ANY (ARRAY['museum_no'::text, 'excavation_no'::text, 'accession_no'::text, 'publication'::text, 'cdli_designation'::text, 'oracc_project'::text, 'ark'::text, 'collection_no'::text, 'seal_id'::text])))
);


--
-- Name: artifact_identifiers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.artifact_identifiers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: artifact_identifiers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.artifact_identifiers_id_seq OWNED BY public.artifact_identifiers.id;


--
-- Name: artifact_languages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_languages (
    p_number text NOT NULL,
    language_id integer NOT NULL,
    confidence real DEFAULT 1.0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL
);


--
-- Name: artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifacts (
    p_number text NOT NULL,
    designation text,
    museum_no text,
    excavation_no text,
    material text,
    object_type text,
    width real,
    height real,
    thickness real,
    seal_id text,
    object_preservation text,
    period text,
    period_normalized text,
    provenience text,
    provenience_normalized text,
    genre text,
    subgenre text,
    supergenre text,
    language text,
    languages text,
    pleiades_id text,
    latitude real,
    longitude real,
    primary_publication text,
    collection text,
    dates_referenced text,
    date_of_origin text,
    findspot_square text,
    accounting_period text,
    acquisition_history text,
    cdli_updated_at timestamp with time zone,
    oracc_projects text,
    annotation_run_id integer,
    language_normalized text,
    atf_source text,
    translation_source text,
    publication_author text,
    cdli_date_entered text,
    db_source text
);


--
-- Name: authority_links; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.authority_links (
    id integer NOT NULL,
    entity_id integer NOT NULL,
    authority text NOT NULL,
    external_id text NOT NULL,
    match_type text,
    annotation_run_id integer,
    confidence real,
    is_accepted integer DEFAULT 0,
    note text,
    CONSTRAINT authority_links_match_type_check CHECK ((match_type = ANY (ARRAY['exact'::text, 'broad'::text, 'narrow'::text, 'related'::text, 'uncertain'::text])))
);


--
-- Name: authority_links_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.authority_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: authority_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.authority_links_id_seq OWNED BY public.authority_links.id;


--
-- Name: authority_reconciliation_disputes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.authority_reconciliation_disputes (
    id integer NOT NULL,
    authority_link_id integer NOT NULL,
    alternative_external_id text NOT NULL,
    scholar_id integer NOT NULL,
    rationale text,
    created_at timestamp with time zone DEFAULT now(),
    resolved integer DEFAULT 0
);


--
-- Name: authority_reconciliation_disputes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.authority_reconciliation_disputes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: authority_reconciliation_disputes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.authority_reconciliation_disputes_id_seq OWNED BY public.authority_reconciliation_disputes.id;


--
-- Name: cad_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cad_entries (
    id integer NOT NULL,
    headword text,
    volume text,
    page text,
    pos text,
    language text
);


--
-- Name: cad_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cad_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cad_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cad_entries_id_seq OWNED BY public.cad_entries.id;


--
-- Name: cad_examples; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cad_examples (
    id integer NOT NULL,
    meaning_id integer,
    text text,
    reference text
);


--
-- Name: cad_examples_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cad_examples_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cad_examples_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cad_examples_id_seq OWNED BY public.cad_examples.id;


--
-- Name: cad_meanings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cad_meanings (
    id integer NOT NULL,
    entry_id integer,
    meaning text,
    sub_meaning text
);


--
-- Name: cad_meanings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cad_meanings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cad_meanings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cad_meanings_id_seq OWNED BY public.cad_meanings.id;


--
-- Name: canonical_genres; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.canonical_genres (
    id integer NOT NULL,
    name text NOT NULL
);


--
-- Name: canonical_genres_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.canonical_genres_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: canonical_genres_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.canonical_genres_id_seq OWNED BY public.canonical_genres.id;


--
-- Name: canonical_languages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.canonical_languages (
    id integer NOT NULL,
    name text NOT NULL,
    oracc_code text,
    family text
);


--
-- Name: canonical_languages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.canonical_languages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: canonical_languages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.canonical_languages_id_seq OWNED BY public.canonical_languages.id;


--
-- Name: collection_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collection_members (
    collection_id integer NOT NULL,
    p_number text NOT NULL
);


--
-- Name: collections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.collections (
    collection_id integer NOT NULL,
    name text,
    description text,
    image_path text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: collections_collection_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.collections_collection_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: collections_collection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.collections_collection_id_seq OWNED BY public.collections.collection_id;


--
-- Name: composites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.composites (
    q_number text NOT NULL,
    designation text,
    language text,
    period text,
    genre text,
    exemplar_count integer
);


--
-- Name: concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.concepts (
    id integer NOT NULL,
    canonical_name text NOT NULL,
    domain_path text,
    description text,
    parent_concept_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: glossary_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_entries (
    entry_id text NOT NULL,
    headword text,
    citation_form text,
    guide_word text,
    language text,
    pos text,
    icount integer,
    project text,
    normalized_headword text,
    periods text,
    norms text,
    annotation_run_id integer
);


--
-- Name: lemma_concepts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemma_concepts (
    lemma_entry_id text NOT NULL,
    concept_id integer NOT NULL,
    relationship_type text DEFAULT 'primary'::text,
    confidence real DEFAULT 1.0,
    annotation_run_id integer,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT lemma_concepts_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT lemma_concepts_relationship_type_check CHECK ((relationship_type = ANY (ARRAY['primary'::text, 'secondary'::text, 'metaphorical'::text, 'specialized'::text])))
);


--
-- Name: concept_lemmas; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.concept_lemmas AS
 SELECT c.id AS concept_id,
    c.canonical_name,
    c.domain_path,
    json_agg(json_build_object('entry_id', ge.entry_id, 'citation_form', ge.citation_form, 'guide_word', ge.guide_word, 'language', ge.language, 'pos', ge.pos, 'relationship', lc.relationship_type, 'confidence', lc.confidence) ORDER BY lc.confidence DESC, ge.language, ge.citation_form) FILTER (WHERE (ge.entry_id IS NOT NULL)) AS lemmas
   FROM ((public.concepts c
     LEFT JOIN public.lemma_concepts lc ON ((c.id = lc.concept_id)))
     LEFT JOIN public.glossary_entries ge ON ((lc.lemma_entry_id = ge.entry_id)))
  GROUP BY c.id, c.canonical_name, c.domain_path;


--
-- Name: concepts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.concepts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: concepts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.concepts_id_seq OWNED BY public.concepts.id;


--
-- Name: discussion_posts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discussion_posts (
    id integer NOT NULL,
    thread_type text NOT NULL,
    thread_id integer NOT NULL,
    scholar_id integer NOT NULL,
    reply_to_id integer,
    content text NOT NULL,
    post_type text,
    evidence_ref text,
    created_at timestamp with time zone DEFAULT now(),
    edited_at timestamp with time zone,
    CONSTRAINT discussion_posts_post_type_check CHECK ((post_type = ANY (ARRAY['observation'::text, 'counterargument'::text, 'evidence'::text, 'question'::text, 'synthesis'::text, 'endorsement'::text]))),
    CONSTRAINT discussion_posts_thread_type_check CHECK ((thread_type = ANY (ARRAY['token_reading'::text, 'lemmatization'::text, 'translation'::text, 'fragment_join'::text, 'scholarly_annotation'::text])))
);


--
-- Name: discussion_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.discussion_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: discussion_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.discussion_posts_id_seq OWNED BY public.discussion_posts.id;


--
-- Name: entity_aliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_aliases (
    id integer NOT NULL,
    canonical_entity_id integer NOT NULL,
    alias_entity_id integer NOT NULL,
    merged_by integer,
    rationale text,
    merged_at timestamp with time zone DEFAULT now()
);


--
-- Name: entity_aliases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_aliases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_aliases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_aliases_id_seq OWNED BY public.entity_aliases.id;


--
-- Name: entity_mention_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_mention_decisions (
    id integer NOT NULL,
    entity_mention_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT entity_mention_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: entity_mention_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_mention_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_mention_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_mention_decisions_id_seq OWNED BY public.entity_mention_decisions.id;


--
-- Name: entity_mention_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_mention_evidence (
    id integer NOT NULL,
    entity_mention_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT entity_mention_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text, 'prosopographic_database'::text])))
);


--
-- Name: entity_mention_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_mention_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_mention_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_mention_evidence_id_seq OWNED BY public.entity_mention_evidence.id;


--
-- Name: entity_mentions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_mentions (
    id integer NOT NULL,
    entity_id integer NOT NULL,
    token_id integer,
    token_end_id integer,
    line_id integer,
    mention_type text,
    role text,
    annotation_run_id integer,
    confidence real,
    is_consensus integer DEFAULT 0,
    note text,
    CONSTRAINT entity_mentions_check CHECK (((token_id IS NOT NULL) OR (line_id IS NOT NULL))),
    CONSTRAINT entity_mentions_mention_type_check CHECK ((mention_type = ANY (ARRAY['explicit'::text, 'epithet'::text, 'implicit'::text, 'restored'::text])))
);


--
-- Name: entity_mentions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_mentions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_mentions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_mentions_id_seq OWNED BY public.entity_mentions.id;


--
-- Name: entity_relationship_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_relationship_decisions (
    id integer NOT NULL,
    relationship_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT entity_relationship_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: entity_relationship_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_relationship_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_relationship_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_relationship_decisions_id_seq OWNED BY public.entity_relationship_decisions.id;


--
-- Name: entity_relationship_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_relationship_evidence (
    id integer NOT NULL,
    relationship_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT entity_relationship_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text, 'prosopographic_database'::text, 'royal_inscription'::text, 'administrative_text'::text])))
);


--
-- Name: entity_relationship_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_relationship_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_relationship_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_relationship_evidence_id_seq OWNED BY public.entity_relationship_evidence.id;


--
-- Name: entity_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_relationships (
    id integer NOT NULL,
    subject_id integer NOT NULL,
    predicate_enum text,
    predicate_custom text,
    object_id integer NOT NULL,
    period_start text,
    period_end text,
    date_bce integer,
    source_mention_id integer,
    annotation_run_id integer,
    confidence real,
    is_consensus integer DEFAULT 0,
    note text,
    CONSTRAINT entity_relationships_check CHECK (((predicate_enum IS NOT NULL) <> (predicate_custom IS NOT NULL)))
);


--
-- Name: entity_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entity_relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entity_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entity_relationships_id_seq OWNED BY public.entity_relationships.id;


--
-- Name: excavation_sites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.excavation_sites (
    code text NOT NULL,
    name text,
    ancient_name text,
    modern_country text,
    pleiades_id text,
    latitude real,
    longitude real
);


--
-- Name: external_resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_resources (
    id integer NOT NULL,
    p_number text,
    name text,
    url text,
    description text
);


--
-- Name: external_resources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.external_resources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: external_resources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.external_resources_id_seq OWNED BY public.external_resources.id;


--
-- Name: fragment_join_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fragment_join_decisions (
    id integer NOT NULL,
    join_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    decision text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT fragment_join_decisions_decision_check CHECK ((decision = ANY (ARRAY['accept'::text, 'reject'::text, 'defer'::text]))),
    CONSTRAINT fragment_join_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'museum_verification'::text])))
);


--
-- Name: fragment_join_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fragment_join_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fragment_join_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fragment_join_decisions_id_seq OWNED BY public.fragment_join_decisions.id;


--
-- Name: fragment_join_discussion_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fragment_join_discussion_threads (
    id integer NOT NULL,
    join_id integer NOT NULL,
    title text,
    status text DEFAULT 'open'::text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    resolution_decision_id integer,
    resolution_note text,
    CONSTRAINT fragment_join_discussion_threads_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'archived'::text])))
);


--
-- Name: fragment_join_discussion_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fragment_join_discussion_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fragment_join_discussion_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fragment_join_discussion_threads_id_seq OWNED BY public.fragment_join_discussion_threads.id;


--
-- Name: fragment_join_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fragment_join_evidence (
    id integer NOT NULL,
    join_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    supports_join integer DEFAULT 1,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT fragment_join_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'physical_inspection'::text, 'textual_continuity'::text])))
);


--
-- Name: fragment_join_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fragment_join_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fragment_join_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fragment_join_evidence_id_seq OWNED BY public.fragment_join_evidence.id;


--
-- Name: fragment_joins; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fragment_joins (
    id integer NOT NULL,
    fragment_a text NOT NULL,
    fragment_b text NOT NULL,
    join_group_id integer,
    join_type text,
    spatial_description text,
    annotation_run_id integer,
    confidence real,
    is_accepted integer DEFAULT 0,
    status text DEFAULT 'proposed'::text,
    proposed_at timestamp with time zone DEFAULT now(),
    CONSTRAINT fragment_joins_join_type_check CHECK ((join_type = ANY (ARRAY['direct'::text, 'indirect'::text, 'uncertain'::text]))),
    CONSTRAINT fragment_joins_status_check CHECK ((status = ANY (ARRAY['proposed'::text, 'verified'::text, 'accepted'::text, 'rejected'::text])))
);


--
-- Name: fragment_joins_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fragment_joins_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fragment_joins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fragment_joins_id_seq OWNED BY public.fragment_joins.id;


--
-- Name: genre_canon; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.genre_canon (
    raw_genre text NOT NULL,
    canonical text NOT NULL,
    supergenre text
);


--
-- Name: glossary_forms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_forms (
    id integer NOT NULL,
    entry_id text NOT NULL,
    form text,
    count integer,
    norm text,
    lang text
);


--
-- Name: glossary_forms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.glossary_forms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: glossary_forms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.glossary_forms_id_seq OWNED BY public.glossary_forms.id;


--
-- Name: glossary_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_relationships (
    id integer NOT NULL,
    from_entry_id text,
    to_entry_id text,
    relationship_type text,
    notes text,
    confidence text
);


--
-- Name: glossary_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.glossary_relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: glossary_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.glossary_relationships_id_seq OWNED BY public.glossary_relationships.id;


--
-- Name: glossary_semantic_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_semantic_fields (
    glossary_entry_id text NOT NULL,
    semantic_field_id integer NOT NULL
);


--
-- Name: glossary_senses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_senses (
    id integer NOT NULL,
    entry_id text NOT NULL,
    sense_number integer,
    guide_word text,
    definition text,
    pos text,
    signatures text
);


--
-- Name: glossary_senses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.glossary_senses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: glossary_senses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.glossary_senses_id_seq OWNED BY public.glossary_senses.id;


--
-- Name: import_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.import_log (
    id integer NOT NULL,
    source text,
    file_path text,
    records_imported integer,
    annotation_run_id integer,
    imported_at timestamp with time zone DEFAULT now()
);


--
-- Name: import_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.import_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: import_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.import_log_id_seq OWNED BY public.import_log.id;


--
-- Name: interpretations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.interpretations (
    id integer NOT NULL,
    target_type text NOT NULL,
    target_id text NOT NULL,
    claim text NOT NULL,
    confidence real,
    basis text,
    citation text,
    scholar_name text,
    annotation_run_id integer,
    supersedes_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT interpretations_basis_check CHECK ((basis = ANY (ARRAY['consensus'::text, 'revision'::text, 'speculative'::text, 'contested'::text]))),
    CONSTRAINT interpretations_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT interpretations_target_type_check CHECK ((target_type = ANY (ARRAY['reading'::text, 'lemma'::text, 'etymology'::text, 'dating'::text, 'concept'::text, 'sign'::text])))
);


--
-- Name: interpretations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.interpretations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: interpretations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.interpretations_id_seq OWNED BY public.interpretations.id;


--
-- Name: intertextuality_links; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intertextuality_links (
    id integer NOT NULL,
    source_token_start integer,
    source_token_end integer,
    target_token_start integer,
    target_token_end integer,
    link_type text,
    confidence real,
    annotation_run_id integer,
    CONSTRAINT intertextuality_links_link_type_check CHECK ((link_type = ANY (ARRAY['parallel'::text, 'quotation'::text, 'formula'::text, 'duplicate'::text, 'commentary'::text])))
);


--
-- Name: intertextuality_links_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.intertextuality_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: intertextuality_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.intertextuality_links_id_seq OWNED BY public.intertextuality_links.id;


--
-- Name: join_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.join_groups (
    id integer NOT NULL,
    designation text,
    fragment_count integer DEFAULT 2,
    status text DEFAULT 'partial'::text,
    created_at timestamp with time zone DEFAULT now(),
    notes text,
    CONSTRAINT join_groups_status_check CHECK ((status = ANY (ARRAY['partial'::text, 'complete'::text, 'disputed'::text])))
);


--
-- Name: join_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.join_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: join_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.join_groups_id_seq OWNED BY public.join_groups.id;


--
-- Name: language_map; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language_map (
    cdli_name text NOT NULL,
    oracc_code text NOT NULL,
    full_name text,
    family text,
    CONSTRAINT language_map_family_check CHECK ((family = ANY (ARRAY['sumerian'::text, 'semitic'::text, 'elamite'::text, 'hurrian'::text, 'hittite'::text, 'other'::text])))
);


--
-- Name: lemma_sign_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemma_sign_usage (
    id integer NOT NULL,
    entry_id text NOT NULL,
    sign_id text NOT NULL,
    reading_value text,
    usage_type text,
    frequency integer DEFAULT 0,
    period text,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT lemma_sign_usage_usage_type_check CHECK ((usage_type = ANY (ARRAY['logographic'::text, 'syllabic'::text, 'mixed'::text])))
);


--
-- Name: lemma_sign_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lemma_sign_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lemma_sign_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lemma_sign_usage_id_seq OWNED BY public.lemma_sign_usage.id;


--
-- Name: lemmatization_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemmatization_decisions (
    id integer NOT NULL,
    lemmatization_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT lemmatization_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: lemmatization_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lemmatization_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lemmatization_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lemmatization_decisions_id_seq OWNED BY public.lemmatization_decisions.id;


--
-- Name: lemmatization_discussion_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemmatization_discussion_threads (
    id integer NOT NULL,
    lemmatization_id integer NOT NULL,
    title text,
    status text DEFAULT 'open'::text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    resolution_decision_id integer,
    resolution_note text,
    CONSTRAINT lemmatization_discussion_threads_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'archived'::text])))
);


--
-- Name: lemmatization_discussion_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lemmatization_discussion_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lemmatization_discussion_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lemmatization_discussion_threads_id_seq OWNED BY public.lemmatization_discussion_threads.id;


--
-- Name: lemmatization_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemmatization_evidence (
    id integer NOT NULL,
    lemmatization_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT lemmatization_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text])))
);


--
-- Name: lemmatization_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lemmatization_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lemmatization_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lemmatization_evidence_id_seq OWNED BY public.lemmatization_evidence.id;


--
-- Name: lemmatizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lemmatizations (
    id integer NOT NULL,
    token_id integer NOT NULL,
    citation_form text,
    guide_word text,
    sense text,
    pos text,
    epos text,
    norm text,
    base text,
    signature text,
    morph_raw text,
    annotation_run_id integer,
    confidence real,
    is_consensus integer DEFAULT 0,
    entry_id text,
    language text,
    norm_id integer
);


--
-- Name: lemmatizations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lemmatizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lemmatizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lemmatizations_id_seq OWNED BY public.lemmatizations.id;


--
-- Name: lexical_lemmas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_lemmas (
    id integer NOT NULL,
    citation_form text NOT NULL,
    guide_word text,
    pos text,
    language_code text NOT NULL,
    base_form text,
    verbal_class text,
    nominal_pattern text,
    dialect text,
    period text,
    region text,
    cognates jsonb,
    derived_from text,
    attestation_count integer DEFAULT 0,
    tablet_count integer DEFAULT 0,
    source text NOT NULL,
    source_citation text,
    source_url text,
    cf_gw_pos text GENERATED ALWAYS AS (((((citation_form || '['::text) || COALESCE(guide_word, ''::text)) || ']'::text) || COALESCE(pos, ''::text))) STORED,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    lemma_type text
);


--
-- Name: lexical_lemmas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_lemmas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_lemmas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_lemmas_id_seq OWNED BY public.lexical_lemmas.id;


--
-- Name: lexical_norm_forms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_norm_forms (
    id integer NOT NULL,
    norm_id integer NOT NULL,
    written_form text NOT NULL,
    attestation_count integer DEFAULT 0,
    source text NOT NULL
);


--
-- Name: lexical_norm_forms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_norm_forms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_norm_forms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_norm_forms_id_seq OWNED BY public.lexical_norm_forms.id;


--
-- Name: lexical_norms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_norms (
    id integer NOT NULL,
    norm text NOT NULL,
    lemma_id integer NOT NULL,
    attestation_count integer DEFAULT 0,
    attestation_pct smallint DEFAULT 0,
    source text NOT NULL,
    source_id text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: lexical_norms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_norms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_norms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_norms_id_seq OWNED BY public.lexical_norms.id;


--
-- Name: lexical_senses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_senses (
    id integer NOT NULL,
    lemma_id integer NOT NULL,
    sense_number integer DEFAULT 1,
    definition_parts text[],
    usage_notes text,
    semantic_domain text,
    typical_context text,
    example_passages text[],
    translations jsonb,
    context_distribution jsonb,
    source text NOT NULL,
    source_citation text,
    source_url text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: lexical_senses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_senses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_senses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_senses_id_seq OWNED BY public.lexical_senses.id;


--
-- Name: lexical_sign_lemma_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_sign_lemma_associations (
    id integer NOT NULL,
    sign_id integer NOT NULL,
    lemma_id integer NOT NULL,
    reading_type text NOT NULL,
    frequency integer DEFAULT 0,
    context_distribution jsonb,
    source text NOT NULL,
    source_citation text,
    source_url text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    value text
);


--
-- Name: lexical_sign_lemma_associations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_sign_lemma_associations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_sign_lemma_associations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_sign_lemma_associations_id_seq OWNED BY public.lexical_sign_lemma_associations.id;


--
-- Name: lexical_signs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_signs (
    id integer NOT NULL,
    sign_name text NOT NULL,
    unicode_char text,
    sign_number text,
    shape_category text,
    component_signs text[],
    determinative_function text,
    language_codes text[],
    dialects text[],
    periods text[],
    regions text[],
    source text NOT NULL,
    source_citation text,
    source_url text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    "values" text[],
    unicode_codepoint text,
    unicode_name text,
    source_contributions jsonb DEFAULT '{}'::jsonb
);


--
-- Name: lexical_signs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_signs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_signs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_signs_id_seq OWNED BY public.lexical_signs.id;


--
-- Name: lexical_tablet_occurrences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lexical_tablet_occurrences (
    id integer NOT NULL,
    sign_id integer,
    lemma_id integer,
    sense_id integer,
    p_number text NOT NULL,
    occurrence_count integer DEFAULT 1,
    computed_at timestamp without time zone DEFAULT now(),
    CONSTRAINT lexical_tablet_occurrences_check CHECK (((sign_id IS NOT NULL) OR (lemma_id IS NOT NULL) OR (sense_id IS NOT NULL)))
);


--
-- Name: lexical_tablet_occurrences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lexical_tablet_occurrences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lexical_tablet_occurrences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lexical_tablet_occurrences_id_seq OWNED BY public.lexical_tablet_occurrences.id;


--
-- Name: morphology; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.morphology (
    id integer NOT NULL,
    lemmatization_id integer NOT NULL,
    language_family text,
    root text,
    stem text,
    tense text,
    person text,
    number text,
    gender text,
    conjugation_prefix text,
    dimensional_prefixes text,
    stem_form text,
    pronominal_suffix text,
    aspect text,
    transitivity text,
    "case" text,
    state text,
    CONSTRAINT morphology_language_family_check CHECK ((language_family = ANY (ARRAY['sumerian'::text, 'akkadian'::text, 'hittite'::text, 'elamite'::text, 'other'::text])))
);


--
-- Name: morphology_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.morphology_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: morphology_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.morphology_id_seq OWNED BY public.morphology.id;


--
-- Name: museums; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.museums (
    code text NOT NULL,
    name text,
    city text,
    country text,
    latitude real,
    longitude real
);


--
-- Name: named_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.named_entities (
    id integer NOT NULL,
    entity_type text NOT NULL,
    canonical_name text NOT NULL,
    guide_word text,
    alternate_names text,
    language_names text,
    primary_language text,
    glossary_entry_id text,
    description text,
    CONSTRAINT named_entities_entity_type_check CHECK ((entity_type = ANY (ARRAY['person'::text, 'deity'::text, 'place'::text, 'institution'::text, 'work'::text, 'watercourse'::text, 'month'::text, 'ethnonym'::text, 'festival'::text])))
);


--
-- Name: named_entities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.named_entities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: named_entities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.named_entities_id_seq OWNED BY public.named_entities.id;


--
-- Name: period_canon; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.period_canon (
    raw_period text NOT NULL,
    canonical text NOT NULL,
    date_start_bce integer,
    date_end_bce integer,
    sort_order integer,
    group_name text
);


--
-- Name: pipeline_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pipeline_status (
    p_number text NOT NULL,
    physical_complete real,
    graphemic_complete real,
    reading_complete real,
    linguistic_complete real,
    semantic_complete real,
    has_image integer DEFAULT 0,
    has_atf integer DEFAULT 0,
    has_lemmas integer DEFAULT 0,
    has_translation integer DEFAULT 0,
    has_sign_annotations integer DEFAULT 0,
    quality_score real,
    last_updated timestamp with time zone
);


--
-- Name: provenience_canon; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provenience_canon (
    raw_provenience text NOT NULL,
    ancient_name text NOT NULL,
    modern_name text,
    pleiades_id text,
    region text,
    subregion text,
    sort_order integer
);


--
-- Name: publication_authors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publication_authors (
    id integer NOT NULL,
    publication_id integer NOT NULL,
    scholar_id integer NOT NULL,
    role text DEFAULT 'author'::text,
    "position" integer,
    CONSTRAINT publication_authors_role_check CHECK ((role = ANY (ARRAY['author'::text, 'editor'::text, 'translator'::text, 'contributor'::text])))
);


--
-- Name: publication_authors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.publication_authors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: publication_authors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.publication_authors_id_seq OWNED BY public.publication_authors.id;


--
-- Name: publication_citations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publication_citations (
    id integer NOT NULL,
    citing_id integer NOT NULL,
    cited_id integer NOT NULL
);


--
-- Name: publication_citations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.publication_citations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: publication_citations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.publication_citations_id_seq OWNED BY public.publication_citations.id;


--
-- Name: publications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.publications (
    id integer NOT NULL,
    bibtex_key text,
    doi text,
    title text NOT NULL,
    short_title text,
    publication_type text NOT NULL,
    year integer,
    series_key text,
    volume_in_series text,
    authors text NOT NULL,
    editors text,
    publisher text,
    place text,
    url text,
    oracc_project text,
    supersedes_id integer,
    superseded_scope text,
    period_coverage text,
    genre_coverage text,
    cited_by_count integer,
    annotation_run_id integer,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT publications_publication_type_check CHECK ((publication_type = ANY (ARRAY['monograph'::text, 'edited_volume'::text, 'journal_article'::text, 'series_volume'::text, 'digital_edition'::text, 'museum_catalog'::text, 'dissertation'::text, 'conference_paper'::text, 'hand_copy_publication'::text, 'chapter'::text, 'proceedings'::text, 'thesis'::text, 'report'::text, 'unpublished'::text, 'other'::text])))
);


--
-- Name: publications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.publications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: publications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.publications_id_seq OWNED BY public.publications.id;


--
-- Name: relationship_predicates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationship_predicates (
    predicate text NOT NULL,
    category text,
    is_symmetric integer DEFAULT 0,
    description text,
    CONSTRAINT relationship_predicates_category_check CHECK ((category = ANY (ARRAY['familial'::text, 'political'::text, 'religious'::text, 'geographic'::text, 'institutional'::text, 'textual'::text, 'lexical'::text, 'identity'::text])))
);


--
-- Name: scholar_merge_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholar_merge_log (
    id integer NOT NULL,
    kept_scholar_id integer NOT NULL,
    merged_scholar_id integer NOT NULL,
    merged_name text NOT NULL,
    merge_reason text NOT NULL,
    merged_at timestamp with time zone DEFAULT now()
);


--
-- Name: scholar_merge_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scholar_merge_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scholar_merge_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scholar_merge_log_id_seq OWNED BY public.scholar_merge_log.id;


--
-- Name: scholarly_annotation_discussion_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholarly_annotation_discussion_threads (
    id integer NOT NULL,
    annotation_id integer NOT NULL,
    title text,
    status text DEFAULT 'open'::text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    resolution_note text,
    CONSTRAINT scholarly_annotation_discussion_threads_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'archived'::text])))
);


--
-- Name: scholarly_annotation_discussion_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scholarly_annotation_discussion_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scholarly_annotation_discussion_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scholarly_annotation_discussion_threads_id_seq OWNED BY public.scholarly_annotation_discussion_threads.id;


--
-- Name: scholarly_annotation_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholarly_annotation_evidence (
    id integer NOT NULL,
    annotation_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT scholarly_annotation_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text, 'personal_communication'::text])))
);


--
-- Name: scholarly_annotation_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scholarly_annotation_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scholarly_annotation_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scholarly_annotation_evidence_id_seq OWNED BY public.scholarly_annotation_evidence.id;


--
-- Name: scholarly_annotations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholarly_annotations (
    id integer NOT NULL,
    artifact_id text,
    surface_id integer,
    line_id integer,
    token_id integer,
    sign_id text,
    composite_id text,
    token_end_id integer,
    line_end_id integer,
    annotation_type text NOT NULL,
    content text NOT NULL,
    "references" text,
    tags text,
    annotation_run_id integer,
    confidence real,
    supersedes_id integer,
    version integer DEFAULT 1,
    visibility text DEFAULT 'public'::text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT scholarly_annotations_annotation_type_check CHECK ((annotation_type = ANY (ARRAY['textual_criticism'::text, 'parallel_passage'::text, 'historical_context'::text, 'cultural_note'::text, 'linguistic_note'::text, 'paleographic_note'::text, 'prosopographic_note'::text, 'bibliography'::text, 'conservation_note'::text, 'museum_note'::text, 'pedagogy'::text, 'methodology'::text, 'editorial_note'::text]))),
    CONSTRAINT scholarly_annotations_check CHECK (((((((
CASE
    WHEN (artifact_id IS NOT NULL) THEN 1
    ELSE 0
END +
CASE
    WHEN (surface_id IS NOT NULL) THEN 1
    ELSE 0
END) +
CASE
    WHEN (line_id IS NOT NULL) THEN 1
    ELSE 0
END) +
CASE
    WHEN (token_id IS NOT NULL) THEN 1
    ELSE 0
END) +
CASE
    WHEN (sign_id IS NOT NULL) THEN 1
    ELSE 0
END) +
CASE
    WHEN (composite_id IS NOT NULL) THEN 1
    ELSE 0
END) = 1)),
    CONSTRAINT scholarly_annotations_visibility_check CHECK ((visibility = ANY (ARRAY['public'::text, 'project'::text, 'private'::text])))
);


--
-- Name: scholarly_annotations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scholarly_annotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scholarly_annotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scholarly_annotations_id_seq OWNED BY public.scholarly_annotations.id;


--
-- Name: scholars; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholars (
    id integer NOT NULL,
    name text NOT NULL,
    orcid text,
    institution text,
    expertise_periods text,
    expertise_languages text,
    active_since text,
    normalized_name text,
    author_type text DEFAULT 'person'::text,
    CONSTRAINT chk_author_type CHECK ((author_type = ANY (ARRAY['person'::text, 'institution'::text, 'project'::text, 'unknown'::text])))
);


--
-- Name: scholarly_annotations_w3c; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.scholarly_annotations_w3c AS
 SELECT ('https://glintstone.app/anno/'::text || sa.id) AS id,
    'Annotation'::text AS type,
    json_build_object('id', ('https://orcid.org/'::text || s.orcid), 'name', s.name, 'affiliation', s.institution) AS creator,
    sa.created_at AS created,
    sa.updated_at AS modified,
    sa.annotation_type AS motivation,
    json_build_object('source', COALESCE(('cuneiform:'::text || sa.artifact_id), ('cuneiform:surface:'::text || (sa.surface_id)::text), ('cuneiform:line:'::text || (sa.line_id)::text), ('cuneiform:token:'::text || (sa.token_id)::text), ('cuneiform:sign:'::text || sa.sign_id), ('cuneiform:composite:'::text || sa.composite_id))) AS target,
    json_build_object('type', 'TextualBody', 'value', sa.content, 'format', 'text/plain') AS body,
    sa.confidence,
    sa.visibility
   FROM ((public.scholarly_annotations sa
     LEFT JOIN public.annotation_runs ar ON ((sa.annotation_run_id = ar.id)))
     LEFT JOIN public.scholars s ON ((ar.scholar_id = s.id)))
  WHERE (sa.visibility = 'public'::text);


--
-- Name: scholars_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.scholars_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: scholars_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.scholars_id_seq OWNED BY public.scholars.id;


--
-- Name: semantic_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.semantic_fields (
    id integer NOT NULL,
    name text,
    description text,
    parent_field_id integer
);


--
-- Name: semantic_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.semantic_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: semantic_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.semantic_fields_id_seq OWNED BY public.semantic_fields.id;


--
-- Name: sign_annotation_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_annotation_evidence (
    id integer NOT NULL,
    sign_annotation_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT sign_annotation_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text])))
);


--
-- Name: sign_annotation_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_annotation_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_annotation_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_annotation_evidence_id_seq OWNED BY public.sign_annotation_evidence.id;


--
-- Name: sign_annotations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_annotations (
    id integer NOT NULL,
    surface_image_id integer,
    sign_id text,
    bbox_x real,
    bbox_y real,
    bbox_w real,
    bbox_h real,
    line_number integer,
    position_in_line integer,
    damage_status text,
    annotation_run_id integer,
    confidence real,
    CONSTRAINT sign_annotations_damage_status_check CHECK ((damage_status = ANY (ARRAY['intact'::text, 'damaged'::text, 'missing'::text, 'illegible'::text])))
);


--
-- Name: sign_annotations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_annotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_annotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_annotations_id_seq OWNED BY public.sign_annotations.id;


--
-- Name: sign_concordance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_concordance (
    id integer NOT NULL,
    ogsl_id text NOT NULL,
    system text NOT NULL,
    number integer NOT NULL,
    confidence real DEFAULT 1.0,
    match_method text,
    note text,
    CONSTRAINT sign_concordance_match_method_check CHECK ((match_method = ANY (ARRAY['auto_unicode'::text, 'manual'::text, 'reading_overlap'::text]))),
    CONSTRAINT sign_concordance_system_check CHECK ((system = ANY (ARRAY['mzl'::text, 'abz'::text, 'lak'::text])))
);


--
-- Name: sign_concordance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_concordance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_concordance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_concordance_id_seq OWNED BY public.sign_concordance.id;


--
-- Name: sign_readings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_readings (
    id integer NOT NULL,
    sign_id text NOT NULL,
    value text NOT NULL,
    value_type text,
    language text,
    period text,
    confidence real DEFAULT 1.0,
    annotation_run_id integer,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT sign_readings_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT sign_readings_value_type_check CHECK ((value_type = ANY (ARRAY['logographic'::text, 'syllabic'::text, 'determinative'::text, 'numeric'::text])))
);


--
-- Name: signs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.signs (
    sign_id text NOT NULL,
    utf8 text,
    unicode_hex text,
    unicode_decimal integer,
    uname text,
    uphase text,
    sign_type text,
    mzl_number integer,
    abz_number text,
    lak_number integer,
    gdl_definition text,
    most_common_value text,
    total_corpus_frequency integer,
    CONSTRAINT signs_sign_type_check CHECK ((sign_type = ANY (ARRAY['simple'::text, 'compound'::text, 'modified'::text])))
);


--
-- Name: sign_detail; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.sign_detail AS
 SELECT s.sign_id,
    s.uname,
    s.utf8,
    s.mzl_number,
    s.most_common_value,
    s.sign_type,
    json_agg(json_build_object('value', sr.value, 'type', sr.value_type, 'language', sr.language, 'period', sr.period, 'confidence', sr.confidence) ORDER BY sr.confidence DESC, sr.value) FILTER (WHERE (sr.id IS NOT NULL)) AS readings
   FROM (public.signs s
     LEFT JOIN public.sign_readings sr ON ((s.sign_id = sr.sign_id)))
  GROUP BY s.sign_id, s.uname, s.utf8, s.mzl_number, s.most_common_value, s.sign_type;


--
-- Name: sign_readings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_readings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_readings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_readings_id_seq OWNED BY public.sign_readings.id;


--
-- Name: sign_values; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_values (
    id integer NOT NULL,
    sign_id text NOT NULL,
    value text,
    sub_index integer,
    value_type text,
    language_context text,
    period_context text,
    frequency integer,
    CONSTRAINT sign_values_value_type_check CHECK ((value_type = ANY (ARRAY['logographic'::text, 'syllabic'::text, 'determinative'::text, 'numeric'::text])))
);


--
-- Name: sign_values_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_values_id_seq OWNED BY public.sign_values.id;


--
-- Name: sign_variants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_variants (
    variant_id text NOT NULL,
    base_sign text,
    modifier_type text,
    modifier_code text,
    CONSTRAINT sign_variants_modifier_type_check CHECK ((modifier_type = ANY (ARRAY['gunu'::text, 'tenu'::text, 'sheshig'::text, 'nutillu'::text, 'rotated'::text])))
);


--
-- Name: surface_canon; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surface_canon (
    raw_surface text NOT NULL,
    canonical text NOT NULL,
    CONSTRAINT surface_canon_canonical_check CHECK ((canonical = ANY (ARRAY['obverse'::text, 'reverse'::text, 'left_edge'::text, 'right_edge'::text, 'top_edge'::text, 'bottom_edge'::text, 'seal'::text, 'unknown'::text])))
);


--
-- Name: surface_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surface_images (
    id integer NOT NULL,
    surface_id integer NOT NULL,
    image_path text NOT NULL,
    image_width integer,
    image_height integer,
    image_type text DEFAULT 'photo'::text,
    lighting text,
    source_url text,
    is_primary integer DEFAULT 0,
    annotation_run_id integer,
    CONSTRAINT surface_images_image_type_check CHECK ((image_type = ANY (ARRAY['photo'::text, 'line_drawing'::text, '3d_render'::text]))),
    CONSTRAINT surface_images_lighting_check CHECK ((lighting = ANY (ARRAY['direct'::text, 'raking'::text, 'ambient'::text, 'infrared'::text])))
);


--
-- Name: surface_images_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.surface_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: surface_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.surface_images_id_seq OWNED BY public.surface_images.id;


--
-- Name: surfaces; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surfaces (
    id integer NOT NULL,
    p_number text NOT NULL,
    surface_type text,
    surface_preservation text,
    condition_description text,
    CONSTRAINT surfaces_surface_type_check CHECK ((surface_type = ANY (ARRAY['obverse'::text, 'reverse'::text, 'left_edge'::text, 'right_edge'::text, 'top_edge'::text, 'bottom_edge'::text, 'seal'::text])))
);


--
-- Name: surfaces_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.surfaces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: surfaces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.surfaces_id_seq OWNED BY public.surfaces.id;


--
-- Name: text_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.text_lines (
    id integer NOT NULL,
    p_number text NOT NULL,
    surface_id integer,
    line_number text,
    raw_atf text,
    is_ruling integer DEFAULT 0,
    is_blank integer DEFAULT 0,
    source text,
    column_number integer DEFAULT 0 NOT NULL,
    CONSTRAINT text_lines_source_check CHECK ((source = ANY (ARRAY['cdli'::text, 'oracc'::text])))
);


--
-- Name: text_lines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.text_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: text_lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.text_lines_id_seq OWNED BY public.text_lines.id;


--
-- Name: token_reading_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_reading_decisions (
    id integer NOT NULL,
    token_reading_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT token_reading_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: token_reading_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_reading_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_reading_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_reading_decisions_id_seq OWNED BY public.token_reading_decisions.id;


--
-- Name: token_reading_discussion_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_reading_discussion_threads (
    id integer NOT NULL,
    token_reading_id integer NOT NULL,
    title text,
    status text DEFAULT 'open'::text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    resolution_decision_id integer,
    resolution_note text,
    CONSTRAINT token_reading_discussion_threads_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'archived'::text])))
);


--
-- Name: token_reading_discussion_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_reading_discussion_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_reading_discussion_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_reading_discussion_threads_id_seq OWNED BY public.token_reading_discussion_threads.id;


--
-- Name: token_reading_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_reading_evidence (
    id integer NOT NULL,
    token_reading_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT token_reading_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text])))
);


--
-- Name: token_reading_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_reading_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_reading_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_reading_evidence_id_seq OWNED BY public.token_reading_evidence.id;


--
-- Name: token_readings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_readings (
    id integer NOT NULL,
    token_id integer NOT NULL,
    form text,
    reading text,
    sign_function text,
    damage text,
    annotation_run_id integer,
    confidence real,
    is_consensus integer DEFAULT 0,
    note text,
    CONSTRAINT token_readings_damage_check CHECK ((damage = ANY (ARRAY['intact'::text, 'damaged'::text, 'missing'::text, 'illegible'::text]))),
    CONSTRAINT token_readings_sign_function_check CHECK ((sign_function = ANY (ARRAY['logographic'::text, 'syllabographic'::text, 'determinative'::text, 'numeric'::text, 'mixed'::text])))
);


--
-- Name: token_readings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.token_readings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: token_readings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.token_readings_id_seq OWNED BY public.token_readings.id;


--
-- Name: tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tokens (
    id integer NOT NULL,
    line_id integer NOT NULL,
    "position" integer,
    gdl_json text,
    lang text
);


--
-- Name: tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tokens_id_seq OWNED BY public.tokens.id;


--
-- Name: translation_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.translation_decisions (
    id integer NOT NULL,
    translation_id integer NOT NULL,
    decided_by integer,
    decision_method text,
    rationale text,
    decided_at timestamp with time zone DEFAULT now(),
    supersedes_id integer,
    CONSTRAINT translation_decisions_decision_method_check CHECK ((decision_method = ANY (ARRAY['editorial'::text, 'vote'::text, 'algorithm'::text, 'import_default'::text])))
);


--
-- Name: translation_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.translation_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: translation_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.translation_decisions_id_seq OWNED BY public.translation_decisions.id;


--
-- Name: translation_discussion_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.translation_discussion_threads (
    id integer NOT NULL,
    translation_id integer NOT NULL,
    title text,
    status text DEFAULT 'open'::text,
    created_at timestamp with time zone DEFAULT now(),
    resolved_at timestamp with time zone,
    resolution_decision_id integer,
    resolution_note text,
    CONSTRAINT translation_discussion_threads_status_check CHECK ((status = ANY (ARRAY['open'::text, 'resolved'::text, 'archived'::text])))
);


--
-- Name: translation_discussion_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.translation_discussion_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: translation_discussion_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.translation_discussion_threads_id_seq OWNED BY public.translation_discussion_threads.id;


--
-- Name: translation_evidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.translation_evidence (
    id integer NOT NULL,
    translation_id integer NOT NULL,
    evidence_type text,
    evidence_ref text,
    added_by integer,
    added_at timestamp with time zone DEFAULT now(),
    note text,
    CONSTRAINT translation_evidence_evidence_type_check CHECK ((evidence_type = ANY (ARRAY['photograph'::text, 'hand_copy'::text, 'collation_note'::text, 'publication'::text, '3d_scan'::text, 'RTI_image'::text, 'ML_output'::text])))
);


--
-- Name: translation_evidence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.translation_evidence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: translation_evidence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.translation_evidence_id_seq OWNED BY public.translation_evidence.id;


--
-- Name: translations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.translations (
    id integer NOT NULL,
    p_number text NOT NULL,
    line_id integer,
    translation text,
    language text DEFAULT 'en'::text,
    source text,
    annotation_run_id integer
);


--
-- Name: translations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.translations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: translations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.translations_id_seq OWNED BY public.translations.id;


--
-- Name: _dedup_candidates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._dedup_candidates ALTER COLUMN id SET DEFAULT nextval('public._dedup_candidates_id_seq'::regclass);


--
-- Name: _unparsed_records id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._unparsed_records ALTER COLUMN id SET DEFAULT nextval('public._unparsed_records_id_seq'::regclass);


--
-- Name: annotation_runs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_runs ALTER COLUMN id SET DEFAULT nextval('public.annotation_runs_id_seq'::regclass);


--
-- Name: artifact_credits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_credits ALTER COLUMN id SET DEFAULT nextval('public.artifact_credits_id_seq'::regclass);


--
-- Name: artifact_edition_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_decisions ALTER COLUMN id SET DEFAULT nextval('public.artifact_edition_decisions_id_seq'::regclass);


--
-- Name: artifact_edition_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_evidence ALTER COLUMN id SET DEFAULT nextval('public.artifact_edition_evidence_id_seq'::regclass);


--
-- Name: artifact_editions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions ALTER COLUMN id SET DEFAULT nextval('public.artifact_editions_id_seq'::regclass);


--
-- Name: artifact_identifier_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_decisions ALTER COLUMN id SET DEFAULT nextval('public.artifact_identifier_decisions_id_seq'::regclass);


--
-- Name: artifact_identifier_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_evidence ALTER COLUMN id SET DEFAULT nextval('public.artifact_identifier_evidence_id_seq'::regclass);


--
-- Name: artifact_identifiers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifiers ALTER COLUMN id SET DEFAULT nextval('public.artifact_identifiers_id_seq'::regclass);


--
-- Name: authority_links id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_links ALTER COLUMN id SET DEFAULT nextval('public.authority_links_id_seq'::regclass);


--
-- Name: authority_reconciliation_disputes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_reconciliation_disputes ALTER COLUMN id SET DEFAULT nextval('public.authority_reconciliation_disputes_id_seq'::regclass);


--
-- Name: cad_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_entries ALTER COLUMN id SET DEFAULT nextval('public.cad_entries_id_seq'::regclass);


--
-- Name: cad_examples id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_examples ALTER COLUMN id SET DEFAULT nextval('public.cad_examples_id_seq'::regclass);


--
-- Name: cad_meanings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_meanings ALTER COLUMN id SET DEFAULT nextval('public.cad_meanings_id_seq'::regclass);


--
-- Name: canonical_genres id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_genres ALTER COLUMN id SET DEFAULT nextval('public.canonical_genres_id_seq'::regclass);


--
-- Name: canonical_languages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_languages ALTER COLUMN id SET DEFAULT nextval('public.canonical_languages_id_seq'::regclass);


--
-- Name: collections collection_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collections ALTER COLUMN collection_id SET DEFAULT nextval('public.collections_collection_id_seq'::regclass);


--
-- Name: concepts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts ALTER COLUMN id SET DEFAULT nextval('public.concepts_id_seq'::regclass);


--
-- Name: discussion_posts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discussion_posts ALTER COLUMN id SET DEFAULT nextval('public.discussion_posts_id_seq'::regclass);


--
-- Name: entity_aliases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases ALTER COLUMN id SET DEFAULT nextval('public.entity_aliases_id_seq'::regclass);


--
-- Name: entity_mention_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_decisions ALTER COLUMN id SET DEFAULT nextval('public.entity_mention_decisions_id_seq'::regclass);


--
-- Name: entity_mention_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_evidence ALTER COLUMN id SET DEFAULT nextval('public.entity_mention_evidence_id_seq'::regclass);


--
-- Name: entity_mentions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions ALTER COLUMN id SET DEFAULT nextval('public.entity_mentions_id_seq'::regclass);


--
-- Name: entity_relationship_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_decisions ALTER COLUMN id SET DEFAULT nextval('public.entity_relationship_decisions_id_seq'::regclass);


--
-- Name: entity_relationship_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_evidence ALTER COLUMN id SET DEFAULT nextval('public.entity_relationship_evidence_id_seq'::regclass);


--
-- Name: entity_relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships ALTER COLUMN id SET DEFAULT nextval('public.entity_relationships_id_seq'::regclass);


--
-- Name: external_resources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_resources ALTER COLUMN id SET DEFAULT nextval('public.external_resources_id_seq'::regclass);


--
-- Name: fragment_join_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_decisions ALTER COLUMN id SET DEFAULT nextval('public.fragment_join_decisions_id_seq'::regclass);


--
-- Name: fragment_join_discussion_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_discussion_threads ALTER COLUMN id SET DEFAULT nextval('public.fragment_join_discussion_threads_id_seq'::regclass);


--
-- Name: fragment_join_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_evidence ALTER COLUMN id SET DEFAULT nextval('public.fragment_join_evidence_id_seq'::regclass);


--
-- Name: fragment_joins id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins ALTER COLUMN id SET DEFAULT nextval('public.fragment_joins_id_seq'::regclass);


--
-- Name: glossary_forms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_forms ALTER COLUMN id SET DEFAULT nextval('public.glossary_forms_id_seq'::regclass);


--
-- Name: glossary_relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_relationships ALTER COLUMN id SET DEFAULT nextval('public.glossary_relationships_id_seq'::regclass);


--
-- Name: glossary_senses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_senses ALTER COLUMN id SET DEFAULT nextval('public.glossary_senses_id_seq'::regclass);


--
-- Name: import_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_log ALTER COLUMN id SET DEFAULT nextval('public.import_log_id_seq'::regclass);


--
-- Name: interpretations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interpretations ALTER COLUMN id SET DEFAULT nextval('public.interpretations_id_seq'::regclass);


--
-- Name: intertextuality_links id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links ALTER COLUMN id SET DEFAULT nextval('public.intertextuality_links_id_seq'::regclass);


--
-- Name: join_groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.join_groups ALTER COLUMN id SET DEFAULT nextval('public.join_groups_id_seq'::regclass);


--
-- Name: lemma_sign_usage id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemma_sign_usage ALTER COLUMN id SET DEFAULT nextval('public.lemma_sign_usage_id_seq'::regclass);


--
-- Name: lemmatization_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_decisions ALTER COLUMN id SET DEFAULT nextval('public.lemmatization_decisions_id_seq'::regclass);


--
-- Name: lemmatization_discussion_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_discussion_threads ALTER COLUMN id SET DEFAULT nextval('public.lemmatization_discussion_threads_id_seq'::regclass);


--
-- Name: lemmatization_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_evidence ALTER COLUMN id SET DEFAULT nextval('public.lemmatization_evidence_id_seq'::regclass);


--
-- Name: lemmatizations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations ALTER COLUMN id SET DEFAULT nextval('public.lemmatizations_id_seq'::regclass);


--
-- Name: lexical_lemmas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_lemmas ALTER COLUMN id SET DEFAULT nextval('public.lexical_lemmas_id_seq'::regclass);


--
-- Name: lexical_norm_forms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norm_forms ALTER COLUMN id SET DEFAULT nextval('public.lexical_norm_forms_id_seq'::regclass);


--
-- Name: lexical_norms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norms ALTER COLUMN id SET DEFAULT nextval('public.lexical_norms_id_seq'::regclass);


--
-- Name: lexical_senses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_senses ALTER COLUMN id SET DEFAULT nextval('public.lexical_senses_id_seq'::regclass);


--
-- Name: lexical_sign_lemma_associations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_sign_lemma_associations ALTER COLUMN id SET DEFAULT nextval('public.lexical_sign_lemma_associations_id_seq'::regclass);


--
-- Name: lexical_signs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_signs ALTER COLUMN id SET DEFAULT nextval('public.lexical_signs_id_seq'::regclass);


--
-- Name: lexical_tablet_occurrences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences ALTER COLUMN id SET DEFAULT nextval('public.lexical_tablet_occurrences_id_seq'::regclass);


--
-- Name: morphology id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.morphology ALTER COLUMN id SET DEFAULT nextval('public.morphology_id_seq'::regclass);


--
-- Name: named_entities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.named_entities ALTER COLUMN id SET DEFAULT nextval('public.named_entities_id_seq'::regclass);


--
-- Name: publication_authors id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors ALTER COLUMN id SET DEFAULT nextval('public.publication_authors_id_seq'::regclass);


--
-- Name: publication_citations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_citations ALTER COLUMN id SET DEFAULT nextval('public.publication_citations_id_seq'::regclass);


--
-- Name: publications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications ALTER COLUMN id SET DEFAULT nextval('public.publications_id_seq'::regclass);


--
-- Name: scholar_merge_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholar_merge_log ALTER COLUMN id SET DEFAULT nextval('public.scholar_merge_log_id_seq'::regclass);


--
-- Name: scholarly_annotation_discussion_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_discussion_threads ALTER COLUMN id SET DEFAULT nextval('public.scholarly_annotation_discussion_threads_id_seq'::regclass);


--
-- Name: scholarly_annotation_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_evidence ALTER COLUMN id SET DEFAULT nextval('public.scholarly_annotation_evidence_id_seq'::regclass);


--
-- Name: scholarly_annotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations ALTER COLUMN id SET DEFAULT nextval('public.scholarly_annotations_id_seq'::regclass);


--
-- Name: scholars id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholars ALTER COLUMN id SET DEFAULT nextval('public.scholars_id_seq'::regclass);


--
-- Name: semantic_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_fields ALTER COLUMN id SET DEFAULT nextval('public.semantic_fields_id_seq'::regclass);


--
-- Name: sign_annotation_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotation_evidence ALTER COLUMN id SET DEFAULT nextval('public.sign_annotation_evidence_id_seq'::regclass);


--
-- Name: sign_annotations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotations ALTER COLUMN id SET DEFAULT nextval('public.sign_annotations_id_seq'::regclass);


--
-- Name: sign_concordance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_concordance ALTER COLUMN id SET DEFAULT nextval('public.sign_concordance_id_seq'::regclass);


--
-- Name: sign_readings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_readings ALTER COLUMN id SET DEFAULT nextval('public.sign_readings_id_seq'::regclass);


--
-- Name: sign_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_values ALTER COLUMN id SET DEFAULT nextval('public.sign_values_id_seq'::regclass);


--
-- Name: surface_images id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_images ALTER COLUMN id SET DEFAULT nextval('public.surface_images_id_seq'::regclass);


--
-- Name: surfaces id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surfaces ALTER COLUMN id SET DEFAULT nextval('public.surfaces_id_seq'::regclass);


--
-- Name: text_lines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_lines ALTER COLUMN id SET DEFAULT nextval('public.text_lines_id_seq'::regclass);


--
-- Name: token_reading_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_decisions ALTER COLUMN id SET DEFAULT nextval('public.token_reading_decisions_id_seq'::regclass);


--
-- Name: token_reading_discussion_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_discussion_threads ALTER COLUMN id SET DEFAULT nextval('public.token_reading_discussion_threads_id_seq'::regclass);


--
-- Name: token_reading_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_evidence ALTER COLUMN id SET DEFAULT nextval('public.token_reading_evidence_id_seq'::regclass);


--
-- Name: token_readings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_readings ALTER COLUMN id SET DEFAULT nextval('public.token_readings_id_seq'::regclass);


--
-- Name: tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tokens ALTER COLUMN id SET DEFAULT nextval('public.tokens_id_seq'::regclass);


--
-- Name: translation_decisions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_decisions ALTER COLUMN id SET DEFAULT nextval('public.translation_decisions_id_seq'::regclass);


--
-- Name: translation_discussion_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_discussion_threads ALTER COLUMN id SET DEFAULT nextval('public.translation_discussion_threads_id_seq'::regclass);


--
-- Name: translation_evidence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_evidence ALTER COLUMN id SET DEFAULT nextval('public.translation_evidence_id_seq'::regclass);


--
-- Name: translations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations ALTER COLUMN id SET DEFAULT nextval('public.translations_id_seq'::regclass);


--
-- Name: _dedup_candidates _dedup_candidates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._dedup_candidates
    ADD CONSTRAINT _dedup_candidates_pkey PRIMARY KEY (id);


--
-- Name: _schema_version _schema_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._schema_version
    ADD CONSTRAINT _schema_version_pkey PRIMARY KEY (key);


--
-- Name: _unparsed_records _unparsed_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._unparsed_records
    ADD CONSTRAINT _unparsed_records_pkey PRIMARY KEY (id);


--
-- Name: annotation_runs annotation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_runs
    ADD CONSTRAINT annotation_runs_pkey PRIMARY KEY (id);


--
-- Name: artifact_composites artifact_composites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_composites
    ADD CONSTRAINT artifact_composites_pkey PRIMARY KEY (p_number, q_number);


--
-- Name: artifact_credits artifact_credits_p_number_oracc_project_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_credits
    ADD CONSTRAINT artifact_credits_p_number_oracc_project_key UNIQUE (p_number, oracc_project);


--
-- Name: artifact_credits artifact_credits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_credits
    ADD CONSTRAINT artifact_credits_pkey PRIMARY KEY (id);


--
-- Name: artifact_edition_decisions artifact_edition_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_decisions
    ADD CONSTRAINT artifact_edition_decisions_pkey PRIMARY KEY (id);


--
-- Name: artifact_edition_evidence artifact_edition_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_evidence
    ADD CONSTRAINT artifact_edition_evidence_pkey PRIMARY KEY (id);


--
-- Name: artifact_editions artifact_editions_p_number_publication_id_reference_string_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_p_number_publication_id_reference_string_key UNIQUE (p_number, publication_id, reference_string);


--
-- Name: artifact_editions artifact_editions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_pkey PRIMARY KEY (id);


--
-- Name: artifact_genres artifact_genres_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_genres
    ADD CONSTRAINT artifact_genres_pkey PRIMARY KEY (p_number, genre_id);


--
-- Name: artifact_identifier_decisions artifact_identifier_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_decisions
    ADD CONSTRAINT artifact_identifier_decisions_pkey PRIMARY KEY (id);


--
-- Name: artifact_identifier_evidence artifact_identifier_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_evidence
    ADD CONSTRAINT artifact_identifier_evidence_pkey PRIMARY KEY (id);


--
-- Name: artifact_identifiers artifact_identifiers_p_number_identifier_type_identifier_va_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifiers
    ADD CONSTRAINT artifact_identifiers_p_number_identifier_type_identifier_va_key UNIQUE (p_number, identifier_type, identifier_value);


--
-- Name: artifact_identifiers artifact_identifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifiers
    ADD CONSTRAINT artifact_identifiers_pkey PRIMARY KEY (id);


--
-- Name: artifact_languages artifact_languages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_languages
    ADD CONSTRAINT artifact_languages_pkey PRIMARY KEY (p_number, language_id);


--
-- Name: artifacts artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_pkey PRIMARY KEY (p_number);


--
-- Name: authority_links authority_links_entity_id_authority_external_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_links
    ADD CONSTRAINT authority_links_entity_id_authority_external_id_key UNIQUE (entity_id, authority, external_id);


--
-- Name: authority_links authority_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_links
    ADD CONSTRAINT authority_links_pkey PRIMARY KEY (id);


--
-- Name: authority_reconciliation_disputes authority_reconciliation_disputes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_reconciliation_disputes
    ADD CONSTRAINT authority_reconciliation_disputes_pkey PRIMARY KEY (id);


--
-- Name: cad_entries cad_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_entries
    ADD CONSTRAINT cad_entries_pkey PRIMARY KEY (id);


--
-- Name: cad_examples cad_examples_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_examples
    ADD CONSTRAINT cad_examples_pkey PRIMARY KEY (id);


--
-- Name: cad_meanings cad_meanings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_meanings
    ADD CONSTRAINT cad_meanings_pkey PRIMARY KEY (id);


--
-- Name: canonical_genres canonical_genres_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_genres
    ADD CONSTRAINT canonical_genres_name_key UNIQUE (name);


--
-- Name: canonical_genres canonical_genres_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_genres
    ADD CONSTRAINT canonical_genres_pkey PRIMARY KEY (id);


--
-- Name: canonical_languages canonical_languages_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_languages
    ADD CONSTRAINT canonical_languages_name_key UNIQUE (name);


--
-- Name: canonical_languages canonical_languages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_languages
    ADD CONSTRAINT canonical_languages_pkey PRIMARY KEY (id);


--
-- Name: collection_members collection_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collection_members
    ADD CONSTRAINT collection_members_pkey PRIMARY KEY (collection_id, p_number);


--
-- Name: collections collections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT collections_pkey PRIMARY KEY (collection_id);


--
-- Name: composites composites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.composites
    ADD CONSTRAINT composites_pkey PRIMARY KEY (q_number);


--
-- Name: concepts concepts_canonical_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_canonical_name_key UNIQUE (canonical_name);


--
-- Name: concepts concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_pkey PRIMARY KEY (id);


--
-- Name: discussion_posts discussion_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discussion_posts
    ADD CONSTRAINT discussion_posts_pkey PRIMARY KEY (id);


--
-- Name: entity_aliases entity_aliases_canonical_entity_id_alias_entity_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_canonical_entity_id_alias_entity_id_key UNIQUE (canonical_entity_id, alias_entity_id);


--
-- Name: entity_aliases entity_aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_pkey PRIMARY KEY (id);


--
-- Name: entity_mention_decisions entity_mention_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_decisions
    ADD CONSTRAINT entity_mention_decisions_pkey PRIMARY KEY (id);


--
-- Name: entity_mention_evidence entity_mention_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_evidence
    ADD CONSTRAINT entity_mention_evidence_pkey PRIMARY KEY (id);


--
-- Name: entity_mentions entity_mentions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_pkey PRIMARY KEY (id);


--
-- Name: entity_relationship_decisions entity_relationship_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_decisions
    ADD CONSTRAINT entity_relationship_decisions_pkey PRIMARY KEY (id);


--
-- Name: entity_relationship_evidence entity_relationship_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_evidence
    ADD CONSTRAINT entity_relationship_evidence_pkey PRIMARY KEY (id);


--
-- Name: entity_relationships entity_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_pkey PRIMARY KEY (id);


--
-- Name: excavation_sites excavation_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.excavation_sites
    ADD CONSTRAINT excavation_sites_pkey PRIMARY KEY (code);


--
-- Name: external_resources external_resources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_resources
    ADD CONSTRAINT external_resources_pkey PRIMARY KEY (id);


--
-- Name: fragment_join_decisions fragment_join_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_decisions
    ADD CONSTRAINT fragment_join_decisions_pkey PRIMARY KEY (id);


--
-- Name: fragment_join_discussion_threads fragment_join_discussion_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_discussion_threads
    ADD CONSTRAINT fragment_join_discussion_threads_pkey PRIMARY KEY (id);


--
-- Name: fragment_join_evidence fragment_join_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_evidence
    ADD CONSTRAINT fragment_join_evidence_pkey PRIMARY KEY (id);


--
-- Name: fragment_joins fragment_joins_fragment_a_fragment_b_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_fragment_a_fragment_b_key UNIQUE (fragment_a, fragment_b);


--
-- Name: fragment_joins fragment_joins_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_pkey PRIMARY KEY (id);


--
-- Name: genre_canon genre_canon_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genre_canon
    ADD CONSTRAINT genre_canon_pkey PRIMARY KEY (raw_genre);


--
-- Name: glossary_entries glossary_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_entries
    ADD CONSTRAINT glossary_entries_pkey PRIMARY KEY (entry_id);


--
-- Name: glossary_forms glossary_forms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_forms
    ADD CONSTRAINT glossary_forms_pkey PRIMARY KEY (id);


--
-- Name: glossary_relationships glossary_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_relationships
    ADD CONSTRAINT glossary_relationships_pkey PRIMARY KEY (id);


--
-- Name: glossary_semantic_fields glossary_semantic_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_semantic_fields
    ADD CONSTRAINT glossary_semantic_fields_pkey PRIMARY KEY (glossary_entry_id, semantic_field_id);


--
-- Name: glossary_senses glossary_senses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_senses
    ADD CONSTRAINT glossary_senses_pkey PRIMARY KEY (id);


--
-- Name: import_log import_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_log
    ADD CONSTRAINT import_log_pkey PRIMARY KEY (id);


--
-- Name: interpretations interpretations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interpretations
    ADD CONSTRAINT interpretations_pkey PRIMARY KEY (id);


--
-- Name: intertextuality_links intertextuality_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_pkey PRIMARY KEY (id);


--
-- Name: join_groups join_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.join_groups
    ADD CONSTRAINT join_groups_pkey PRIMARY KEY (id);


--
-- Name: language_map language_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_map
    ADD CONSTRAINT language_map_pkey PRIMARY KEY (cdli_name);


--
-- Name: lemma_concepts lemma_concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemma_concepts
    ADD CONSTRAINT lemma_concepts_pkey PRIMARY KEY (lemma_entry_id, concept_id);


--
-- Name: lemma_sign_usage lemma_sign_usage_entry_id_sign_id_reading_value_period_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemma_sign_usage
    ADD CONSTRAINT lemma_sign_usage_entry_id_sign_id_reading_value_period_key UNIQUE (entry_id, sign_id, reading_value, period);


--
-- Name: lemma_sign_usage lemma_sign_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemma_sign_usage
    ADD CONSTRAINT lemma_sign_usage_pkey PRIMARY KEY (id);


--
-- Name: lemmatization_decisions lemmatization_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_decisions
    ADD CONSTRAINT lemmatization_decisions_pkey PRIMARY KEY (id);


--
-- Name: lemmatization_discussion_threads lemmatization_discussion_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_discussion_threads
    ADD CONSTRAINT lemmatization_discussion_threads_pkey PRIMARY KEY (id);


--
-- Name: lemmatization_evidence lemmatization_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_evidence
    ADD CONSTRAINT lemmatization_evidence_pkey PRIMARY KEY (id);


--
-- Name: lemmatizations lemmatizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations
    ADD CONSTRAINT lemmatizations_pkey PRIMARY KEY (id);


--
-- Name: lexical_lemmas lexical_lemmas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_lemmas
    ADD CONSTRAINT lexical_lemmas_pkey PRIMARY KEY (id);


--
-- Name: lexical_norm_forms lexical_norm_forms_norm_id_written_form_source_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norm_forms
    ADD CONSTRAINT lexical_norm_forms_norm_id_written_form_source_key UNIQUE (norm_id, written_form, source);


--
-- Name: lexical_norm_forms lexical_norm_forms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norm_forms
    ADD CONSTRAINT lexical_norm_forms_pkey PRIMARY KEY (id);


--
-- Name: lexical_norms lexical_norms_norm_lemma_id_source_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norms
    ADD CONSTRAINT lexical_norms_norm_lemma_id_source_key UNIQUE (norm, lemma_id, source);


--
-- Name: lexical_norms lexical_norms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norms
    ADD CONSTRAINT lexical_norms_pkey PRIMARY KEY (id);


--
-- Name: lexical_senses lexical_senses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_senses
    ADD CONSTRAINT lexical_senses_pkey PRIMARY KEY (id);


--
-- Name: lexical_sign_lemma_associations lexical_sign_lemma_associatio_sign_id_lemma_id_reading_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_sign_lemma_associations
    ADD CONSTRAINT lexical_sign_lemma_associatio_sign_id_lemma_id_reading_type_key UNIQUE (sign_id, lemma_id, reading_type, source);


--
-- Name: lexical_sign_lemma_associations lexical_sign_lemma_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_sign_lemma_associations
    ADD CONSTRAINT lexical_sign_lemma_associations_pkey PRIMARY KEY (id);


--
-- Name: lexical_signs lexical_signs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_signs
    ADD CONSTRAINT lexical_signs_pkey PRIMARY KEY (id);


--
-- Name: lexical_signs lexical_signs_sign_name_source_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_signs
    ADD CONSTRAINT lexical_signs_sign_name_source_key UNIQUE (sign_name, source);


--
-- Name: lexical_tablet_occurrences lexical_tablet_occurrences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences
    ADD CONSTRAINT lexical_tablet_occurrences_pkey PRIMARY KEY (id);


--
-- Name: morphology morphology_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.morphology
    ADD CONSTRAINT morphology_pkey PRIMARY KEY (id);


--
-- Name: museums museums_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.museums
    ADD CONSTRAINT museums_pkey PRIMARY KEY (code);


--
-- Name: named_entities named_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.named_entities
    ADD CONSTRAINT named_entities_pkey PRIMARY KEY (id);


--
-- Name: period_canon period_canon_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.period_canon
    ADD CONSTRAINT period_canon_pkey PRIMARY KEY (raw_period);


--
-- Name: pipeline_status pipeline_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pipeline_status
    ADD CONSTRAINT pipeline_status_pkey PRIMARY KEY (p_number);


--
-- Name: provenience_canon provenience_canon_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provenience_canon
    ADD CONSTRAINT provenience_canon_pkey PRIMARY KEY (raw_provenience);


--
-- Name: publication_authors publication_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_pkey PRIMARY KEY (id);


--
-- Name: publication_authors publication_authors_publication_id_scholar_id_role_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_publication_id_scholar_id_role_key UNIQUE (publication_id, scholar_id, role);


--
-- Name: publication_citations publication_citations_citing_id_cited_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_citations
    ADD CONSTRAINT publication_citations_citing_id_cited_id_key UNIQUE (citing_id, cited_id);


--
-- Name: publication_citations publication_citations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_citations
    ADD CONSTRAINT publication_citations_pkey PRIMARY KEY (id);


--
-- Name: publications publications_bibtex_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_bibtex_key_key UNIQUE (bibtex_key);


--
-- Name: publications publications_doi_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_doi_key UNIQUE (doi);


--
-- Name: publications publications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_pkey PRIMARY KEY (id);


--
-- Name: relationship_predicates relationship_predicates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship_predicates
    ADD CONSTRAINT relationship_predicates_pkey PRIMARY KEY (predicate);


--
-- Name: scholar_merge_log scholar_merge_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholar_merge_log
    ADD CONSTRAINT scholar_merge_log_pkey PRIMARY KEY (id);


--
-- Name: scholarly_annotation_discussion_threads scholarly_annotation_discussion_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_discussion_threads
    ADD CONSTRAINT scholarly_annotation_discussion_threads_pkey PRIMARY KEY (id);


--
-- Name: scholarly_annotation_evidence scholarly_annotation_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_evidence
    ADD CONSTRAINT scholarly_annotation_evidence_pkey PRIMARY KEY (id);


--
-- Name: scholarly_annotations scholarly_annotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_pkey PRIMARY KEY (id);


--
-- Name: scholars scholars_orcid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholars
    ADD CONSTRAINT scholars_orcid_key UNIQUE (orcid);


--
-- Name: scholars scholars_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholars
    ADD CONSTRAINT scholars_pkey PRIMARY KEY (id);


--
-- Name: semantic_fields semantic_fields_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_fields
    ADD CONSTRAINT semantic_fields_name_key UNIQUE (name);


--
-- Name: semantic_fields semantic_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_fields
    ADD CONSTRAINT semantic_fields_pkey PRIMARY KEY (id);


--
-- Name: sign_annotation_evidence sign_annotation_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotation_evidence
    ADD CONSTRAINT sign_annotation_evidence_pkey PRIMARY KEY (id);


--
-- Name: sign_annotations sign_annotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotations
    ADD CONSTRAINT sign_annotations_pkey PRIMARY KEY (id);


--
-- Name: sign_concordance sign_concordance_ogsl_id_system_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_concordance
    ADD CONSTRAINT sign_concordance_ogsl_id_system_number_key UNIQUE (ogsl_id, system, number);


--
-- Name: sign_concordance sign_concordance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_concordance
    ADD CONSTRAINT sign_concordance_pkey PRIMARY KEY (id);


--
-- Name: sign_readings sign_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_readings
    ADD CONSTRAINT sign_readings_pkey PRIMARY KEY (id);


--
-- Name: sign_readings sign_readings_sign_id_value_language_period_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_readings
    ADD CONSTRAINT sign_readings_sign_id_value_language_period_key UNIQUE (sign_id, value, language, period);


--
-- Name: sign_values sign_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_values
    ADD CONSTRAINT sign_values_pkey PRIMARY KEY (id);


--
-- Name: sign_variants sign_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_variants
    ADD CONSTRAINT sign_variants_pkey PRIMARY KEY (variant_id);


--
-- Name: signs signs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signs
    ADD CONSTRAINT signs_pkey PRIMARY KEY (sign_id);


--
-- Name: surface_canon surface_canon_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_canon
    ADD CONSTRAINT surface_canon_pkey PRIMARY KEY (raw_surface);


--
-- Name: surface_images surface_images_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_images
    ADD CONSTRAINT surface_images_pkey PRIMARY KEY (id);


--
-- Name: surface_images surface_images_surface_id_image_path_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_images
    ADD CONSTRAINT surface_images_surface_id_image_path_key UNIQUE (surface_id, image_path);


--
-- Name: surfaces surfaces_p_number_surface_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surfaces
    ADD CONSTRAINT surfaces_p_number_surface_type_key UNIQUE (p_number, surface_type);


--
-- Name: surfaces surfaces_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surfaces
    ADD CONSTRAINT surfaces_pkey PRIMARY KEY (id);


--
-- Name: text_lines text_lines_p_surface_col_line_src_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_lines
    ADD CONSTRAINT text_lines_p_surface_col_line_src_key UNIQUE (p_number, surface_id, column_number, line_number, source);


--
-- Name: text_lines text_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_lines
    ADD CONSTRAINT text_lines_pkey PRIMARY KEY (id);


--
-- Name: token_reading_decisions token_reading_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_decisions
    ADD CONSTRAINT token_reading_decisions_pkey PRIMARY KEY (id);


--
-- Name: token_reading_discussion_threads token_reading_discussion_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_discussion_threads
    ADD CONSTRAINT token_reading_discussion_threads_pkey PRIMARY KEY (id);


--
-- Name: token_reading_evidence token_reading_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_evidence
    ADD CONSTRAINT token_reading_evidence_pkey PRIMARY KEY (id);


--
-- Name: token_readings token_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_readings
    ADD CONSTRAINT token_readings_pkey PRIMARY KEY (id);


--
-- Name: tokens tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT tokens_pkey PRIMARY KEY (id);


--
-- Name: translation_decisions translation_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_decisions
    ADD CONSTRAINT translation_decisions_pkey PRIMARY KEY (id);


--
-- Name: translation_discussion_threads translation_discussion_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_discussion_threads
    ADD CONSTRAINT translation_discussion_threads_pkey PRIMARY KEY (id);


--
-- Name: translation_evidence translation_evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_evidence
    ADD CONSTRAINT translation_evidence_pkey PRIMARY KEY (id);


--
-- Name: translations translations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_pkey PRIMARY KEY (id);


--
-- Name: idx_ae_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ae_current ON public.artifact_editions USING btree (p_number, is_current_edition) WHERE (is_current_edition = 1);


--
-- Name: idx_ae_p_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ae_p_number ON public.artifact_editions USING btree (p_number);


--
-- Name: idx_ae_publication; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ae_publication ON public.artifact_editions USING btree (publication_id);


--
-- Name: idx_ae_reference; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ae_reference ON public.artifact_editions USING btree (reference_normalized);


--
-- Name: idx_ae_supersedes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ae_supersedes ON public.artifact_editions USING btree (supersedes_id);


--
-- Name: idx_ag_genre; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ag_genre ON public.artifact_genres USING btree (genre_id);


--
-- Name: idx_ai_authority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_authority ON public.artifact_identifiers USING btree (authority);


--
-- Name: idx_ai_normalized; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_normalized ON public.artifact_identifiers USING btree (identifier_normalized);


--
-- Name: idx_ai_p_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_p_number ON public.artifact_identifiers USING btree (p_number);


--
-- Name: idx_ai_type_value; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_type_value ON public.artifact_identifiers USING btree (identifier_type, identifier_value);


--
-- Name: idx_al_authority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_al_authority ON public.authority_links USING btree (authority);


--
-- Name: idx_al_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_al_entity ON public.authority_links USING btree (entity_id);


--
-- Name: idx_al_external; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_al_external ON public.authority_links USING btree (external_id);


--
-- Name: idx_al_lang; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_al_lang ON public.artifact_languages USING btree (language_id);


--
-- Name: idx_artifact_credits_p_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifact_credits_p_number ON public.artifact_credits USING btree (p_number);


--
-- Name: idx_artifacts_genre; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifacts_genre ON public.artifacts USING btree (genre) WHERE (genre IS NOT NULL);


--
-- Name: idx_artifacts_lang_norm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifacts_lang_norm ON public.artifacts USING btree (language_normalized) WHERE (language_normalized IS NOT NULL);


--
-- Name: idx_artifacts_language_normalized; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifacts_language_normalized ON public.artifacts USING btree (language_normalized);


--
-- Name: idx_artifacts_period_norm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifacts_period_norm ON public.artifacts USING btree (period_normalized) WHERE (period_normalized IS NOT NULL);


--
-- Name: idx_artifacts_prov_norm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_artifacts_prov_norm ON public.artifacts USING btree (provenience_normalized) WHERE (provenience_normalized IS NOT NULL);


--
-- Name: idx_concepts_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concepts_domain ON public.concepts USING btree (domain_path);


--
-- Name: idx_concepts_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_concepts_parent ON public.concepts USING btree (parent_concept_id);


--
-- Name: idx_em_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_em_entity ON public.entity_mentions USING btree (entity_id);


--
-- Name: idx_em_line; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_em_line ON public.entity_mentions USING btree (line_id);


--
-- Name: idx_em_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_em_run ON public.entity_mentions USING btree (annotation_run_id);


--
-- Name: idx_em_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_em_token ON public.entity_mentions USING btree (token_id);


--
-- Name: idx_er_custom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_er_custom ON public.entity_relationships USING btree (predicate_custom);


--
-- Name: idx_er_object; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_er_object ON public.entity_relationships USING btree (object_id);


--
-- Name: idx_er_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_er_period ON public.entity_relationships USING btree (period_start);


--
-- Name: idx_er_predicate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_er_predicate ON public.entity_relationships USING btree (predicate_enum);


--
-- Name: idx_er_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_er_subject ON public.entity_relationships USING btree (subject_id);


--
-- Name: idx_fj_fragment_a; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fj_fragment_a ON public.fragment_joins USING btree (fragment_a);


--
-- Name: idx_fj_fragment_b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fj_fragment_b ON public.fragment_joins USING btree (fragment_b);


--
-- Name: idx_fj_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fj_group ON public.fragment_joins USING btree (join_group_id);


--
-- Name: idx_fj_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fj_status ON public.fragment_joins USING btree (status);


--
-- Name: idx_interpretations_basis; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interpretations_basis ON public.interpretations USING btree (basis);


--
-- Name: idx_interpretations_scholar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interpretations_scholar ON public.interpretations USING btree (scholar_name);


--
-- Name: idx_interpretations_supersedes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interpretations_supersedes ON public.interpretations USING btree (supersedes_id);


--
-- Name: idx_interpretations_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interpretations_target ON public.interpretations USING btree (target_type, target_id);


--
-- Name: idx_lemma_concepts_concept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemma_concepts_concept ON public.lemma_concepts USING btree (concept_id);


--
-- Name: idx_lemma_concepts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemma_concepts_type ON public.lemma_concepts USING btree (relationship_type);


--
-- Name: idx_lemma_sign_usage_entry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemma_sign_usage_entry ON public.lemma_sign_usage USING btree (entry_id);


--
-- Name: idx_lemma_sign_usage_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemma_sign_usage_period ON public.lemma_sign_usage USING btree (period);


--
-- Name: idx_lemma_sign_usage_sign; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemma_sign_usage_sign ON public.lemma_sign_usage USING btree (sign_id);


--
-- Name: idx_lemmatizations_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemmatizations_language ON public.lemmatizations USING btree (language);


--
-- Name: idx_lemmatizations_norm_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lemmatizations_norm_id ON public.lemmatizations USING btree (norm_id);


--
-- Name: idx_lexical_lemmas_attestation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_attestation ON public.lexical_lemmas USING btree (attestation_count DESC);


--
-- Name: idx_lexical_lemmas_cf; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_cf ON public.lexical_lemmas USING btree (citation_form);


--
-- Name: idx_lexical_lemmas_composite; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_lexical_lemmas_composite ON public.lexical_lemmas USING btree (cf_gw_pos, source);


--
-- Name: idx_lexical_lemmas_dialect; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_dialect ON public.lexical_lemmas USING btree (dialect);


--
-- Name: idx_lexical_lemmas_gw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_gw ON public.lexical_lemmas USING btree (guide_word);


--
-- Name: idx_lexical_lemmas_lang; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_lang ON public.lexical_lemmas USING btree (language_code);


--
-- Name: idx_lexical_lemmas_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_period ON public.lexical_lemmas USING btree (period);


--
-- Name: idx_lexical_lemmas_pos; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_pos ON public.lexical_lemmas USING btree (pos);


--
-- Name: idx_lexical_lemmas_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_lemmas_source ON public.lexical_lemmas USING btree (source);


--
-- Name: idx_lexical_norm_forms_norm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norm_forms_norm ON public.lexical_norm_forms USING btree (norm_id);


--
-- Name: idx_lexical_norm_forms_written; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norm_forms_written ON public.lexical_norm_forms USING btree (written_form);


--
-- Name: idx_lexical_norms_freq; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norms_freq ON public.lexical_norms USING btree (attestation_count DESC);


--
-- Name: idx_lexical_norms_lemma; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norms_lemma ON public.lexical_norms USING btree (lemma_id);


--
-- Name: idx_lexical_norms_norm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norms_norm ON public.lexical_norms USING btree (norm);


--
-- Name: idx_lexical_norms_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_norms_source ON public.lexical_norms USING btree (source);


--
-- Name: idx_lexical_senses_domain; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_senses_domain ON public.lexical_senses USING btree (semantic_domain);


--
-- Name: idx_lexical_senses_lemma; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_senses_lemma ON public.lexical_senses USING btree (lemma_id);


--
-- Name: idx_lexical_senses_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_senses_source ON public.lexical_senses USING btree (source);


--
-- Name: idx_lexical_sign_lemma_freq; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_sign_lemma_freq ON public.lexical_sign_lemma_associations USING btree (frequency DESC);


--
-- Name: idx_lexical_sign_lemma_lemma; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_sign_lemma_lemma ON public.lexical_sign_lemma_associations USING btree (lemma_id);


--
-- Name: idx_lexical_sign_lemma_sign; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_sign_lemma_sign ON public.lexical_sign_lemma_associations USING btree (sign_id);


--
-- Name: idx_lexical_sign_lemma_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_sign_lemma_type ON public.lexical_sign_lemma_associations USING btree (reading_type);


--
-- Name: idx_lexical_signs_codepoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_codepoint ON public.lexical_signs USING btree (unicode_codepoint);


--
-- Name: idx_lexical_signs_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_language ON public.lexical_signs USING gin (language_codes);


--
-- Name: idx_lexical_signs_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_name ON public.lexical_signs USING btree (sign_name);


--
-- Name: idx_lexical_signs_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_period ON public.lexical_signs USING gin (periods);


--
-- Name: idx_lexical_signs_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_source ON public.lexical_signs USING btree (source);


--
-- Name: idx_lexical_signs_unicode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_unicode ON public.lexical_signs USING btree (unicode_char);


--
-- Name: idx_lexical_signs_values; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lexical_signs_values ON public.lexical_signs USING gin ("values");


--
-- Name: idx_ne_glossary; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ne_glossary ON public.named_entities USING btree (glossary_entry_id);


--
-- Name: idx_ne_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ne_name ON public.named_entities USING btree (canonical_name);


--
-- Name: idx_ne_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ne_type ON public.named_entities USING btree (entity_type);


--
-- Name: idx_period_canon_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_period_canon_group ON public.period_canon USING btree (group_name, sort_order);


--
-- Name: idx_provenience_canon_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_provenience_canon_region ON public.provenience_canon USING btree (region, subregion, sort_order);


--
-- Name: idx_pub_bibtex; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pub_bibtex ON public.publications USING btree (bibtex_key);


--
-- Name: idx_pub_oracc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pub_oracc ON public.publications USING btree (oracc_project);


--
-- Name: idx_pub_series; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pub_series ON public.publications USING btree (series_key, volume_in_series);


--
-- Name: idx_pub_short_title; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pub_short_title ON public.publications USING btree (short_title);


--
-- Name: idx_pub_supersedes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pub_supersedes ON public.publications USING btree (supersedes_id);


--
-- Name: idx_publications_cited_by_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_publications_cited_by_count ON public.publications USING btree (cited_by_count DESC) WHERE (cited_by_count IS NOT NULL);


--
-- Name: idx_sa_artifact; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sa_artifact ON public.scholarly_annotations USING btree (artifact_id);


--
-- Name: idx_sa_line; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sa_line ON public.scholarly_annotations USING btree (line_id);


--
-- Name: idx_sa_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sa_run ON public.scholarly_annotations USING btree (annotation_run_id);


--
-- Name: idx_sa_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sa_token ON public.scholarly_annotations USING btree (token_id);


--
-- Name: idx_sa_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sa_type ON public.scholarly_annotations USING btree (annotation_type);


--
-- Name: idx_sc_ogsl; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sc_ogsl ON public.sign_concordance USING btree (ogsl_id);


--
-- Name: idx_sc_system_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sc_system_number ON public.sign_concordance USING btree (system, number);


--
-- Name: idx_scholar_merge_log_kept; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholar_merge_log_kept ON public.scholar_merge_log USING btree (kept_scholar_id);


--
-- Name: idx_scholar_merge_log_merged; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholar_merge_log_merged ON public.scholar_merge_log USING btree (merged_scholar_id);


--
-- Name: idx_scholars_author_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholars_author_type ON public.scholars USING btree (author_type);


--
-- Name: idx_scholars_normalized_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholars_normalized_name ON public.scholars USING btree (normalized_name);


--
-- Name: idx_si_primary; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_si_primary ON public.surface_images USING btree (surface_id, is_primary) WHERE (is_primary = 1);


--
-- Name: idx_si_surface; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_si_surface ON public.surface_images USING btree (surface_id);


--
-- Name: idx_sign_readings_language; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sign_readings_language ON public.sign_readings USING btree (language);


--
-- Name: idx_sign_readings_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sign_readings_period ON public.sign_readings USING btree (period);


--
-- Name: idx_sign_readings_sign; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sign_readings_sign ON public.sign_readings USING btree (sign_id);


--
-- Name: idx_sign_readings_value; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sign_readings_value ON public.sign_readings USING btree (value);


--
-- Name: idx_tablet_occ_lemma; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tablet_occ_lemma ON public.lexical_tablet_occurrences USING btree (lemma_id);


--
-- Name: idx_tablet_occ_p_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tablet_occ_p_number ON public.lexical_tablet_occurrences USING btree (p_number);


--
-- Name: idx_tablet_occ_sense; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tablet_occ_sense ON public.lexical_tablet_occurrences USING btree (sense_id);


--
-- Name: idx_tablet_occ_sign; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tablet_occ_sign ON public.lexical_tablet_occurrences USING btree (sign_id);


--
-- Name: idx_unparsed_p_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_unparsed_p_number ON public._unparsed_records USING btree (p_number);


--
-- Name: idx_unparsed_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_unparsed_source ON public._unparsed_records USING btree (source_script);


--
-- Name: _unparsed_records _unparsed_records_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public._unparsed_records
    ADD CONSTRAINT _unparsed_records_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: annotation_runs annotation_runs_scholar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_runs
    ADD CONSTRAINT annotation_runs_scholar_id_fkey FOREIGN KEY (scholar_id) REFERENCES public.scholars(id);


--
-- Name: artifact_composites artifact_composites_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_composites
    ADD CONSTRAINT artifact_composites_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifact_composites artifact_composites_q_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_composites
    ADD CONSTRAINT artifact_composites_q_number_fkey FOREIGN KEY (q_number) REFERENCES public.composites(q_number);


--
-- Name: artifact_credits artifact_credits_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_credits
    ADD CONSTRAINT artifact_credits_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifact_edition_decisions artifact_edition_decisions_artifact_edition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_decisions
    ADD CONSTRAINT artifact_edition_decisions_artifact_edition_id_fkey FOREIGN KEY (artifact_edition_id) REFERENCES public.artifact_editions(id);


--
-- Name: artifact_edition_decisions artifact_edition_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_decisions
    ADD CONSTRAINT artifact_edition_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: artifact_edition_decisions artifact_edition_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_decisions
    ADD CONSTRAINT artifact_edition_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.artifact_edition_decisions(id);


--
-- Name: artifact_edition_evidence artifact_edition_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_evidence
    ADD CONSTRAINT artifact_edition_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: artifact_edition_evidence artifact_edition_evidence_artifact_edition_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_edition_evidence
    ADD CONSTRAINT artifact_edition_evidence_artifact_edition_id_fkey FOREIGN KEY (artifact_edition_id) REFERENCES public.artifact_editions(id);


--
-- Name: artifact_editions artifact_editions_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: artifact_editions artifact_editions_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifact_editions artifact_editions_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_publication_id_fkey FOREIGN KEY (publication_id) REFERENCES public.publications(id);


--
-- Name: artifact_editions artifact_editions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_editions
    ADD CONSTRAINT artifact_editions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.artifact_editions(id);


--
-- Name: artifact_genres artifact_genres_genre_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_genres
    ADD CONSTRAINT artifact_genres_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES public.canonical_genres(id);


--
-- Name: artifact_genres artifact_genres_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_genres
    ADD CONSTRAINT artifact_genres_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifact_identifier_decisions artifact_identifier_decisions_artifact_identifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_decisions
    ADD CONSTRAINT artifact_identifier_decisions_artifact_identifier_id_fkey FOREIGN KEY (artifact_identifier_id) REFERENCES public.artifact_identifiers(id);


--
-- Name: artifact_identifier_decisions artifact_identifier_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_decisions
    ADD CONSTRAINT artifact_identifier_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: artifact_identifier_decisions artifact_identifier_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_decisions
    ADD CONSTRAINT artifact_identifier_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.artifact_identifier_decisions(id);


--
-- Name: artifact_identifier_evidence artifact_identifier_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_evidence
    ADD CONSTRAINT artifact_identifier_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: artifact_identifier_evidence artifact_identifier_evidence_artifact_identifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifier_evidence
    ADD CONSTRAINT artifact_identifier_evidence_artifact_identifier_id_fkey FOREIGN KEY (artifact_identifier_id) REFERENCES public.artifact_identifiers(id);


--
-- Name: artifact_identifiers artifact_identifiers_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifiers
    ADD CONSTRAINT artifact_identifiers_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: artifact_identifiers artifact_identifiers_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_identifiers
    ADD CONSTRAINT artifact_identifiers_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifact_languages artifact_languages_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_languages
    ADD CONSTRAINT artifact_languages_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.canonical_languages(id);


--
-- Name: artifact_languages artifact_languages_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_languages
    ADD CONSTRAINT artifact_languages_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: artifacts artifacts_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: authority_links authority_links_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_links
    ADD CONSTRAINT authority_links_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: authority_links authority_links_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_links
    ADD CONSTRAINT authority_links_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.named_entities(id);


--
-- Name: authority_reconciliation_disputes authority_reconciliation_disputes_authority_link_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_reconciliation_disputes
    ADD CONSTRAINT authority_reconciliation_disputes_authority_link_id_fkey FOREIGN KEY (authority_link_id) REFERENCES public.authority_links(id);


--
-- Name: authority_reconciliation_disputes authority_reconciliation_disputes_scholar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authority_reconciliation_disputes
    ADD CONSTRAINT authority_reconciliation_disputes_scholar_id_fkey FOREIGN KEY (scholar_id) REFERENCES public.scholars(id);


--
-- Name: cad_examples cad_examples_meaning_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_examples
    ADD CONSTRAINT cad_examples_meaning_id_fkey FOREIGN KEY (meaning_id) REFERENCES public.cad_meanings(id);


--
-- Name: cad_meanings cad_meanings_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cad_meanings
    ADD CONSTRAINT cad_meanings_entry_id_fkey FOREIGN KEY (entry_id) REFERENCES public.cad_entries(id);


--
-- Name: collection_members collection_members_collection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collection_members
    ADD CONSTRAINT collection_members_collection_id_fkey FOREIGN KEY (collection_id) REFERENCES public.collections(collection_id);


--
-- Name: collection_members collection_members_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.collection_members
    ADD CONSTRAINT collection_members_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: concepts concepts_parent_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_parent_concept_id_fkey FOREIGN KEY (parent_concept_id) REFERENCES public.concepts(id) ON DELETE SET NULL;


--
-- Name: discussion_posts discussion_posts_reply_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discussion_posts
    ADD CONSTRAINT discussion_posts_reply_to_id_fkey FOREIGN KEY (reply_to_id) REFERENCES public.discussion_posts(id);


--
-- Name: discussion_posts discussion_posts_scholar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discussion_posts
    ADD CONSTRAINT discussion_posts_scholar_id_fkey FOREIGN KEY (scholar_id) REFERENCES public.scholars(id);


--
-- Name: entity_aliases entity_aliases_alias_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_alias_entity_id_fkey FOREIGN KEY (alias_entity_id) REFERENCES public.named_entities(id);


--
-- Name: entity_aliases entity_aliases_canonical_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_canonical_entity_id_fkey FOREIGN KEY (canonical_entity_id) REFERENCES public.named_entities(id);


--
-- Name: entity_aliases entity_aliases_merged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_merged_by_fkey FOREIGN KEY (merged_by) REFERENCES public.scholars(id);


--
-- Name: entity_mention_decisions entity_mention_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_decisions
    ADD CONSTRAINT entity_mention_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: entity_mention_decisions entity_mention_decisions_entity_mention_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_decisions
    ADD CONSTRAINT entity_mention_decisions_entity_mention_id_fkey FOREIGN KEY (entity_mention_id) REFERENCES public.entity_mentions(id);


--
-- Name: entity_mention_decisions entity_mention_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_decisions
    ADD CONSTRAINT entity_mention_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.entity_mention_decisions(id);


--
-- Name: entity_mention_evidence entity_mention_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_evidence
    ADD CONSTRAINT entity_mention_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: entity_mention_evidence entity_mention_evidence_entity_mention_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mention_evidence
    ADD CONSTRAINT entity_mention_evidence_entity_mention_id_fkey FOREIGN KEY (entity_mention_id) REFERENCES public.entity_mentions(id);


--
-- Name: entity_mentions entity_mentions_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: entity_mentions entity_mentions_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.named_entities(id);


--
-- Name: entity_mentions entity_mentions_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.text_lines(id);


--
-- Name: entity_mentions entity_mentions_token_end_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_token_end_id_fkey FOREIGN KEY (token_end_id) REFERENCES public.tokens(id);


--
-- Name: entity_mentions entity_mentions_token_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_mentions
    ADD CONSTRAINT entity_mentions_token_id_fkey FOREIGN KEY (token_id) REFERENCES public.tokens(id);


--
-- Name: entity_relationship_decisions entity_relationship_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_decisions
    ADD CONSTRAINT entity_relationship_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: entity_relationship_decisions entity_relationship_decisions_relationship_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_decisions
    ADD CONSTRAINT entity_relationship_decisions_relationship_id_fkey FOREIGN KEY (relationship_id) REFERENCES public.entity_relationships(id);


--
-- Name: entity_relationship_decisions entity_relationship_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_decisions
    ADD CONSTRAINT entity_relationship_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.entity_relationship_decisions(id);


--
-- Name: entity_relationship_evidence entity_relationship_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_evidence
    ADD CONSTRAINT entity_relationship_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: entity_relationship_evidence entity_relationship_evidence_relationship_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationship_evidence
    ADD CONSTRAINT entity_relationship_evidence_relationship_id_fkey FOREIGN KEY (relationship_id) REFERENCES public.entity_relationships(id);


--
-- Name: entity_relationships entity_relationships_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: entity_relationships entity_relationships_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.named_entities(id);


--
-- Name: entity_relationships entity_relationships_predicate_enum_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_predicate_enum_fkey FOREIGN KEY (predicate_enum) REFERENCES public.relationship_predicates(predicate);


--
-- Name: entity_relationships entity_relationships_source_mention_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_source_mention_id_fkey FOREIGN KEY (source_mention_id) REFERENCES public.entity_mentions(id);


--
-- Name: entity_relationships entity_relationships_subject_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_subject_id_fkey FOREIGN KEY (subject_id) REFERENCES public.named_entities(id);


--
-- Name: external_resources external_resources_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_resources
    ADD CONSTRAINT external_resources_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: annotation_runs fk_annotation_runs_publication; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_runs
    ADD CONSTRAINT fk_annotation_runs_publication FOREIGN KEY (publication_id) REFERENCES public.publications(id);


--
-- Name: fragment_join_decisions fragment_join_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_decisions
    ADD CONSTRAINT fragment_join_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: fragment_join_decisions fragment_join_decisions_join_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_decisions
    ADD CONSTRAINT fragment_join_decisions_join_id_fkey FOREIGN KEY (join_id) REFERENCES public.fragment_joins(id);


--
-- Name: fragment_join_decisions fragment_join_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_decisions
    ADD CONSTRAINT fragment_join_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.fragment_join_decisions(id);


--
-- Name: fragment_join_discussion_threads fragment_join_discussion_threads_join_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_discussion_threads
    ADD CONSTRAINT fragment_join_discussion_threads_join_id_fkey FOREIGN KEY (join_id) REFERENCES public.fragment_joins(id);


--
-- Name: fragment_join_discussion_threads fragment_join_discussion_threads_resolution_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_discussion_threads
    ADD CONSTRAINT fragment_join_discussion_threads_resolution_decision_id_fkey FOREIGN KEY (resolution_decision_id) REFERENCES public.fragment_join_decisions(id);


--
-- Name: fragment_join_evidence fragment_join_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_evidence
    ADD CONSTRAINT fragment_join_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: fragment_join_evidence fragment_join_evidence_join_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_join_evidence
    ADD CONSTRAINT fragment_join_evidence_join_id_fkey FOREIGN KEY (join_id) REFERENCES public.fragment_joins(id);


--
-- Name: fragment_joins fragment_joins_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: fragment_joins fragment_joins_fragment_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_fragment_a_fkey FOREIGN KEY (fragment_a) REFERENCES public.artifacts(p_number);


--
-- Name: fragment_joins fragment_joins_fragment_b_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_fragment_b_fkey FOREIGN KEY (fragment_b) REFERENCES public.artifacts(p_number);


--
-- Name: fragment_joins fragment_joins_join_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fragment_joins
    ADD CONSTRAINT fragment_joins_join_group_id_fkey FOREIGN KEY (join_group_id) REFERENCES public.join_groups(id);


--
-- Name: glossary_entries glossary_entries_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_entries
    ADD CONSTRAINT glossary_entries_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: glossary_forms glossary_forms_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_forms
    ADD CONSTRAINT glossary_forms_entry_id_fkey FOREIGN KEY (entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: glossary_relationships glossary_relationships_from_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_relationships
    ADD CONSTRAINT glossary_relationships_from_entry_id_fkey FOREIGN KEY (from_entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: glossary_relationships glossary_relationships_to_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_relationships
    ADD CONSTRAINT glossary_relationships_to_entry_id_fkey FOREIGN KEY (to_entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: glossary_semantic_fields glossary_semantic_fields_glossary_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_semantic_fields
    ADD CONSTRAINT glossary_semantic_fields_glossary_entry_id_fkey FOREIGN KEY (glossary_entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: glossary_semantic_fields glossary_semantic_fields_semantic_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_semantic_fields
    ADD CONSTRAINT glossary_semantic_fields_semantic_field_id_fkey FOREIGN KEY (semantic_field_id) REFERENCES public.semantic_fields(id);


--
-- Name: glossary_senses glossary_senses_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_senses
    ADD CONSTRAINT glossary_senses_entry_id_fkey FOREIGN KEY (entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: import_log import_log_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_log
    ADD CONSTRAINT import_log_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: interpretations interpretations_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interpretations
    ADD CONSTRAINT interpretations_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.interpretations(id) ON DELETE SET NULL;


--
-- Name: intertextuality_links intertextuality_links_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: intertextuality_links intertextuality_links_source_token_end_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_source_token_end_fkey FOREIGN KEY (source_token_end) REFERENCES public.tokens(id);


--
-- Name: intertextuality_links intertextuality_links_source_token_start_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_source_token_start_fkey FOREIGN KEY (source_token_start) REFERENCES public.tokens(id);


--
-- Name: intertextuality_links intertextuality_links_target_token_end_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_target_token_end_fkey FOREIGN KEY (target_token_end) REFERENCES public.tokens(id);


--
-- Name: intertextuality_links intertextuality_links_target_token_start_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intertextuality_links
    ADD CONSTRAINT intertextuality_links_target_token_start_fkey FOREIGN KEY (target_token_start) REFERENCES public.tokens(id);


--
-- Name: lemma_concepts lemma_concepts_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemma_concepts
    ADD CONSTRAINT lemma_concepts_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE CASCADE;


--
-- Name: lemmatization_decisions lemmatization_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_decisions
    ADD CONSTRAINT lemmatization_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: lemmatization_decisions lemmatization_decisions_lemmatization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_decisions
    ADD CONSTRAINT lemmatization_decisions_lemmatization_id_fkey FOREIGN KEY (lemmatization_id) REFERENCES public.lemmatizations(id);


--
-- Name: lemmatization_decisions lemmatization_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_decisions
    ADD CONSTRAINT lemmatization_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.lemmatization_decisions(id);


--
-- Name: lemmatization_discussion_threads lemmatization_discussion_threads_lemmatization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_discussion_threads
    ADD CONSTRAINT lemmatization_discussion_threads_lemmatization_id_fkey FOREIGN KEY (lemmatization_id) REFERENCES public.lemmatizations(id);


--
-- Name: lemmatization_discussion_threads lemmatization_discussion_threads_resolution_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_discussion_threads
    ADD CONSTRAINT lemmatization_discussion_threads_resolution_decision_id_fkey FOREIGN KEY (resolution_decision_id) REFERENCES public.lemmatization_decisions(id);


--
-- Name: lemmatization_evidence lemmatization_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_evidence
    ADD CONSTRAINT lemmatization_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: lemmatization_evidence lemmatization_evidence_lemmatization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatization_evidence
    ADD CONSTRAINT lemmatization_evidence_lemmatization_id_fkey FOREIGN KEY (lemmatization_id) REFERENCES public.lemmatizations(id);


--
-- Name: lemmatizations lemmatizations_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations
    ADD CONSTRAINT lemmatizations_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: lemmatizations lemmatizations_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations
    ADD CONSTRAINT lemmatizations_entry_id_fkey FOREIGN KEY (entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: lemmatizations lemmatizations_norm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations
    ADD CONSTRAINT lemmatizations_norm_id_fkey FOREIGN KEY (norm_id) REFERENCES public.lexical_norms(id) ON DELETE SET NULL;


--
-- Name: lemmatizations lemmatizations_token_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lemmatizations
    ADD CONSTRAINT lemmatizations_token_id_fkey FOREIGN KEY (token_id) REFERENCES public.tokens(id);


--
-- Name: lexical_norm_forms lexical_norm_forms_norm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norm_forms
    ADD CONSTRAINT lexical_norm_forms_norm_id_fkey FOREIGN KEY (norm_id) REFERENCES public.lexical_norms(id) ON DELETE CASCADE;


--
-- Name: lexical_norms lexical_norms_lemma_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_norms
    ADD CONSTRAINT lexical_norms_lemma_id_fkey FOREIGN KEY (lemma_id) REFERENCES public.lexical_lemmas(id) ON DELETE CASCADE;


--
-- Name: lexical_senses lexical_senses_lemma_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_senses
    ADD CONSTRAINT lexical_senses_lemma_id_fkey FOREIGN KEY (lemma_id) REFERENCES public.lexical_lemmas(id) ON DELETE CASCADE;


--
-- Name: lexical_sign_lemma_associations lexical_sign_lemma_associations_lemma_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_sign_lemma_associations
    ADD CONSTRAINT lexical_sign_lemma_associations_lemma_id_fkey FOREIGN KEY (lemma_id) REFERENCES public.lexical_lemmas(id) ON DELETE CASCADE;


--
-- Name: lexical_sign_lemma_associations lexical_sign_lemma_associations_sign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_sign_lemma_associations
    ADD CONSTRAINT lexical_sign_lemma_associations_sign_id_fkey FOREIGN KEY (sign_id) REFERENCES public.lexical_signs(id) ON DELETE CASCADE;


--
-- Name: lexical_tablet_occurrences lexical_tablet_occurrences_lemma_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences
    ADD CONSTRAINT lexical_tablet_occurrences_lemma_id_fkey FOREIGN KEY (lemma_id) REFERENCES public.lexical_lemmas(id) ON DELETE CASCADE;


--
-- Name: lexical_tablet_occurrences lexical_tablet_occurrences_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences
    ADD CONSTRAINT lexical_tablet_occurrences_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: lexical_tablet_occurrences lexical_tablet_occurrences_sense_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences
    ADD CONSTRAINT lexical_tablet_occurrences_sense_id_fkey FOREIGN KEY (sense_id) REFERENCES public.lexical_senses(id) ON DELETE CASCADE;


--
-- Name: lexical_tablet_occurrences lexical_tablet_occurrences_sign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lexical_tablet_occurrences
    ADD CONSTRAINT lexical_tablet_occurrences_sign_id_fkey FOREIGN KEY (sign_id) REFERENCES public.lexical_signs(id) ON DELETE CASCADE;


--
-- Name: morphology morphology_lemmatization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.morphology
    ADD CONSTRAINT morphology_lemmatization_id_fkey FOREIGN KEY (lemmatization_id) REFERENCES public.lemmatizations(id);


--
-- Name: named_entities named_entities_glossary_entry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.named_entities
    ADD CONSTRAINT named_entities_glossary_entry_id_fkey FOREIGN KEY (glossary_entry_id) REFERENCES public.glossary_entries(entry_id);


--
-- Name: pipeline_status pipeline_status_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pipeline_status
    ADD CONSTRAINT pipeline_status_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: publication_authors publication_authors_publication_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_publication_id_fkey FOREIGN KEY (publication_id) REFERENCES public.publications(id);


--
-- Name: publication_authors publication_authors_scholar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_authors
    ADD CONSTRAINT publication_authors_scholar_id_fkey FOREIGN KEY (scholar_id) REFERENCES public.scholars(id);


--
-- Name: publication_citations publication_citations_cited_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_citations
    ADD CONSTRAINT publication_citations_cited_id_fkey FOREIGN KEY (cited_id) REFERENCES public.publications(id);


--
-- Name: publication_citations publication_citations_citing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publication_citations
    ADD CONSTRAINT publication_citations_citing_id_fkey FOREIGN KEY (citing_id) REFERENCES public.publications(id);


--
-- Name: publications publications_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: publications publications_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.publications
    ADD CONSTRAINT publications_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.publications(id);


--
-- Name: scholar_merge_log scholar_merge_log_kept_scholar_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholar_merge_log
    ADD CONSTRAINT scholar_merge_log_kept_scholar_id_fkey FOREIGN KEY (kept_scholar_id) REFERENCES public.scholars(id);


--
-- Name: scholarly_annotation_discussion_threads scholarly_annotation_discussion_threads_annotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_discussion_threads
    ADD CONSTRAINT scholarly_annotation_discussion_threads_annotation_id_fkey FOREIGN KEY (annotation_id) REFERENCES public.scholarly_annotations(id);


--
-- Name: scholarly_annotation_evidence scholarly_annotation_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_evidence
    ADD CONSTRAINT scholarly_annotation_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: scholarly_annotation_evidence scholarly_annotation_evidence_annotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotation_evidence
    ADD CONSTRAINT scholarly_annotation_evidence_annotation_id_fkey FOREIGN KEY (annotation_id) REFERENCES public.scholarly_annotations(id);


--
-- Name: scholarly_annotations scholarly_annotations_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: scholarly_annotations scholarly_annotations_artifact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES public.artifacts(p_number);


--
-- Name: scholarly_annotations scholarly_annotations_composite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_composite_id_fkey FOREIGN KEY (composite_id) REFERENCES public.composites(q_number);


--
-- Name: scholarly_annotations scholarly_annotations_line_end_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_line_end_id_fkey FOREIGN KEY (line_end_id) REFERENCES public.text_lines(id);


--
-- Name: scholarly_annotations scholarly_annotations_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.text_lines(id);


--
-- Name: scholarly_annotations scholarly_annotations_sign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_sign_id_fkey FOREIGN KEY (sign_id) REFERENCES public.signs(sign_id);


--
-- Name: scholarly_annotations scholarly_annotations_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.scholarly_annotations(id);


--
-- Name: scholarly_annotations scholarly_annotations_surface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_surface_id_fkey FOREIGN KEY (surface_id) REFERENCES public.surfaces(id);


--
-- Name: scholarly_annotations scholarly_annotations_token_end_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_token_end_id_fkey FOREIGN KEY (token_end_id) REFERENCES public.tokens(id);


--
-- Name: scholarly_annotations scholarly_annotations_token_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarly_annotations
    ADD CONSTRAINT scholarly_annotations_token_id_fkey FOREIGN KEY (token_id) REFERENCES public.tokens(id);


--
-- Name: semantic_fields semantic_fields_parent_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_fields
    ADD CONSTRAINT semantic_fields_parent_field_id_fkey FOREIGN KEY (parent_field_id) REFERENCES public.semantic_fields(id);


--
-- Name: sign_annotation_evidence sign_annotation_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotation_evidence
    ADD CONSTRAINT sign_annotation_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: sign_annotation_evidence sign_annotation_evidence_sign_annotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotation_evidence
    ADD CONSTRAINT sign_annotation_evidence_sign_annotation_id_fkey FOREIGN KEY (sign_annotation_id) REFERENCES public.sign_annotations(id);


--
-- Name: sign_annotations sign_annotations_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotations
    ADD CONSTRAINT sign_annotations_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: sign_annotations sign_annotations_sign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotations
    ADD CONSTRAINT sign_annotations_sign_id_fkey FOREIGN KEY (sign_id) REFERENCES public.signs(sign_id);


--
-- Name: sign_annotations sign_annotations_surface_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_annotations
    ADD CONSTRAINT sign_annotations_surface_image_id_fkey FOREIGN KEY (surface_image_id) REFERENCES public.surface_images(id);


--
-- Name: sign_concordance sign_concordance_ogsl_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_concordance
    ADD CONSTRAINT sign_concordance_ogsl_id_fkey FOREIGN KEY (ogsl_id) REFERENCES public.signs(sign_id);


--
-- Name: sign_values sign_values_sign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_values
    ADD CONSTRAINT sign_values_sign_id_fkey FOREIGN KEY (sign_id) REFERENCES public.signs(sign_id);


--
-- Name: sign_variants sign_variants_base_sign_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_variants
    ADD CONSTRAINT sign_variants_base_sign_fkey FOREIGN KEY (base_sign) REFERENCES public.signs(sign_id);


--
-- Name: surface_images surface_images_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_images
    ADD CONSTRAINT surface_images_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: surface_images surface_images_surface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_images
    ADD CONSTRAINT surface_images_surface_id_fkey FOREIGN KEY (surface_id) REFERENCES public.surfaces(id);


--
-- Name: surfaces surfaces_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surfaces
    ADD CONSTRAINT surfaces_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: text_lines text_lines_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_lines
    ADD CONSTRAINT text_lines_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- Name: text_lines text_lines_surface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_lines
    ADD CONSTRAINT text_lines_surface_id_fkey FOREIGN KEY (surface_id) REFERENCES public.surfaces(id);


--
-- Name: token_reading_decisions token_reading_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_decisions
    ADD CONSTRAINT token_reading_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: token_reading_decisions token_reading_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_decisions
    ADD CONSTRAINT token_reading_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.token_reading_decisions(id);


--
-- Name: token_reading_decisions token_reading_decisions_token_reading_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_decisions
    ADD CONSTRAINT token_reading_decisions_token_reading_id_fkey FOREIGN KEY (token_reading_id) REFERENCES public.token_readings(id);


--
-- Name: token_reading_discussion_threads token_reading_discussion_threads_resolution_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_discussion_threads
    ADD CONSTRAINT token_reading_discussion_threads_resolution_decision_id_fkey FOREIGN KEY (resolution_decision_id) REFERENCES public.token_reading_decisions(id);


--
-- Name: token_reading_discussion_threads token_reading_discussion_threads_token_reading_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_discussion_threads
    ADD CONSTRAINT token_reading_discussion_threads_token_reading_id_fkey FOREIGN KEY (token_reading_id) REFERENCES public.token_readings(id);


--
-- Name: token_reading_evidence token_reading_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_evidence
    ADD CONSTRAINT token_reading_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: token_reading_evidence token_reading_evidence_token_reading_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_reading_evidence
    ADD CONSTRAINT token_reading_evidence_token_reading_id_fkey FOREIGN KEY (token_reading_id) REFERENCES public.token_readings(id);


--
-- Name: token_readings token_readings_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_readings
    ADD CONSTRAINT token_readings_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: token_readings token_readings_token_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_readings
    ADD CONSTRAINT token_readings_token_id_fkey FOREIGN KEY (token_id) REFERENCES public.tokens(id);


--
-- Name: tokens tokens_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT tokens_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.text_lines(id);


--
-- Name: translation_decisions translation_decisions_decided_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_decisions
    ADD CONSTRAINT translation_decisions_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES public.scholars(id);


--
-- Name: translation_decisions translation_decisions_supersedes_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_decisions
    ADD CONSTRAINT translation_decisions_supersedes_id_fkey FOREIGN KEY (supersedes_id) REFERENCES public.translation_decisions(id);


--
-- Name: translation_decisions translation_decisions_translation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_decisions
    ADD CONSTRAINT translation_decisions_translation_id_fkey FOREIGN KEY (translation_id) REFERENCES public.translations(id);


--
-- Name: translation_discussion_threads translation_discussion_threads_resolution_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_discussion_threads
    ADD CONSTRAINT translation_discussion_threads_resolution_decision_id_fkey FOREIGN KEY (resolution_decision_id) REFERENCES public.translation_decisions(id);


--
-- Name: translation_discussion_threads translation_discussion_threads_translation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_discussion_threads
    ADD CONSTRAINT translation_discussion_threads_translation_id_fkey FOREIGN KEY (translation_id) REFERENCES public.translations(id);


--
-- Name: translation_evidence translation_evidence_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_evidence
    ADD CONSTRAINT translation_evidence_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.scholars(id);


--
-- Name: translation_evidence translation_evidence_translation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translation_evidence
    ADD CONSTRAINT translation_evidence_translation_id_fkey FOREIGN KEY (translation_id) REFERENCES public.translations(id);


--
-- Name: translations translations_annotation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_annotation_run_id_fkey FOREIGN KEY (annotation_run_id) REFERENCES public.annotation_runs(id);


--
-- Name: translations translations_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.text_lines(id);


--
-- Name: translations translations_p_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_p_number_fkey FOREIGN KEY (p_number) REFERENCES public.artifacts(p_number);


--
-- PostgreSQL database dump complete
--
