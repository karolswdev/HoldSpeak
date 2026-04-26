# Evidence — HS-3-06: DoD sweep + phase-3 closure

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-06
- **Captured at HEAD:** `3f36046` (pre-commit; this commit closes the phase)
- **Date:** 2026-04-26

## What shipped

11-file evidence bundle at
`docs/evidence/phase-dir-loop-closure/20260426-1111/`:

```
00_manifest.md
01_env.txt
02_git_status.txt
10_ut_project_root.log         (8 passed)
10_ut_runtime_counters.log     (15 passed)
10_ut_doctor.log               (26 passed)
20_it_project_context.log      (4 passed)
20_it_cold_start.log           (2 passed)
20_it_llama_cpp_e2e.log        (1 SKIPPED — gated; runs on reference Mac)
30_full_regression.log         (1007 passed, 13 skipped)
40_doctor_run.log              (`uv run holdspeak doctor` against this checkout)
99_phase_summary.md             (what shipped + 8 deferred items)
```

Each file leads with `# Captured: <ISO timestamp>` + `# Git: <sha>`,
and test logs additionally lead with `# Command: <exact command>`
per the HS-2-11 cadence convention.

Phase tracking docs flipped:
- `current-phase-status.md` → "Last updated" bumped, story-06 row to `done`, all 6 phase-exit boxes ticked with evidence pointers.
- `pm/roadmap/holdspeak/README.md` → phase index row 3 to `done`, "Current phase" reverted to `none — between phases`, "Last updated" bumped.

## Test output

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output captured in 30_full_regression.log)
1007 passed, 13 skipped in 16.08s
```

Pass delta vs. HS-3-scaffold baseline (`eefba0a` — 973 passed):
**+34** cumulative across the phase. Pass delta vs. HS-3-05
(`3f36046` — 1007 passed): **+0** (this commit ships no new tests;
the bundle exercises the existing phase-3 suite).

### Bundle smoke

```
$ ls docs/evidence/phase-dir-loop-closure/20260426-1111/ | wc -l
12  (11 files + the manifest)
```

## Deviations from story scope

- The story stub said the bundle path uses the timestamp at the
  start of the sweep. Used `20260426-1111` per that convention.
- Per the standing `feedback_no_validation_spikes` memory, the
  bundle does **not** include latency benchmarks. The bundle proves
  the pipeline runs end-to-end (gated tests + integration tests +
  unit tests) but does not assert latency targets. Latency is the
  user's dogfood-time concern.
- The HS-3-03 gated `llama_cpp` e2e test is captured as `SKIPPED`
  in `20_it_llama_cpp_e2e.log` — the dev box doesn't carry the
  GGUF (~3 GB) and per the standing memory, fetching it just to
  satisfy this bundle would be ceremony. The user runs it against
  the real GGUF on the reference Mac during ongoing dogfood.

## Phase summary headline

**Phase 3 closes with the dictation pipeline genuinely useful in
dogfood:** project context flows end-to-end, the cross-platform
LLM leg is tested + documented, operational counters surface in
doctor, and the cold-start hard-cap protects "useful" from a
runaway first call. See `99_phase_summary.md` in the bundle for
the full enumeration of what shipped and 8 deferred follow-up
items.
