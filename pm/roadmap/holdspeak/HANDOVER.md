# HoldSpeak — Agent Handover

**Written:** 2026-06-01. **Author:** Claude (Opus 4.8 session).
**Read this first**, then `pm/roadmap/holdspeak/README.md` and the active phase's
`current-phase-status.md`. This is a pickup snapshot, not canon — if it disagrees
with the live status docs, the status docs win.

---

## 1. TL;DR — where things stand

- **Branch:** `main`, clean, **`main == origin/main`** (everything pushed; HEAD = `d26f071`).
- **Test suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1926 passed, 14 skipped**. (One of the 14 skips is the new opt-in spoken e2e — see §5.)
- **Phase 16 — First Real Plugin: DONE (5/5).** The whole transcript→LLM→artifact→rendered path is live for `mermaid_architecture`. See its `final-summary.md`.
- **Phase 27 — Ubiquitous plugins + spoken e2e: IN-PROGRESS (3/5).** `action_owner_enforcer` (HS-27-01), the spoken e2e harness (HS-27-02), and `decision_capture` (HS-27-03) shipped. **Pick up at HS-27-04** (see §3).
- **Three real LLM-backed plugins now ship** (mermaid_architecture, action_owner_enforcer, decision_capture); the other 11 `_BUILTIN_PLUGIN_DEFS` entries are still `DeterministicPlugin` stubs.
- Phases **24** (companion, 2/5) and **25** (HS-25-07) are **hardware-gated** (need the physical AI PI / a real mic). **Phase 15** (out-and-about) is `not-started`, software-only.

## 2. What happened this session

A long build session, all on `main`, all PMO-gated + pushed:
1. **HS-24-02** — companion lifecycle controls (select/dismiss/pin/clear-stale on `/companion`). [`a1c3948`]
2. **intel self-hosted key fix** — a custom `intel_cloud_base_url` no longer requires `$OPENAI_API_KEY`. [`7f03008`]
3. **Phase 16 closed (HS-16-02..05)** — LLM capability gate, diagram artifact body, inline-SVG web render (mermaid.js), RFC reality-check + calibration + final-summary.
4. **Phase 27 scaffolded** (`987106d`) then **HS-27-01/02/03 shipped** + a second intel fix (`fe9c0e8`, see §6).

## 3. Pick up here → HS-27-04 (`requirements_extractor`)

> **▶ Phase 27 → HS-27-04 — flip the `requirements_extractor` stub to real**, with
> its own structured web render. Story:
> `phase-27-ubiquitous-plugins-and-e2e/story-04-requirements-extractor.md`.
> Then **HS-27-05** closes the phase (incl. the RFC reality-status refresh).

**The pattern is now well-trodden — copy it.** For a new/flipped plugin:
1. New plugin class in `holdspeak/plugins/builtin/<id>.py` — mirror
   `action_owner_enforcer.py` / `decision_capture.py` (strict prompt → single
   fenced ```json → a `_extract_*` parser → success/failure shape; deferred;
   `required_capabilities=["llm"]`; default `_call_intel` uses
   `build_configured_meeting_intel()`).
2. Register in `builtin/__init__.py`: add to `_REAL_PLUGINS` (and add a
   `_BUILTIN_PLUGIN_DEFS` entry only if net-new — `requirements_extractor`
   already has one).
3. `synthesis.py`: it already maps `requirements_extractor → "requirements"`; add
   a strict body branch + `structured_json["requirements"]` (keep other bodies
   byte-for-byte unchanged).
4. **Structured web render** in `web/src/pages/history.astro` +
   `web/src/scripts/history-app.js` (a `requirementsFor(artifact)` helper + an
   `x-for` list). **Do NOT lean on the raw `body_markdown` plain-text path** —
   that was the HS-27-02 mistake (see §6). Then `(cd web && npm run build)`.
5. Tests: a plugin unit suite (mirror `test_decision_capture_plugin.py`) + a
   synthesis body case in `test_artifact_synthesis_diagram.py`.
6. **If you route it into a base chain, expect a routing ripple** (see §5) — update
   `test_intent_dispatch.py` + the two full-pipeline tests' stub unions.
7. Extend the spoken e2e (`tests/e2e/test_spoken_meeting_e2e.py`) to run it + a
   Playwright wait/assert, and re-shoot the screenshot.

## 4. The plugin pipeline (how it actually works now)

- **Registrar:** `holdspeak/plugins/builtin/__init__.py` — `_REAL_PLUGINS` maps
  IDs to real classes; everything else is a `DeterministicPlugin` stub.
- **Provider:** plugins call `intel.build_configured_meeting_intel()` → reads
  `Config.load().meeting` → talks to the configured endpoint (the self-hosted
  **`.43:8080` Qwen3.5-9B-Q6**). The `"llm"` capability is gated on at the
  `PluginHost` site in `web_runtime.py` via `resolve_llm_capability` (HS-16-02).
- **Routing:** `holdspeak/plugins/router.py` — `PROFILE_PLUGIN_BASE_CHAINS`
  (per-profile, intent-independent) + `_INTENT_PLUGIN_CHAIN`. `decision_capture`
  rides the `balanced` (default) base chain.
- **Synthesis → artifacts:** `holdspeak/plugins/synthesis.py`
  (`synthesize_meeting_artifacts` / `synthesize_and_persist`) — per-type body
  branches (`diagram`, `action_items`, `decisions`) + `structured_json`.
- **Web render:** `/history` meeting-detail modal renders `diagram` as SVG,
  `action_items` + `decisions` as structured lists, everything else as
  `body_markdown` text.

## 5. Conventions & gotchas you MUST honor (this repo bites otherwise)

- **PMO pre-commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` with **≥7
  `[x]`** (template in `pm/roadmap/PMO-CONTRACT.md`). A story flipping to `done`
  ships its `evidence-story-{n}.md` in the **same** commit; **one** `done`-flip
  per commit. Phase-exit stories still need an `evidence-story-{n}.md` (the hook
  enforces it) **in addition to** `final-summary.md`.
- **NO `Co-Authored-By` trailer.** Repo rule #5 — overrides the default habit.
- **Agents may not use `--no-verify`.**
- **Full-suite gate:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Run the
  **whole** suite — narrow `-k` filters miss real bugs.
- **Routing ripple:** adding a plugin to a base chain changes the dispatched chain,
  which breaks `tests/unit/test_intent_dispatch.py` (chain constant + window
  counts) and the two full-pipeline tests (`test_intent_pipeline.py`,
  `test_multi_intent_routing.py` — they register the *union* of plugin IDs as
  stubs). Update those stub lists + counts; don't silence.
- **LAN endpoint + sandbox:** intel runs on `.43:8080` (LAN). **Sandboxed Bash
  can't reach the LAN** → use `dangerouslyDisableSandbox: true` for any command
  that hits `.43` (or runs the spoken e2e / a real plugin call). See memory
  `reference-lan-llm-endpoint`.
- **The spoken e2e is opt-in:** `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m
  spoken_e2e -s`. It module-skips otherwise (so the default sweep never runs it),
  and skips cleanly if `say` / scipy / Playwright+Chromium / `.43` / Whisper are
  absent. **Playwright is a transient install** (`uv pip install playwright &&
  playwright install chromium`) — NOT declared in `pyproject.toml` yet (open
  question in story-02; consider a dev/e2e extra). Chromium lives in
  `~/.cache/...`; a fresh clone must reinstall.
- **`holdspeak/static/_built/` is gitignored** — `(cd web && npm run build)` after
  editing anything under `web/`. Page-content tests read the built JS.
- **Operating cadence:** every shipping commit updates the story header, the phase
  `current-phase-status.md` (row + Last-updated + "Where we are"), the project
  `README.md` (phase row + Last-updated + Current-phase), and any canon doc the
  story touches.

## 6. Two real bugs the work surfaced this session (don't reintroduce)

- **Plugins ignored the configured provider.** `register_builtin_plugins` built a
  bare `MeetingIntel()` (module defaults), so in the *real runtime* the plugins
  never used the `.43` config and silently returned their failure shape. Fixed by
  `build_configured_meeting_intel()` (`fe9c0e8`). **Lesson:** test the real wiring,
  not just an injected `intel_call` override — the spoken e2e is what caught this.
- **Text artifacts rendered as a raw-markdown blob.** `/history` dumped
  `body_markdown` via a plain-text binding, so `action_items` showed as collapsed
  `### … - [ ] … ⚠️ missing both`. Fixed with a structured render. **Lesson:**
  any new text-output plugin ships a structured web render; never the raw
  `body_markdown` path. (Also: `MeetingState.started_at` must be a **naive**
  datetime — the codebase's duration math uses `datetime.now()`.)

## 7. Decisions of record (from this session)

- **Intel runs on `.43` Q6; the localhost `:8081` Q4 reasoning-leak is a
  non-issue** — don't build `reasoning_content` fallback extraction (memory
  `project-intel-use-43-q6`).
- **Phase 27 ships both `decision_capture` and `requirements_extractor`**; the
  spoken e2e is a **pytest test** (Playwright), not just a script.
- **"Phase 17" is taken** (`phase-17-device-initiative`, done) — the
  plugin-rollout follow-on to Phase 16 is **Phase 27**.

## 8. Useful entry points

- Roadmap: `pm/roadmap/holdspeak/README.md` (phase index + Current-phase).
- Active phase: `phase-27-ubiquitous-plugins-and-e2e/` (status + 5 story files).
- Plugin reference impls: `holdspeak/plugins/builtin/{mermaid_architecture,action_owner_enforcer,decision_capture}.py`.
- Synthesis + render: `holdspeak/plugins/synthesis.py`, `web/src/pages/history.astro`, `web/src/scripts/history-app.js`.
- The spoken e2e (living demo): `tests/e2e/test_spoken_meeting_e2e.py`; latest screenshot `phase-27-…/evidence/spoken_meeting_artifacts.png`.
- Parent RFC (reality-status table + Appendix A): `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`.
- Test commands: full `uv run pytest -q --ignore=tests/e2e/test_metal.py`; spoken e2e `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`.
