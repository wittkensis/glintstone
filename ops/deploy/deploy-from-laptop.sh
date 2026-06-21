#!/usr/bin/env bash
# Glintstone — laptop fallback deploy.
#
# WHEN TO USE THIS
#   The CI -> VPS deploy (.github/workflows/deploy.yml) is the normal path. Use
#   this script ONLY when CI can't deploy (ssh-keyscan flake that survives the
#   in-workflow retries, a GitHub Actions outage, or a deploy that needs to ship
#   before the next CI run). It is the documented, repeatable form of the manual
#   fallback that was previously typed by hand each time.
#
# WHAT IT FIXES vs. typing the command by hand
#   1. ENV OVERRIDE (snapshot-gate trap, infra-incident
#      `laptop-fallback-env-app-env-override`): the laptop .env carries
#      APP_ENV=local. deploy.sh only sources .env when DEPLOY_HOST is UNSET, so
#      we EXPORT DEPLOY_HOST / APP_ENV / SSH_KEY_PATH here to skip that source
#      block entirely — APP_ENV=local can no longer override our APP_ENV=production
#      and trip the pre-deploy pg_dump safety gate.
#   2. LOCAL-MAIN DRIFT (infra-incident
#      `local-main-drifts-behind-origin-after-laptop-fallback-deploy`, #266): a
#      hand-run fallback deploys whatever is checked out but never advances local
#      main, so the next engineer branches from a stale HEAD and risks regressing
#      merged work. This script fast-forwards local main to origin/main BEFORE
#      deploying (so we ship what origin has) and re-confirms the sync AFTER, and
#      refuses to deploy a main that has drifted from origin in a way that can't
#      fast-forward (you'd be shipping something origin doesn't have).
#
# USAGE
#   ./ops/deploy/deploy-from-laptop.sh                 # deploy api app www (default)
#   ./ops/deploy/deploy-from-laptop.sh api app         # deploy a subset
#   DEPLOY_HOST=1.2.3.4 ./ops/deploy/deploy-from-laptop.sh api   # override host
#
# ENV (override any of these; sensible defaults baked in):
#   DEPLOY_HOST    default 76.13.208.149         (the prod VPS)
#   APP_ENV        default production            (forces the snapshot gate ON)
#   SSH_KEY_PATH   default ~/.ssh/glintstone_deploy
#   SKIP_GIT_SYNC  set to 1 to bypass the main<->origin sync guard (NOT advised)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- The three overrides that make the fallback safe. EXPORT (not just set) so
#     deploy.sh sees DEPLOY_HOST already set and skips sourcing the laptop .env. ---
export DEPLOY_HOST="${DEPLOY_HOST:-76.13.208.149}"
export APP_ENV="${APP_ENV:-production}"
export SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/glintstone_deploy}"

TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(api app www)

echo "=== Glintstone laptop fallback deploy ==="
echo "  Host:     $DEPLOY_HOST"
echo "  Env:      $APP_ENV"
echo "  Key:      $SSH_KEY_PATH"
echo "  Targets:  ${TARGETS[*]}"
echo

# --- Git sync guard: ship origin/main, keep local main in lock-step. ---
sync_main_to_origin() {
    local phase="$1"   # "pre" or "post"
    git -C "$PROJECT_DIR" fetch origin main --quiet

    local local_sha origin_sha base
    local_sha="$(git -C "$PROJECT_DIR" rev-parse main 2>/dev/null || echo none)"
    origin_sha="$(git -C "$PROJECT_DIR" rev-parse origin/main)"

    if [ "$local_sha" = "$origin_sha" ]; then
        echo "  [git $phase] local main == origin/main ($origin_sha) ✓"
        return 0
    fi

    base="$(git -C "$PROJECT_DIR" merge-base main origin/main 2>/dev/null || echo none)"
    if [ "$base" = "$local_sha" ]; then
        # local main is strictly BEHIND origin — safe fast-forward.
        echo "  [git $phase] local main is behind origin/main — fast-forwarding..."
        git -C "$PROJECT_DIR" branch -f main origin/main
        echo "  [git $phase] local main fast-forwarded to $origin_sha ✓"
    elif [ "$base" = "$origin_sha" ]; then
        echo "::error:: local main is AHEAD of origin/main — you have unpushed commits."
        echo "::error:: Push them (and let CI deploy) or reset; refusing to fallback-deploy"
        echo "::error:: a main that origin doesn't have. Override with SKIP_GIT_SYNC=1."
        [ "${SKIP_GIT_SYNC:-}" = "1" ] || exit 1
    else
        echo "::error:: local main and origin/main have DIVERGED (base $base)."
        echo "::error:: Reconcile manually before deploying. Override with SKIP_GIT_SYNC=1."
        [ "${SKIP_GIT_SYNC:-}" = "1" ] || exit 1
    fi
}

if [ "${SKIP_GIT_SYNC:-}" != "1" ]; then
    echo "Syncing local main to origin/main before deploy..."
    sync_main_to_origin pre
    echo
fi

# --- Hand off to the real deploy. APP_ENV=production keeps the snapshot gate ON. ---
"$SCRIPT_DIR/deploy.sh" "${TARGETS[@]}"
deploy_rc=$?

echo
if [ "$deploy_rc" -ne 0 ]; then
    echo "::error:: deploy.sh exited $deploy_rc — NOT touching local main."
    exit "$deploy_rc"
fi

# --- Post-deploy: re-confirm local main is in lock-step with origin so the next
#     engineer branches from a fresh HEAD. This is the anti-drift backstop. ---
if [ "${SKIP_GIT_SYNC:-}" != "1" ]; then
    echo "Re-confirming local main == origin/main after deploy..."
    sync_main_to_origin post
fi

echo
echo "=== Laptop fallback deploy complete ==="
