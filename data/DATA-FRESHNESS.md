# Data Freshness & Refresh Guide

Source of truth for when each dataset was last pulled and how to refresh it.

Last full audit: **2026-02-14**

---

## Current State

### CDLI (Cuneiform Digital Library Initiative)

| Asset | Local Path | Pulled | Upstream Date | Size | Status |
|-------|-----------|--------|---------------|------|--------|
| Catalog CSV | `sources/CDLI/metadata/cdli_cat.csv` | 2026-02-04 | Aug 2022 (last CDLI bulk dump) | 148 MB, 353k artifacts | Current with upstream |
| ATF transliterations | `sources/CDLI/metadata/cdliatf_unblocked.atf` | 2026-02-04 | Aug 2022 (last CDLI bulk dump) | 83 MB, 135k inscriptions | Current with upstream |
| Catalog JSON (API) | `sources/CDLI/catalogue/batch-00000.json` | 2026-02-04 | Live API | 909 KB (100 records only) | Incomplete -- only used for early prototyping. Production uses CSV. |
| Images | `sources/CDLI/images/` | On-demand | Live | ~104 cached | Fetched by the app as needed |

**Upstream source:** https://github.com/cdli-gh/data (git-lfs). CDLI's README states "last update was August 2022." The bulk dump repo has not been updated since. The live API at cdli.earth may have newer records but there is no bulk export mechanism beyond the git repo.

### ORACC Projects

| Project | Local Path | Pulled | Upstream Build Date | Glossaries | Corpus Files | Status |
|---------|-----------|--------|---------------------|------------|--------------|--------|
| **dcclt** | `sources/ORACC/dcclt/json/dcclt/` | 2026-02-04 | 2025-12-12 | 8 files (61 MB) | 4,980 | In DB |
| **ogsl** | `sources/ORACC/ogsl/json/ogsl/` | 2026-02-04 | 2024-02-14 | N/A (sign list) | N/A | In DB |
| **saao** | `sources/ORACC/saao/json/saao/` | 2026-02-04 | 2023-12-10 | 6 files (334 MB) | 0 (index only) | Ready to import |
| **rinap** | `sources/ORACC/rinap/json/rinap/` | 2026-02-04 | 2025-04-28 | 3 files (83 MB) | 48 (rinap1) | Ready to import |
| **hbtin** | `sources/ORACC/hbtin/json/hbtin/` | 2026-02-04 | 2024-06-28 | 1 file (4.3 MB) | 487 | Ready to import |
| **dccmt** | `sources/ORACC/dccmt/json/dccmt/` | 2026-02-04 | 2024-06-28 | 1 file (5 MB) | 252 | Ready to import |
| **ribo** | `sources/ORACC/ribo/json/ribo/` | 2026-02-04 | 2023-10-22 | 3 files (31 MB) | 0 (uses proxies) | Ready to import |
| **epsd2** | `sources/ORACC/epsd2/json/epsd2/` | 2026-02-14 | 2022-12-07 | 1 file (1.8 GB) | 0 (dictionary) | Ready to import |
| **riao** | `sources/ORACC/riao/json/riao/` | 2026-02-14 | 2024-06-07 | 0 | 0 (index only) | Ready to import |
| **etcsri** | `sources/ORACC/etcsri/json/etcsri/` | 2026-02-14 | 2024-08-14 | 2 files (33 MB) | 1,456 | Ready to import |
| **blms** | `sources/ORACC/blms/json/blms/` | 2026-02-14 | 2024-06-28 | 4 files (42 MB) | 229 | Ready to import |
| **amgg** | `sources/ORACC/amgg/json/amgg/` | 2026-02-14 | 2024-11-25 | 0 | 0 (portal only) | Reference data only |

**Unavailable on ORACC server** (checked 2026-02-14, all return 500/404):
- rime, etcsl, cams, ctij

**Upstream source:** `https://build-oracc.museum.upenn.edu/json/{project}.zip` for most projects. Some also available at `https://oracc.museum.upenn.edu/json/{project}.zip`. The "Upstream Build Date" comes from the `metadata.json` timestamp inside each zip -- this is when ORACC last rebuilt that project's JSON export.

### ML Training Data

| Asset | Local Path | Pulled | Source | Status |
|-------|-----------|--------|--------|--------|
| CompVis annotations | `sources/compvis-annotations/` | 2026-02-05 | [GitHub](https://github.com/CompVis/cuneiform-sign-detection-dataset) | Git clone, HEAD=77d8e03. In DB (11,070 annotations). |
| eBL OCR data | `sources/ebl-annotations/` | 2026-02-05 | [GitHub](https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data) | Git clone, HEAD=ffaee6f. Used for ML training. |
| eBL API reference | `sources/eBL/metadata/ebl-api/` | 2026-02-04 | [GitHub](https://github.com/ElectronicBabylonianLiterature/ebl-api) | Shallow clone for schema reference. No data imported. |

### Reference Data

| Asset | Local Path | Pulled | Source | Status |
|-------|-----------|--------|--------|--------|
| Unicode character names | `sources/ePSD2/unicode/DerivedName.txt` | 2026-02-04 | unicode.org | 1.8 MB. Stable, rarely changes. |
| Unicode block definitions | `sources/ePSD2/unicode/Blocks.txt` | 2026-02-04 | unicode.org | 11 KB. Stable. |
| ATF primer | `sources/ePSD2/atf/atf-primer.html` | 2026-02-04 | oracc.museum.upenn.edu | 18 KB. Reference spec. |

---

## Refresh Procedures

### CDLI Catalog & ATF

CDLI's bulk dump has not been updated since August 2022. Check periodically whether they resume publishing.

```bash
# Check if the CDLI data repo has new commits
git -C data/sources/CDLI/metadata log --oneline -1 --format="%H %ci"
git -C data/sources/CDLI/metadata fetch origin
git -C data/sources/CDLI/metadata log --oneline -1 origin/master --format="%H %ci"

# If new commits exist:
git -C data/sources/CDLI/metadata pull
git -C data/sources/CDLI/metadata lfs pull

# Then re-import:
python data/tools/import/import_cdli_catalog.py
python data/tools/import/import_cdli_atf.py
python data/tools/import/import_translations.py
```

**What changes:** The `cdli_cat.csv` and `cdliatf_unblocked.atf` files are Git LFS objects in the cdli-gh/data repo. When CDLI pushes updates, pulling will get new versions.

**Frequency:** Check monthly. Low urgency since upstream appears stalled.

### ORACC Project Zips

Each ORACC project publishes a zip of its entire JSON export. The build date inside `metadata.json` tells you when ORACC last rebuilt it.

```bash
# Check if a project has been rebuilt since our last pull
# Compare the remote Last-Modified header to our local file date
curl -sI "https://build-oracc.museum.upenn.edu/json/dcclt.zip" | grep -i last-modified

# Re-download a specific project
PROJECT=dcclt
curl -L -o "data/sources/ORACC/$PROJECT/$PROJECT.zip" \
  "https://build-oracc.museum.upenn.edu/json/$PROJECT.zip"

# Verify it's a valid zip (not an HTML error page)
file "data/sources/ORACC/$PROJECT/$PROJECT.zip"
# Should say "Zip archive data", NOT "HTML document" or "ASCII text"

# Extract (overwrites existing json/ folder)
unzip -o "data/sources/ORACC/$PROJECT/$PROJECT.zip" \
  -d "data/sources/ORACC/$PROJECT/json/"

# Then re-import (when import script supports this project)
```

**Fallback URL patterns** (if the primary 500s):
1. `https://build-oracc.museum.upenn.edu/json/{project}.zip` (primary)
2. `https://oracc.museum.upenn.edu/json/{project}.zip` (sometimes works when build-oracc doesn't)
3. `https://oracc.museum.upenn.edu/{project}/json/{project}.zip` (individual project path)

**Known issue:** Some projects (rime, etcsl, cams, ctij) return 500 errors on all URL patterns. This is a server-side issue. Re-check periodically.

**Frequency:** Quarterly. ORACC rebuilds are infrequent -- most projects haven't changed in 1-2 years.

### Refresh All ORACC Projects (Batch)

```bash
# Check all projects at once
for proj in dcclt saao rinap hbtin dccmt ribo epsd2 riao etcsri blms ogsl; do
  remote_date=$(curl -sI "https://build-oracc.museum.upenn.edu/json/$proj.zip" 2>/dev/null \
    | grep -i last-modified | cut -d' ' -f2-)
  local_date=$(stat -f "%Sm" -t "%Y-%m-%d" \
    "data/sources/ORACC/$proj/json/$proj/metadata.json" 2>/dev/null || echo "missing")
  echo "$proj: local=$local_date  remote=$remote_date"
done

# Re-download only projects where remote is newer
# (manual comparison needed -- remote returns HTTP date, local is file date)
```

### Git Sub-repos (CompVis, eBL)

```bash
# Check for updates
git -C data/sources/compvis-annotations fetch origin
git -C data/sources/compvis-annotations log --oneline HEAD..origin/main

git -C data/sources/ebl-annotations fetch origin
git -C data/sources/ebl-annotations log --oneline HEAD..origin/main

# Pull if new commits exist
git -C data/sources/compvis-annotations pull
git -C data/sources/ebl-annotations pull

# Re-import CompVis annotations if updated
python data/tools/import/import_compvis_annotations.py
```

**Frequency:** Monthly. Both repos update rarely.

### Unavailable Projects (rime, etcsl, cams, ctij)

These return server errors as of 2026-02-14. To check if they've come back online:

```bash
for proj in rime etcsl cams ctij; do
  status=$(curl -sIL -o /dev/null -w "%{http_code}" \
    "https://build-oracc.museum.upenn.edu/json/$proj.zip")
  echo "$proj: HTTP $status"
done
```

If any return 200, download and extract using the standard ORACC procedure above.

**Frequency:** Monthly. These may come back when ORACC rebuilds their server.

---

## Validation After Refresh

After re-downloading any source, verify data integrity before importing:

```bash
# Check file isn't an HTML error page (643 bytes = ORACC error page, 4 bytes = "404")
file data/sources/ORACC/{project}/{project}.zip
# Must say "Zip archive data"

# Check extracted JSON is valid
python3 -c "import json; json.load(open('data/sources/ORACC/{project}/json/{project}/metadata.json'))"

# After import, verify record counts haven't decreased
sqlite3 database/glintstone.db "SELECT COUNT(*) FROM glossary_entries;"
sqlite3 database/glintstone.db "SELECT COUNT(*) FROM lemmas;"
```

---

## Known Data Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| CDLI bulk dump frozen at Aug 2022 | ~4 years of new catalog entries missing | Monitor cdli-gh/data repo; consider CDLI API scraping for delta updates |
| 4 ORACC projects unavailable (rime, etcsl, cams, ctij) | Missing early royal inscriptions, Sumerian literature, scholarly texts | Server-side issue. Re-check periodically. |
| ePSD2 data is from Dec 2022 | Sumerian dictionary may be outdated | Re-download from `oracc.museum.upenn.edu/json/epsd2.zip` if rebuilt |
| Only DCCLT lemmas imported from ORACC | 10 other extracted projects have glossaries/corpora not yet in DB | Write expanded import scripts |
| eBL fragments directory empty | No fragment data beyond OCR annotations | eBL API requires authentication; consider applying for access |
