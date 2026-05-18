-- Migration 028: user saved items (bookmarks)
--
-- Intentionally generic: item_type + item_id allows future extension to
-- scholars, lemmas, etc. without schema changes. Phase 1 only uses
-- item_type='artifact' with p_number as item_id.

BEGIN;

CREATE TABLE IF NOT EXISTS user_saved_items (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_type   text NOT NULL,
    item_id     text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, item_type, item_id)
);

CREATE INDEX idx_user_saved_items_user_id ON user_saved_items(user_id);
CREATE INDEX idx_user_saved_items_lookup ON user_saved_items(user_id, item_type);

GRANT SELECT, INSERT, UPDATE, DELETE ON user_saved_items TO glintstone;

COMMIT;
