# The App

Glintstone's web interface is at [app.glintstone.org](https://app.glintstone.org). No account required for browsing and search.

## Search and filter

The main search bar accepts free text — a word, a P-number, a scholar's name, a museum number. Results are sorted by relevance. Facets on the left let you narrow by:

- **Period** — Ur III, Old Babylonian, Neo-Assyrian, etc.
- **Provenience** — Nippur, Ur, Nineveh, etc.
- **Genre** — Administrative, Literary, Legal, etc.
- **Language** — Sumerian, Akkadian, Elamite, etc.
- **Pipeline stage** — filter to tablets that have ATF, lemmatization, or translation

Facet counts update as you select — each count shows how many results would remain if you added that filter.

## Reading an artifact page

Each artifact page is organized around the five pipeline stages:

**Captured** — The basic catalog record: designation, museum number, period, provenience, genre, material, dimensions. A photograph if one is cached.

**Recognized** — Sign detection bounding boxes overlaid on the image (when available). Currently limited to the 81 Neo-Assyrian tablets from CompVis.

**Transcribed** — The ATF transliteration, parsed line by line with surface markers. The ATF viewer shows `@obverse`, `@reverse`, and edge markers. Broken or missing signs are indicated with `[...]`.

**Lemmatized** — Where available, each token links to its dictionary entry. Clicking a lemma opens the sign dictionary with citation form, guide word, part of speech, and attested senses.

**Translated** — Line-by-line translations in available languages (English, German, and others).

## The ATF viewer

The ATF viewer renders the transliteration with interlinear glossing when lemmatization is present. Hover over a word to see the linked lemma. The viewer shows competing lemmatizations when multiple annotation runs exist for the same token.

## The dictionary

The dictionary tab (at the top of the app) lets you browse signs and lemmas directly. Filter by language, part of speech, frequency, or source. Each lemma page shows attestation count, all known written forms, and senses.

## When data seems wrong

Data errors happen. The most common causes:

- CDLI catalog has not been updated since August 2022 — some metadata may be stale
- ATF parsing occasionally produces alignment errors on complex texts
- Lemmatizations are sparse and may disagree between sources

To report a specific error, see [Report an Error](/docs/overview/report-error/).
