# PHILO-3-01 - Record the decision

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** done
- **Depends on:** none
- **Unblocks:** the meeting loop
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** A1

## Problem

The owner cannot record a decision on the desk: `POST /api/decisions` answers 500 because the route factory deletes `ctx` at `holdspeak/web/routes/primitives/decisions.py:20` and its `_svc` closure reads it at `:27` (since aa865f57). Both live passes, both widths. Without a decision there is no decision-backed brief.

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.route.decisions_create; state.briefs.populated (setup); J10 populated/shelf

## Acceptance criteria

- [x] A decision recorded on the desk opens in its face and reopens after a reload; the reviewed-meeting provenance is proven by A2/A3's chain; a create/read failure is NAMED on the face.
- [x] A fence POSTs a decision through the real route and reads it back (id, text, source); a second fence proves the pre-fix 500.
- [x] Closure evidence: face create → exact id/text/source read back → reopen after a reload, at 1440 and 393; the shelf is exercised separately before any claim about it.

## Effort (council estimate, not a promise)

hours for the route; up to a day for the face path

## Built 2026-09-23 (Opus 5.5)

The defect was one line: `del ctx` at `holdspeak/web/routes/primitives/decisions.py:20`, removed to match the sibling primitive routers (`notes.py`, `kbs.py`, `directories.py`); the five other `del ctx` sites in the routes never read `ctx` afterwards. Fences: `tests/unit/test_philo3_01_decision_route.py` — a POST read back through the lifecycle router (id, title, decision_markdown, context_markdown, tags, status, then the list) and the pre-fix 500 loaded from `git show 7ce95358`. The face path: `desk.new-decision` (`verbRegistry.ts:147-158`; Desk menu / ⌘⇧N at 1440, Search at both widths) → `createPrimitive("decision")` → `POST /api/decisions`; reopen via Search → `DecisionPullout.tsx`; a create failure is already named on the face (`useWriteReceipt.ts:61-103`, "CREATE DECISION FAILED · HTTP n" with Retry). Rig (`docs/internal/philo/graph/atlas-phase3.json`, `case.a1.decision_face_create.reopened`): create through Search → read the id → reload → reopen → write the text → check on the hub → reload → reopen → check on the card; trigger = a bad status → 400 "invalid decision status": PASS at 1440 (`20260923T052321Z`) and 393 (`052332Z`), 0 console errors; the populated-brief setup now passes both widths; the shelf cases (acknowledged, deferred, refused 422) pass as protocol cases — no face claim for the shelf. Shots under `assets/story-01-shots/` (two extra runs recorded the Desk-menu path and its 393 block: the Desk menu is hidden at 393, so New Decision is reachable there only through Search).

**Round two (Astra's counsel paid, 2026-09-23):** New Decision now OPENS the decision's own window (`DecisionPullout`) straight in Edit (`dataSlice.ts`; a decision has no inline editor); on Done a default "New decision" title becomes the first line of the text, capped at 120 chars, never replacing an owner's own title (so the brief reads "Review decision: <first line>"). A failed decisions READ is named on the desk's receipt line — "READ DECISIONS FAILED · HTTP 500" with Retry — and a clean read clears it (`api.ts` `loadAll` returns the first failed collection); a failed CREATE already rendered "CREATE DECISION FAILED · HTTP n". The receipt's Retry and OK were raw `<button>`s on every desk receipt; now the library Button (`useWriteReceipt.ts`). At 393 the receipt slot collapsed to 0 px in the phone bar (the text was in the page but on no screen — the rig's text check passed while the shot showed nothing): it now sits in the strip between the bar and the work area (`chrome-menus.css`, 720 px rule). The rig gained an `http_fault` boundary (browser-side fault injection, recorded as a substitution). Rig: `case.a1.decision_face_create.opens_and_reopens` (6 setup checks, 0 console errors; title, text and source read back after reload), `case.a1.decision_face_create.failure_named`, `case.a1.decisions_read.failure_named`, `case.j10.arrival_generate_brief.populated` — all PASS at 1440 and 393. Vitest `philo301DecisionFace.test.tsx` fails 4/4 on HEAD, passes 4/4 now; `tsc` clean; the desk vitest baseline run below. Three owner-visible changes were built without a canvas (opening the existing window in Edit; the phone receipt placement; the library Button in every receipt) — the owner sees the shots before merge. Ledger: the supersede route is shadowed by the lifecycle router and emits zero change callbacks (Astra reproduced it; deferred). The reviewed-meeting provenance is A2/A3's chain (acceptance line reworded).

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
