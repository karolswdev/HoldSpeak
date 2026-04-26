# HS-4-01 — Audit + integration coverage for existing web-flagship surfaces

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-3-06 (phase 3 closed; phase-4 scaffold landed)
- **Unblocks:** HS-4-02..05 (audit confirms which surfaces are stable to build on top of)
- **Owner:** unassigned

## Problem

The runtime/CLI/meeting-control halves of WFS-01 are *already
built* (`holdspeak/web_runtime.py`, `holdspeak/main.py` `web`/`tui`
subcommands, `--no-tui` deprecation, `/api/meeting/start|stop|*`).
But there's no integration-test coverage that exercises them
end-to-end as a web-first flow. This story closes that gap with
a small set of focused integration tests so the phase exits with
the original WFS-* requirement family covered, not just the
configurability amendment.

## Scope

- **In:**
  - Integration test verifying `holdspeak` (no args) launches the web runtime and the runtime serves `/history` and `/settings` while idle (`WFS-P-001`, `WFS-R-001`, `WFS-R-002`).
  - Integration test verifying `holdspeak tui` still launches the TUI mode (or at least starts the TUI entry point — the actual TUI loop is hard to drive in tests; assert the path is reached).
  - Integration test verifying `--no-tui` emits the deprecation message before falling through to web mode (`WFS-C-003`).
  - Integration test verifying `/api/meeting/start` and `/api/meeting/stop` are callable on a running web runtime without the TUI being involved (`WFS-P-002`, `WFS-R-003`).
  - Integration test verifying the bind address defaults to `127.0.0.1` (`WFS-R-004`).
  - Document any spec §5.1–§5.4 gaps as deferred follow-up items in evidence (e.g., `WFS-O-001` mode-logging consistency, `WFS-O-003` startup-failure messaging).
- **Out:**
  - New product code in `web_runtime.py` / `web_server.py` / `main.py`. This story is a verify-by-test pass; refactors only if the audit reveals a concrete bug.
  - Coverage for any `/api/dictation/*` endpoints — those don't exist yet (HS-4-02..05 territory).

## Acceptance criteria

- [x] 5 new integration tests at `tests/integration/test_web_flagship_audit.py` covering WFS-R-004 (loopback default + explicit host override), WFS-R-001+R-002 (idle `/history` + `/settings`), WFS-P-003 (runtime-status payload shape with `mode="web"`), WFS-P-002 (meeting start/stop routes mounted).
- [x] Tests execute without `requires_meeting` mark — they use the minimal `MeetingWebServer` fixture pattern from existing `test_web_server.py`.
- [x] Audit found that `tests/unit/test_main_modes.py` (7 tests) already covers WFS-C-001/C-002/C-003 + doctor passthrough, and `tests/integration/test_web_server.py` already covers TestRuntimeControlEndpoints / TestSettingsApiEndpoints / TestHistoryUiSmoke. Documented in `evidence-story-01.md`. The new audit file is small *because* the surface is already well-covered — the audit's value is the WFS-* requirement traceability.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 1012 passed, 13 skipped (delta +5 vs. HS-3-06 baseline 1007).

## Test plan

- **Integration:** the new tests above. Use `TestClient` from FastAPI (existing pattern in `test_web_server.py`).
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- The TUI assertion is necessarily shallow — driving the TUI through tests is out of scope for this audit. Asserting `_run_tui_mode` is reached (via monkey-patch) is enough.
- If the audit finds a real bug (not just a coverage gap), fix it inline and document in evidence — don't push a separate story.
