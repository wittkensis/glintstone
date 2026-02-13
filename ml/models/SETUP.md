# ML Models Setup

This directory contains three model repositories. Clone or download each as needed.

---

## akkademia/

Automatic transliteration of Unicode cuneiform glyphs. BiLSTM achieves 96.7% accuracy on RINAP corpora.

```bash
cd ml/models
git clone https://github.com/gaigutherz/Akkademia.git akkademia
```

**Requirements:** Python 3.7.x, PyTorch. See `requirements.txt` after cloning.

**Glintstone status:** Available but not yet wired to UI. Can be used standalone via its Python package.

---

## deepscribe/

CNN/ResNet sign classification trained on the Persepolis Fortification Archive (100K+ annotated Elamite cuneiform regions).

```bash
cd ml/models
git clone https://github.com/oi-deepscribe/deepscribe.git deepscribe
```

**Requirements:** Conda environment via `environment.yml`. See `docs/requirements.txt` after cloning.

**Glintstone status:** Code only, no pre-trained weights included. Weights must be trained from the Persepolis data (not publicly distributed).

---

## ebl_ocr/

Cuneiform sign detection using Deformable DETR + ResNet-50. Trained 1,000 epochs on eBL annotations, 173 sign classes, mAP@50 = 43.1%.

The trained checkpoint `detr-173-classes-10-2025.tar.gz` is not in git. To set up:

1. Obtain the checkpoint from the eBL OCR training pipeline
2. Place the `.tar.gz` in `ml/models/ebl_ocr/`
3. Extract: `tar -xzf detr-173-classes-10-2025.tar.gz`

**Glintstone status:** Integrated into `ml/service/app.py` (FastAPI). Currently runs in mock mode on macOS ARM64 due to mmcv incompatibility. Works in Docker (x86_64), Modal serverless, or Google Colab.
