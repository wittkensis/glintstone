#!/bin/bash
# Pre-push docs-freshness check. Warn-only — never blocks the push.
#
# Two checks:
#   1. The path-to-doc contract from .claude/skills/gs-curator-docs/SKILL.md
#      (mirrors ops/hooks/pre-commit-docs.sh but over the full commit range)
#   2. YAML 'modified:' stamps older than 60 days on active skills + key docs.

WARN=0
note() { echo "⚠ $*"; WARN=1; }

UPSTREAM="${1:-origin/main}"
RANGE="$UPSTREAM..HEAD"

# If upstream doesn't exist, fall back to last 5 commits
if ! git rev-parse --verify "$UPSTREAM" >/dev/null 2>&1; then
    RANGE="HEAD~5..HEAD"
fi

TOUCHED=$(git diff --name-only "$RANGE" 2>/dev/null)
if [ -z "$TOUCHED" ]; then
    exit 0
fi

# Contract checks
if echo "$TOUCHED" | grep -qE 'data-model/migrations/.*\.sql$'; then
    if ! echo "$TOUCHED" | grep -q 'gs-expert-data-model/migrations.md'; then
        note "Migrations touched but gs-expert-data-model/migrations.md not updated"
    fi
fi

if echo "$TOUCHED" | grep -qE 'ingestion/connectors/.*\.py$'; then
    if ! echo "$TOUCHED" | grep -q 'gs-expert-integrations/framework.md'; then
        note "Connectors touched but gs-expert-integrations/framework.md not updated"
    fi
fi

if echo "$TOUCHED" | grep -q 'app/static/css/core/tokens.css'; then
    if ! echo "$TOUCHED" | grep -q 'gs-expert-ui/css-tokens.md'; then
        note "tokens.css touched but gs-expert-ui/css-tokens.md not updated"
    fi
fi

if echo "$TOUCHED" | grep -qE '(\.github/workflows/.*\.yml|ops/deploy/.*\.sh)'; then
    if ! echo "$TOUCHED" | grep -q 'gs-expert-deployment/'; then
        note "Deployment surface touched but no gs-expert-deployment/ doc updated"
    fi
fi

# Stamp staleness — 60-day window on active skill files and v2 schema docs
STAMP_CUTOFF=$(date -v-60d +%Y-%m-%d 2>/dev/null || date -d '60 days ago' +%Y-%m-%d 2>/dev/null)
if [ -n "$STAMP_CUTOFF" ]; then
    STALE=0
    while IFS= read -r f; do
        if [ -f "$f" ]; then
            MOD=$(awk '/^modified:/ { print $2; exit }' "$f" 2>/dev/null)
            if [ -n "$MOD" ] && [ "$MOD" \< "$STAMP_CUTOFF" ]; then
                if [ "$STALE" -eq 0 ]; then
                    note "Docs with 'modified:' older than 60 days (cutoff $STAMP_CUTOFF):"
                    STALE=1
                fi
                echo "    $f  (modified: $MOD)"
            fi
        fi
    done < <(find .claude/skills data-model docs/data-model -maxdepth 4 -name '*.md' 2>/dev/null; ls README.md CLAUDE.md 2>/dev/null)
fi

if [ "$WARN" -ne 0 ]; then
    echo ""
    echo "(Warnings only — push proceeds.)"
fi

exit 0
