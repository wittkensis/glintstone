-- Migration 037: user role column
--
-- Adds a 'role' column to users (values: 'admin' | 'standard').
-- Default is 'standard' for all new sign-ups.
-- Seeds eric.wittke@gmail.com as the initial admin.

BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role text NOT NULL DEFAULT 'standard'
    CHECK (role IN ('admin', 'standard'));

UPDATE users SET role = 'admin' WHERE email = 'eric.wittke@gmail.com';

COMMIT;
