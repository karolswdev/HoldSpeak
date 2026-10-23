# threads

Job: Continue a saved specialist conversation with turns and tools  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_threads`  
Evidence class: active React/Python source and assertions; no execution or owner walk. Archived Thread shots are parked history, not acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The active entry is not a Thread face. `web/src/desk/pullouts/ThreadToAsk.tsx:1-14` opens the single Ask window and closes the pullout. The supported path is Recent or a thread reference → read turns/About → follow up → receive a persisted answer → return through Recent or a source reference. `AskPanel` implements it (`web/src/desk/components/AskPanel.tsx:293-329,457-503`), and an active assertion covers ask, follow-up, reopen, and return (`web/src/desk/__tests__/ask.app.test.tsx:224-280`).

The declared “specialist” scope is wider: a Thread can have a mode, recipe/profile, branch, regeneration, drafts, and a held tool call (`docs/AGENTS_AND_THREADS.md:25-41`; `web/src/desk/threads.ts:24-40`). Cover those states or explicitly bound this family to Ask-created threads. A bounded job still needs trigger, source/About identity, interruption, stale source, tool hold, failure, and return. Do not resurrect the parked Thread pullout to satisfy old screenshots.

FINDINGS:

1. **P1 — specialist identity is silently lost on continuation.** The thread wire carries `recipe_id`, `profile_override`, and `mode` (`web/src/desk/threads.ts:24-40`), but `ThreadToAsk` passes only an id (`web/src/desk/pullouts/ThreadToAsk.tsx:9-13`). `AskService.ask_in_thread` reads history, then selects the global Ask tool mode and route (`holdspeak/services/ask_service.py:586-620`); it does not resolve the saved mode/profile. Owner cost: a follow-up can run with different instructions, tools, or engine without warning. This fails Tenets 3 and 7. Correction: bound the audit to Ask-created threads, or preserve/display the saved mode/profile/palette and assert that a specialist stays specialist.

2. **P1 — opening Recent A then B can paint A into B.** `loadThread` resets state, awaits `getThread(id)`, and checks only `mounted`, not the selected id or a generation (`web/src/desk/components/AskPanel.tsx:293-309`). The assertion is sequential only (`web/src/desk/__tests__/ask.app.test.tsx:247-265`). Owner cost: wrong questions, answers, and sources appear. This fails Tenets 3 and 7. Add a generation/current-thread fence and delayed A/B assertion; retain one Ask window.

3. **P1 — interruption and held-tool return are unspecified and not one path.** Closing or unmounting aborts the request (`web/src/desk/components/AskPanel.tsx:246-271`); a held call exists only in live `ask_progress` state (`:217-232`) and is rendered only while running (`:884-889`). The saved-thread mapper draws text/refs/`used`, but no held decision state (`web/src/desk/ask.ts:473-518`), although a separate store hydrates tool rows (`web/src/desk/threads.ts:1064-1125`). Owner cost: closing during a hold or slow run can force duplicate work or lose the next decision. This fails Tenets 3 and 7. Define durable invocation/hold recovery, or state that close cancels; test terminal state, draft retention, and no duplicate turn.

## Convergence

Converge with `ask_whole_desk` for the single Ask surface, immutable request snapshots, invocation identity, draft retention, receipts, and `Looked at`/`Used`. `source_context` and `memory` provide qualified refs, selection handoff, and source-gone handling; `keep_answer` consumes answer/message/source provenance. `agents_conductor` remains the agent-session entry point, not another conversation renderer. Keep thread identity, mode/palette, and branch history separate: source authority and tool policy have different owners. Do not merge these into a generic explorer.

## User experience

Source evidence suggests a fast happy path: one in-world Ask window, empty follow-up box, Recent, and per-answer verbs (`AskPanel.tsx:731-760,820-867`). That is likely useful to a senior architect. It will not please when “specialist” changes meaning, a late response contaminates another thread, or a held action vanishes. No current capture or owner acceptance was inspected in this review; archived Thread shots depict the parked surface and cannot certify current craft or 393 layout.

CONDITIONS: State the active boundary; preserve or explicitly exclude specialist mode/profile; fence overlapping loads; specify durable interruption/hold recovery and stale-source behavior. Keep the Ask surface, public controls, and existing receipt/tool machinery.

MISSED:

1. Saved mode/profile/palette changing across a follow-up.  
2. A/B reopen race and wrong source/answer pairing.  
3. Close/reload during a held tool or pending answer.  
4. A source deleted or permission-lost between turns.

TUESDAY: The one-window happy path is quick, but the audit is not sufficient until a specialist can return without hidden mode changes, stale content, or lost held work.

## Acceptance challenges

1. Open a saved thread with a non-default mode/profile, send a follow-up, and verify the same mode/palette and source refs remain authoritative.  
2. Start Recent A, immediately open B, resolve A last, and verify only B’s title, turns, About, and draft remain.  
3. Reach a supported held effect call, close/reopen the Ask window, and verify one persisted hold with one allow/deny outcome and no duplicate turn.  
4. Reopen a thread after one referenced source disappears; verify an honest source-gone result, retained draft, and a usable return to the conversation.

UNKNOWN: No tests, builds, live Desk/API/provider/native actions, performance measurements, or owner acceptance were performed. Current 393 appearance, production tool elicitation, and pending-invocation claim after close remain unproved.
