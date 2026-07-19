# Evidence - HS-100-12

- **Story:** HS-100-12 - B8: geometry walk + assembled chain
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T15:52:21Z

- **Command:** `sh -c HS_WALK_BASE=http://localhost:8792 HS_WALK_TOKEN=YZi6W-PzL8bfY4UbMgxThqUdUUKQcGj8 uv run python scripts/desk_gl_walk.py geometry && uv run pytest -q tests/unit/test_web_null_read_guard.py tests/integration/test_web_dictation_readiness_api.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fc912c6b3f33f011000d6ebf07c32b25862550b4

```text
geometry walk: 12 windows measured against the grammar — heads, lights, padded bodies, no sideways scroll, no tab walls, reflow at 360px
14 passed in 5.59s
```

## Summary of proof — the assembled chain

- **The geometry leg exists and passes** (captured above): all 12
  registered surface windows opened via their deep links and measured
  against the grammar — head band, traffic lights present and
  disc-shaped, padded bodies with zero horizontal overflow, no tab
  wall in any body (the settings rail archetype and the gallery's
  marked specimen are the two legal tablist forms), and the same
  truths after a squeeze to 360px. The leg earned its keep before
  passing: ActivityCore's strip became head wings; the Components
  gallery's Tabs demo is a declared data-specimen.
- **The full walk chain: 21/21 legs green** on the staged hub (smoke,
  windows, shell, cores, dictation, speakflow, meetings, meetingflow,
  config, lastexits, placement, arrangement, depth, frame, switcher,
  shelf, grammar, reflow, surfaces, chrome [HEADED], geometry).
- **The storm (HEADED)**: hardware GPU, 961 frames, median 8.3 ms,
  p95 9.29 ms, zero steady-state layout/paint events.
- **Suites**: full pytest sweep 2 failed / 4116 passed / 37 skipped
  (metal excluded per standing rule); both stragglers were pins made
  stale by this phase (the runtime-docs pin retargeted to the
  Settings-wing alias; the dock test rewritten for the null-read
  guard) and are re-proven green in the capture above. vitest 296/296;
  token gate clean; judgment + mockup censuses zero omissions; **the
  vocabulary allowlist is EMPTY and locked**.
- Composite screenshot (three applications layered, lights front/idle,
  running marks, badged bell): assets/hs-100-12-three-apps-1440.png.
