# Evidence — HS-25-01 — Loud Cloud-Path Consent: No Silent Transcript Egress

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The premise was verified before any change and **corrected**: at the default
`provider="local"`, HoldSpeak is already structurally incapable of cloud egress
(`resolve_intel_provider` returns local-only; `MeetingIntel._ensure_runtime_loaded`
only builds the OpenAI client for non-local providers). The real gap was the
absence of a test locking that invariant. This story locks it, and makes the
egress posture visible.

## Files touched

- `tests/unit/test_intel_egress_invariant.py` — **new**; 8 cases. Locks the
  privacy invariant (local never constructs a cloud client, even with a key
  present; deferred queue same) and pins the consent boundary (`cloud`/`auto`
  still reach the cloud). Also covers the new `intel_egress_posture` helper.
- `holdspeak/intel.py` — added `intel_egress_posture(provider)` → `(can_transmit,
  description)`; single source of truth for the posture string.
- `holdspeak/commands/doctor.py` — added `_check_meeting_intel_egress` and
  registered it; prints a "Meeting intelligence egress" line (PASS for local,
  WARN — expected, not a failure — for cloud/auto).
- `holdspeak/web_runtime.py` — `_get_runtime_status()` now includes an
  `intel_egress` block (`enabled`, `provider`, `can_transmit_offmachine`,
  `egress`) so the web surface can render it.
- `tests/unit/test_web_runtime.py` — asserts the `intel_egress` block is wired
  into the runtime-status payload.
- `docs/MEETING_MODE_GUIDE.md` — new "Where your transcripts go (egress posture)"
  subsection.

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_intel_egress_invariant.py
8 passed

$ uv run pytest -q tests/unit/test_intel_egress_invariant.py \
    tests/unit/test_web_runtime.py tests/unit/test_doctor_command.py \
    tests/unit/test_intel_cloud.py
56 passed

$ uv run ruff check holdspeak/intel.py holdspeak/commands/doctor.py \
    holdspeak/web_runtime.py tests/unit/test_intel_egress_invariant.py \
    tests/unit/test_web_runtime.py
All checks passed!   (touched files; pre-existing CYCLE_ORDER warning in
                      web_runtime.py left untouched — out of scope, rule #5)

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
9 failed, 1844 passed, 13 skipped
```

## Pre-existing failures (NOT caused by this story)

The full-suite run shows 9 failures. Verified pre-existing by stashing this
story's changes (`git stash -u`) and re-running the same tests against `HEAD` —
they fail identically without this work:

- `test_web_dictation_readiness_api`, `test_web_dictation_settings_api`,
  `test_web_dry_run_api`, `test_web_project_kb_api`,
  `test_web_server::...device_health_surface`,
  `test_web_server::...companion_page...` — page-content assertions against a
  **stale committed `holdspeak/static/_built/`** (Astro bundle drift).
- `test_activity_history` (3) — depend on a Safari history fixture not present
  in this checkout.

Finding surfaced to the phase status; not in scope for HS-25-01. The `_built`
drift overlaps HS-25-08 (which rebuilds the bundle).

## Acceptance criteria — re-checked

- [x] Test: `provider="local"` + missing model → no cloud client constructed
      (live + deferred) — `test_intel_egress_invariant.py`.
- [x] Test: explicit `cloud`/`auto` still reach the cloud — same file.
- [x] `doctor` reports the egress posture — `_check_meeting_intel_egress`.
- [x] Egress posture exposed for the web surface — `intel_egress` in
      `/api/runtime/status`; visual badge split to HS-25-08.
- [x] Documented in `docs/MEETING_MODE_GUIDE.md`.

## Deviations from plan

Premise corrected from "fix a silent-egress bug" to "lock the already-correct
invariant + surface the posture" (no production behavior change). The visual
dashboard badge was split into a new follow-up story **HS-25-08** because it
requires an Astro `_built` rebuild — a different blast radius from this backend
trust work.

## Follow-ups

- **HS-25-08** — render the egress badge on the web dashboard.
- Pre-existing `_built` staleness + missing Safari fixture cause 9 failing tests
  on `main`; flagged in `current-phase-status.md` "Where we are".
