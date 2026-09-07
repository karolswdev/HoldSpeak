# HS-200-41: Return to unfinished work

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-02, HS-200-04, HS-200-09
- **Unblocks:** HS-200-15, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-UX-001–002, AA-UX-005; AC-26; C1, C11

## Problem

An ask the owner starts in a Project Room survives nothing. Its text lives in browser state only: `runAsk` says so itself (`web/src/desk/ask.ts:127`), the kernel journals a payload hash and not the prompt (`holdspeak/kernel/inference_runner.py:63-66`), and `ask_results.payload_json` (`holdspeak/db/schema.py:2069-2076`) holds the answer without the question. A restart, a crash, or a trip to Settings to fix a route loses the work. The dictated audio for that same field already survives (`web/src/lib/pendingVoice.ts:39-110`); only the typed words do not.

Story 04 proved the state half of return-to-task — readiness re-reads without a reload. Nothing returns focus to the verb the owner left, and the resumable work has no face because it has no record.

## Scope

Make an unfinished Room ask durable and resumable, give it the ratified `TaskResume` face, and complete return-to-task with its focus half. Persist the Thread composer draft rather than warning about it. Pay the composer's raw-button canon residues and the library contract debt on species already in use.

Implementation seams: ask service; Room ask well; the existing unfinished/resume machinery; return-to-task event; Desk surface library.

Out: the whole posture 6 wing and its six work states (story 15); the recipe pick (story 11); replacing the composer textarea with a library species (a library story, ledgered).

## Acceptance criteria

- [ ] An unfinished ask keeps its purpose, its Project, its state, why it is stopped, and when it was saved, and survives a process restart and a browser reload.
- [ ] `TaskResume` is added to `web/src/desk/surface/` and documented in `contract.md` before any face hand-rolls it, and draws only fields the store actually holds.
- [ ] Returning from setup restores focus to the verb the owner left, on every dispatcher of the return-to-task event, and the Room ask well subscribes to it.
- [ ] A Thread composer draft survives a reload and a crash restore, carries no stale sending state, and is not written to durable disk storage.
- [ ] Every verb in the Thread composer is the library `Button`, and `EditInPlace` and `ConfirmVerb` are documented in the library contract.

## Test plan

Planned suite `phase200_task_resume`. State tests under `tests/unit`, the durability and restart flow under `tests/integration`, the resume and focus-return path under `tests/e2e`. Cite and extend `web/src/desk/__tests__/ThreadComposer.test.tsx:389` and `web/src/pages/cores/dictation/__tests__/returnToTask.test.tsx` rather than mirroring them. Shoot the `TaskResume` specimen at 1440 and 393.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

Split out of HS-200-10 on 2026-09-07 by the orchestrator, after that story's three trace lanes showed it carried two unrelated jobs. The daily-workflow design's Sizes table had assigned these obligations to story 10 for want of a better home ("the phase's only other draft AC is 28 AC1, at G3, which is too late to carry it"). The split follows the convention that design states for posture 6: IDs stay stable and new IDs go at the end. See [Addendum 3](assets/settled-design-daily-workflow.md) for the corrections that produced it.

Ruling R2 is reversed here. The design said the face would state the limitation with a token `DRAFT NOT SAVED` "unless persistence proves trivial"; it proved trivial, so the condition the design itself ratified has fired and the draft is persisted instead. `DRAFT NOT SAVED` is not drawn on any face. The store is `sessionStorage`, not `localStorage`: a draft can hold dictated meeting material, and session scope survives the reload and the crash restore that ruling R2 was about while dying with the tab, so an orphaned draft cannot outlive the work.

### The build rulings (2026-09-07)

**B1 — a new record, not the Thought machinery.** The Thought tables cannot
carry a Room ask: `refinement_thoughts.working_note_id` is
`TEXT NOT NULL UNIQUE REFERENCES notes(id)` (`holdspeak/db/schema.py:895`) and
birth files that Note into the Inbox
(`refinement_thought_service.py:141`, `:153-155`), so every unfinished question
would deposit a note on the owner's real desk; and its `state` check is
three-valued (`schema.py:902`) where this needs six. A Thought is raw words
refined into a Note; a Room ask is a question against a Project's material. New
table `project_ask_tasks`, additive at the tail of `SCHEMA_SQL`, every INSERT
naming its columns, the canonical snapshot regenerated by the normalizer in
`tests/unit/test_db.py`. What is reused is the pattern, not the table:
`list_unfinished`'s keyset shape, reconcile-from-receipts-never-re-dispatch, and
the host lease identity.

**B2 — the owner is `ProjectService`.** It already owns Room state
(`holdspeak/web/routes/projects.py:46`, `:55`, `projects.room_read_at`).
`AskService` keeps its one property — it persists nothing, which is what keeps it
replayable — and gains no durable rows.

**B3 — the invocation identity is the seam.** The answer already survives a
restart: `ask_results.invocation_id` is UNIQUE and its own comment says the
response may be replayed after a lost response (`schema.py:2066-2076`), with
`kernel/ask_projection.py:11-47` registered for startup recovery. What is missing
is the key back — `/api/ask` never accepts an `invocation_id`
(`holdspeak/web/routes/primitives/ask.py:47-48`) though `AskService.ask` takes one
(`ask_service.py:177`). So: mint the id and write the row **before** dispatch;
`resume` reads `ask_results` **first** and, finding an answer, settles the task
without dispatching anything; only an absent result dispatches, and
`operation_id UNIQUE` refuses the double. Orphaned leases settle to `failed` with
a named reason on startup — reconcile only, never re-dispatch.

**B4 — one story, not two.** The build plan recommended splitting the backend
durability from the face. Refused: a durable record with no way to see it is not a
story the owner could call done, and the charter question for this project is
whether he would use it on a Tuesday. It ships as one L story whose evidence file
carries both a pytest tail and a vitest tail. The lanes below are the parallelism;
they are not stories.

**B5 — `stopped_reason` is quoted, never composed.** `ask_service.py:331` already
raises `target_unavailable` carrying the target's own readiness reason. Store that
verbatim. A synthesised sentence on a failure row is prose in the UI.

**B6 — `Discard` sets a state.** Never delete; the projection excludes
`discarded`.

**B7 — the custody token is `SAVED HERE`, not `THIS DEVICE`.** `THIS DEVICE` is
the egress vocabulary (`web/src/desk/surface/egress.ts:16,25`) and egress badges
are a hard boundary; two different facts must not wear one token. Custody reads
`SAVED HERE` on the coordinator that holds the row and `SAVED ON <host>`
otherwise. The ratified footer keeps `THIS DEVICE` for egress, where it is
correct.

**B8 — the six work states are a union across three owners, not six states of one
record.** A Room ask cannot honestly draw `RUNNING · 00:52` with a `Stop`:
`/api/ask` is one blocking POST with no job row, no clock and no progress record,
where a Thought has `refinement_invocations.state`. This story's record produces
only the states an ask can actually reach; the `TaskResume` species accepts the
full vocabulary so that story 15, which draws the whole wing, can pass the others
from their own owners. Recorded for story 15.

**B9 — the canon scanner is not touched here.** Rule A1 is blind to the way
Prettier writes a raw button, so paying the composer's five buys no ratchet
movement. Prove the swap with a vitest assertion instead. The regex and its
re-baseline are ledgered in BACKLOG.md as their own work.

**B10 — the owner's desk has no unfinished work to walk.** Read-only census:
`refinement_thoughts` is `completed|8` with zero `working`, and all 13
`ask_results` rows carry no question. The browser proof runs on an isolated rig;
his attended leg needs him to start an ask and walk away from it.

### Open on the canvas, for his verdict

`DRAFT NOT SAVED` is drawn on `P6Repair` and `P6Phone`. Ruling R2's own escape
clause has fired, so the token is retired and this story draws it nowhere — but
the two ratified artboards still carry it. The boards are his canvas and are not
edited here.
