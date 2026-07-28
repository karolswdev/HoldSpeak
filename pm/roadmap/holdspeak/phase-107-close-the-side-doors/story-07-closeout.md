# HS-107-07 - Closeout — the sitting and the census delta

- **Project:** holdspeak
- **Phase:** 107
- **Status:** planned
- **Depends on:** HS-107-06
- **Unblocks:** none
- **Owner:** unassigned

## The thesis (the bar)

Phase 106 closed on a census delta of **zero** — it built the kernel
and moved no doors, honestly reported. This phase exists to move that
number, so the number **is** the verdict.

The bar: the delta is printed as a plain figure in the first lines of
the final summary, whatever it turns out to be, and the owner drives
the beats himself (Article IX.4).

## Problem

Migration work is the easiest kind to overstate, because its output is
an absence — nothing visibly happens, and the only evidence is a count
that the people who produced it also reported. Phase 106's own closeout
caught this in the opposite direction: the machine sitting failed a
beat and reported 7 of 8 rather than rounding up.

## Recipe

1. **Machine beats first**, in one staged session, before asking the
   owner for a minute:
   1. Hold-key dictation on real metal, **timed**, against
      HS-107-01's baseline — no regression.
   2. A dictation typing act read back from the journal with its
      receipt.
   3. Dictation → agent pane through `process.input`.
   4. A Cadence reply landing in a real pane with its receipt.
   5. A migrated subprocess: success, non-zero exit, and an
      indeterminate outcome not blindly retried.
   6. A migrated egress with its destination named in the receipt, and
      one honest refusal.
   7. Transcription timed — **unchanged** from baseline.
   8. A new unlisted effect site failing the fence by name, then green.
2. **Then the sitting.** The owner drives the same beats. Verdict
   recorded verbatim, riders chartered rather than absorbed.
3. **The census delta, printed.** Covered at phase start (4 of 40)
   versus at close, as a plain number in the first lines of
   `final-summary.md`. No rounding, no framing.
4. **The ledger:** which operation types exist and which drivers use
   them; what remains in the register with each closing condition;
   which Article XI clauses are now materially satisfied and which
   remain north stars, re-audited against the shipped tree; and
   whether clause 6 still stands (it will).
5. **Remainders to BACKLOG** as a named candidate: §5b confinement and
   the ten primitives, the second userland program, the process
   window, the generic liveness seam, and the CI blind spot from Phase
   106 (`tests/e2e/test_live_bus.py` skips without Playwright and a
   built bundle — three tests sat red on main across three merges).
6. **Cadence sweep** in the closing commit.

## Out of scope

- New capability.
- Framing the delta to read better than it is.

## Acceptance

- Full suite green (pre-existing failures documented), web chain green.
- Eight machine beats passed in one staged session, each evidenced —
  **or an honest count below eight with the failures named.**
- **Dictation and transcription latency printed, before and after.**
  A regression here fails the phase regardless of the census delta.
- The owner's sitting run and his verdict recorded verbatim.
- The census delta printed as a number in the first lines of the final
  summary.
- Clause 6's continued force stated with its unmet sunset.
- BACKLOG candidate filed with the remainders.
- Every sitting rider chartered or explicitly declined by the owner.

## Test plan

- **Full suite + web chain**, output read from a file before any flip.
- **Live (evidence):** the eight beats, then the sitting.
- **Guards:** fence, density, doc counts.

## Chef's notes

- Print the delta before writing the prose around it. It is very easy
  to write a summary that makes 4→26 sound like 4→36.
- Run the beats to completion before booking the owner. Phase 106's
  sitting was staged with a broken beat and the owner had to be told
  before he sat down; that was the right call but a poor use of his
  time.
- If dictation got slower, that is the headline — above the delta,
  above the count, in the first paragraph.
