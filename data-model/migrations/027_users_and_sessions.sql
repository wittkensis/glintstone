-- Migration 027: users, auth methods, sessions, API keys
--
-- Foundation for researcher identity: ORCID OAuth and magic-link email auth,
-- bearer-token sessions, and tiered API keys (prefix: glst_).
--
-- Tables are owned by wittkensis; glintstone app user gets DML only.

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email               text UNIQUE NOT NULL,
    display_name        text,
    orcid_id            text UNIQUE,
    created_at          timestamptz NOT NULL DEFAULT now(),
    email_verified_at   timestamptz
);

GRANT SELECT, INSERT, UPDATE, DELETE ON users TO glintstone;

CREATE TABLE IF NOT EXISTS user_auth_methods (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider    text NOT NULL,
    provider_id text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (provider, provider_id)
);

GRANT SELECT, INSERT, UPDATE, DELETE ON user_auth_methods TO glintstone;

CREATE TABLE IF NOT EXISTS user_sessions (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   text NOT NULL UNIQUE,
    created_at   timestamptz NOT NULL DEFAULT now(),
    expires_at   timestamptz NOT NULL,
    last_seen_at timestamptz,
    ip           text,
    user_agent   text
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);

GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO glintstone;

CREATE TABLE IF NOT EXISTS api_keys (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash     text NOT NULL UNIQUE,
    label        text NOT NULL,
    tier         text NOT NULL DEFAULT 'free',
    created_at   timestamptz NOT NULL DEFAULT now(),
    last_used_at timestamptz,
    revoked_at   timestamptz
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO glintstone;

COMMIT;
