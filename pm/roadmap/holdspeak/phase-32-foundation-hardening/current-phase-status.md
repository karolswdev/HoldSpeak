# Phase 32 — Foundation Hardening & Doc Truth

**Status:** CLOSED ✅ — 7/7 stories shipped (closed 2026-06-02). See
[final-summary.md](./final-summary.md).

**Last updated:** 2026-06-02 (HS-32-06 shipped — **phase closed**: doc-truth
sweep (false stub claims, dead branch header, TUI mentions, vestigial
`web_enabled`) + a committed doc-drift guard; `HANDOVER.md` refreshed; suite green
1954/14.)

## Goal

Close the structural, verification, and doc-integrity gaps surfaced by the
2026-06-02 engineering review — the items that are each too small for their own
phase but together decide whether the foundation stays workable. Two runtime
refactors (class-ify `web_runtime.py`; invert the meeting→web-server coupling),
one correctness consolidation (a single audio-ownership model), one trust gap
(a CI end-to-end smoke test for the core hotkey→text path that today only runs
behind never-in-CI markers), one cleanup (a route error-handling helper), and
one honesty fix (reconcile non-PMO docs that assert false current state).

## Scope

### In

- Convert `run_web_runtime()` (1,702 lines, 9+ `nonlocal` vars) into a `WebRuntime`
  class with instance state and lifecycle methods, matching `controller.py`.
- Invert `meeting_session.py:1552`'s `self._web_server.broadcast(...)` to an
  emit/callback the runtime observes — `MeetingSession` stops importing/knowing
  the web server.
- Converge the three audio-ownership paths (hotkey / device / meeting) on the
  `VoiceTypingSession` single-owner contract so there is one ownership model.
- Add a CI-runnable end-to-end smoke test of the core path (synthesized WAV → a
  tiny/real-but-small Whisper → injection seam), asserting on actual output text,
  not "didn't throw."
- Extract one route error-handling helper (decorator/middleware) and apply it to
  the duplicated `except → log → JSONResponse(500)` blocks in `activity.py` /
  `dictation.py` (and siblings).
- Reconcile non-PMO docs with reality: **delete** dead `PLAN_*.md` docs/sections
  (non-existent branches, shipped-differently features), fix `HANDOVER.md` + README
  positioning; add a lightweight guard so the worst drift (stub counts) can't rot again.
- **(Added 2026-06-02, user directive) Retire the TUI + menubar runtimes** —
  delete `holdspeak/tui/` + `controller.py` + `menubar.py`, their CLI subcommands,
  the `--no-tui` alias, and the `textual`/`rumps` deps; the web runtime becomes
  the sole interactive runtime. Update all relevant docs. Sequenced first so the
  audio-ownership convergence (HS-32-03) has a single home.

**Posture: greenfield/aggressive** — one user (the author), destructive changes
fine. The refactors (HS-32-01/02) preserve behavior because that's what a refactor
*is*, not out of compat duty; but HS-32-03 may change meeting-capture behavior to
reach the clean single model, and HS-32-06 **deletes** dead docs rather than
archiving them.

### Out

- New endpoints, payload changes, or product features.
- The PMO roadmap corpus itself — the historical record stays as-is by design;
  this phase touches **non-PMO** project docs only (`docs/`, `HANDOVER.md`, README).
- The `db.py` work (that is Phase 31) and async DB offload (settled in Phase 26).
- Building or killing the menubar/intel-streaming *features* — HS-32-06 fixes/deletes
  their stale *docs*, it does not change the code those docs describe.

## Exit criteria (evidence required)

- [x] `web_runtime.py`'s orchestration is a `WebRuntime` class (no module-level
      `nonlocal`-threaded god-function); behavior unchanged, web suite green.
      **(HS-32-01, 2026-06-02.)**
- [x] `MeetingSession` no longer references a web server; it emits, the runtime
      observes — proven by a test constructing a `MeetingSession` with no web
      server and exercising broadcast-triggering paths. **(HS-32-02, 2026-06-02;
      embedded server dropped per user decision.)**
- [x] One audio-ownership model: hotkey / device / meeting all acquire through the
      `VoiceTypingSession` owner contract; a concurrency test shows mutual exclusion.
      **(HS-32-03, 2026-06-02; meeting holds the floor via `acquire`/`release`.)**
- [x] A CI job runs the core hotkey→text smoke test on every push and asserts on
      the produced text; it is **not** gated behind `metal`/`spoken_e2e`.
      **(HS-32-04, 2026-06-02; macOS integration job, real Whisper `tiny` on a
      committed WAV; mutation check shown.)**
- [x] The route error-handling duplication is removed via a single helper, with a
      before/after handler count recorded. **(HS-32-05, 2026-06-02; `error_500`
      at 48 sites; chose a helper fn over a decorator — see decisions.)**
- [x] `HANDOVER.md`, the `PLAN_*.md` status headers, and README positioning state
      only true things; the stub-count guard is committed. **(HS-32-06, 2026-06-02;
      `test_doc_drift_guard.py` + the stub-claim/branch-header/`web_enabled` fixes.)**
- [x] **The TUI + menubar runtimes are removed** (`tui/`, `controller.py`,
      `menubar.py`, their subcommands, `--no-tui`, and `textual`/`rumps` deps);
      the web runtime is the sole interactive runtime; live docs updated.
      **(HS-32-07, 2026-06-02; user directive.)**
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout.
      **(Green at every story; closed at 1954 passed / 14 skipped.)**

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-32-01 | Class-ify `web_runtime.py` (`WebRuntime`) | done | [story-01-web-runtime-classify.md](./story-01-web-runtime-classify.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-32-02 | Invert meeting→web-server coupling | done | [story-02-meeting-web-inversion.md](./story-02-meeting-web-inversion.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-32-03 | Converge audio ownership | done | [story-03-audio-ownership.md](./story-03-audio-ownership.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-32-04 | CI end-to-end smoke test (core path) | done | [story-04-ci-e2e-smoke.md](./story-04-ci-e2e-smoke.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-32-05 | Route error-handling helper | done | [story-05-route-error-helper.md](./story-05-route-error-helper.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-32-06 | Stale non-PMO doc sweep + drift guard | done | [story-06-doc-truth-sweep.md](./story-06-doc-truth-sweep.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-32-07 | Retire the TUI + menubar runtimes | done | [story-07-retire-tui-menubar.md](./story-07-retire-tui-menubar.md) | [evidence-story-07.md](./evidence-story-07.md) |

## Where we are

Opened 2026-06-02 alongside Phase 31, sequenced after it. The review found the
TUI runtime (`controller.py`) is clean and the web runtime is its messy twin;
Phase 26 decomposed `web_server.py` but left `web_runtime.py` and the meeting→web
inversion standing. This phase finishes that and closes the test-trust and
doc-truth gaps in the same pass.

**HS-32-01 shipped (2026-06-02):** the 1,702-line `run_web_runtime()`
god-function (10 `nonlocal` vars, ~55 closures) is now a `WebRuntime` class —
state on `self`, closures as methods, `run()` owning the lifecycle, and a
4-line `run_web_runtime()` shim preserving the entry point. Behavior-preserving;
suite green at 2063/14, `web_runtime.py` ruff-clean. The class is now the
substrate HS-32-02 (meeting→web inversion) builds the observer onto.

**HS-32-02 shipped (2026-06-02):** `MeetingSession` is now web-free — it no
longer imports, owns, starts, stops, or broadcasts to a `MeetingWebServer`. It
**emits** live events (`segment`/`intel_status`/`intel_token`/`intel_complete`/
`meeting_updated`) through an injected `on_broadcast` callback (default no-op);
`WebRuntime` observes via `_on_meeting_broadcast`, forwarding the two events
(`intel_token`, `meeting_updated`) that were previously delivered only to the
embedded server and dead in the flagship runtime. Per **user decision**, the
embedded per-meeting web server was **dropped** (not relocated to TUI/menubar);
`config.meeting.web_enabled` is now vestigial (flagged for HS-32-06). Suite green
at 2066/14 (+3 headless tests).

**HS-32-07 shipped (2026-06-02) — user directive, "kill the TUI":** the Textual
TUI (`tui/` + `controller.py`) and the macOS menu-bar app (`menubar.py`) are
**deleted** — ~13k lines removed across code, the `tui`/`menubar` subcommands,
the `--no-tui` alias, the `textual`/`rumps` deps, the TUI/menubar-only tests, and
the dead TUI/menubar docs (+ live-doc updates). The **web runtime is now the sole
interactive runtime**. Sequenced before HS-32-03 (also user choice) so the
audio-ownership convergence has a single home — with the TUI gone,
hotkey/device/meeting capture all live only in `WebRuntime`. Suite green at
1939/14.

**HS-32-03 shipped (2026-06-02):** one audio-ownership model. `VoiceTypingSession`
gained source-less `acquire`/`release`; the meeting now holds the **shared** floor
(claimed in `_start_meeting`, released right after `session.stop()` + on shutdown),
so hotkey/device `begin()` is rejected mid-meeting and a meeting can't start while
either records (first-to-hold-wins precedence). The redundant
`_active_meeting_session()` guards in the hotkey path were **removed** — the
arbiter is the single decision point; the device path keeps its meeting-attached
*frame-routing*. New `TestAudioFloorArbitration` (7 tests incl. a 10-thread
concurrency mutual-exclusion test). Suite green at 1946/14. Real-audio paths stay
`metal`-gated (not runnable remotely).

**HS-32-04 shipped (2026-06-02):** the ungated CI core-path smoke test. A
committed 16 kHz WAV (generated once via `say` — *"the quick brown fox…"*) is run
through the **real** `Transcriber("tiny")` → `TextProcessor` → a capturing typer
(injection seam), asserting the produced text contains the phrase. It runs on the
**macOS integration job** (mlx-whisper is a core dep) on **every push** — off the
never-in-CI `metal`/`spoken_e2e` markers — and skips where no backend is
installed. Verified locally (2 passed, real mlx `tiny`); the mutation check
(silence → empty transcript → red) is shown in evidence. Suite green at 1948/14.
*Discovered:* a latent Phase-31 db-decomposition miss —
`web_runtime.py` calls `get_all_projects_for_detector()` on the `Database`
container (it moved to `db.projects`), so the project detector silently loads
nothing at startup; **fixed in a follow-up commit** (separate from the story).

**HS-32-05 shipped (2026-06-02):** one route 500-response helper. `error_500(exc,
logger, detail)` in `runtime_support.py` replaces the canonical `log.error(f"…:
{e}"); return JSONResponse({"error": str(e)}, status_code=500)` block at **48**
call sites (activity 32 / projects 8 / meetings 7 / system 1) — a change to the
error contract is now a one-line edit. Behavior byte-identical (verified). Chose
a **helper function over the deferred "decorator" default**: handlers have nested
try/except + specific non-500 handling that a whole-handler `except Exception`
decorator would swallow. Applied via a reviewed codemod (exactly the 48 expected
sites). Suite green at 1952/14.

**HS-32-06 shipped (2026-06-02) — PHASE CLOSED (7/7):** the doc-truth sweep +
drift guard. Fixed the false `DeterministicPlugin` "stub" markers in
`PLAN_ARCHITECT_PLUGIN_SYSTEM.md` (the worst rot), a dead `Branch:` header in
`PLAN_INTEL_STREAMING.md`, and retired-TUI mentions (banners on the two TUI-heavy
plans); removed the vestigial `config.meeting.web_enabled` (field + test_config +
the live `MEETING_MODE_GUIDE` example/table + a screenshot mock); refreshed the
stale `HANDOVER.md` TL;DR; and committed `tests/unit/test_doc_drift_guard.py`
(verified it catches reintroduced stub-rot). Suite green at 1954/14. See
[final-summary.md](./final-summary.md). **The whole phase is a stacked local
branch — push & open a PR to `main`.**

## Pickup order

1. ~~HS-32-01 — class-ify the runtime first; it is the substrate the inversion
   and audio-ownership stories build on.~~ **DONE (2026-06-02).**
2. ~~HS-32-02 — invert meeting→web once `WebRuntime` can hold the observer.~~
   **DONE (2026-06-02).**
3. ~~HS-32-07 — retire the TUI + menubar (inserted by user directive) so the
   audio convergence has one home.~~ **DONE (2026-06-02).**
4. ~~HS-32-03 — converge audio ownership (now `WebRuntime`-only).~~ **DONE (2026-06-02).**
5. ~~HS-32-04 — the CI smoke test (independent; most valuable early).~~ **DONE (2026-06-02).**
6. ~~HS-32-05 — the error helper (mechanical, low risk).~~ **DONE (2026-06-02).**
7. ~~HS-32-06 — doc-truth sweep + guard; last so the docs describe the post-phase
   reality.~~ **DONE (2026-06-02). PHASE CLOSED (7/7).**

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Class-ifying the runtime changes startup/shutdown ordering | Medium | Move state to instance attrs verbatim; preserve call order; web suite as gate | A lifecycle/web test fails or ordering visibly changes |
| The meeting→web inversion drops a broadcast that tests didn't cover | Medium | Add the headless-`MeetingSession` test *first*, then invert under it | A broadcast that fired before no longer fires |
| ~~Audio-ownership convergence breaks a real capture path~~ **(HS-32-03: RESOLVED — the meeting capture mechanism is unchanged; only a logical floor-acquire gate was added around it, so no real path regresses. Real-audio paths stay `metal`-gated.)** | Medium | Kept `MeetingRecorder` as-is; added `acquire`/`release` gate; arbiter unit + concurrency tests | A real-audio path can no longer acquire the recorder at all |
| ~~The CI smoke test is flaky~~ **(HS-32-04: addressed — `tiny` model (deterministic greedy decode) + a fixed committed WAV + tolerant substring assertion; runs in 1.24s locally. The only network dependency is the one-time `whisper-tiny-mlx` download on the macOS job.)** | Medium | smallest model + fixed WAV + substring tolerance | The job fails intermittently on unchanged code |

## Decisions made (this phase)

- 2026-06-02 — Doc-truth fix lives as a tracked story (HS-32-06), not an untracked
  cleanup commit — keep the change evidenced like everything else — user.
- 2026-06-02 — Scope is non-PMO docs only; the PMO historical record is kept
  verbatim by design — user.
- 2026-06-02 — **HS-32-02: drop the embedded per-meeting web server** rather than
  relocate its lifecycle into `controller.py`/`menubar.py`. Greenfield/aggressive;
  the flagship `WebRuntime` is the single dashboard owner. Consequence:
  `config.meeting.web_enabled` + its Settings toggle are now vestigial → flagged
  for HS-32-06 — user.
- 2026-06-02 — **Retire the TUI *and* the menubar (new story HS-32-07), web is the
  sole interactive runtime.** Full removal (delete, don't deprecate); sequenced
  **before** HS-32-03 so the audio convergence has one home. Includes updating all
  relevant docs. The CLI subcommands (`meeting`/`history`/`intel`/…) stay — user.

## Decisions made (continued)

- 2026-06-02 — **HS-32-04: smoke model = `tiny`** + a **checked-in** `say`-generated
  WAV (both, not either/or — the `tiny` model transcribes the committed fixture).
  Substring assertion with tolerance. (Resolves the deferred "which Whisper model"
  question.)
- 2026-06-02 — **HS-32-05: a helper *function* (`error_500`), not a decorator.**
  The deferred default was a decorator, but the route handlers have nested
  try/except + specific non-500 handling that a whole-handler `except Exception`
  decorator would swallow (violating "leave specific handling as-is"). The helper
  dedups the canonical 500 construction at each `except` instead — explicit
  per-route, behavior-preserving, low-risk. (Resolves the deferred "decorator vs
  exception handler" question — neither; a called helper.)

## Decisions deferred

- *(none open — all phase decisions resolved.)*
