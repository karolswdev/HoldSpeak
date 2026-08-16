# Evidence - HS-132-07

- **Story:** HS-132-07 - Workbench edits hold
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T23:02:12Z

- **Command:** `env HOME=/tmp/hs132-07-home uv run pytest -q tests/integration/test_web_meeting_rename_api.py tests/integration/test_live_action_item_triage.py tests/integration/test_meeting_stop_and_conflicts.py tests/unit/test_api_surface.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4b12b7bf44811e050dbb7b72f0c0707460db7e16

```text
..........................                                               [100%]
26 passed in 6.17s
```

## Orchestrator notes

- Web proof (not in the captured run): workbenchEditing (7) +
  renameHonesty (5) + workbenchFrames (3) vitest green under the
  orchestrator; the worker's full desk sweep ran 88 files / 675 green;
  tsc clean; architecture guard green.
- The audit's keystroke probe is a kept regression test: two rapid
  changes hold "ab", zero mid-burst PUTs, one debounced PUT per pause.
- Per-kind rename table recorded in the worker report: chain/workbench
  map entries added (routes existed), meetings gained PUT
  /api/meetings/{id} (archive-only, never the live session), and seven
  kinds honestly hide Rename with the reason shown in place.
- Riders in this commit, documented: (1) docs/api-surface.json + docs/
  API_SURFACE.md regenerated under an isolated HOME covering the four
  routes this phase added (brief shelf x2, cadence reply, meeting
  rename) — the generator crashes against the owner's real drifted DB
  when run with a real HOME (real DB verified untouched, mtime + absent
  shelf table); (2) the orchestrator repaired HS-132-06's two test files
  to a body-scoped query helper, re-greening the architecture guard.
- This commit also carries HS-132-03's WorkbenchWindow frame-subscription
  edits per shared-file etiquette (documented in 03's evidence).
