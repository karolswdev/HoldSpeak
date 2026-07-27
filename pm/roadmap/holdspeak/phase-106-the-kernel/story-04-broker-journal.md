# HS-106-04 - The broker and the journal — four calls

- **Project:** holdspeak
- **Phase:** 106
- **Status:** done
- **Depends on:** HS-106-01, HS-106-02, HS-106-03
- **Unblocks:** HS-106-05, HS-106-06, HS-106-07
- **Owner:** unassigned

## The thesis (the bar)

This is the spine: `holdspeak/kernel/` with exactly four public
caller calls — `read`, `submit`, `decide`, `events` — a typed
operation registry, and an append-only hash-chained journal behind
them. The whole design's credibility rests on this package staying
**small and boring**. The RFC's top risk is a God envelope, and the
countermeasure is not discipline-by-intention; it is the line-budget
guard and the zero-conditional census test that HS-106-03 already
stood up.

The bar: a reader can hold the entire broker in their head. If they
cannot, the phase has already failed and the later stories are
decoration.

## Problem

The four ideas — admit, derive authority, decide once, receipt —
exist five times over in private forms (`connector_runtime.
PermissionGate:84`, the actuator proposal machine, `delivery/
commands.py:328` and `:676`, `web/routes/primitives/_shared.py:87`,
and the Phase-104 gate). None of them can be reused by the others,
so every new capability re-implements consent from scratch and the
receipts do not compose.

## Recipe

1. **Four caller calls, no more** (RFC §3):
   - `read(refs, view, consistency)` — canonical objects, process
     state, operation state, receipt projections. Refs, never copied
     authoritative content. Cheap; pays no ceremony beyond auth.
   - `submit(OperationRequest)` — the only entrance for a
     consequential run, mutation, signal, or external effect.
     Returns a handle: `running | awaiting_decision | refused |
     <terminal>`.
   - `decide(operation_id, approve|reject, expected_revision)` —
     records a decision against an ALREADY-ADMITTED operation. It
     can never change payload, target, or placement. Approval mints
     one-use authority bound to the admitted envelope hash. The
     Phase-104 gate is this call, prototyped early — it is adapted,
     not rebuilt.
   - `events(after_cursor, filter)` — replayable batches from the
     journal. WebSocket and long-poll become transports for this
     call, never truths of their own.
2. **Operations are registered versioned types, never new
   syscalls.** Registration is trusted startup configuration. No
   LLM, plugin, or runtime caller may register an operation type.
   Each type is a module with a typed codec — the envelope must
   never become a JSON junk drawer.
3. **The caller never asserts authority** (RFC §4). Actor, control
   mode, authority basis, effect class, data classes, and policy
   version are DERIVED AT ADMISSION from HS-106-02's principal. The
   broker authenticates, validates against the module's codec,
   resolves refs, hashes the canonical material, snapshots the
   operation spec plus current policy, and records an admitted
   envelope.
4. **Authority is four layers, checked in order, once** (RFC §5):
   authenticated principal → declared capability → hard
   prerequisites (these refuse even in YOLO — the Phase-93
   invariant rule, unchanged) → interruption policy. The result is a
   verifiable, expiring, payload-bound **execution warrant** — the
   policy-snapshot-plus-envelope-hash shape `delivery/commands.py`
   already models. Authority is resolved ONCE at admission.
5. **The executor plane is specified beside the four, not hidden
   under them** (sol's amendment 3): `claim` (atomic acquisition of
   admitted work — the semantics `HubCommandService.claim_for_node`
   already implements), `receipt`/`ack` (immutable outcome,
   including indeterminate), `reconcile` (resolve uncertain effects
   by command id). An executor acquiring already-admitted work is
   not proposing a new consequential act and is never forced through
   `submit`. A remote executor validates the warrant and re-checks
   its LOCAL hard prerequisites only — it never re-authenticates the
   human or re-resolves grants, which would create the second policy
   decision the migration rules forbid.
6. **The journal is truth; the bus is a projection** (RFC §6).
   Append-only operation lifecycle metadata: hub sequence, event id,
   operation/process/correlation/causation ids, typed event version,
   refs, privacy class, timestamp. Domain content stays in its
   canonical store — the journal holds refs, hashes, bounded heads,
   result refs. Records are SHA-256 hash-chained per stream, the
   Borrowed-Fire-II carry-over that upgrades the audit claim from
   audited to provable. Every attempted consequence produces an
   immutable terminal receipt, **including refusals and
   indeterminate outcomes**.
7. **The process model is a projection, not a rewrite.** One index
   over the NATIVE records — agent sessions, capability invocations,
   plugin jobs, captures, Work attempts project in; their tables
   stay authoritative. Universal states stay small
   (`starting/running/waiting/unknown/ended/failed`); domain states
   remain domain data. A signal is a submitted operation.

## Out of scope

- Adapting any driver. Slices are 05, 06, 07 — this story lands the
  spine and at most one trivial reference operation type to prove
  the calls compile end to end.
- Replacing `/ws`. It becomes a transport for `events` in the
  slices; this story defines the cursor contract it will carry.
- Effect-capability confinement (RFC §5b).
- Any new UI.

## Acceptance

- `holdspeak/kernel/` exposes exactly four public caller calls plus
  the three executor-plane calls, and the module census proves no
  fifth public entrance exists.
- The line-budget guard and the zero-conditional guard from
  HS-106-03 are green against the real broker — not adjusted upward
  to fit it. If the budget is genuinely wrong, it is raised in a
  separate, argued commit that says so.
- A submitted operation that is refused produces a receipt, proven
  by test — refusal receipts are the clause most likely to be
  quietly skipped.
- The hash chain is tamper-evident: mutate a journal record, watch a
  named verification failure, restore, watch green (the HS-104-03
  mutation method).
- `events` replays from a cursor across a hub restart and returns
  the same batch — proven with a real SIGKILL, not a graceful stop.
- An admitted envelope is immutable: a `decide` attempting to alter
  payload, target, or placement is refused by name.
- An agent principal calling `decide` is refused by name (Article
  XI.4, enforced at HS-106-02's derivation point).
- A warrant past expiry is refused at claim; a revoked warrant is
  refused at claim.

## Test plan

- **Unit:** envelope codec per operation type; admission ordering of
  the four authority layers; warrant minting, expiry, revocation;
  hash-chain append and verify.
- **Mutation (evidence):** journal tampering; a driver conditional
  added to a broker module; the line budget blown — each a named
  failure, then green.
- **Integration:** submit → await decision → decide → dispatch →
  receipt → event, over real HTTP against a real spawned hub.
- **Restart (evidence):** SIGKILL mid-operation, restart, cursor
  replay, and the operation's honest state on recovery.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

### Verification note — 2026-07-26

The exact full-suite command completed with **4,245 passed, 41 skipped,
1 failed**. The sole failure is pre-existing and outside this story's
changed surface: `tests/uat/test_voice_notes.py::
test_transcribe_up_but_unreachable_is_honest` receives the honest
`Transcribe failed (HTTP 502).` response but its assertion accepts only
wording containing `reach` or `not up`. It reproduces standalone; no UAT
proxy or voice-note code changed here. The final kernel/gate/schema proof
set is **64 passed**, including real HTTP, SIGKILL restart, mutation,
warrant, receipt, and density proofs. This is the phase exit criterion's
explicit "pre-existing unrelated failures documented per-story" case.

## Chef's notes

- Generalize nothing until two real drivers need it. The envelope
  field that "will obviously be needed" is exactly how the God
  envelope arrives. Slice II and III are where fields earn their
  place.
- The Phase-104 gate already IS `decide`. Adapt it — a second
  decision surface would be the double-truth failure the migration
  rules name.
- Audio frames and token streams are never journaled (RFC §12). Put
  that in the code as a refusal, not a convention.
- Keep `read` genuinely cheap. If reads start paying admission
  ceremony, the desk gets slow and the kernel gets blamed for being
  a kernel when it is really being badly written.
