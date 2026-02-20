#!/bin/bash
# Glintstone v2 — Deploy to Production
# Syncs code, installs deps, runs migrations, restarts services.
#
# Usage:
#   ./ops/deploy/deploy.sh                  # deploy everything
#   ./ops/deploy/deploy.sh api              # deploy API only
#   ./ops/deploy/deploy.sh app              # deploy web app only
#   ./ops/deploy/deploy.sh marketing        # deploy marketing site only
#   ./ops/deploy/deploy.sh api app          # deploy API + web app
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REMOTE_DIR="/var/www/glintstone"

# Load deploy target from .env or default
if [ -f "$PROJECT_DIR/.env" ]; then
    DEPLOY_HOST=$(grep -E '^DEPLOY_HOST=' "$PROJECT_DIR/.env" | cut -d= -f2)
fi
REMOTE="deploy@${DEPLOY_HOST:-76.13.208.149}"

# Parse targets (default: all)
TARGETS=("$@")
if [ ${#TARGETS[@]} -eq 0 ]; then
    TARGETS=(api app marketing)
fi

deploy_api=false
deploy_app=false
deploy_marketing=false
for target in "${TARGETS[@]}"; do
    case "$target" in
        api)       deploy_api=true ;;
        app)       deploy_app=true ;;
        marketing) deploy_marketing=true ;;
        *)         echo "Unknown target: $target (use: api, app, marketing)"; exit 1 ;;
    esac
done

echo "=== Deploying Glintstone v2 to $REMOTE ==="
echo "  Targets: ${TARGETS[*]}"
echo ""

# --- Shared rsync excludes ---
EXCLUDES=(
    --exclude='.git'
    --exclude='.env'
    --exclude='.pids'
    --exclude='venv'
    --exclude='__pycache__'
    --exclude='app-v0.1'
    --exclude='_archive'
    --exclude='data'
    --exclude='RESEARCH'
    --exclude='data-model/v1'
    --exclude='data-model/v2'
    --exclude='data-model/source-schemas'
    --exclude='source-data'
    --exclude='ml'
    --exclude='.DS_Store'
    --exclude='.claude'
    --exclude='*.log'
    --exclude='TODO.md'
    --exclude='glintstone.code-workspace'
    --exclude='ops/local'
)

# --- Sync nginx configs first (needed before individual targets install them) ---
echo "Syncing nginx configs..."
ssh "$REMOTE" "mkdir -p $REMOTE_DIR/ops/deploy/nginx"
rsync -avz "$PROJECT_DIR/ops/deploy/nginx/" "$REMOTE:$REMOTE_DIR/ops/deploy/nginx/"

# --- Sync shared library (always, if deploying api or app) ---
if $deploy_api || $deploy_app; then
    echo "Syncing shared library (core/)..."
    rsync -avz "${EXCLUDES[@]}" \
        "$PROJECT_DIR/core/" "$REMOTE:$REMOTE_DIR/core/"
    rsync -avz "$PROJECT_DIR/requirements.txt" "$REMOTE:$REMOTE_DIR/requirements.txt"

    echo "Installing dependencies..."
    ssh "$REMOTE" "cd $REMOTE_DIR && venv/bin/pip install --quiet -r requirements.txt"

    echo "Running migrations..."
    rsync -avz "${EXCLUDES[@]}" \
        "$PROJECT_DIR/data-model/" "$REMOTE:$REMOTE_DIR/data-model/"
    ssh "$REMOTE" "cd $REMOTE_DIR && venv/bin/python data-model/migrate.py"
fi

# --- API ---
if $deploy_api; then
    echo ""
    echo "Deploying API..."
    rsync -avz "${EXCLUDES[@]}" \
        "$PROJECT_DIR/api/" "$REMOTE:$REMOTE_DIR/api/"

    ssh "$REMOTE" "
        if [ ! -f /etc/nginx/http.d/api.glintstone.org.conf ]; then
            sudo cp $REMOTE_DIR/ops/deploy/nginx/api.glintstone.org.conf /etc/nginx/http.d/
            echo '  Installed nginx config: api.glintstone.org'
        fi
    "

    ssh "$REMOTE" "sudo supervisorctl restart glintstone-api"
    echo "  API restarted"
fi

# --- Web App ---
if $deploy_app; then
    echo ""
    echo "Deploying web app..."
    rsync -avz "${EXCLUDES[@]}" \
        "$PROJECT_DIR/app/" "$REMOTE:$REMOTE_DIR/app/"

    ssh "$REMOTE" "
        if [ ! -f /etc/nginx/http.d/app.glintstone.org.conf ]; then
            sudo cp $REMOTE_DIR/ops/deploy/nginx/app.glintstone.org.conf /etc/nginx/http.d/
            echo '  Installed nginx config: app.glintstone.org'
        fi
    "

    ssh "$REMOTE" "sudo supervisorctl restart glintstone-web"
    echo "  Web app restarted"
fi

# --- Marketing ---
if $deploy_marketing; then
    echo ""
    echo "Deploying marketing site..."
    rsync -avz "${EXCLUDES[@]}" \
        "$PROJECT_DIR/marketing/" "$REMOTE:$REMOTE_DIR/marketing/"

    ssh "$REMOTE" "
        if [ ! -f /etc/nginx/http.d/glintstone.org.conf ]; then
            sudo cp $REMOTE_DIR/ops/deploy/nginx/glintstone.org.conf /etc/nginx/http.d/
            echo '  Installed nginx config: glintstone.org'
        fi
    "
    echo "  Marketing synced"
fi

# --- Reload nginx ---
ssh "$REMOTE" "sudo rc-service nginx reload" 2>/dev/null || true

echo ""
echo "=== Deploy complete ==="
$deploy_api       && echo "  API:       https://api.glintstone.org/health"
$deploy_app       && echo "  App:       https://app.glintstone.org"
$deploy_marketing && echo "  Marketing: https://glintstone.org"
