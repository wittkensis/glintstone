---
question: "TODO: one sentence — what question does README.md answer?"
created: 2026-05-11
modified: 2026-05-11
context: "TODO: why was this file created?"
status: draft
audience: [engineers]
owners: [eric]
related_issues: []
related_skills: []
supersedes: null
superseded_by: null
---

# Source Snapshots

Raw source files are large and should not live in git. This directory contains
scripts to archive them and track their location in `source_snapshots` (migration 021).

## Storage decision

| File | Size | Backend | Rationale |
|---|---|---|---|
| `cdliatf_unblocked.atf` | ~500 MB | **B2** | Too large for VPS; rarely re-downloaded |
| `cdli_cat.csv` | ~200 MB | **B2** | Same |
| ORACC project ZIPs | ~50–200 MB each | **B2** | Multiple projects |
| `ogsl-sl.json` | ~10 MB | VPS disk | Small; cheap to keep locally |
| `ebl.txt`, `cuneiform-signs.json` | < 5 MB | VPS disk | Trivial size |

**Rule:** files over 50 MB go to B2; under 50 MB stay on VPS disk under
`/var/www/glintstone/source-data/sources/` (excluded from rsync deploys).

## Setup (one-time)

```bash
# Install B2 CLI
pip install b2

# Authenticate
b2 authorize-account <keyID> <applicationKey>

# Create bucket
b2 create-bucket glintstone-sources allPrivate
```

Add to `~/.env` (never committed):
```
B2_KEY_ID=...
B2_APPLICATION_KEY=...
B2_BUCKET=glintstone-sources
```

## Archiving a source file

```bash
./ops/snapshots/archive.sh source-data/sources/CDLI/metadata/cdli_cat.csv cdli-catalog
```

This will:
1. Compute SHA-256 checksum
2. Upload to B2 (if > 50 MB) or note VPS path
3. Insert a row into `source_snapshots`

## Restoring a source file

```bash
./ops/snapshots/restore.sh cdli-catalog 2022-08-01
```

Lists available snapshots and downloads to the correct local path.
