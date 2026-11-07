# HoldSpeak provisional seam design notes

**RETAINED EARLIER SEAM NOTES — not the governing target. The latest direction is surgical evolution serving the two journeys in [Product vision](PRODUCT-VISION-AND-JOURNEYS.md). These four seams are not separately approved and may inform, not constrain, the next-generation proposal. No implementation assignment is granted.**
## Confirmed review criteria

The user's governing direction is a streamlined, coherent, high-quality web stack with clear interfaces and implementations, less dead code, and bounded onboarding for the next agent. Evaluate a proposed structure by how easily a feature can grow or change without edits spreading across unrelated modules, not by how tidy the tree looks.

- **No hard 300/500-line caps.** A large cohesive file can be right. A God object is diagnosed through mixed responsibilities, coupling and independent reasons to change—not its line count alone.
- **Do not fragment the system into tiny files.** A split should give a responsibility a clear owner, reduce change amplification or make a contract easier to understand. Moving code without improving those properties is not progress.
- **Interfaces and implementations should be legible together.** An agent should discover a domain's public contract, implementation entry point and proving tests through a bounded map, without tracing private dependencies across the repository.
- **Use the existing web stack coherently.** Package boundaries and shared UI should support feature work rather than require every change to learn the whole system or create another framework.
- **Dead code requires proof.** Check static and dynamic entrypoints, registries, plugin loading, compatibility/re-export paths and tests. An absent text reference or grep result does not prove code is unused. No removal is authorized at this checkpoint.

These are evaluation criteria confirmed by the user. They do not imply acceptance of any particular module split, target layout, deletion or one of the four earlier seams.

## Structural diagnosis precedes a target architecture

The user has clarified that the foundation must examine repository modules, package declarations, filesystem layout, responsibility placement and bloat/refactor opportunities. The [first structural review and layout options](STRUCTURAL-REVIEW.md) are available; user direction is pending, and the broader dependency/reachability audit is incomplete. The four seams below are incomplete prior draft notes, not a comprehensive target architecture or chosen layout. Do not expand them or treat them as constraints on the structural diagnosis. Revise or retire them in response to findings and user direction.

## Outcome and boundary

The owner should be able to open the same Program twice and see coherent state, stop or leave a conversation without ambiguous lifecycle effects, trust that a project-update draft sees only its permitted sources, and understand whether a checkpoint actually recorded a restart point. If the user retains these candidate outcomes, deliver the accepted subset through narrow changes to existing mechanisms; revise or retire the others. This is a **proposed target**, not a claim that the current repository already implements it or that a production bug was reproduced.

The design follows the repository's product direction: a local hub owns durable work; the Desk exposes complete jobs through shared patterns. A green backend test that leaves a misleading ledger or loses an acknowledged edit is not completion. Reuse the existing frameworks. [Invariants](INVARIANTS.md) are part of the design, not optional commentary.

## 1 Program detail reads share existing ownership

### Present seam

`web/src/desk/programs/api.ts` exposes `useProgram(id)` with `{loading, error, program, reload, apply}` using local state and an `alive` ref. `ProgramBody` and `ProgramShot` consume it. In contrast, `usePrimitiveDetail` already uses `deskQueryClient` and `deskResourceKey`. The Desk windows are keyed, so an A-to-B navigation overwrite is not established. The concrete opportunity is reducing bespoke request ownership and making duplicate-reader and accepted-write ordering explicit.

### Target

Keep the typed `readProgram` API and existing hook-facing contract. Give one Program ID one existing Desk cache key. A Program-local use of TanStack Query is the preferred default if `usePrimitiveDetail` cannot preserve `apply`, error handling and loading presentation without a broad helper change. No second QueryClient, Zustand server-state copy or new resource framework.

| Responsibility | Target owner |
| --- | --- |
| Durable Program state and action outcomes | Existing hub/service |
| Resource identity, shared reads and invalidation | Existing `deskQueryClient` and `deskResourceKey` |
| Typed HTTP request and Program shape | Existing `programs/api.ts` and `types.ts` |
| View selection, text edits, busy operation and local receipt | Existing Program UI |
| Program-change notification | Existing RuntimeBus and `useProgramFrames` filtering |

Use `deskResourceKey("program", id)` **only after T10 confirms that this kind does not collide with an incompatible cache shape**. It is a proposed key use, not a newly established repository contract. Do not change global query defaults. Detail-only adoption excludes `usePrograms`, Dock lamps, Calls hooks and other application lists.

### Ordering rules

- Two mounted detail consumers of the same ID share data and the in-flight fetch. Distinct IDs never share a result.
- A matching Program event refreshes that Program; an unscoped Program event refreshes currently observed Program detail resources according to the existing semantics. Other entities cause no reread.
- `apply(acknowledgedProgram)` writes only the matching Program key. Null keeps the existing no-op behavior. Mismatched IDs must never poison the current resource.
- Characterize and deliberately handle the sequence “read starts → mutation acknowledgment is applied → old read returns.” Using TanStack alone is not proof. Use existing query cancellation/result-discard semantics or the smallest Program-local ordering guard, with a deferred-read regression test.
- Preserve initial-load versus refresh behavior the UI relies on. A failed refresh retains last good data and exposes a named failure. Optional absence stays null only where `readProgram` already defines it; do not turn arbitrary errors into empty success.
- Logical suppression of an obsolete fetch result is not a claim that the network transport was aborted. The current `usePrimitiveDetail` fetch function has no AbortSignal.

## 2 Thread owns an explicit interactive turn handle

### Present seam

`ask_desk.cancel_loop` and `_holds` inspect ThreadService's private global registries. `run_loop` polls `_active_turns` and then polls persistence. Ask's `_tap_loop_text` replaces a private broadcast callback. Calls `DeskTurns` delegates through Ask and obtains private tool handles. These callers know more about Thread internals than their jobs require.

### Target owner and compatibility

ThreadService remains the authority for turn admission, streaming execution, tool holds, persistent message completion and cleanup. Add a small public in-process handle for **interactive** callers. Keep existing route wire shapes and `start_turn` compatibility unless the contract task proves a necessary bounded additive change. Internal registries may remain; Ask and Calls must no longer traverse them or overwrite `_broadcast`.

The proposed handle is a capability scoped to one admitted turn and its current principal/context. It is not a new independently authorized principal, a cross-turn tool handle map, a durable job engine or a new HTTP protocol. Exact names and placement are settled by T20; the semantic surface is:

| Semantic operation | Required behavior |
| --- | --- |
| Identity | Stable thread/user-message/assistant-message/invocation IDs already required by callers |
| Observe progress | Text and held-tool changes for this turn; never replace global delivery; disposal is idempotent and observer exceptions do not fail execution |
| Inspect current holds | A public safe snapshot sufficient for the existing Ask/Calls readback; no private executor object escapes |
| Decide a hold | Routes through the existing admitted decision/approval path; bound to the turn/call and current hold; preserves approve/deny/answer validation |
| Request cancellation | Idempotent intent to stop; returns acknowledgment of the request, never a claim that execution or external effects were rolled back |
| Await completion | Settles after the terminal message and required final metadata are persisted; returns the authoritative final result or a named failure |
| Detach observation | Releases that observer only; does not cancel the turn or remove another observer |

### Completion and lifetime contract

The source currently flushes remaining text, persists abort/completion and metadata, emits final state and cleans up active registries. Integrate the handle at those boundaries rather than infer completion from registry absence. A subscriber installed during start must not lose early text/hold events. A waiter attached after terminal persistence must receive the completed result without polling. Multiple waiters must agree. An observer exception must not gate persistence.

Treat persistence failure explicitly: never resolve a successful completion before the durable terminal write, never wait forever because cleanup ran on an exceptional path, and never convert an unknown outcome into an empty successful answer. The exact supported error result is selected in T20 from existing caller/result contracts. Avoid new durable storage; the in-memory handle may keep its settled value for holders while the registry is released. Existing durable messages remain the authority after process restart; this plan does not invent automatic turn resumption.

The result consumed by Ask preserves its existing fields: `user_message_id`, `assistant_message_id`, `turn_invocation_id`, final non-draft text, structured error, aborted status, egress scope and model. The final answer remains the last answer pass, not concatenated planning text from tool passes.

### Ask and Calls semantics

Ask keeps its current Stop semantics through explicit cancellation. Its text frames subscribe through the public boundary, preserving per-pass reset and final text flush; no service-wide broadcast replacement. Scoped callbacks are detached in `finally` without making ordinary cleanup a cancellation request.

Calls retains its reducer and spoken-approval flows. Spoken readback must still cover the payload and destination actually held. Hanging up or ending speech detaches presentation; slow work may finish and be delivered through the existing answer-later path. T22 must inspect `_after_hangup`, `_turn`, and the late-task owner before changing disposal. A detached UI does not remove a still-needed late-answer observer. Cancel request, hangup, interrupted speech and terminal persisted result remain distinct events.

Do not merge automatic `engine_tool_loop` execution into this handle. Automation runs within its own frozen/admitted parent lifecycle; Thread owns interactive conversation persistence/admission.

## 3 The existing project update policy has a common home

### Present seam

HTTP and CLI already share the algorithms `project_update_scope`, `project_update_palette`, `prepare_project_update_call` and private response filters in `engine_tool_loop.py`. The MCP dispatcher imports those helpers while the engine loop also dispatches through MCP. The problem is ownership and backward dependency, not two separate policy engines or a demonstrated security flaw.

### Target module boundary

Proposed new file: `holdspeak/services/project_update_policy.py`. Move the source-policy constants and shared preparation/filtering logic there with minimal semantic change. Public filter names may drop their leading underscore; exact export names and all import consumers must be updated together. Keep transport envelope construction in its existing adapter when it is not actually shared policy. Avoid a new class hierarchy, dependency container, policy DSL, caching layer or middleware framework.

```text
trusted HTTP run binding ── engine_tool_loop ──┐
                                            ├── project_update_policy ── existing source services
CLI durable credential ─── MCP dispatcher ───┘
```

Do not make the common module import `engine_tool_loop` or `mcp.server`. Both adapters import it. Preserve the existing service construction during relocation; dependency injection or composition-root cleanup is separate work, not an invisible companion refactor.

### Policy truth to preserve

| Input/context | Required behavior after relocation |
| --- | --- |
| Project-bound CLI automation credential | Resolve project from the durable authenticated credential; preserve its narrowed palette |
| HTTP automation run | Use trusted runtime binding as today; do not require a CLI credential or trust model-supplied project identity |
| Explicit conflicting project argument | Same refusal before reading or writing an out-of-scope resource |
| Missing project argument on bound read | Same project injection and project scope for memory reads |
| Private 1:1 meeting or derived excluded source | Same exclusion of body, snippets, nested provenance and draft source refs |
| Explicit owner-filed allowed descendant | Same narrow exception, not blanket permission for its private ancestor |
| Missing/unavailable source authority | Same fail-closed result; do not silently widen the source set |
| Ordinary Ask/unbound caller | Same existing palette and behavior; no project-update policy injected by accident |
| Prepared final update/send | Preparation is not final send; owner press and frozen provenance remain unchanged |

Characterization covers both entry paths rather than testing helper equality alone. A filtered envelope must preserve allowed refs, response structure and error mapping. If before/after differences expose an actual defect, record a separate issue and decision; do not silently alter policy in a relocation task.

## 4 Checkpoint recoverability is visible without changing execution

### Present seam

`ProgramRunner.pin_checkpoint` records a hidden Git ref using a temporary copied index. It returns a `note` on optional failure instead of raising. Handoff proceeds in the same worktree and retains the pin result in the checkpoint undo data. The API projects `ref`, `ref_commit` and `pin_note`, but ordinary `PinCell` renders nothing without a ref, and matched handoff rows bypass `PinCell` entirely.

### Target projection

Keep the existing backend wire contract and persistence. Add a pure Program-local projection in existing `model.ts` (name **proposed**, for example `checkpointRecovery`). It consumes the checkpoint plus only the Program/step facts necessary for honest applicability. It produces display intent, not executable authority or live Git health.

| Evidence in the record | Presentation | Start from here |
| --- | --- | --- |
| Stored `ref` | Existing commit/ref presentation, meaning “snapshot recorded,” not “guaranteed restorable forever” | Existing explicit action |
| No ref and known pin failure note | Plain explanation that work/checkpoint entry was retained but no restart snapshot was recorded | Absent |
| Known no-worktree-yet outcome | Neutral “No worktree snapshot”/current safe wording; do not imply the work failed | Absent |
| Explicitly non-step/non-applicable row | No alarming failure chrome | Absent |
| Historical row with neither ref nor note, applicability uncertain | Neutral unavailable/unknown presentation or omission with no positive recoverability claim | Absent |

T40 settles exact mapping from actual stored facts. Do not parse arbitrary diagnostic prose into a universal state machine. `No worktree to pin yet` is a known producer phrase, not proof that an old worktree never existed. The absence of a ref alone does not prove a pin attempt failed or that pinning was inapplicable. If current data cannot prove a distinction, preserve unknown rather than invent a migration or use the current mutable step to rewrite historical meaning.

Known source notes are bounded plain strings. Use an explicit safe mapping/fallback rather than dump arbitrary future exception text into the ordinary UI. No secrets, absolute filesystem details or raw Git diagnostics belong in normal row text. Preserve access to legitimate existing detail using the shared UI disclosure pattern where needed.

### Both ledger branches

Ordinary rows and matched handoff rows use the same projection. `HandoffLine` must receive the **matched checkpoint's** pin facts, not a later step checkpoint or a guessed handoff entry. Preserve existing chronological matching, handoff brief and redaction presentation. A failed pin does not hide successful continuation and does not prevent View brief. Existing successful handoff `continues_from` remains unchanged.

No retry button is introduced. Retrying pinning after the tree changes would create a different snapshot, not recover the missing historical snapshot. Preserve the original note. No live Git probe is added to every Program read. When an existing stored ref has disappeared, Start from here must produce the existing named refusal/error and leave the Program unchanged; its action result is validated, not predicted by the projection.

## Rollout and compatibility

If accepted and expanded, each epic should be independently reviewable and reversible; keep commits/PRs concern-sized when shipping is authorized. E01 and E04 share Program tests, so serialize edits to those paths. E02 and E03 may share a broader runtime import boundary; integrate carefully, never use parallel workers in one file. No schema migration is planned. Route/MCP shapes should remain stable; if a gate shows otherwise, stop for a scoped amendment.

Roll back only the task-owned delta after checking current tree ownership. Workers do not reset/restore or revert unrelated work. For an already-shipped defect, follow the repository's current fix-forward and security/data-loss exception policy through the authorized owner. Do not undo durable messages, sends, checkpoints or handoffs as a “rollback” of code.

## Completion

If execution is later authorized, completion means the eventual validation task establishes the user-accepted, revised outcomes with focused tests, stored-state assertions, quick check, and applicable UI shots. T90 is currently only a reserved outline ID, not an executable task. It does not mean the parked research questions were turned into code. It does not imply live provider/phone proof, deployment, owner aesthetic acceptance or shipping permission. See [Execution index](EXECUTION_INDEX.md) and [Validation](VALIDATION.md).
