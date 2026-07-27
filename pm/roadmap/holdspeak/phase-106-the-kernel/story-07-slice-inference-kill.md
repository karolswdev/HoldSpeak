# HS-106-07 - Thin slice III — inference, and the kill criterion

- **Project:** holdspeak
- **Phase:** 106
- **Status:** done
- **Depends on:** HS-106-06
- **Unblocks:** HS-106-08
- **Owner:** unassigned

## The thesis (the bar)

The third heterogeneous driver and the phase's verdict story.
Inference runs differ again on every axis: **placement** (which
machine, which model, what egress), **duration** (long attempts, not
a keystroke), **streaming** (tokens that must never be journaled),
and **cancellation** (a running attempt the owner interrupts).

And then the criterion, adopted from Codex verbatim in spirit:

> If the first three drivers — terminal input, actuator egress,
> inference runs — cannot share admission, principal, journal, and
> receipt code without driver-specific conditionals in the broker,
> **stop calling it a kernel.**

This story is written so it can genuinely fail. A verdict story
whose failing branch is unwritten is not a verdict story.

## Problem

`RunLifecycle` (`holdspeak/web/routes/primitives/_shared.py:87`)
owns run admission and lifecycle privately. Meanwhile Article XI
clause 2 says a consequential effect performed by a tool inside a
model's run is a causally linked CHILD operation of that run — the
nested-effects loophole sol demonstrated. Nothing in the codebase
expresses that parent-child relationship today, which is precisely
how an agent's file writes and shell commands could hide inside "the
run's interior."

## Recipe

1. **Register `inference.run`** with a typed codec: definition ref,
   grounding refs with revisions, placement, deadline. `RunLifecycle`
   becomes a kernel adapter **for recipes first** — the narrowest
   honest starting point.
2. **Placement and egress are derived, not asserted.** Which node,
   which model, whether anything leaves the machine — all derived at
   admission from the principal and policy, all recorded. Article
   III is satisfied from the journal.
3. **Tokens are never journaled** (RFC §12). The stream is exempt
   computation under Article XI clause 5. The operation is
   journaled; its interior is not. Enforce this as a refusal in
   code, not a convention in a comment.
4. **Child operations close the loophole.** A tool effect inside a
   run submits as a causally linked child operation with the parent
   run's correlation. Clause 2 becomes a mechanism: the receipt for
   the file write exists at the layer where the file write happened,
   not swallowed by the outer run's receipt.
5. **Cancellation is a submitted operation**, not a side channel. A
   signal is an operation (RFC §6).
6. **Long attempts survive restart.** A run in flight when the hub
   dies recovers to an honest state — `running` if it truly is,
   `unknown` if that cannot be established. `unknown` is a real
   state and must appear on the desk as itself, never rounded to
   failed or done.
7. **Then apply the kill criterion.** With three heterogeneous
   drivers landed, the census runs for real:
   - zero driver-specific conditionals in broker modules;
   - admission, principal derivation, journal write, and receipt
     minting are literally the same code for all three;
   - the line budget held without being raised to fit.
   The verdict is recorded either way.
8. **Write the failing branch too.** If the criterion fails: the
   name "kernel" is dropped, the evidence records exactly which
   driver forced which conditional and why, the RFC gains a
   post-mortem section, and HS-106-08 is rechartered against
   whatever the shared spine actually turned out to be. The durable
   idea is the invariant spine, not the name.

## Out of scope

- Migrating chains, workflows, Ask, plugin jobs, or mesh runs. Those
  are rung 5, after the criterion.
- Capture, Whisper, punctuation, and rewrite — they stay on the
  low-latency path permanently. Audio frames are never journaled.
- Streaming UI changes.

## Acceptance

- A real recipe run goes through `submit(inference.run)` end to end
  on real metal against the LAN endpoint — control-versus-treatment,
  not a seeded fixture.
- A tool effect inside a run appears as a linked CHILD operation
  with its own receipt, proven by a run that writes a file and a
  journal query showing parent and child.
- Token streams appear nowhere in the journal; a grep census proves
  it.
- Cancelling a long run is a submitted operation with a receipt.
- A hub SIGKILL mid-run recovers to an honest state, and `unknown`
  renders as `unknown` on the desk.
- **The kill criterion is applied and its verdict recorded
  verbatim**, with the census output pasted into the evidence — pass
  or fail.
- On pass: the three drivers demonstrably share admission, principal,
  journal, and receipt code, shown by citing the same functions from
  all three adapters.
- On fail: the post-mortem is written, the name is dropped in docs
  and code, and the phase's remaining stories are rechartered before
  anything else ships.

## Test plan

- **Unit:** the `inference.run` codec; child-operation linkage;
  cancellation as an operation; placement derivation.
- **Census (evidence):** zero driver conditionals; no tokens in the
  journal; the same admission and receipt functions reached from all
  three adapters.
- **Live (evidence):** a real run on the LAN endpoint; a run that
  performs a tool effect; a cancelled run; a SIGKILLed run.
- **Guards:** line budget green without being raised.
- **Full suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Chef's notes

- The honest failure mode here is a conditional that hides as
  polymorphism — a driver-shaped strategy object selected by a
  branch in the broker is still a branch in the broker. The census
  must catch dispatch-by-type, not just literal `if`.
- Clause 2 is the clause that makes Article XI worth having. If
  child operations are hard, that difficulty IS the finding — the
  loophole is real and expensive to close, and the owner deserves to
  know the price rather than get a clause that reads well.
- Do not soften the criterion when it is close. "Almost no
  conditionals" is a fail. The whole value of a written kill
  criterion is that it is applied on the day it is inconvenient.
