# HS-106-10 - Closeout — the sitting and the kernel ledger

- **Project:** holdspeak
- **Phase:** 106
- **Status:** ready
- **Depends on:** HS-106-09
- **Unblocks:** none
- **Owner:** unassigned

## The thesis (the bar)

Phase 104 closed on a seven-beat walk the owner drove himself.
Phase 105 closed on a six-beat composite. This phase closes the same
way, with one addition that no previous phase needed: **the kernel
ledger** — a written account of what is actually admitted through
the kernel, what is not, and what the debt register still holds.

The bar: the owner drives the beats, and the phase's claim survives
contact with him. Article IX.4 — the verdict is his, in his words.

## Problem

A kernel is the easiest thing in this codebase to claim falsely,
because its value is invisible when it works. Without a closeout
that walks it and a ledger that enumerates its actual coverage, "we
have a kernel now" becomes a sentence nobody can check.

## Recipe

1. **The machine beats first**, in one staged session, before the
   owner is asked for a minute of his time:
   1. An agent principal is refused a decision route by name
      (HS-106-02).
   2. A new effect site fails the census by name, then green
      (HS-106-03).
   3. An operation is submitted, held, decided, dispatched,
      receipted — read back from the journal (HS-106-04).
   4. Real text reaches a real pane through `process.input`, gated
      approve and gated deny, the deny reason reaching the agent
      verbatim (HS-106-05).
   5. A real actuator proposal waits, is approved, egresses, and
      receipts; a rejected one does not (HS-106-06).
   6. A real run, with a tool effect inside it appearing as a linked
      child operation with its own receipt (HS-106-07).
   7. The full PR loop on a real pull request in this repository:
      needs-you row → agent sent at it → comment proposed → owner
      approves → comment lands → every consequence receipted
      (HS-106-08).
   8. A hub SIGKILL mid-operation, restart, cursor replay, honest
      state — including `unknown` rendering as `unknown`.
2. **Then the sitting.** The owner drives the same beats. The
   verdict is recorded verbatim, including riders. A rider is
   chartered as a story in this phase or the next, never absorbed
   silently — the HS-104-08 precedent.
3. **The kernel ledger** is written into `final-summary.md`:
   - which operation types are registered, and which drivers use
     them;
   - the census delta: sites covered at phase start versus at close,
     against the baseline of 4 of 40;
   - what remains in the **debt register** under the migration
     provision, and therefore what an agent principal still may not
     reach;
   - the kill-criterion verdict from HS-106-07, quoted;
   - which of Article XI's clauses are now materially satisfied, and
     which remain north stars — the honesty audit from HS-106-01,
     re-run against the shipped tree.
4. **The remainders go to BACKLOG.md** as a named candidate: rung 5
   broad migration, §5b confinement, the process window, and the
   second userland program (project memory and
   decisions-to-artifacts). Named, not mega-bundled.
5. **The cadence sweep:** phase status, project README, HANDOVER,
   and any canon doc the phase touched, all updated in the closing
   commit.

## Out of scope

- New capability. Closeout ships proof and record.
- Softening any claim to make the ledger read better.

## Acceptance

- Full sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  with the result stated as a number, and the web chain green.
- The eight machine beats passed in one staged session, each with
  evidence.
- The owner's sitting run and his verdict recorded verbatim.
- The kernel ledger complete, including the census delta and the
  debt register's remaining contents.
- **If HS-106-07's kill criterion failed**, the closeout says so in
  the first line of the final summary, the name is dropped
  everywhere, and the ledger records what the shared spine actually
  turned out to be. A phase that fails its own criterion and reports
  it honestly is a successful phase.
- BACKLOG candidate filed with the remainders.
- Every rider from the sitting either chartered or explicitly
  declined by the owner.

## Test plan

- **Full suite + web chain**, output read from a file before
  anything is flipped.
- **Live (evidence):** the eight machine beats, then the sitting.
- **Guards:** all phase guards green — census, line budget,
  zero-conditional, doc voice.

## Chef's notes

- Run the machine beats to completion before booking the owner. The
  Phase-104 sitting cost him a second pass because a rider surfaced
  mid-sitting; that was worth it, but only because the machine work
  was already solid.
- The census delta is the number that tells the truth about this
  phase. Four covered of forty at the start. Whatever it is at the
  close, print it — a modest honest number beats a claim.
- Do not chain the flip behind the test run. Read the suite output
  from a file first, then flip.
