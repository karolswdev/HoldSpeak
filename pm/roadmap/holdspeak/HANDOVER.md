# HoldSpeak — Agent Handover

**Written:** 2026-06-03. **Author:** Claude (Opus 4.8 session).
**Read this first**, then `pm/roadmap/holdspeak/README.md` and the active phase's
`current-phase-status.md`. This is a pickup snapshot, not canon — if it disagrees
with the live status docs, the status docs win.

---

## 1. TL;DR — where things stand

- **Phase 31 (db decomposition): MERGED** to `main` (was PR #7). `holdspeak/db.py`
  (5,481-line god-object) → the `holdspeak/db/` package: a thin `Database`
  container + 5 repositories, migration ladder squashed to one canonical schema.
- **Phase 32 — Foundation Hardening & Doc Truth: DONE (7/7), MERGED** to `main`
  via PR #8 (all CI green, incl. the new real-Whisper smoke test on the macOS
  runner). Highlights: `web_runtime.py` → a `WebRuntime` class; `MeetingSession` is
  web-free (emits via `on_broadcast`); **the TUI *and* the macOS menubar were
  retired** (web runtime is now the *sole* interactive runtime — `tui/`,
  `controller.py`, `menubar.py`, the `tui`/`menubar` CLI, `--no-tui`, and the
  `textual`/`rumps` deps all gone; ~13k lines removed); one audio-ownership model
  (meeting holds the shared `VoiceTypingSession` floor); an **ungated CI
  core-path smoke test** (real Whisper `tiny` on a committed WAV, macOS job, every
  push); one route 500-helper (`error_500`, 48 sites); and the doc-truth sweep +
  drift guard.
- **Test suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **~1954 passed, 14 skipped** (count grew/shrank across the phase; see the latest
  story evidence for the exact number).
- **Plugins: 14 real, ZERO stubs** — locked by
  `tests/unit/test_decision_announcement_drafter_plugin.py::test_no_deterministic_stub_remains`,
  and now also guarded at the doc level by `tests/unit/test_doc_drift_guard.py`
  (no live doc may claim a `DeterministicPlugin` stub).
- **Hardware-gated, untouched:** Phase 24 (companion, 3/6), Phase 25 (HS-25-07
  dogfood), Phase 15 (out-and-about, not-started). All need the physical AI-PI / a
  real mic; the author is remote.

## 2. What happened recently

- **Phase 30 — UI/UX overhaul: DONE (9/9).** Amiga Workbench retired for "Signal".
- **Phase 31 — Database Decomposition: DONE (5/5), merged.** `db.py` → `db/`
  package (`Database` container + 5 repos); 18-version migration ladder squashed
  to one canonical schema; the `MeetingDatabase` god-class retired → `Database`.
- **Phase 32 — Foundation Hardening & Doc Truth: DONE (7/7), this session.** See §1.
  Notable user decisions: drop the embedded per-meeting web server (HS-32-02); kill
  the TUI **and** the menubar (HS-32-07); a helper *function* over a decorator for
  the route 500s (HS-32-05).

## 3. Pick up here

**▶ Phase 36 — Meeting Intelligence & Experience is OPEN (0/6), on local branch
`phase-36/hs-36-01-artifact-card-shell`** (folder slug `phase-36-meeting-artifact-experience`
predates a same-day scope expansion). On direct user feedback, two tracks:

- **Experience (HS-36-01→03):** the artifact rendering is basic, has no copy affordance,
  and overflows horizontally. Make it a first-class deliverable — Signal **"elevated"
  artifact cards**, **copy-as-Markdown** (reuse `CommandPreview.astro`), **overflow-safe**
  wide artifacts (the risk table first). UI lives in `web/src/pages/history.astro`
  (~856–1136) + its CSS; rebuild the bundle (`cd web && npm run build`) before
  verifying — `holdspeak/static/_built/` is **gitignored** (built at install from
  `web/src`), so commit the **source**, never `_built`.
- **Intelligence (HS-36-04→05):** fix the routing weakness where a brief intent in a
  digression is **diluted below the 0.6 threshold and silently lost** (MIR-01 =
  fixed-90s windows + lexical keywords; see `intent_timeline.build_intent_windows`,
  `plugins/signals.extract_intent_signals`, `plugins/router.select_active_intents`,
  `plugins/dispatch`, `plugins/pipeline.process_meeting_state`). HS-36-04 adds a
  **dynamic/messy multi-topic spoken-e2e** driving the *real* routing path + captures a
  **BEFORE** screenshot; HS-36-05 implements **segment-aware per-segment intent probing**
  (LLM-assisted via `intel.build_configured_meeting_intel`, with the lexical scorer as a
  deterministic fallback; union-aggregate) + captures the **AFTER**.

**Headline deliverable:** a **before/after** of the same messy meeting (old routing
sparse → new routing rich), presented at closeout (HS-36-06). Start with **HS-36-01**
(most visible win). Full plan: `phase-36-meeting-artifact-experience/current-phase-status.md`.
**Update in lockstep, don't silence:** the spoken-e2e artifact selectors
(`.risk-table tbody tr`, `.incident-timeline li`, …) AND the routing tests
(`test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing`).

**Phase 35 — Plugin Frontier: CLOSED ✅ (5/5), merged via PR #11.** The plugin system
is externalizable end-to-end: public `docs/PLUGIN_AUTHORING.md`, a plugin-pack manifest
+ discovery loader (`plugin_sdk.py` / `plugin_pack_loader.py`, first-party +
`~/.holdspeak/plugin_packs/`), per-project enable/disable (a `skipped` dispatch gate;
`router.py` untouched), and a second spoken-e2e (incident + comms, verified on `.43`).
Full record: `phase-35-plugin-frontier/final-summary.md`.

**Phase 37 — Actuators** is the teed-up successor (renumbered from 36 when the artifact
UX phase took the 36 slot): the host's `actuator` kind stays **blocked** today; Phase 35
built its groundwork (the authoring + pack + manifest contract). Phase 37 adds preview →
human approval → external side effect (RFC open question #5; intersects the Phase-25
egress posture). Scaffold a phase folder + stories when starting.

> **▶ Config hardening — DONE (merged PR #12):** `Config.load()` now filters unknown/
> legacy keys per sub-config (the HS-32-06-retired `meeting.web_enabled` no longer nukes
> the whole config) and logs the last-resort fallback instead of swallowing it. The
> earlier "silently discards the whole config" hazard is resolved.

> **▶ Routing ripple (HANDOVER §5):** adding/suppressing a plugin in a chain touches
> `tests/unit/test_intent_dispatch.py` (chain constants + window counts) +
> `test_intent_pipeline.py` / `test_multi_intent_routing.py` — update in lockstep,
> don't silence. The connector-pack system is the precedent to mirror.

> **▶ Earlier (both merged to `main`):** Phase 33 (Documentation & OSS readiness,
> PR #9) — Apache-2.0 LICENSE, `docs/MODELS.md`, `docs/` reorg, OSS README +
> CHANGELOG/CONTRIBUTING, brand mark + social card. Phase 34 (Structural
> Decomposition II, PR #10) — the four god-files (5,373 lines) → four packages
> (`routes/dictation/`, `routes/activity/`, `agent_context/`, `intel/`),
> behavior-preserving. The decomposition lineage (26 → 31 → 32 → 34) is complete.

> **▶ Manual follow-up (not a repo file):** set
> `docs/assets/pixellab/social-card.png` as the repo's GitHub social preview
> (*Settings → Social preview*). Cutting an actual release (tag + PyPI) is a
> deliberate future follow-up — Phase 33 made the positioning *honest*, not
> *published*.

> **▶ pixellab MCP** (for future asset work): record each asset's object ID +
> prompt in `docs/assets/pixellab/README.md`; derived (composed) assets like the
> social card are reproduced via `docs/assets/pixellab/compose_og_card.py`.

> **▶ Note for a remote (no-hardware) session:** the real-audio capture paths
> (`metal`) can't run here; the HS-32-04 smoke test covers real transcription on a
> committed WAV instead. Anything touching the AI-PI or a live mic stays gated.

> **Historical:** Phases 31 (db decomposition) and 32 (foundation hardening +
> TUI/menubar retirement) are both **merged to `main`** (PRs #7 and #8). Their
> `final-summary.md` files record the exit state.

## 4. The persistence layer (Phase 31 — how it's shaped now)

`holdspeak/db/` package (was the single `db.py`):

- `core.py` — the **`Database` container**: owns the one sqlite connection
  (`_connection`), builds the schema (`_ensure_schema` / `_apply_schema` →
  `SCHEMA_SQL`), holds the `get_database()` singleton. **No domain methods.** It
  constructs the repos: `self.meetings / .intel / .plugins / .projects / .activity`.
- `meetings.py` `MeetingRepository` — meetings, segments, speakers, topics,
  bookmarks, action items, **and intel snapshots** (embedded in `MeetingState`).
- `intel.py` `IntelRepository` — the deferred-intel **jobs/attempts queue**.
- `plugins.py` `PluginArtifactRepository` — intent windows, plugin runs/jobs, artifacts.
- `projects.py` `ProjectRepository` — projects, associations, detection log.
- `activity.py` `ActivityRepository` — the local activity-intelligence ledger.
- `models.py` — all dataclasses + validation constants (shared; breaks the cycle).
- `base.py` — `BaseRepository`: connection factory, the `_json_*` helpers, and a
  **container back-reference `self._db`** for the rare cross-domain call (e.g.
  `intel.requeue_intel_job` → `self._db.meetings.get_meeting`; an activity rule →
  `self._db.projects.get_project`).
- `__init__.py` — re-exports the full public surface, so `from holdspeak.db import X`
  is unchanged. **Call domain methods as `db.<repo>.<method>(...)`**, not `db.<method>`.

The fresh-build schema is pinned by `tests/fixtures/db_schema_canonical.txt` +
`TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` — **any schema
change must regenerate that snapshot in the same commit.**

## 5. Conventions & gotchas you MUST honor (this repo bites otherwise)

- **PMO pre-commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` with **≥7
  `[x]`** (template in `pm/roadmap/PMO-CONTRACT.md`). A story flipping to `done`
  ships its `evidence-story-{n}.md` in the **same** commit; **one** `done`-flip per
  commit (else write `.tmp/BUNDLE-OK.md`). Phase-exit stories need an
  `evidence-story-{n}.md` **in addition to** `final-summary.md` (the hook enforces
  the forward pairing). The story Status line must be the list-item form
  `- **Status:** done` or the hook won't detect the flip.
- **`.tmp/` is not auto-created** — `mkdir -p .tmp` before writing the contract.
- **NO `Co-Authored-By` trailer.** Repo rule #5 — overrides the default habit.
- **No `--no-verify`.**
- **Full-suite gate:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the
  metal file hangs without a real mic). Run the **whole** suite — `-k` filters miss
  real bugs. The db package must stay **ruff-clean** (`uv run ruff check holdspeak/db/`).
- **`python` is not on PATH — use `python3`.**
- **Routing ripple:** adding a plugin to a base chain breaks
  `tests/unit/test_intent_dispatch.py` (chain constant + window counts) and the two
  full-pipeline tests (`test_intent_pipeline.py`, `test_multi_intent_routing.py` —
  they register the *union* of plugin IDs as stubs). Update those; don't silence.
- **LAN endpoint + sandbox:** intel runs on `.43:8080` (LAN, Qwen3.5-9B-Q6).
  **Sandboxed Bash can't reach the LAN** → use `dangerouslyDisableSandbox: true`
  for any command that hits `.43` / the spoken e2e / a real plugin call. Memory
  `reference-lan-llm-endpoint`.
- **Spoken e2e is opt-in:** `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`;
  module-skips otherwise. Playwright/Chromium are transient installs (not in
  `pyproject.toml`).
- **`holdspeak/static/_built/` is gitignored** — `(cd web && npm run build)` after
  editing anything under `web/` (Node ≥ 22.12; CI uses Node 22). Page-content tests
  read the built JS.
- **Operating cadence:** every shipping commit updates the story header, the phase
  `current-phase-status.md` (row + Last-updated + "Where we are"), the project
  `README.md` (phase row + Last-updated + Current-phase), and any canon doc touched.

## 6. Decomposition lessons (Phase 31 — don't relearn the hard way)

- **Verbatim moves still need their imports.** Splitting a module drops relative
  imports one level (`from .x` → `from ..x`) and the per-domain module needs its own
  `import uuid` / `import json` / `from urllib.parse import …`. Run `ruff --select F821`
  on a new module to surface every undefined name at once.
- **External code called *private* db helpers** (`db._normalize_activity_url`) and
  held the db under odd receivers (`self._db`, `kwargs["db"]`, `activity_db`). A
  name-based call-site sweep misses these — the full suite is what caught them.
- **Test doubles need repo properties.** A fake db stubbing domain methods needs
  `meetings = property(lambda self: self)` (and `intel`/`plugins`/`projects`/`activity`
  as used) so `db.<repo>.<method>` resolves back to the fake.
- **Monkeypatch targets follow the symbol.** `DEFAULT_DB_PATH` moved to
  `holdspeak.db.core`; tests patching the package namespace had to patch `core`.

## 7. Decisions of record (recent)

- **Greenfield/aggressive** is the standing posture (one user, one dev DB,
  destructive-OK): Phase 31 deleted the god-class with no alias, squashed migrations
  with no upgrade path, rebuilt the dev DB. Memory `feedback_holdspeak_not_really_released`.
- **`intel_snapshots` live with `MeetingRepository`** (embedded in `MeetingState`),
  not `IntelRepository`.
- **Container back-reference (`self._db`)** is the cross-domain repo-call pattern.
- Intel runs on **`.43` Q6**; the localhost Q4 reasoning-leak is a non-issue (memory
  `project-intel-use-43-q6`).

## 8. Useful entry points

- Roadmap: `pm/roadmap/holdspeak/README.md` (phase index + Current-phase).
- Active phase: `phase-32-foundation-hardening/` (status + 6 story files).
- Just-closed phase: `phase-31-database-decomposition/final-summary.md`.
- Persistence: `holdspeak/db/` (container `core.py`; repos `meetings/intel/plugins/projects/activity.py`).
- Plugin reference impls: `holdspeak/plugins/builtin/{mermaid_architecture,action_owner_enforcer,decision_capture}.py`; registrar `builtin/__init__.py`.
- Synthesis + render: `holdspeak/plugins/synthesis.py`, `web/src/pages/history.astro`, `web/src/scripts/history-app.js`.
- Test commands: full `uv run pytest -q --ignore=tests/e2e/test_metal.py`; spoken e2e `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`.
