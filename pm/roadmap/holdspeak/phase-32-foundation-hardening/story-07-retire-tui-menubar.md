# HS-32-07 — Retire the TUI + menubar runtimes

- **Status:** done (2026-06-02). Evidence: [evidence-story-07.md](./evidence-story-07.md).

## Goal

Make the **web runtime the sole interactive runtime**. Delete the Textual TUI
(`holdspeak/tui/` + `controller.py`) and the macOS menu-bar app
(`holdspeak/menubar.py`) outright, along with their CLI subcommands, the
deprecated `--no-tui` alias, and the `textual`/`rumps` dependencies. Update all
relevant documentation. *(User directive, 2026-06-02: "the TUI needs to be
killed" → full removal including the menubar.)*

This also clears the way for HS-32-03: with the TUI/menubar gone, the
hotkey/device/meeting audio paths live **only** in `WebRuntime`, so the
audio-ownership convergence has a single home.

## Scope

- **Delete code:** `holdspeak/tui/` (package), `holdspeak/controller.py`,
  `holdspeak/menubar.py`. Plus the dead `_run_simple_mode` legacy helper.
- **`main.py`:** remove the `tui` + `menubar` subcommands, the `--no-tui` flag +
  its deprecation helper, the controller import, and the TUI/menubar run helpers.
  `holdspeak` (no subcommand) still launches the web runtime.
- **`pyproject.toml`:** drop `textual` (core dep) and the `menubar`/`rumps` extra.
- **Tests:** delete the TUI/menubar/controller-only tests; adjust the few with
  incidental controller mentions.
- **Docs:** update the live user-facing surface (README, USER_GUIDE,
  MEETING_MODE_GUIDE); delete the wholly-dead TUI/menubar docs + screenshots;
  banner the most-contradicted canon doc. Remaining `PLAN_*.md` passing TUI
  mentions are reconciled in HS-32-06.

**Posture: greenfield/aggressive** — delete, don't deprecate. Web is the flagship.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green (the
  drop in count is the deleted TUI/menubar/controller tests).
- `holdspeak --help` lists no `tui`/`menubar`; `holdspeak tui` is rejected
  (argparse exit 2); the CLI imports with no `textual`/`controller`/`menubar`.

## Done when

- [x] `holdspeak/tui/`, `controller.py`, `menubar.py` are gone; nothing imports
      them; `textual`/`rumps` dropped from `pyproject`.
- [x] `main.py` exposes no `tui`/`menubar` subcommand and no `--no-tui`; the web
      runtime is the sole interactive runtime.
- [x] Live user docs updated; dead TUI/menubar docs deleted; full suite green; ruff clean (no new findings).
