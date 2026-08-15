# Evidence - HS-132-03

- **Story:** HS-132-03 - The desk hears intelligence live
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:48:15Z

- **Command:** `env HOME=/tmp/hs132-03-home uv run pytest -q tests/unit/test_realtime_frame_registry.py tests/unit/test_workbench_run_frames.py tests/unit/test_workbench_runner_migration.py tests/unit/test_workbench_conductor.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a1d1de0e685149c57bd983645b57437bdc6d1401

```text
..................................                                       [100%]
34 passed in 7.65s
```

## Orchestrator notes

- Web proof (not in the captured run): LiveCore (7) + queueHud (5) +
  workbenchFrames (3) vitest green under the orchestrator's own run.
- Guard baseline proven red-first: before the fix the registry guard
  reported 6 failed, naming exactly the audit's orphans (9 emitted-no-
  consumer, 7 consumed-no-emitter); after, it passes with ONE allowlisted
  row (wake_armed, dormant desktop wake leg) and the allowlist is itself
  guarded against going stale.
- intent_controls_updated and device_health received honest consumers in
  LiveCore rather than allowlist entries. Article XI.5 held: tokens are
  component state only, asserted by test.
- Shared-file etiquette: WorkbenchWindow.tsx (frame subscriptions) and
  AmbientLayer.tsx (queue HUD) edits ride in the HS-132-07 / HS-132-08
  commits respectively, since those workers hold the same files; the
  guard and vitest prove the working-tree state regardless.
- Ledger (recorded, unfixed): MissionControlConveyor.tsx:583 listens on a
  DOM CustomEvent("hs-broadcast") that nothing dispatches — a dead DOM-bus
  seam invisible to the WS-frame guard; later slice.
