# CAD Digitization

STATUS: This has NOT been done yet, but the tools are in place.

Extract the Chicago Assyrian Dictionary (CAD) PDFs into a structured database using [langextract](https://github.com/google/langextract).

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Download CAD PDFs
./01_download_pdfs.sh

# 3. Run pilot extraction on smallest volume
./02_pilot_extraction.sh

# 4. Review pilot results, then run full extraction
./03_full_extraction.sh

# 5. Import into glintstone.db
./04_import_to_db.sh

# 6. Verify results
./05_verify.sh
```

## Prerequisites

- Python 3.10+
- Google AI Studio API key ([get one here](https://aistudio.google.com/apikey))

## Project Structure

```
cad-digitization/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── setup.sh                     # Install dependencies
│
├── 01_download_pdfs.sh          # Download all 26 CAD PDFs
├── 02_pilot_extraction.sh       # Test on cad_g.pdf (smallest)
├── 03_full_extraction.sh        # Extract all volumes
├── 04_import_to_db.sh           # Import JSONL → glintstone.db
├── 05_verify.sh                 # Verification checks
│
├── config/
│   ├── extraction_config.py     # langextract schema
│   └── examples.json            # Few-shot examples (you create)
│
├── scripts/
│   ├── download_cad_pdfs.py     # Download script
│   ├── convert_pdf_to_text.py   # PDF → text extraction
│   ├── run_extraction.py        # langextract wrapper
│   ├── import_cad_entries.py    # JSONL → SQLite importer
│   └── verify_extraction.py     # Verification script
│
├── pdfs/                        # Downloaded CAD PDFs
├── text/                        # Extracted text from PDFs
├── output/                      # langextract JSONL output
├── html/                        # HTML visualizations
└── logs/                        # Timestamped logs
```

## Database Schema

After import, these tables are available in `glintstone.db`:

| Table | Description |
|-------|-------------|
| `cad_entries` | Main entry table (headword, POS, volume) |
| `cad_meanings` | Definitions/meanings for each entry |
| `cad_attestations` | Text citations with references |
| `cad_cross_references` | Links between entries |
| `cad_logograms` | Sumerian equivalents |
| `cad_fts` | Full-text search index |
| `cad_entries_summary` | View with aggregated stats |

### Example Queries

```sql
-- Search by headword
SELECT * FROM cad_entries WHERE headword LIKE 'šarr%';

-- Full-text search
SELECT * FROM cad_fts WHERE cad_fts MATCH 'king';

-- Entry with meanings
SELECT e.headword, m.definition
FROM cad_entries e
JOIN cad_meanings m ON m.entry_id = e.id
WHERE e.headword = 'šarru';

-- Attestations for a period
SELECT e.headword, a.text_reference, a.akkadian_text
FROM cad_entries e
JOIN cad_attestations a ON a.entry_id = e.id
WHERE a.period = 'OB';
```

## Creating Few-Shot Examples

Before running extraction, you need to create `config/examples.json` with 5-10 manually transcribed CAD entries. This teaches the model the expected output format.

### Example Format

```json
{
  "examples": [
    {
      "input_text": "šarru s.; king; ...",
      "expected_output": {
        "headword": "šarru",
        "part_of_speech": "s.",
        "meanings": [
          {
            "position": "a",
            "definition": "king, ruler",
            "attestations": [
              {
                "text_reference": "CH 1:1",
                "period": "OB"
              }
            ]
          }
        ],
        "logograms": [
          {"sumerian_form": "LUGAL"}
        ]
      }
    }
  ]
}
```

### Tips for Examples

1. Include diverse entry types (nouns, verbs, adjectives)
2. Include entries with multiple meanings
3. Include entries with many attestations
4. Include entries with cross-references
5. Include entries with logograms

## Cost Estimates

| Phase | API Cost |
|-------|----------|
| Pilot (Flash) | ~$3-5 |
| Full extraction (Pro) | ~$120-180 |
| **Total** | **~$130-200** |

## Troubleshooting

### "langextract not installed"

Run `./setup.sh` or manually: `pip install langextract`

### "GOOGLE_API_KEY not set"

1. Get API key from https://aistudio.google.com/apikey
2. Add to `.env` file: `GOOGLE_API_KEY=your_key_here`

### PDF conversion issues

If two-column text is merging incorrectly:
1. Try different `pdfplumber` settings in `convert_pdf_to_text.py`
2. Or use `pdftotext -layout` as alternative

### Low extraction quality

1. Review HTML visualizations to identify patterns
2. Add more few-shot examples to `config/examples.json`
3. Adjust prompts in `config/extraction_config.py`

## References

- [Chicago Assyrian Dictionary (ISAC)](https://isac.uchicago.edu/research/publications/assyrian-dictionary-oriental-institute-university-chicago-cad)
- [langextract Documentation](https://github.com/google/langextract)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
