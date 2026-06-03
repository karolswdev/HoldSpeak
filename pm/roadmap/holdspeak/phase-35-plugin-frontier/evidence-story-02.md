# Evidence — HS-35-02: Plugin pack manifest + discovery loader

**Date:** 2026-06-03. **Story:** [story-02-plugin-packs.md](./story-02-plugin-packs.md).

## What shipped

The plugin-pack system, deliberately mirroring the proven connector-pack
precedent (`connector_sdk.py` + `connector_pack_loader.py`):

- **`holdspeak/plugin_sdk.py`** — `PluginManifest` (`id`/`label`/`version`/`kind`/
  `required_capabilities`/`description`/`execution_mode` + `profiles`/`intents`
  chain hints) and `validate_manifest`, which collects **every** problem as a
  stable-`code` `ManifestError` and raises `PluginManifestError`. Kinds:
  synthesizer/validator/artifact_generator/signals/detector — `actuator` is
  intentionally rejected (`unknown_kind`) since actuators are deferred. Capabilities
  gate on `llm`. `KNOWN_PROFILES`/`KNOWN_INTENTS` are hardcoded (dependency-light) and
  guarded against router drift by a unit test.
- **`holdspeak/plugin_packs/__init__.py`** — the first-party pack slot, `ALL_PACKS = ()`
  (the 14 built-ins stay hardcoded — the behavior-preserving default).
- **`holdspeak/plugin_pack_loader.py`** — `discover_user_packs` (imports each `.py`
  in `~/.holdspeak/plugin_packs/`, env-overridable via
  `HOLDSPEAK_USER_PLUGIN_PACKS_DIR`, requiring `MANIFEST` + a callable
  `create_plugin()`), `build_registry` (first-party + user; first-party/built-in ids
  win collisions), `register_discovered_plugins` + `load_and_register_plugin_packs`
  (register pack plugins on a `PluginHost`). Every failure mode — import error,
  missing manifest/factory, invalid manifest, id collision, id/manifest mismatch,
  factory raise — is a structured `DiscoveryError`; discovery never crashes.
- **`WebRuntime`** — discovers + registers packs after `register_builtin_plugins` +
  the project detector, passing the built-in ids as `forbidden_ids`, fully wrapped so
  a bad pack only logs.
- **`tests/fixtures/plugin_packs/example_user_pack.py`** — a committed, working pack.
- **`docs/PLUGIN_AUTHORING.md`** — gained the "Plugin packs" section the HS-35-01
  forward note promised.

**Scope decision (delegated posture):** the manifest declares + validates
`profiles`/`intents` chain hints, but wiring them into the live router is deferred to
HS-35-03 (per-project enable/disable at dispatch). `router.py` is **untouched**, so
the 14 built-ins' routing is provably byte-identical.

## Tests

### New unit tests + routing regression

```
$ uv run pytest -q tests/unit/test_plugin_sdk.py tests/unit/test_plugin_pack_loader.py tests/unit/test_intent_dispatch.py
...................................                                      [100%]
35 passed in 0.10s
```

`test_plugin_pack_loader.py` covers: empty/missing dir, a valid pack loading with
`source="user"`, missing-manifest / missing-factory rejection, invalid-manifest →
`import_failed`, an importer that raises not crashing its neighbours, id collision
with a forbidden id, duplicate user ids (first wins), underscored files skipped, the
`HOLDSPEAK_USER_PLUGIN_PACKS_DIR` override, the committed fixture pack loading,
register-and-dispatch on a host (`host.execute` → `success`), id-already-on-host and
id/manifest-mismatch skips, the empty first-party registry, and the
built-ins-register-identically-with-no-packs regression. `test_intent_dispatch.py`
(the routing chain constants) is **unchanged and green**.

### Doc drift-guard + link-check (new doc links resolve)

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
...                                                                      [100%]
3 passed in 0.02s
```

### ruff + F821 on the new modules

```
$ uv run ruff check holdspeak/plugin_sdk.py holdspeak/plugin_pack_loader.py holdspeak/plugin_packs/ tests/unit/test_plugin_sdk.py tests/unit/test_plugin_pack_loader.py tests/fixtures/plugin_packs/example_user_pack.py
All checks passed!
$ uv run ruff check --select F821 holdspeak/plugin_sdk.py holdspeak/plugin_pack_loader.py
All checks passed!
```

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
...
1995 passed, 15 skipped in 48.34s
```

(+29 over HS-35-01's 1966; skips are the hardware/model-gated tests as expected on a
remote no-hardware session.)

## Done-when verification

- [x] `PluginManifest` + `plugin_pack_loader` exist; first-party + user-pack
      discovery works; bad packs surface as `DiscoveryError`s, not crashes.
- [x] A fixture user pack loads + registers with the host (and dispatches via
      `host.execute`); the 14 built-ins are unchanged — registration identical
      (`test_builtins_register_identically_with_no_packs`) and routing identical
      (`test_intent_dispatch.py` unchanged + green).
- [x] Full suite green (1995 / 15); new modules ruff + F821 clean.
