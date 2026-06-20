"""Issue #55 quality baseline — evaluates summarize_artifact quality on a local sample.

Usage:
    python -m core.agent.eval baseline [OPTIONS]

Options:
    --n N           Total tablets to evaluate (default: 30)
    --strata        Split: sumerian,akkadian,sparse (default auto)
    --judge-model   Haiku model for LLM-as-judge (default: claude-haiku-4-5)
    --out FILE      JSON output path (default: /tmp/gs-eval-baseline.json)

Metrics:
    synthesis_rate   % of tablets that produced synthesis (vs. degraded fallback)
    citation_rate    % of syntheses with ≥2 [n] markers (grounding compliance)
    best_guess_rate  % that triggered the sparse / best-guess path
    judge_mean       Mean Haiku judge score 1-5 (specificity + factual grounding)
    judge_p25/p75    Quartile distribution

Cost estimate: ~$0.005/tablet for Sonnet summaries + ~$0.001/tablet for Haiku judge
At n=30: ~$0.18 total.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_JUDGE_MODEL = "claude-haiku-4-5"
_JUDGE_PROMPT = """You are evaluating an AI-generated summary of a cuneiform tablet for a scholarly database.

Rate the summary on these criteria (score 1–5):
1 = Completely generic, no artifact-specific content ("This is a tablet.")
2 = Mentions language/period but nothing specific
3 = Names specific facts (designation, genre, period) but shallow
4 = Grounds in specific facts, plausible scholarly description
5 = Specific, well-grounded, cites concrete details about content

Tablet P-number: {p_number}
Summary: {synthesis}

Respond with JSON only: {{"score": N, "reason": "one sentence"}}"""


@dataclass
class EvalResult:
    p_number: str
    language: str
    stratum: str  # sumerian | akkadian | sparse
    synthesis_success: bool
    synthesis_len: int
    citation_count: int
    best_guess: bool
    judge_score: float | None
    judge_reason: str | None
    error: str | None


def _fetch_candidates(
    conn, n_sumerian: int, n_akkadian: int, n_sparse: int
) -> list[tuple[str, str, str]]:
    """Return [(p_number, language, stratum), ...]."""
    rows: list[tuple[str, str, str]] = []

    with conn.cursor() as cur:
        # High-quality Sumerian (lemmatized + ATF)
        cur.execute(
            """
            SELECT a.p_number, a.language_normalized
            FROM artifacts a
            JOIN pipeline_status ps ON ps.p_number = a.p_number
            WHERE ps.linguistic_complete > 0 AND ps.reading_complete > 0
              AND a.language_normalized ILIKE 'Sumerian%%'
            ORDER BY ps.linguistic_complete DESC, a.p_number
            LIMIT %s
            """,
            (n_sumerian,),
        )
        rows.extend(
            (r["p_number"], r["language_normalized"], "sumerian")
            for r in cur.fetchall()
        )

        # High-quality Akkadian
        cur.execute(
            """
            SELECT a.p_number, a.language_normalized
            FROM artifacts a
            JOIN pipeline_status ps ON ps.p_number = a.p_number
            WHERE ps.linguistic_complete > 0 AND ps.reading_complete > 0
              AND a.language_normalized ILIKE 'Akkadian%%'
            ORDER BY ps.linguistic_complete DESC, a.p_number
            LIMIT %s
            """,
            (n_akkadian,),
        )
        rows.extend(
            (r["p_number"], r["language_normalized"], "akkadian")
            for r in cur.fetchall()
        )

        # Sparse (completeness ≤ 2 — stress-tests best-guess path)
        cur.execute(
            """
            SELECT a.p_number, COALESCE(a.language_normalized, 'Unknown') AS language_normalized
            FROM artifacts a
            JOIN pipeline_status ps ON ps.p_number = a.p_number
            WHERE (ps.linguistic_complete = 0 OR ps.linguistic_complete IS NULL)
              AND ps.reading_complete > 0
              AND (a.language_normalized ILIKE 'Sumerian%%' OR a.language_normalized ILIKE 'Akkadian%%')
            ORDER BY a.p_number
            LIMIT %s
            """,
            (n_sparse,),
        )
        rows.extend(
            (r["p_number"], r["language_normalized"], "sparse") for r in cur.fetchall()
        )

    return rows


def _judge_synthesis(
    anthropic_client, p_number: str, synthesis: str
) -> tuple[float, str]:
    """Ask Haiku to rate the synthesis quality. Returns (score, reason)."""
    prompt = _JUDGE_PROMPT.format(p_number=p_number, synthesis=synthesis[:800])
    try:
        msg = anthropic_client._client.messages.create(
            model=_JUDGE_MODEL,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        data = json.loads(raw)
        return float(data["score"]), str(data.get("reason", ""))
    except Exception as exc:
        logger.warning("Judge failed for %s: %s", p_number, exc)
        return 0.0, f"judge_error: {exc}"


def run_baseline(args: argparse.Namespace) -> int:
    from api.services import agent_service  # noqa: PLC0415
    from core.database import connect_one_shot  # noqa: PLC0415

    conn = connect_one_shot()

    n = args.n
    n_sumerian = n // 3
    n_akkadian = n // 3
    n_sparse = n - n_sumerian - n_akkadian

    candidates = _fetch_candidates(conn, n_sumerian, n_akkadian, n_sparse)
    if not candidates:
        print("No candidates found in local DB.", file=sys.stderr)
        return 1

    # Force-init the Anthropic client
    anthropic = agent_service._get_anthropic()

    print(f"Eval baseline: {len(candidates)} tablets")
    print(f"  {n_sumerian} sumerian | {n_akkadian} akkadian | {n_sparse} sparse")
    print(f"  judge model: {args.judge_model}")
    print()

    results: list[EvalResult] = []

    for i, (p_number, language, stratum) in enumerate(candidates, 1):
        print(
            f"  [{i}/{len(candidates)}] {p_number} ({stratum}) … ", end="", flush=True
        )
        try:
            resp = agent_service.do_summarize_artifact(
                conn,
                p_number=p_number,
                focus="general",
                interaction_id_int=None,
                interaction_id_str=f"eval-{p_number}",
            )
            card = resp.data
            synthesis = card.synthesis or ""
            citation_count = len(re.findall(r"\[\d+\]", synthesis))
            synthesis_success = bool(synthesis)
            best_guess = bool(card.best_guess)

            judge_score = None
            judge_reason = None
            if synthesis_success and len(synthesis) > 30:
                judge_score, judge_reason = _judge_synthesis(
                    anthropic, p_number, synthesis
                )

            result = EvalResult(
                p_number=p_number,
                language=language,
                stratum=stratum,
                synthesis_success=synthesis_success,
                synthesis_len=len(synthesis),
                citation_count=citation_count,
                best_guess=best_guess,
                judge_score=judge_score,
                judge_reason=judge_reason,
                error=None,
            )
            status = f"score={judge_score}" if judge_score else "degraded"
            print(status)
        except Exception as exc:
            # Reset any aborted transaction so subsequent tablets aren't poisoned
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"ERROR: {exc}")
            result = EvalResult(
                p_number=p_number,
                language=language,
                stratum=stratum,
                synthesis_success=False,
                synthesis_len=0,
                citation_count=0,
                best_guess=False,
                judge_score=None,
                judge_reason=None,
                error=str(exc),
            )

        results.append(result)
        if i < len(candidates):
            time.sleep(0.3)  # gentle back-off

    # Aggregate metrics
    n_total = len(results)
    n_success = sum(1 for r in results if r.synthesis_success)
    n_cited = sum(1 for r in results if r.citation_count >= 2)
    n_best_guess = sum(1 for r in results if r.best_guess)
    scores = [r.judge_score for r in results if r.judge_score is not None]
    judge_mean = sum(scores) / len(scores) if scores else 0.0

    sorted_scores = sorted(scores)
    p25 = sorted_scores[len(sorted_scores) // 4] if sorted_scores else 0.0
    p75 = sorted_scores[3 * len(sorted_scores) // 4] if sorted_scores else 0.0

    per_stratum: dict[str, dict] = {}
    for stratum in ("sumerian", "akkadian", "sparse"):
        s_results = [r for r in results if r.stratum == stratum]
        s_scores = [r.judge_score for r in s_results if r.judge_score is not None]
        per_stratum[stratum] = {
            "n": len(s_results),
            "synthesis_rate": sum(1 for r in s_results if r.synthesis_success)
            / max(len(s_results), 1),
            "judge_mean": sum(s_scores) / len(s_scores) if s_scores else None,
        }

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "n_total": n_total,
        "synthesis_rate": n_success / n_total,
        "citation_rate": n_cited / max(n_success, 1),
        "best_guess_rate": n_best_guess / n_total,
        "judge_mean": judge_mean,
        "judge_p25": p25,
        "judge_p75": p75,
        "judge_model": args.judge_model,
        "per_stratum": per_stratum,
        "results": [asdict(r) for r in results],
    }

    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)

    # Persist to DB so results survive restarts and can be trended.
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO eval_runs
                    (run_at, n_total, synthesis_rate, citation_rate,
                     best_guess_rate, judge_mean, judge_p25, judge_p75,
                     judge_model, per_stratum, results)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    summary["run_at"],
                    summary["n_total"],
                    summary["synthesis_rate"],
                    summary["citation_rate"],
                    summary["best_guess_rate"],
                    summary["judge_mean"],
                    summary["judge_p25"],
                    summary["judge_p75"],
                    summary["judge_model"],
                    json.dumps(summary["per_stratum"]),
                    json.dumps(summary["results"]),
                ),
            )
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not persist eval run to DB: %s", exc)

    print()
    print("── Baseline Results ──────────────────────────────────")
    print(
        f"  Synthesis rate:    {summary['synthesis_rate']:.0%}  ({n_success}/{n_total})"
    )
    print(f"  Citation rate:     {summary['citation_rate']:.0%}  (≥2 [n] markers)")
    print(
        f"  Best-guess rate:   {summary['best_guess_rate']:.0%}  (sparse path triggered)"
    )
    print(f"  Judge mean score:  {judge_mean:.2f}/5.0  (n={len(scores)})")
    print(f"  Judge P25/P75:     {p25:.1f} / {p75:.1f}")
    print()
    print("  Per stratum:")
    for s, m in per_stratum.items():
        jm = f"{m['judge_mean']:.2f}" if m["judge_mean"] is not None else "n/a"
        print(f"    {s:10s}  synthesis={m['synthesis_rate']:.0%}  judge={jm}")
    print()
    print(f"  Full results: {args.out}")

    conn.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m core.agent.eval",
        description="Quality evaluation for agentic summaries",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline_p = subparsers.add_parser("baseline", help="Run quality baseline eval")
    baseline_p.add_argument(
        "--n", type=int, default=30, help="Total tablets to evaluate"
    )
    baseline_p.add_argument("--judge-model", default=_JUDGE_MODEL)
    baseline_p.add_argument("--out", default="/tmp/gs-eval-baseline.json")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if args.command == "baseline":
        return run_baseline(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
