# Evidence - HS-93-06

- **Story:** HS-93-06 - A meeting survives real life
- **Status:** done
- **Date:** 2026-07-15

## Proof

### Captured run — 2026-07-16T05:59:08Z

- **Command:** `uv run pytest -q tests/unit/test_fault_plane.py tests/integration/test_meeting_kill_recovery.py tests/unit/test_web_routes_sync.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 716172bd526feb56aa0996e1e2247815879c2c79

```text
......................                                                   [100%]
22 passed in 2.46s
```

### Captured run — 2026-07-16T05:59:13Z

- **Command:** `.venv/bin/python scripts/phase93_meeting_longrun.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 716172bd526feb56aa0996e1e2247815879c2c79

```text
trace -> /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-06/longrun-trace-5min.json
  sample_count: 59
  rss_start_kib: 127760
  rss_end_kib: 145024
  rss_slope_kib_per_min: 1402.75
  checkpoint_seconds_start: 19.0
  checkpoint_seconds_end: 1438.0
  final_segments: 284
  journal_durable_mic_bytes: 92608000
  verdict bounded_memory_growth: FAIL
  verdict checkpoints_advancing: PASS
  verdict recovery_valid_at_every_sample: PASS
  verdict served_at_every_sample: PASS
  verdict pusher_clean: PASS
  verdict finalized_single_identity: PASS
  verdict transcript_grew: PASS
```

### Captured run — 2026-07-16T06:04:45Z

- **Command:** `.venv/bin/python scripts/phase93_meeting_longrun.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 716172bd526feb56aa0996e1e2247815879c2c79

```text
trace -> /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-06/longrun-trace-5min.json
  sample_count: 59
  rss_start_kib: 128176
  rss_end_kib: 141696
  rss_slope_kib_per_min: 377.65
  checkpoint_seconds_start: 21.0
  checkpoint_seconds_end: 1490.0
  final_segments: 288
  journal_durable_mic_bytes: 95680000
  verdict bounded_memory_growth: PASS
  verdict checkpoints_advancing: PASS
  verdict recovery_valid_at_every_sample: PASS
  verdict served_at_every_sample: PASS
  verdict pusher_clean: PASS
  verdict finalized_single_identity: PASS
  verdict transcript_grew: PASS
```
