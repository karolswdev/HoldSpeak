# decisions — Record, review and supersede an architecture decision

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430; anchors may drift).  Reviewer task: `review_decisions`.  Evidence class: source inspected, representative assertions read, and available 1440/393 desk-sweep captures inspected; no tests, live walk, or owner observation.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job has three variants: capture a meeting decision with bounded provenance; author and review a Desk decision; and replace one with a named successor while keeping the old record findable. After evidence, editing, refusal, restart, or supersession, the architect must return to a list where identity and current/replaced state are truthful. The audit treats these variants as one loop and does not specify actor, canonical record, Desk projection, or successor at each transition.

The existing guards are narrower than the job. `DecisionsView.test.tsx:122-192,231-320` protects list/detail navigation and late-read rejection; `tests/unit/test_decisions.py:195-235,315-336` protects backend lineage and refusal. They do not prove the live `DecisionPullout` edit/supersede loop.

FINDINGS:

1. **P0 — “Supersede” has no coherent successor outcome.** The pullout exposes `Replaced` as a direct `CycleGadget` state and calls only the status endpoint (`web/src/desk/pullouts/DecisionPullout.tsx:30-35,164-198`); it never supplies a successor. That status path updates and synchronizes the existing row (`holdspeak/services/primitive_service.py:259-274`); it does not call the separate Desk supersede operation, which creates a copied `Superseding ...` proposed successor (`holdspeak/services/primitive_service.py:276-289`; `holdspeak/db/primitives.py:327-339`). The canonical supersede route requires `successor_id` and writes lineage separately (`holdspeak/web/routes/decision_records.py:136-145`; `holdspeak/services/decision_record_service.py:417-495`). Owner cost: replacement can diverge from canonical history. This fails Tenets 3, 6, and 7. Correction: one operation must choose/create a named successor, update both identities atomically, return a receipt, and reopen the successor; withhold the direct status choice.

2. **P1 — Concurrent edits are not an honest conflict workflow.** Local generation counters protect late acknowledgements, not two windows or a stale canonical record (`web/src/desk/pullouts/DecisionPullout.tsx:129-163`). `DeskDecisionRepository.update` upserts without an expected revision (`holdspeak/db/primitives.py:304-316`), and canonical sync can preserve an authored record without telling a stale editor why (`holdspeak/services/decision_record_service.py:199-229`). Owner cost: a long ADR can be overwritten while Save appears successful. This fails Tenets 3 and 6. Correction: carry revision/updated-at, refuse stale writes by name, keep the draft, and offer refresh/reapply with a receipt.

3. **P1 — Review and provenance variants are under-specified.** New Decision posts an owner-authored row as `accepted` (`web/src/desk/store/dataSlice.ts:323-355`), while the canonical producer permits `accepted` or `proposed` (`holdspeak/web/routes/decision_records.py:63-89`). The audit does not define review of a meeting proposal versus an owner-authored record, or each return to the same ID. Source tags are retained (`holdspeak/services/decision_record_service.py:161-197`), but project sources have no open action and are filtered from evidence (`web/src/desk/pullouts/views/DecisionsView.tsx:515-547`). Owner cost: “reviewed” is ambiguous and source context disappears. This fails Tenets 3, 6, and 7. Correction: split variants; preserve source type/ref and provide open-source/parked-source state.

## Convergence

Converge `decisions` with `meeting_aftercare` for source identity/receipts, `meeting_archive` for restart findability, and `projects_room` for project links. Reuse `EDIT_IME` and draft/conflict behavior from `notes_editor`, plus the command registry, compositor, `DecisionRecordService`, and receipts. Keep successor lineage separate from meeting aftercare; a universal editor would erase the boundary and add Tenet-3 ceremony.

## User experience

The available captures (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-decisions-393.png` and `surface-decisions-1440.png`) show a compact, legible list with search, voice input, Current only, dates, and a proposed token. That likely pleases for finding and reading. They do not show edit, evidence, conflict, review, or replacement. Make source/state and the next verb clear; keep refusal, stale draft, and successor return in the same window. Beauty and accessibility remain unknown.

CONDITIONS: Add the three corrections with exact identity/status/receipt contracts and recovery/return behavior for each variant. Keep existing list/read and lineage guards; add assertions for the cross-surface same-ID path before completeness claims.

MISSED:

1. Named successor creation and old/new return state (highest cost).
2. Two-window stale edit with preserved draft.
3. Parked or unavailable meeting/project source without invented evidence.
4. Restart after an edit or replacement with canonical and Desk identities aligned.

TUESDAY: The list-to-read path is plausible, but the architect cannot yet trust the list-to-edit-to-replace path without losing provenance or creating an unnamed successor.

## Acceptance challenges

1. Create a decision from the palette with a title and rationale; open it from Decisions, edit all three fields, close/reopen, and confirm the same ID, body, and source remain visible.
2. Open a meeting-derived proposed decision, inspect its transcript source, accept it, return to the list, then supersede it with a named successor; the old row says REPLACED and the successor is CURRENT in both Desk and canonical record views.
3. Open the same decision through two supported editing views or browser sessions; save one first. The second save is refused as stale, preserves its draft, and can refresh/reapply without overwriting the first.
4. Park or remove the linked meeting source, reopen the decision, and verify the decision remains findable while the source is explicitly unavailable and no evidence is fabricated.
UNKNOWN: No tests were executed; no live Desk, provider, native, API, or owner-state action was taken; no owner acceptance, accessibility, performance, or WebKit proof exists. Captures show list presentation only, not execution or delight.
