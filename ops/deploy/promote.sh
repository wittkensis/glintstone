#!/usr/bin/env bash
# Open a PR to promote staging → main (which triggers the gated prod deploy).
#
# Usage:
#   ops/deploy/promote.sh                   # opens PR with auto-generated body
#   ops/deploy/promote.sh "release notes"   # uses given message as PR body
#
# Preconditions:
#   - `staging` branch ahead of `main` (otherwise there's nothing to promote)
#   - `gh` authenticated against this repo
#
# What it does:
#   1. Refreshes both remote branches locally
#   2. Computes the diff (commits + files changed) between staging and main
#   3. Opens a PR `staging → main` with that diff summarised in the body
#   4. Prints the PR URL — merge from the GitHub UI to trigger the prod approval gate

set -euo pipefail

cd "$(dirname "$0")/../.."

git fetch --quiet origin staging main

ahead=$(git rev-list --count origin/main..origin/staging)
if [ "$ahead" -eq 0 ]; then
    echo "staging is not ahead of main — nothing to promote."
    exit 0
fi

# Refuse to promote a staging branch that hasn't been deployed to staging.
# Heuristic: check that the latest CI run on `staging` finished green.
latest_status=$(gh run list --branch staging --workflow deploy.yml --limit 1 \
                  --json conclusion --jq '.[0].conclusion' 2>/dev/null || echo "")
if [ "$latest_status" != "success" ]; then
    cat >&2 <<EOF
::warning:: Latest deploy.yml run on staging is "$latest_status" (not "success").
Promoting now would push code that hasn't proven itself on staging.

Continue anyway? [y/N]
EOF
    read -r reply
    case "$reply" in
        y|Y) ;;
        *) echo "Aborted."; exit 1 ;;
    esac
fi

commits=$(git log --oneline origin/main..origin/staging)
files=$(git diff --stat origin/main..origin/staging | tail -n +1)
commit_count=$(echo "$commits" | wc -l | tr -d ' ')

custom_body="${1:-}"

body=$(cat <<EOF
## Promote staging → production

**$commit_count commit(s) ahead of main.** Staging deploy is green.

### Commits

\`\`\`
$commits
\`\`\`

### Files changed

\`\`\`
$files
\`\`\`

${custom_body:+### Notes\n\n$custom_body\n}

---

Merging this PR triggers \`.github/workflows/deploy.yml\` against the
**production** environment, which is gated on a required reviewer approval.
EOF
)

url=$(gh pr create \
        --base main \
        --head staging \
        --title "Promote staging → production ($commit_count commits)" \
        --body "$body")

echo "Promotion PR opened: $url"
echo "Merge from the GitHub UI to trigger the production approval gate."
