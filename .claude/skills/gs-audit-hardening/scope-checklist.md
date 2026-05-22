---
question: "What exactly should I check in each area of a Glintstone hardening audit?"
created: 2026-05-18
modified: 2026-05-18
context: "Companion to SKILL.md — the per-area question list that drives audit coverage. Each question maps to a class of finding discovered in past audits."
status: active
audience: [claude]
owners: [eric]
related_issues: ["#83"]
related_skills: [gs-audit-hardening]
supersedes: null
superseded_by: null
---

# Audit scope checklist

Work through every section. Answer each question explicitly — "yes/verified", "no/gap found", or "N/A". A gap is a finding; write it up.

---

## A. Deploy pipeline (`ops/deploy/deploy.sh`)

- [ ] Does the default `TARGETS` array match what actually runs in CI? (CI passes no args → default runs)
- [ ] Does every deploy target have a corresponding supervisor service that exists on the server?
- [ ] Is there a smoke-test for every deployed service? Does smoke failure trigger rollback for each?
- [ ] Does the rollback in the smoke-fail path restart all affected services (not just api/app)?
- [ ] Is `nginx -t` run before `nginx reload`? Is it in the sudoers allowlist?
- [ ] Is the `shared/marketing → shared/www` migration shim still needed, or can it be removed?
- [ ] Are all rsync `--exclude` patterns still accurate? Are there new dirs that should be excluded?
- [ ] Does the pre-deploy DB snapshot step only run for production? (Correct — staging doesn't need it.)
- [ ] Is the release-trim `KEEP_RELEASES` value sensible given disk space on the VPS?
- [ ] Can a staging and production deploy race in a way that corrupts either environment?

## B. Server provisioning (`provision.sh`, `provision-staging.sh`)

- [ ] Do all supervisor `command=` paths use `current/venv/bin/…` not a fixed absolute path?
- [ ] Do all supervisor `directory=` settings use the `current/` symlink?
- [ ] Are any supervisor services configured with `autostart=true` for a module that doesn't exist?
- [ ] Is the sudoers allowlist complete? Does it cover every `sudo` call in `deploy.sh`?
- [ ] Does `provision-staging.sh` create all the directories that `deploy.sh` expects to exist?
- [ ] Is the nightly prod→staging restore cron at a time that is: (a) deterministic, (b) after prod backup completes (~04:20 UTC)?
- [ ] Is `provision.sh` still accurate for re-provisioning a fresh VPS? Or has the live server drifted?

## C. nginx (`ops/deploy/nginx/*.conf`, `ops/local/nginx.conf`)

- [ ] Do all `alias` directives for static files follow the `current/` symlink?
- [ ] Are all nginx configs HTTP-only, or do they include TLS? If HTTP-only: does `deploy.sh` overwrite certbot-managed HTTPS configs on every deploy?
- [ ] Is the `www.` → apex redirect in its own `server {}` block (not inside an `if` inside the main block)?
- [ ] Does `staging.glintstone.org.conf` install when either `deploy_api` OR `deploy_app` is true (not just `deploy_app`)?
- [ ] Does the local `nginx.conf` use project-relative paths (not machine-specific `/Volumes/…` paths)?
- [ ] Are there any nginx configs in `ops/deploy/nginx/` that reference a service or domain not yet provisioned?
- [ ] Is `proxy_read_timeout` set appropriately for SSE endpoints (MCP)?
- [ ] Are `Cache-Control: immutable` headers on static assets paired with cache-busted URLs?

## D. Rollback (`ops/deploy/rollback.sh`)

- [ ] Does `rollback.sh` respect `APP_ENV` to target staging vs. production? (Uses correct `REMOTE_DIR` and service names for each.)
- [ ] Does it restart all services that were deployed, including MCP when relevant?
- [ ] Is the `|| true` on supervisorctl restart appropriate, or does it mask real failures?
- [ ] Is there a `nginx reload` after symlink swap (so static alias paths resolve correctly)?

## E. GitHub Actions (`.github/workflows/`)

- [ ] Does `test.yml` run ruff, mypy, and pytest? Or only a subset?
- [ ] Does `deploy.yml` validate secrets are non-empty before attempting SSH?
- [ ] Does `ssh-keyscan` use `-T` (timeout) and surface the error if VPS is unreachable?
- [ ] Does the concurrency group prevent racing deploys on the same ref?
- [ ] Does `promote.sh` verify CI passed for the specific SHA being promoted (not just the latest run on the branch)?
- [ ] Are GitHub environment protection rules configured correctly (production requires reviewer, staging does not)?

## F. MCP (`mcp/`)

- [ ] Does every module referenced in supervisor configs (`mcp.server_http`, etc.) exist in the codebase?
- [ ] Does every transport documented in the [Getting-Started-MCP wiki page](https://github.com/wittkensis/glintstone/wiki/Getting-Started-MCP) have a corresponding implementation?
- [ ] Is the `DEFAULT_BASE_URL` in `mcp/client.py` correct for the current API URL?
- [ ] Does `mcp/__init__.py` use `extend_path` to avoid shadowing the installed MCP SDK?
- [ ] Are all four tools smoke-tested against the live API? (semantic_search, summarize_artifact, interpret_token, submit_correction)

## G. Database indexes (`data-model/migrations/`, `api/repositories/`)

- [ ] Is there an index on `artifact_genres(p_number)`?
- [ ] Is there an index on `artifact_languages(p_number)`?
- [ ] Is there an index on `pipeline_status(p_number)` (or is it the PK)?
- [ ] Do trigram indexes exist on `artifacts.designation` and `artifacts.p_number`? Is `pg_trgm` extension installed?
- [ ] Are `COUNT(DISTINCT …)` queries in filter-option queries justified? (Check for unique constraints on junction tables.)
- [ ] Does `EXPLAIN ANALYZE` on the key queries show index scans (not seq scans) on filtered columns?
- [ ] Are any migrations creating duplicate indexes (same column, same table, different names across migrations)?

## H. Query performance (`api/repositories/artifact_repo.py`)

- [ ] Does `search()` run two queries (items + COUNT)? Could a window function replace the second?
- [ ] Does `get_filter_options()` run N sequential queries that could be a single CTE?
- [ ] Are filter-option results cached anywhere? What is the cache TTL?
- [ ] Do any queries use `ILIKE '%term%'` (leading wildcard) without a trigram index?
- [ ] Does the LATERAL join in `search()` for primary thumbnail add meaningful latency? (Explain analyze.)
- [ ] Is the `ORDER BY a.p_number` sort on the artifact list consistent for pagination? (Yes, PK sort is stable.)

## I. Web layer latency (`app/routes/tablets.py`, `api/routes/artifacts.py`)

- [ ] Does `tablet_list` make more than one API call? Are they sequential or parallel?
- [ ] Are any API calls made with a synchronous httpx client inside an async FastAPI route (or vice versa)?
- [ ] Is an httpx client instantiated per-request, or shared at app startup?
- [ ] Does the detail page make multiple sequential API calls? (auth/me, saved-items, artifact, debug)
- [ ] Is there a `/healthz` and `/health` endpoint on the app and API respectively? Do they check DB connectivity?

## J. Connection pool and concurrency (`core/database.py`)

- [ ] What is `max_size` for the pool? Is it sized for local Postgres (headroom up to ~100) or Neon (tight limits)?
- [ ] Are `min_size` and `max_size` configurable via env var, or hardcoded?
- [ ] Is there a pool timeout configured? What happens to a request that waits too long?
- [ ] Are keepalive settings still appropriate for local Postgres (vs. Neon WAN tuning)?

## K. Documentation freshness

- [ ] Does `CLAUDE.md` tech stack section accurately describe the current database (local Postgres on VPS, not Neon)?
- [ ] Does `CLAUDE.md` non-negotiables mention any decommissioned services or tools?
- [ ] Does `gs-expert-deployment/SKILL.md` pipeline diagram match the actual deploy flow?
- [ ] Does the [Engineer-Onboarding wiki page](https://github.com/wittkensis/glintstone/wiki/Engineer-Onboarding) directory map match the current project structure?
- [ ] Does the [Getting-Started-MCP wiki page](https://github.com/wittkensis/glintstone/wiki/Getting-Started-MCP) only document features that are actually implemented?
- [ ] Are `modified:` stamps on active skills within 60 days?
- [ ] Does `ops/deploy/DEPLOY.md` CI/CD diagram match what `test.yml` actually runs?

## L. Environment and configuration

- [ ] Does `.env.example` contain any keys that reference renamed, removed, or archived paths?
- [ ] Does `core/config.py` contain any default values that reference archived paths (`app-v0.1/`, etc.)?
- [ ] Are there any env vars in `.env.example` with no corresponding usage in `core/`, `api/`, or `app/`?
- [ ] Is `requirements-docs.txt` a subset of `requirements.txt`? (If yes, delete it.)

## M. Git hygiene

- [ ] Are any editor-specific files committed that should be gitignored (`*.code-workspace`, `.vscode/`, etc.)?
- [ ] Does `.gitignore` use current directory names (not renamed predecessors like `marketing/docs/`)?
- [ ] Does `check-docs-freshness.sh` reference directories that actually exist (`data-model/v2` → `data-model`)?
- [ ] Do pre-commit and pre-push hooks reflect current paths and contracts?
- [ ] Are there any large binary files accidentally tracked? (`git lfs check` or `find . -size +1M -not -path './.git/*'`)
