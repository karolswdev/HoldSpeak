# HS-42-01 — Setup-state contract + `first_run` milestone

- **Project:** holdspeak
- **Phase:** 42
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-42-03, HS-42-04, HS-42-05, HS-42-06, HS-42-07
- **Owner:** unassigned

## Problem

Every first-run surface (welcome route, guided test, trust chip, model assistant,
presence onboarding) needs **one** backend shape that answers "is this product
ready, and if not, what's the single next thing to do?" That truth exists today,
but scattered across `doctor`, `/api/dictation/readiness`, runtime status, the
egress helper, and presence detection. Without a single composed contract, each UI
surface would re-derive readiness and drift from the doctor.

## Scope

- In:
  - `GET /api/setup/status` returning the stable model in the proposal (`overall`,
    `first_run`, `primary_action`, `sections[]`, `trust{}`, `presence{}`).
  - A pure composition layer (e.g. `holdspeak/setup_status.py`) that **adapts**
    the existing structured sources — `collect_doctor_checks()` (already
    `list[DoctorCheck(name,status,detail,fix)]`), `/api/dictation/readiness` data,
    `intel_egress_posture()`, and `detect_presence_platform()` — into setup
    sections + a `primary_action` (the highest-severity unmet check) + a trust
    summary. No new check logic.
  - A durable **first-success milestone**: a tiny marker (a `milestones` row or the
    existing repository pattern) recorded the first time a dictation verifiably
    succeeds; `first_run` is true when the marker is absent (or no config file
    exists). `overall` ∈ `ready|needs_attention|blocked` derived from section
    statuses.
  - Cheapness: the status read loads no large model and does no network call by
    default (endpoint preflight is a separate opt-in path).
- Out:
  - Any UI (welcome route, chip, panel) — those consume this contract.
  - Recording the milestone from the real dictation path (HS-42-04 wires the write;
    this story defines + persists the marker + exposes a seam to set it).
  - Endpoint preflight network calls (HS-42-06).

## Acceptance criteria

- [ ] `GET /api/setup/status` returns the documented shape; integration-tested for
      a ready state and a blocked state (snapshot fixtures).
- [ ] The composition is an **adapter over `collect_doctor_checks()`** — a unit
      test asserts **every doctor `FAIL` maps to a setup section** (the drift guard),
      and check IDs are stable.
- [ ] `first_run` flips from `true` to `false` once the durable milestone is set,
      and **survives a process restart** (DB-backed); proven by a test.
- [ ] `primary_action` points at the single highest-severity next step with a
      `route` deep link.
- [ ] The status read is cheap (no large-model load / no default network call);
      asserted structurally.
- [ ] Default suite green; with no config it reports `first_run: true` without
      error.

## Test plan

- Unit: `tests/unit/test_setup_status.py` (composition, overall derivation,
  primary-action selection, first_run milestone set/persist/restart).
- Unit: `tests/unit/test_setup_status_doctor_drift.py` (every doctor FAIL → a section).
- Integration: `tests/integration/test_web_setup_status_api.py` (route shape;
  ready + blocked fixtures).
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Milestone home: prefer a small durable marker via the existing `db/` repository
  pattern (mirrors `db/corrections.py` / `db/actuators.py`); regenerate the
  canonical schema snapshot if a table is added.
- Keep the doctor the single source of check truth — this story must not fork its
  logic, only adapt its output.
