# Evidence - HS-169-04

- **Story:** HS-169-04 - The wire for the four questions (needs-you items derived from real Watch entities; the read marker; the health inputs; the meeting Watch never offered until it evaluates; MCP twins)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-05T00:15:52Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.5RiQDG3Ucc uv run pytest -q tests/unit/test_hs169_wire.py tests/unit/test_project_setup_service.py tests/unit/test_github_templates.py tests/unit/test_project_room_read.py tests/unit/test_db.py::test_schema_snapshot_matches_canonical -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 4
- **Index-tree:** 28ebe56fa4c89282ef95fd807bcf6da2b4675ba6

```text
ERROR: not found: /Users/karol/dev/tools/HoldSpeak/tests/unit/test_db.py::test_schema_snapshot_matches_canonical
(no match in any of [<Module test_db.py>])


no tests ran in 3.86s
```

### Captured run — 2026-09-05T00:16:35Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7D5wg0uZup uv run pytest -q tests/unit/test_hs169_wire.py tests/unit/test_project_setup_service.py tests/unit/test_github_templates.py tests/unit/test_project_room_read.py tests/unit/test_db.py::test_fresh_schema_matches_canonical_snapshot -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 4
- **Index-tree:** 28ebe56fa4c89282ef95fd807bcf6da2b4675ba6

```text
ERROR: not found: /Users/karol/dev/tools/HoldSpeak/tests/unit/test_db.py::test_fresh_schema_matches_canonical_snapshot
(no match in any of [<Module test_db.py>])


no tests ran in 1.76s
```

### Captured run — 2026-09-05T00:24:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.VHIRC3wGKD uv run pytest -q tests/unit/test_hs169_wire.py tests/unit/test_project_setup_service.py tests/unit/test_github_templates.py tests/unit/test_project_room_read.py tests/unit/test_db.py -k not test_db or fresh_schema_matches_canonical_snapshot -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 28ebe56fa4c89282ef95fd807bcf6da2b4675ba6

```text
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
149 passed, 73 deselected in 30.97s
```

### Captured run — 2026-09-05T00:28:32Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.OTrkqd098l uv run pytest -q tests/unit/test_hs169_wire.py tests/unit/test_project_setup_service.py tests/unit/test_github_templates.py tests/unit/test_project_room_read.py tests/unit/test_db.py -k not test_db or fresh_schema_matches_canonical_snapshot -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 28ebe56fa4c89282ef95fd807bcf6da2b4675ba6

```text
........................................................................ [ 47%]
........................................................................ [ 94%]
........                                                                 [100%]
152 passed, 73 deselected in 33.79s
```
