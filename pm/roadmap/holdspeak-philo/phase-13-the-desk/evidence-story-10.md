# Evidence - PHILO-13-10

- **Story:** PHILO-13-10 - B5 — The update writes the week
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T17:46:43Z

- **Command:** `uv run pytest -q tests/unit/test_philo13_b5_week.py tests/unit/test_update_drafter.py tests/integration/test_update_routes.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
........................................................................ [ 29%]
........................................................................ [ 59%]
........................................................................ [ 89%]
..........................                                               [100%]
242 passed in 18.64s
```

### Captured run — 2026-10-03T17:47:16Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.update.linked_week --brain astra --viewport 1440 --engine replayed --out .tmp/close-b5/week-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50213 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-pkk5dgw8/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/close-b5/week-1440/20261003T174716Z-case.p13.update.linked_week-astra-1440/before.png', '.tmp/close-b5/week-1440/20261003T174716Z-case.p13.update.linked_week-astra-1440/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/projects/proj-a5dfe5172052/updates/draft answered 200, wanted 200 (body sha256 b34d005b9607); response body matches its declared fields | text_contains: 'The ledger cutover is ready for the controlled migration.' in observe_at text | text_contains: 'Decision: Use the controlled migration window' in observe_at text | text_contains: 'Action: Confirm the migration window' in observe_at text | text_contains: 'owner Avery' in observe_at text | text_contains: 'Action: Send the rollback checklist' in observe_at text | text_contains: 'owner Morgan' in observe_at text | text_contains: 'All sources consulted successfully.' in observe_at text | protocol_reads: GET /api/projects/proj-a5dfe5172052/updates answered 200 with 1 row(s) {'generator': 'deterministic', 'lifecycle': 'draft'}
```

### Captured run — 2026-10-03T17:48:04Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.update.linked_week --brain astra --viewport 393 --engine replayed --out .tmp/close-b5/week-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50325 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-166ywcjk/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/close-b5/week-393/20261003T174804Z-case.p13.update.linked_week-astra-393/before.png', '.tmp/close-b5/week-393/20261003T174804Z-case.p13.update.linked_week-astra-393/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/projects/proj-690e5197f4ce/updates/draft answered 200, wanted 200 (body sha256 7109a3be490e); response body matches its declared fields | text_contains: 'The ledger cutover is ready for the controlled migration.' in observe_at text | text_contains: 'Decision: Use the controlled migration window' in observe_at text | text_contains: 'Action: Confirm the migration window' in observe_at text | text_contains: 'owner Avery' in observe_at text | text_contains: 'Action: Send the rollback checklist' in observe_at text | text_contains: 'owner Morgan' in observe_at text | text_contains: 'All sources consulted successfully.' in observe_at text | protocol_reads: GET /api/projects/proj-690e5197f4ce/updates answered 200 with 1 row(s) {'generator': 'deterministic', 'lifecycle': 'draft'}
```

### Captured run — 2026-10-03T17:49:00Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.update.linked_week.op --brain astra --viewport 1440 --engine replayed --out .tmp/close-b5/week-op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
PASS: live
BRAIN: astra
SOURCE: 23a6c137f896e230e44e8e4e31f1f508b60fa05f dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-CXOlJz0z.js'] hub=http://127.0.0.1:50492 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-08v9wz3u/.local/share/holdspeak/holdspeak.db engine=replayed
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/close-b5/week-op/20261003T174900Z-case.p13.update.linked_week.op-astra-1440/before.png', '.tmp/close-b5/week-op/20261003T174900Z-case.p13.update.linked_week.op-astra-1440/after.png']
NOTE: placeholder(s) ['update_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 8 facts hold: the trigger update.id holds; the trigger update.generator holds; the trigger update.lifecycle holds; the trigger update.body_md holds; the trigger update.claims_json holds; observe_at updates holds; observe_at updates.0.body_md holds; observe_at updates.0.claims_json holds
```

## Closure reading

The scope, real-producer trace, current-main revision, reviewed 1440/393 shots,
source claims, no-engine boundary and remaining limits are recorded in
[close-10-astra.md](close-10-astra.md). The copied raw observations and shots
are under [assets/story-10-close](assets/story-10-close/manifest.json). The
commands above wrote their original run directories under `.tmp/close-b5`;
those raw observations were copied without edits. Muad'Dib's existing
[PASS on #739](checks/story-10-muaddib-record.md) checks the built implementation.

### Captured run — 2026-10-03T17:55:10Z

- **Command:** `uv run python .tmp/close-b5/navigation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8230cc4075acc108bba14d996e1a217949b9735d

```text
COMMAND: python -m unittest discover -s tests/unit -p test_docs_navigation.py
.........
----------------------------------------------------------------------
Ran 9 tests in 0.003s

OK
EXIT: 0
COMMAND: python scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
EXIT: 0
COMMAND: python scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
EXIT: 0
COMMAND: python scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
EXIT: 0
COMMAND: python scripts/philo_api_reference.py --check
API reference checked
EXIT: 0
COMMAND: python scripts/philo_boundary_census.py --check
Boundary candidate census checked
EXIT: 0
COMMAND: python scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
EXIT: 0
COMMAND: python scripts/philo_config_reference.py --check
Configuration declaration reference is current
EXIT: 0
COMMAND: python scripts/philo_graph_reference.py --check
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
EXIT: 0
COMMAND: python scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 151 record(s)
Architecture metadata validation passed.
EXIT: 0
COMMAND: python scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
EXIT: 0
COMMAND: python scripts/check_doc_coverage.py --check
Documentation coverage checked.
EXIT: 0
All 12 Documentation Navigation commands passed.
```
