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
#   ./ops/deploy/deploy.sh app marketing        # web app + marketing site
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

# --- Parse deploy targets ---
TARGETS=("$@")
if [ ${#TARGETS[@]} -eq 0 ]; then
    TARGETS=(api app marketing)
fi
deploy_api=false; deploy_app=false; deploy_marketing=false
for target in "${TARGETS[@]}"; do
    case "$target" in
        api)       deploy_api=true ;;
        app)       deploy_app=true ;;
        marketing) deploy_marketing=true ;;
        *) echo "Unknown target: $target (use: api, app, marketing)" >&2; exit 1 ;;
    esac
done

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
    --exclude='source-data/sources'
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
for d in core api app ingestion data-model marketing ops; do
    [ -d "$PROJECT_DIR/$d" ] || continue
    rsync_to "${EXCLUDES[@]}" "$PROJECT_DIR/$d/" "$REMOTE:$RELEASE_DIR/$d/" >/dev/null
done
# Migrations live under source-data/migrations/ — ship only that subtree, not the
# (gitignored, multi-GB) source-data/sources/.
if [ -d "$PROJECT_DIR/source-data/migrations" ]; then
    ssh_run "mkdir -p $RELEASE_DIR/source-data"
    rsync_to "${EXCLUDES[@]}" "$PROJECT_DIR/source-data/migrations/" "$REMOTE:$RELEASE_DIR/source-data/migrations/" >/dev/null
fi
rsync_to "$PROJECT_DIR/requirements.txt" "$REMOTE:$RELEASE_DIR/requirements.txt" >/dev/null

# --- Install dependencies inside the release's venv ---
echo "Installing dependencies into release venv..."
ssh_run "cd $RELEASE_DIR && python3 -m venv venv && venv/bin/pip install --quiet --upgrade pip && venv/bin/pip install --quiet -r requirements.txt"

# --- Symlink shared state (the .env stays out of releases for safety) ---
ssh_run "ln -sfn $SHARED_DIR/.env $RELEASE_DIR/.env"

# --- Run migrations against the target database ---
# Tables are owned by `wittkensis` (per CLAUDE.md); the app connects as `glintstone`
# which lacks CREATE on `public`. The shared .env must define DATABASE_URL_MIGRATIONS
# (the owning role); we fall back to DATABASE_URL for environments that don't separate.
echo "Running migrations..."
ssh_run "cd $RELEASE_DIR && set -a && . ./.env && set +a && \
    DATABASE_URL=\"\${DATABASE_URL_MIGRATIONS:-\$DATABASE_URL}\" venv/bin/python data-model/migrate.py up"

# --- Write version file for cache-busting and build identification ---
ssh_run "echo '$RELEASE_TAG' > $RELEASE_DIR/version.txt"

# --- Swap the `current` symlink atomically ---
echo "Swapping current → $RELEASE_TAG..."
ssh_run "ln -sfn $RELEASE_DIR $CURRENT_LINK.new && mv -Tf $CURRENT_LINK.new $CURRENT_LINK"

# --- Restart services ---
if [ "$APP_ENV" = "staging" ]; then
    API_SVC="glintstone-staging-api"
    WEB_SVC="glintstone-staging-web"
else
    API_SVC="glintstone-api"
    WEB_SVC="glintstone-web"
fi

if $deploy_api; then
    ssh_run "sudo supervisorctl restart $API_SVC" || true
    echo "  $API_SVC restarted"
fi
if $deploy_app; then
    ssh_run "sudo supervisorctl restart $WEB_SVC" || true
    echo "  $WEB_SVC restarted"
fi
if $deploy_marketing; then
    ssh_run "sudo rc-service nginx reload" 2>/dev/null || true
    echo "  marketing/nginx reloaded"
fi

# --- Trim old releases ---
ssh_run "cd $RELEASES_DIR && ls -1t | tail -n +$((KEEP_RELEASES + 1)) | xargs -r rm -rf"

echo
echo "=== Deploy complete ==="
echo "  Release:  $RELEASE_TAG"
echo "  Rollback: ops/deploy/rollback.sh <previous-tag>"
