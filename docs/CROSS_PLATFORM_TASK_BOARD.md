# HoldSpeak Cross-Platform Task Board (macOS + Linux)

## How to use this board

- Unit of planning: issue-sized tasks (0.5d to 3d each).
- Size scale:
  - `XS` = 0.5 day
  - `S` = 1 day
  - `M` = 2 days
  - `L` = 3 days
- Priority:
  - `P0` blocking release
  - `P1` important non-blocking
  - `P2` optional/post-release
- Status:
  - `todo`, `in_progress`, `blocked`, `done`

---

## Epic E1: Test and Runtime Baseline Reliability

Goal: make cross-platform behavior measurable and non-regressing.

### CP-001 — Repair stale TUI integration test imports
- Priority: `P0`
- Size: `M`
- Status: `done`
- Owner: `codex`
- Depends on: none
- Scope:
  - Update `tests/integration/test_tui.py` to match current TUI exports/architecture.
  - Remove references to dead symbols (`_clamp01`, old widget exports).
- Acceptance criteria:
  - `pytest -q tests/integration/test_tui.py` collects and executes.
  - No import-time failures caused by stale symbols.
- Evidence:
  - CI/log snippet of passing collection and test run.

### CP-002 — Split integration tests by dependency profile
- Priority: `P0`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: `CP-001`
- Scope:
  - Mark tests requiring optional deps (e.g., FastAPI/web server pieces).
  - Ensure base integration subset can run with documented extras.
- Acceptance criteria:
  - Running integration tests with documented env does not fail at import collection.
  - Dependency requirements are explicit in docs/commands.

### CP-003 — Harden Linux smoke script interpreter detection
- Priority: `P0`
- Size: `XS`
- Status: `done`
- Owner: `codex`
- Depends on: none
- Scope:
  - Prefer active venv python, then `python3`, then `python`.
  - Fail with actionable message if none exist.
- Acceptance criteria:
  - Script passes on hosts with only `python3`.
  - Script output clearly states which interpreter is used.

### CP-004 — Add smoke checks for no-`pactl` environments
- Priority: `P1`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: `CP-003`
- Scope:
  - Extend smoke script to simulate/validate behavior when `pactl` is missing.
- Acceptance criteria:
  - Script exits successfully and reports degraded capability instead of failing.

---

## Epic E2: CI Platform Gates

Goal: enforce macOS + Linux quality gates in CI.

### CP-005 — Add dedicated Linux smoke CI job
- Priority: `P0`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: `CP-003`
- Scope:
  - Add job to `.github/workflows/test.yml` running `scripts/linux_smoke.sh`.
  - Ensure it does not download models.
- Acceptance criteria:
  - CI has mandatory Linux smoke job.
  - Job passes on PRs that do not break imports/capability checks.

### CP-006 — Linux CI dependency matrix hardening
- Priority: `P0`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: none
- Scope:
  - Make Linux jobs use explicit extras (`.[test]`, optionally `.[linux]` where needed).
  - Confirm Apple-only deps are never installed on Linux jobs.
- Acceptance criteria:
  - Linux CI logs show no attempt to install `mlx-whisper`.

### CP-007 — Add Linux integration-lite CI target
- Priority: `P1`
- Size: `M`
- Status: `todo`
- Owner: `unassigned`
- Depends on: `CP-001`, `CP-002`, `CP-006`
- Scope:
  - Add a small integration subset runnable on Linux without GUI/audio hardware.
- Acceptance criteria:
  - Linux integration-lite job is green and stable over 3 consecutive PRs.

---

## Epic E3: UX and Docs Consistency

Goal: make platform behavior explicit and reduce user confusion.

### CP-008 — Normalize macOS-only wording in CLI/help/metadata
- Priority: `P0`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: none
- Scope:
  - Update package description, CLI description/epilog, and user-facing help to reflect cross-platform core support.
- Acceptance criteria:
  - No core command/help text states macOS-only support for TUI voice typing.

### CP-009 — README support matrix + known limitations
- Priority: `P0`
- Size: `S`
- Status: `done`
- Owner: `codex`
- Depends on: none
- Scope:
  - Add matrix for macOS/Linux/X11/Wayland capabilities.
  - Clarify `menubar` is macOS-only.
- Acceptance criteria:
  - README has dedicated "Platform Support" and "Known Limitations" sections.

### CP-010 — Meeting setup docs cleanup for Linux/macOS
- Priority: `P1`
- Size: `S`
- Status: `todo`
- Owner: `unassigned`
- Depends on: `CP-009`
- Scope:
  - Remove conflicting macOS-only instructions from Linux paths.
  - Add Linux-native meeting setup guidance.
- Acceptance criteria:
  - Linux user can follow docs end-to-end without encountering `brew`/Metal-only steps.

### CP-011 — Wayland fallback copy improvements
- Priority: `P1`
- Size: `S`
- Status: `todo`
- Owner: `unassigned`
- Depends on: none
- Scope:
  - Tighten in-app notifications for disabled global hooks/text injection.
- Acceptance criteria:
  - On Wayland failure path, notifications clearly state next action (focused key or manual paste).

---

## Epic E4: Linux Core-Flow Parity Hardening

Goal: ensure Linux behavior is robust where platform constraints apply.

### CP-012 — Diagnostics capability-state test coverage
- Priority: `P1`
- Size: `M`
- Status: `todo`
- Owner: `unassigned`
- Depends on: `CP-001`
- Scope:
  - Add tests for diagnostics rendering of:
    - session env vars
    - global hotkey enabled/disabled reason
    - text injection enabled/disabled reason
- Acceptance criteria:
  - Tests verify both enabled and degraded states.

### CP-013 — `meeting --setup` failure messaging enhancement
- Priority: `P1`
- Size: `S`
- Status: `todo`
- Owner: `unassigned`
- Depends on: none
- Scope:
  - Improve guidance when monitor source is not found (`pactl`, PipeWire/Pulse checks).
- Acceptance criteria:
  - Setup output includes actionable numbered steps and command examples.

### CP-014 — Add non-regression tests for ffmpeg pulse fallback
- Priority: `P1`
- Size: `M`
- Status: `todo`
- Owner: `unassigned`
- Depends on: none
- Scope:
  - Mock subprocess + monitor resolution path in `MeetingRecorder`.
- Acceptance criteria:
  - Unit tests cover both PortAudio monitor success and ffmpeg fallback path.

---

## Epic E5: Release Readiness

Goal: ship V1 cross-platform with controlled risk.

### CP-015 — Cross-platform RC checklist doc
- Priority: `P0`
- Size: `XS`
- Status: `todo`
- Owner: `unassigned`
- Depends on: `CP-005`, `CP-008`, `CP-009`
- Scope:
  - Create release checklist from roadmap verification gates.
- Acceptance criteria:
  - Checklist used for RC sign-off and attached to release PR.

### CP-016 — Known issues + workarounds section
- Priority: `P1`
- Size: `XS`
- Status: `todo`
- Owner: `unassigned`
- Depends on: `CP-009`
- Scope:
  - Document current Wayland/global-hook constraints and workarounds.
- Acceptance criteria:
  - Release notes and docs both reference same known issues list.

---

## Suggested Sprint Cut (first 2 weeks)

Sprint A (must ship):
- `CP-001`, `CP-002`, `CP-003`, `CP-005`, `CP-006`, `CP-008`, `CP-009`

Sprint B (stabilize):
- `CP-010`, `CP-011`, `CP-012`, `CP-013`, `CP-014`, `CP-015`

Post-V1:
- `CP-004`, `CP-007`, `CP-016`

---

## Dependency Graph (condensed)

- `CP-001` -> `CP-002` -> `CP-007`
- `CP-003` -> `CP-005`
- `CP-001` -> `CP-012`
- `CP-009` -> `CP-010`, `CP-016`
- `CP-005` + `CP-008` + `CP-009` -> `CP-015`

---

## Tracking Fields Template (for GitHub issues)

Use this template on each issue:
- `Epic`: E1/E2/E3/E4/E5
- `ID`: CP-###
- `Priority`: P0/P1/P2
- `Estimate`: XS/S/M/L
- `Depends on`: CP-### (optional)
- `Platforms affected`: macOS / Linux-X11 / Linux-Wayland / CI
- `Acceptance criteria`: checklist
- `Evidence`: test log, screenshot, CI link
