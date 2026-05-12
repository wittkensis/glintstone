---
question: "How do I go from zero to contributing on Glintstone in one week?"
created: 2026-02-23
modified: 2026-05-11
context: "Day 1–5 ramp-up. Migrated from PLAN/Engineer Onboarding Guide.md during the 2026-05-11 knowledge architecture overhaul, with Day 4 rewritten to point at the ingestion framework (ingestion/connectors/) instead of the retired v1 numbered scripts."
status: active
audience: [engineers]
owners: [eric]
related_issues: ["#60"]
related_skills: [gs-orient-project, gs-expert-integrations, gs-expert-data-model, gs-expert-ui, gs-expert-deployment]
supersedes: "PLAN/Engineer Onboarding Guide.md"
superseded_by: null
---

# Engineer Onboarding Guide

> Goal: zero-to-contributing in one week. Read [Assyriology 101](assyriology-101.md) first for the domain primer; this file covers the codebase.

---

## Day 1: Orient

### What Glintstone Is

A platform that unifies fragmented cuneiform research data (CDLI, ORACC, eBL, ePSD2, OGSL) so scholars can search, browse, and analyze ~353k ancient artifacts in one place. Every artifact is tracked through five stages: Captured > Recognized > Transcribed > Lemmatized > Translated.

This is a production academic tool. Data integrity and source attribution are not optional — they're structural requirements. Scholars' careers depend on proper credit.

### Architecture in 60 Seconds

```
Browser
  |
nginx (.test domains, port 80)
  |
  +---> Web App (port 8002, FastAPI + Jinja2)
  |         |
  |         +---> API (port 8001, FastAPI + JSON)
  |                   |
  |                   +---> PostgreSQL 17
  |
  +---> Marketing site (static)
```

Two-tier FastAPI: the web layer renders HTML and calls the API layer via httpx. The web layer never touches the database directly. This separation exists so the API can serve future consumers (other tools, ML pipelines, public access).

### Directory Map

```
api/                 REST API: routes, repositories, services
app/                 Web app: routes, Jinja2 templates, CSS, JS
core/                Shared: config, database pool, base repository
source-data/
  import-tools/      Numbered import scripts (01-23+)
  migrations/        SQL migrations (008-017)
  sources/           Raw data (gitignored, ~25GB)
data-model/       Schema spec (YAML), design docs
ml/                  ML model integrations
ops/local/           setup.sh, start.sh, stop.sh, nginx.conf
PLANNING/            Design documents, domain research
```

### Get Running

```bash
# Prerequisites: Homebrew, PostgreSQL 17, Python 3.9+

# One-time setup (creates DB, venv, /etc/hosts entries, nginx config)
./ops/local/setup.sh

# Start everything (PostgreSQL, API on 8001, web on 8002, nginx)
./ops/local/start.sh

# Verify
open http://app.glintstone.test       # Web UI
open http://api.glintstone.test/docs  # API docs (Swagger)

# Stop
./ops/local/stop.sh
```

Both servers run with `--reload` — edit a Python file and changes are live immediately.

---

## Day 2: Read the Code

### Start Here (in order)

| File | Why |
|------|-----|
| `Assyriology 101.md` | Domain primer — wedge-shaped marks to database tables |
| `core/config.py` | How settings work (pydantic-settings, .env) |
| `core/database.py` | Connection pool (psycopg3, dict_row, get_db dependency) |
| `core/repository.py` | BaseRepository: fetch_all, fetch_one, build_in_clause |
| `api/routes/artifacts.py` | Trace a request end-to-end |
| `api/repositories/artifact_repo.py` | Where SQL lives — the largest repo file |
| `app/routes/tablets.py` | How the web layer calls the API and renders templates |
| `app/templates/tablets/list.html` | Jinja2 template with macros and filters |
| `data-model/glintstone-schema.yaml` | Full schema spec |

### Key Code Patterns

**Repository pattern** — all SQL in `api/repositories/*_repo.py`, injected via FastAPI's `Depends(get_db)`:

```python
@router.get("/{p_number}")
def get_artifact(p_number: str, conn=Depends(get_db)):
    repo = ArtifactRepository(conn)
    return repo.find_by_p_number(p_number)
```

**Two-tier call chain** — web route calls API, never DB:

```python
# app/routes/tablets.py
async def tablet_detail(request, p_number):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_URL}/artifacts/{p_number}")
    return templates.TemplateResponse("tablets/detail.html", {"artifact": resp.json()})
```

**Cross-filter counts** — the filter sidebar shows how many results each option would produce, dynamically excluding the current dimension:

```python
def _cross_filter_where(self, active: dict, exclude: str):
    # Builds WHERE for all active filters EXCEPT the excluded dimension
    # So "Period" counts reflect your Genre/Language/Provenience selections
```

**Source attribution** — every record links to an `annotation_run` identifying who produced it, when, and from what source. This is non-negotiable.

---

## Day 3: Understand the Data

### The P-Number is Everything

`P227657` is a tablet. The P-number (from CDLI) is the universal join key across every table, every source, every system in the field. Think of it as the primary key for all of Assyriology.

### Canon Tables

Raw source data is messy. Canon tables normalize it:

| Table | Purpose | Example |
|-------|---------|---------|
| `period_canon` | Normalize time periods | "Ur III" maps to group "Third Millennium" |
| `provenience_canon` | Normalize places | "Nippur (mod. Nuffar)" becomes "Nippur" |
| `language_map` | Normalize language codes | "sux-x-emesal" maps to "Sumerian" |
| `genre_canon` | Normalize genres | Various genre strings to canonical forms |

These are seeded by `01_seed_lookup_tables.py` and used by the filter system.

### Database Access

```bash
# As the table owner (for migrations, schema changes)
/opt/homebrew/Cellar/postgresql@17/17.8/bin/psql -h 127.0.0.1 -U wittkensis -d glintstone

# As the app user (for read-only exploration)
/opt/homebrew/Cellar/postgresql@17/17.8/bin/psql -h 127.0.0.1 -U glintstone -d glintstone
```

**Ownership matters**: tables are owned by `wittkensis`, not `glintstone`. Run migrations as `wittkensis`. After creating new tables or sequences, GRANT permissions:

```sql
GRANT ALL ON new_table TO glintstone;
GRANT USAGE, SELECT ON SEQUENCE new_table_id_seq TO glintstone;
```

### Current Scale

| Table | Rows | Notes |
|-------|------|-------|
| artifacts | 353,283 | Every known tablet |
| text_lines | 1,395,668 | ATF decomposed |
| tokens | 3,957,240 | Individual words |
| lexical_lemmas | 61,435 | Dictionary entries |
| lexical_senses | 155,491 | Meaning distinctions |
| scholars | 20,490 | Researcher registry |
| publications | 16,725 | Academic bibliography |

---

## Day 4: The Ingestion Framework

### How data gets in

The project is on a **ingestion framework** (`ingestion/`) where every source has a typed connector. The old numbered scripts in `source-data/import-tools/` are retired; that folder is kept for reference but is not the canonical path. Detailed connector anatomy lives in the `gs-expert-integrations` skill (see `.claude/skills/gs-expert-integrations/`).

The framework:

```
ingestion/
  base.py          — SourceConnector, ModelConnector, RunContext, LoadStats
  runner.py        — run_connector() — wraps ETL + import_runs bookkeeping
  loader.py        — upsert_batch() — INSERT … ON CONFLICT
  registry.py      — discover_connectors() — auto-discovers ingestion.connectors.*
  dead_letters.py  — DeadLetterSink, DeadLetterCategory
  cli.py           — python -m ingestion.cli list|run|status|dead-letters
  connectors/      — one file per source
```

Key connectors:

| Connector | What |
|---|---|
| `lookup_tables.py` | Canon tables for normalization (runs first) |
| `annotation_runs.py` | Register data sources |
| `ogsl_signs.py` | OGSL sign list (3,367 signs) |
| `cdli_catalog.py` | CDLI artifact catalog (~353k records) |
| `atf_parser.py` | ATF → text_lines + tokens |
| `oracc_lemmatizations.py` | ORACC linguistic annotations |
| `oracc_glossaries.py` | ORACC glossary entries |
| `epsd2.py` | ePSD2 Sumerian dictionary |
| `oracc_lexical_glossaries.py` | ORACC glossaries (8 projects, 6 langs) |
| `translation_line_matcher.py` | Match translations to text_lines |
| `baby_lemmatizer.py` | ML lemmatization (BabyLemmatizer) |

### Running a connector

```bash
python -m ingestion.cli list                # show registered connectors
python -m ingestion.cli run cdli-catalog    # run one
python -m ingestion.cli status              # recent runs across all connectors
python -m ingestion.cli dead-letters cdli-catalog   # triage failures
```

A web admin dashboard is at `/admin/ingestion`.

### Conventions

```python
class MyConnector(SourceConnector):
    id = "my-connector"           # stable slug
    kind = "catalog"              # catalog | corpus | lexicon | annotation | lookup | derived
    runs_after = ["lookup-tables"]
    license = "CC-BY-4.0"

    def discover(self, ctx) -> SourceManifest: ...   # checksum for skip-if-unchanged
    def extract(self, ctx) -> Iterator[dict]: ...    # yield raw rows
    def transform(self, ctx, record) -> Iterator[dict]: ...  # validate, dead-letter, reshape
    def load(self, ctx, rows) -> LoadStats:
        return upsert_batch(ctx.db, table="my_table", rows=rows,
                            unique_key=["id"], policy=ConflictPolicy.UPDATE)
    def verify(self, ctx) -> None: ...               # sanity-check, raise on issue
```

`upsert_batch()` covers idempotency via UPDATE / SKIP / REPLACE policies. Bad rows go to dead-letters via `ctx.dead_letter(...)`; connectors never raise on per-record problems.

Source data lives in `source-data/sources/` (gitignored, ~25 GB). Each source directory has a `SETUP.md` explaining how to obtain the data.

---

## Day 5: Common Tasks

### Add an API Endpoint

1. Add route function in `api/routes/<domain>.py`
2. Add repository method in `api/repositories/<domain>_repo.py`
3. If new router, register it in `api/main.py`
4. Test at `http://api.glintstone.test/docs`

### Add a Web Page

1. Add route in `app/routes/<domain>.py`
2. Create template in `app/templates/<domain>/`
3. If new router, register in `app/main.py`
4. Add CSS in `app/static/css/pages/`
5. Add JS in `app/static/js/` if needed

### Add a Database Migration

1. Create `source-data/migrations/NNN_description.sql` (next number after 017)
2. Run as `wittkensis`:
   ```bash
   /opt/homebrew/Cellar/postgresql@17/17.8/bin/psql -h 127.0.0.1 -U wittkensis -d glintstone -f source-data/migrations/018_description.sql
   ```
3. GRANT permissions to `glintstone` user for any new tables/sequences
4. Update the schema YAML if it affects the data model

### Add a New Import Script

1. Create `NN_description.py` following existing patterns
2. Register an `annotation_run` before importing data
3. Use `ON CONFLICT` for idempotency
4. Use `ImportCheckpoint` for large imports
5. Support `--dry-run`, `--limit`, `--reset` flags

---

## Gotchas & Traps

### Python / psycopg

- **Rollback trap**: `conn.rollback()` undoes ALL uncommitted changes in the transaction, not just the failed statement. Never use try/except for UniqueViolation — use `NOT EXISTS` subqueries or `ON CONFLICT` instead.
- **macOS SSL**: Python's urllib/requests can fail with SSL errors on macOS. Use `subprocess.run(["curl", ...])` for external HTTP calls in import scripts.

### Jinja2 Templates

- **Dict method collision**: If a dict key is named `items`, `values`, `keys`, `get`, or `update`, dot notation (`dict.items`) calls the Python dict method instead of the key. Use bracket notation (`dict['items']`) or rename the key.
- **No `in` test**: `selectattr('val', 'in', list)` doesn't work — `'in'` is not a valid Jinja2 test. Use a loop with `namespace` to check membership.

### Data

- **Subscript semantics differ by language**: In Sumerian, `du3` is a different word than `du`. In Akkadian, subscripts are just sign disambiguation — `du3` normalizes to `du`. The tokenizer must handle both modes based on the ATF language header.
- **Competing interpretations are intentional**: Two scholars may lemmatize the same word differently. Both are stored. This is a feature.
- **Coverage is sparse**: Only ~2% of tablets are lemmatized. 35% have transliteration. 12% have translations. Expect NULLs everywhere.

### Infrastructure

- **Table ownership**: `wittkensis` owns tables. `glintstone` is the app user. Migrations run as `wittkensis`. New tables need explicit GRANTs.
- **Servers must be running**: The web app calls the API over HTTP. If the API is down, the web app shows errors, not empty pages.
- **OpenAlex API**: Uses "topics" not the deprecated "concepts". Topic T12307 = "Ancient Near East History".

---

## Key Vocabulary (Beyond Assyriology 101)

| Term | Meaning in this codebase |
|------|--------------------------|
| **annotation_run** | A batch of imported data with full provenance (source, version, timestamp) |
| **canon table** | Lookup table that normalizes messy source values to canonical forms |
| **cross-filter count** | Dynamic count showing results per filter option, excluding that dimension |
| **P-number** | CDLI artifact identifier, universal join key (e.g., P227657) |
| **Q-number** | CDLI composite text identifier — the abstract "work" vs. physical tablet |
| **stage** | Pipeline position: Captured (1) through Translated (5) |
| **unified lexical** | The three-table architecture (signs, lemmas, senses) from migration 008 |

---

## Who to Ask

The project is early-stage. There are no separate frontend/backend teams. You'll touch Python, SQL, Jinja2, CSS, and vanilla JS in the same week. Domain questions will come up constantly — `Assyriology 101.md` and the `PLANNING/Domain Research/` folder are your references. For linguistic questions that go deeper, the data model docs at `data-model/` have detailed commentary.

---

## First Week Checklist

- [ ] Run `ops/local/setup.sh` and get both servers running
- [ ] Open `http://app.glintstone.test` and browse tablets
- [ ] Open `http://api.glintstone.test/docs` and try a few endpoints
- [ ] Read `Assyriology 101.md` end to end
- [ ] Read through the five files listed in "Start Here"
- [ ] Connect to psql and run `SELECT * FROM artifacts WHERE p_number = 'P227657';`
- [ ] Run an import script in dry-run mode: `python 05_import_artifacts.py --dry-run --limit 10`
- [ ] Find a tablet with ATF, a translation, and lemmatization (try P001282)
- [ ] Trace a request from browser to database: pick a URL and follow the code
- [ ] Read `PLANNING/PRIVATE-TODO.md` for current priorities and open work

---

## Open Issues (as of 2026-02-23)

Status key: **DONE** = closed, **IN PROGRESS** = actively being worked, **IMPROVED** = recent meaningful commits

### Foundation & Infrastructure

| # | Issue | Labels | Status |
|---|-------|--------|--------|
| 1 | API Design | `help wanted` | Open |
| 2 | Caching | `enhancement` `help wanted` | Open |
| 3 | Schema Design & Data Quality | `help wanted` | Open — schema is solid through v2/migration 017, but multilingual edge cases remain |
| 4 | Pressure Testing, Unit Testing & QA | `help wanted` | Open — no test framework exists yet |
| 5 | Automated Data Ingestion | `help wanted` | Open — scripts run manually today |
| 7 | Server Configuration & Security | `help wanted` | Open — Hostinger VPS, Alpine, bot protection |
| 14 | Deployment & Versioning System | `help wanted` | Open |

### Data Migration (v2)

| # | Issue | Status |
|---|-------|--------|
| 17 | Lemmatization Matches | Open — 38% match rate, 99k "no line match" |
| 18 | CompVis Unmatched Tablets | Open |
| 19 | Surface Type Precision | Open |
| 20 | Citations | Open — many CDLI 302 redirects, CSV fallback planned |
| 21 | Remaining Import Steps | **DONE** — eBL annotations, collections, ORACC credits all landed |
| 22 | Citation Phases Remaining | Open — 8 of 12 citation scripts still pending (03-10) |
| 24 | Rewire Global Search | `bug` | Open |

### App UI & UX

| # | Issue | Labels | Status |
|---|-------|--------|--------|
| 9 | App UI v2 | `enhancement` | **IN PROGRESS** — ATF viewer done, composites done, dictionary Phase 1 done, Phase 2 (knowledge graph) schema deployed but API/UI pending |
| 6 | UI Systems Componentization | `enhancement` | Open — headers, dictionary surfaces inconsistent |
| 13 | Remove Tailwind Completely | `enhancement` | Open |
| 15 | Gut Check on Frontend Framework | `help wanted` | Open — stay Jinja2 or move to something else? |
| 33 | UX: Dictionary experience | `ux` | **IN PROGRESS** (assigned) — Phase 1 shipped, Phase 2 in progress |
| 34 | UX: Composite experience | `ux` | **IMPROVED** — composites tab implemented in #9 |
| 35 | UX: Useful app homepage | `ux` | Open |
| 36 | UX: ATF viewer revamp | `ux` | **IMPROVED** — new viewer with glassmorphism legend, interlinear glossing landed in #9 |
| 37 | UX: Knowledge sidebar | `ux` | Open |
| 38 | UX: Global semantic search | `ux` | Open |
| 39 | UX: Source overview | `ux` | Open |
| 40 | UX: Pipeline design system | `ux` | Open |
| 41 | UX: Citation/provenance/trust layer | `ux` | Open |
| 43 | UX: Dynamic Collections | `ux` | Open |

### Features & Enhancements

| # | Issue | Labels | Status |
|---|-------|--------|--------|
| 8 | Database Transparency | `enhancement` | Open |
| 10 | Marketing Page Updates | `enhancement` | Open (assigned) |
| 11 | Agentic Summaries (Anthropic API) | `help wanted` | Open |
| 12 | ML Integration | `enhancement` | Open |
| 16 | Tablet Thumbnail Generation | `help wanted` | Open |
| 25 | Semantic Global Search | `enhancement` `help wanted` | Open |
| 27 | Integrate new dictionary sources | (assigned) | Open |
| 32 | Account creation & management | `enhancement` | Open |
| 42 | Jupyter notebook templates | `enhancement` | Open |
| 46 | Multilingual UI (EN/DE/AR/FA) | `enhancement` | Open |

### Research & Decisions

| # | Issue | Labels | Status |
|---|-------|--------|--------|
| 23 | Consider GraphQL Integration | `enhancement` `help wanted` | Open |
| 26 | Docs: Assyriology Basics in 5 mins | `documentation` (assigned) | **IMPROVED** — `Assyriology 101.md` exists at repo root |
| 28 | Docs: Language Litmus Tests | `documentation` (assigned) | Open |
| 29 | App UI: Pull from API classes or HTTP? | `question` | Open — architectural decision on two-tier boundary |
| 30 | Teach Eric Proper GIT etiquette | `help wanted` `question` | Open |
| 31 | Usage telemetry | `question` | Open |
| 44 | Mathematica integration? | `question` | Open |
| 45 | Socialization: Identify 5 early participants | `research` (assigned) | Open |

### Good First Issues for New Engineers

If you're looking for where to start, these are approachable and high-value:

1. **#4 — Testing framework**: Set up pytest, write first tests for repository layer and API endpoints. Huge impact, well-scoped.
2. **#16 — Tablet thumbnails**: Image processing task, self-contained. Pillow is already a dependency.
3. **#13 — Remove Tailwind**: CSS cleanup, good way to learn the template/styling structure.
4. **#2 — Caching**: Profile slow queries (`get_filter_options()` hits 353k rows), add Redis or in-memory cache. Performance win.
5. **#6 — UI componentization**: Audit and unify Jinja2 macros, CSS patterns. Good way to learn the full frontend.
