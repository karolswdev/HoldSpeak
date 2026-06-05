# HS-40-06 — Desktop + Web Verification

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done
- **Depends on:** HS-40-03, HS-40-04, HS-40-05
- **Unblocks:** HS-40-07
- **Owner:** unassigned

## Problem

Presence indicators fail if they steal focus, flicker, show stale status, or
look broken under real desktop constraints. This story proves the native and
web renderers work across the important states before closeout.

## Scope

- **In:**
  - Add deterministic event playback for idle, listening/recording,
    transcribing, processing, typing, meeting live, saving, reconnecting, and
    error states.
  - Capture web Playwright screenshots for desktop/mobile states.
  - Capture native-host screenshots or smoke artifacts on macOS/Linux where
    available.
  - Verify reduced-motion behavior and focus preservation.
  - Add regression coverage so stale websocket/reconnect events cannot leave
    the indicator permanently wrong.
- **Out:**
  - Full visual regression infrastructure for every route.
  - Native device testing.

## Acceptance Criteria

- [x] Desktop and mobile web screenshots exist for the main presence states.
- [x] Native host screenshot/smoke artifacts exist for the supported platform
      path(s), with unsupported platform gaps explicitly documented.
- [x] No text overlap, clipped labels, or control resizing is visible in the
      screenshots.
- [x] Reduced-motion mode disables/neutralizes pulse animation.
- [x] A focus-preservation smoke test or manual evidence confirms the native
      window does not steal typing focus in the supported path.
- [x] Automated tests cover state reducer/message handling enough that stale
      websocket events cannot leave the indicator wrong.

## Test Plan

- Backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Web: run the documented web build and Playwright/screenshot commands.
- Desktop: run host fixture/smoke command on available GUI platform(s).
- Evidence: paste actual command output and screenshot paths into
  `evidence-story-06.md`.

## Notes / Open Questions

- Platform coverage may be asymmetric in CI. If Linux GUI smoke cannot run in
  CI, record a manual smoke command and keep unit coverage for the platform
  adapter.
- 2026-06-05: backend/lint/build/web screenshot evidence captured in
  [evidence-story-06.md](./evidence-story-06.md). Installed
  `python-tk@3.13`, moved Tk rendering into a subprocess, completed the
  interactive Tk smoke, and captured a frontmost-app focus smoke.
- 2026-06-05: added `scripts/desktop_presence_smoke.py`. Default `--render
  view` mode is CI-safe and emits renderer-ready JSON for every state; `--render
  tk` is reserved for manual interactive macOS/Linux native-window smoke.
