# HS-74-01 — Run results persist as artifacts (hub)

- **Status:** todo
- **Severity:** HIGH
- **Depends on:** —

## What

The three run routes (`POST /api/agents/{id}/run`, `/api/chains/{id}/run`,
`/api/workflows/{id}/run`) persist their output as a REAL artifact in the
one plugin-artifact store, so it syncs, lands on the desk, and enters the
iPad's artifact review — instead of evaporating with the HTTP response.

## How

- `record_artifact` gains run-born tolerance: `meeting_id` may be empty
  (the anchor is the capability lineage instead). The sync value already
  serializes `meeting_id` as a plain string — an empty string rides the
  existing shape; NOTHING else about the serialization changes (the
  Phase-72 contract locks stay green).
- Each run route, on success: `record_artifact(artifact_id=new,
  meeting_id="", artifact_type="run_output", title="<name> — <input
  head>", body_markdown=output, status="draft",
  plugin_id="<agent|chain|workflow>_run", sources=[{source_type: <kind>,
  source_ref: <id>}])` and the response gains `artifact_id`.
- Meeting-scoped read paths are untouched (a run-born artifact simply has
  no meeting to appear under); `/api/sync/pull` picks it up from the same
  store.

## Test plan

- Unit: `record_artifact` accepts empty meeting_id; still rejects empty
  artifact_id; meeting-scoped list unaffected.
- Route: a run (stub engine) persists the artifact with the capability
  source; the response carries `artifact_id`; `/api/sync/pull` includes
  it with the unchanged value shape.
- The serialization-contract suite stays green untouched.
