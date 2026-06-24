# Phase 67 — The Dogfood

**Status:** scaffolded. Opened 2026-06-14 on owner direction — build a thorough,
easy-to-fill dogfooding protocol that exercises literally all of HoldSpeak on
believable data (mock repos with completed stages + `.hs/` files, meetings and
dictation rendered through `say` voices, fed to the program, then verified).
HS-67-01..04 are built; the phase stays open until a run is recorded (HS-67-06).

**Last updated:** 2026-06-14 (**scaffolded + harness built** — `dogfood/` exists:
the isolated runner + sandbox config (HS-67-01), the 3-repo mock fleet
(HS-67-02), the 12-scenario library + `make_fixtures.py` + committed transcripts
(HS-67-03), and the two-tier fillable `PROTOCOL.md` + results template
(HS-67-04). Opt-in plumbing pytest `tests/e2e/test_dogfood_plumbing_e2e.py`
green (20). Remaining: docs wiring (HS-67-05) and a recorded real-metal run
(HS-67-06). The story rows below mark what is built vs. what awaits a commit.)

## The thesis — why this phase

HoldSpeak shipped (v0.3.0 on PyPI, Phase 65) and is now documented (Phase 66),
but it has never been exercised end to end, as a whole, on data that looks like
real work. Individual phases proved their own slice on real metal; nobody has
sat down and driven every surface in one pass against believable repos and
meetings. This phase builds the instrument for that: a self-contained,
**isolated** harness with believable fixtures, and a fillable protocol the owner
can re-run each release to answer one question honestly — does the whole thing
actually work?

## Goal

Deliver a `dogfood/` harness and a fillable two-tier `PROTOCOL.md` that, run by
the owner, exercises every user-facing surface of HoldSpeak on believable data
and produces a durable, re-runnable record of what works. Plus a thin automated
guard so the fixtures can't silently rot.

## Scope

- **In:** the isolated harness (HS-67-01); the 3 mock repos (HS-67-02); the
  scenario library + `say` fixture generator + transcript fixtures (HS-67-03);
  the master protocol + results template (HS-67-04); docs wiring (HS-67-05); a
  recorded run + findings + final summary (HS-67-06). An opt-in plumbing pytest.
- **Out:** any product/runtime code change (this phase is additive tooling +
  docs; fixing bugs the run *finds* is follow-on work, filed as new phases/issues).
  No CI gating on the real-metal tier (it needs `.43` + a Mac mic).

## Exit criteria (evidence required)

- The harness runs isolated: a full session never writes outside `dogfood/_home`
  (HS-67-01, proven by protocol check X-05).
- All three mock repos load through the real loaders (KB + `.hs/` context), and
  every scenario renders to audio + every committed transcript parses (HS-67-02,
  HS-67-03; guarded by the plumbing pytest).
- `PROTOCOL.md` covers every surface in the functional inventory across both
  tiers and is fillable (HS-67-04).
- The harness is discoverable from the contributor docs (HS-67-05).
- One full run is recorded under `dogfood/results/` with findings filed
  (HS-67-06).

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-67-01 | The isolated harness scaffold | built (awaiting commit) | none |
| HS-67-02 | The mock repo fleet | built (awaiting commit) | HS-67-01 |
| HS-67-03 | Scenario library + fixture generator | built (awaiting commit) | HS-67-01, HS-67-02 |
| HS-67-04 | The master protocol | built (awaiting commit) | HS-67-02, HS-67-03 |
| HS-67-05 | Docs wiring | backlog | HS-67-01..04 |
| HS-67-06 | Closeout: a recorded run | backlog | HS-67-01..05 |

## Where we are

The harness and protocol are written and self-verified: `make_fixtures.py`
renders real `say` audio (checked a meeting clip at 16 kHz mono and a dictation
clip), the three KBs parse, and the opt-in plumbing pytest is 20 green / clean
skip. Nothing is committed yet — the story rows say "built (awaiting commit)" so
a reviewer flips them to `done` with evidence when the work lands via PR. Next:
wire the harness into the contributor docs (HS-67-05), then the owner drives
`PROTOCOL.md` once on real metal and we record the run + findings (HS-67-06),
which is what actually closes the phase.
