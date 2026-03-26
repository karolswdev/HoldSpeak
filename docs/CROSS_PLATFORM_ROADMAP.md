# HoldSpeak Cross-Platform Roadmap (macOS + Linux)

## Purpose

Ship and maintain HoldSpeak as a reliable dual-platform app with:
- First-class support on macOS (Apple Silicon) and Linux (Ubuntu/Debian class distros).
- Explicitly documented degraded behavior where platform security models differ (notably Wayland global input/text injection).
- CI and test gates that prevent platform regressions.

Execution board:
- `docs/CROSS_PLATFORM_TASK_BOARD.md`

---

## Current Snapshot (as of 2026-03-26)

Implemented already:
- Platform-aware transcription backend selection (`mlx-whisper` on macOS arm64, `faster-whisper` when installed).
- Linux install path via `.[linux]` extra.
- Linux system-audio detection via Pulse/PipeWire monitor sources, plus `ffmpeg` fallback capture.
- Focused-only hold-to-talk path in TUI when global hooks are unavailable.
- Diagnostics screen reporting session/runtime capability details.
- Repaired stale TUI integration imports against the current screen/component architecture.
- Integration dependency split: FastAPI/web integration modules are explicitly optional (`requires_meeting`) and skip cleanly when missing.
- Linux smoke script interpreter portability (`venv python` -> `python3` -> `python`) with clear interpreter reporting.
- Linux smoke CI gate added and included in required summary checks.
- CLI/help/package/README wording updated for macOS + Linux support matrix and known limitations.

Known gaps:
- Wayland fallback UX copy can be tightened further in runtime notifications.
- Diagnostics capability-state coverage should be expanded for degraded states.
- `meeting --setup` Linux failure messaging can include more explicit step-by-step remediation.

---

## Support Targets (V1)

### In-scope targets
- macOS 14+ (Apple Silicon)
- Linux x86_64 (Ubuntu 24.04+ baseline, Debian-family compatible)
- Sessions:
  - X11: global hotkey + cross-app paste expected to work
  - Wayland: focused-only hold-to-talk guaranteed; global hooks/text injection best effort

### Out of scope (V1)
- Linux tray/menu bar parity with macOS `rumps` mode.
- Universal Wayland compositor-specific global shortcut support.
- Packaging native distro artifacts (`.deb`, `.rpm`, Flatpak, Snap).

---

## Milestones

### M1: Baseline Reliability (2 weeks)

Goal: make current cross-platform behavior explicit and reproducible.

Deliverables:
- Fix stale integration tests and remove dead imports/assumptions.
- Make Linux smoke script portable (`python3` fallback).
- Align CLI/help/docs wording with dual-platform reality.
- Add platform-capability notes to docs (X11 vs Wayland behavior).

Acceptance criteria:
- `pytest -q tests/integration` collects and runs in a dev environment with required extras.
- `scripts/linux_smoke.sh` passes on a host that has `python3` but not `python`.
- No primary entrypoint/help text claims macOS-only behavior for core TUI/voice typing paths.
- README has a clear support matrix and known limitations section.

Exit evidence:
- Green local test run logs for unit + integration.
- Updated docs merged and reviewed.

---

### M2: CI Platform Gates (1-2 weeks)

Goal: catch macOS/Linux regressions before merge.

Deliverables:
- Add Linux smoke CI job (no model download, no audio hardware required).
- Keep Linux unit tests in CI as mandatory.
- Keep macOS integration/e2e jobs for Apple-specific paths.
- Ensure optional dependency sets are explicit per job (`.[test]`, `.[linux]`, `.[meeting]` as needed).

Acceptance criteria:
- CI matrix includes at least:
  - Linux: unit + smoke
  - macOS: integration + e2e (existing)
- Linux jobs run without installing Apple-only dependencies.
- Smoke job verifies:
  - import of key modules
  - backend selection logic
  - monitor-source discovery does not crash if `pactl` is unavailable

Exit evidence:
- CI workflow green on one PR that touches platform-sensitive code.

---

### M3: Linux UX Parity for Core Flows (2 weeks)

Goal: remove ambiguity for Linux users, especially on Wayland.

Deliverables:
- Harden user messaging when global hotkey/text injection are unavailable.
- Ensure fallback path is obvious in TUI and docs ("hold key while focused", "copied, paste manually").
- Improve `meeting --setup` guidance for monitor-source setup failures.

Acceptance criteria:
- On Wayland without working global hooks:
  - app starts without crashing
  - focused hold-to-talk works
  - transcription still usable via clipboard/manual paste path
- Diagnostics screen always shows capability status and reasons.
- `holdspeak meeting --setup` provides actionable Linux instructions in failure cases.

Exit evidence:
- Manual verification checklist completed on one X11 host and one Wayland host.

---

### M4: Release Readiness (1 week)

Goal: finalize dual-platform V1 release quality.

Deliverables:
- Cross-platform release checklist in docs.
- Known-issues section with workarounds.
- Versioned release notes calling out platform support level and limitations.

Acceptance criteria:
- All required checks green in CI.
- Manual sanity checks pass on target OS matrix.
- Documentation is internally consistent (README + docs + CLI help).

Exit evidence:
- Tagged release candidate with signed-off checklist.

---

## Workstream Backlog (Prioritized)

P0:
- Repair integration suite drift (`tests/integration/test_tui.py` and related exports).
- Add Linux smoke CI gate.
- Fix linux smoke interpreter portability.
- Normalize macOS-only language in public docs/help text.

P1:
- Strengthen Wayland-specific fallback UX and copy.
- Add explicit support matrix to README and docs.
- Expand automated tests for capability-state reporting.

P2:
- Optional Linux helper integrations (`wl-clipboard`, `wtype`) with clear opt-in guidance.
- Optional Linux packaging/distribution work.

---

## Definition of Done (Cross-Platform V1)

Cross-platform V1 is complete when all are true:
- Install:
  - macOS arm64 install works with default deps.
  - Linux install works with `uv pip install -e '.[linux]'`.
- Core runtime:
  - `holdspeak` TUI launches and records/transcribes on both platforms.
  - Linux meeting mode supports mic capture; system-audio capture works where monitor source exists.
- Degraded-path behavior:
  - Wayland limitations are non-fatal and clearly communicated.
- Quality gates:
  - Required CI jobs for Linux and macOS are green.
  - Unit/integration suites are stable and non-stale.
- Documentation:
  - README, setup guides, and CLI help consistently describe cross-platform behavior and limitations.

---

## Verification Checklist (Release Candidate)

Automated:
- `pytest -q tests/unit`
- `pytest -q tests/integration -m integration`
- Linux smoke script in CI

Manual (macOS):
- Launch TUI, hold-to-talk, paste into another app.
- Start/stop meeting mode and verify transcript generation.

Manual (Linux X11):
- Verify global hotkey path + cross-app paste.
- Verify `meeting --setup` and monitor-source detection.

Manual (Linux Wayland):
- Verify focused-only hold-to-talk path.
- Verify text copy/manual paste fallback messaging.
- Verify diagnostics screen capability flags.
