# Texts — Layer 2

Layer 2 is the textual content: transliterations broken into lines and tokens, and translations.

## Key tables

**`text_lines`** — One row per line of ATF transliteration. Fields include:
- `p_number` — the artifact
- `surface_type` — obverse, reverse, edge, etc.
- `line_no` — ATF line label (e.g., "1.", "r.1.", "e.1.")
- `content` — raw ATF text for the line
- `line_order` — integer ordering for display

**`tokens`** — Individual words (and determinatives) within a line. One row per word-position. Fields include:
- `line_id` — foreign key to text_lines
- `word_no` — position within the line
- `form` — the written form as it appears in ATF (e.g., "lu₂-gal")
- `is_determinative` — true for silent classifier signs ({d}, {f}, {ki})
- `flags` — damage markers from ATF (!, ?, #, *)

**`token_readings`** — The reading assigned to a token — the sign sequence used to produce the written form. Separate from lemmatization.

**`translations`** — Line-by-line translations grouped by language code. Fields:
- `p_number`
- `line_no`
- `language` — ISO 639 code (en, de, it, fr, es, dk, ca, fa, ts)
- `text` — the translation text for that line

## ATF line structure

ATF (ASCII Transliteration Format) is the standard digital notation for cuneiform. Key conventions:

```
&P227657 = KTT 188
#atf: lang sux
@obverse
1. ninda
2. kasz
#tr.en: bread
#tr.en: beer
@reverse
(blank)
```

- `&P227657` — tablet ID header
- `#atf: lang sux` — language declaration (sux = Sumerian)
- `@obverse` / `@reverse` — surface markers
- `1.` — line number
- `#tr.en:` — inline English translation
- `[...]` — broken or missing text
- `{d}` — determinative (divine name follows)

## CDL tree decomposition

ORACC stores annotated texts as CDL (Chunk-Delimiter-Lemma) trees. Each text decomposes into nested nodes: chunk > sentence > lemma > grapheme. The ingestion pipeline walks this tree and maps it into `tokens` and `lemmatizations` (Layer 3), keyed by `(p_number, line_no, word_no)`.

## Translation language codes

Translations in Glintstone use these language codes:

| Code | Language |
|------|----------|
| en | English |
| de | German |
| it | Italian |
| fr | French |
| es | Spanish |
| dk | Danish |
| ca | Catalan |
| fa | Farsi |
| ts | Transliteration supplement |

43,777 artifacts have at least one translation (~12% of the catalog). Coverage is not uniform — literary and well-studied texts have translations; administrative tablets typically do not.
