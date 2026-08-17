# Evidence - HS-134-02

- **Story:** HS-134-02 - One target spec, one API
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T22:15:29Z

- **Command:** `HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ZwUtReWldV uv run pytest -q tests/unit/test_web_routes_primitives.py tests/unit/test_inference_targets.py tests/unit/test_one_dial.py tests/unit/test_mesh_liveness_surfaces.py tests/integration/test_primitive_framework_sync.py tests/uat/test_trust_dictation.py --tb=short`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** 891ff49749d7b3e213973998d4ed8d861c438f26

```text
(command could not be executed: [Errno 2] No such file or directory: 'HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ZwUtReWldV')
```

### Captured run — 2026-08-16T22:15:37Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_web_routes_primitives.py tests/unit/test_inference_targets.py tests/unit/test_one_dial.py tests/unit/test_mesh_liveness_surfaces.py tests/integration/test_primitive_framework_sync.py tests/uat/test_trust_dictation.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 891ff49749d7b3e213973998d4ed8d861c438f26

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 17.01s
```
