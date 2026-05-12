"""BabyLemmatizer connector — proves ModelConnector extensibility.

Runs the BabyLemmatizer (HuggingFace) over uninferred tokens and writes
lemmatizations with a model_registry FK. This connector is the reference
implementation for ML model connectors in Glintstone.

BabyLemmatizer: https://huggingface.co/cltl/babylemmatizer
  Input:  token form + POS tag
  Output: citation_form, guide_word, pos

Depends on: atf-parser (tokens must exist), annotation-runs
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, ModelConnector, RunContext
from ingestion.loader import upsert_batch

BATCH_SIZE = 256


class BabyLemmatizerConnector(ModelConnector):
    id = "baby-lemmatizer"
    display_name = "BabyLemmatizer v2 (HuggingFace)"
    description = (
        "Lemmatizes uninferred Sumerian/Akkadian tokens using the BabyLemmatizer "
        "transformer model. Writes to lemmatizations with model_registry FK."
    )
    kind = "model"
    runs_after = ["atf-parser", "annotation-runs"]
    upstream_url = "https://huggingface.co/cltl/babylemmatizer"
    license = "CC-BY-SA-4.0"
    citation = (
        "Bogaert, P., & Vossen, P. (2022). BabyLemmatizer: A Lemmatizer for "
        "Low-Resource Languages. In Proceedings of LaTeCH-CLfL."
    )

    model_name = "babylemmatizer"
    model_version = "2.0"
    hf_repo = "cltl/babylemmatizer"

    def predict(self, ctx: RunContext) -> Iterator[dict]:
        """Yield lemmatization dicts for tokens that have no existing lemma.

        Fetches tokens in batches from the DB, runs BabyLemmatizer inference,
        and yields one dict per token. Skips tokens that already have a
        lemmatization to keep re-runs idempotent.
        """
        try:
            from transformers import pipeline  # type: ignore[import]
        except ImportError:
            ctx.error(
                "baby_lemmatizer.missing_dependency",
                message="transformers not installed; run: pip install transformers",
            )
            return

        ctx.info("baby_lemmatizer.load_model", hf_repo=self.hf_repo)
        lemmatizer = pipeline("text2text-generation", model=self.hf_repo)

        # Find tokens without any existing lemmatization
        ctx.info("baby_lemmatizer.fetch_uninferred")
        tokens = ctx.db.execute(
            """
            SELECT t.id, t.gdl_json, t.lang
            FROM tokens t
            LEFT JOIN lemmatizations l ON l.token_id = t.id
            WHERE t.gdl_json IS NOT NULL AND l.id IS NULL
            LIMIT 100000
            """
        ).fetchall()
        ctx.info("baby_lemmatizer.uninferred_count", count=len(tokens))

        model_id = self.register_model_version(ctx.db)

        for i in range(0, len(tokens), BATCH_SIZE):
            batch = tokens[i : i + BATCH_SIZE]
            forms = []
            for token in batch:
                import json

                gdl = token["gdl_json"] if isinstance(token, dict) else token[1]
                try:
                    form = json.loads(gdl).get("frag", "")
                except (ValueError, TypeError):
                    form = ""
                forms.append(form)

            # Run inference — BabyLemmatizer expects "form [LANG]" input
            inputs = [
                f"{form} [{(token['lang'] if isinstance(token, dict) else token[2]) or 'und'}]"
                for form, token in zip(forms, batch)
            ]
            try:
                results = lemmatizer(inputs, max_length=64)
            except Exception as exc:
                ctx.warn(
                    "baby_lemmatizer.inference_failed", error=str(exc), batch_start=i
                )
                continue

            for token, result in zip(batch, results):
                token_id = token["id"] if isinstance(token, dict) else token[0]
                generated = result[0]["generated_text"] if result else ""
                # BabyLemmatizer output format: "cf[gw//gw]POS"
                # Parse best-effort; treat full output as citation_form if unparseable
                cf, gw, pos = _parse_lemma_output(generated)
                if not cf:
                    continue
                yield {
                    "token_id": token_id,
                    "citation_form": cf,
                    "guide_word": gw,
                    "pos": pos,
                    "confidence": 0.8,
                    "annotation_run_id": None,
                    "model_id": model_id,
                    "signature": generated,
                }

            if i % (BATCH_SIZE * 10) == 0 and i > 0:
                ctx.info("baby_lemmatizer.progress", processed=i, total=len(tokens))

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        # Strip model_id (not a column in lemmatizations) before inserting
        def _strip_model_id(rows_iter):
            for row in rows_iter:
                row.pop("model_id", None)
                yield row

        return upsert_batch(
            ctx.db,
            table="lemmatizations",
            rows=_strip_model_id(rows),
            unique_key=["token_id"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM model_registry WHERE name = %s",
            (self.model_name,),
        ).fetchone()
        n = row["n"] if isinstance(row, dict) else row[0]
        if n == 0:
            raise AssertionError(f"model_registry has no row for {self.model_name!r}")
        ctx.info("baby_lemmatizer.verify", model_registry_rows=n)


def _parse_lemma_output(text: str) -> tuple[str | None, str | None, str | None]:
    """Parse BabyLemmatizer output: 'cf[gw//gw]POS' → (cf, gw, pos)."""
    import re

    m = re.match(r"^([^\[]+)\[([^/]+)//[^\]]+\](\w+)", text.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    # Fallback: treat whole output as citation form
    return text.strip() or None, None, None
