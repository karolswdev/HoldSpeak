# Evidence - HS-134-08

- **Story:** HS-134-08 - The routing profile stands alone
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T22:38:49Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_intel_profile_resolution.py tests/unit/test_one_dial.py tests/unit/test_meeting_placement_policy.py tests/unit/test_config_intent_router.py tests/unit/test_config.py tests/unit/test_doctor_command.py tests/unit/test_meeting_plugins.py tests/unit/test_web_runtime.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_plugin_provider_admission.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d6cee86fb90465016fd6a611b38eb2dde7aabb0a

```text
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
....................................................................     [100%]
356 passed in 36.00s
```
