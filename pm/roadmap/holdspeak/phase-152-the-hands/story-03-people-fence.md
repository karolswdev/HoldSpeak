# HS-152-03 - The People fence (sensitive results, multi-pass redaction)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** done
- **Depends on:** HS-152-02
- **Unblocks:** HS-152-06
- **Owner:** unassigned

## Problem

DC-01 redacts sensitive parts at the coordinator, but a tool loop
creates new sensitive material mid-turn: `people.*` results (counsel M1,
M2). The fence must hold on every pass and on every later cloud turn.

## Scope

### In

- `people.*` result parts inserted with `sensitive=1` (M2).
- `_sensitive_texts` accumulated across passes and re-injected before every `payload_redactor` call (M1).
- People effects only via the truth table; the family's own refusals untouched.

### Out

The DC-03 egress-guard (paraphrase laundering — recorded R2).

## Acceptance criteria

- [x] Through the REAL coordinator: a `people.*` tool result on a local turn, then `profile_override` → cloud; the captured payload contains `[people content withheld]` and no sentinel; the part row has `sensitive=1`.
- [x] Within one multi-pass turn on a cloud profile, pass 2's payload already withholds pass 1's people result.
- [x] A non-people tool result passes verbatim on cloud.

## Test plan

- **Unit / integration:** tests/unit/test_thread_people_fence.py (real coordinator + fake engine + capture); the metal script leg 2 extended.
- **Manual / device:** `.43` leg 2 in story 06.

## What shipped (2026-08-30)

The fence itself (M1/M2) was already in the loop from story 01; this
story is the **real-path proof** — and the real path, driven honestly,
was not carrying tools at all. Four latent defects, each one the
fake-adoption loop tests could not see (the HS-151-04 law, again):

1. **The hub built a handless ThreadService.** `_thread_factory.py` never
   passed `tool_dispatch_fn`/`control_mode_fn`; the pass loop was inert
   on the hub. Now: `holdspeak.mcp.tools.dispatch` in-process + the
   desk's `Config.control_mode` (the posture the truth table reads).
2. **Pass 1 never saw the palette.** `execute_stream` replays the payload
   frozen at admission; `tools` was injected only inside the pass loop,
   after `start_turn` had admitted. Now the palette rides inside the
   admitted payload.
3. **The runner dropped `tool_calls` deltas.** `_attempt_stream`
   forwarded text/reasoning/usage/done/error only. Now `tool_calls` is a
   first-class delta (it IS the answer of a tool pass).
4. **The full census overflowed admission.** 141 schemas = 79 KB, and
   the admission law reserves one token per byte → `context_overflow`
   on a 32k profile before a word was sent. Now `CHAT_PALETTE` (26
   desk-facing hands, 12.6 KB) is what a turn OFFERS; `TOOL_NAMES`
   stays the gate's classification table. DC-03 modes widen/narrow it.

And one DC-01 gap the synthetic metal leg had papered over:

5. **`profile_override` was decorative.** Stored on the thread, never
   consulted at admission; a thread always routed via the `chat.turn`
   assignment. Now the pick is honored lawfully — written as an
   invocation-scoped next-run override (`apply_next_run_override`, the
   Phase 143 mechanism) before `start_turn`'s admit and before every
   pass re-admission. A v2 profile pins its newest revision; a legacy
   `profiles` row (the hosted path) pins `legacy-<id>@1`.

Proof: `tests/unit/test_thread_people_fence.py` (real coordinator +
real `ThreadToolExecutor` + real `mcp.tools.dispatch`; `people.readiness`
is a genuine People-family call) and
`assets/story-03-hub-leg.py` (the real hub over HTTP — POST thread,
POST turn, PATCH override, GET detail; 15/15; payloads under
`assets/story-03-hub-payloads/`). The cloud fixture is a legacy
`profiles` row with a public base URL — exactly how a hosted model
routes (`external_service` → leg boundary `cloud`); a schema-v2
revision is `same_device` by construction, so a SQL-patched boundary
fails the content-id integrity check (a good fence, kept).

Ledgered, not fixed here: historical tool-role messages are replayed on
later turns as `{"role":"tool"}` without `tool_call_id` (a strict cloud
provider may 400 — story 05/06 metal leg to confirm and shape);
`test_phase143_inference_assignments.py::{selected_group_starter,
group_retry_policy}` fail on a pristine HEAD export too (branch-inherited,
not in main's 64-name baseline; the story-06 name-diff will show them).
