# Evidence - HS-152-03

- **Story:** HS-152-03 - The People fence (sensitive results, multi-pass redaction)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T04:55:39Z

- **Command:** `uv run pytest -q -n 4 tests/unit/test_thread_people_fence.py tests/unit/test_thread_tool_loop.py tests/unit/test_thread_service.py tests/unit/test_thread_tool_gate.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_one_path_census.py tests/unit/test_inference_runner_stream.py tests/unit/test_inference_runner.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d5464271c2552ba058eb9b3a90d4db4bd5bbb6d

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 41%]
........................................................................ [ 83%]
.............................                                            [100%]
173 passed in 56.58s
```

### Captured run — 2026-08-30T04:56:43Z

- **Command:** `uv run python pm/roadmap/holdspeak/phase-152-the-hands/assets/story-03-hub-leg.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0d5464271c2552ba058eb9b3a90d4db4bd5bbb6d

```text

== LEG A: local turn, people.* through the hub route ==
  PASS POST /api/threads -> 201
  PASS POST /turns -> 201
  PASS assistant row carries one tool_call part (the hub wired dispatch)
  PASS one tool-role message persisted
  PASS people.* result part is sensitive=1
  PASS local egress (local)
  PASS tool palette reached the engine (26 tools)
  PASS two passes (2)
  PASS pass 2 carried People bytes verbatim on local egress

== LEG B: profile_override -> cloud; later turn withholds ==
  PASS PATCH profile_override -> 200
  PASS POST /turns (cloud) -> 201
  PASS override honored at admission: egress=cloud
  PASS cloud payload carries [people content withheld]
  PASS cloud payload carries NO People bytes
  PASS no sentinel key leaks

== FINDINGS ==
mode=DRY payloads=pm/roadmap/holdspeak/phase-152-the-hands/assets/story-03-hub-payloads failures=0
```
