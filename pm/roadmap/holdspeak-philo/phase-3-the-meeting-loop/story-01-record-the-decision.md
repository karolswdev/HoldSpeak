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

- [x] The existing decision face saves a decision from the reviewed meeting and reopens it; a create/read failure is NAMED on the face.
- [x] A fence POSTs a decision through the real route and reads it back (id, text, source); a second fence proves the pre-fix 500.
- [x] Closure evidence: face create → exact id/text/source read back → reopen after a reload, at 1440 and 393; the shelf is exercised separately before any claim about it.

## Effort (council estimate, not a promise)

hours for the route; up to a day for the face path

## Built 2026-09-23 (Opus 5.5)

The defect was one line: `del ctx` at `holdspeak/web/routes/primitives/decisions.py:20`, removed to match the sibling primitive routers (`notes.py`, `kbs.py`, `directories.py`); the five other `del ctx` sites in the routes never read `ctx` afterwards. Fences: `tests/unit/test_philo3_01_decision_route.py` — a POST read back through the lifecycle router (id, title, decision_markdown, context_markdown, tags, status, then the list) and the pre-fix 500 loaded from `git show 7ce95358`. The face path: `desk.new-decision` (`verbRegistry.ts:147-158`; Desk menu / ⌘⇧N at 1440, Search at both widths) → `createPrimitive("decision")` → `POST /api/decisions`; reopen via Search → `DecisionPullout.tsx`; a create failure is already named on the face (`useWriteReceipt.ts:61-103`, "CREATE DECISION FAILED · HTTP n" with Retry). Rig (`docs/internal/philo/graph/atlas-phase3.json`, `case.a1.decision_face_create.reopened`): create through Search → read the id → reload → reopen → write the text → check on the hub → reload → reopen → check on the card; trigger = a bad status → 400 "invalid decision status": PASS at 1440 (`20260923T052321Z`) and 393 (`052332Z`), 0 console errors; the populated-brief setup now passes both widths; the shelf cases (acknowledged, deferred, refused 422) pass as protocol cases — no face claim for the shelf. Shots under `assets/story-01-shots/` (two extra runs recorded the Desk-menu path and its 393 block: the Desk menu is hidden at 393, so New Decision is reachable there only through Search).

**Findings for the council (face changes, not made here):** New Decision answers 201 and NOTHING OPENS on the Chair (`INLINE_EDITOR_CONTENT.decision` is null, `pullouts/editors/registry.ts:39`) — the owner must Search for what he just made; no title at create ("New decision" until Edit); a failed decisions READ is only an `aria-label` on the hub dot (`DeskChrome.tsx:144-150`); Retry/Dismiss in the write receipt are raw `<button>`s (shared by the desk); the reviewed-meeting path confirms a decision through `/api/proposals/{id}/confirm`, not this route — the acceptance box's "from the reviewed meeting" is A2/A3's chain, verified there; a desk decision has no `source` field (context_markdown + tags carry it). UNKNOWN: both routers declare `POST /api/decisions/{id}/supersede` and the lifecycle router is included first (possible shadowing, untested).

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
