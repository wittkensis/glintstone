-- Migration 032: normalize lexical text columns to Unicode NFC
--
-- Sign names, lemma citation forms, normalized forms, and written forms were
-- written with mixed Unicode normalization (NFC vs NFD, e.g. "š" stored
-- variously as U+0161 or "s" + U+030C). Read-side queries using `=` fail
-- across normalization boundaries, producing missed lookups in the Knowledge
-- Bar Translation Assistant and Dictionary.
--
-- This migration rewrites every affected row in place to NFC. Read paths in
-- api/repositories/lexical_repo.py and core/lexical.py also normalize inputs
-- (issue #47).
--
-- Idempotent: re-running is a no-op once all rows are NFC.

BEGIN;

-- Lock the targets so concurrent imports don't race the rewrite.
LOCK TABLE lexical_signs IN SHARE MODE;
LOCK TABLE lexical_lemmas IN SHARE MODE;
LOCK TABLE lexical_norms IN SHARE MODE;
LOCK TABLE lexical_norm_forms IN SHARE MODE;

UPDATE lexical_signs
   SET sign_name = normalize(sign_name, NFC)
 WHERE sign_name IS DISTINCT FROM normalize(sign_name, NFC);

-- values[] is a text[] of readings — rewrite per-element.
UPDATE lexical_signs
   SET values = ARRAY(
       SELECT normalize(v, NFC) FROM unnest(values) AS v
   )
 WHERE values IS NOT NULL
   AND values <> ARRAY(SELECT normalize(v, NFC) FROM unnest(values) AS v);

UPDATE lexical_lemmas
   SET citation_form = normalize(citation_form, NFC)
 WHERE citation_form IS DISTINCT FROM normalize(citation_form, NFC);

UPDATE lexical_lemmas
   SET guide_word = normalize(guide_word, NFC)
 WHERE guide_word IS DISTINCT FROM normalize(guide_word, NFC);

UPDATE lexical_norms
   SET norm = normalize(norm, NFC)
 WHERE norm IS DISTINCT FROM normalize(norm, NFC);

UPDATE lexical_norm_forms
   SET written_form = normalize(written_form, NFC)
 WHERE written_form IS DISTINCT FROM normalize(written_form, NFC);

COMMIT;
