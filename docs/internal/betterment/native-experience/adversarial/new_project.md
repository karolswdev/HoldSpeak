# new_project

Job: create a project from a name and selected sources  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_new_project`  
Evidence class: active source, assertions, and existing 1440/393 captures; no execution or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at Projects or the Desk command (`web/src/pages/cores/ProjectsCore.tsx:124-128`, `web/src/desk/applications.ts:377-393`), names the outcome, checks optional sources, selects material and watches, creates one durable project, opens its Room by `project:<id>`, and returns to work. Cancel must leave no project; provider refusal, partial found-link failure, duplicate/stale source, and failed create must remain recoverable. The current record omits its trigger, Room return, blank choice, and close/reopen path. Existing assertions cover blank/cancel (`web/src/features/project-room/door/__tests__/newProject.app.test.tsx:78-104`), provider failure/partial retry (`web/src/features/project-room/door/__tests__/DoorCore.test.tsx:585-616,747-826`), and durable blank facts (`tests/integration/test_desk_new_project.py:44-63`).

FINDINGS:

1. **P1 — the stated source authority is wrong and the scope is too narrow.** `docs/USE_CASES.md:12` describes asking about project work, not creating a project. The record does not say whether New Project is bounded creation or also source-context import. Cost: implementation can miss Desk entry, Room handoff, and cancel/return. Tenets 3 and 7 fail. Correction: replace the authority with `docs/WEB_DESK.md:18`, `docs/PROJECT_ROOMS.md:27`, `web/src/desk/applications.ts:377-393`, and the Room destination; state the boundary.

2. **P1 — pasted-source validation has no egress fact at the decision point.** The Door renders only source label/state/reason (`web/src/features/project-room/door/DoorCore.tsx:400-421`); `doorPreview` returns no host (`web/src/features/project-room/door/api.ts:147-157,187-192`), although it validates external providers (`holdspeak/services/project_door_service.py:218-228,290-323`). Cost: the architect cannot tell which check leaves the machine before Create. Tenets 5 and 6 fail. Correction: return per-source egress and render `EgressChip` on each checked source row; preserve connected-row chips (`web/src/features/project-room/door/DoorCore.tsx:201-204`).

3. **P1 — connection-read failure silently becomes a blank project.** `readConnections` catches every error without setting one (`web/src/features/project-room/door/useDoorController.ts:243-271`); the Door can show no rows and `NO SOURCES · BLANK PROJECT` (`DoorCore.tsx:540-543`). Cost: a broken dependency looks intentional. Tenet 6 fails. Correction: retain a named inventory failure with retry; if blank creation remains allowed, make that choice explicit and receipt-backed.

4. **P1 — count responses are not fenced to the selected source.** `fetchCount` writes state, host, counts and reason without a request identity (`useDoorController.ts:331-355,363-399`); a fast scope change can let an older response describe the newer row. The checking test holds one request (`DoorCore.test.tsx:514-546`) but does not assert out-of-order recovery. Cost: the preview can describe the wrong scope/count/egress while the create choice names the newer source; wrong project creation itself was not demonstrated. Tenet 6 fails. Correction: fence responses by scope/toggle revision and add delayed A→B coverage.

## Convergence

`projects_room` is the first consumer of stable project identity, Room handoff, and source-add outcomes; share `project:<id>`, source identity, and return semantics, not a second creation screen. `source_context` should share immutable provider refs and egress facts, while its picker stays distinct. `feedback` supplies operation-outcome/egress vocabulary; `meeting_aftercare` can consume per-item partial-link results and retry, but its review flow stays separate. Counterargument: a universal picker or wizard adds the interface cost this one-screen Door removes.

## User experience

The 1440 capture (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-project-setup-1440.png`) shows a calm name/source path and honest disabled Create state, promising for Tuesday. The 393 capture (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-project-setup-393.png`) keeps the grammar, but its initial frame ends while the Confluence row continues behind the footer. Scroll ownership, recovery visibility, and return focus are unknown. This is observation, not owner acceptance or a beauty/performance claim.

CONDITIONS: Correct source authority and whole-job boundary; define Room return/close-reopen; add preview egress; name connection-load failure; fence responses and add scenarios. Preserve Button, partial-link retry, provider refusal, and row-egress guards.

MISSED:

1. High: source inventory failure or ambiguous accounts while the user chooses blank versus connected creation.
2. High: close/reopen after partial create, retry, or Room load failure, with the project identity retained.
3. Medium: fast scope replacement/out-of-order counts and a pasted duplicate or unsupported link.

TUESDAY: The one-screen path is likely quick when all reads work, but it is not yet an honest, recoverable creation job when sources or return state fail.

## Acceptance challenges

1. Open New Project from Projects, enter a name, cancel, and assert no create; create blank and assert one Room opens with the returned project identity.
2. Paste a GitHub and an Atlassian source, check them, and assert each row names its provider state and egress before Create; remove one found item and assert only the selected item links.
3. Make the connection inventory fail, then retry; assert a named failure and an explicit blank-project decision, never an unexplained empty source list.
4. Pick source A, immediately pick source B, delay A's count, and assert B's label, counts, egress and create payload remain B's.

UNKNOWN: No tests were executed. No live Desk, backend/provider, native, accessibility, performance, or owner-state actions were made; captures and assertions do not prove owner delight or production acceptance.
