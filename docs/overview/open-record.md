# The Open Record

Five thousand years of writing on clay. Roughly 500,000 known artifacts. Less than 2% linguistically analyzed.

The cuneiform record spans the invention of writing through the fall of Babylon — administrative tablets, astronomical observations, literary epics, royal proclamations, medical texts, private letters. The scholarship behind digitizing this record is extraordinary. But it is scattered across incompatible systems and largely inaccessible to anyone outside a narrow circle of specialists.

Glintstone federates the open portion of that record into a single queryable layer.

## What Glintstone indexes

- **353,283 artifacts** from CDLI — tablets, prisms, cones, seals, and other cuneiform carriers
- **ATF transliterations** for ~35% of the catalog (135,200 texts, ~3.5M lines)
- **Lemmatizations** for ~2% (~7,500 texts), primarily from ORACC scholarly projects
- **Translations** for ~12% (~43,777 tablets), across 9 languages
- **Sign dictionary**: 3,367 signs and ~15,000 reading values from OGSL
- **Lexical data**: 61,435 lemmas and 155,491 senses from ePSD2 and ORACC glossaries
- **Scholarly context**: 20,490 scholars and 16,725 publications from CDLI, eBL, and OpenAlex

## The five pipeline stages

Every artifact in Glintstone is tracked through five stages of documentation:

| Stage | What it means |
|-------|--------------|
| **Captured** | A photograph exists |
| **Recognized** | Individual signs detected on the image (ML) |
| **Transcribed** | ATF transliteration written by a scholar |
| **Lemmatized** | Words linked to dictionary entries |
| **Translated** | Meaning rendered in a modern language |

The stage is stored on each artifact and drives the filter system. Most tablets are Transcribed or below. The jump from Transcribed to Lemmatized is the largest gap — it requires deep linguistic expertise and represents years of scholarly work per text.

## Where the data comes from

No single project has the full picture. Glintstone merges five major open-access sources:

**CDLI** (Cuneiform Digital Library Initiative) provides the artifact catalog and ATF transliterations. The P-number — CDLI's universal identifier — is the join key for everything in Glintstone.

**ORACC** (Open Richly Annotated Cuneiform Corpus) provides the richest linguistic annotations: lemmatized texts organized by scholarly project, glossaries, and sign data.

**eBL** (Electronic Babylonian Literature) provides fragment-level scholarly editions and bibliographic data.

**ePSD2** (electronic Pennsylvania Sumerian Dictionary) is the primary Sumerian lexicon, hosted as an ORACC project.

**OGSL** (ORACC Global Sign List) is the canonical sign inventory with Unicode mappings and ~15,000 reading values.

## What this means for a researcher

You can search across 353k artifacts by period, provenience, genre, language, and pipeline stage. You can read the ATF for any tablet that has it, follow the lemmatization chain to dictionary entries, and see the scholarly publications associated with a text. The API exposes all of this programmatically, and the MCP server makes it conversational via Claude.

Coverage is honest and sparse where it is sparse. Every record carries its source, so you know what you're looking at.
