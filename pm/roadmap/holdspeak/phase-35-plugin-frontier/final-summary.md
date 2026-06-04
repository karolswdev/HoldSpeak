# Phase 35 — Plugin Frontier — Final Summary

**Status:** CLOSED ✅ — 5/5 stories shipped. **Closed:** 2026-06-04.

The phase that turns the meeting-intel plugin system from a closed set of 14
hardcoded built-ins into something **others can extend** — the "next frontier"
Phase 29 handed off. The contract is now public, packs are discoverable, plugins can
be disabled per project, and the incident/comms chains have spoken end-to-end
coverage. Behavior of the 14 built-ins is **unchanged**; every new mechanism layers
*around* them. Actuators are deliberately deferred to Phase 36.

## What shipped

| Story | Target → result |
|---|---|
| **HS-35-01** | `docs/PLUGIN_AUTHORING.md` — the public authoring guide (mirrors `docs/CONNECTOR_DEVELOPMENT.md`): the `HostPlugin` protocol, the build-prompt → LLM → parse/validate → structured-output run pattern, the `llm` capability gate, registering a synthesis renderer, joining a chain, the testing pattern. Wired into `docs/README.md` + the README plugin section. |
| **HS-35-02** | The plugin-pack system mirroring connector packs — `plugin_sdk.py` (`PluginManifest` + `validate_manifest`, `actuator` kind rejected as deferred) + `plugin_pack_loader.py` (first-party + `~/.holdspeak/plugin_packs/` user-pack discovery; validate + surface `DiscoveryError`, never crash). `WebRuntime` registers packs after the built-ins. Chain hints declared/validated; live router wiring deferred to HS-35-03. |
| **HS-35-03** | Per-project enable/disable — `MeetingConfig.disabled_plugins` + a dispatch gate (`plugins/dispatch.py`) that drops disabled ids from the *executed* set and records each as a new `skipped` `PluginRun` status. `router.py` untouched → the *built* chain is byte-identical. |
| **HS-35-04** | A second opt-in spoken-meeting e2e (`test_spoken_incident_retro_end_to_end`) covering the previously-uncovered **incident + comms** chains; verified for real against `.43`. |
| **HS-35-05** | Closeout — routing invariants re-verified, this summary. |

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **2,007 passed, 15 skipped** (the spoken-e2e module skips cleanly without
  `HOLDSPEAK_SPOKEN_E2E=1`).
- **Routing invariants intact:** `test_intent_dispatch.py` / `test_intent_router.py`
  unchanged and green — the 14 built-ins register + route identically; packs and the
  disable gate sit around them. The disable gate touches only the *executed* set, not
  the *built* chain.
- **New modules ruff + F821 clean:** `plugin_sdk.py`, `plugin_pack_loader.py`,
  `plugin_packs/`, and the spoken-e2e file.
- **Doc truth:** drift-guard + the live-doc link-check green; `docs/PLUGIN_AUTHORING.md`
  matches the shipped pack/enable surface and is linked from `docs/README.md` + README.
- **Incident/comms e2e:** verified for real against `.43` (Qwen3.5-9B-Q6) — 1 passed
  in 24.14s, all five artifacts (`incident_timeline`, `runbook_delta`, `risk_register`,
  `stakeholder_update`, `decision_announcement`) produced and rendered; screenshot
  `evidence/spoken_incident_artifacts.png` (1280×3094) committed.
- **Branch:** `phase-35/hs-35-01-plugin-authoring-guide` (open of the phase + 5 story
  commits). No API/behavior change to the built-ins.

## Decisions of record

- 2026-06-03 — **Scope = externalization** (authoring guide + packs + per-project
  enable/disable + e2e breadth); **actuators deferred to Phase 36** (they need this
  groundwork + an approval flow + external egress / a Phase-25 intersection).
- 2026-06-03 — **Mirror the connector-pack system** for plugin packs (manifest +
  local-dir discovery, no remote/PyPI), matching the existing source boundary.
- 2026-06-03 — **Leave the 14 built-ins hardcoded**; packs *augment* the registry
  (behavior-preserving) rather than repackaging the built-ins as a "core" pack.
- 2026-06-03 — **Disable at dispatch, not in the router** — `skipped` is a first-class
  `PluginRun` status; the built chain stays byte-identical so the routing tests don't
  move.

## Follow-ups beyond this phase

- **Phase 36 — Actuators** (the teed-up successor): the host's `actuator` kind stays
  blocked here; the authoring + pack + manifest contract built this phase is its
  groundwork. Adds preview → human approval → external side effect (the RFC's open
  question #5; intersects Phase-25 egress posture).
- **Config silent-fallback hardening (surfaced HS-35-04, NOT fixed here).**
  `Config.load()` parses each sub-config as `MeetingConfig(**data)` inside a broad
  `except Exception: return cls()`. A single unknown/legacy key (found in the wild:
  the HS-32-06-retired `meeting.web_enabled`) makes the **entire** config silently
  fall back to defaults — e.g. a configured `intel_cloud_base_url` (`.43`) is ignored
  on every load with no error. Recommend a small hardening fix (filter unknown keys
  per sub-config, or log-and-drop the offending key instead of discarding everything).
  Foundation-hardening family (Phase 32), not plugin-frontier — left for the user to
  schedule.
- **Live router wiring for pack-declared chain hints** (deferred from HS-35-02): packs
  can declare `profiles`/`intents` but those don't yet auto-join the live router; a
  pack plugin is reachable via explicit dispatch / disable, not via profile routing.
  A thin follow-on if pack authors want declarative chain membership.
