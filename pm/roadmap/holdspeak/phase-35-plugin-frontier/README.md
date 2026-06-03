# Phase 35 — Plugin Frontier

**Status:** in-progress (opened 2026-06-03; runs after Phase 34).

The meeting-intel plugin system is **internally complete** — 14 real LLM-backed
plugins, zero stubs, a clean render registry, deterministic profile/intent routing
(Phases 16 → 27 → 28 → 29). But it is **not externalizable**, which is exactly the
"next frontier" Phase 29's `final-summary.md` handed off. Now that the project is
OSS-adoptable (Phase 33) and structurally clean (Phase 34), this phase makes the
plugin system something **others can extend**:

1. **No public authoring guide.** The contract lives only in the *internal* RFC
   (`docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`); there's no
   `docs/PLUGIN_AUTHORING.md` (Phase 29 explicitly deferred it).
2. **No plugin packs / discovery.** Plugins are hardcoded in
   `holdspeak/plugins/builtin/__init__.py` — unlike the **connector** system, which
   already has a manifest + loader (`connector_sdk.py`, `connector_pack_loader.py`,
   first-party + `~/.holdspeak/connector_packs/`). Meeting-intel plugins have no
   manifest, no discovery, no user packs.
3. **No per-project enable/disable.** All chain-selected plugins fire on every saved
   meeting; a team can't suppress one.
4. **Incident/comms have no spoken-e2e coverage.** The one spoken scenario
   (`tests/e2e/test_spoken_meeting_e2e.py`) exercises balanced/architecture/
   delivery/product only — Phase 29 wanted a second (incident retro) scenario.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `../phase-29-plugin-rollout-iii-and-docs/final-summary.md` §Handoff — the frontier
  this phase discharges.
- `holdspeak/plugins/` — `host.py` (`PluginHost`, the dormant `allow_actuators`
  gate), `router.py` (`PROFILE_PLUGIN_BASE_CHAINS`), `synthesis.py` (render
  registry), `builtin/__init__.py` (hardcoded registration).
- `holdspeak/connector_pack_loader.py` + `connector_sdk.py` — the **pack precedent**
  to mirror.

## Phase boundaries

Plugin **extensibility + docs + test breadth** — no change to the 14 built-ins'
behavior or the existing routing output (a pack/enable layer sits *around* them).
**Actuators are out of scope** — the host's `actuator` kind stays blocked; this
phase builds the authoring + pack contract that a later **Phase 36 — Actuators**
(preview → human approval → external side effect) will extend. Non-hardware-gated;
the spoken-e2e scenario is opt-in (`HOLDSPEAK_SPOKEN_E2E=1`, real LAN LLM) like the
existing one.
