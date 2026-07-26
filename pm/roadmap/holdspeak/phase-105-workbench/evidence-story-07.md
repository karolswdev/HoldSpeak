# Evidence - HS-105-07

- **Story:** HS-105-07 - Closeout — the sitting loop and the spec ledger
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T17:37:19Z

- **Command:** `sh -c tail -2 /tmp/hs105-final-pytest.txt && grep -E 'Tests|gate|exit' /tmp/hs105-final-web.txt | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 829fe949c9c4ec7bb93a883a793abaefa960dafc

```text
4150 passed, 37 skipped in 898.14s (0:14:58)
exit=0
> holdspeak-web@0.0.1 tokens:gate
token gate: clean (61 allow-listed exceptions, all in use)
exit=0
```

## The machine close (2026-07-26, merged main 8e56ba7f)

- **Full pytest sweep** (metal excluded): **4150 passed, 37 skipped,
  ZERO failures, exit 0** — output written to file and read. The
  sweep EARNED its place first: its provisional runs caught the
  stale API-surface manifest (regenerated per the named ritual) and
  a hardcoded phase-count pin (now asserting the floor, not a moving
  total) — both paid on PR #373 before the merge.
- **Web chain**: tsc clean, vitest 340/340 (55 files), build clean,
  tokens gate clean, exit 0.
- **The composite six-beat walk**, one continuous live session on the
  staged hub (assets/hs105-close-composite.png): density ≥30 objects
  reads; select answers (cell + inverted label); a drawer opens into
  its window AND RESTORES across reload; Info opens by right-click;
  the drop verb tag rides a live drag; the menu grammar proven BOTH
  ways (runnable with a selection, ghosted-with-reason without —
  beat 6's first "failure" was the walk asserting one-sidedly; the
  product was right).
- Per-story live proofs recorded in evidence-story-01..06 (each with
  its own walk shots, all read).
- Bookkeeping shipped: final-summary.md (including the SPEC LEDGER —
  contract-specified atoms vs named TypeScript-only spec debt, per
  the standing web-desk-is-the-spec direction) and BACKLOG candidate
  AA (the remainders, recorded not waived).

## The sitting (the one input only the owner renders)

Staged and health-checked: the dense seeded desk on
`http://localhost:8788/`, serving the final merged bundle. The
verdict per Article IX.4 goes here verbatim when rendered.

## The owner's sitting verdict (2026-07-26)

Verbatim: **"I accept. Although I still think that we need to do a
much better job at making the OS an actual OS. I'm guessing that's
Phase 104?"**

Acceptance closes HS-105-07 and the phase 7/7. The rider is recorded
as the STANDING BAR for what follows: Phase 104 (Borrowed Fire II —
the gate, receipts, PR rows: the OS's consent and process organs) and
the kernel phases chartered from PLAN_KERNEL_OPERATION_BROKER.md are
exactly the "actual OS" program — the innards under the grammar this
phase installed — with backlog candidate AA and the deferred
workspaces/process-window items carrying the felt-OS remainders.
