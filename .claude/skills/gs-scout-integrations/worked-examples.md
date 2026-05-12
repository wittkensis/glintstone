---
question: "Take the 5 HuggingFace candidates I mentioned — how does each score against the integration framework?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul using 5 HuggingFace projects the user surfaced: Thalesian/cuneiformBase-400m, praeclarum/cuneiform, NAQarabash/nllb-akkadian-cuneiform, boatbomber/CuneiformPhotosMSII, FactGridCuneiform/lemma-model. Scoring is from URLs + names only; actual integration would require pulling model cards."
status: draft
audience: [claude, engineers]
owners: [eric]
related_issues: ["#11", "#12", "#27"]
related_skills: [gs-scout-integrations]
supersedes: null
superseded_by: null
---

# Worked examples — 5 HF candidates

Each scored against the 5-section framework in [SKILL.md](SKILL.md). These are first-pass evaluations from URL/name only. Each should be re-scored after pulling the actual model card and license — leave `status: draft` until that's done.

---

## 1. `Thalesian/cuneiformBase-400m`

URL: https://huggingface.co/Thalesian/cuneiformBase-400m

### Fit
Likely a foundation language model trained on cuneiform-related text. If it's a general LM (Akkadian/Sumerian transliterations), it doesn't directly close a Tier 1 gap, but it could underpin downstream tasks: lemmatization, translation, semantic search embeddings.

### Integration path
**Pattern 2 — ML model.** Lives in `ml/service/cuneiform-base/`. Wrap `inference.py` around the model; expose `embed(text) -> vector` and / or `complete(text) -> text` endpoints.

### Sketch
```python
# ml/service/cuneiform_base/inference.py
class CuneiformBase:
    def __init__(self, model_id="Thalesian/cuneiformBase-400m"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id)

    def embed(self, text: str) -> list[float]:
        ...
```

### UI placement
Surface 6 (Global / Semantic search) if embeddings power semantic search. Surface 5 (Dictionary) for lemma similarity. Could power Surface 2 (Knowledge Bar) "see similar" sections.

### Risks
- **License**: unknown from URL; HF default is often Apache 2.0 or research-only. **Verify before commit.**
- **Size**: 400m params — non-trivial inference cost. Use Modal or batched offline embeddings, not per-request inference.
- **Training data**: if trained on the same corpora we ingest, embedding similarity may circularly reflect ingest decisions. Document.
- **Attribution**: every embedding written to DB carries `annotation_run_id` = `cuneiformBase-400m@<version>`.

---

## 2. `praeclarum/cuneiform`

URL: https://huggingface.co/praeclarum/cuneiform

### Fit
Name alone is too generic. Could be a model or a tokenizer or a dataset. **Pull the model card before scoring properly.**

If it's a transliteration/OCR model: closes Tier 1 (Sign detection / OCR).
If it's a Unicode-cuneiform language model: similar profile to Thalesian above.

### Integration path
**Probably Pattern 2 (ML model).** Could be Pattern 1 (dataset) — check.

### Sketch
TBD until card is read. Stub.

### UI placement
Depends on what it produces:
- Sign boxes → Surface 1 (Tablet detail) overlay
- Text predictions → Surface 3 (Translation Builder)

### Risks
- Sparse documentation on HF user `praeclarum` — verify it's maintained
- License unknown

---

## 3. `NAQarabash/nllb-akkadian-cuneiform`

URL: https://huggingface.co/NAQarabash/nllb-akkadian-cuneiform

### Fit
NLLB-family (No Language Left Behind) fine-tuned for Akkadian ↔ cuneiform. **Closes Tier 2** (Translations beyond English) if it translates Akkadian ATF / normalized text into modern languages. Also potentially Tier 1 (lemmatization-adjacent if it does morphologically aware translation).

### Integration path
**Pattern 2 — ML model.** Live inference for the Translation Builder. Optionally Pattern 1 too: pre-compute translations for the tablets that lack them, store as a `babylemmatizer`-style annotation run.

### Sketch
```python
# ml/service/nllb_akkadian/inference.py
class NLLBAkkadian:
    def translate(self, source_text: str, target_lang: str = "eng_Latn") -> dict:
        # NLLB takes source/target language codes
        # Return: {"translation": "...", "confidence": 0.87}
```

### UI placement
**Primary**: Surface 3 (Translation Builder) — "machine suggestion" track alongside scholar translations, marked with model + confidence.
**Secondary**: Surface 1 (Tablet detail) — "auto-translation available" badge for un-translated tablets.

### Risks
- **License**: NLLB is CC BY-NC 4.0 (non-commercial). Fine-tuned derivatives often inherit this. **If NC, incompatible with our CC BY-SA distribution. Stop.**
- **Hallucination**: NLLB-class models confidently produce plausible-but-wrong translations for low-resource languages. NEVER auto-publish without confidence + scholar review.
- Output language inventory may be limited — check what target languages are supported.

---

## 4. `boatbomber/CuneiformPhotosMSII`

URL: https://huggingface.co/datasets/boatbomber/CuneiformPhotosMSII

### Fit
A photo dataset. **Closes Tier 1** (Sign detection / OCR) as training data, or as additional source images we don't have. The "MSII" suggests a multi-spectral capture (Middle Series II? Multi-Spectral Imaging II?) — distinctive, likely valuable.

### Integration path
**Pattern 1 — ingestion connector** for the images themselves (write to Cloudflare R2 once it's ready; otherwise local filesystem).

If we're consuming the dataset to train OUR own models, it's a Pattern 1 + ML training pipeline.

### Sketch
```python
# ingestion/connectors/hf_cuneiform_photos.py
class CuneiformPhotosConnector(SourceConnector):
    id = "hf-cuneiform-photos-msii"
    kind = "annotation"
    upstream_url = "https://huggingface.co/datasets/boatbomber/CuneiformPhotosMSII"

    def extract(self, ctx):
        ds = load_dataset("boatbomber/CuneiformPhotosMSII")
        for row in ds["train"]:
            yield {"image_id": row["id"], "p_number": row.get("p_number"), ...}
```

Need to know:
- Does it have P-number labels? If yes, join key is solved.
- If not: image-similarity matching against CDLI's catalog (heavy lift).

### UI placement
**Surface 1** (Tablet detail) — additional image variants if P-number-keyed.
**Surface 4** (Browse Tablets) — thumbnail fallback for tablets without CDLI photos.

### Risks
- **License**: most HF datasets are CC BY or CC0; verify.
- **Image storage**: feed into the Cloudflare R2 plan (`gs-expert-deployment/storage.md`).
- **Resolution / quality**: low-res training data ≠ scholarly reference image. Mark provenance clearly.
- **Duplication with CDLI**: if it's a re-shoot of CDLI tablets, decide which is canonical for display.

---

## 5. `FactGridCuneiform/lemma-model`

URL: https://huggingface.co/FactGridCuneiform/lemma-model

### Fit
**Closes Tier 1 (lemmatization coverage)** — by far the most directly impactful candidate of the five. FactGrid is a Wikibase project; a cuneiform lemma model from that ecosystem is interesting because Wikibase identifiers could bridge our lemmas to broader linked-open-data.

### Integration path
**Pattern 2 — ML model** for lemmatization inference. Lives alongside BabyLemmatizer in `ml/service/factgrid_lemma/`. Wrap, expose `lemmatize(form, language) -> [candidates]`.

**Plus Pattern 4 (reference data)** if it emits FactGrid QIDs — seed a `factgrid_qids` lookup table to bridge our `lexical_lemmas.id` ↔ FactGrid QID.

### Sketch
```python
# ml/service/factgrid_lemma/inference.py
class FactGridLemmatizer:
    def predict(self, form: str, language: str) -> list[dict]:
        # Returns ranked lemma candidates with confidence
        # Plus FactGrid QID if available
        return [{"lemma": "šarru", "confidence": 0.91, "factgrid_qid": "Q12345"}]
```

### UI placement
**Surface 3** (Translation Builder) — alternate lemma track alongside ORACC + BabyLemmatizer.
**Surface 2** (Knowledge Bar) — "FactGrid says" with link out to the FactGrid item.
**Surface 5** (Dictionary) — entry-level FactGrid backlink.

### Risks
- **License**: FactGrid is generally CC0 (Wikibase ethos). Verify model itself.
- **Quality vs BabyLemmatizer**: needs head-to-head evaluation before promoting in UI. Treat as competing-interpretation (per the data model: store both with confidence).
- **FactGrid as authority**: tying our lemmas to QIDs creates a dependency. Choose carefully which lemmas get which QID; allow many-to-one.

---

## Cross-cutting recommendation

If only one of these gets prioritized, **start with #5 (`FactGridCuneiform/lemma-model`)** — directly closes the biggest gap (lemmatization coverage) and the QID bridge is high-leverage for future LOD work.

Pair it with #3 (NLLB) for Translation Builder if license permits.

Defer #1 (`Thalesian/cuneiformBase-400m`) and #2 (`praeclarum/cuneiform`) until model cards confirm specifics.

#4 (`boatbomber/CuneiformPhotosMSII`) is independent of the others and depends on Cloudflare R2 readiness.

---

## When this file gets stale

- A scored candidate ships → flip its section to `status: shipped` and link to the connector
- A score changes after reading the model card → update the section, bump `modified:`
- A new candidate is mentioned → add a section

This file is `status: draft` until at least one card has been read and the scores updated.
