# Evidence - PHILO-13-01

- **Story:** PHILO-13-01 - B0 — Walk what was not walked
- **Status:** in-progress (incremental capture; #747 merge and final main rerun pending)
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T17:48:26Z

- **Command:** `uv run pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
........................................................................ [ 41%]
........................................................................ [ 83%]
............................                                             [100%]
172 passed in 8.58s
```

### Captured run — 2026-10-03T17:49:37Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 1440 --engine none --out .tmp/close-b0/zone-1440`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50616 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-njbpxgwk/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: fail terminal=None
EVIDENCE: ['.tmp/close-b0/zone-1440/20261003T174937Z-case.p13.directory.zone-astra-1440/blocked.png']
NOTE: TRIGGER lifecycle failed: ui step click_role on 'Open' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
Call log:
  - waiting for get_by_role("menuitem", name="Open", exact=True).first
    - locator resolved to <button type="button" role="menuitem" aria-disabled=
```

### Captured run — 2026-10-03T17:50:44Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 393 --engine none --out .tmp/close-b0/zone-393`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50699 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-xz69j1sh/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/close-b0/zone-393/20261003T175044Z-case.p13.directory.zone-astra-393/blocked.png']
NOTE: BLOCKED: ui step click on '.desk-tools-launch' failed: TimeoutError: Locator.tap: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-tools-launch").first
    - locator resolved to <button type="button" title="Search ⌘K" aria-expanded="false" aria-contro
```

### Captured run — 2026-10-03T17:51:54Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 1440 --engine none --out .tmp/close-b0/chain-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50785 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-pr5q41wq/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/close-b0/chain-1440/20261003T175155Z-case.p13.chain.pullout-astra-1440/before.png', '.tmp/close-b0/chain-1440/20261003T175155Z-case.p13.chain.pullout-astra-1440/after.png']
NOTE: predicate: 'No steps' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1022, 'y': 64, 'w': 400, 'h': 553}
```

### Captured run — 2026-10-03T17:54:39Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 393 --engine none --out .tmp/close-b0/chain-393`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50955 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kafueapb/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: fail terminal=None
EVIDENCE: ['.tmp/close-b0/chain-393/20261003T175439Z-case.p13.chain.pullout-astra-393/blocked.png']
NOTE: TRIGGER lifecycle failed: ui step click on '.desk-tools-launch' failed: TimeoutError: Locator.tap: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-tools-launch").first
    - locator resolved to <button type="button" title="Search ⌘K" aria-expanded="false" aria-contro
```

### Captured run — 2026-10-03T17:56:03Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.coder.pullout --brain astra --viewport 1440 --engine none --out .tmp/close-b0/coder-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:51040 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3ir76l29/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/close-b0/coder-1440/20261003T175603Z-case.p13.coder.pullout-astra-1440/before.png', '.tmp/close-b0/coder-1440/20261003T175603Z-case.p13.coder.pullout-astra-1440/after.png']
NOTE: predicate: 'Should I run the full suite now?' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1022, 'y': 64, 'w': 400, 'h': 274}
```

### Captured run — 2026-10-03T17:57:14Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.coder.pullout --brain astra --viewport 393 --engine none --out .tmp/close-b0/coder-393`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** d170f272a7dc30f2287e921e231910834032f707

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:51143 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-it4dx3lc/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: fail terminal=None
EVIDENCE: ['.tmp/close-b0/coder-393/20261003T175714Z-case.p13.coder.pullout-astra-393/blocked.png']
NOTE: TRIGGER lifecycle failed: ui step click on '.desk-tools-launch' failed: TimeoutError: Locator.tap: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-tools-launch").first
    - locator resolved to <button type="button" title="Search ⌘K" aria-expanded="false" aria-contro
```
