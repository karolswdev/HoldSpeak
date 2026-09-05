# Interview delivery

Status: initial manual increment implemented and integrated with the desktop changes. Updated 2026-09-05. Owner authorization: “I want you to drive the delivery of this” and “run it to full completion.” Delivery branch: `feat/repeatable-interview-delivery`, based on desktop merge `860ad7d2`.

[Integration record](INTEGRATION.md) and [final verification](VALIDATION.md) cover the shipped scope, repaired web checks, and exact limits. Desktop PR #528 and prerequisite repair #560 are merged. This Interview increment is delivered through [PR #561](https://github.com/karolswdev/HoldSpeak/pull/561); the running preview and its conversation remain intact. The broader SRS and daily-use pilot remain future work.

## Reviewable behavior

An **Interview** mode now runs in the existing Desk Thread. Enter Goals, Projects, What matters, Cadences, Decision log, Delegation, or Sources & models independently; return later; inspect context; and choose a suggested manual draft. People opens the existing protected People surface before accepting relationship input.

The configured LLM conducts the conversation and proposes contextual suggestions through actual MCP contracts. It uses existing model assignments, in-process dispatch, domain services, and the kernel. This is the initial manual path in DP-00A; it does not close all eighteen interview requirements or a complete R0–R4 gate.

| Delivery item | State and evidence |
|---|---|
| Existing Thread integration | Implemented: seed mode, composer, model selection, streaming, Keep, and tool policy. Physical microphone capture remains untested here. |
| Repeatable section context | Implemented: persistence, revision conflicts, replay, corrections, stale suggestions, dismissal, removal, deletion, and re-open checks. Context belongs to this Thread; no organization-wide Goals service was created. |
| Actual tool execution | Implemented: offered-tool restriction, live section/schema recheck, authenticated principal preserved, claimed kernel children, terminal receipts, revoked-parent and consumed-claim refusal. |
| Project setup MCP parity | Implemented: select, deselect, test, and repository clarification call existing ProjectSetupService operations. Tested proposals activate; untested proposals are refused while a blank Project remains lawful. Finalization replay returns the existing Project. |
| Manual result | Browser proof: converse → suggestion → Try draft → Keep as artifact → change section → reload. The browser model is a scripted fixture. |
| Live LLM behavior | Real LAN model completed the [two-turn interview](assets/live-interview-two-turns.json) and subsequently the [full manual draft → Keep → revisit path](assets/live-interview-complete.json), with kernel receipts. Content quality findings remain open; these are mechanical proofs, not owner acceptance. |
| Integration authorization and pilot | The owner authorized delivery. Daily usefulness, organizational sources, voice hardware, and the ten-workday pilot remain unproved. |

## State and execution contract

`InterviewService` owns a Thread-scoped state document and command journal. Each command takes `expected_revision`; `BEGIN IMMEDIATE` rechecks the live Thread and serializes changes. Replay compares the event digest and returns current state without applying another mutation. HTTP controls use UUID command IDs. MCP writes derive identity from the Thread's revision slot, so the LLM need not invent replay identifiers.

Facts require an exact quotation from ordinary user input in this Thread. Inferences remain labelled. Corrections invalidate dependent ideas; removal drops dependent suggestions. A deleted, sensitive, or draft source is excluded from subsequent context and suggestion projections. Pruning persists with the next accepted command. This checks active disclosure; it does not erase historical messages, frozen inference evidence, backups, or receipts.

Model context includes bounded fact details, a small complete index, suggestion choices, coverage counts, and the registered-schema digest. Each pass refreshes it. Older successful control exchanges are represented by current state; domain observations, failures, and the latest complete protocol group remain available. Project room observations project identity and linked evidence while the full result remains in the Thread. After saving a suggestion, the model explains it using state and source observations without more tools. Empty responses, raw tool markup, and route failures are visible failures.

The turn uses the existing `tool.turn` parent. Each physical model attempt and executed tool is a child. Limits are ten minutes, thirty children, and the existing ten-pass chat cap. Claims prevent redispatch of consumed operations. Domain effects retain their service's idempotency. This does not claim universal exactly-once execution or provider-side interruption of an already-running native call.

**Try draft** saves the owner's choice before sending the request through the normal composer path. Drafting offers only reads; Explore restores discovery tools. Keep idea, Later, and Dismiss persist. Unsupported effects cannot start from a suggestion button. Explicit Project work uses existing setup and runtime policy; no additional approval policy was introduced.

Setup continuation reuses an active/completed session and replaces an expired one. A crash/conflict between creating a transient setup session and binding its ID can leave an unbound session. Finalization's existing atomic Project/session contract prevents another Project on replay. Full prepared-plan recovery and cross-surface setup rebasing remain later DP-00A work.

## Earlier development verification (superseded by VALIDATION.md)

| Check | Observed result |
|---|---|
| Broad backend regression | 239 passed; one new test incorrectly expected blank Project creation to fail. Corrected test and separate Watch-refusal case passed. |
| Focused backend regression | 138 passed after corrections; a core rerun passed 37 checks after controller identity and context changes. |
| Full Desk suite | 152 files, 1,481 tests passed. |
| UI checks after layout refinement | Three files, 61 tests passed, including seven InterviewPanel cases. |
| Thread visibility regression | Seven files, 139 tests passed: immediate prompt, delayed acknowledgement, failed-send draft retention, HTTP/socket races, saved streaming text, and shared Call submission. Paused-model production browser passed both connected and all-frames-dropped cases without reload; reader scroll stayed in place. |
| Tool activity disclosure | 60 Thread rendering/tool checks passed. Production browser paused after two real MCP calls and before the final answer: routine details stayed collapsed; manual expansion survived completion. Build and bundle gate passed; TypeScript retains the unchanged baseline. |
| Production build | Passed; existing chunk-size advisory remains. |
| Bundle gate | Passed: Desk JS 1,253,203 bytes; CSS 294,483 bytes; no source maps. |
| Production browser | Passed at widths 1440 and 393: real routing/kernel/MCP, fixture model, draft, artifact Keep, section/context persistence, People handoff. |
| TypeScript | Thirty diagnostics; output matched an archived unchanged HEAD byte-for-byte. |
| Architecture guard | Same existing failure as unchanged HEAD: Project room door CSS outside the library fence. |
| Token gate | Same nine existing values as unchanged HEAD in gadgets and Project room CSS. |

Synthetic fixture screenshots: [desktop](assets/interview-walk-1440.png), [compact](assets/interview-walk-393.png), [People](assets/interview-walk-people-393.png). They establish rendered behavior and viewport inspection; the owner's visual verdict remains open.

Live trials exposed copied command IDs, repeated state exceeding the endpoint's conservative 16,384-byte accounting, blank failures, and raw tool markup when schemas were removed while old protocol frames remained. Fixes assign write identity, refresh/compact context, project relevant room evidence, settle failures explicitly, and convert the final explanation into ordinary conversational input. A subsequent trial asked questions without saving requested context or suggestions; instructions were strengthened and the failure retained.

The owner reported invisible prompts/replies during Thread use. Send had cleared the draft immediately, discarded HTTP message IDs, and relied on a live start event that inserted only an assistant stub. Prompts appeared only after a later GET; absent or incomplete streaming buffers could hide persisted response text. The composer now awaits acknowledgement, the store shows a pending user row immediately and reconciles server IDs, stale reads cannot erase a newer submission, and active turns use a read-only 1.5-second recovery check. Saved response text survives missed frames. Scrolling back suspends automatic following. Failed sends retain the draft; the receipt does not independently replay Send. At that earlier checkpoint, the production build and bundle gate passed and TypeScript matched main’s thirty-diagnostic baseline. Final delivery now passes TypeScript, tokens, architecture, and the complete web contract; see VALIDATION.md. This frontend update was served by the existing preview without restarting its temporary database.

Visibility evidence: [paused before acknowledgement](assets/thread-visibility-pending.png), [response with live frames dropped](assets/thread-visibility-offline.png), and [browser assertions](assets/thread-visibility.json). Call mode now uses the same store action, with a failed transcript retained in the existing manual retry callback. The Call wiring is unit-tested; microphone hardware remains untested.

The owner also reported tool details expanding before the final answer. The old Interview-only disclosure required the assistant turn to be finished. Routine pending, running, and completed calls now share a collapsed Actions disclosure in every Thread mode, from their first appearance. Requests for decisions, questions, failures, and denials remain visible outside it. Native disclosure state preserves an explicit choice to inspect while the answer arrives. Evidence: [before the answer](assets/tool-activity-before-answer.png), [after the answer](assets/tool-activity-after-answer.png), and [browser assertions](assets/tool-activity.json).

The final three-turn trial completed mechanical integration, kept `artifact_66ee91032624`, and retained facts and the Try disposition when revisiting Decisions. Manual review found an unnecessary repeat question, an overstatement about missing external sources, and unprovided draft context/ID presented without consistent placeholder labels. The final prompts were tightened after this trial; those semantic improvements still require live evaluation. Green fixtures and successful tool flows are not evidence of reliable recommendation quality. Long conversations and large source payloads can still require existing compaction or a larger configured context allowance.

## Reproduction

These drivers redirect Python home/path resolution into a temporary directory without changing HOME. They leave owner settings and the database intact. The live driver sends only synthetic interview content to the supplied endpoint.

```sh
uv run python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/integration/test_interview_conversation.py tests/unit/test_interview_service.py tests/unit/test_interview_tool_execution.py tests/unit/test_project_mcp_driver.py tests/unit/test_thread_tool_loop.py tests/unit/test_thread_modes.py
uv run python docs/internal/architect-assistant/proof/browser_walk.py
uv run python docs/internal/architect-assistant/proof/thread_visibility.py
uv run --with 'openai>=1.0.0' python docs/internal/architect-assistant/proof/live_model.py --endpoint <existing-compatible-endpoint>/v1 --model <actual-model-id>
```

The browser driver requires a current production build and installed Playwright browser. The LAN adapter requires the optional compatible client package; `uv run --with` supplies it to the proof invocation. A concurrent Homebrew Node library mismatch prevented default Node startup during verification. The already-installed Playwright Node binary ran Vite, Vitest, TypeScript, and guards successfully; global Node was not changed.

## Remaining delivery

1. Evaluate the final grounding instructions and fix the recorded repeat-question, missing-source, and draft-placeholder quality gaps with a stable scenario set; retain failed trials.
2. Obtain the owner's live UI verdict and correct observed interaction/recommendation problems.
3. Extend the manual increment through separately reviewed delivery slices. The integration and stamped commit/PR process for this increment are complete in the accompanying delivery; no additional merge authorization is needed.
4. Complete R0 runtime/restore attestation and the real transformation-stream pilot; extend recovery and section adapters from observed gaps.
5. Deliver Assignment-based supervised work and bounded scheduling through DP-03/DP-04/DP-06. This increment does not enable them.

The other checkout's Phase 170–173 work and unrelated edits were read-only. No owner runtime was replaced. Delivery Workbench reports inherited historical roadmap/evidence issues; this work does not close those phases. The [Constitution](../CONSTITUTION.md) and [repository contract](../../../CLAUDE.md) retain their shipping and live-proof requirements.
