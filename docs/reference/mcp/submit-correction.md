# submit_correction

Submit a scholarly correction of something the agent said.

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `interaction_id` | integer | yes | From `ToolResponse.interaction_id` of the response being corrected |
| `claim` | string | yes | The specific claim the agent made that is wrong |
| `correction` | string | yes | What the correct interpretation is |
| `evidence` | string | no | Scholarly citation supporting the correction |
| `scholar_id` | integer | no | Links to `scholars` table for attribution |

The `interaction_id` is the integer in the `interaction_id` field of any `ToolResponse`. Every response from `semantic_search`, `summarize_artifact`, and `interpret_token` includes one.

## What happens

1. A new row is created in `annotation_runs` with `source_name='user-correction'` and `method='agent-hypothesis-correction'`. If `scholar_id` is provided, the run is attributed to that scholar.

2. A row is created in `interaction_feedback` recording the full correction payload: the original claim, the correction, and the evidence.

3. Any cached `agent_outputs` that cited the corrected annotation are marked for regeneration. The next call to `summarize_artifact` for the same P-number will regenerate rather than return the cached result.

4. The correction is returned with its assigned IDs.

## Permanence and attribution

Corrections are permanent. They do not delete or overwrite existing data. The original interpretation remains in the database with its provenance intact. The correction layers on top as a new annotation run.

If `scholar_id` is provided, the correction is attributed in the `annotation_runs.scholar_id` column. Corrections are discoverable via the annotation run history.

## Example

```python
# After interpret_token returns an incorrect reading:
submit_correction(
    interaction_id=44,
    claim="The agent read lu₂-gal as lugal[king]N",
    correction="This sign sequence in this context should be read as lugal[owner]N — the administrative genre and parallel texts from Nippur support the 'owner' sense",
    evidence="Steinkeller 1987, FAOS 9/2, p. 62",
    scholar_id=1234
)
```

## Response

```json
{
  "interaction_id": 44,
  "feedback_id": 17,
  "new_annotation_run_id": 88,
  "message": "Correction recorded. The next request that re-loads any agent output citing the corrected annotation will regenerate."
}
```
