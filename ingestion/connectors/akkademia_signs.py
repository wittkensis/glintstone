"""Akkademia sign-recognition connector (backlog #535).

Runs the Akkademia model over each tablet's detected cuneiform signs and writes
the predicted sign-readings to `sign_recognitions`, each row attributed to a new
`annotation_run_id` (source_name = 'akkademia-signs').

WHAT AKKADEMIA ACTUALLY IS (spec-vs-reality, see migration 061):
    The #535 brief framed this as "image sign recognition". The shipped pip
    package is `akkadian` (repo gaigutherz/Akkademia, v1.0.12). It is NOT an
    image detector -- it is a *text* transliterator: given a string of Unicode
    cuneiform glyphs it predicts the reading of each sign (HMM / MEMM / BiLSTM).

        import akkadian.transliterate as akk
        akk.transliterate_bilstm("<unicode signs>")        -> "sza2 nak-ba ..."
        akk.transliterate_bilstm_top3("<unicode signs>")   -> (top1, top2, top3)

    So this connector feeds Akkademia the Unicode cuneiform signs Glintstone
    already has -- the CompVis sign-detection layer (`sign_annotations`) joined
    to `signs.utf8` -- and stores the model's predicted readings. The artifact
    image URL (the thing #535 wanted "recognized") is recorded on each row as
    `image_source_url` for provenance, even though Akkademia reads the glyphs,
    not the pixels. `bounding_box` is left NULL (reserved for a future
    image-based detector).

    Akkademia upstream pins Python 3.7.x + torch + allennlp 0.8.5, which will
    not install under Glintstone's Python 3.13 runtime. The connector therefore
    treats the dependency as OPTIONAL: if `akkadian` can't be imported it logs a
    clear message and yields nothing, exactly like the BabyLemmatizer connector's
    missing-`transformers` path. Nothing breaks; the run is a clean no-op.

CONFIDENCE: Akkademia's public API returns no probability. We derive a coarse
confidence from which of the top-3 BiLSTM candidates a reading came from
(rank 1 = 0.95, rank 2 = 0.6, rank 3 = 0.3). The full ranked list is stored in
`alternatives` so a scholar can see the competing readings.

IDEMPOTENT: skips any artifact already present in the LATEST akkademia-signs run.
Re-running is a no-op; a fresh run (new annotation_run_id) re-predicts and the
new rows coexist with the old (competing interpretations are a feature).

Depends on: annotation-runs (seeds the akkademia-signs source row),
compvis sign annotations (provides the Unicode signs + image link).
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ingestion.base import ConflictPolicy, LoadStats, ModelConnector, RunContext
from ingestion.loader import upsert_batch

# How many artifacts to transliterate per run. The current corpus has ~81
# tablets with detected signs and ~100 with images; this ceiling keeps a single
# run bounded while scaling automatically as #524 scrapes more images.
MAX_ARTIFACTS_PER_RUN = 500

# Rank -> derived confidence for a top-3 BiLSTM candidate. Akkademia exposes no
# raw probability, so this is a deliberately coarse, monotonic encoding.
RANK_CONFIDENCE = {0: 0.95, 1: 0.6, 2: 0.3}


def _split_readings(transliteration: str) -> list[str]:
    """Split an Akkademia transliteration string into per-sign readings.

    Akkademia separates signs within a word by '-' and words by spaces, e.g.
    'sza2 nak-ba-i-mu-ru iz-di'. We flatten to a per-sign list, dropping empties.
    """
    out: list[str] = []
    for word in (transliteration or "").split():
        for sign in word.split("-"):
            sign = sign.strip()
            if sign:
                out.append(sign)
    return out


class AkkademiaSignsConnector(ModelConnector):
    id = "akkademia-signs"
    display_name = "Akkademia Sign Recognition"
    description = (
        "Predicts cuneiform sign-readings with the Akkademia BiLSTM model "
        "(pip package `akkadian`) over each tablet's detected signs. Writes to "
        "sign_recognitions with a per-run annotation_run_id."
    )
    kind = "model"
    runs_after = ["annotation-runs"]
    upstream_url = "https://github.com/gaigutherz/Akkademia"
    license = "MIT"
    citation = (
        "Gordin, S., Gutherz, G., Elazary, A., Romach, A., Jimenez, E., "
        "Berant, J., & Cohen, Y. (2020). Reading Akkadian cuneiform using "
        "natural language processing. PLOS ONE 15(10): e0240511."
    )

    model_name = "akkademia"
    model_version = "1.0.12"
    hf_repo = None

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _scalar(row, key, idx):
        return row[key] if isinstance(row, dict) else row[idx]

    def _annotation_run_id(self, ctx: RunContext) -> int | None:
        """Resolve the canonical akkademia-signs annotation_runs row id.

        The annotation-runs connector seeds this row. If it's missing (the
        connector hasn't run), we return None and skip -- we never invent an
        unattributed run, because attribution is structural.
        """
        run = ctx.db.execute(
            "SELECT id FROM annotation_runs WHERE source_name = %s LIMIT 1",
            ("akkademia-signs",),
        ).fetchone()
        if not run:
            ctx.error(
                "akkademia_signs.missing_annotation_run",
                message=(
                    "annotation_runs has no 'akkademia-signs' row; run the "
                    "annotation-runs connector first."
                ),
            )
            return None
        return self._scalar(run, "id", 0)

    def _already_recognized(self, ctx: RunContext, run_id: int) -> set[str]:
        """P-numbers already written under THIS akkademia-signs run (idempotency)."""
        rows = ctx.db.execute(
            "SELECT DISTINCT p_number FROM sign_recognitions WHERE annotation_run_id = %s",
            (run_id,),
        ).fetchall()
        return {self._scalar(r, "p_number", 0) for r in rows}

    def _artifacts_with_signs(self, ctx: RunContext) -> list[dict]:
        """Artifacts that have BOTH detected cuneiform signs and an image.

        Builds, per artifact, the ordered Unicode cuneiform string Akkademia
        needs by joining the CompVis sign-detection layer to signs.utf8, plus a
        representative image URL for provenance. Only artifacts whose signs
        resolve to a Unicode glyph are returned (Akkademia needs real glyphs).
        """
        rows = ctx.db.execute(
            """
            WITH ordered AS (
                SELECT s.p_number,
                       sg.utf8 AS glyph,
                       sa.line_number,
                       sa.position_in_line,
                       sa.id AS ann_id
                FROM sign_annotations sa
                JOIN surface_images si ON sa.surface_image_id = si.id
                JOIN surfaces s        ON si.surface_id = s.id
                JOIN signs sg          ON sa.sign_id = sg.sign_id
                WHERE sg.utf8 IS NOT NULL AND sg.utf8 <> ''
            ),
            img AS (
                SELECT p_number,
                       (ARRAY_AGG(r2_key ORDER BY display_order, id))[1] AS r2_key,
                       (ARRAY_AGG(source_url ORDER BY display_order, id))[1] AS source_url
                FROM artifact_images
                GROUP BY p_number
            )
            SELECT o.p_number,
                   STRING_AGG(o.glyph, '' ORDER BY o.line_number, o.position_in_line, o.ann_id) AS glyphs,
                   MAX(img.r2_key)    AS r2_key,
                   MAX(img.source_url) AS source_url
            FROM ordered o
            LEFT JOIN img ON img.p_number = o.p_number
            GROUP BY o.p_number
            ORDER BY o.p_number
            LIMIT %s
            """,
            (MAX_ARTIFACTS_PER_RUN,),
        ).fetchall()
        out: list[dict] = []
        for r in rows:
            out.append(
                {
                    "p_number": self._scalar(r, "p_number", 0),
                    "glyphs": self._scalar(r, "glyphs", 1),
                    "r2_key": self._scalar(r, "r2_key", 2),
                    "source_url": self._scalar(r, "source_url", 3),
                }
            )
        return out

    @staticmethod
    def _image_url(r2_key, source_url) -> str | None:
        """Prefer the public R2 URL; fall back to the scraped CDLI source URL."""
        if r2_key:
            try:
                from core.storage import public_url_for_key

                return public_url_for_key(r2_key)
            except Exception:
                pass
        return source_url

    # ------------------------------------------------------------------ predict

    def predict(self, ctx: RunContext) -> Iterator[dict]:
        try:
            import akkadian.transliterate as akk  # type: ignore[import]
        except Exception as exc:  # ImportError, or torch/allennlp load failure
            ctx.error(
                "akkademia_signs.missing_dependency",
                message=(
                    "akkadian not importable; install with `pip install akkadian` "
                    "(needs Python 3.7.x + torch + allennlp 0.8.5). Skipping run."
                ),
                error=str(exc),
            )
            return

        run_id = self._annotation_run_id(ctx)
        if run_id is None:
            return

        # Bind this model to model_registry for cross-run provenance (parity with
        # the BabyLemmatizer connector). The annotation_run_id remains the
        # structural attribution written on every row.
        try:
            self.register_model_version(ctx.db)
        except Exception as exc:
            ctx.warn("akkademia_signs.model_registry_skip", error=str(exc))

        done = self._already_recognized(ctx, run_id)
        artifacts = self._artifacts_with_signs(ctx)
        ctx.info(
            "akkademia_signs.candidates",
            total=len(artifacts),
            already_done=len(done),
        )

        for art in artifacts:
            p_number = art["p_number"]
            if p_number in done:  # idempotent skip
                continue
            glyphs = art["glyphs"]
            if not glyphs:
                continue

            try:
                top3 = akk.transliterate_bilstm_top3(glyphs)
            except Exception as exc:
                ctx.warn(
                    "akkademia_signs.inference_failed",
                    p_number=p_number,
                    error=str(exc),
                )
                continue

            # transliterate_bilstm_top3 returns a (top1, top2, top3) tuple of
            # whole-string transliterations. Split each into per-sign readings
            # and align by position so each sign gets its ranked alternatives.
            if isinstance(top3, (list, tuple)):
                ranked = [_split_readings(t) for t in top3]
            else:
                ranked = [_split_readings(str(top3))]
            if not ranked or not ranked[0]:
                continue

            top = ranked[0]
            image_url = self._image_url(art.get("r2_key"), art.get("source_url"))
            import json

            for idx, sign_label in enumerate(top):
                alternatives = [
                    lst[idx]
                    for lst in ranked
                    if idx < len(lst) and lst[idx]
                ]
                yield {
                    "p_number": p_number,
                    "sign_index": idx,
                    "sign_label": sign_label,
                    "source_glyph": None,
                    "confidence": RANK_CONFIDENCE.get(0, 0.95),
                    "alternatives": json.dumps(alternatives, ensure_ascii=False)
                    if len(alternatives) > 1
                    else None,
                    "bounding_box": None,
                    "image_source_url": image_url,
                    "annotation_run_id": run_id,
                }

    # --------------------------------------------------------------------- load

    def load(self, ctx: RunContext, rows: Iterable[dict]) -> LoadStats:
        return upsert_batch(
            ctx.db,
            table="sign_recognitions",
            rows=rows,
            unique_key=["p_number", "annotation_run_id", "sign_index"],
            policy=ConflictPolicy.SKIP,
            batch_size=500,
        )

    # ------------------------------------------------------------------- verify

    def verify(self, ctx: RunContext) -> None:
        row = ctx.db.execute(
            "SELECT COUNT(*) AS n FROM annotation_runs WHERE source_name = %s",
            ("akkademia-signs",),
        ).fetchone()
        n = self._scalar(row, "n", 0)
        if n == 0:
            raise AssertionError(
                "annotation_runs has no 'akkademia-signs' row; run annotation-runs first."
            )
        ctx.info("akkademia_signs.verify", annotation_runs_rows=n)
