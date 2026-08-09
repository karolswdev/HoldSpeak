# Evidence - HS-130-02

- **Story:** HS-130-02 - Collision-free secret slots — the exfiltration path closes
- **Status:** done
- **Date:** 2026-08-09

## Proof

### Captured run — 2026-08-09T07:04:12Z

- **Command:** `bash -lc HOME='/Users/karol/.claude/jobs/b0c53811/tmp/iso-ev02' XDG_DATA_HOME='/Users/karol/.claude/jobs/b0c53811/tmp/iso-ev02/.local/share' .venv/bin/python -m pytest -q tests/unit/test_secret_slots.py tests/unit/test_doctor_command.py::test_cloud_preflight_passes_when_model_available tests/unit/test_doctor_command.py::test_cloud_preflight_warns_on_dns_failure tests/unit/test_doctor_command.py::test_cloud_preflight_warns_when_model_missing`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 33f6ead6b07e03ec48f8d36d6446a8995e5f4d97

```text
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                                              [100%][0m
[32m[32m[1m11 passed[0m[32m in 0.43s[0m[0m
```
