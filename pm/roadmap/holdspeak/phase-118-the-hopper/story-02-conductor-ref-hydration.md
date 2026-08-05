# HS-118-02 — Conductor ref hydration

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** HS-118-04, HS-118-05
- **Owner:** unassigned

## The thesis (the bar)

The conductor's `_hydrate_item_grounding()` in
`workbench_conductor.py` reads `meeting_ids` and `artifact_ids` from
an item's `grounding_json`, but silently ignores the `refs` field.
Qualified refs like `zone:dir_abc` — the wire format that the
@-reference tokenizer (HS-118-04) and voice drawer resolution
(HS-118-05) produce — vanish before the agent ever sees the content
they point at.

The hydration pipeline in `holdspeak/grounding.py` already supports
qualified refs via `_hydrate_qualified()`. Zone refs expand to their
member content. The conductor just doesn't call it.

When this ships, `_hydrate_item_grounding()` forwards every field
from the grounding JSON — `meeting_ids`, `artifact_ids`, AND `refs`
— through the hydration pipeline. A workbench item grounded on
`zone:dir_abc` produces the same rich context the Ask pipeline
already delivers for the same ref.

**Articles served:** I (the Desk is the operating surface — zones are
first-class desk objects, not second-class to meetings), VI (honest
by construction — grounding that silently drops is a lie).

## Deliverables

1. **Forward `refs` in `_hydrate_item_grounding()`.** After
   extracting `meeting_ids` and `artifact_ids`, also read
   `refs: list[str]` from the parsed grounding JSON. Pass all three
   to `hydrate_grounding_blocks()`. The `refs` parameter already
   exists on that function — it's just never called with a value from
   the workbench path.

2. **Respect the grounding cap.** The existing cap is
   `GROUNDING_MAX_REFS = 16`. All ref types count toward the cap.
   If the total exceeds 16, truncate in this order: drop excess
   `refs` last-added-first, then `artifact_ids` last-added-first,
   preserving `meeting_ids` in their original order. Within each
   list, ordering is preserved from the grounding JSON array. Log a
   warning with the item ID, the number of refs dropped, and which
   refs were dropped.

3. **Coexistence and prompt ordering.** `meeting_ids`,
   `artifact_ids`, and `refs` all hydrate in the same prompt. They
   produce separate `[GROUNDING]` blocks in a stable order:
   meetings first, then artifacts, then qualified refs. This
   ordering is deterministic — the agent sees the same context for
   the same grounding regardless of when the run happens. No
   deduplication — if a meeting is referenced both by ID and by a
   zone ref that contains it, the content appears twice. This is
   honest (shows what was asked for) and avoids complex dedup logic.
   Token budget pressure is the natural governor.

## What NOT to do

- Do NOT change the grounding wire format. The `refs` field already
  exists in the schema. This story only unblocks its hydration in
  the conductor path.
- Do NOT add `expand` (summary vs full) support to workbench
  grounding yet. Default to full expansion.

## Test plan

- `uv run pytest -q tests/ -k workbench` — existing tests pass.
- New integration test: create a zone with two notes, create a
  workbench item with `grounding: {"refs": ["zone:dir_xxx"]}`, call
  `_hydrate_item_grounding()`, assert both notes' content appears in
  the hydrated output.
- New test: grounding with 20 total refs → only 16 hydrated, warning
  logged, meeting_ids preserved.
- New test: grounding with `meeting_ids` + `artifact_ids` + `refs`
  all present → all three hydrated in the same prompt.
- New test: `refs` containing an invalid qualified ref → graceful
  skip with warning, other refs still hydrate.
