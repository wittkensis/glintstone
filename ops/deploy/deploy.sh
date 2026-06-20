#!/usr/bin/env bash
# Glintstone v2 — Deploy to Hostinger VPS
#
# Works from either:
#   1. Local laptop  (reads DEPLOY_HOST from .env)
#   2. GitHub Actions (reads DEPLOY_HOST, SSH_KEY_PATH, RELEASE_TAG from env)
#
# Deploys to a versioned release directory and swaps a `current` symlink so
# rollback is one symlink change away.
#
# Usage:
#   ./ops/deploy/deploy.sh                      # deploy everything
#   ./ops/deploy/deploy.sh api                  # API only
#   ./ops/deploy/deploy.sh app www               # web app + marketing site
#   ./ops/deploy/deploy.sh api --force-no-snapshot  # skip pre-deploy DB snapshot
#
# Safety: a real deploy (DEPLOY_HOST set) aborts unless APP_ENV is 'production'
# or 'staging', because the pre-deploy pg_dump snapshot is gated on that label —
# deploying with APP_ENV=local would hit prod with NO backup. Pass
# --force-no-snapshot to override deliberately.
#
# Env vars (all optional unless noted):
#   DEPLOY_HOST       — VPS IP or hostname (REQUIRED; loaded from .env if unset)
#   DEPLOY_USER       — defaults to "deploy"
#   DEPLOY_REMOTE_DIR — defaults to /var/www/glintstone
#   RELEASE_TAG       — versioned release name (defaults to YYYYmmdd-HHMMSS-<short-sha>)
#   SSH_KEY_PATH      — path to private SSH key (defaults to ssh agent)
#   APP_ENV           — production | staging (defaults to production)
#   KEEP_RELEASES     — how many old releases to retain on the server (default 5)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load .env if we have one and the env vars aren't already set (CI sets them directly).
if [ -z "${DEPLOY_HOST:-}" ] && [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST not set; export it or add to .env}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
APP_ENV="${APP_ENV:-production}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"

# Staging deploys to a separate directory so production and staging coexist.
if [ "$APP_ENV" = "staging" ]; then
    REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/var/www/glintstone-staging}"
else
    REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/var/www/glintstone}"
fi

# Generate a release tag if none provided.
if [ -z "${RELEASE_TAG:-}" ]; then
    short_sha="$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo nogit)"
    RELEASE_TAG="$(date -u +%Y%m%d-%H%M%S)-${short_sha}"
fi

RELEASES_DIR="$REMOTE_DIR/releases"
RELEASE_DIR="$RELEASES_DIR/$RELEASE_TAG"
CURRENT_LINK="$REMOTE_DIR/current"
SHARED_DIR="$REMOTE_DIR/shared"

REMOTE="$DEPLOY_USER@$DEPLOY_HOST"

# SSH options — pin known_hosts location, use deploy key if provided.
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=~/.ssh/known_hosts)
if [ -n "${SSH_KEY_PATH:-}" ]; then
    SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

ssh_run() { ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"; }
rsync_to() { rsync -avz --delete -e "ssh ${SSH_OPTS[*]}" "$@"; }

# --- Parse deploy targets (and the optional --force-no-snapshot flag) ---
TARGETS=("$@")
deploy_api=false; deploy_app=false; deploy_www=false; deploy_mcp=false
force_no_snapshot=false
KEPT_TARGETS=()
for target in "${TARGETS[@]}"; do
    case "$target" in
        api) deploy_api=true; KEPT_TARGETS+=("$target") ;;
        app) deploy_app=true; KEPT_TARGETS+=("$target") ;;
        www) deploy_www=true; KEPT_TARGETS+=("$target") ;;
        mcp) deploy_mcp=true; KEPT_TARGETS+=("$target") ;;
        --force-no-snapshot) force_no_snapshot=true ;;
        *) echo "Unknown target: $target (use: api, app, www, mcp)" >&2; exit 1 ;;
    esac
done
# Re-derive the target list without the flag tokens, defaulting to the full set.
if [ ${#KEPT_TARGETS[@]} -eq 0 ]; then
    TARGETS=(api app www)
    deploy_api=true; deploy_app=true; deploy_www=true
else
    TARGETS=("${KEPT_TARGETS[@]}")
fi

# --- Guard: a real deploy MUST run against a known environment label ---
# DEPLOY_HOST is always set by this point (the :? check above), i.e. this is a
# real deploy that writes to the production/staging release dir and restarts
# prod services. The pre-deploy pg_dump snapshot is gated on APP_ENV; if APP_ENV
# is something other than production/staging (e.g. a laptop .env with
# APP_ENV=local), the snapshot is silently skipped while the deploy still hits
# production. Refuse to proceed unless the operator explicitly opts out.
if [ "$APP_ENV" != "production" ] && [ "$APP_ENV" != "staging" ]; then
    if $force_no_snapshot; then
        echo "::warning::APP_ENV='$APP_ENV' is not production/staging — proceeding"
        echo "::warning::WITHOUT a pre-deploy DB snapshot (--force-no-snapshot given)."
    else
        cat >&2 <<EOF
============================================================================
ABORTING DEPLOY — unsafe environment label
============================================================================
  APP_ENV     = '$APP_ENV'  (expected 'production' or 'staging')
  DEPLOY_HOST = '$DEPLOY_HOST'
  REMOTE_DIR  = '$REMOTE_DIR'

This is a real deploy: it writes to the release dir above and restarts
production services. But the pre-deploy pg_dump snapshot is only taken when
APP_ENV is 'production' or 'staging'. With APP_ENV='$APP_ENV' the snapshot would
be SKIPPED — running migrations against production with no backup.

This usually means you deployed from a laptop whose .env has APP_ENV=local.

Fix one of:
  • Set APP_ENV=production (or staging) for this deploy:
        APP_ENV=production ./ops/deploy/deploy.sh ${TARGETS[*]}
  • If you genuinely want to skip the snapshot, pass --force-no-snapshot:
        APP_ENV=$APP_ENV ./ops/deploy/deploy.sh ${TARGETS[*]} --force-no-snapshot
============================================================================
EOF
        exit 1
    fi
fi

echo "=== Glintstone deploy ==="
echo "  Host:        $REMOTE"
echo "  Environment: $APP_ENV"
echo "  Release:     $RELEASE_TAG"
echo "  Targets:     ${TARGETS[*]}"
echo

# --- Prepare release directory on the server ---
ssh_run "mkdir -p $RELEASE_DIR $SHARED_DIR"

# Exclusions: anything not needed at runtime.
EXCLUDES=(
    --exclude='.git'
    --exclude='.github'
    --exclude='.env'
    --exclude='.env.*'
    --exclude='.pids'
    --exclude='venv'
    --exclude='__pycache__'
    --exclude='.pytest_cache'
    --exclude='.mypy_cache'
    --exclude='.ruff_cache'
    --exclude='app-v0.1'
    --exclude='_archive'
    --exclude='_progress'
    --exclude='data'
    --exclude='RESEARCH'
    --exclude='PLAN'
    --exclude='PLANNING'
    --exclude='PRDs'
    --exclude='data-model/v1'
    --exclude='data-model/source-schemas'
    --exclude='source-data'
    --exclude='ml'
    --exclude='.DS_Store'
    --exclude='.claude'
    --exclude='*.log'
    --exclude='TODO.md'
    --exclude='tests'
    --exclude='glintstone.code-workspace'
    --exclude='ops/local'
)

# --- Always sync shared core + dependencies into the release ---
echo "Syncing core/, requirements.txt, data-model/, ingestion/..."
for d in core api app ingestion data-model www ops scripts mcp; do
    [ -d "$PROJECT_DIR/$d" ] || continue
    rsync_to "${EXCLUDES[@]}" "$PROJECT_DIR/$d/" "$REMOTE:$RELEASE_DIR/$d/" >/dev/null
done
# Migrations ship as part of data-model/ (already synced above).
rsync_to "$PROJECT_DIR/requirements.txt" "$REMOTE:$RELEASE_DIR/requirements.txt" >/dev/null

# The agentic summary/interpretation agents load their prompt templates at runtime
# from <release>/.claude/skills/gs-expert-agentic/prompts/ (core/agent/synthesis.py
# resolves the path relative to the release root). The broader .claude/ skill tree is
# dev-only and stays excluded above — but these prompt files are production runtime data.
echo "Syncing agentic prompt templates..."
ssh_run "mkdir -p $RELEASE_DIR/.claude/skills/gs-expert-agentic/prompts"
rsync_to "$PROJECT_DIR/.claude/skills/gs-expert-agentic/prompts/" \
    "$REMOTE:$RELEASE_DIR/.claude/skills/gs-expert-agentic/prompts/" >/dev/null

# --- Install dependencies inside the release's venv ---
echo "Installing dependencies into release venv..."
ssh_run "cd $RELEASE_DIR && python3 -m venv venv && venv/bin/pip install --quiet --upgrade pip && venv/bin/pip install --quiet -r requirements.txt"

# --- Symlink shared state (the .env stays out of releases for safety) ---
ssh_run "ln -sfn $SHARED_DIR/.env $RELEASE_DIR/.env"

# --- Symlink shared source-data (ORACC/CDLI bulk downloads persist across releases) ---
ssh_run "mkdir -p $SHARED_DIR/source-data && ln -sfn $SHARED_DIR/source-data $RELEASE_DIR/source-data"

# --- Verify the new venv actually imports the app code ---
# Catches dependency drift, syntax errors, and missing-module bugs BEFORE migrations
# run and BEFORE the symlink swap. If this fails the previous release stays live.
echo "Verifying release imports..."
ssh_run "cd $RELEASE_DIR && set -a && . ./.env && set +a && \
    venv/bin/python -c 'import api.main; import app.main; import core.version; print(\"imports ok:\", core.version.release_tag())'"

# --- Pre-deploy DB snapshot (production only — staging restores from prod nightly) ---
# A failed OR timed-out pg_dump aborts the deploy: deploying without a complete
# backup right before a migration is the risk profile we're eliminating. The
# wait below is bounded AND fails hard — it must never fall through to migrations
# with a partial dump on disk (see the #7 deploy-hang post-mortem, 2026-06-20).
if [ "$APP_ENV" = "production" ]; then
    SNAPSHOT_NAME="pre-deploy-$RELEASE_TAG.dump"

    # --- Pre-flight: make room and verify the dump can fit ---
    # The dump is written to the same filesystem as everything else. A 19 GB DB
    # produces a ~6 GB -Fc dump; with the disk at ~91% used this can fail
    # mid-write (leaving a truncated "backup"). Rotate OLD dumps BEFORE the new
    # one runs (we previously trimmed afterward, so peak usage held 4 dumps at
    # once), then refuse to start if free space is implausibly low.
    echo "Rotating old snapshots before dump (keep newest 2)..."
    ssh_run "cd $SHARED_DIR/backups && ls -1t pre-deploy-*.dump 2>/dev/null | tail -n +3 | xargs -r rm -f; \
             rm -f pre-deploy-*.dump.done 2>/dev/null || true"
    AVAIL_KB=$(ssh_run "df -P $SHARED_DIR/backups | awk 'NR==2{print \$4}'")
    MIN_FREE_KB=$((10 * 1024 * 1024))   # require ~10 GB headroom for the dump
    if [ "${AVAIL_KB:-0}" -lt "$MIN_FREE_KB" ]; then
        echo "::error::Only ${AVAIL_KB}KB free on the backups volume — need ~${MIN_FREE_KB}KB."
        echo "::error::Refusing to start pg_dump (a truncated backup is worse than no deploy)."
        echo "::error::Free space on the VPS or move backups off-box, then re-run."
        exit 1
    fi

    echo "Snapshotting production DB → $SNAPSHOT_NAME (background, polling for completion)..."
    # Run pg_dump in the background on the server so the SSH session doesn't need
    # to stay open for the full dump. Poll with short reconnects instead.
    # -Fc (custom format) compresses internally — do not pipe through gzip.
    ssh_run "set -a && . $SHARED_DIR/.env && set +a && \
        mkdir -p $SHARED_DIR/backups && \
        nohup bash -c 'pg_dump -Fc \"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" \
            > $SHARED_DIR/backups/$SNAPSHOT_NAME \
            && echo done > $SHARED_DIR/backups/$SNAPSHOT_NAME.done \
            || echo failed > $SHARED_DIR/backups/$SNAPSHOT_NAME.done' \
            > /tmp/pg_dump_deploy.log 2>&1 &"

    # --- Bounded wait with a HARD failure on timeout ---
    # The DB grows over time; the previous 10-min budget was already being
    # blown by a ~12-min dump (19 GB DB → ~6 GB -Fc). When the loop ran out it
    # silently FELL THROUGH and ran migrations against prod with only a
    # partial backup on disk. That is the exact failure we are eliminating:
    # a slow dump must ABORT, not proceed. Budget = 30 min, with a timestamped
    # progress line every minute so a future stall is diagnosable from the log.
    SNAPSHOT_MAX_MIN="${SNAPSHOT_MAX_MIN:-30}"
    snapshot_done=false
    echo "  Waiting for pg_dump (timeout ${SNAPSHOT_MAX_MIN}m)..."
    for _ in $(seq 1 "$SNAPSHOT_MAX_MIN"); do
        for _ in $(seq 1 6); do        # 6 × 10s = 1 min between progress lines
            sleep 10
            STATUS=$(ssh_run "cat $SHARED_DIR/backups/$SNAPSHOT_NAME.done 2>/dev/null || echo pending")
            if [ "$STATUS" = "done" ]; then
                snapshot_done=true; break 2
            elif [ "$STATUS" = "failed" ]; then
                echo "  pg_dump FAILED — see /tmp/pg_dump_deploy.log on the VPS"
                ssh_run "rm -f $SHARED_DIR/backups/$SNAPSHOT_NAME.done"
                echo "::error::Pre-deploy DB snapshot failed — aborting deploy (no migrations run)"
                exit 1
            fi
        done
        SZ=$(ssh_run "du -h $SHARED_DIR/backups/$SNAPSHOT_NAME 2>/dev/null | cut -f1 || echo 0")
        echo "  [$(date -u +%H:%M:%S)] pg_dump still running (dump size: ${SZ})..."
    done

    if ! $snapshot_done; then
        echo "::error::pg_dump did not finish within ${SNAPSHOT_MAX_MIN} min — aborting deploy."
        echo "::error::The previous release stays live; NO migrations were run."
        echo "::error::The background pg_dump may still be running on the VPS; check"
        echo "::error::/tmp/pg_dump_deploy.log and $SHARED_DIR/backups/. If the DB has"
        echo "::error::simply outgrown the window, raise SNAPSHOT_MAX_MIN and re-run."
        ssh_run "rm -f $SHARED_DIR/backups/$SNAPSHOT_NAME.done" || true
        exit 1
    fi
    echo "  pg_dump done."
    ssh_run "rm -f $SHARED_DIR/backups/$SNAPSHOT_NAME.done"
fi

# --- Run migrations against the target database ---
# Tables are owned by `wittkensis` (per CLAUDE.md); the app connects as `glintstone`
# which lacks CREATE on `public`. The shared .env must define DATABASE_URL_MIGRATIONS
# (the owning role); we fall back to DATABASE_URL for environments that don't separate.
echo "Running migrations..."
ssh_run "cd $RELEASE_DIR && set -a && . ./.env && set +a && \
    DATABASE_URL=\"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" venv/bin/python data-model/migrate.py up"

# --- Write version file for cache-busting and build identification ---
ssh_run "echo '$RELEASE_TAG' > $RELEASE_DIR/version.txt"

# --- Capture the previous release so we can roll back on smoke-test failure ---
PREV_RELEASE="$(ssh_run "readlink $CURRENT_LINK 2>/dev/null || echo none")"
echo "Previous release: $PREV_RELEASE"

# --- Swap the `current` symlink atomically ---
echo "Swapping current → $RELEASE_TAG..."
ssh_run "ln -sfn $RELEASE_DIR $CURRENT_LINK.new && mv -Tf $CURRENT_LINK.new $CURRENT_LINK"

# --- Restart services + install nginx configs ---
if [ "$APP_ENV" = "staging" ]; then
    API_SVC="glintstone-staging-api"
    WEB_SVC="glintstone-staging-web"
    API_PORT=8003
    WEB_PORT=8004
else
    API_SVC="glintstone-api"
    WEB_SVC="glintstone-web"
    API_PORT=8001
    WEB_PORT=8002
fi

NGINX_CONF_DIR="/etc/nginx/http.d"
nginx_reload_needed=false

# Shared http-context directives (rate-limit zones + geo) — install once on
# every deploy that touches any nginx config. Snippets directory carries
# include-only fragments (security headers).
if $deploy_api || $deploy_app || $deploy_mcp || $deploy_www; then
    ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/00-shared.conf $NGINX_CONF_DIR/00-shared.conf"
    ssh_run "sudo mkdir -p $NGINX_CONF_DIR/snippets && sudo cp $RELEASE_DIR/ops/deploy/nginx/snippets/security-headers.conf $NGINX_CONF_DIR/snippets/security-headers.conf"
    echo "  00-shared.conf + snippets/security-headers.conf installed"
    nginx_reload_needed=true
fi

if $deploy_api; then
    ssh_run "sudo supervisorctl restart $API_SVC" || true
    echo "  $API_SVC restarted"
    if [ "$APP_ENV" != "staging" ]; then
        ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/api.glintstone.org.conf $NGINX_CONF_DIR/api.glintstone.org.conf"
        echo "  api.glintstone.org.conf installed"
        nginx_reload_needed=true
    fi
fi

if $deploy_app; then
    ssh_run "sudo supervisorctl restart $WEB_SVC" || true
    echo "  $WEB_SVC restarted"
    if [ "$APP_ENV" != "staging" ]; then
        ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/app.glintstone.org.conf $NGINX_CONF_DIR/app.glintstone.org.conf"
        echo "  app.glintstone.org.conf installed"
    fi
    nginx_reload_needed=true
fi

# Staging's single nginx config covers both staging api + app. Install it on
# either target so an api-only deploy doesn't skip the config refresh.
if [ "$APP_ENV" = "staging" ] && ( $deploy_api || $deploy_app ); then
    ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/staging.glintstone.org.conf $NGINX_CONF_DIR/staging.glintstone.org.conf"
    echo "  staging.glintstone.org.conf installed"
    nginx_reload_needed=true
fi

if $deploy_mcp; then
    ssh_run "sudo supervisorctl restart glintstone-mcp" || true
    echo "  glintstone-mcp restarted"
    if [ "$APP_ENV" != "staging" ]; then
        ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/mcp.glintstone.org.conf $NGINX_CONF_DIR/mcp.glintstone.org.conf"
        echo "  mcp.glintstone.org.conf installed"
        nginx_reload_needed=true
    fi
fi

if $deploy_www; then
    # Nginx serves glintstone.org from shared/www/ (persists across releases).
    # Migrate from old shared/marketing/ path on first deploy after rename.
    ssh_run "[ -d $SHARED_DIR/marketing ] && mv $SHARED_DIR/marketing $SHARED_DIR/www || true"
    echo "Syncing www/ → shared/www/..."
    rsync_to --exclude='.DS_Store' "$PROJECT_DIR/www/" "$REMOTE:$SHARED_DIR/www/"
    ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/glintstone.org.conf $NGINX_CONF_DIR/glintstone.org.conf"
    echo "  glintstone.org.conf installed"
    ssh_run "sudo cp $RELEASE_DIR/ops/deploy/nginx/assets.glintstone.org.conf $NGINX_CONF_DIR/assets.glintstone.org.conf"
    ssh_run "sudo mkdir -p /var/cache/nginx/r2 && sudo chown nginx:nginx /var/cache/nginx/r2 2>/dev/null || true"
    echo "  assets.glintstone.org.conf installed"
    nginx_reload_needed=true
fi

if $nginx_reload_needed; then
    echo "Validating and reloading nginx..."
    # Validate before reload — a bad config that fails -t will abort the deploy
    # rather than silently leave the previous config running while reporting success.
    # Sudoers entry: deploy ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t (see provision.sh).
    ssh_run "sudo nginx -t && (sudo rc-service nginx reload 2>/dev/null || sudo nginx -s reload)"
    echo "  nginx reloaded"
fi

# --- Post-deploy smoke test ---
# Poll local ports for healthy responses. Auto-roll-back to PREV_RELEASE on failure.
# IMPORTANT: rollback only swaps the *code* symlink — migrations are not reversed.
# This is safe for additive migrations only; if a migration is destructive, the
# pre-deploy DB snapshot (above) is the recovery path.
smoke_failed=false
if $deploy_api || $deploy_app || $deploy_mcp; then
    echo "Smoke-testing release..."
    SMOKE_CMD=""
    if $deploy_api; then
        SMOKE_CMD="$SMOKE_CMD curl -fsS --max-time 5 http://127.0.0.1:$API_PORT/health >/dev/null &&"
    fi
    if $deploy_app; then
        SMOKE_CMD="$SMOKE_CMD curl -fsS --max-time 5 http://127.0.0.1:$WEB_PORT/healthz >/dev/null &&"
    fi
    if $deploy_mcp; then
        SMOKE_CMD="$SMOKE_CMD curl -fsS --max-time 5 http://127.0.0.1:8005/healthz >/dev/null &&"
    fi
    SMOKE_CMD="${SMOKE_CMD% &&} && echo SMOKE_OK"
    # Up to 20 attempts × 1.5s = 30s budget.
    if ! ssh_run "for i in \$(seq 1 20); do
            if $SMOKE_CMD 2>/dev/null; then exit 0; fi
            sleep 1.5
        done
        exit 1"; then
        smoke_failed=true
    fi
fi

if $smoke_failed; then
    echo "::error::Smoke test failed — rolling back to $PREV_RELEASE"
    if [ "$PREV_RELEASE" != "none" ] && [ -n "$PREV_RELEASE" ]; then
        ssh_run "ln -sfn $PREV_RELEASE $CURRENT_LINK.new && mv -Tf $CURRENT_LINK.new $CURRENT_LINK"
        $deploy_api && ssh_run "sudo supervisorctl restart $API_SVC" || true
        $deploy_app && ssh_run "sudo supervisorctl restart $WEB_SVC" || true
        $deploy_mcp && ssh_run "sudo supervisorctl restart glintstone-mcp" || true
        echo "Rolled back. Current is now: $PREV_RELEASE"
    else
        echo "::warning::No previous release recorded; cannot auto-roll-back"
    fi
    exit 1
fi

# --- Trim old releases ---
ssh_run "cd $RELEASES_DIR && ls -1t | tail -n +$((KEEP_RELEASES + 1)) | xargs -r rm -rf"

echo
echo "=== Deploy complete ==="
echo "  Release:  $RELEASE_TAG"
echo "  Previous: $PREV_RELEASE"
echo "  Rollback: ops/deploy/rollback.sh $PREV_RELEASE"
