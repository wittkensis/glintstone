---
name: missing-sources
description: Cuneiform/Assyriology databases and corpora that are not yet integrated into Glintstone — integration readiness, access patterns, and priority.
metadata:
  type: project
---

# Missing sources — integration candidates

Sources that are NOT in Glintstone and not part of the ORACC project family. Organized by integration readiness.

---

## Priority 1 — Ready to integrate (data accessible, format known)

### SEAL — Sources of Early Akkadian Literature
**PI**: Michael Streck (Leipzig); collaborators include Nathan Wasserman (Jerusalem).
**Covers**: Akkadian literary texts predating the Standard Babylonian canon — Old Babylonian and earlier literary compositions (~500 texts). The pre-SB counterpart to what CAMS/NERE covers for later periods.
**Access**: https://seal.huji.ac.il — web database with text browser. No public bulk dump yet (as of 2026), but a JSON/XML export has been planned. Contact Streck/Wasserman for bulk access.
**Format**: Proprietary web DB; structured ATF transliteration + translation + bibliography.
**License**: Research use; no CC statement found.
**Gap**: Important for covering the Old Babylonian literary period that ePSD2 and DCCLT only partially address. Overlaps with akklove (now integrated from ORACC) but broader scope.
**Integration path**: Email PI for bulk export. If available, write a new `seal_corpus.py` connector targeting `lexical_lemmas`, `artifact_credits`, `translations`.

---

### Archibab — Archives babyloniennes (Old Babylonian)
**PI**: Bertrand Lafont (CNRS Nanterre).
**Covers**: Old Babylonian administrative and legal archives — ~20,000+ tablets from sites like Sippar, Ur, Nippur, Mari archives. Complementary to balt/obta/obmc (now integrated) but focused on published OB archives.
**Access**: https://archibab.fr — Angular SPA with REST API endpoints. JSON responses visible in browser DevTools. No published API spec.
**Format**: Structured JSON via undocumented REST endpoints; catalogue entries with museum numbers, CDLI P-numbers, dates, personal names.
**License**: Unclear; French academic project. Likely research use.
**Gap**: Best coverage of OB administrative texts outside CDLI. Personal name data (Akkadian personal names) is especially valuable for the scholar/prosopography layer.
**Integration path**: Reverse-engineer REST endpoints; write `archibab.py` connector as a live-API connector. P-number JOIN is feasible since they track CDLI IDs.

---

### BDTNS — Base de datos de textos neo-sumerios
**PI**: Manuel Molina (CSIC Madrid).
**Covers**: ~100,000 Ur III administrative tablets. This is the most complete Ur III corpus online, comparable to but distinct from CDLI's Ur III coverage.
**Access**: https://bdtns.filol.csic.es — has a REST-like query interface. P-number JOIN feasible.
**Format**: Structured web database; catalogue data with person names, commodities, dates. No published bulk dump.
**License**: Research use.
**Gap**: Ur III prosopography, commodity data (grain rations, silver payments), date-formula normalization. Extremely valuable for economic history queries.
**Integration path**: Contact PI for bulk export or scrape structured endpoints. Write `bdtns.py` connector targeting `artifact_credits`, new `ur3_transactions` table (if warranted), or commodity annotations.

---

### KeiBi — Keilschriftbibliographie
**Already documented in `sources.md`.** Manual snapshots only. No automated bulk download available.
**Gap**: ~90k bibliography entries covering all Assyriology publications. The citation layer in Glintstone is thin without this.
**Integration path**: Negotiate a bulk export with the editors (Pontifical Biblical Institute, Rome). Alternatively, cross-reference via OpenAlex DOIs.

---

## Priority 2 — Integration feasible, needs investigation

### eBL API — electronic Babylonian Library (beyond sign concordance)
**Already partially integrated** via `ebl_sign_concordance.py`. The live eBL API (ebl.lmu.de) exposes fragment metadata, lemmatizations, and bibliography that we are not yet using.
**Gap**: ~6,000 fragmentary texts with eBL-specific lemmatizations (often more current than ORACC data); Babylonian Library text reconstructions.
**Blocker**: eBL API requires Auth0 authentication. The CDLI-to-eBL fragment concordance exists but requires API key.
**Integration path**: Request API access from Enrique Jiménez (Munich). Write `ebl_fragments.py` targeting `lemmatizations`, `artifact_credits`.

---

### Achemenet — Achaemenid Persian administrative texts
**PI**: Wouter Henkelman (Paris).
**Covers**: Persepolis Fortification Archive and related Achaemenid administrative texts in Elamite and Aramaic, with cuneiform content.
**Access**: http://www.achemenet.com — structured database. Unclear if bulk export is available.
**Format**: Structured web DB.
**Gap**: Achaemenid period coverage (539–330 BCE) is thin in Glintstone. `ario` (now integrated from ORACC) covers Old Persian royal inscriptions; Achemenet covers the administrative side.
**Integration path**: Contact Henkelman. Possibly overlap with ORACC `ario` data.

---

### OCHRE — Object Coregistration and Heritage Research (Oriental Institute)
**Covers**: OI excavation data, some textual corpora including the Chicago Assyrian Dictionary source cards (~450,000 index cards, partially digitized).
**Access**: ochre.lib.uchicago.edu — publicly browsable; some exports available.
**Format**: XML-based OCHRE format; non-standard.
**Gap**: CAD cross-references would enrich the lexical layer significantly. OCHRE also holds unpublished OI excavation data from Nippur, Khafajah, etc.
**Integration path**: Contact OI Digital Initiatives for bulk export. CAD source cards would need custom parsing.

---

### CUNES — Cuneiform Manuscripts at York University (via CDLI)
**Covers**: Primarily Ur III tablets from the Schøyen Collection and related holdings.
**Status**: Most CUNES texts ARE in CDLI already. This is not a separate integration target — it's a museum collection within CDLI.
**Action**: None needed; CDLI catalog covers it.

---

## Priority 3 — Future / requires new infrastructure

### CAD — Chicago Assyrian Dictionary (full text)
**Covers**: 21 volumes (A–Z + supplements) of Akkadian lexicography — the authoritative reference for ~20,000 Akkadian lemmas with attestation citations.
**Access**: PDFs freely available at https://oi.uchicago.edu/research/publications/assyrian-dictionary-oriental-institute-university-chicago-cad. Machine-readable version: not officially published, but a community effort at https://github.com/oracc/cad has structured text extractions.
**Gap**: Would massively enrich `lexical_lemmas` / `lexical_senses` for Akkadian with guide words, usage notes, and bibliographic citations.
**Integration path**: Use the GitHub community CAD parsing project as a starting point. Write `cad_lexicon.py` against extracted JSON. This is complex — CAD has deep citation structure that maps poorly to our current schema. Suggest adding a `cad_entry_id` foreign-key column to `lexical_lemmas` first.

---

### ARMADA / Archibab New Discoveries
**Status**: Checking whether ARMADA exists as a separate project from Archibab. Based on research, ARMADA appears to be an internal project name; Archibab is the public face.

---

## Eckart Frahm's projects — status

Eckart Frahm (Yale) is one of the most prolific ORACC contributors. All of his publicly available work is now covered:

| Project | ORACC slug | Status after this update |
|---|---|---|
| CAMS Geography of Knowledge | `cams/gkab` | **Now integrated** |
| RINAP 3 (Sennacherib) | `rinap/rinap3` | **Now integrated** |
| RINAP 5 (Ashurbanipal) | `rinap/rinap5` | **Now integrated** |
| Reading Library of Ashurbanipal | `asbp/rlasb` | **Now integrated** |
| Babylonian Commentary Texts | covered under `cams` | **Integrated via parent** |
| SAA 3 (Court Poetry) | `saao/saa03` | **Now integrated** |

Frahm's *Babylonian and Assyrian Text Commentaries* (BACT, Harrassowitz 2011) is a monograph, not a digital corpus. Commentary tablet data is in ORACC under CAMS subprojects (gkab, barutu, etc.).

---

## Other ORACC projects NOT integrated (lower priority)

Projects on the ORACC project list that were intentionally omitted from Glintstone connectors because they are:
- **Journal articles** (iraq, iraq/iraq85) — textual content, not cuneiform data
- **Bibliography / secondary literature** (issl, arrim) — not primary-source corpora
- **Pedagogical** (cams/ntlab, cams/tlab, saao/knpp, saao/aebp) — teaching editions, thin linguistic data
- **Very small or experimental** (kish, kish/fieldmus, contrib/jacobsen, contrib/lambert) — consider on-demand
- **Catalogue-only** (qcat, xcat) — internal ORACC housekeeping, no cuneiform texts
- **Non-cuneiform adjacent** (aemw/idrimi — Ugaritic) — added to credits/enrichment only

---

## New sources not yet in `sources.md`

The following should be added to `gs-expert-integrations/sources.md` when integration begins:

- SEAL (Sources of Early Akkadian Literature)
- Archibab
- BDTNS
- Achemenet
- OCHRE / CAD digital
