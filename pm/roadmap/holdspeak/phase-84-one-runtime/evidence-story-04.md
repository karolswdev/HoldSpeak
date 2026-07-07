# Evidence — HS-84-04 — The honest doctor + one egress derivation

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-84-04-honest-doctor-one-egress` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/intel/providers.py` — `endpoint_host` (the bare-host rule,
  moved here from `ask.py`) and `endpoint_egress(cloud=, base_url=, label=)`
  — the ONE `{scope, host?, label?}` badge constructor.
- `holdspeak/web/routes/primitives/ask.py` — `_host_of` becomes an alias of
  `endpoint_host` (import surface preserved); the inline 3-branch egress
  block extracted as `_run_egress(ctx, prof, intel)` — which now reports the
  EFFECTIVE default-cloud endpoint (`effective_intel_cloud`), fixing the
  stale-badge find below.
- `holdspeak/web/routes/primitives/recipes.py` — the mirrored inline egress
  block replaced by the shared `_run_egress` import.
- `holdspeak/web/routes/cadence.py`, `holdspeak/cadence/audit.py` — their
  local-only dicts built by `endpoint_egress` (byte-equal shapes).
- `holdspeak/commands/doctor.py` — the new **"Runtime profiles"** check
  (registered in `collect_doctor_checks`); `_check_meeting_intel_egress`
  names the adopted profile's host (or the fallback reason);
  `_check_dictation_runtime` reports "runs on profile …" when adopted and
  carries the dangling note + re-pick fix on every legacy branch.
- `holdspeak/setup_status.py` — the trust block's meeting-intel endpoint is
  the EFFECTIVE base URL, matching the HS-84-02 dictation fix.
- `tests/unit/test_doctor_runtime_profiles.py` — new, 13 tests.

## Verification artifacts

- `uv run pytest -q tests/unit/test_doctor_runtime_profiles.py` →
  **13 passed in 0.50s**.
- `uv run pytest -q tests/ -k doctor` → **62 passed, 2 skipped** (the
  setup-status drift guard among them — the new check auto-surfaces as a
  section), unmodified.
- Route/status neighbors (`test_web_routes_ask.py`,
  `test_web_routes_recipe_chat.py`, `test_web_routes_primitives.py`,
  `test_setup_status.py`) → **70 passed**, unmodified — the wire shapes the
  one constructor emits are byte-equal to the old inline dicts.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3250 passed, 37 skipped, 2 warnings in 250.88s** (standing env-gated
  skips).

## Acceptance criteria — re-checked

- [x] One helper; ask's badge, cadence's local dict, and the doctor posture
  all call it — `endpoint_egress` called from `_run_egress` (ask + recipes),
  `cadence._LOCAL_EGRESS`, `audit.export_audit`, and the doctor checks read
  the same `EffectiveEndpoint` resolution; equality test-pinned
  (`test_the_scattered_egress_sites_use_the_one_constructor`,
  `test_endpoint_egress_shapes`).
- [x] Doctor names the resolved profile per pipeline, test-pinned for:
  unset (hub default), profile-cloud (by name + host), dangling id (WARN +
  reason + re-pick fix), requires_key-without-key (WARN naming
  `HOLDSPEAK_PROFILE_<ID>_KEY`), nothing enabled (quiet PASS) — the six
  `_check_runtime_profiles` tests + the two per-pipeline check tests.
- [x] The setup-status drift guard still holds — the new check is registered
  in `collect_doctor_checks`, so the 1:1 check→section invariant covers it;
  `tests/ -k doctor` (which includes the drift guard) passed unmodified.
- [x] Wire shapes of existing badge consumers unchanged — the 70
  route/status neighbor tests passed verbatim.

## Deviations from plan

The "one helper" split into two honest layers (recorded in the story
Notes): `endpoint_egress` as the shape constructor in `providers.py`, and
`_run_egress` as the shared run-badge derivation in `ask.py`.
`intel_egress_posture` was kept (it states provider-level *intent*, a
different question) and its doctor consumer now appends the resolved
destination. Beyond the plan, the story fixed a real staleness bug it
uncovered: the default-cloud run badge named the raw legacy host even when
the engine ran on the assigned intel profile (an HS-84-01 side effect) —
now derived from `effective_intel_cloud` and pinned by
`test_run_egress_default_cloud_reports_the_effective_endpoint`.

## Follow-ups

- HS-84-05's live walk should read `holdspeak doctor` on the real hub and
  capture the "Runtime profiles" line naming the `.43` profile for both
  pipelines (already in the walk's plan).
