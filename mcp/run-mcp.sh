#!/usr/bin/env bash
# Glintstone MCP stdio launcher — self-healing entry point.
#
# WHY THIS EXISTS (backlog #489):
# The ~/.claude.json registration used to hardcode an absolute interpreter path
# (/Library/Frameworks/Python.framework/Versions/3.13/bin/python3) and an absolute
# cwd inside iCloud (.../CloudDocs/.../Glintstone/PROJECT). Both went stale:
#   - the 3.13 framework python was removed (only an empty version dir remained)
#   - the repo was re-cloned to ~/Glintstone, so the iCloud cwd vanished
# Either dead path makes Claude Code fail to spawn the process => "ENOENT".
#
# This wrapper makes the launch robust by RE-DERIVING everything at each (re)launch:
#   - cwd  = the repo root (the dir this script lives in, two levels up)
#   - python = first working interpreter from a preference list (repo venv first)
#   - env  = sane defaults that the registration can still override
# So if the env drifts again (pyenv version bump, venv rebuilt, etc.) the next
# relaunch self-corrects instead of staying broken. Claude Code respawns a dead
# stdio MCP on reconnect; because this script re-derives paths, that respawn heals.

set -euo pipefail

# Repo root = parent of this script's directory (mcp/ -> repo root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Defaults — overridable by env passed from the registration / shell.
export GS_API_URL="${GS_API_URL:-https://api.glintstone.org/api/v2}"
export GS_CLIENT_LABEL="${GS_CLIENT_LABEL:-claude-code}"

# Pick the first interpreter that exists AND can import the MCP deps.
# Order: repo venv (most isolated) -> pyenv -> PATH python3 -> system python3.
pick_python() {
  local candidates=(
    "${REPO_ROOT}/venv/bin/python"
    "${REPO_ROOT}/.venv/bin/python"
  )
  # pyenv-resolved python, if pyenv is present.
  if command -v pyenv >/dev/null 2>&1; then
    local pyenv_py
    pyenv_py="$(pyenv which python3 2>/dev/null || true)"
    [ -n "${pyenv_py}" ] && candidates+=("${pyenv_py}")
  fi
  # PATH python3, then the macOS system python.
  local path_py
  path_py="$(command -v python3 2>/dev/null || true)"
  [ -n "${path_py}" ] && candidates+=("${path_py}")
  candidates+=("/usr/bin/python3")

  local py
  for py in "${candidates[@]}"; do
    if [ -x "${py}" ] && "${py}" -c "import mcp.server.fastmcp, httpx" >/dev/null 2>&1; then
      echo "${py}"
      return 0
    fi
  done
  return 1
}

PYTHON="$(pick_python || true)"
if [ -z "${PYTHON:-}" ]; then
  echo "glintstone-mcp: no Python interpreter with mcp[fastmcp]+httpx found." >&2
  echo "  Fix: ${REPO_ROOT}/venv/bin/pip install 'mcp[fastmcp]' httpx" >&2
  exit 127
fi

# Brief retry: a transient import/spawn hiccup on the first try shouldn't kill
# the session. exec on the final attempt so the server owns the process (clean
# stdio for the JSON-RPC stream).
attempt=1
max=3
while [ "${attempt}" -lt "${max}" ]; do
  if "${PYTHON}" -c "import mcp.server_stdio" >/dev/null 2>&1; then
    break
  fi
  echo "glintstone-mcp: module import failed (attempt ${attempt}/${max}), retrying..." >&2
  sleep 1
  attempt=$((attempt + 1))
done

exec "${PYTHON}" -m mcp.server_stdio
