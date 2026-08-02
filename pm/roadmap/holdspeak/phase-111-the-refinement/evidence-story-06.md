# Evidence - HS-111-06

- **Story:** HS-111-06 - Delivery and process
- **Status:** done
- **Date:** 2026-08-01

## Proof

### Captured run — 2026-08-02T02:48:04Z

- **Command:** `uv run pytest -q tests/unit tests/integration`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d8b5b776833798d4b5f407eb4e82345b3eaee9c9

```text
........................................................................ [  1%]
........................................................................ [  3%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
.................................s...................................... [ 85%]
........................................................................ [ 87%]
..........................ss............................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
.........................................                                [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
4214 passed, 3 skipped in 434.63s (0:07:14)
```

(Captured run = the full python proof including the 7 NEW sweep
tests: unit 3450 + integration 764, 3 pre-existing model skips. Web
ran separately, output read: exit 0 — **69 test files / 398 tests**,
token gate clean, architecture guard 198 files, typecheck, build
green.)

## What shipped

The kernel-facing programs rethought as instrumentation, per the
verified audit (.tmp/hs-111-06-audit.md), plus the owner's
duplicate-rows report traced to the wire and FIXED:

- **The belt → the rails panel**: the ~450-pin emoji flood (the
  phase's largest violation — it buried the whole desk) is dead.
  Off-belt sessions fold into per-agent census token lines
  (`CLAUDE 141 · IDLE 138 · …`) with the roster behind a folded
  ledger; needs-you sessions are the ONLY individually rendered
  layer — steady inverted-video cells, the blink species deleted;
  ticker a bounded ledger; flip strip MxRadio + ConfirmVerb; zero
  emoji anywhere.
- **The process window → the process monitor**: five SurfaceLedger
  sections (`HH:MM:SS · OP · TARGET · PRINCIPAL · STATE`),
  StatusPill dead, ALL heads render at zero (a zeroed instrument,
  never a void), needs-you verb ANSWER, footer
  `KERNEL · CURSOR n · RUNS n`. **processWindow.ts + reducer
  git-diff EMPTY** — the HS-109-06 pure-consumer law held; wire
  tests unedited.
- **Delivery**: board ledgers, gadget launch composer with the token
  consequence line, the dead keypad (emitting a CSS class whose caps
  died in HS-111-04) rebuilt as TransportRow, dossier facts/RAW
  folds.
- **PaneWell extracted** (one shared seam for SessionPullout + the
  delivery terminal): **xterm deferred to HS-111-11 by argued
  decision** — building it against the stripped-peek wire would
  ship the same photograph; story 11 swaps ONE interior and both
  inherit.
- **Project memory**: ledger timeline, lifecycle tokens, gadget
  promote/supersede, `GROUNDED ON n OF m` in Ask's exact species.

## The data fix (the owner's PR-387 duplicates — root-caused live)

Two wire bugs, both proven and closed:
1. **Liveness-by-gaze**: the state sweep ran ONLY as a side effect
   of `/api/delivery/factory/discover` — surfaces that never call it
   showed `starting` for days (the audit proved it live: its own
   board-open fired the sweep and 14 stale attempts advanced to
   `ended` minutes later). Now the sweep runs on the attempts READ
   path — staleness is impossible by construction.
2. **Sibling minting**: a worktree-resolution change defeated the
   idempotence key, minting a `rider_claim` sibling per run. The key
   is now `(session, story, source)`; a claim with no session
   attempt ADOPTS the unbound launch attempt (guarded UPDATE, the DB
   partial-unique index stays the final guard).
Seven new unit tests pin both behaviors
(tests/unit/test_delivery_attempts_sweep.py). Historical sibling
rows remain as ended history — nothing deleted. **No
pre-existing-dirty python file was touched** (attempts.py +
routes/delivery_attempts.py were clean before this story).

## Live proof (real hub, :8765)

Before/after in [assets/hs-111-06/](./assets/hs-111-06/):
`before-desktop-buried.png` + `before-desktop-belt-flood.png` (the
pin flood burying the desk) vs `desktop-10-rails-open.png` (the
rails panel: 14 inverted NEEDS YOU cells, census lines, bounded
events ledger), `desktop-30-process.png` (the zeroed instrument),
`desktop-21-delivery-terminal.png` (styled TransportRow keypad),
`desktop-23-launch-composer.png`, `mobile-10`. Full 24-shot set
reviewed (.tmp/hs-111-06-after/), error leg included (in-flow
Not Found + the honest `UNAVAILABLE dw exited 2` recovery).

## Honest notes

- Terminal Enter toggle is a TransportKey (inverted when active),
  not the audit's CheckGadget sketch — matches the HS-111-04 steer
  composer so both are one species.
- PM timeline-with-data could not be walked (the resident project
  404s on read — pre-existing); ledger rendering locked by unit
  tests; the error faces captured are the honest state.
- The attempts-path sweep skips the LaunchLedger JSON catch-up
  (attempt state is authoritative; the ledger row catches up on the
  next discover).
- Walk conduct: nothing decided, nothing sent, no flip proposed.
