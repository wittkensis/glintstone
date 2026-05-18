-- Migration 032: NFC audit on lexical text columns (notice only)
--
-- The original plan was to rewrite every stored citation_form / guide_word /
-- sign_name / norm / written_form in place to NFC. That collides with the
-- existing unique constraints when the same source contributed the same
-- entity twice in different normalizations — e.g. ePSD2 wrote `kāru[quay]N`
-- both as NFD (k+ā with combining macron) and NFC (kā precomposed), and
-- both rows independently satisfy lexical_lemmas_composite UNIQUE
-- (cf_gw_pos, source). Normalizing them in place would violate the index.
--
-- The read-path fix (api/repositories/lexical_repo.py `_nfc` + core/lexical.py
-- `lookup_lemmas_by_form`) already collapses the encoding mismatch on every
-- user query. v2 connectors (epsd2, oracc_norms, scholars) normalize on
-- insert, so new rows are clean. The remaining concern is purely cosmetic:
-- browse views may show a duplicate row pair until a follow-up dedup
-- migration repoints the relevant FKs and merges attestations.
--
-- This migration reports the affected counts so the operator knows the
-- backlog without enforcing anything. See issue #49.

BEGIN;

DO $$
DECLARE
  n_lemma  integer;
  n_sign   integer;
  n_norm   integer;
  n_form   integer;
BEGIN
  SELECT COUNT(*) INTO n_lemma FROM lexical_lemmas
   WHERE citation_form IS DISTINCT FROM normalize(citation_form, NFC)
      OR guide_word    IS DISTINCT FROM normalize(guide_word, NFC);

  SELECT COUNT(*) INTO n_sign FROM lexical_signs
   WHERE sign_name IS DISTINCT FROM normalize(sign_name, NFC);

  SELECT COUNT(*) INTO n_norm FROM lexical_norms
   WHERE norm IS DISTINCT FROM normalize(norm, NFC);

  SELECT COUNT(*) INTO n_form FROM lexical_norm_forms
   WHERE written_form IS DISTINCT FROM normalize(written_form, NFC);

  IF n_lemma + n_sign + n_norm + n_form > 0 THEN
    RAISE NOTICE 'NFC backlog (read path handles all of these): lemma=%, sign=%, norm=%, form=%',
      n_lemma, n_sign, n_norm, n_form;
  END IF;
END $$;

COMMIT;
