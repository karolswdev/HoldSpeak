# Phase 35 — Plugin Frontier

**Status:** in-progress (opened 2026-06-03). 0/5 stories shipped.

**Last updated:** 2026-06-03 (phase opened; HS-35-01 public authoring guide first).

## Goal

Make the meeting-intel plugin system **extensible by others** — the "next frontier"
Phase 29 handed off. Externalize the contract (a public authoring guide), give it a
**pack** mechanism that mirrors the proven connector-pack precedent (manifest +
discovery loader + user packs), let a team **enable/disable** plugins per project,
and close the **incident/comms spoken-e2e** gap. Behavior of the 14 built-ins is
unchanged; the new machinery sits around them.

## Scope

### In

- **Public authoring guide (HS-35-01).** `docs/PLUGIN_AUTHORING.md` — the
  `HostPlugin` protocol (`id`/`version`/`kind`/`required_capabilities`/
  `execution_mode`/`run`), the build-prompt → LLM → parse/validate → structured
  output pattern, registering a synthesis renderer, the testing pattern (stub intel,
  fixtures), how a plugin joins a chain, and the `llm` capability gate. Mirror the
  shape of `docs/CONNECTOR_DEVELOPMENT.md`; wire into `docs/README.md` + the README
  plugin section.
- **Plugin pack manifest + discovery loader (HS-35-02).** A `PluginManifest`
  (`plugin_sdk.py`) + `plugin_pack_loader.py` mirroring the connector loader:
  first-party packs + user packs from `~/.holdspeak/plugin_packs/`
  (env-overridable), validated at load (errors surfaced, never crash), each pack
  declaring its plugin id(s)/kind/capabilities/version. The host registers
  discovered packs alongside the built-ins. **Behavior-preserving** for the 14
  built-ins.
- **Per-project plugin enable/disable (HS-35-03).** A config knob + a dispatch gate
  so a team can suppress specific plugin ids for a project/profile; the router/
  dispatch honors it; disabled plugins are skipped (not failed), surfaced in
  readiness/telemetry. Unit-tested at the routing layer.
- **Spoken-e2e breadth (HS-35-04).** A second spoken scenario (incident retro) in
  `tests/e2e/test_spoken_meeting_e2e.py` exercising the **incident + comms** chains
  (`incident_timeline`, `runbook_delta`, `risk_heatmap`, `stakeholder_update_drafter`,
  `decision_announcement_drafter`). Opt-in (`HOLDSPEAK_SPOKEN_E2E=1`) like the
  existing one.
- **Closeout (HS-35-05).** Re-verify routing invariants + suite, ruff-clean, write
  `final-summary.md`.

### Out

- **Actuators.** The host's `actuator` kind stays blocked. The authoring + pack
  contract built here is the groundwork for a later **Phase 36 — Actuators**
  (preview → human approval → external side effect; the RFC's open question #5).
- **Remote/third-party package distribution** (PyPI entry-points) — user packs from
  a local dir only, matching the connector-pack boundary.
- **Changing the 14 built-ins' behavior or the default routing output.**

## Exit criteria (evidence required)

- [ ] `docs/PLUGIN_AUTHORING.md` documents the full plugin contract + workflow;
      linked from `docs/README.md` + README; doc link-check green. (HS-35-01)
- [ ] A plugin-pack manifest + discovery loader exist (first-party + user packs);
      a fixture user pack loads + registers; bad packs surface as errors, not
      crashes; the 14 built-ins still register + route identically. (HS-35-02)
- [ ] Per-project enable/disable suppresses a plugin at dispatch (skipped, not
      failed); routing unit tests cover it. (HS-35-03)
- [ ] A second spoken-e2e scenario covers incident + comms chains. (HS-35-04)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; routing
      chain constants/tests updated in lockstep (not silenced); touched trees
      ruff-clean.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-35-01 | Public plugin-authoring guide (`docs/PLUGIN_AUTHORING.md`) | not-started | [story-01-plugin-authoring-guide.md](./story-01-plugin-authoring-guide.md) | — |
| HS-35-02 | Plugin pack manifest + discovery loader | not-started | [story-02-plugin-packs.md](./story-02-plugin-packs.md) | — |
| HS-35-03 | Per-project plugin enable/disable | not-started | [story-03-per-project-enable-disable.md](./story-03-per-project-enable-disable.md) | — |
| HS-35-04 | Spoken-e2e breadth: incident retro | not-started | [story-04-spoken-e2e-incident.md](./story-04-spoken-e2e-incident.md) | — |
| HS-35-05 | Phase closeout + final-summary | not-started | [story-05-closeout.md](./story-05-closeout.md) | — |

## Where we are

Opened 2026-06-03 right after Phase 34 closed (merged via PR #10). The decomposition
lineage (26 → 31 → 32 → 34) is complete and the project is OSS-adoptable (Phase 33),
so the highest-leverage next move is to let the community **extend** the plugin
system. The connector-pack system (`connector_pack_loader.py` + `connector_sdk.py`)
is the proven precedent to mirror for plugin packs.

## Pickup order

1. HS-35-01 — `docs/PLUGIN_AUTHORING.md`. **◀ first** (pure docs, no deps; documents
   the contract the rest of the phase formalizes).
2. HS-35-02 — plugin pack manifest + discovery loader (mirror connector packs).
3. HS-35-03 — per-project enable/disable (builds on the plugin-id model).
4. HS-35-04 — spoken-e2e incident-retro scenario.
5. HS-35-05 — closeout + final-summary.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Adding a pack/registration path changes the 14 built-ins' routing output | Medium | Keep built-ins' hardcoded registration as-is; packs *layer on*; assert the existing chain constants unchanged | `test_intent_dispatch.py` / pipeline tests diff |
| Pack discovery crashes the runtime on a bad user pack | Medium | Mirror the connector loader's "validate + surface `DiscoveryError`, never crash" contract | An import error from `~/.holdspeak/plugin_packs/` brings down startup |
| Routing chain-constant tests break on enable/disable wiring | Medium (expected) | Update `test_intent_dispatch.py` chain constants + the two full-pipeline tests in lockstep — don't silence (HANDOVER §5) | A `-k`-filtered green that hides a real diff |
| Spoken-e2e needs the LAN LLM + Chromium | High (for *running* it) | Commit the scenario module-skipped without `HOLDSPEAK_SPOKEN_E2E=1`; run it via the `.43` box (dangerouslyDisableSandbox) when verifying | n/a — it's opt-in by design |

## Decisions made (this phase)

- 2026-06-03 — **Scope = externalization** (authoring guide + packs + per-project
  enable/disable + e2e breadth); **actuators deferred to Phase 36** — decided by the
  agent (user delegated: "you decide"). Rationale: actuators need the authoring/pack
  contract + an approval flow + external egress (Phase-25 intersection), which is
  its own phase; sequencing it after this groundwork is the sound call.
- 2026-06-03 — **Mirror the connector-pack system** for plugin packs (manifest +
  local-dir discovery, no remote/PyPI), matching the existing source boundary.

## Decisions deferred

- Whether per-project enable/disable lives in config only vs. also a web-UI toggle —
  trigger: HS-35-03 — default: config knob + dispatch gate first; a web toggle is a
  thin follow-on if wanted.
- Whether the 14 built-ins get repackaged as a first-party "core" pack vs. left
  hardcoded with packs layered around — trigger: HS-35-02 — default: leave them
  hardcoded (behavior-preserving) and have packs *augment* the registry.
