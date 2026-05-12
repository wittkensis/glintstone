---
question: "How are images and large assets hosted today, and what's the Cloudflare R2 migration plan?"
created: 2026-05-11
modified: 2026-05-12
context: "Created 2026-05-11. Updated 2026-05-12 when R2 went live: bucket glintstone-assets provisioned, migration 022 (artifact_images) deployed, 102 locally-archived tablet images uploaded as the seed batch."
status: active
audience: [claude, ops]
owners: [eric]
related_issues: ["#52", "#16"]
related_skills: [gs-expert-deployment, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Asset storage

## Today (Cloudflare R2, live as of 2026-05-12)

Tablet images live in the `glintstone-assets` R2 bucket. Per-image metadata
lives in the `artifact_images` table (migration 022). The R2 backend is
S3-compatible — see `core/storage.py` for the boto3 client with the R2-specific
quirks (sigv4 + when_required checksums + cfat_-token-to-sha256 secret
derivation).

Object key layout:

```
tablets/<P-number>/<image_type>-<suffix>.<ext>
tablets/<P-number>/<image_type>-<suffix>-thumb.webp
```

Examples: `tablets/P000001/photo-local.jpg`, `tablets/P000001/photo-local-thumb.webp`,
`tablets/P000001/photo-88909.jpg` (where 88909 is the cdli_reader_id).

Two ingestion paths populate the table:

| Path | Triggered by | Rate limit | Owner |
|---|---|---|---|
| `ops/scripts/upload_local_images.py` | One-time bulk upload of pre-downloaded archive | 5s floor | ops (manual) |
| `ingestion/connectors/cdli_images.py` (planned, task #9) | Periodic background crawl | 60s (robots.txt) | scheduler |
| `api/services/image_ondemand.py` (planned, task #11) | User views an artifact card without cached image | 5s floor | API |

### Current seed batch

102 unique P-numbers uploaded 2026-05-12 15:31–15:37 UTC, originals (~29 MB)
+ WebP thumbnails (400px long edge, q80). All rows have
`attribution_raw IS NULL` pending the HTML-only attribution backfill pass.

### Public access

The bucket needs "Allow Access" toggled on for the auto-assigned
`pub-<bucket>.r2.dev` URL, OR a custom domain like `cdn.glintstone.org`
mapped via Cloudflare. Without one of those, originals + thumbnails return
HTTP 401 to browsers. Server-side ingestion uses authenticated S3 PUTs
and is unaffected.

### Marketing assets

Marketing site (`/marketing/`) still ships in the release tarball. No plan
to move it to R2 — it's small and the symlink-rotation pattern works fine.

### ML training data

Lives in `source-data/sources/` (gitignored). When ML jobs land on the
VPS, they'll read from R2 instead. Not migrated yet.

## Migration history

| Date | What |
|---|---|
| 2026-05-11 | Plan drafted, issue #52 opened |
| 2026-05-12 12:48 | VPS Postgres stood up; production DB migrated off Neon |
| 2026-05-12 15:03 | Migration 022 applied (artifact_images schema) |
| 2026-05-12 15:37 | First 102 images live in R2 + DB |
| Open | R2 public access toggle; attribution backfill; on-demand fetch; full background backfill |

## R2 quirks worth remembering

These are footguns we hit during the 2026-05-12 cutover. They live in
`core/storage.py` and the test suite, but if either is rewritten, preserve
the behavior:

1. **`cfat_*` secret format requires SHA-256 derivation.** Cloudflare's
   dashboard / AI Assistant shows the raw API token value (starts with
   `cfat_`). The actual S3 Secret Access Key is `sha256(token_value)` in
   hex. `_resolve_r2_secret()` in `core/storage.py` handles this
   transparently — if you bypass it, you'll get `SignatureDoesNotMatch`
   on every PUT and the error will not say why.

2. **boto3 ≥1.36 default checksum settings break R2.** Force
   `request_checksum_calculation="when_required"` and
   `response_checksum_validation="when_required"` in the `Config`.
   Otherwise you'll see `SignatureDoesNotMatch` (same error as #1 — these
   are easy to confuse during diagnosis).

3. **`NULLS NOT DISTINCT` in unique constraints isn't free.** The
   `artifact_images_unique_source` UNIQUE on `(p_number, image_type,
   cdli_reader_id)` doesn't catch duplicates when `cdli_reader_id IS NULL`
   (which is true for every locally-uploaded image). Migration 023 adds a
   partial unique index for the NULL case.

4. **R2 public access defaults to OFF.** New buckets refuse anonymous GETs
   even on `pub-<bucket>.r2.dev`. Toggle "Allow Access" in dashboard or
   front with a custom domain.

## What lives where (steady state)

| Asset type | Where | Why |
|---|---|---|
| Tablet photographs (full-res) | R2 `tablets/<P>/<type>-<suffix>.jpg` | Heavy, public, cached at CDN |
| Tablet thumbnails | R2 `tablets/<P>/<type>-<suffix>-thumb.webp` | Generated server-side at upload time |
| Marketing site (static HTML/CSS/JS) | VPS filesystem, shipped with release | Small, no benefit to CDN |
| User-uploaded assets (future) | R2 + signed URLs | When user accounts land |
| ML training data | `source-data/sources/` (local) + R2 mirror | Heavy; gitignored locally |
| Database | VPS-local Postgres `127.0.0.1:5432` (as of 2026-05-12) | Migrated off Neon |
| Database backups | `/var/www/glintstone/shared/backups/` on VPS | Replaced Neon point-in-time |

## MCP routing

When the user mentions image hosting, Cloudflare, R2 — load this file. Once the Cloudflare MCP is available, see `mcp-cheat-sheet.md` for which tool to use.

## When to revisit

- Hostinger disk usage > 80%: prioritize the R2 migration
- Tablet thumbnails ship: update `core/storage.py` defaults
- Issue #16 lands: thumbnail generation pipeline can write directly to R2

This file is `status: draft` until the migration starts; flip to `active` once `core/storage.py` exists.
