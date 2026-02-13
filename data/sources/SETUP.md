# Data Sources Setup

This directory holds raw source data used by the import pipeline (`data/tools/import/`). Nothing here is tracked in git -- download or clone each source as needed.

---

## CDLI/

Cuneiform Digital Library Initiative. Catalog metadata, ATF transliterations, and tablet images.

Download via `data/tools/download/download_cuneiform_data.py` or manually from https://cdli.earth.

Expected structure:
```
CDLI/
├── catalogue/     JSON catalog files
├── metadata/      cdli_cat.csv, cdliatf_unblocked.atf (86 MB)
├── atf/           Individual ATF files
└── images/        Tablet photographs (fetched on demand by the app)
```

---

## ORACC/

Open Richly Annotated Cuneiform Corpus. Project corpora, glossaries, and sign lists.

Download via `data/tools/download/download_glossaries.py` or from https://oracc.museum.upenn.edu.

Key subdirectories:
- `dcclt/` -- DCCLT lexical corpus and glossaries (gloss-sux.json, gloss-akk.json, etc.)
- `ogsl/` -- OGSL sign list (ogsl-sl.json)
- Various project corpora (rime, ribo, rinap, etcsl, etc.) for lemma data

---

## eBL/

Electronic Babylonian Literature. Fragment metadata and OCR data.

See https://www.ebl.lmu.de for access.

---

## ePSD2/

Electronic Pennsylvania Sumerian Dictionary data and Unicode mappings.

See http://oracc.org/epsd2.

---

## compvis-annotations/

CompVis cuneiform sign detection dataset. 81 tablets, 8,109 bounding-box annotations.

```bash
cd data/sources
git clone https://github.com/CompVis/cuneiform-sign-detection-dataset.git compvis-annotations
```

Used by `data/tools/import/import_compvis_annotations.py` to populate the `sign_annotations` table.

---

## ebl-annotations/

eBL cuneiform OCR training data. Cropped sign images and training configurations.

```bash
cd data/sources
git clone https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr-data.git ebl-annotations
```

Used by the ML training pipeline. The eBL OCR DETR model (`ml/models/ebl_ocr/`) was trained on this data.
