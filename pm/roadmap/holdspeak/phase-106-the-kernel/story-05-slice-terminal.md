# HS-106-05 - Thin slice I — terminal input

- **Project:** holdspeak
- **Phase:** 106
- **Status:** done
- **Depends on:** HS-106-04
- **Unblocks:** HS-106-06
- **Owner:** unassigned

## The thesis (the bar)

The reference driver. The owner controls agents through xterm.js;
text going into a pane is the most consequential and most frequent
thing this system does, and per the census every typing family
bottoms out at `holdspeak/tmux_transport.py:20` (`send_text_to_pane`).
Terminal delivery is where the strangler ladder starts because the
authority machinery is already the most mature here —
`delivery/commands.py` already models claim semantics
(`NodeCommandProcessor:328`, `HubCommandService:676`) and a
payload-bound warrant in all but name.

The bar: the existing protocol is **adapted, not rewritten**. If
this slice requires touching the node protocol, the broker is wrong,
not the protocol.

## Problem

Terminal delivery has its own admission, its own idea of authority,
and its own receipts. Nothing else in the system can reuse any of
it, and the desk cannot answer "what did we send to that pane, on
whose authority, and what came back" from one place.

## Recipe

1. **Register `process.input`** as a versioned operation type with a
   typed codec — text, submit flag, target process ref with expected
   generation. Its semantics are terminal-specific and live in the
   operation module, never in the broker.
2. **Adapt the existing services.** `HubCommandService` and
   `NodeCommandProcessor` keep their protocol; they gain a kernel
   adapter. `HubCommandService.claim_for_node` becomes the executor
   plane's `claim` — the RFC observes it already implements those
   semantics, so this is a naming and wiring change, not a new
   queue.
3. **Routes become façades.** The delivery and coder routes keep
   their shapes and additively return a kernel operation id.
   `coder_steering` and `coder_factory` remain the executors and are
   not rewritten. Existing clients keep working, unchanged.
4. **Dual-link by correlation, never by copying.** Domain tables
   stay authoritative; the journal holds refs and hashes. There is
   never a moment where two tables both claim to be the truth about
   one send.
5. **One decision, one warrant.** The hub decides at admission; the
   node validates the warrant (expiry, revocation, target
   generation, sequence, payload hash) and re-checks its LOCAL hard
   prerequisites immediately before typing. It never re-authenticates
   the owner.
6. **Indeterminate outcomes are first-class.** A send whose result
   is unknown is receipted as unknown and reconciled by command id.
   It is never blindly retried — the two-sided ledger rule.
7. **The Phase-104 gate rides in front, unchanged in behaviour.** A
   gated risky call still stops and asks the desk; it now does so as
   `decide` against an admitted `process.input`, and the shade card
   renders from the journal instead of a private table.

## Out of scope

- Any other typing family. Dictation, Cadence replies, macros, keys,
  and kill are rung 5 and wait for dictation's commit-boundary
  semantics to be settled — dictation is migrated once, never twice.
- Spawn and launch were re-scoped into HS-106-08 by owner decision on
  2026-07-27, after the three-driver kill criterion passed. Their
  original deferral had served its purpose: actuator and inference had
  both voted before the fourth driver registered.
- Rewriting the node protocol.
- Removing the old routes. The strangler keeps them.
- xterm.js UI work. The pane surface is unchanged by this story;
  only what happens behind a keystroke moves.

## Acceptance

- A real steered agent session takes real input through
  `submit(process.input)` end to end on real metal — the Phase-104
  live rig (`claude -p --settings <file>` against a real spawned
  hub), not a fixture.
- The Phase-104 gate's approve and deny both still work, and the
  deny reason still reaches the agent verbatim — the HS-104-02
  proof, re-run against the kernel path and shown identical.
- Existing delivery and coder route clients work unchanged; the
  operation id is additive.
- Every send has exactly one decision. A census proves no second
  approval path exists for the same act.
- A killed node mid-send yields an indeterminate receipt and a
  reconcile by command id — proven with a real SIGKILL.
- The broker gained zero terminal-specific conditionals; the
  HS-106-03 guard proves it.
- Latency: a normal ungated send stays within the Phase-104 unarmed
  latency budget. Measured, not assumed.

## Test plan

- **Unit:** the `process.input` codec; warrant validation at the
  node; reconcile by command id.
- **Integration:** submit → claim → type → receipt over real HTTP
  against a real spawned hub.
- **Live (evidence):** two real agent sessions — one clean send, one
  gated send approved, one gated send denied with the reason
  reaching the agent verbatim.
- **Restart (evidence):** SIGKILL the node mid-send; indeterminate
  receipt; reconcile.
- **Guards:** zero-conditional and line-budget census green.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Chef's notes

- The temptation here is to migrate the other seven typing sites
  "while we are in there." Do not. Breadth inside the terminal
  family is not heterogeneity, and it is exactly how the broker
  ossifies around Phase-94 semantics before actuators and inference
  get a vote.
- Read `delivery/commands.py` before designing anything. Much of the
  warrant model is already there under other names; discovering that
  late means writing a second one.
- Keep the pane feeling instant. The owner will judge this slice by
  whether typing into an agent still feels like typing.
