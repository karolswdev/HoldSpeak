# HoldSpeak — Agent Handover

**Written:** 2026-05-31. **Author of this handover:** Claude (prior session).
**Read this first**, then `pm/roadmap/holdspeak/README.md` and the active phase's
`current-phase-status.md`. This is a pickup snapshot, not canon — if it disagrees
with the live status docs, the status docs win.

---

## 1. TL;DR — where things stand

- **Branch:** `main`, clean, **`main == origin/main`** (everything is pushed; latest is the HS-26-07 closeout commit).
- **Test suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1879 passed, 0 failed, 13 skipped**.
- **Phase 26 — Web Runtime Decomposition: DONE (7/7).** `web_server.py` 5658 → 523 lines (−91%); 7 cohesive route modules under `holdspeak/web/routes/` + `WebContext` (`web/context.py`) + shared helpers (`web/runtime_support.py`); `MeetingWebServer(callbacks: WebRuntimeCallbacks, *, host, port, auth_token)` (was ~30 kwargs); all 122 routes unchanged. See the phase's `final-summary.md`. **No active phase right now** — see §3 for what to pick up.
- **Phase 25 — Trust & Hardening:** 7/8 done, functionally complete, **formally open** — only `HS-25-07` remains and it is **`blocked`** (needs in-person hardware dogfood; see §4).
- Phases **16** and **24** are `paused` (see §6); **Phase 15** (out-and-about) is `not-started` but auth-unblocked by HS-25-02.
- **Stray lint (not yours):** a pre-existing `current_time` F841 in `meeting_session.py:1277` predates Phase 26 — don't attribute it to recent work.

## 2. What happened this session (the narrative)

1. Did a full-system analysis of HoldSpeak (a sprawling solo-built voice tool: voice typing, meeting mode, dictation pipeline, activity intelligence, web runtime, AIPI-Lite hardware companion).
2. Scaffolded **Phase 25 (Trust & Hardening)** and **Phase 26 (Web Runtime Decomposition)**; reconciled stale phase states (16, 24 → `paused`).
3. Shipped **Phase 25 HS-25-01..06 + HS-25-08** (7 stories), each a PMO-gated commit with evidence.
4. Fixed a pre-existing time-bomb test; merged Phase 25 to `main`; pushed to origin.
5. Opened **Phase 26**, shipped **HS-26-01** (the router seam), pushed.

## 3. Pick up here → choose the next phase

Phase 26 is delivered and there is **no active phase**. Pick one (all are
PMO-gated, one commit per story, same cadence as the rest of this roadmap):

- **Resume Phase 24 — AI PI Companion Productization** (`paused`, 1/5 shipped).
  The web runtime is now navigable (Phase 26), which was the implicit blocker for
  comfortably extending the companion surface. Its routes live in
  `holdspeak/web/routes/system.py` (`/api/companion/status`) +
  `holdspeak/web/routes/pages.py` (`/companion`). Read
  `phase-24-ai-pi-companion-productization/current-phase-status.md`.
- **Resume Phase 16 — First Real Plugin** (`paused`, 1/5 shipped). The
  `mermaid_architecture` plugin still has a `DeterministicPlugin` stub and the LLM
  capability gate (HS-16-02) never landed; the diagram feature is not wired
  end-to-end.
- **Start Phase 15 — Out-and-About** (`not-started`). Now auth-unblocked by
  HS-25-02 (the web runtime refuses non-loopback binds without a token).
- **Unblock Phase 25 — HS-25-07** when hardware is available (§4): run the 3
  dogfood scenarios, write `evidence-story-07.md` + `final-summary.md`, close the
  phase. Code-level proof already exists in the story tests.

**Working on the web runtime now?** It's clean: route modules under
`holdspeak/web/routes/` each expose `build_*_router(ctx: WebContext)`; they import
**nothing** from `web_server`. To add a route, add a handler to the right module
(or a new `routes/<domain>.py` + `include_router` in `_create_app`), read state via
`ctx`, and grow `WebContext`/`WebRuntimeCallbacks` if a new server collaborator is
needed. Conventions: context param is `ctx` (name shadowing locals `project`);
relocate single-domain helpers into the module, put cross-cutting ones in
`web/runtime_support.py`; re-anchor `Path(__file__)` to the package dir if you move
a module; **run the full suite as the gate** (a narrow `-k` missed real bugs three
times this phase). See `phase-26-web-runtime-decomposition/final-summary.md`.

## 4. Phase 25's one open item — HS-25-07 (BLOCKED)

Everything in Phase 25 is shipped and tested **except** the closeout dogfood,
which needs **real hardware** (mic / local display / a real non-loopback bind).
**The author is currently remote (abroad, RDP) and cannot run it.** Do **not**
fabricate dogfood evidence. When hardware access returns, run the 3 scenarios and
record `evidence-story-07.md`, then write `final-summary.md` and close the phase:
1. Misconfigured local intel model + `intel_provider="local"` → confirm no
   transcript egress (`holdspeak doctor` shows "Local only").
2. Bind a non-loopback host → confirm it refuses without a token / 401s
   unauthenticated requests.
3. Force a slow/hung transcription → confirm it abandons and the next utterance works.

Code-level proof for all three already exists in the story tests.

## 5. Conventions & gotchas you MUST honor (this repo bites otherwise)

- **PMO pre-commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` with **≥7
  `[x]` checkboxes** (template in `pm/roadmap/PMO-CONTRACT.md`). The hook deletes
  it on success. A story flipping to `done` **must** ship its
  `evidence-story-{n}.md` in the **same** commit, and **only one** story may flip
  to `done` per commit (else `.tmp/BUNDLE-OK.md`).
- **Evidence files are write-once.** The hook **rejects editing an
  `evidence-story-*.md` without a matching story `done`-flip in the same commit**
  ("orphan evidence"). If you need to correct shipped evidence, put the correction
  in the *mutable* `current-phase-status.md` instead (I had to do exactly this).
- **NO `Co-Authored-By` trailer.** Repo contract rule #5 forbids unrequested
  trailers — this **overrides** the default Claude Code commit-trailer habit.
- **Agents may not use `--no-verify`.** Only the human may, in emergencies.
- **Full-suite command excludes the metal test:**
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` (it hangs without a mic).
- **`holdspeak/static/_built/` is gitignored** — built on demand by
  `hatch_build.py` / `npm run build` (in `web/`). It is **not** committed. If
  page-content tests fail locally on stale HTML, run `(cd web && npm run build)`.
- **Operating cadence:** every shipping commit updates, together: the story
  header status, the phase `current-phase-status.md` (story row + "Where we are"),
  the project `README.md` "Last updated", and any canon doc the story touches.
- **Tests must actually run** (read the output) before flipping `done` — type-check
  is not validation. This repo is greenfield-ish (`v0.2.0` is forward-looking; no
  real users) — skip backwards-compat ceremony.
- **Keep `origin` current:** the author asked that work be pushed up; push `main`
  after shipping.

## 6. Corrections of record (don't re-trust stale claims)

Two things in earlier docs/analysis were verified wrong this session — fixed in
the live status docs, but flagged here so you don't repeat them:
- **"Silent cloud egress" was NOT a live bug.** `intel_provider="local"` (the
  default) is structurally local-only (`resolve_intel_provider`); the value
  delivered (HS-25-01) was *locking that invariant* with a test, not a fix.
- **The 3 `test_activity_history` failures were NOT a "missing Safari fixture."**
  The test self-creates its fixture; the failures were a **retention time-bomb**
  (a fixed fixture `visit_time` pruned by the 30-day retention default once
  wall-clock passed it). Fixed in `278ef0e`.
- **`_built` is gitignored** (not a "stale committed bundle") — see §5.

## 7. Paused phases (context, not your job unless asked)

- **Phase 16 — first real plugin** (`mermaid_architecture`): 1/5 stories shipped
  then abandoned; the diagram feature is NOT wired end-to-end (HS-16-02 capability
  gate never landed). Paused.
- **Phase 24 — AI PI companion productization:** 1/5 shipped; paused to prioritize
  Phase 25. Resume after 25 closes.
- **Phase 15 — out-and-about (cross-network):** `not-started`. **Now auth-unblocked**
  by HS-25-02 (the web runtime refuses non-loopback binds without a token).

## 8. Useful entry points

- Roadmap: `pm/roadmap/holdspeak/README.md` (phase index + cadence).
- Methodology / rules: `pm/roadmap/roadmap-builder.md`, `pm/roadmap/PMO-CONTRACT.md`.
- Phase 26 work: `holdspeak/web_server.py`, `holdspeak/web/` (the new seam),
  `holdspeak/web_runtime.py`, `tests/integration/test_web_server.py`.
- Security posture (from HS-25-03): `docs/SECURITY.md`.
- Test commands: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (full),
  `uv run pytest -q tests/ -k doctor` (doctor).
