# Phase 35 — Plugin Frontier

**Status:** in-progress (opened 2026-06-03). 3/5 stories shipped.

**Last updated:** 2026-06-03 (HS-35-03 shipped — per-project plugin enable/disable:
`MeetingConfig.disabled_plugins` + a dispatch gate that records disabled plugins as
`skipped` (built chain unchanged; `router.py` untouched); HS-35-04 incident-retro
spoken-e2e next).

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
| HS-35-01 | Public plugin-authoring guide (`docs/PLUGIN_AUTHORING.md`) | done | [story-01-plugin-authoring-guide.md](./story-01-plugin-authoring-guide.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-35-02 | Plugin pack manifest + discovery loader | done | [story-02-plugin-packs.md](./story-02-plugin-packs.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-35-03 | Per-project plugin enable/disable | done | [story-03-per-project-enable-disable.md](./story-03-per-project-enable-disable.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-35-04 | Spoken-e2e breadth: incident retro | not-started | [story-04-spoken-e2e-incident.md](./story-04-spoken-e2e-incident.md) | — |
| HS-35-05 | Phase closeout + final-summary | not-started | [story-05-closeout.md](./story-05-closeout.md) | — |

## Where we are

Opened 2026-06-03 right after Phase 34 closed (merged via PR #10). The decomposition
lineage (26 → 31 → 32 → 34) is complete and the project is OSS-adoptable (Phase 33),
so the highest-leverage next move is to let the community **extend** the plugin
system. The connector-pack system (`connector_pack_loader.py` + `connector_sdk.py`)
is the proven precedent to mirror for plugin packs.

**HS-35-01 shipped (2026-06-03):** `docs/PLUGIN_AUTHORING.md` — the public
authoring guide, mirroring `docs/CONNECTOR_DEVELOPMENT.md`. Covers the `HostPlugin`
protocol (`id`/`version`/`kind`/`execution_mode`/`required_capabilities` + the
`run(context) -> dict` signature and the context dict), the reference run pattern
(JSON-only prompt → `build_configured_meeting_intel()._chat_completion_text` →
parse/validate → success/failure shapes with `confidence_hint`), the `llm`
capability gate (`resolve_llm_capability` → `enabled_capabilities` → `blocked`
skip), registering a synthesis renderer (`_ARTIFACT_TYPE_BY_PLUGIN` +
`_ARTIFACT_RENDERERS`), joining a chain (`PROFILE_PLUGIN_BASE_CHAINS` /
`_INTENT_PLUGIN_CHAIN` + the routing-ripple warning), the testing pattern (the
`intel_call` injection seam + the capability-gate test), and the "shipped" bar.
Wired into `docs/README.md` (reference index) and the README "Meeting intelligence
plugins" section. Doc drift-guard + link-check green; full suite 1966 passed /
15 skipped. Next: HS-35-02 (plugin-pack manifest + discovery loader).

**HS-35-02 shipped (2026-06-03):** the plugin-pack system, mirroring the
connector-pack precedent. `holdspeak/plugin_sdk.py` — `PluginManifest`
(`id`/`label`/`version`/`kind`/`required_capabilities`/`description`/
`execution_mode` + `profiles`/`intents` chain hints) + `validate_manifest` (collects
every error as a stable-`code` `ManifestError`; `actuator` kind rejected — deferred).
`holdspeak/plugin_pack_loader.py` — `discover_user_packs` (loads `.py` packs from
`~/.holdspeak/plugin_packs/`, env-overridable via `HOLDSPEAK_USER_PLUGIN_PACKS_DIR`,
requiring `MANIFEST` + a `create_plugin()` factory), `build_registry` (first-party +
user; first-party/built-in ids win collisions), and `register_discovered_plugins` /
`load_and_register_plugin_packs` (register pack plugins on the host with structured
`DiscoveryError`s — never crashes). `holdspeak/plugin_packs/` is the first-party slot
(empty `ALL_PACKS` — built-ins stay hardcoded). `WebRuntime` discovers + registers
packs after the built-ins, fully defensively. A committed fixture pack
(`tests/fixtures/plugin_packs/example_user_pack.py`) proves load → register →
dispatch; `test_plugin_sdk.py` + `test_plugin_pack_loader.py` cover validation,
discovery, malformed packs, collisions, and the built-ins-unchanged regression.
**Scope decision:** chain hints are declared/validated but live router wiring is
deferred to HS-35-03 — `router.py` untouched, so the 14 built-ins' routing is
byte-identical (`test_intent_dispatch.py` unchanged). `docs/PLUGIN_AUTHORING.md`
gained the promised "Plugin packs" section. Full suite 1995 passed / 15 skipped;
new modules ruff + F821 clean. Next: HS-35-03 (per-project enable/disable).

**HS-35-03 shipped (2026-06-03):** per-project plugin enable/disable. A flat config
knob `MeetingConfig.disabled_plugins: list[str]` (normalized + validated in
`__post_init__`; unknown ids are a no-op) and a **dispatch gate** in
`plugins/dispatch.py` — `dispatch_window` drops disabled ids from the *executed* set
and records each as a new `skipped` `PluginRun` status (distinct from
capability-`blocked` and ran-and-failed `error`; synthesis ignores it). `router.py`
is **untouched** so the *built* chain (`RouteDecision.plugin_chain`) and
`test_intent_dispatch.py` are unchanged. The knob threads
`dispatch_window`/`dispatch_windows` → `process_meeting_state` → `MeetingSession`
(ctor + `stop()`) → `WebRuntime` (passes `config.meeting.disabled_plugins`); `skipped`
persists via `record_plugin_run` and surfaces on `GET /api/meetings/{id}/plugin-runs`
(no new route). New `test_plugin_disable.py` (12 tests): the pure
`partition_chain`/`normalize_disabled_plugins` helpers, skip-not-execute at dispatch,
unknown-id no-op, default byte-identical, and config validation. Default (empty list)
behavior is byte-identical. Full suite 2007 passed / 15 skipped; authored files ruff
clean. `docs/PLUGIN_AUTHORING.md` gained a "Disabling a plugin per project" note.
Next: HS-35-04 (incident-retro spoken-e2e scenario).

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
