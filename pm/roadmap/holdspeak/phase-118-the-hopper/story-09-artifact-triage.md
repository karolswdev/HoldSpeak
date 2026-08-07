# HS-118-09 — Artifact triage

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** HS-118-06
- **Unblocks:** --
- **Owner:** unassigned

## The thesis (the bar)

HS-118-06 auto-mints artifacts in `pending-review` state. Without a
triage surface, those artifacts are invisible proposals with no path
to acceptance. The workbench proposes output; the owner must be able
to accept, reject, or rework each result before it becomes a real
desk object. This is Article V: consent is the spine of action.
Propose → approve → execute.

When this ships, the workbench item card shows a triage strip for
every `pending-review` artifact. The owner can:

- **Accept** — promotes the artifact to `draft` status. It appears in
  the desk primitive list, can be filed in zones, and behaves like
  any artifact.
- **Reject** — deletes the artifact and marks the workbench item as
  `dismissed`. The result text is preserved on the item for audit but
  the artifact is gone. No orphan desk objects.
- **Rework** — resets the workbench item to `pending` with an
  optional refinement note appended to the body. The rejected artifact
  is archived (status `"rejected"`, retained in DB for lineage but
  hidden from all surfaces). On the next run, the agent re-processes
  the item with the refinement context.

**Articles served:** IV (every text input can be spoken into — the
rework refinement input gets a MicButton), V (consent — owner
approves before artifacts reach the desk), VI (honest by
construction — rejected artifacts are archived for lineage, not
silently deleted), XI (kernel — each triage verb is a consequential
operation admitted with a terminal receipt; the kernel authenticates
the caller and derives authority).

## Deliverables

1. **Triage strip on the item card.** When a workbench item has
   `result_artifact_id` and the linked artifact's status is
   `pending-review`, the item card shows a triage strip below the
   result section:

   ```
   wb-triage-strip               flex row, gap 6px
   ├── desk-chip "Accept"        data-tone="ok"
   ├── desk-chip "Rework"        data-tone="warn"
   └── desk-chip "Reject"        data-tone="danger"
   ```

   The strip is visible only for `pending-review` artifacts. Once
   triaged, it disappears.

2. **Accept verb.** Clicking Accept:
   - Calls `POST /api/workbenches/{id}/items/{item_id}/triage` with
     `{action: "accept"}` (the dedicated triage endpoint — never
     the generic `PUT /api/artifacts/{id}`, which would bypass
     validation, kernel admission, and item-state updates).
   - The artifact status changes to `draft`. It appears in the main
     desk primitive list.
   - The item card updates: triage strip disappears, "Open" chip
     remains (now opens a real desk pullout), status shows
     "Accepted."
   - Kernel admission: the endpoint submits to the kernel (the
     kernel authenticates the owner and derives authority —
     Article XI.3). Terminal receipt recorded.

3. **Reject verb.** Clicking Reject:
   - Shows a confirmation (ConfirmVerb — two-click pattern, matching
     the existing "Clear all" memory pattern).
   - On confirm: calls the triage endpoint with
     `{action: "reject"}`.
   - The artifact status changes to `"rejected"` — it is archived
     in the DB for lineage, NOT deleted. Archived artifacts are
     retained but hidden from all user-facing surfaces.
   - The workbench item status changes to `dismissed`.
   - The item card shows the original result text (for audit) with a
     "Rejected" chip.
   - `result_artifact_id` is cleared on the item.
   - Kernel admission with terminal receipt.

4. **Rework verb.** Clicking Rework:
   - Shows a one-line text input with a MicButton (Article IV —
     every text input can be spoken into): "What should change?"
     (optional refinement note).
   - On submit: the existing artifact is archived (status
     `"rejected"`), `result_artifact_id` is cleared, and the item
     resets to `pending`:
     - If a refinement note was provided, it's appended to the item
       body: `\n\n[REFINEMENT]\n{note}`.
     - The item's `result` is cleared.
     - The item's `status` returns to `pending`.
   - On the next workbench run, the agent processes this item again.
     The refinement note is visible in the instruction. The agent's
     memory may also recall the previous attempt.
   - Kernel admission: `kind: "workbench_triage"`,
     `action: "rework"`.

5. **Backend: triage API.** New endpoint:

   ```
   POST /api/workbenches/{id}/items/{item_id}/triage
   Body: { "action": "accept" | "reject" | "rework",
           "refinement"?: string }
   ```

   The endpoint validates that the item belongs to the workbench,
   has a `result_artifact_id`, and the artifact is in
   `pending-review`. Returns 409 if already triaged. Each action is
   kernel-admitted with a terminal receipt.

6. **Batch triage.** A "Triage all" section at the top of the items
   wing when there are 2+ pending-review items. Shows count:
   "3 outputs awaiting review." Two batch verbs:
   - "Accept all" — promotes all pending-review artifacts to draft.
     Each item is individually kernel-admitted with its own receipt.
     If any individual accept fails, the others still proceed
     (partial success). The result summary shows: "Accepted N,
     failed M" with failed items retaining their triage strip.
   - "Dismiss all" — rejects all (with ConfirmVerb). Same
     per-item admission and partial-failure semantics.

   No batch rework — rework requires per-item refinement notes.

7. **WebSocket events.**
   - `workbench.item_triaged`: `{workbench_id, item_id,
     artifact_id, action, refinement?}`.
   - The frontend subscribes and refreshes the item list on receipt.

8. **Artifact status vocabulary update.** Ensure the artifact status
   set includes `pending-review` and `rejected`. `rejected` artifacts
   are retained in the DB for lineage queries but hidden from all
   user-facing surfaces (desk primitive list, zone members, search).

## What NOT to do

- Do NOT auto-accept artifacts. Every output requires explicit owner
  triage. The workbench is an agent; agents propose, owners approve.
- Do NOT show `pending-review` or `rejected` artifacts in the main
  desk primitive list, zone members, or search results. They are
  only visible in the workbench item card triage surface.
- Do NOT add a "triage later" or "snooze" state. Accept, reject, or
  rework. Three verbs, no deferrals.

## Test plan

- `uv run pytest -q tests/ -k workbench` — existing tests pass.
- New integration tests:
  - Triage accept: artifact status → `draft`, appears in primitive
    list, kernel receipt recorded.
  - Triage reject: artifact status → `rejected`, item → `dismissed`,
    `result_artifact_id` cleared, kernel receipt recorded.
  - Triage rework: artifact → `rejected`, item → `pending`, body
    has `[REFINEMENT]` note, `result_artifact_id` cleared.
  - Double triage → 409.
  - Triage on item without artifact → 404.
  - Batch accept: all pending-review → draft.
  - `rejected` artifacts hidden from primitive listing.
- `npx vitest run` — frontend tests:
  - Triage strip renders for `pending-review` items.
  - Accept click → strip disappears, "Accepted" shown.
  - Reject click → ConfirmVerb (two-click), then "Rejected" shown.
  - Rework click → refinement input shown, submit resets item.
  - Batch triage section appears with 2+ pending-review items.
- Visual at 1440: triage strip below result, three colored chips,
  refinement input on rework.
- Visual at 393: triage strip wraps or scrolls, chips remain
  tappable.
