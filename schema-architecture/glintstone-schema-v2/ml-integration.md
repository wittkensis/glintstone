# ML Model Integration

Glintstone treats machine learning models as annotation sources, not oracles. Every ML-generated record carries the same provenance infrastructure as human-produced annotations: an `annotation_run_id` linking to the model version, configuration, and confidence score. This means ML output and human scholarship coexist in the same tables, are queryable by the same mechanisms, and can be compared directly.

---

## BabyLemmatizer

**What it does**: POS-tagging and lemmatization of transliterated cuneiform text using sequence-to-sequence neural networks (OpenNMT encoder-decoder). The current state-of-the-art tool for automated cuneiform lemmatization.

**Reference**: Sahala & Linden, 2023

### Where It Fits in the Pipeline

BabyLemmatizer operates between the Reading layer (transliteration) and the Linguistic layer (lemma + POS):

```
Image > OCR > ATF > [BabyLemmatizer] > Lemmas > Translation
                     Reading layer       Linguistic layer
```

It takes transliterated text as input and produces lemmatization (dictionary headword mapping) and POS tags as output. It does not operate on images or produce translations.

### Tokenization Modes

BabyLemmatizer defines three tokenization strategies, each designed for different writing systems:

| Mode | Languages | Behavior |
|------|-----------|----------|
| 0: Logo-syllabic unindexed | Akkadian, Elamite, Hittite, Urartian, Hurrian | Syllabic signs become character sequences; logograms preserved as tokens. Subscript numbers stripped (du3 becomes du) because subscripts are disambiguation devices, not phonological. |
| 1: Logo-syllabic indexed | Sumerian | Preserves subscript numbers because they carry lexical meaning. du (go), du3 (build), and du7 (perfect) are different words. |
| 2: Character sequences | Non-cuneiform (Greek, Latin) | Standard character-level tokenization. |

The tokenization mode is a pre-processing contract between the data and the model. Glintstone stores the raw transliterated form as canonical on `token_readings.form` and can derive tokenized representations on demand.

### CoNLL-U Interchange Format

BabyLemmatizer uses CoNLL-U as its input/output format. This is the closest thing cuneiform NLP has to a standard, also used by CDLI and MTAAC.

Mapping from CoNLL-U fields to Glintstone schema:

| CoNLL-U Field | Schema Target | Notes |
|---------------|---------------|-------|
| ID | `tokens.position` | 1-indexed position in line |
| FORM | `token_readings.form` | Surface form as transliterated |
| LEMMA | `lemmatizations.citation_form` | Dictionary headword |
| UPOS | `lemmatizations.pos` | Universal POS tag (N, V, ADJ, etc.) |
| XPOS | `lemmatizations.epos` | ORACC-specific POS (more granular) |
| FEATS | `morphology` table | Key=Value pairs decomposed into language-specific slots |
| MISC | Various | Damage info, confidence scores |

### What CoNLL-U Does Not Capture

The schema is deliberately richer than CoNLL-U:

- **Sign-level data**: CoNLL-U operates at word level. The graphemic layer (individual signs, visual forms, damage states) sits below CoNLL-U's granularity.
- **Mixed-language writing**: CoNLL-U has one FORM field. It does not represent that `LUGAL-us` is a Sumerian logogram + Hittite phonetic complement. The schema tracks this via `token_readings.sign_function`.
- **Alternative analyses**: CoNLL-U gives one LEMMA. The schema stores competing lemmatizations with confidence scores via `lemmatizations` (multiple rows per token_id).
- **Physical context**: CoNLL-U has no concept of the tablet, surface, or image. The schema's full hierarchy (artifact > surface > text_line > token) provides this.

CoNLL-U is the interchange format for import/export. The schema is the internal data model.

### Accuracy and Confidence

- **In-vocabulary forms**: 94-96% accuracy (Akkadian)
- **Out-of-vocabulary forms**: 68-84% accuracy depending on language/dialect
- **LLM comparison** (EvaCun 2025): LLMs achieved ~90% in-vocabulary but only ~9% OOV, far worse than BabyLemmatizer

BabyLemmatizer's post-correction module assigns confidence by checking neural output against a dictionary:
1. Form-lemma pair attested in training data: high confidence
2. Lemma in dictionary but this form not attested: medium confidence
3. Entirely novel lemma: low confidence, flagged for review

POS errors propagate into lemmatization errors (chained architecture), so confidence scoring accounts for both stages.

### Training Data

BabyLemmatizer is trained on ORACC corpus exports -- the same human-annotated data that Glintstone imports. This creates a virtuous cycle: better ORACC annotations produce better BabyLemmatizer models, which can then annotate the 98% of texts that ORACC has not yet reached.

Separate models exist for:
- Neo-Assyrian Akkadian (richest training data)
- Other Akkadian dialects (Standard Babylonian, Old Babylonian)
- Literary Sumerian vs. administrative Sumerian (different vocabulary distributions)

No pretrained models exist for Hittite or Elamite. The tokenization modes support these languages, but training corpora are insufficient.

### Schema Integration

BabyLemmatizer output enters Glintstone through:

1. **annotation_runs**: A record with `source_type='model'`, `source_name='BabyLemmatizer v{version}'`, `method='ML_model'`, and `config_snapshot` containing tokenization mode, tagger context window, and model name.
2. **lemmatizations**: One row per token with `citation_form`, `pos`, `confidence`, and `annotation_run_id`. Stored alongside any existing ORACC human lemmatization as a competing analysis.
3. **morphology**: If FEATS are produced, decomposed into language-specific slots (root, stem, tense for Akkadian; conjugation_prefix, dimensional_prefixes for Sumerian).

The `is_consensus` flag is NOT automatically set on BabyLemmatizer output. Human ORACC annotations retain consensus by default. BabyLemmatizer becomes consensus only for tokens with no human annotation, or when explicitly promoted by editorial decision.

---

## eBL OCR (DETR Sign Detection)

**What it does**: Detects and classifies cuneiform signs in tablet photographs using a Deformable DETR + ResNet-50 architecture.

**Training**: 173 sign classes, 1000 epochs on eBL cuneiform-ocr-data annotations
**Performance**: mAP@50 = 43.1%
**Current status**: Trained model available. Runs in mock mode on macOS ARM64 due to mmcv library incompatibility.

### Schema Integration

- **Output**: Bounding box coordinates + predicted sign class + confidence score
- **Schema target**: `sign_annotations` table
- **Coordinate system**: Pixel-absolute from model, converted to percentage-based (0-100%) for resolution independence
- **Sign resolution**: Model outputs CompVis/eBL class names, resolved to OGSL sign_id via MZL/ABZ concordance
- **Provenance**: `annotation_runs` with `source_type='model'`, `source_name='eBL DETR v{version}'`, `method='ML_model'`

### Inference Service

The ML service runs as a FastAPI application at `ml/service/`:
- `/health` -- service status
- `/classes` -- available sign classes
- `/detect-signs` -- detect signs from uploaded image
- `/detect-signs-by-path` -- detect signs from local file path

Sign class to OGSL mapping defined in `ml/service/sign_mapping.json` (173 entries with OGSL names and Unicode codepoints).

---

## Akkademia

**What it does**: Akkadian transliteration using BiLSTM (also HMM, MEMM variants).
**Accuracy**: 96.7% on RINAP evaluation set
**Training data**: RINAP corpora via ORACC
**License**: Apache 2.0

### Schema Integration

- **Schema target**: `token_readings` layer (transliteration form + reading)
- **Current status**: Model available in `ml/models/akkademia/`, not yet wired to UI or import pipeline
- **Provenance**: Would use `annotation_runs` with `source_type='model'`, `source_name='Akkademia v{version}'`

---

## DeepScribe

**What it does**: Elamite cuneiform OCR using CNN/ResNet architecture.
**Training data**: Persepolis Fortification Archive (100k+ annotations)
**License**: MIT
**Current status**: Code only, no trained weights available.

- **Schema target**: `sign_annotations` (future, when weights become available)
- **Note**: Elamite is an underrepresented language in cuneiform NLP. Training data exists (PFA) but no production model is available.

---

## Model-Agnostic Provenance

The schema is deliberately model-agnostic. The `annotation_runs` table can record output from any tool:

```yaml
annotation_runs:
  source_type: model | human | hybrid | import
  source_name: "BabyLemmatizer v2.2" | "L2" | "GPT-4" | "human_collation" | ...
  method: ML_model | hand_copy | collation | import | ...
  config_snapshot: { tokenizer_mode: 0, model: "neo-assyrian", ... }
```

This means new models (LLMs, future specialized tools, BabyFST finite-state transducers) can be added without schema changes. The provenance mechanism is the same regardless of what produced the annotation.

The EvaCun 2025 shared task demonstrated that different tools excel at different subtasks. The schema supports storing and comparing all of them on the same tokens, enabling retrospective evaluation as the field evolves.
