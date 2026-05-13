# Open Questions

These are genuinely unresolved questions that Glintstone has not answered yet. Some are design questions; some are domain questions; some are questions about what the scholarly community would actually want. If you have opinions, [get in touch](mailto:eric.wittke@gmail.com).

## Trust and reputation

How should scholar trust be represented in the data model? The current schema tracks `annotation_run_id` and `is_consensus`, but this is binary — a reading is either consensus or it is not. A more nuanced model might weight interpretations by the scholar's track record on similar texts, or by community endorsement. What does the scholarly community actually want here? What would be defensible in a published workflow?

## Correction granularity

What is the right granularity for user-submitted corrections? Currently `submit_correction` operates at the level of an interaction — "the agent said X about this tablet." But should corrections be linkable to specific tokens? Specific lines? Specific annotation runs? Getting this wrong either creates data that is too coarse to act on or data that is so granular it is unusable in practice.

## ORACC/CDLI metadata disagreement

ORACC and CDLI occasionally disagree on basic artifact metadata — period, provenience, genre. Both are authoritative in their domains. Glintstone currently treats CDLI as the authority for identity metadata and ORACC as the authority for linguistic annotation, but edge cases exist. How should explicit disagreements be surfaced to users, rather than silently resolved?

## When does an ML hypothesis become a consensus reading?

BabyLemmatizer achieves 94–96% accuracy on in-vocabulary forms. If it lemmatizes 300,000 tokens and 95% are correct, that is 15,000 errors in the corpus. At what confidence threshold should a model hypothesis be treated as a working reading rather than a hypothesis? Who should have the authority to make that call — the model developer, the Glintstone maintainer, or the scholarly community?

## What does "Glintstone data is citable" actually require?

For a scholar to cite data found in Glintstone in a peer-reviewed publication, they need: a stable URL, a timestamp, a clear attribution chain, and confidence that the data will not change or disappear. Glintstone has the attribution chain. It does not yet have stable permalinks with versioning, a data availability commitment, or a DOI for the dataset itself. What would it take to get there?

## Elamite and Hittite corpora

Glintstone is built primarily around Sumerian and Akkadian, which dominate the cuneiform record. But Elamite (Persepolis Fortification Archive, ~2,000 texts) and Hittite (HETHITER.net, CHD) are significant corpora with their own specialists. Are the data model and annotation schema adequate for these languages, or do they assume too much about Sumero-Akkadian structure? What would need to change?

## The public/specialist divide

Glintstone's personas span from PhD Assyriologists to curious general readers. These groups have different needs. A museum curator wants quality control and attribution; a graduate student wants deep linguistic access; a hobbyist wants approachable explanations. Is there a way to serve all three without compromising the scholarly infrastructure for any of them? Or does serving general users necessarily create pressure that degrades scholarly reliability?
