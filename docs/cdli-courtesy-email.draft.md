---
question: "What's the draft of the heads-up email to CDLI about Glintstone's imagery ingestion?"
created: 2026-05-12
modified: 2026-05-12
context: "Drafted while building the image pipeline (R2 + artifact_images + crawler). CDLI is our most-cited source; this email gives them a chance to flag concerns about the scrape rate or scope before we kick off the long background crawler."
status: draft
audience: [eric]
owners: [eric]
related_issues: ["#52"]
related_skills: [gs-expert-deployment, gs-expert-integrations]
supersedes: null
superseded_by: null
---

# Courtesy email to CDLI — draft

**To**: cdli@cdli.mpiwg-berlin.mpg.de
**From**: eric.wittke@gmail.com
**Subject**: Glintstone — academic web app indexing CDLI imagery (heads-up)

---

Hello CDLI team,

I'm building [Glintstone](https://app.glintstone.org), a web app for
cuneiform scholars that aggregates and cross-references CDLI, ORACC, eBL,
and ePSD2 data with proper per-source attribution. CDLI is the backbone of
the project — every dependent feature credits CDLI in its UI.

I wanted to give you a heads-up about how I'm using cdli.earth so there are
no surprises and so I can adjust if any of this is unwelcome:

**Catalog data**: I use the public daily CSV dump from `cdli-gh/data` for
artifact metadata. No issue there — that's how the repo is intended to be
consumed.

**Imagery**: This is the part I wanted to flag. To put tablet thumbnails on
artifact cards, I'm fetching individual artifact pages on `cdli.earth`
(e.g. `https://cdli.earth/P000001`), parsing the per-image copyright string
verbatim, then downloading the `/dl/photo/*.jpg` and `/dl/lineart/*_l.jpg`
binaries. Originals + 400px WebP thumbnails are then cached in our own
Cloudflare R2 bucket.

I'm respecting `robots.txt` (Crawl-delay: 60), throttled in code so background
crawling tops out at one request per minute. User-Agent on every request
identifies Glintstone and includes my contact email.

Each image we cache stores the verbatim © string from your page and surfaces
it on every artifact card (`Image courtesy of {institution}, via CDLI`).
Originals link back to CDLI.

If any of this is something you'd like me to throttle further, gate behind a
shared dataset, or stop entirely while we work out a more sustainable arrangement,
just let me know and I'll adjust same-day. I'd also be happy to push any
improvements (e.g. a per-image attribution parser) back upstream as a
contribution if useful.

Thanks for everything CDLI has built — most of what Glintstone does is only
possible because the underlying corpus is open.

Best,
Eric Wittke
eric.wittke@gmail.com
https://app.glintstone.org
