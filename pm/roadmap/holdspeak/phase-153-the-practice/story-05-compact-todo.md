# HS-153-05 - Compaction and todo (chat.compact cut row, door.add_item)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
- **Depends on:** HS-153-02
- **Unblocks:** HS-153-06
- **Owner:** unassigned

## Problem

Long threads need a cut that keeps the fence (counsel M7), and a todo
said in a thread must land on the Door — never a parallel list
(settled design D5).

## Scope

- **In (LANDED `67723588`, verify):** `action_items.meeting_id`
  nullable + `source_type`/`source_ref`; `DoorService.add_item`; MCP
  `door.add_item` (effect_proposal, `source_type='thread'`); the
  `chat.compact` capability + `thread_practice` entrance.
- **In (this story):** `/compact` → `POST /api/threads/{id}/compact` →
  `chat.compact` admission over the leaf path (through the real
  coordinator, `payload_redactor` applied) → a `system` row with
  `stats_json = {"compaction": true, "cut_at": <message_id>}` and a text
  part = the summary; the assembler includes only that row and what
  follows; the summary part is `sensitive=1` when ANY summarized part
  was, and its text joins `_sensitive_texts`. Pullout: the cut marker row
  ("compacted · N messages", RAW fold shows the summary). `/todo <text>`
  → `door.add_item` through the SAME executor path as a model call
  (receipt row); the Door card provenance case `thread` ("from a thread"
  chip opening the pullout at the message).
- **Out:** automatic compaction on context pressure (R1 adaptive cap).

## Acceptance criteria

- [ ] After `/compact`, the next turn's admitted payload contains the summary + later messages only (captured via the real coordinator); a thread with a sensitive part before the cut yields a sensitive summary that the cloud payload withholds.
- [ ] `/todo buy the cake` → an `action_items` row with `source_type='thread'`, `source_ref=<message_id>`, `meeting_id NULL`; the Door board shows it with the `thread` provenance chip; the receipt row appears in the thread.
- [ ] Glass 1440 + 393: cut marker + the Door card with the thread chip; the chip opens the pullout.

## Test plan

- **Unit:** `tests/unit/test_thread_compaction.py` (assembler cut + sensitivity inheritance + real coordinator capture); `tests/unit/test_hs153_practice_capabilities.py` (extend for the route).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` legs `compact`, `todo`.
- **Manual / device:** story 06.

## Notes / open questions

- The cut is a row, not a deletion: fork/regenerate before the cut still works; the assembler's "after the last compaction cut" rule is the only reader.

## What shipped

### Files

**Backend:**
- `holdspeak/services/thread_service.py` -- `compact_thread()` and `todo_from_thread()` methods; assembler compaction cut logic in `_assemble_payload` (skips messages before the latest compaction row)
- `holdspeak/services/thread_practice.py` -- fixed `run_compact` to work through the real coordinator: proper `deadline_at`, deployment revision resolution from the backfilled assignment chain, `publish` callback to capture the adapter's result
- `holdspeak/kernel/inference_stream.py` -- `emit_thread_compacted` frame emitter
- `holdspeak/realtime_frames.py` -- `thread_compacted` added to `RUNTIME_FRAME_TYPES`
- `holdspeak/web/routes/threads.py` -- `POST /api/threads/{id}/compact` and `POST /api/threads/{id}/todo` routes

**Frontend:**
- `web/src/desk/components/ThreadComposer.tsx` -- wired `/compact` (POST call + system row) and `/todo` (POST call with arg validation)
- `web/src/desk/pullouts/ThreadPullout.tsx` -- `CompactionCutMarker` (cut marker row with RAW summary fold), `CompactFailedRow`, `ThreadMessageList` (fold earlier messages behind a toggle); subscribes to `thread_compacted` frame
- `web/src/desk/pullouts/thread-pullout.css` -- styles for cut marker, fold toggle, compact_failed row
- `web/src/desk/chair/lanes/DoorBoardLane.tsx` -- `provenance` field on `DoorCard` type; "from a thread" chip with `data-testid="door-card-thread-chip"` that opens the thread pullout on click
- `web/src/desk/chair/chair.css` -- styles for `.door-card-provenance-chip`
- `web/src/runtime/frames.ts` -- `thread_compacted` in web mirror

**Tests (new):**
- `tests/unit/test_thread_compaction.py` -- 10 tests (assembler cut, sensitivity inheritance, real coordinator compact, cloud redaction, failure path)
- `tests/unit/test_thread_todo.py` -- 6 tests (yolo todo, receipt row, empty text, source_ref, safe mode, follow-through provenance)
- `web/src/desk/__tests__/threadCompaction.test.tsx` -- 5 tests (cut marker, fold toggle, RAW fold, compact_failed row)
- DoorBoardLane.test.tsx -- 3 new tests (thread provenance chip renders, omits when no thread_id, omits when no provenance)

### Seams

- **Compaction admission** uses `run_compact` through the real `InferenceRunner` (not mock) with the M1 redactor applied to the payload before it reaches the engine. Egress scope is derived from the latest assistant message on the thread.
- **Assembler cut** in `_assemble_payload`: finds the LAST system message with `stats_json.compaction == true` and includes only that row and what follows. The cut is a row, not a deletion.
- **Sensitivity inheritance**: the summary part gets `sensitive=1` when ANY summarized part was sensitive; the summary text joins `_sensitive_texts` in later payloads (tested: a cloud-route capture withholds it).
- **Todo executor path**: `/todo` goes through `ThreadToolExecutor.admit()` + `.execute()` for `door.add_item` -- the SAME gate/truth-table path a model call takes. In safe/neutral mode it holds for the decision box. Receipt row (tool_call + tool result parts) persisted exactly like a turn's tool call.
- **Door card provenance**: `FollowThroughService._provenance_for` already handles `source_type='thread'`; the DoorCard chip renders "from a thread" and opens the pullout at `thread:{thread_id}`.
- **Frame registry**: `thread_compacted` registered in both Python and web mirror; the fence test (`test_realtime_frame_registry.py`) passes.

### Real-path defects found

1. **`run_compact` was untestable through the real coordinator** -- three defects hidden by mock-only tests: `deadline_at=0` (refused by the runner's `not deadline > clock()` check), `deployment_revision=""` (refused by `not revision` check), and `CanonicalPromptAdapter` expected `system_prompt`/`user_prompt` but the payload had `messages`. Fixed with proper deadline, deployment revision resolution from the backfilled assignment chain, and structured payload formatting.
2. **`InvocationOutcome.result` is always `None` through the real runner** -- the runner stores results via `publish()`, not as an attribute. Existing code `getattr(outcome, "result", None)` always returns None. Fixed with a publish callback capture.
3. **`chat.compact` and `chat.guardrail` are NOT in `EXECUTING_CAPABILITIES`** -- they are "internal" visibility capabilities that cannot go through the adoption service's `admit()/execute()` path. Must go through `runner.invoke()` directly.
4. **`run_guardrail` had the same defects** as `run_compact` (`deadline_at=0`, `deployment_revision=""`, wrong adapter shape, missing publish callback). Fixed in this story (same file, same pattern). Two real-coordinator tests in `test_thread_guardrail.py::TestRealCoordinatorGuardrail` that previously mocked `_run_guardrail_admission` now drive through the real runner; two new cloud-redaction tests added in `TestRealRunnerGuardrailCloudRedaction`. See story-03 "What shipped" for the cross-reference.
5. **Controlled `<details>` in CompactionCutMarker** -- React's `open={showRaw}` attribute on `<details>` fought the native `<summary>` click toggle (click opens natively, React re-renders with `open={false}`). Fixed by using the same uncontrolled `<details>` pattern as the existing RAW fold.
6. **`handleSend` did not intercept freeform-arg slash commands** -- `/todo buy the cake` has `hasArg: true` but returns zero completion items (freeform text), so the palette closes and Enter sends the literal text as a regular message instead of dispatching the command. Fixed by adding a regex check in `handleSend` to dispatch recognized slash commands before falling through to `onSend`.
7. **Glass `_seed_profile` lacked chat.compact/chat.guardrail assignments** -- `_resolve_deployment_revision` queries `capability:chat.compact` specifically; the global-only assignment did not satisfy it. Fixed by adding a chat.turn-scoped assignment + running `_backfill_chat_practice_assignments`.

### Glass (story 05)

- `tests/e2e/test_hs153_practice_glass.py` -- 2 new legs (`test_compact_cut_marker_and_fold`, `test_todo_receipt_and_door_card_chip`) at 1440 + 393
- Screenshots in `assets/story-05-shots/`: compact-cut-marker, compact-raw-fold, compact-fold-expanded, todo-receipt, door-card-thread-chip (both widths)
