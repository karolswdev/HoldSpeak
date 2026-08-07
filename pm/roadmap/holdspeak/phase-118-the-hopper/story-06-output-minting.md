# HS-118-06 — Output minting

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** HS-118-09
- **Owner:** unassigned

## The thesis (the bar)

Today a workbench result is a plain string stored on
`WorkbenchItemRecord.result`. The "Keep" verb is manual, per-item,
creates an artifact through `keepReply()` with minimal lineage
(`source_type: "recipe"`), and loses the egress boundary. The minted
artifact has no link back to the workbench item, no grounding
provenance, and no way to know "this result was already kept."

When this ships, every successful workbench item auto-mints an
artifact in `pending-review` state. The mint is a consequential
operation admitted through the kernel (Article XI). The minted
artifact carries full provenance: egress boundary, source workbench
item, original grounding refs, recipe, and run ID. The item record
links to the minted artifact via `result_artifact_id`.

The artifact is NOT immediately a desk object. It enters
`pending-review` — a proposal. The owner triages it in HS-118-09
(accept, reject, rework). The workbench proposes; the owner approves.
This is Article V: consent is the spine of action.

**Articles served:** V (consent — minted artifacts require owner
triage before becoming desk objects), XI (kernel admission — every
auto-mint enters the kernel as a consequential operation), III
(honest egress — provenance travels from inference to artifact),
II (DeskPrimitive contract — results become typed primitives).

## Deliverables

1. **New field: `result_artifact_id`.** Add `result_artifact_id
   TEXT` to the `workbench_items` table (nullable, default NULL).
   Add the corresponding field to `WorkbenchItemRecord` and to
   `WorkbenchItem` in `detail-types.ts`.

2. **New artifact status: `pending-review`.** Add to the artifact
   status vocabulary alongside `draft`, `final`, etc. Artifacts in
   `pending-review` are visible in the workbench triage surface
   (HS-118-09) but do NOT appear in the main desk primitive list
   until accepted (promoted to `draft`). They are real DB records
   with full lineage — not ephemeral.

3. **Kernel-admitted auto-mint in the conductor.** In
   `run_workbench()`, after successful inference:

   a. Admit the mint operation through the kernel. The conductor
      submits a kernel request — the kernel authenticates the
      caller, derives the principal and authority (Article XI.3 —
      callers do not supply authority), and admits or refuses:
      ```python
      kernel.submit(
          kind="workbench_mint",
          target=f"workbench_item:{item.id}",
          context={"recipe_id": recipe.id, "run_id": run.id},
      )
      ```
      The kernel derives authority from the authenticated owner
      context. The conductor does not claim authority.

   b. Mint the artifact via `_persist_run_artifact()`:
      - `artifact_type`: `"workbench_output"`
      - `title`: `"{recipe_name}: {item_title}"`
      - `body_markdown`: raw result string
      - `status`: `"pending-review"`
      - `plugin_id`: `"workbench_run"`
      - `sources`: full lineage array:
        ```python
        [
          {"source_type": "workbench_item", "source_ref": item.id},
          {"source_type": "recipe", "source_ref": recipe.id},
        ]
        ```
      - `structured_json`: provenance envelope:
        ```python
        {
          "egress": {"boundary": target.boundary, "model": target.model},
          "grounding_refs": json.loads(item.grounding_json),
          "workbench_id": workbench.id,
          "run_id": run.id,
        }
        ```

   c. Link: `item.result_artifact_id = artifact_id`.

   d. Terminal receipt on the kernel operation.

4. **Idempotent minting.** The mint is keyed by `(run_id, item_id)`.
   A unique database constraint on
   `(run_id, item_id)` in the artifacts table (via a
   `source_run_id` + `source_item_id` column pair) prevents
   duplicate mints at the DB level — not just by checking
   `result_artifact_id` in application code. The artifact creation
   and item link update are persisted in a single transaction —
   both succeed or neither does. Concurrent retries that race past
   the application check hit the DB constraint and are safely
   rejected.

5. **Register source and artifact types.**
   - Add `"workbench_item"` to `CANONICAL_SOURCE_TYPES` and
     `VALID_ARTIFACT_SOURCE_TYPES`.
   - Add `"workbench_output"` to the artifact type vocabulary.

6. **New WebSocket event: `workbench.item_minted`.** Emitted after
   artifact persistence:
   ```python
   _emit("workbench.item_minted", {
       "workbench_id": workbench.id,
       "item_id": item.id,
       "artifact_id": artifact_id,
       "artifact_title": title,
   })
   ```

7. **Frontend item card update.** When `result_artifact_id` is
   present:
   - Remove the "Keep" verb (it already happened).
   - Show an "Open" chip that opens the artifact's pullout card.
   - Show the artifact title below the result text.
   - Show `EgressChip` from the artifact's provenance.
   - Show a `pending-review` status chip on the artifact link
     (visually distinct from `draft`).

8. **Failure semantics.** If inference succeeds but minting fails
   (DB error, kernel refusal): the item is marked `done` with its
   result, but `result_artifact_id` remains null. The item card
   shows a visible "Mint failed" warning chip (not just a log
   warning) and a "Retry mint" verb that re-attempts the
   kernel-admitted mint into `pending-review`. The legacy "Keep"
   path is NOT offered as a fallback — it would bypass the consent
   and provenance model. The run receipt records the mint failure.

9. **Backward compatibility.** Existing items with results but no
   `result_artifact_id` (created before this story shipped) show the
   legacy "Keep" verb. No migration of historical results. New items
   always go through the auto-mint path.

10. **Open chip scope.** The "Open" chip on a `pending-review`
    artifact opens the artifact's detail as an inline expansion of
    the triage surface (HS-118-09) — NOT as an independently
    discoverable desk pullout. `pending-review` artifacts are not
    in the main primitive list and cannot be opened outside the
    workbench context.

## What NOT to do

- Do NOT auto-file the artifact into a zone. It enters
  `pending-review` unfiled.
- Do NOT add a "disable auto-mint" toggle. Every successful result
  mints. The triage gate (HS-118-09) is where the owner decides.
- Do NOT stream the result into the artifact during inference. Mint
  after completion, from the final result.

## Test plan

- `uv run pytest -q tests/ -k workbench` — existing tests pass.
- New integration test: run a workbench with one pending item →
  item has `result_artifact_id`, artifact exists with status
  `pending-review`, correct `artifact_type`, `sources`,
  `structured_json.egress`, and `structured_json.grounding_refs`.
- New test: kernel admission recorded with correct kind/authority.
- New test: retry after partial failure → no duplicate artifact
  (idempotent by run_id + item_id).
- New test: mint failure → item is `done` with result,
  `result_artifact_id` is null, warning logged, "Keep" available.
- New test: `workbench.item_minted` event emitted with correct
  payload.
- New test: `pending-review` artifacts do NOT appear in main
  primitive listing.
- `npx vitest run` — frontend tests:
  - Item with `result_artifact_id` shows "Open" instead of "Keep."
  - Item without `result_artifact_id` shows "Keep."
  - `pending-review` chip visible on artifact link.
- Visual at 1440: completed item card shows artifact link + egress
  chip + pending-review indicator.
