# HS-74-01 — Run results persist as artifacts (hub)

- **Status:** done
- **Severity:** HIGH
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

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

## Done

Shipped — as a REAL schema migration, not the planned empty-string loosen:
the artifacts table's NOT NULL + FK made run-born rows impossible without
v6, so v6 follows the repo's own v5 precedent verbatim (owner-typed:
nullable meeting_id + origin IN ('meeting','run'); the standard rebuild
with ids kept; Phase-50 backup-then-apply proven by test). record_artifact
takes empty meeting_id → NULL + origin='run'; list_run_artifacts is the
sync pull's second lane; the wire keeps meeting_id a plain string ("" for
run-born) so the iPad's non-optional decode is unmoved, and the merge path
accepts pushed run-born artifacts. All three run routes persist via one
helper (workflow on both paths) and respond with artifact_id; persistence
failure never eats a successful run. tests/unit/test_run_artifacts.py 5/5
(incl. the v5→v6 facsimile upgrade with the pre-migration backup
asserted); the schema snapshot + sync stub guards fired and were updated
in-commit. See [evidence-story-01.md](./evidence-story-01.md).
