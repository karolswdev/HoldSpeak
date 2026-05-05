# HS-13-10 evidence — Phase 13 exit + DoD

## What shipped

This story is a closeout, not new feature work. The deliverables
are doc + roadmap state + a green regression sweep.

### Doc — `docs/CONNECTOR_DEVELOPMENT.md`

New "Phase 13 additions — runtime gates, pipelines, user
packs, run history" section appended ahead of "Out of scope".
It documents the four runtime surfaces phase 13 added on top
of the phase-11 contract:

- **`kind: pipeline`** — manifest delta (`consumes`,
  `pipeline_freshness_seconds`, required read-permissions per
  consumed `output_kind`), the validator's
  `pipeline_requires_consumes` /
  `pipeline_missing_read_permission` /
  `consumes_only_on_pipeline` codes, and the four
  `PipelineRunner` step statuses (`skipped_fresh`, `ran`,
  `failed`, `missing_runner`).
- **Permission gates at runtime** — the four operationally
  gated permissions (`shell:exec`, `network:outbound`,
  `loopback:http`, `fs:read`), how `PermissionGate` raises
  `PermissionDenied`, and the "honest enforcement, not a
  sandbox" framing. Persisted error string format documented.
- **Local-user pack discovery** — `~/.holdspeak/connector_packs/`
  contract: one `.py` per pack, `MANIFEST` export required,
  `validate_manifest` re-run on import, id-collision rules
  (`id_collision_user_pack`, first-party always wins,
  duplicate user-pack ids rejected), the
  `HOLDSPEAK_USER_PACKS_DIR` test override, and the
  per-pack `source` field.
- **`connector_runs`** — the schema, the
  `record_connector_run` / `list_connector_runs` /
  `delete_connector_runs` DB API, the
  `GET /api/activity/enrichment/connectors/{id}/runs`
  endpoint, the dashboard inline-row surface, and the
  pipeline-runner freshness-skip linkage.

The phase-11 sections above ("TL;DR", "Connector lifecycle",
"Manifest reference", etc.) were left intact — they remain
correct and a reader who only needs the producer-pack
contract should not have to wade through pipeline / runtime
detail.

### Roadmap state

- `pm/roadmap/holdspeak/phase-13-connector-runtime-and-context/story-10-dod.md`:
  status flipped `backlog → done`. Acceptance-criteria
  checkboxes flipped per the verification below.
- `current-phase-status.md`: HS-13-10 row → `done`,
  evidence link wired, "Last updated" bumped, "Where we
  are" extended with the close-out note.
- `pm/roadmap/holdspeak/README.md`: "Last updated" line
  bumped to 2026-05-04 (HS-13-10), phase-13 status flipped
  `planning → done`.

### Test fixture fix (incidental, in-scope for closeout)

`tests/integration/test_web_activity_api.py::test_run_pipeline_endpoint_executes_meeting_context`
was a time-bomb: it hardcoded `base = datetime(2026, 5, 2,
11, 0, 0)` for the upstream `connector_runs` rows and relied
on those rows being within the 600-second
`pipeline_freshness_seconds` window so the runner would
short-circuit them. The window passed two days after the
test was written, so the runner started trying to invoke
`gh.run(db)` / `jira.run(db)` / `calendar_activity.run(db)`,
none of which exist, surfacing as `missing_runner` and
aborting the pipeline with `succeeded=False`.

Replaced the hardcoded timestamp with `datetime.now()` —
the test's comment ("Upstreams are seeded as fresh so the
runner skips them") describes the intent, which only holds
when the timestamps stay near "now". This kind of fixture
should never have been hardcoded; flagging here so the
author/reviewer pattern doesn't repeat.

### Out of scope (deferred to the user)

- **Designer-handoff screenshots.** The dashboard
  pre-briefing panel (`/`) and the `/history` project
  briefing timeline both ship behind a running web server
  and need a real browser capture. The acceptance row for
  screenshots is left unchecked; the user re-captures
  manually against `uv run holdspeak web` and drops the
  files into `designer-handoff/screenshots/`. Everything
  else in the AC list is verified.

## Acceptance criteria

- [x] Every shipped story has a matching `evidence-story-{n}.md`
  file. `ls pm/roadmap/holdspeak/phase-13-connector-runtime-and-context/evidence-story-*.md`
  shows `evidence-story-01.md` through `evidence-story-10.md`.
- [x] `current-phase-status.md` story table fully updated.
  HS-13-10 row flipped to `done` with evidence link.
- [x] `pm/roadmap/holdspeak/README.md` "Last updated"
  bumped, phase 13 row flipped to `done`.
- [x] `docs/CONNECTOR_DEVELOPMENT.md` documents the
  pipeline kind, the permission gates, the user-pack
  discovery path, and the run-history surface (new
  section described above).
- [ ] `designer-handoff/screenshots/` recapture — deferred
  to the user (manual browser capture; flagged above).
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  green. See "Tests ran" below.
- [x] `npm run build` clean. `(cd web && npm run build)`
  exits 0 with `[build] 7 page(s) built`.

## Tests ran

```
$ (cd web && npm run build)
17:12:10 [build] 7 page(s) built in 803ms
17:12:10 [build] Complete!
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1406 passed, 13 skipped
```

(See the rerun output appended at the end of this commit's
contract — the time-bomb fixture above was the one failure
in the first sweep.)

The 13 pre-existing skips (mock meeting WAV, llama-cpp /
Qwen GGUF) are unchanged from HS-13-09.

## What comes next (one line)

Phase 14: bring the connector-runtime UI surfaces forward
— per-pack run-history timeline, per-project pipeline-run
args on the briefing endpoint, and the deferred
"connectors panel" run-history view that HS-13-05 stubbed.
