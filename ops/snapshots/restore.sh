#!/usr/bin/env bash
# Restore a raw source file from B2 or VPS path.
# Usage: ./ops/snapshots/restore.sh <source_name> [snapshot_date]
#
# Without a date, lists available snapshots.
# With a date (YYYY-MM-DD), downloads that snapshot.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "${DATABASE_URL:-}" ] && [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

SOURCE_NAME="${1:?Usage: restore.sh <source_name> [snapshot_date]}"
SNAPSHOT_DATE="${2:-}"

if [ -z "$SNAPSHOT_DATE" ]; then
    echo "Available snapshots for $SOURCE_NAME:"
    python3 - <<PYTHON
import os, psycopg
conn = psycopg.connect(os.environ["DATABASE_URL"])
rows = conn.execute(
    "SELECT snapshot_date, version_label, file_name, file_size_bytes, storage_backend, uri "
    "FROM source_snapshots WHERE source_name = %s ORDER BY snapshot_date DESC",
    ("$SOURCE_NAME",),
).fetchall()
for row in rows:
    size_mb = (row[3] or 0) // 1024 // 1024
    print(f"  {row[0]}  {row[2]}  ({size_mb} MB, {row[4]})  {row[5]}")
conn.close()
PYTHON
    exit 0
fi

echo "Restoring $SOURCE_NAME snapshot from $SNAPSHOT_DATE..."
python3 - <<PYTHON
import os, subprocess, psycopg
conn = psycopg.connect(os.environ["DATABASE_URL"])
row = conn.execute(
    "SELECT file_name, storage_backend, uri FROM source_snapshots "
    "WHERE source_name = %s AND snapshot_date = %s ORDER BY id DESC LIMIT 1",
    ("$SOURCE_NAME", "$SNAPSHOT_DATE"),
).fetchone()
conn.close()

if not row:
    print(f"No snapshot found for $SOURCE_NAME on $SNAPSHOT_DATE")
    exit(1)

file_name, backend, uri = row
dest = f"$PROJECT_DIR/source-data/sources/$SOURCE_NAME/{file_name}"
os.makedirs(os.path.dirname(dest), exist_ok=True)

if backend == "b2":
    # uri = b2://bucket/key
    parts = uri[5:].split("/", 1)
    bucket, key = parts[0], parts[1]
    print(f"Downloading from B2: {uri}")
    subprocess.run(["b2", "download-file-by-name", bucket, key, dest], check=True)
elif backend in ("vps", "local"):
    print(f"Source is at: {uri}")
    print(f"Copy manually or run: cp '{uri}' '{dest}'")
else:
    print(f"Unknown backend: {backend}")
    exit(1)

print(f"Restored to: {dest}")
PYTHON
