#!/usr/bin/env bash
# Refresh materialized views after major ingestion runs or nightly.
#
# Required env vars (sourced from .env or systemd EnvironmentFile):
#   DB_PASSWORD, DB_HOST, DB_PORT, DB_USER, DB_NAME
#
# Usage:
#   ./ops/cron/refresh_views.sh
#
# In crontab (runs nightly at 02:30 local):
#   30 2 * * * cd /opt/glintstone/current && ./ops/cron/refresh_views.sh >> /var/log/glintstone/refresh_views.log 2>&1

set -euo pipefail

PGPASSWORD="${DB_PASSWORD:-}" psql \
    -h "${DB_HOST:-127.0.0.1}" \
    -p "${DB_PORT:-5432}" \
    -U "${DB_USER:-glintstone}" \
    -d "${DB_NAME:-glintstone}" \
    -c "REFRESH MATERIALIZED VIEW CONCURRENTLY filter_options_cache;" \
    -c "REFRESH MATERIALIZED VIEW CONCURRENTLY genre_period_lemma_prior;"

echo "Materialized views refreshed at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
