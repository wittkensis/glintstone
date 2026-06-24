#!/usr/bin/env bash
# smoke-with-auth.sh — post-deploy authed render check that does NOT mint or
# delete production user_sessions rows (#280).
#
# Background
#   Authed post-deploy checks used to create a throwaway session row and delete
#   it afterwards, touching the live sessions table on every deploy. Instead this
#   script reuses a single, pre-provisioned read-only verify session (see
#   provision_verify_session.py) by sending its token as the `session_token`
#   cookie. The only write it causes server-side is a `last_seen_at` UPDATE
#   (a touch) on that one stable row — never an INSERT, never a DELETE.
#
# What it checks
#   1. /_me returns HTTP 200 with a JSON body → the session is recognised, i.e.
#      authed pages will render as logged-in (the thing we actually want to
#      verify after a deploy). A 204 means the token was rejected (logged-out).
#   2. Optionally, a target authed page renders 200 and contains an expected
#      logged-in marker.
#
# Usage
#   GLINTSTONE_VERIFY_TOKEN=<raw-token> ./ops/deploy/smoke-with-auth.sh \
#       [BASE_URL] [AUTHED_PATH] [EXPECT_SUBSTRING]
#
#   BASE_URL          default https://glintstone.org
#   AUTHED_PATH       optional authed page to additionally fetch (e.g. /account)
#   EXPECT_SUBSTRING  optional string that must appear in AUTHED_PATH's HTML
#                     (default: header-user — the logged-in chip id)
#
# Exit codes
#   0  authed render check passed
#   1  token rejected / page failed / missing token

set -euo pipefail

BASE_URL="${1:-https://glintstone.org}"
AUTHED_PATH="${2:-}"
EXPECT_SUBSTRING="${3:-header-user}"

if [ -z "${GLINTSTONE_VERIFY_TOKEN:-}" ]; then
    echo "::error::GLINTSTONE_VERIFY_TOKEN is not set." >&2
    echo "Provision one with: python -m ops.deploy.provision_verify_session" >&2
    exit 1
fi

COOKIE="session_token=${GLINTSTONE_VERIFY_TOKEN}"

# --- 1. /_me must recognise the verify session (200, not 204) ---
echo "Checking authed session against ${BASE_URL}/_me ..."
me_status="$(curl -fsS -o /tmp/gs_verify_me.json -w '%{http_code}' \
    --max-time 10 \
    --cookie "$COOKIE" \
    "${BASE_URL}/_me" || true)"

if [ "$me_status" = "204" ]; then
    echo "::error::/_me returned 204 — the verify token was NOT recognised." >&2
    echo "The session may have expired; re-run provision_verify_session.py --rotate." >&2
    exit 1
fi

if [ "$me_status" != "200" ]; then
    echo "::error::/_me returned HTTP $me_status (expected 200)." >&2
    exit 1
fi

echo "OK: /_me recognised the verify session (HTTP 200, logged-in)."

# --- 2. Optional: a specific authed page renders with the logged-in marker ---
if [ -n "$AUTHED_PATH" ]; then
    echo "Checking authed page ${BASE_URL}${AUTHED_PATH} ..."
    page_status="$(curl -fsS -o /tmp/gs_verify_page.html -w '%{http_code}' \
        --max-time 10 \
        --cookie "$COOKIE" \
        "${BASE_URL}${AUTHED_PATH}" || true)"

    if [ "$page_status" != "200" ]; then
        echo "::error::${AUTHED_PATH} returned HTTP $page_status (expected 200)." >&2
        exit 1
    fi

    if ! grep -q "$EXPECT_SUBSTRING" /tmp/gs_verify_page.html; then
        echo "::error::${AUTHED_PATH} did not contain expected marker '$EXPECT_SUBSTRING'." >&2
        exit 1
    fi
    echo "OK: ${AUTHED_PATH} rendered logged-in (found '$EXPECT_SUBSTRING')."
fi

echo "SMOKE_AUTH_OK"
