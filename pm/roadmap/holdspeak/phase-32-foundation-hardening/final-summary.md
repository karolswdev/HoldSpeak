# Phase 32 — Foundation Hardening & Doc Truth — Final Summary

**Status:** CLOSED ✅ — 7/7 stories shipped. **Closed:** 2026-06-02.

Phase 32 closed the structural, verification, and doc-integrity gaps surfaced by
the 2026-06-02 engineering review — plus a mid-phase user directive to retire the
TUI and menubar. The web runtime is now the project's *sole* interactive runtime,
and the core promise (audio → text) finally has a CI gate.

## What shipped

| Story | Outcome |
|---|---|
| **HS-32-01** | `run_web_runtime()` (1,702-line god-function, 10 `nonlocal` vars) → a `WebRuntime` class; entry point unchanged via a thin shim. |
| **HS-32-02** | `MeetingSession` is **web-free** — emits live events via an injected `on_broadcast`; `WebRuntime` observes. **User decision:** the embedded per-meeting web server was *dropped*, not relocated. |
| **HS-32-07** | *(inserted by user directive)* **Retired the TUI + the macOS menubar.** `tui/` + `controller.py` + `menubar.py`, the `tui`/`menubar` subcommands, `--no-tui`, and the `textual`/`rumps` deps all deleted — **~13k lines removed**. Web is the sole interactive runtime. |
| **HS-32-03** | **One audio-ownership model** — `VoiceTypingSession` gained source-less `acquire`/`release`; the meeting holds the shared floor; hotkey/device/meeting arbitrate through one owner with defined precedence (concurrency-tested). |
| **HS-32-04** | **Ungated CI core-path smoke test** — a committed `say`-generated WAV → real Whisper `tiny` → the injection seam, asserting on produced text; runs on the macOS integration job **every push** (off the never-in-CI `metal`/`spoken_e2e` markers). Mutation check shown. |
| **HS-32-05** | **One route 500-response helper** (`error_500`) replaces the canonical `log.error + JSONResponse(500)` block at **48** sites — an error-contract change is now a one-line edit. |
| **HS-32-06** | **Doc-truth sweep + drift guard** — fixed the false "DeterministicPlugin stub" claims, a dead branch header, and TUI mentions; removed the vestigial `config.meeting.web_enabled`; refreshed `HANDOVER.md`; committed a doc-drift guard so the stub-rot can't return. |

## Decisions of record (user)

- **Drop the embedded per-meeting web server** (HS-32-02) — the flagship
  `WebRuntime` is the single dashboard owner.
- **Kill the TUI *and* the menubar** (HS-32-07), full removal, sequenced *before*
  the audio convergence so it had a single home. CLI subcommands
  (`meeting`/`history`/`intel`/…) stay.
- **A helper *function* over a decorator** for the route 500s (HS-32-05) — the
  handlers' nested try/except + specific non-500 handling made a whole-handler
  decorator unsafe.
- **Smoke model = `tiny`** + a committed WAV (HS-32-04).

## Also fixed (discovered en route)

- A latent Phase-31 db-decomposition miss: `web_runtime.py` called
  `get_all_projects_for_detector()` on the `Database` container (it had moved to
  `db.projects`), silently degrading the project detector to zero projects at
  startup. Fixed + regression-tested (a standalone commit).

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **1954 passed, 14 skipped**.
- **Branch:** the whole phase is a **stacked local branch**
  `phase-32/hs-32-01-web-runtime-classify` (7 story commits + the db fix),
  **unpushed** — open a PR to `main`.
- **Real-audio caveat:** the `metal` paths (a meeting opening a live mic) remain
  hardware-gated and were not runnable in this remote session; HS-32-04 covers
  real transcription on a committed WAV instead.

## Hardware-gated, still open

Phase 24 (companion, 3/6), Phase 25 (HS-25-07 dogfood), Phase 15 (out-and-about)
— all need the physical AI-PI / a real mic and a non-remote author.
