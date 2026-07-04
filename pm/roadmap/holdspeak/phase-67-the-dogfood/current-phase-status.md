# Phase 67 — The Dogfood

**Status:** **CLOSED — 6/6 (2026-07-04).** The recorded run landed: `dogfood/results/2026-07-04.md` (63 checks, 40 PASS / 14 PARTIAL / 1 FAIL / 8 SKIP-for-glass, real `.43` metal; findings F-01..F-12, three harness gaps fixed in-run). Opened 2026-06-14 on owner direction — build a thorough,
easy-to-fill dogfooding protocol that exercises literally all of HoldSpeak on
believable data (mock repos with completed stages + `.hs/` files, meetings and
dictation rendered through `say` voices, fed to the program, then verified).
All six stories are done; the run that closed it was driven headless with honest SKIPs where glass or a mic is required.

**Last updated:** 2026-07-04 (**CLOSED — the run is on the record.** 63 checks driven
against the real `.43` Qwythos endpoint: real Whisper on the `say` fixtures, real
grounded rewriting (the LL-118 brief citing every `.hs/memory.md` invariant), a real
actuator execute byte-equal into a local receiver, the learning loop taught live, the
cadence tier 5/5. Score 40 PASS / 14 PARTIAL / 1 FAIL / 8 SKIP-for-glass. The findings
ledger F-01..F-12 is the follow-on worklist — the headline is **F-05: imported meetings
never receive typed plugin artifacts** (base intel only; the plugin host runs solely on
live windows), a candidate phase of its own. Three harness gaps were found and fixed
in-run: the missing repo `blocks.yaml` fixtures, the missing `project-rewriter` stage in
`setup.sh`, and the stray uncommitted questline sources. Earlier: scaffolded + harness
built, 2026-06-14.)

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
| HS-67-01 | The isolated harness scaffold | done (committed; exercised by the run: P-01/02, X-05 isolation proven) | none |
| HS-67-02 | The mock repo fleet | done (committed; + this run added the missing `.holdspeak/blocks.yaml` ×3 and the stray questline `src/lib/` files) | HS-67-01 |
| HS-67-03 | Scenario library + fixture generator | done (committed; P-04 rendered all 38 fixtures; every meeting + dictation scenario driven) | HS-67-01, HS-67-02 |
| HS-67-04 | The master protocol | done (committed; driven end to end — wording drifts F-11/T1-16/X-02 noted for the next revision) | HS-67-02, HS-67-03 |
| HS-67-05 | Docs wiring | done (CONTRIBUTING.md §Running the tests points at the harness + protocol) | HS-67-01..04 |
| HS-67-06 | Closeout: a recorded run | done — [`dogfood/results/2026-07-04.md`](../../../dogfood/results/2026-07-04.md) (force-committed past the results gitignore as the phase's exit evidence) | HS-67-01..05 |

## Where we are

CLOSED. The recorded run is [`dogfood/results/2026-07-04.md`](../../../dogfood/results/2026-07-04.md)
(force-committed as the exit evidence; future runs stay gitignored per the results
convention). The protocol answered its one question honestly: the product works end to
end — transcription, intel, routing controls, the queue, aftercare, the actuator gates,
grounded dictation, languages, the learning loop, cadence, isolation — with one
capability gap promoted to the worklist (F-05) and a dozen precise findings filed. The
harness itself came out stronger (fixtures + stage config fixed). Re-run each release.
