# HS-35-02 — Plugin pack manifest + discovery loader

- **Status:** done (2026-06-03). Evidence: [evidence-story-02.md](./evidence-story-02.md).

## Goal

Meeting-intel plugins are hardcoded in `holdspeak/plugins/builtin/__init__.py` — no
manifest, no discovery, no user packs. The **connector** system already solves this
(`connector_sdk.py` + `connector_pack_loader.py`). Give plugins the same: a manifest
+ a discovery loader for first-party and user packs, so a plugin can ship outside
the built-in set without editing core.

## Scope

- **`PluginManifest`** (`holdspeak/plugin_sdk.py`, mirroring `ConnectorManifest`):
  `id` (`^[a-z][a-z0-9_]{0,31}$`), `label`, `version` (semver), `kind` (validator /
  synthesizer / artifact_generator / …), `required_capabilities`, optional
  `description`, and how it exposes its plugin class/factory + chain hints
  (profile/intent it fires on).
- **`holdspeak/plugin_pack_loader.py`** (mirroring `connector_pack_loader.py`):
  - first-party packs (a `holdspeak/plugin_packs/` dir, each exporting
    `MANIFEST: PluginManifest` + its plugin class), imported eagerly;
  - user packs from `~/.holdspeak/plugin_packs/*.py` (env-overridable, e.g.
    `HOLDSPEAK_USER_PLUGIN_PACKS_DIR`);
  - validate each at load; a bad pack surfaces a `DiscoveryError`, **never crashes**
    the runtime; record `source` ("first-party"/"user"), module, file path.
- **Host registration** — discovered packs' plugins register with `PluginHost`
  alongside the built-ins. **Behavior-preserving:** the 14 built-ins keep their
  current hardcoded registration + routing; packs *augment* the registry (default
  decision: built-ins stay hardcoded — see status doc).
- A **fixture user pack** under `tests/fixtures/` proving load → register → (if
  chain-eligible) dispatch, plus a malformed-pack test proving graceful surfacing.

## Test plan

- Unit: manifest validation (good/bad ids, versions, kinds); loader discovery
  (first-party + a temp user-pack dir via the env override); malformed pack →
  `DiscoveryError`, runtime intact.
- Regression: the 14 built-ins still register and the existing chain constants
  (`test_intent_dispatch.py`) are unchanged.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Done when

- [x] `PluginManifest` + `plugin_pack_loader` exist; first-party + user-pack
      discovery works; bad packs surface as errors, not crashes.
- [x] A fixture user pack loads + registers with the host; the 14 built-ins are
      unchanged (registration + routing identical).
- [x] Full suite green; new modules ruff-clean.

## Notes

- **Scope decision (agent, delegated posture):** chain hints (`profiles`/`intents`)
  are declared + validated on the manifest, but live wiring into the router/dispatch
  chain is **deferred to HS-35-03** ("the router/dispatch honors it" — per-project
  enable/disable). This keeps `router.py` untouched so the 14 built-ins' routing is
  provably byte-identical (no `test_intent_dispatch.py` churn), matching the status
  doc's risk-table mitigation. A pack plugin registers on the host and dispatches by
  id today; HS-35-03 consumes the hints.
- The 14 built-ins stay **hardcoded** (the deferred default in the status doc);
  `holdspeak/plugin_packs/ALL_PACKS` is empty — packs *augment* the registry.
- `docs/PLUGIN_AUTHORING.md` gained the promised "Plugin packs" section (the HS-35-01
  forward note is now fulfilled, not stale).
