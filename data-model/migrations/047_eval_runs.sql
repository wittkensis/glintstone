-- Migration 047: Add eval_runs table for persisting quality baseline results.
--
-- Replaces the /tmp JSON output as the durable store for eval runs so results
-- survive restarts and can be trended over time. eval.py still writes JSON for
-- local inspection but also INSERTs a row here on every successful run.

CREATE TABLE IF NOT EXISTS eval_runs (
    id              BIGSERIAL PRIMARY KEY,
    run_at          TIMESTAMPTZ NOT NULL,
    n_total         INTEGER NOT NULL,
    synthesis_rate  REAL NOT NULL,
    citation_rate   REAL NOT NULL,
    best_guess_rate REAL NOT NULL,
    judge_mean      REAL,
    judge_p25       REAL,
    judge_p75       REAL,
    judge_model     TEXT NOT NULL,
    per_stratum     JSONB NOT NULL DEFAULT '{}',
    results         JSONB NOT NULL DEFAULT '[]'
);
