# HS-107-02 - The typing families — ten sites through the kernel

- **Project:** holdspeak
- **Phase:** 107
- **Status:** planned
- **Depends on:** HS-107-01
- **Unblocks:** HS-107-05
- **Owner:** unassigned

## The thesis (the bar)

Ten sites, and the one the owner touches every day is among them.

| id | site |
|---|---|
| T03 | `runtime/dictation_capture.py:429` — dictation → agent pane |
| T04 | `web/routes/cadence.py:256` — Cadence reply → pane |
| D01-D05 | `runtime/dictation_capture.py:188,284,369,485,509` |
| D06-D07 | `runtime/wake_glue.py:291,346` |
| D08 | `plugins/voice_macro_connector.py:118` (dormant) |

The bar is not the count. **It is that dictation does not get slower
or chattier.** Article XI clause 4 exists because the owner's hold
gesture is already approval; a migration that adds a hold, a
confirmation, or measurable latency to that path has failed no matter
how many entries leave the register.

## Problem

Every one of these types into the world without admission or receipt.
`send_text_to_pane` and `TextTyper.type_text` are called directly, so
there is no single answer to "what did HoldSpeak type today, on whose
authority?" — the question the whole kernel exists to answer.

## Recipe

1. **Obey the contract HS-107-01 wrote.** It named the commit point,
   authority basis, and receipt content for each dictation path. This
   story implements it; it does not re-litigate it. If implementation
   contradicts the contract, the contract is wrong and gets amended
   deliberately — never silently.
2. **T03 and T04 go to `process.input`** — already registered, already
   proven on real metal in HS-106-05, already exact-claiming by
   `native_id`. Typing into a pane is what that operation is for. Do
   not invent a second terminal operation.
3. **D01-D08 need a desktop typing operation** (`desktop.type_text`,
   the RFC's own example name). Register it as a peer codec in
   `runtime.py`, structured like `process_input.py`. It admits, derives
   authority from the gesture, and receipts — **without waiting on a
   decision when the authority basis is the owner's direct gesture.**
   That is the clause-4 fast path and it is the whole ballgame for
   latency.
4. **The receipt records the act, not the content.** Text is hashed
   and bounded, never journaled in full — the same discipline
   `coder_steering` already uses (sha256 + 120 chars). Article XI
   clause 5 and RFC §12: audio frames never, token streams never.
5. **D08 is dormant.** Prove it is reachable before migrating it, or
   re-classify it as dormant-with-reason. Migrating dead code and
   claiming a closed door is the cheapest way to inflate the number.
6. **Remove each migrated site from the register in the same commit**
   as its migration. The fence will fail otherwise — which is the
   point.

## Out of scope

- The raw `typer.py` primitives (§5b confinement). This story migrates
  *callers*; the primitives stay reachable and stay in the register.
- Changing dictation behaviour, preview semantics, or wake behaviour.
- The egress and subprocess families.

## Acceptance

- **Latency, measured on real metal before and after, printed:** the
  hold-key path (capture → transcribe → type) shows no regression
  against HS-107-01's baseline. This is the first acceptance criterion
  because it is the one that matters most.
- No hold, no confirmation, and no new visible step appears on the
  owner's direct dictation path.
- All ten sites either migrated or re-classified with a reason;
  register shrinks accordingly in the same commits.
- Every migrated typing act produces a terminal receipt including
  refusals; text hashed and bounded, never journaled in full.
- The kernel spine is byte-unchanged: `git diff --exit-code` over
  `broker/admission/journal/model/executor` exits 0.
- Density guards green; zero driver-specific conditionals with a
  fifth driver registered.
- A real wake-word typing act and a real Cadence reply both proven on
  real metal with their receipts read back.

## Test plan

- **Unit:** the `desktop.type_text` codec; gesture-basis fast path;
  receipt content bounds.
- **Live (evidence):** hold-key dictation into a real focused app,
  timed; dictation → agent pane; a Cadence reply landing in a real
  pane; wake-word typing; each receipt read from the journal.
- **Census:** register shrinkage matches migrations exactly; fence
  green without loosening.

## Chef's notes

- The fast path is the design. If `desktop.type_text` waits on a
  decision when the owner already held the key, the whole product gets
  worse to satisfy a rule that explicitly says it shouldn't.
- `dictation_capture.py` has five sites — resist doing them as one
  blob. Each has its own commit point per HS-107-01, and the preview
  path is genuinely different from the others.
- Watch for the second-decision trap: dictation already consults
  `operation_policy.py`. Admission must not become a *second* policy
  evaluation for the same act.
