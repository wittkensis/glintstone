# Report an Error

Glintstone data comes from multiple open-access sources and may contain errors in transcription, lemmatization, metadata, or attribution. Domain experts finding problems are exactly who we want to hear from.

## Via the MCP tool (if you're using Claude)

If you're working with Glintstone through Claude, use the `submit_correction` tool. Provide:

- The `interaction_id` from the response you're correcting
- The claim that is wrong (`claim`)
- What it should say (`correction`)
- An optional scholarly citation (`evidence`)
- Your scholar ID from the Glintstone database, if you know it (`scholar_id`)

The correction is stored as a new annotation run with method `agent-hypothesis-correction`, and any cached outputs that cited the corrected annotation are invalidated. Corrections are permanent and attributed.

## Via email

Email [eric.wittke@gmail.com](mailto:eric.wittke@gmail.com) with:

- The P-number of the tablet (e.g., P227657)
- A description of what is wrong
- A correction or a reference to the correct reading

We want to hear from Assyriologists, curators, and anyone who knows the texts. The more specific, the better.

## What happens to a correction

Corrections flow into the same annotation run infrastructure as all other data. They do not overwrite existing records — they create new ones. The original interpretation remains in the database with its provenance intact. The correction is layered on top.

For errors in source data (e.g., something wrong in the CDLI catalog), we will flag it upstream and note the discrepancy in Glintstone's records.
