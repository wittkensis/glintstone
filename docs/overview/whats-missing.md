# What's Missing

Glintstone is honest about its gaps. Here is a specific accounting of what is not yet integrated, not yet complete, or not yet working well.

## The Chicago Assyrian Dictionary (CAD)

The CAD is the most comprehensive scholarly dictionary of Akkadian — 21 volumes covering the complete lexicon from A to Z, decades of expert consensus. It is not yet in Glintstone. ISAC (the Institute for the Study of Ancient Cultures at Chicago) is digitizing it. Until a structured format is available, PDF extraction is the fallback. This is the single highest-value missing source for Akkadian text.

## Elamite corpus is thin

Elamite is the third major cuneiform language after Sumerian and Akkadian. Glintstone has minimal Elamite coverage. The Persepolis Fortification Archive contains the richest Elamite corpus, but Glintstone has not integrated it yet. Elamite lemmatization is essentially absent.

## Only ~2% lemmatized

Of 353,283 artifacts in the catalog, approximately 7,500 have any lemmatization. This means that for 98% of tablets, you can see the transliteration (if it exists) but cannot follow individual words to dictionary entries. Lemmatization requires deep linguistic expertise — a senior Assyriologist might fully lemmatize 50–200 texts in a career.

## BabyLemmatizer not run at scale

BabyLemmatizer is a neural model for Sumerian part-of-speech tagging with 94–96% accuracy on in-vocabulary forms. The model has been evaluated, the import pipeline is designed, but the full-corpus run has not yet been executed. When it is, its outputs will be stored as a separate lower-confidence interpretation — not as ground truth.

## Most tablets have no locally cached images

Images are fetched on demand from CDLI and cached in R2. Many tablets have no published images at all. For tablets that do have images, they are fetched the first time someone views the artifact page; cold loads take a few seconds.

## Contribution workflows not designed

The long-term goal is a platform where a scholar's annotations, corrections, and translations are attributed, discoverable, and citable. The data model supports this — every annotation carries `annotation_run_id`. But the contribution workflow itself (how a domain expert submits a correction that flows into the trust system) is not yet designed for external scholars. The `submit_correction` MCP tool is the first surface.

## Hittite and Hurrian coverage very limited

Glintstone's data model is language-aware, but dictionary data for Hittite (CHD) and Hurrian is sparse. The Chicago Hittite Dictionary is partially digitized; Glintstone has not imported it.

## CDLI bulk export is frozen

The main CDLI catalog export used to build Glintstone's artifact table was last updated in August 2022. CDLI's data pipeline has been frozen upstream since then. New tablets cataloged since then are not reflected in Glintstone's main artifact table.

---

If you notice something specific that is wrong or missing, [report an error](/docs/overview/report-error/).
