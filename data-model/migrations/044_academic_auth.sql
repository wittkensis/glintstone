-- Migration 044: Academic auth — invite codes + password auth
--
-- Adds password auth fields to the existing users table (from 027).
-- Adds invite_codes table.
-- Does NOT create a new sessions table — user_sessions from 027 is used by
-- the existing session_repo.py and is already suitable for password auth.
--
-- Tables owned by wittkensis; app connects as glintstone.

BEGIN;

-- Invite codes table (new — must exist before invite_code_id FK on users)
CREATE TABLE IF NOT EXISTS invite_codes (
    id          SERIAL PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    label       TEXT,               -- e.g. "Cohort 1 — Dr. Al-Rashid"
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    used_by_email TEXT,             -- denormalized copy; email at time of use
    used_at     TIMESTAMPTZ
);

GRANT SELECT, INSERT, UPDATE ON invite_codes TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE invite_codes_id_seq TO glintstone;

-- Add password auth fields to existing users table.
-- All columns are nullable so that existing ORCID/magic-link users are unaffected.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash  TEXT,
    ADD COLUMN IF NOT EXISTS name           TEXT,
    ADD COLUMN IF NOT EXISTS affiliation    TEXT,
    ADD COLUMN IF NOT EXISTS invite_code_id INTEGER REFERENCES invite_codes(id);

-- Index for invite code lookup during registration
CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON invite_codes(code);

COMMIT;
