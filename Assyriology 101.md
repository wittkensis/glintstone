# Assyriology 101

> Five thousand years of writing on clay. ~500,000 known artifacts. Less than 2% linguistically analyzed.
>
> Glintstone unifies fragmented cuneiform research data so scholars and volunteers can close that gap.

This doc gets you oriented in under 5 minutes.

---

## Meet P227657

A clay tablet, roughly the size of your palm. Pressed into wet clay ~3,800 years ago in what is now Iraq. It's a word list -- a school exercise where a student practiced writing Sumerian vocabulary.

353,283 tablets like this one sit in Glintstone's database. Here's what it takes to understand just one.

---

## Step 1: The Object

A curator in a museum photographs the tablet. Front side (obverse), back side (reverse), edges. The photo enters CDLI's catalog and gets a **P-number** -- a universal identifier that every system in the field uses.

**P-number** = the join key for everything in Glintstone. Think of it like a DOI, but for tablets. Example: P227657.

---

## Step 2: The Signs

The surface shows wedge-shaped marks. This is **cuneiform** -- a writing system used from ~3400 BCE to ~100 CE.

This is not an alphabet. There are **~3,400 known signs**. Each sign can represent a syllable, a whole word, a word function (AKA "determinative"), or all three -- depending on context and language. The canonical inventory (OGSL) catalogs these signs along with **~15,000 reading values**.

To put that in perspective: English has 26 letters. Cuneiform has 3,400 signs, each of which might mean several completely different things.

**Polyvalency** = one sign, many readings. The sign "/KA/" can be read as "ka," "gu," "dug," "inim," or "zu" depending on context. A scholar needs years of training and surrounding context to know which reading is correct.

Glintstone includes an ML model (Deformable DETR) that draws bounding boxes around signs it detects in tablet photographs. It currently knows 173 sign classes out of 3,400+. Human experts handle the rest.

---

## Step 3: The Transliteration

A scholar reads the signs and writes them in **ATF** (ASCII Transliteration Format) -- the standard digital notation for cuneiform:

```
&P227657 = KTT 188
#atf: lang sux
@obverse
1. ninda
2. kasz
```

Line by line: `&P227657` is the tablet ID. `#atf: lang sux` declares the language (Sumerian). `@obverse` marks the front surface. `1. ninda` is the first line of text.

**Transliteration** = converting cuneiform signs into Latin letters. This is not the same as translation. Transliteration tells you *what signs are there*. Translation tells you *what they mean*.

Other ATF conventions you'll see in the data:
- `{d}` = determinative (a silent classifier: "divine name follows")
- `[...]` = broken or missing text (tablets are 4,000 years old -- they break)
- `@reverse` = back surface of the tablet

135,200 tablets have ATF in our database. That's roughly 35% of the catalog.

---

## Step 4: The Languages

P227657 is in **Sumerian** -- a language isolate with no known living or dead relatives. It's agglutinative (words are built by stacking meaningful pieces together, like Turkish or Japanese).

The other major cuneiform language is **Akkadian** -- a Semitic language, in the same family as Arabic and Hebrew. Akkadian has dialects spanning 2,500 years (Old Babylonian, Neo-Assyrian, etc.).

Both languages use the same cuneiform script, but with completely different grammar. And here's where it gets interesting: Sumerian words frequently appear *inside* Akkadian texts as shorthand. These are called **Sumerograms** -- like writing "etc." (Latin) in an English sentence, except the reader pronounces it as the Akkadian word.

And then there's Hittite: a language from modern Turkey that can include a combination of Sumerograms and **Akkadograms**.

Elamite is a different ballgame.

**What trips people up:**
- In Sumerian, subscript numbers distinguish different words: `du` ("go") is not `du3` ("build"). The subscripts are meaningful.
- In Akkadian, subscripts are just disambiguation for which sign is being used -- they don't change the word's identity. So `du3` normalizes to `du`.
- The tokenizer must handle both modes depending on the language declared in the ATF header.
- Occasionally, tablets can contain both languages side-by-side.

**Important caveat:** Scholars genuinely disagree on Sumerian grammar. There are 3+ competing frameworks for how the Sumerian verb works. This isn't a matter of incomplete research -- it's an active, unresolved academic debate. The data model reflects this: multiple competing analyses can coexist for the same text.

---

## Step 5: The Dictionary Lookup

"ninda" in our glossary resolves to: `ninda[food]N` -- meaning "bread, food." It has 109,427 attestations across the corpus.

The process of linking a word-form to its dictionary entry is called **lemmatization**. It requires knowing the language, dialect, historical period, and genre of the text. A single word might lemmatize differently in a royal inscription vs. a merchant's letter.

Only **~2% of our 353,000 tablets** have lemmatization. This is the single biggest gap in the pipeline. A senior scholar might fully lemmatize 50-200 texts in a career.

Glintstone integrates **BabyLemmatizer**, a neural model that automates part of this process. It achieves 94-96% accuracy on words it has seen before, but drops to 68-84% on rare or novel forms. Its outputs are stored alongside human annotations as a separate, lower-confidence interpretation -- never silently replacing expert work.

---

## Step 6: The Translation

```
1. ninda  -->  bread
2. kasz   -->  beer
```

43,777 tablets have translations in our database (~12% of the catalog). Simple word lists like P227657 are straightforward. Literary epics, legal contracts, and royal inscriptions are orders of magnitude harder -- and many have no translation at all.

---

## Step 7: The Debate

Another scholar might read line 1 differently. Maybe the tablet surface is damaged and the sign is ambiguous. Maybe they trained under a different school of thought about Sumerian grammar.

Glintstone stores **all interpretations with provenance**: who annotated it, when, what source they used, and with what confidence. Every record links back to an `annotation_run` that identifies its origin.

**Competing interpretations are a feature of Glintstone, and core to the data model.**

---

## The Pipeline at a Glance

Every artifact is tracked through 5 stages:

| Stage | What Happens | Current Coverage |
|-------|-------------|-----------------|
| 1. Captured | Photograph exists | Varies by collection |
| 2. Recognized | Signs detected on image | 81 tablets (ML) |
| 3. Transcribed | ATF text written | 135,200 (~35%) |
| 4. Lemmatized | Words linked to dictionary | ~7,500 (~2%) |
| 5. Translated | Meaning in modern language | 43,777 (~12%) |

The drop from Stage 3 to Stage 4 is the critical gap. Transcription can be done with good training. Lemmatization requires deep linguistic expertise.

---

## Where the Data Comes From

No single project has the full picture. Glintstone merges five major sources:

| Source | What It Provides | Scale |
|--------|-----------------|-------|
| **CDLI** | Artifact catalog, ATF transliterations, images. The P-number authority. | 353k artifacts |
| **ORACC** | Richest linguistic annotations: lemmatized texts, glossaries. Project-based. | ~7,500 lemmatized texts |
| **OGSL** | Canonical sign list with Unicode mappings and cross-references. | 3,367 signs, ~15k values |
| **eBL** | Computer vision training data, bibliography, fragment joins. | 173 sign classes |
| **ePSD2** | Primary Sumerian dictionary. | 1.8 GB |

Each source covers different tablets, uses different conventions, and updates on different schedules. CDLI's bulk catalog export has been frozen since August 2022. Coverage overlaps are partial.

---

## Who Does This Work

**Assyriologists** are scholars who specialize in the languages and cultures of ancient Mesopotamia. Reading cuneiform fluently requires 2-3 years of graduate-level study -- and that's just the starting point. Mastering a specific corpus or dialect is a career-long pursuit.

Glintstone serves several types of users:
- **Senior scholars** who need quality control and proper attribution for their decades of work
- **PhD candidates** working intensively on narrow corpora for their dissertations
- **Museum curators** managing collections of 100,000+ objects

The field's expertise is both its greatest asset and its bottleneck. There are far more tablets than there are people qualified to read them.

---

## Quick Glossary

| Term | Plain English |
|------|--------------|
| **P-number** | Universal tablet ID (e.g., P000001). The join key for everything. |
| **Q-number** | Composite text ID -- the abstract "work" (e.g., Epic of Gilgamesh). Individual tablets are *exemplars*. |
| **ATF** | ASCII Transliteration Format -- how scholars type cuneiform digitally. |
| **Transliteration** | Converting signs into Latin letters (not the same as translation). |
| **Lemmatization** | Linking a word-form to its dictionary entry. The bottleneck. |
| **Determinative** | Silent classifier sign: `{d}` = divine, `{f}` = female, `{ki}` = place name. |
| **Sumerogram** | A Sumerian word used as shorthand inside an Akkadian text. |
| **Polyvalency** | One sign having multiple possible readings. |
| **Annotation run** | A batch of data from one source. Every record is traceable to its origin. |

---

## How This Maps to the Codebase

| Concept | Database Table(s) | Key File(s) |
|---------|--------------------|-------------|
| Tablets & metadata | `artifacts` | `source-data/import-tools/05_import_artifacts.py` |
| Cuneiform signs | `signs`, `sign_values` | `source-data/import-tools/04_import_signs.py` |
| ATF text | `text_lines`, `tokens` | `source-data/import-tools/07_parse_atf.py` |
| Dictionary | `glossary_entries`, `glossary_senses` | `source-data/import-tools/13_import_glossaries.py` |
| Lemmatization | `lemmatizations` | `source-data/import-tools/11_import_lemmatizations.py` |
| Pipeline status | `artifacts` (stage columns) | `api/repositories/artifact_repo.py` |
| ML sign detection | -- | `ml/service/inference.py` |
| Data provenance | `annotation_runs` | `source-data/import-tools/02_seed_annotation_runs.py` |
| Schema definition | -- | `data-model/v2/glintstone-v2-schema.yaml` |
