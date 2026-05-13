#!/bin/bash
# Pre-commit documentation-freshness check.
# Mirrors the contract documented in .claude/skills/gs-curator-docs/SKILL.md.
# Warn-only — never blocks the commit.
#
# Rewritten 2026-05-11 for v2 paths.

WARN=0
STAGED=$(git diff --cached --name-only)

if [ -z "$STAGED" ]; then
    exit 0
fi

note() { echo "⚠ $*"; WARN=1; }

# Schema YAML or migration changed → expect a doc touch
if echo "$STAGED" | grep -qE 'data-model/migrations/.*\.sql$'; then
    if ! echo "$STAGED" | grep -qE '(gs-expert-data-model/migrations\.md|data-model/v2/glintstone-v2-schema\.yaml)'; then
        note "data-model/migrations/ touched — review .claude/skills/gs-expert-data-model/migrations.md and data-model/v2/glintstone-v2-schema.yaml"
    fi
fi

# Connector framework changed → expect skill doc touch
if echo "$STAGED" | grep -qE 'ingestion/(base|registry|runner|loader|dead_letters|cli)\.py$'; then
    if ! echo "$STAGED" | grep -q '.claude/skills/gs-expert-integrations/'; then
        note "ingestion/ framework touched — review .claude/skills/gs-expert-integrations/{SKILL.md,framework.md}"
    fi
fi

# New connector → expect port-table touch
if echo "$STAGED" | grep -qE '^A\s+ingestion/connectors/.*\.py$' || \
   git diff --cached --name-status --diff-filter=A | grep -qE 'ingestion/connectors/.*\.py$'; then
    if ! echo "$STAGED" | grep -q 'gs-expert-integrations/framework.md'; then
        note "New connector file — update the port table in .claude/skills/gs-expert-integrations/framework.md"
    fi
fi

# CSS tokens changed → expect tokens doc touch
if echo "$STAGED" | grep -q 'app/static/css/core/tokens.css'; then
    if ! echo "$STAGED" | grep -q 'gs-expert-ui/css-tokens.md'; then
        note "tokens.css touched — review .claude/skills/gs-expert-ui/css-tokens.md"
    fi
fi

# Deploy workflow / scripts changed
if echo "$STAGED" | grep -qE '(\.github/workflows/.*\.yml|ops/deploy/.*\.sh)'; then
    if ! echo "$STAGED" | grep -q 'gs-expert-deployment/'; then
        note "Deployment surface touched — review .claude/skills/gs-expert-deployment/"
    fi
fi

# New tables in a migration → fixture catalog reminder
if echo "$STAGED" | grep -qE 'data-model/migrations/.*\.sql$'; then
    if git diff --cached data-model/migrations/ 2>/dev/null | grep -qE '^\+CREATE TABLE'; then
        if ! echo "$STAGED" | grep -q 'gs-curator-artifacts/catalog.yaml'; then
            note "New table in migration — consider adding a fixture scenario to .claude/skills/gs-curator-artifacts/catalog.yaml"
        fi
    fi
fi

if [ "$WARN" -ne 0 ]; then
    echo ""
    echo "(Warnings only — commit proceeds. Run again after updating docs.)"
fi

exit 0
