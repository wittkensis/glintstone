# UI
- Reincorporate lost homepage styling
- Add section to homepage that addresses academics

# Data
- Linguistic pipeline schema v2
- Add source attribution
- Add academic referencess and CDLI profile links
- Support multiple CDLI images
- Add about page with schema and CC licenses
- Add CC license to this project
- Add academic publishing associations
- Add demo placeholders for future added contributions
- Make sure aggregations are updated and kept up-to-date moving forward (x_stats tables)

## ORACC Import Status

### In Database
- **dcclt** (Lexical Texts) — 2.0 GB, 4,980 texts. Glossaries + corpus lemmas (308k) imported. Only ORACC project with lemma data.
- **ogsl** (Sign List) — 2.7 MB. 3,367 signs, 10,312 sign values imported.

### Extracted, Ready to Import
- **saao** (State Archives of Assyria) — 760 MB, 5,055 catalogue entries. Largest corpus. Rich dialect coverage (Neo-Assyrian, Neo-Babylonian, Middle Assyrian, Std Babylonian). 134 MB Akkadian glossary. Has geojson.
- **rinap** (Neo-Assyrian Royal Inscriptions) — 287 MB, 1,037 catalogue entries. Subproject structure (per king). 69 MB Akkadian glossary, 48 corpusjson files in rinap1.
- **hbtin** (Hellenistic Babylonia) — 460 MB, 487 corpus files, 2,817 catalogue entries. Unique Late Babylonian dialect coverage.
- **dccmt** (Mathematical Texts) — 102 MB, 252 corpus files, 1,463 catalogue entries. Old Babylonian math, Old Assyrian dialect.
- **ribo** (Babylonian Royal Inscriptions) — 84 MB, 391 catalogue entries. Subproject structure (per dynasty). 27 MB Akkadian glossary. Has geojson.

### Extracted, Ready to Import (re-downloaded/extracted 2026-02-14)
- **epsd2** (Sumerian Dictionary) — 1.8 GB glossary (gloss-sux.json), sign list, 73 MB catalogue. Dictionary project, no corpus texts.
- **riao** (Royal Inscriptions of Assyria) — 102 MB lemma index, 3.3 MB catalogue. Has geojson. No corpus files.
- **etcsri** (Royal Inscriptions of Sumer/Akkad) — 22 MB Sumerian glossary, 11 MB proper-name glossary, 1,456 corpus files. Has geojson.
- **blms** (Babylonian Library of Magical Spells) — 15 MB Sumerian glossary, 12 MB Akkadian glossary, 12 MB Std Babylonian glossary, 229 corpus files. Also has Emesal dialect.
- **amgg** (Ancient Mesopotamian Gods and Goddesses) — Portal/reference data only (383 KB), no glossaries or corpus.

### Unavailable on ORACC Server (500/404 errors on all URL patterns, checked 2026-02-14)
- **rime** (Early Royal Inscriptions, 3rd millennium BCE)
- **etcsl** (Sumerian Literature: myths, hymns, laments)
- **cams** (Scholarly/Scientific Texts: astronomy, medicine, divination)
- **ctij** (Texts Mentioning Israelites/Judeans)

# Resources to Review
- https://compvis.github.io/cuneiform-sign-detection-code/
- CDLI Tablet Detail https://cdli.earth/artifacts/322250
- DeepScribe Methodology https://arxiv.org/html/2306.01268v2
