# HS-153-03 - Guardrails (chat.guardrail, seeds, the advisory row)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
- **Depends on:** HS-153-01
- **Unblocks:** HS-153-06
- **Owner:** unassigned

## Problem

A cheaper second model watches the hands (counsel M8): before the
per-call admission, one guardrail pass over the last N messages + the
pending calls yields violations/warnings as an in-flow row. Advisory
only — yolo proceeds; safe/neutral flips the decision box default to
Deny; never auto-denies; a guardrail failure is a warning, never a
block (settled design D3).

## Scope

- **In (LANDED `67723588`, verify):** capabilities `chat.guardrail`
  (`{violations[], warnings[]}`) and `chat.compact` (`{summary}`), sealed
  structured output, backfill family `chat-practice-assignments` from
  `chat.turn`; `holdspeak/services/thread_practice.py` runner entrances;
  census rows; `tests/unit/test_hs153_practice_capabilities.py`.
- **In (this story):** guardrail notes — a Note tagged `guardrail`
  {instruction, trigger tools, N}; seeds `effect-guard` (any effect
  touching a person's ledger without a named source) and `egress-guard`
  (cloud egress of a `people.*` read); per-mode enablement (`tools_json`
  sibling key `guardrails`). Loop timing: tool_calls extracted →
  guardrail admission ONCE via `thread_practice` → `thread_guardrail`
  frame + a `guardrail` part on the assistant message → THEN per-call
  admission with `default_decision` carried on `thread_tool_pending`
  (`deny` when a violation names the call and control_mode ≠ yolo).
  Pullout: the guardrail row (violations red, warnings amber, in-flow,
  RAW fold); the decision box honours the default.
- **Out:** auto-deny (recorded), guardrails outside threads.

## Acceptance criteria

- [ ] Real coordinator, fake engines for both capabilities: a pending `people.commitment.transition` without a source → `effect-guard` violation → `thread_guardrail` frame + part; in yolo the call still runs; in safe the pending frame carries `default_decision: deny`.
- [ ] The guardrail engine failing (exception / timeout 10 s) → one `guardrail_failed` warning row; the turn continues; no call denied.
- [ ] The guardrail runs ONCE per pass regardless of call count; disabled per mode → no admission at all (no receipt).
- [ ] Glass 1440 + 393: the row renders, the decision box shows Deny focused by default under a violation.

## Test plan

- **Unit:** `tests/unit/test_hs153_practice_capabilities.py` (extend) + `tests/unit/test_thread_guardrail.py` (real coordinator + fake engine + capture, the story-03/152 pattern).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `guardrail`.
- **Manual / device:** story 06 (`effect-guard` fires on `.43`).

## Notes / open questions

- The guardrail model's payload = the last N message contents + the pending calls' names/args heads — it crosses the fence too: `_m1_redactor` applies to its admission as well (its own `payload_redactor`).

## What shipped

### Files changed

**Python (backend)**
- `holdspeak/services/thread_modes.py` — `Mode` dataclass gains `guardrails: tuple[str, ...]`; per-mode guardrail enablement (Chase: both seeds, Desk: egress-guard, Draft/Plan: none); `guardrails_for_thread()` resolves enabled guardrails from mode + DB; `seed_guardrails()` creates the two seed notes; `toggle_guardrail_on_mode()` toggles guardrails on a mode recipe; `_parse_guardrail_note()` extracts config from YAML front matter; `_extract_guardrails_from_db()` reads guardrails from the `tools_json` object format.
- `holdspeak/services/thread_service.py` — `_guardrail_matches()` helper for prefix/wildcard pattern matching; `_GUARDRAIL_TIMEOUT_S = 10.0`; `_run_guardrail_admission()` method composes the guardrail payload with M1 redaction on cloud routes and runs with asyncio timeout; guardrail admission loop in `_run_streaming_turn` after tool_calls extracted and BEFORE per-call admission (runs ONCE per pass); `guardrail` and `guardrail_failed` parts persisted on the assistant message; `default_decision` computed per tool call (deny when violation + non-yolo, allow otherwise) and carried on `emit_thread_tool_pending`.
- `holdspeak/kernel/inference_stream.py` — `emit_thread_guardrail()` broadcast helper; `emit_thread_tool_pending()` gains `default_decision` optional parameter.
- `holdspeak/realtime_frames.py` — `thread_guardrail` frame type registered.
- `holdspeak/db/schema.py` — `thread_message_parts.kind` CHECK constraint extended: `'guardrail'`, `'guardrail_failed'`.
- `holdspeak/db/base.py` — `_json_loads_list()` tolerates object format `{"tools": [...], "guardrails": [...]}` (returns the "tools" list).
- `holdspeak/db/seed.py` — calls `seed_guardrails(db)` alongside `seed_modes(db)`.
- `holdspeak/seeds/fresh-desk.yaml` — two guardrail note seeds: `hs-seed-guardrail-effect-guard` and `hs-seed-guardrail-egress-guard`.
- `holdspeak/web/routes/threads.py` — PATCH `/api/threads/:id` handles `toggle_guardrail` field to toggle guardrails on the thread's mode recipe.

**TypeScript (web)**
- `web/src/runtime/frames.ts` — `thread_guardrail` added to `RUNTIME_FRAME_TYPES` mirror.
- `web/src/desk/threads.ts` — `GuardrailRow` interface; `ThreadGuardrailPayload` interface; `ToolRow.defaultDecision` field; `ThreadToolPendingPayload.default_decision` field; `guardrailRows` store state; `applyGuardrail()` store action; `applyToolPending()` passes `default_decision` through.
- `web/src/desk/pullouts/ThreadPullout.tsx` — `GuardrailRowView` component (violations red, warnings amber, RAW fold); decision box respects `defaultDecision` (Deny gets primary+focus when "deny"); `thread_guardrail` bus subscription; guardrail row rendered before tool rows on assistant messages.
- `web/src/desk/pullouts/thread-pullout.css` — guardrail row styles (`.thread-guardrail-row`, violation/warning colors, RAW fold).
- `web/src/desk/components/ThreadComposer.tsx` — `/guardrail <name>` wired: toggles guardrail on the thread's mode; shows "bind a mode first" when no mode is bound; `onToggleGuardrail` callback prop.
- `web/src/desk/__tests__/ThreadToolRows.test.tsx` — `guardrailRows` added to afterEach state reset (prevents infinite re-render from the new selector).

**Tests**
- `tests/unit/test_thread_guardrail.py` — 24 tests: `TestGuardrailMatches` (5), `TestGuardrailSeeds` (3), `TestModeGuardrails` (4), `TestGuardrailsForThread` (3), `TestToggleGuardrail` (3), `TestRealCoordinatorGuardrail` (3: yolo+violation, safe+deny, disabled/draft), `TestGuardrailRunsOncePerPass` (1), `TestGuardrailTimeoutContinues` (1), `TestGuardrailExceptionContinues` (1).

### Seams and design decisions

- **Guardrail notes** use YAML front matter in `body_markdown` (`---\ninstruction: ...\ntrigger_tools: [...]\nn_messages: N\n---`). Editable in the Note editor. Parsed with `yaml.safe_load`, JSON fallback.
- **Per-mode enablement** hardcoded in `MODE_SEEDS` for deterministic seeds. Custom modes store guardrails in `tools_json` as `{"tools": [...], "guardrails": [...]}` — `_json_loads_list` tolerates both array and object formats.
- **Loop timing**: after `tool_calls_this_pass` extracted, before the per-call loop. Runs ONCE per pass regardless of call count. Payload = last N messages + pending calls + combined guardrail instructions. M1 redactor applied inline (sensitive texts replaced on cloud route).
- **Advisory only**: violations map to `default_decision: deny` on affected pending calls when `control_mode != yolo`. Yolo proceeds unchanged. Never auto-denies. The decision box styling flips (Deny gets `is-primary` + `autoFocus`).
- **Failure tolerance**: any exception or timeout from `_run_guardrail_admission` produces a `guardrail_failed` part + frame. Turn continues. No call denied by a failure.

### Defects found

- **CHECK constraint on `thread_message_parts.kind`** did not include `guardrail` or `guardrail_failed`. Fixed by extending the CHECK clause in schema.py. This is an additive schema change -- but `CREATE TABLE IF NOT EXISTS` leaves an existing table's CHECK intact.
- **REAL-PATH BLOCKER: existing DB CHECK constraint (defect #3)** -- the CHECK widening in schema.py only applies to fresh DBs; the owner's real DB has the old 5-kind CHECK and will reject `guardrail`/`guardrail_failed` part inserts. Same class as the 152-06 real-DB reconcile blocker. Fixed with `_rebuild_thread_message_parts_for_kind_drift()` in `holdspeak/db/reconcile.py`, modelled on `_rebuild_kernel_parent_runs_for_kind_drift`: detects the live kind set vs canonical DDL, copies rows into the canonical shape under a SAVEPOINT, preserves indexes/FK triggers, logs once. Wired at the same site as the other rebuilds (~L627). Proven with 3 tests in `test_thread_guardrail.py::TestReconcileThreadMessagePartsKindDrift`: old DB rejects guardrail (precondition), reconcile widens + original rows survive, rebuild is idempotent no-op.
- **Zustand infinite re-render** from `s.guardrailRows[threadId] ?? {}` creating a new empty object on every render cycle. Fixed with a stable `EMPTY_GUARDRAIL_ROWS` module-level const (same pattern as `EMPTY_TOOL_ROWS`).
