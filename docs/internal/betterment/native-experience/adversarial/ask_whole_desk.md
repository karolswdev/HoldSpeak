# ask_whole_desk — adversarial review

workflow_id: ask_whole_desk  
job: Ask a question about work on the Desk and get cited evidence  
baseline: main55572802181d6a8045f6d27e3c722aaf5694dbbd (PR1430)  
reviewer task: review_ask_whole_desk  
evidence class: source inspected; active assertions read; no tests, live Desk walk, provider call, or owner observation

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The declared job is an active Ask application (`web/src/desk/applications.ts:134-142`) with About/context choice, prompt, answer, named Looked-at sources, follow-up thread, tool writes and prepared sends. The happy path is real in source: `AskPanel` snapshots input, runs one request, stores a thread turn, and keeps the draft (`web/src/desk/components/AskPanel.tsx:457-533`). The brief is too narrow about return and evidence boundaries. “Whole desk” is either relevance-bounded memory retrieval or a tool-capable engine's allowed palette, not an unbounded read; the audit must name no-hit, stale-source, refusal, write-hold, and egress-free outcomes.

FINDINGS:

1. **P1 — interrupted Ask has no demonstrated return.** Unmount/close aborts the request and posts cancel (`web/src/desk/components/AskPanel.tsx:246-264`), while durable `AskTask` save/claim/resume exists separately but is not called by Ask (`web/src/desk/ask.ts:657-737`). A senior architect who closes or reloads during a slow answer can lose the result or repeat work. This fails Tenets 3 and 7 (accelerate the Tuesday job; serve the first architect). Condition the audit on one correction: integrate the invocation/result claim path into Ask reopen, or bound the job to “answer only while this window remains open” and say recovery is out of scope. Test the terminal state, no duplicate dispatch, draft retention, and source links.

2. **P1 — saved-thread navigation is stale-race unsafe.** `loadThread` starts `getThread(id)` and applies its turns/about whenever it resolves, with no generation or current-id check (`web/src/desk/components/AskPanel.tsx:293-309`). The active assertion covers sequential reopen only (`web/src/desk/__tests__/ask.app.test.tsx:247-265`), not A-then-B with A resolving last. The owner can read B's title with A's answer and citations, failing Tenets 3 and 7. Add a generation tied to the selected thread and discard late reads/errors; retain the one-window grammar.

3. **P2 — “cited evidence” is not defined at the face boundary.** The wire parser receives grounding claims and matched/overflow receipt data (`web/src/desk/ask.ts:163-173,340-361`), but `AskTurn` drops both and the active face renders only Looked-at source-name links (`web/src/desk/ask.ts:395-403`; `web/src/desk/components/AskPanel.tsx:495-501,845-852`). Assertions prove named refs (`tests/unit/test_desk_ask.py:85-95`; `tests/integration/test_desk_ask_tools.py:150-157`), not claim support, no-match, or overflow. Condition the audit to preserve and render this claim/receipt contract, or rename the job to “show sources looked at”; include zero-match/partial-support. Do not invent a new evidence framework.

## Convergence

Converge with `threads` for thread/message identity and the Ask window, `source_context` for About chips, selected-text handoff and `openRef`, `memory` for bounded retrieval and citable refs, and `keep_answer` for answer-to-note/artifact provenance. `meeting_intelligence` shares APP_ID, ASYNC_STALE, OP_OUTCOME, SOURCE and FEEDBACK but remains a queued meeting-result job. `send_prepare` should keep using `NoteSendWells` and its prepare-only boundary. Do not merge these into one generic explorer: memory, meeting work, and conversational Ask have different lifecycles and source ownership.

## User experience

Source and assertion evidence suggests a pleasing happy path: starter prompts focus the editor (`web/src/desk/__tests__/askPanelExperience.test.tsx:43-54`), one window supports follow-up and Recent (`web/src/desk/__tests__/ask.app.test.tsx:224-265`), and the browser assertion keeps the composer visible at 1440/393 (`tests/e2e/test_ask_glass.py:203-245`). This is inference, not acceptance: no capture or owner walk was inspected in this review. The face should make bounded coverage and return state as legible as the answer, without a wizard or prose wall.

CONDITIONS: Clarify bounded whole-desk retrieval; specify and verify interrupted-run return; guard stale thread loads; define source-name versus claim-level citation and test no-hit/partial evidence. Preserve existing Button, thread, grounding, receipt and SendWell species.

MISSED:

1. Reload/close while a request is pending, including whether a completed result can be claimed once (highest cost).
2. Rapid Recent A/B selection with out-of-order reads (wrong answer/source cost).
3. No-match, stale source, context overflow and tool refusal/hold outcomes.
4. Prepared send remains unsent until the owner presses Send.

TUESDAY: Yes for one short, already-visible question; no for a slow or interrupted question whose return and evidence boundary are not yet explicit.

## Acceptance challenges

1. With no About and a tool-capable engine, ask “What needs my attention?”; verify named Looked-at links, bounded records, and no write without an explicit request.
2. Start a slow Ask, close/reopen or reload, then return to the same thread; verify one answer, retained draft, and no duplicate inference—or the stated bounded refusal.
3. Open Recent A then B while A’s read is delayed; resolve A last and verify only B’s turns/About remain.
4. Ask about a note/project, refresh or remove the source before submit; verify an honest source-gone/refusal path, not an answer with stale context.
5. Ask an engine to prepare a send and deny a held write; verify Prepared/no egress and no Wrote mutation.

UNKNOWN: No tests were executed. No browser captures, model latency/refusal observation, live provider/native behavior, performance, accessibility, or owner acceptance was established. The baseline anchors may drift.
