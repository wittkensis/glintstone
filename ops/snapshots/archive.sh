#!/usr/bin/env bash
# Archive a raw source file to B2 (>50MB) or record VPS path (<50MB).
# Usage: ./ops/snapshots/archive.sh <file_path> <source_name> [version_label]
#
# Requires: b2 CLI, DATABASE_URL or .env, B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "${DATABASE_URL:-}" ] && [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

FILE_PATH="${1:?Usage: archive.sh <file_path> <source_name> [version_label]}"
SOURCE_NAME="${2:?Usage: archive.sh <file_path> <source_name> [version_label]}"
VERSION_LABEL="${3:-$(date +%Y-%m)}"
B2_BUCKET="${B2_BUCKET:-glintstone-sources}"
THRESHOLD_BYTES=$((50 * 1024 * 1024))  # 50 MB

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: file not found: $FILE_PATH" >&2
    exit 1
fi

FILE_NAME="$(basename "$FILE_PATH")"
FILE_SIZE="$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH")"
CHECKSUM="$(shasum -a 256 "$FILE_PATH" | awk '{print $1}')"
SNAPSHOT_DATE="$(date +%Y-%m-%d)"

echo "File:     $FILE_NAME"
echo "Size:     $(( FILE_SIZE / 1024 / 1024 )) MB"
echo "SHA-256:  $CHECKSUM"

if [ "$FILE_SIZE" -gt "$THRESHOLD_BYTES" ]; then
    BACKEND="b2"
    B2_KEY="${SOURCE_NAME}/${SNAPSHOT_DATE}/${FILE_NAME}"
    URI="b2://${B2_BUCKET}/${B2_KEY}"
    echo "Uploading to B2: $URI"
    b2 upload-file --info "source_name=${SOURCE_NAME}" "$B2_BUCKET" "$FILE_PATH" "$B2_KEY"
else
    BACKEND="vps"
    URI="$(realpath "$FILE_PATH")"
    echo "Small file — recording VPS path: $URI"
fi

echo "Recording in source_snapshots..."
python3 - <<PYTHON
import os, psycopg
conn = psycopg.connect(os.environ["DATABASE_URL"])
conn.execute(
    "INSERT INTO source_snapshots "
    "(source_name, snapshot_date, version_label, file_name, file_size_bytes, "
    "sha256_checksum, storage_backend, uri) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
    ("$SOURCE_NAME", "$SNAPSHOT_DATE", "$VERSION_LABEL", "$FILE_NAME",
     $FILE_SIZE, "$CHECKSUM", "$BACKEND", "$URI"),
)
conn.commit()
conn.close()
print("  Inserted into source_snapshots.")
PYTHON

echo "Done."
