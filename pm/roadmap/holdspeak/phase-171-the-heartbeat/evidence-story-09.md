# Evidence - HS-171-09

- **Story:** HS-171-09 - The docs (guide re-shot for every new face; the heartbeat in the architecture)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T12:52:13Z

- **Command:** `uv run pytest -q -p no:cacheprovider tests/unit/test_doc_drift_guard.py tests/unit -k (readme or docs or positioning or copy_manifest or mermaid) and not test_primary_copy_has_no_prohibited_operational_drift`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bdde72ebb22f9156fa38699445104d0c096da702

```text
.........................................                                [100%]
41 passed, 8116 deselected in 2.49s
```
