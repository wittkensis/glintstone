---
event: UserPromptSubmit
action: warn
---

# Import Pipeline Context Injection

Auto-load import pipeline context when user asks about data import.

## Patterns

- `\b(import|ETL|pipeline|source data)\b`
- `source-data/import-tools`
- `CDLI|ORACC|eBL|ePSD2`

## Context to Inject

When user mentions import-related topics, remember:

### Import Script Sequence (15 numbered scripts)

```
00_setup_database.py       - Initialize schema
01-05                      - Core data imports
06_seed_artifact_identifiers.py
07_parse_atf.py           - ATF transliteration parsing
08-12                      - Additional data sources
13_import_glossaries.py   - Lexical data
14-15                      - Final enrichment
```

### Primary Data Sources

- **CDLI** - Cuneiform Digital Library Initiative (artifacts, ATF)
- **ORACC** - Open Richly Annotated Cuneiform Corpus (glossaries, lemmatization)
- **eBL** - electronic Babylonian Library (fragments, transliterations)
- **ePSD2** - Electronic Pennsylvania Sumerian Dictionary (Sumerian lexicon)

### Import Pipeline Location

All import scripts: `source-data/import-tools/`
Data sources manifest: `source-data/sources/`

**Note:** Source data directories are read-only and excluded from git (downloaded separately).
