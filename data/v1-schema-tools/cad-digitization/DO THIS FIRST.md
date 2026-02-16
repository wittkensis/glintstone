# DO THIS FIRST

Before running the extraction pipeline, you need to complete one manual step:

## Create Few-Shot Examples

The extraction quality depends on providing 5-10 manually transcribed CAD entries as examples. These teach the model the expected output format.

### Steps

1. **Open a CAD PDF** (e.g., download `cad_g.pdf` first with `./01_download_pdfs.sh -v g`)

2. **Find 5-10 representative entries** covering:
   - Simple noun entries
   - Verb entries with multiple stems
   - Entries with many attestations
   - Entries with cross-references (cf., see)
   - Entries with Sumerian logograms

3. **Create `config/examples.json`** with this structure:

```json
{
  "description": "Few-shot examples for CAD entry extraction",
  "examples": [
    {
      "input_text": "The raw text from the PDF for this entry...",
      "expected_output": {
        "headword": "gamālu",
        "part_of_speech": "v.",
        "meanings": [
          {
            "position": "a",
            "definition": "to spare, show mercy",
            "semantic_domain": "social",
            "attestations": [
              {
                "text_reference": "CT 25 50:3",
                "akkadian_text": "i-gam-mi-il",
                "translation": "he will spare",
                "period": "OB"
              }
            ]
          }
        ],
        "logograms": [
          {
            "sumerian_form": "ŠU.TAG",
            "pronunciation": "gamālu"
          }
        ],
        "cross_references": [
          {
            "to_headword": "gamīlu",
            "reference_type": "see"
          }
        ]
      }
    }
  ]
}
```

### Tips

- Copy the exact text from the PDF as `input_text`
- Include all the structure you want extracted in `expected_output`
- More examples = better extraction quality
- Include edge cases (complex entries, unusual formatting)

### Period Abbreviations

| Code | Meaning |
|------|---------|
| OA | Old Assyrian |
| OB | Old Babylonian |
| MA | Middle Assyrian |
| MB | Middle Babylonian |
| NA | Neo-Assyrian |
| NB | Neo-Babylonian |
| SB | Standard Babylonian |

---

## Then Run the Pipeline

```bash
./setup.sh              # Install dependencies
./01_download_pdfs.sh   # Download PDFs
./02_pilot_extraction.sh # Test on cad_g (will prompt for examples)
# Review html/cad_g_pilot.html
./03_full_extraction.sh  # Full extraction
./04_import_to_db.sh     # Import to database
./05_verify.sh           # Verify results
```
