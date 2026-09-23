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

**Owner ruling 2026-09-23 on the 393 receipt placement (canvas `assets/story-01-canvas/`, published at https://claude.ai/artifact/PGZa6PxgXmc12R7presoqv): FULL-WIDTH ROW, the work moves down while a failure stands, the whole cause reads; the strip under the bar is withdrawn. Built in round four: `DeskReceiptRow.tsx` renders the backstop receipt as a full-width in-flow row under the bar at phone width (one seat: the bar drops its receipt there), measuring its height so the Chair starts below it; no failure = no row, no reserved space; the label wraps at 12 px, Retry/OK own 44 px hits; `write-receipt.css` has no viewport query (intrinsic reflow) and `containerQueryLaw.test.ts` passes without a widened exception — the seat choice comes from the shell's existing `useCompactViewport` hook (the menu bar's own fold), not a CSS query; the hit fence asserts the row is in flow, full width, uncut, above the Chair; the three atlas-phase3 cases pass at both widths with new runs; canvas `receipt-row-393.{html,png}` shows the three real 393 frames (both causes now read whole). Not verified: the Floor and list view at 393 (the row sits above a separately laid-out surface); the Chair's bottom capture panel scrolls inside the shorter Chair while a failure stands.**

**Round three (Astra's second counsel paid, 2026-09-23):** automatic Edit and the Edit button seed their drafts from the current record (a quick reopen inside the 4.5 s new-object marker no longer erases saved text; fence `philo301DecisionNoLoss.test.tsx` fails on the previous code); a read failure never replaces a standing CREATE/SAVE receipt and a clean read clears only a READ receipt (fence `philo301RetryKept.test.tsx`: fault the POST and the GET, refresh while faulted, recover both, click the rendered Retry → one record); the shared write receipt reaches the 12 px floor on its label and verbs, grows to hold 44 px hit areas at 393, gets the footer's full second row (the Brief receipt was clipped to "ACK…" in a 400 px pullout before this story), and the chrome receipt no longer clips its verbs at 1440; a real-hub hit fence (`tests/e2e/test_philo3_01_receipt_hits.py`) probes nine points on Retry and OK for the chrome, Thread and Brief receipts at both widths with the HS-202-05 classifier and a real pointer; `http_fault` matches the hub's origin only and `http_fault_lift` lets a case recover; the atlas-phase3 cases run THROUGH Retry (create: faults → receipt stands → lift → Retry → 201; read: faults → receipt → lift → Retry → gone) and pass at 1440 and 393. The 393 receipt strip (top 38 px, clear of the bar's controls) is DESIGN and awaits the owner: canvas `assets/story-01-canvas/receipt-strip-393.{html,png}` (real 393 frames of the three states) with one question — the strip under the bar (the create label cuts its cause at the 12 px floor; full text in `title`), or a full-width row that moves the work down while a failure stands. Desk vitest baseline: zero branch-new.

**Round two (Astra's counsel paid, 2026-09-23):** New Decision now OPENS the decision's own window (`DecisionPullout`) straight in Edit (`dataSlice.ts`; a decision has no inline editor); on Done a default "New decision" title becomes the first line of the text, capped at 120 chars, never replacing an owner's own title (so the brief reads "Review decision: <first line>"). A failed decisions READ is named on the desk's receipt line — "READ DECISIONS FAILED · HTTP 500" with Retry — and a clean read clears it (`api.ts` `loadAll` returns the first failed collection); a failed CREATE already rendered "CREATE DECISION FAILED · HTTP n". The receipt's Retry and OK were raw `<button>`s on every desk receipt; now the library Button (`useWriteReceipt.ts`). At 393 the receipt slot collapsed to 0 px in the phone bar (the text was in the page but on no screen — the rig's text check passed while the shot showed nothing): it now sits in the strip between the bar and the work area (`chrome-menus.css`, 720 px rule). The rig gained an `http_fault` boundary (browser-side fault injection, recorded as a substitution). Rig: `case.a1.decision_face_create.opens_and_reopens` (6 setup checks, 0 console errors; title, text and source read back after reload), `case.a1.decision_face_create.failure_named`, `case.a1.decisions_read.failure_named`, `case.j10.arrival_generate_brief.populated` — all PASS at 1440 and 393. Vitest `philo301DecisionFace.test.tsx` fails 4/4 on HEAD, passes 4/4 now; `tsc` clean; the desk vitest baseline run below. Three owner-visible changes were built without a canvas (opening the existing window in Edit; the phone receipt placement; the library Button in every receipt) — the owner sees the shots before merge. Ledger: the supersede route is shadowed by the lifecycle router and emits zero change callbacks (Astra reproduced it; deferred). The reviewed-meeting provenance is A2/A3's chain (acceptance line reworded).

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
