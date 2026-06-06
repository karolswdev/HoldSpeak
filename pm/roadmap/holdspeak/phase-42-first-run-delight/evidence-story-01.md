# Evidence — HS-42-01 — Setup-state contract + `first_run` milestone

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

The backend spine every first-run surface reads — one composed
`GET /api/setup/status` snapshot plus a durable first-success milestone — built
as an **adapter** over the existing structured sources, never a second doctor.

### The composition — `holdspeak/setup_status.py`

`build_setup_status(*, database, config, env, skip_network=True)` returns:

```json
{
  "overall": "ready|needs_attention|blocked",
  "first_run": true,
  "primary_action": {"id": "...", "label": "...", "route": "/setup#..."},
  "sections": [{"id","label","status","detail","fix"}, ...],
  "trust": {"web_bind","auth_token_set","transcript_egress","egress_detail",
            "configured_endpoints","actuators_enabled","webhook_allowed_hosts"},
  "presence": {"enabled","available","tier","os","wayland"}
}
```

- **Adapter, not a re-implementation.** `sections` are **1:1** with
  `collect_doctor_checks()` (22 checks), so no check — and crucially no `FAIL` —
  can be filtered out of the setup view. `trust` reuses `intel_egress_posture()` +
  the config trust fields; `presence` reuses `detect_presence_platform()` +
  `desktop_presence_enabled()`.
- **`overall`** = blocked on any `FAIL`, else needs_attention on any `WARN`, else
  ready. **`primary_action`** = the single highest-severity unmet check (FAIL
  before WARN), or — when ready + first-run — the first-dictation test itself.
- **Cheap by construction.** `skip_network=True` is passed to
  `collect_doctor_checks`, so the cloud preflight returns a neutral "not run"
  check instead of a 4s HTTP probe; no check loads a large model (the runtime
  checks inspect paths/imports only). Doctor gained a `skip_network` param
  (`_check_meeting_intel_cloud_preflight(..., skip_network=...)`); the CLI
  `holdspeak doctor` keeps the full live preflight.

### The `first_run` milestone — `holdspeak/db/milestones.py`

`MilestoneRepository` (`db.milestones`) over a new `milestones(key, achieved_at)`
table: `mark` (idempotent), `is_set`, `achieved_at`, `clear`. `first_run` is true
while `FIRST_DICTATION_SUCCESS` is absent, so it **survives a restart** (HS-42-04
sets it on a verified first dictation). Canonical schema snapshot regenerated
(the trap) and proven by `test_fresh_schema_matches_canonical_snapshot`.

### The route — `holdspeak/web/routes/setup.py`

`build_setup_router(ctx)` exposes `GET /api/setup/status` (reads the
`get_database()` singleton defensively, never blocks on the DB), registered in
`web_server._create_app` alongside the other routers.

## Tests run

```
uv run pytest -q tests/unit/test_setup_status.py \
  tests/unit/test_setup_status_doctor_drift.py \
  tests/integration/test_web_setup_status_api.py
→ 22 passed

uv run pytest -q tests/unit/test_doctor_command.py tests/unit/test_db.py
→ 93 passed   (incl. the regenerated canonical-schema snapshot)
```

- `test_setup_status.py` (19): overall derivation, single primary action, the
  trust/presence blocks (local-only default + cloud/actuator variants + macOS/
  Wayland tiers), the milestone set→persist→restart, and the
  **cheapness** guarantee (`skip_network=True` passed by default).
- `test_setup_status_doctor_drift.py` (3): the **no-duplicate-doctor invariant** —
  every real doctor check becomes a section 1:1, a `FAIL` always surfaces as a
  blocking section + primary action, and `skip_network` returns the cloud
  preflight as a neutral "not run".
- `test_web_setup_status_api.py` (3): the route shape for ready + blocked, and
  `first_run` flipping false after the milestone.

Full suite: see HS-42-01 commit message / the closeout.

## Acceptance criteria

- [x] `GET /api/setup/status` returns the documented shape; integration-tested for
      ready + blocked.
- [x] Adapter over `collect_doctor_checks()` — a test asserts every doctor `FAIL`
      maps to a setup section (1:1); check IDs are stable slugs.
- [x] `first_run` flips true→false once the milestone is set and **survives a
      restart** (DB-backed); proven.
- [x] `primary_action` points at the single highest-severity next step with a
      `route` deep link.
- [x] The status read is cheap (no large-model load / no default network call) —
      `skip_network=True` asserted.
- [x] Default suite green; no config ⇒ `first_run: true` without error.
