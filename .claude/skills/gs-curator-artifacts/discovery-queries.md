---
question: "I need to find a record matching specific criteria — what SQL gets there fastest?"
created: 2026-05-11
modified: 2026-05-11
context: "Created during the 2026-05-11 overhaul. Each query template is named after a scenario in catalog.yaml; running them against Neon should produce a candidate to add to the catalog."
status: active
audience: [claude, engineers]
owners: [eric]
related_issues: []
related_skills: [gs-curator-artifacts, gs-expert-data-model]
supersedes: null
superseded_by: null
---

# Discovery queries

Each query finds candidates for a scenario. Run against Neon (or local Postgres), pick the best result, add to `catalog.yaml`, mirror into `tests/fixtures/fixtures.py`.

## Artifacts

### Tablet with rich linguistic data

```sql
SELECT a.p_number, a.designation, a.period_normalized, a.provenience_normalized,
       COUNT(DISTINCT tl.id)  AS lines,
       COUNT(DISTINCT t.id)   AS tokens,
       COUNT(DISTINCT l.id)   AS lemmas,
       COUNT(DISTINCT tr.id)  AS translations
FROM artifacts a
JOIN text_lines tl    ON tl.artifact_id = a.id
JOIN tokens t         ON t.line_id = tl.id
LEFT JOIN lemmatizations l ON l.token_id = t.id
LEFT JOIN translations tr  ON tr.artifact_id = a.id
WHERE a.designation IS NOT NULL
  AND a.period_normalized IS NOT NULL
GROUP BY a.id
HAVING COUNT(DISTINCT l.id) > 100
   AND COUNT(DISTINCT tr.id) > 50
ORDER BY lemmas DESC, translations DESC
LIMIT 5;
```

### Joined fragments

```sql
SELECT p_number, designation
FROM artifacts
WHERE designation ~ '\+'
  AND period_normalized IS NOT NULL
ORDER BY length(designation) DESC
LIMIT 10;
```

### Multi-surface tablet

```sql
SELECT a.p_number, a.designation, COUNT(DISTINCT s.id) AS surface_count
FROM artifacts a
JOIN surfaces s ON s.artifact_id = a.id
GROUP BY a.id
HAVING COUNT(DISTINCT s.id) >= 4
ORDER BY surface_count DESC
LIMIT 5;
```

### Bilingual tablet (Sumerian-Akkadian)

```sql
SELECT a.p_number, a.designation, COUNT(DISTINCT l.language) AS langs
FROM artifacts a
JOIN text_lines tl ON tl.artifact_id = a.id
JOIN tokens t      ON t.line_id = tl.id
JOIN lemmatizations l ON l.token_id = t.id
WHERE l.language IS NOT NULL
GROUP BY a.id
HAVING COUNT(DISTINCT l.language) >= 2
ORDER BY COUNT(DISTINCT t.id) DESC
LIMIT 5;
```

### Tablet with competing lemmatizations on the same token

```sql
SELECT t.id, COUNT(DISTINCT l.annotation_run_id) AS interpretations
FROM tokens t
JOIN lemmatizations l ON l.token_id = t.id
GROUP BY t.id
HAVING COUNT(DISTINCT l.annotation_run_id) > 1
LIMIT 10;
```

## Scholars

### Scholar with merge history

```sql
SELECT s.id, s.display_name, COUNT(*) AS merge_count
FROM scholars s
JOIN scholar_merge_log m ON m.kept_scholar_id = s.id
GROUP BY s.id
HAVING COUNT(*) > 3
ORDER BY merge_count DESC
LIMIT 5;
```

### Scholar — both ATF editor and ORACC author

```sql
SELECT s.id, s.display_name
FROM scholars s
WHERE EXISTS (SELECT 1 FROM artifact_editions e WHERE e.scholar_id = s.id)
  AND EXISTS (SELECT 1 FROM publication_authors pa WHERE pa.scholar_id = s.id)
  AND s.orcid IS NOT NULL
LIMIT 10;
```

## Lemmas

### High-polysemy lemma

```sql
SELECT l.id, l.citation_form, l.language_code, l.source,
       COUNT(s.id) AS sense_count, l.attestation_count
FROM lexical_lemmas l
JOIN lexical_senses s ON s.lemma_id = l.id
GROUP BY l.id
HAVING COUNT(s.id) > 10
ORDER BY sense_count DESC, l.attestation_count DESC
LIMIT 10;
```

### High-attestation lemma

```sql
SELECT id, citation_form, guide_word, language_code, attestation_count
FROM lexical_lemmas
ORDER BY attestation_count DESC
LIMIT 20;
```

### Lemma backed by a Sumerogram

```sql
SELECT l.id, l.citation_form, l.language_code, c.sumerogram
FROM lexical_lemmas l
JOIN cad_logograms c ON c.lemma_id = l.id
WHERE l.language_code = 'akk'
LIMIT 20;
```

## Signs

### Sign with no Unicode mapping

```sql
SELECT s.id, s.name, COUNT(*) AS attestations
FROM signs s
LEFT JOIN sign_values v ON v.sign_id = s.id
WHERE s.unicode_codepoint IS NULL
GROUP BY s.id
ORDER BY attestations DESC
LIMIT 10;
```

### High-polyvalency sign

```sql
SELECT s.id, s.name, COUNT(v.id) AS value_count
FROM signs s
JOIN sign_values v ON v.sign_id = s.id
GROUP BY s.id
HAVING COUNT(v.id) > 5
ORDER BY value_count DESC
LIMIT 10;
```

## Composites

### Composite with many exemplars

```sql
SELECT c.q_number, c.designation, COUNT(ac.artifact_id) AS exemplar_count
FROM composites c
JOIN artifact_composites ac ON ac.composite_id = c.id
GROUP BY c.id
ORDER BY exemplar_count DESC
LIMIT 10;
```

## How to use these queries

1. Run via psql or the admin dashboard.
2. Pick the top candidate (usually) — best is highest count + interesting metadata.
3. Verify the record is meaningful (spot-check via `/tablets/<p>` or `/dictionary/<id>`).
4. Add to `catalog.yaml` with `as_of: <today>` and an appropriate `usefulness:` tag.
5. Add a constant to `tests/fixtures/fixtures.py`.
6. Reference in the test that exercises this scenario.

## Adding new query templates

When a new entity type or scenario emerges, add a section here. Each query should:

- Run in < 1 second on Neon (use indexes; avoid full table scans)
- Return ≤ 20 rows
- Include enough metadata in the SELECT to make picking obvious
