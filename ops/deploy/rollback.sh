#!/usr/bin/env bash
# Roll back to a previous release by swapping the `current` symlink.
#
# Usage:
#   ./ops/deploy/rollback.sh                  # list available releases
#   ./ops/deploy/rollback.sh <release-tag>    # roll back to that release

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "${DEPLOY_HOST:-}" ] && [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST not set}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
REMOTE_DIR="${DEPLOY_REMOTE_DIR:-/var/www/glintstone}"
REMOTE="$DEPLOY_USER@$DEPLOY_HOST"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new)
[ -n "${SSH_KEY_PATH:-}" ] && SSH_OPTS+=(-i "$SSH_KEY_PATH")

ssh_run() { ssh "${SSH_OPTS[@]}" "$REMOTE" "$@"; }

if [ $# -eq 0 ]; then
    echo "Available releases (newest first):"
    ssh_run "ls -1t $REMOTE_DIR/releases/"
    echo
    echo "Current:"
    ssh_run "readlink $REMOTE_DIR/current"
    exit 0
fi

TAG="$1"

if ! ssh_run "test -d $REMOTE_DIR/releases/$TAG"; then
    echo "Release not found on server: $TAG" >&2
    exit 1
fi

echo "Rolling back to $TAG..."
ssh_run "ln -sfn $REMOTE_DIR/releases/$TAG $REMOTE_DIR/current.new && mv -Tf $REMOTE_DIR/current.new $REMOTE_DIR/current"
ssh_run "sudo supervisorctl restart glintstone-api glintstone-web" || true
ssh_run "sudo rc-service nginx reload" 2>/dev/null || true

echo "Rolled back. Current is now: $TAG"
