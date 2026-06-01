# HoldSpeak — Agent Handover

**Written:** 2026-05-31. **Author of this handover:** Claude (prior session).
**Read this first**, then `pm/roadmap/holdspeak/README.md` and the active phase's
`current-phase-status.md`. This is a pickup snapshot, not canon — if it disagrees
with the live status docs, the status docs win.

---

## 1. TL;DR — where things stand

- **Branch:** `main`, clean, **`main == origin/main`** at `e5b1136` (everything is pushed).
- **Test suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1875 passed, 0 failed, 13 skipped**.
- **Active phase:** **Phase 26 — Web Runtime Decomposition** (`in-progress`, 3/7 done). **Next story: HS-26-04** (activity / connector / plugin-job routes). HS-26-02 shipped meeting/speaker/intel → `routes/meetings.py`; HS-26-03 shipped dictation/agent-hook/intent → `routes/dictation.py`. **web_server.py is now 3133 lines (was 5658).** The §3 TL;DR below describes the HS-26-02 pickup — follow the same seam pattern for HS-26-04; mind the `web_ctx` param-naming gotcha (a handler may use a local `ctx`) and run the **full** suite, not a narrow `-k`, as the gate.
- **Phase 25 — Trust & Hardening:** 7/8 done, functionally complete, **formally open** — only `HS-25-07` remains and it is **`blocked`** (needs in-person hardware dogfood; see §4).
- Phases **16** and **24** are `paused` (pre-existing work, not this session's; see §6).

## 2. What happened this session (the narrative)

1. Did a full-system analysis of HoldSpeak (a sprawling solo-built voice tool: voice typing, meeting mode, dictation pipeline, activity intelligence, web runtime, AIPI-Lite hardware companion).
2. Scaffolded **Phase 25 (Trust & Hardening)** and **Phase 26 (Web Runtime Decomposition)**; reconciled stale phase states (16, 24 → `paused`).
3. Shipped **Phase 25 HS-25-01..06 + HS-25-08** (7 stories), each a PMO-gated commit with evidence.
4. Fixed a pre-existing time-bomb test; merged Phase 25 to `main`; pushed to origin.
5. Opened **Phase 26**, shipped **HS-26-01** (the router seam), pushed.

## 3. Pick up here → HS-26-02

Phase 26 breaks the **5.6k-line `holdspeak/web_server.py`** monolith (≈125 routes
inline in one `_create_app`, 40+ constructor callbacks) into route modules,
**behavior-preserving at every step**.

**The seam is built (HS-26-01) — follow its pattern exactly:**
- `holdspeak/web/context.py` — `WebContext` dataclass: shared accessors routes
  read instead of closing over the `MeetingWebServer` instance. **Grow it one
  field per migrated concern.** It imports no route module (no cycle).
- `holdspeak/web/routes/core.py` — reference router: `build_core_router(ctx) ->
  APIRouter`. `/health` + `/api/state` live here now.
- `holdspeak/web_server.py::_create_app` mounts routers via
  `app.include_router(build_*_router(web_ctx))` (search for the `# Phase 26
  (HS-26-01)` comment to see where).

**HS-26-02 = migrate the meeting / speaker / intel route cluster** (the largest):
1. Read `story-02-meeting-routes.md` for the exact route list.
2. Create `holdspeak/web/routes/meetings.py` with `build_meetings_router(ctx)`.
3. Add the accessors those handlers need to `WebContext` (today the inline
   handlers close over `self.on_*` callbacks + `self.get_state` etc. — move the
   ones this cluster needs onto `WebContext`).
4. Move the handlers **verbatim** (don't "improve" them — that's not this phase).
5. Mount via `include_router`; delete the inline versions from `_create_app`.
6. Gate: the existing web suite must pass unchanged + the route inventory
   (paths/methods) must be identical. A quick inventory diff:
   `python -c "from holdspeak.web_server import MeetingWebServer; ..."` listing
   `app.routes` before/after — or just rely on the integration tests, which
   already exercise these paths.

Then HS-26-03 (dictation), 04 (activity), 05 (device/project), 06 (collapse the
callback bag into `WebContext`), 07 (closeout: line-count + route-inventory
evidence). Each is one PMO-gated commit.

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
