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
#
# Keepalive + timeout matter here. Every `ssh_run` below opens a fresh SSH
# connection, and the pg_dump poll loop opens dozens of them in a row from the
# GitHub Actions runner. Without these, a single half-open TCP connection (the
# runner sits behind NAT; the VPS may drop an idle/established-but-silent socket)
# makes `ssh` block FOREVER with no error — the exact "Deploy to Hostinger hangs
# post-rsync, no progress" symptom from the 2026-06-21 incident. With these, a
# stalled connection fails in ~30s with a clear error instead of pinning the job
# until the workflow's timeout-minutes kills it 10+ minutes later.
#   ConnectTimeout=15        — give up establishing a connection after 15s
#   ServerAliveInterval=15   — probe the peer every 15s on an open session
#   ServerAliveCountMax=4    — drop the session after 4 missed probes (~60s)
#   BatchMode=yes            — NEVER prompt for a password/passphrase. Over a
#                              non-TTY CI SSH a prompt would hang waiting on
#                              stdin that never comes; fail fast instead.
SSH_OPTS=(
    -o StrictHostKeyChecking=accept-new
    -o UserKnownHostsFile=~/.ssh/known_hosts
    -o BatchMode=yes
    -o ConnectTimeout=15
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=4
)
if [ -n "${SSH_KEY_PATH:-}" ]; then
    SSH_OPTS+=(-i "$SSH_KEY_PATH")
fi

# --- Connection-level retry wrapper (#437) -----------------------------------
# The GitHub-runner → VPS SSH connect has intermittently timed out at the TCP
# layer (~6 deploys needed a manual re-run). The keyscan step already retries;
# this wraps the deploy SSH/rsync legs themselves.
#
# CRITICAL safety property: we retry ONLY on a connection-level failure, never
# on a remote command's own non-zero exit. ssh returns 255 when *it* fails to
# connect/authenticate; rsync returns 255 when its transport (ssh) fails, or
# 30/35 on transport timeouts. Any other non-zero is the remote command (or a
# real rsync data error) reporting failure — that is a genuine result and must
# propagate unretried, so we never re-run a command that already executed (which
# could double-apply a non-idempotent step). stdout/stderr and the final exit
# code are passed through unchanged, so command-substitution callers still work.
#
# Tunables (env-overridable so CI or an operator can dial them):
#   SSH_RETRY_ATTEMPTS   total attempts including the first (default 4)
#   SSH_RETRY_BASE_DELAY first backoff in seconds, doubled each retry (default 5)
SSH_RETRY_ATTEMPTS="${SSH_RETRY_ATTEMPTS:-4}"
SSH_RETRY_BASE_DELAY="${SSH_RETRY_BASE_DELAY:-5}"

# Exit codes that mean "the connection/transport failed before/around the
# command" and are therefore safe to retry.
_ssh_retryable_code() {
    case "$1" in
        255) return 0 ;;  # ssh: connection/auth failure
        30|35) return 0 ;;  # rsync: timeout in data send/receive or I/O timeout
        *) return 1 ;;
    esac
}

# Run "$@" with connection-level retries. Used by ssh_run / rsync_to.
with_ssh_retry() {
    local attempt=1 delay="$SSH_RETRY_BASE_DELAY" code
    while :; do
        "$@" && return 0
        code=$?
        if _ssh_retryable_code "$code" && [ "$attempt" -lt "$SSH_RETRY_ATTEMPTS" ]; then
            echo "  ⚠ connection failed (exit $code), attempt $attempt/$SSH_RETRY_ATTEMPTS — retrying in ${delay}s..." >&2
            sleep "$delay"
            attempt=$((attempt + 1))
            delay=$((delay * 2))
            continue
        fi
        # Either a non-retryable (real command) failure, or attempts exhausted:
        # surface the true exit code without further retries.
        return "$code"
    done
}

_ssh_run_once() { ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"; }
_rsync_to_once() { rsync -avz --delete -e "ssh ${SSH_OPTS[*]}" "$@"; }

ssh_run() { with_ssh_retry _ssh_run_once "$@"; }
rsync_to() { with_ssh_retry _rsync_to_once "$@"; }

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
# Bound with a remote `timeout` (busybox `timeout` is present on the VPS): a
# wedged pip resolver or a stalled PyPI fetch must fail this step in ~8 min, not
# hang the whole deploy. The SSH keepalive above only catches a dead *connection*
# — it can't tell a live-but-stuck remote command from a slow one, so the remote
# `timeout` is the backstop for that case.
echo "[$(date -u +%H:%M:%S)] Installing dependencies into release venv (timeout 8m)..."
ssh_run "timeout 480 sh -c 'cd $RELEASE_DIR && python3 -m venv venv && venv/bin/pip install --quiet --upgrade pip && venv/bin/pip install --quiet -r requirements.txt'" || {
    echo "::error::Dependency install failed or exceeded 8 min — aborting (previous release stays live)."
    exit 1
}

# --- Symlink shared state (the .env stays out of releases for safety) ---
ssh_run "ln -sfn $SHARED_DIR/.env $RELEASE_DIR/.env"

# --- Symlink shared source-data (ORACC/CDLI bulk downloads persist across releases) ---
ssh_run "mkdir -p $SHARED_DIR/source-data && ln -sfn $SHARED_DIR/source-data $RELEASE_DIR/source-data"

# --- Verify the new venv actually imports the app code ---
# Catches dependency drift, syntax errors, and missing-module bugs BEFORE migrations
# run and BEFORE the symlink swap. If this fails the previous release stays live.
echo "[$(date -u +%H:%M:%S)] Verifying release imports (timeout 2m)..."
ssh_run "timeout 120 sh -c 'cd $RELEASE_DIR && set -a && . ./.env && set +a && \
    venv/bin/python -c \"import api.main; import app.main; import core.version; print(\\\"imports ok:\\\", core.version.release_tag())\"'" || {
    echo "::error::Import verification failed or timed out — aborting (previous release stays live)."
    exit 1
}

# --- Decide whether this deploy needs a pre-deploy DB snapshot (#219 / #272) ---
# The full pg_dump of the ~22 GB prod DB is the single biggest phase of a deploy
# (~18 min) and it gates EVERY deploy — including code-only deploys that touch no
# data at all. A code-only deploy can never change the database, so the previous
# release is already a perfectly good rollback point and a fresh dump buys nothing.
#
# We take the dump ONLY when this release actually has a database migration to run.
# Detection is delegated to the migration runner itself — the SAME `migrate.py`
# that the migrations step below will execute — via its `status` command, which
# compares the migration files shipped in THIS release against the `_migrations`
# tracking table in the live DB and prints `Applied: N` for the count already
# applied out of the total found. If "found" > "applied" there is at least one
# pending migration, so the DB MAY change and we MUST back up first. If they are
# equal, `migrate.py up` below would be a no-op and the data cannot change, so the
# dump is safely skipped. Using the runner's own view (not a git diff) means the
# skip decision can never disagree with what actually runs.
#
# FAIL-SAFE: any uncertainty defaults to TAKING the dump. If `migrate.py status`
# errors, times out, or its output can't be parsed into two clean numbers, we set
# migrations_pending=true and back up. A needless dump costs ~18 min; a skipped
# backup before a real migration risks the data — so the safe default is to dump.
migrations_pending=true   # fail-safe default: back up unless we PROVE it's unneeded
if [ "$APP_ENV" = "production" ]; then
    echo "[$(date -u +%H:%M:%S)] Checking for pending migrations (timeout 1m)..."
    # `migrate.py status` prints lines like:
    #   Found 53 migrations in /.../migrations
    #   Applied: 53
    # We extract the two integers and compare. Anything unexpected -> stay safe.
    MIG_STATUS="$(ssh_run "timeout 60 sh -c 'cd $RELEASE_DIR && set -a && . ./.env && set +a && \
        DATABASE_URL=\"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" venv/bin/python data-model/migrate.py status'" 2>/dev/null)" || MIG_STATUS=""
    found_count="$(printf '%s\n' "$MIG_STATUS" | sed -n 's/^Found \([0-9]\{1,\}\) migrations.*/\1/p' | head -1)"
    applied_count="$(printf '%s\n' "$MIG_STATUS" | sed -n 's/^Applied: \([0-9]\{1,\}\).*/\1/p' | head -1)"
    if [ -n "$found_count" ] && [ -n "$applied_count" ]; then
        if [ "$found_count" -le "$applied_count" ]; then
            migrations_pending=false
            echo "  No pending migrations ($applied_count/$found_count applied) — DB cannot change."
            echo "  SKIPPING the pre-deploy pg_dump (code-only deploy; previous release is the rollback)."
        else
            echo "  $((found_count - applied_count)) pending migration(s) ($applied_count/$found_count applied) — will snapshot the DB first."
        fi
    else
        echo "::warning::Could not parse migrate.py status output — defaulting to TAKING a backup (fail-safe)."
        echo "::warning::status output was: ${MIG_STATUS:-<empty / command failed>}"
    fi
fi

# --- Pre-deploy DB snapshot (production only — staging restores from prod nightly) ---
# A failed OR timed-out pg_dump aborts the deploy: deploying without a complete
# backup right before a migration is the risk profile we're eliminating. The
# wait below is bounded AND fails hard — it must never fall through to migrations
# with a partial dump on disk (see the #7 deploy-hang post-mortem, 2026-06-20).
if [ "$APP_ENV" = "production" ] && $migrations_pending; then
    # Directory-format dump (a directory of per-table files), NOT a single file.
    # Suffix `.dumpdir` so the rotation glob and restore command can tell the new
    # parallel dumps apart from any legacy single-file `.dump` left on the box.
    SNAPSHOT_NAME="pre-deploy-$RELEASE_TAG.dumpdir"
    # Parallelism for the dump (#272). The prod box has several cores and the dump
    # is I/O+CPU bound on a single connection with -Fc; -Fd -j N runs N worker
    # connections in parallel and cuts wall-clock roughly N-fold. 4 is a safe
    # default that leaves headroom for the live API/web workers also hitting PG.
    DUMP_JOBS="${DUMP_JOBS:-4}"

    # --- Pre-flight: make room and verify the dump can fit ---
    # The dump is written to the same filesystem as everything else. A ~22 GB DB
    # produces a ~6 GB compressed dump; with the disk tight this can fail mid-write
    # (leaving a truncated "backup"). Rotate OLD dumps BEFORE the new one runs,
    # then refuse to start if free space is implausibly low. Covers both the new
    # `.dumpdir` directories and any legacy single-file `.dump` snapshots.
    echo "Rotating old snapshots before dump (keep newest 2)..."
    ssh_run "cd $SHARED_DIR/backups 2>/dev/null && \
             ls -1dt pre-deploy-*.dumpdir pre-deploy-*.dump 2>/dev/null | tail -n +3 | xargs -r rm -rf; \
             rm -f pre-deploy-*.done 2>/dev/null || true"
    AVAIL_KB=$(ssh_run "df -P $SHARED_DIR/backups | awk 'NR==2{print \$4}'")
    MIN_FREE_KB=$((10 * 1024 * 1024))   # require ~10 GB headroom for the dump
    if [ "${AVAIL_KB:-0}" -lt "$MIN_FREE_KB" ]; then
        echo "::error::Only ${AVAIL_KB}KB free on the backups volume — need ~${MIN_FREE_KB}KB."
        echo "::error::Refusing to start pg_dump (a truncated backup is worse than no deploy)."
        echo "::error::Free space on the VPS or move backups off-box, then re-run."
        exit 1
    fi

    # NOTE: this is the longest phase of the deploy, but it only runs on a deploy
    # that ships a migration now (code-only deploys skipped the whole block above).
    # With -Fd -j $DUMP_JOBS the ~22 GB DB dumps in roughly a quarter of the old
    # ~18 min single-stream time. The progress lines below tick every ~60s WITH a
    # dump size so the step is visibly alive; do NOT mistake a slow-but-progressing
    # dump for a hang and cancel it (that was the 2026-06-21 misdiagnosis). The
    # deploy job's workflow timeout-minutes must comfortably exceed dump + rsync +
    # migrations.
    #
    # RESTORE (directory format): use pg_restore, NOT psql. Parallel restore too:
    #   pg_restore -j 4 --clean --if-exists -d "$DATABASE_URL_MIGRATIONS" \
    #       /var/www/glintstone/shared/backups/pre-deploy-<RELEASE_TAG>.dumpdir
    # (Drop --clean/--if-exists to restore into a fresh/empty database instead.)
    echo "[$(date -u +%H:%M:%S)] Snapshotting production DB → $SNAPSHOT_NAME (-Fd -j $DUMP_JOBS)"
    echo "  (background parallel dump; ~5 min expected for a ~22 GB DB; polling below)..."
    # Run pg_dump in the background on the server so the SSH session doesn't need
    # to stay open for the full dump. Poll with short reconnects instead.
    # -Fd writes a directory of internally-compressed files; -j runs N in parallel.
    # The directory must not pre-exist (pg_dump -Fd refuses a non-empty target), so
    # clear any stale same-named dir from a prior aborted run first.
    ssh_run "set -a && . $SHARED_DIR/.env && set +a && \
        mkdir -p $SHARED_DIR/backups && rm -rf $SHARED_DIR/backups/$SNAPSHOT_NAME && \
        nohup bash -c 'pg_dump -Fd -j $DUMP_JOBS -Z 1 \
            -f $SHARED_DIR/backups/$SNAPSHOT_NAME \
            \"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" \
            && echo done > $SHARED_DIR/backups/$SNAPSHOT_NAME.done \
            || echo failed > $SHARED_DIR/backups/$SNAPSHOT_NAME.done' \
            > /tmp/pg_dump_deploy.log 2>&1 &"

    # --- Bounded wait with a HARD failure on timeout ---
    # A slow dump must ABORT, not silently fall through and run migrations against
    # prod with only a partial backup on disk (the failure we are eliminating).
    # The parallel -Fd dump is much faster than the old single-stream -Fc, but we
    # keep a generous 30-min budget so a transiently-loaded box doesn't false-fail;
    # a timestamped progress line every minute keeps a future stall diagnosable.
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
# Bound with a remote `timeout`: a migration that blocks on a table lock (e.g. a
# long-running query holding the table) would otherwise hang the deploy with no
# progress. 10 min is generous for the additive migrations we ship; if a
# migration legitimately needs longer it should be run out-of-band, not inline.
echo "[$(date -u +%H:%M:%S)] Running migrations (timeout 10m)..."
ssh_run "timeout 600 sh -c 'cd $RELEASE_DIR && set -a && . ./.env && set +a && \
    DATABASE_URL=\"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" venv/bin/python data-model/migrate.py up'" || {
    echo "::error::Migrations failed or exceeded 10 min — aborting deploy."
    echo "::error::The current symlink was NOT swapped; the previous release stays live."
    echo "::error::A timeout here usually means a migration is waiting on a DB lock —"
    echo "::error::check pg_stat_activity on the VPS for a blocking query."
    exit 1
}

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
# Pure housekeeping — it runs AFTER the symlink swap and a passing smoke test, so
# the new release is already live and healthy. A hiccup here must NEVER fail the
# deploy. Old releases can contain root-owned __pycache__/*.pyc (bytecode written
# while prod services run as root), which the `deploy` user can't rm; `xargs` then
# returns 123 and, under `set -e`, that previously failed the WHOLE deploy job
# even though everything that matters already succeeded (the false-failure that
# surfaced on the 2026-06-21 CI deploy once the run finally reached this step).
# Make it best-effort: `rm -f` swallows per-file permission errors, and the whole
# block is guarded with `|| true` so trim can never flip a good deploy to failed.
#
# Durable fix (#271): the root-owned `.pyc` accumulate because prod services run
# as root and write bytecode into the release tree the `deploy` user owns. Before
# trimming, reclaim ownership of the releases directory to `deploy`, after which
# the trim's `rm -rf` succeeds outright instead of silently skipping root-owned
# files, so old releases are actually reclaimed rather than piling up.
#
# This needs a NARROW sudoers grant (the deploy user's default sudo is limited to
# supervisorctl/nginx). Installed at /etc/sudoers.d/deploy-trim on 2026-06-23:
#   deploy ALL=(root) NOPASSWD: /bin/chown -R deploy /var/www/glintstone/releases
#   deploy ALL=(root) NOPASSWD: /bin/chown -R deploy /var/www/glintstone-staging/releases
# The command path and args below MUST match that rule exactly (absolute
# /bin/chown, `-R deploy`, the literal releases path) or sudo rejects it. The
# chown is still guarded so a hiccup can't fail the (already-live) deploy.
echo "Reclaiming ownership of old releases for trim (best-effort)..."
ssh_run "sudo -n /bin/chown -R $DEPLOY_USER $RELEASES_DIR 2>/dev/null" \
    || echo "::warning::Could not chown releases dir (sudoers rule /etc/sudoers.d/deploy-trim missing or path mismatch) — trim falls back to best-effort rm."

echo "Trimming old releases (keep newest $KEEP_RELEASES; best-effort)..."
ssh_run "cd $RELEASES_DIR && ls -1t | tail -n +$((KEEP_RELEASES + 1)) | xargs -r rm -rf 2>/dev/null" \
    || echo "::warning::Old-release trim hit permission/other errors and was skipped — deploy is unaffected (release is live)."

echo
echo "=== Deploy complete ==="
echo "  Release:  $RELEASE_TAG"
echo "  Previous: $PREV_RELEASE"
echo "  Rollback: ops/deploy/rollback.sh $PREV_RELEASE"
