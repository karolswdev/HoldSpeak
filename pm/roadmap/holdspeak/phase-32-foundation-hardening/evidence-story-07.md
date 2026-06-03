# Evidence — HS-32-07 (Retire the TUI + menubar runtimes)

**Shipped:** 2026-06-02. Per the user directive ("the TUI needs to be killed" →
full removal including the menubar), the **web runtime is now the sole
interactive runtime**. The Textual TUI and the macOS menu-bar app are deleted
outright — code, CLI surface, dependencies, tests, and docs.

## Code removed (~7,300 lines of runtime code)

- `holdspeak/tui/` — the whole Textual package (**5,876 lines**: app, screens,
  components, services, state, styles, utils).
- `holdspeak/controller.py` — the TUI runtime controller (**786 lines**).
- `holdspeak/menubar.py` — the macOS menu-bar app (**644 lines**).
- `holdspeak/main.py` — removed the `tui` + `menubar` subcommands, the `--no-tui`
  flag + `_emit_no_tui_deprecation`, the `from .controller import …`, the
  `_run_tui_mode` / `_preload_model_before_tui` / `_run_menubar_mode` helpers,
  and the dead `_run_simple_mode` legacy path (plus its now-unused
  `HotkeyListener`/`AudioRecorder`/`TextTyper`/`TextProcessor` imports). `holdspeak`
  with no subcommand still launches the web runtime; the default `--no-open` is
  now `False` (no more `args.no_tui` alias).
- `holdspeak/web_runtime.py` — removed the three stale "run `holdspeak tui`"
  strings (startup failure fallback, hotkey-unavailable hint, and the class
  docstring's `controller.py` reference).

## Dependencies dropped

- `pyproject.toml`: removed `textual>=0.50.0` (core dep) and the entire
  `[project.optional-dependencies] menubar = ["rumps…"]` extra. Confirmed
  nothing outside the deleted dirs imports `textual`/`rumps`.

## Tests

- **Deleted** (test only the removed runtimes): `tests/unit/test_controller.py`
  (597), `tests/unit/test_menubar.py` (827), `tests/integration/test_tui.py`
  (755), `tests/integration/test_quit_during_meeting.py` (83).
- **Adjusted:**
  - `tests/unit/test_main_modes.py` — dropped the `tui`-routing and the two
    `--no-tui` tests; the defaults test no longer patches the deleted
    `_run_tui_mode`/`_emit_no_tui_deprecation`; added
    `test_unknown_tui_subcommand_is_rejected` (argparse exit 2).
  - `tests/integration/test_dictation_project_context.py` — removed the two
    controller-path tests (they imported helpers from the deleted
    `test_controller.py`); the runtime dictation-pipeline project-root behavior
    they covered is already asserted by `test_web_runtime.py`'s device-reply
    test. The two CLI-path tests stay. Unused imports cleaned.
  - `test_transcribe_timeout.py`, `test_web_flagship_audit.py`,
    `test_voice_typing_via_device.py` — stale "controller"/"menubar"/`--no-tui`
    comments reworded.

## Docs

- **Updated (live surface):** root `README.md` (removed the "Menu bar mode"
  platform row; reworded the Wayland fallback line — no more "focused
  hold-to-talk"); `docs/USER_GUIDE.md`; `docs/MEETING_MODE_GUIDE.md` (rewrote the
  TUI mode/controls/screenshot sections to web-dashboard equivalents).
- **Deleted (wholly dead):** root `HANDOFF.md` (a stale "TUI Phase 3" handoff,
  superseded by `pm/roadmap/holdspeak/HANDOVER.md`); `docs/TUI_INVENTORY.md`,
  `TUI_PROJECT_PLAN.md`, `TUI_ARCHITECTURE_SPEC.md`, `TUI_ROADMAP.md`;
  `docs/PLAN_MENU_BAR.md`; the 7 `docs/screenshots/tui_*.svg`.
- **Canon banner:** `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` got a superseded
  note at the top — its `WFS-C-002`/`WFS-C-003` (keep TUI as fallback,
  `--no-tui` deprecation) requirements are now historical. Remaining `PLAN_*.md`
  passing TUI mentions (`PLAN_MEETING_MODE`, `PLAN_MEETING_INTEL_PI`,
  `PLAN_ARCHITECT_PLUGIN_SYSTEM`, `PLAN_PHASE_MULTI_INTENT_ROUTING`) are
  **deferred to HS-32-06** (the doc-truth sweep), which is explicitly scoped to
  reconcile `PLAN_*.md`; flagged in that story.

Total: **54 files deleted, ~13,050 lines removed.**

## Verification

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1939 passed, 14
  skipped** (down from 2066 — the delta is the deleted TUI/menubar/controller
  tests; no remaining test references the deleted modules).
- `holdspeak --help` lists only
  `{web,meeting,history,actions,intel,dictation,agent-hook,device-psk,doctor}`;
  `holdspeak tui` → "invalid choice: 'tui'" (argparse exit 2); the CLI imports
  with no `textual`/`controller`/`menubar`.
- Ruff: no new findings in changed code (`web_runtime.py` clean; the 3 `main.py`
  findings — `F541`/`E741`×2 — are pre-existing in the untouched
  `_run_meeting_mode`).

## Decisions / deviations

- **Full removal, menubar included** (user choice). Web is the flagship and now
  the *only* interactive runtime; the CLI subcommands
  (`meeting`/`history`/`intel`/`dictation`/…) stay.
- **Sequenced before HS-32-03** (user choice) so the audio-ownership convergence
  has a single home (`WebRuntime`) with no TUI/menubar caveat.
- **`config.meeting.web_enabled`** (made vestigial by HS-32-02) is still present;
  its removal remains flagged for HS-32-06.
