-- Migration 046: Add token_id FK to sign_annotations
--
-- Wires sign annotations (Tablet Viewer, PRD-005) to the tokens table so the
-- `sign:selected` event can carry a real tokenId instead of always null.
-- Unblocks FR11/FR12: highlighting the matched token in the Translation Builder
-- when a sign is selected in the Tablet Viewer.
--
-- token_id: NULL = unmatched (legacy rows and signs with no token mapping).
-- ON DELETE SET NULL so deleting a token does not orphan/delete annotations.

BEGIN;

ALTER TABLE sign_annotations
    ADD COLUMN IF NOT EXISTS token_id INTEGER
    REFERENCES tokens(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_sign_annotations_token_id
    ON sign_annotations(token_id);

COMMENT ON COLUMN sign_annotations.token_id IS
    'Nullable FK to tokens.id. Links a sign annotation to its matched token so '
    'the Tablet Viewer sign:selected event can highlight the token in the '
    'Translation Builder. NULL = no token match.';

COMMIT;
