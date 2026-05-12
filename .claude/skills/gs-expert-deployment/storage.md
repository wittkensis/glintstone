---
question: "How are images and large assets hosted today, and what's the Cloudflare R2 migration plan?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Captures the current asset flow (Hostinger filesystem) and the planned R2 migration referenced in issue #52."
status: draft
audience: [claude, ops]
owners: [eric]
related_issues: ["#52", "#16"]
related_skills: [gs-expert-deployment]
supersedes: null
superseded_by: null
---

# Asset storage

## Today (Hostinger filesystem)

Images served ad-hoc from `/opt/glintstone/static/` on the VPS:

- Tablet photographs: proxied/cached from `cdli.earth` on first request
- Marketing site assets: shipped in the release tarball
- ML training-data thumbnails: synced from `source-data/sources/` at deploy time (small subset)

Pain points (per issue #52):

- No thumbnails — every page load fetches full-resolution images
- No CDN — every byte goes through Hostinger's bandwidth
- Filesystem usage trends toward VPS disk limit
- No image-processing pipeline

## Planned: Cloudflare R2

R2 = S3-compatible object storage with no egress fees and Cloudflare's global CDN.

Migration outline (when this rolls forward):

1. **Provision R2 bucket** `glintstone-assets`
2. **Generate access keys**, store in GitHub Actions secrets
3. **Write `gs-expert-integrations` connector** to push tablet thumbnails into R2 (separate runs per artifact type)
4. **Add a `core/storage.py`** abstraction with two backends: `LocalFilesystem` and `R2`. Switch via env var.
5. **Update `app/templates/`** to use the URL helper rather than hardcoded paths
6. **Cutover** in stages: marketing assets first, then thumbnails, then full-res
7. **Cloudflare image transforms** for on-the-fly thumbnailing (skip server-side resize)
8. **Custom domain** `cdn.glintstone.org` pointing at R2 via Cloudflare

## Decisions to make before starting

- **Bucket layout**: `tablets/P######/{obverse,reverse}.jpg` vs flat `images/<sha>.jpg`? Recommend keyed-by-P-number for human-debuggability.
- **Versioning**: enable R2 versioning so deletions are reversible.
- **Public vs signed URLs**: tablet images are CC0 — public. ML training subsets may need attribution headers.
- **Cache headers**: long TTL (immutable URLs keyed by content hash).

## What lives where (steady state)

| Asset type | Where | Why |
|---|---|---|
| Tablet photographs (full-res) | R2 | Heavy, public, cached at CDN |
| Tablet thumbnails (generated) | R2 + Cloudflare transforms | On-demand sizing |
| Marketing site (static HTML/CSS/JS) | Hostinger (or Cloudflare Pages later) | Small, shipped with release |
| User-uploaded assets (future) | R2 + signed URLs | When user accounts land |
| ML training data | `source-data/sources/` (local) + R2 mirror | Heavy; gitignored locally |
| Database backups | Neon's built-in (point-in-time) | Don't duplicate |

## MCP routing

When the user mentions image hosting, Cloudflare, R2 — load this file. Once the Cloudflare MCP is available, see `mcp-cheat-sheet.md` for which tool to use.

## When to revisit

- Hostinger disk usage > 80%: prioritize the R2 migration
- Tablet thumbnails ship: update `core/storage.py` defaults
- Issue #16 lands: thumbnail generation pipeline can write directly to R2

This file is `status: draft` until the migration starts; flip to `active` once `core/storage.py` exists.
