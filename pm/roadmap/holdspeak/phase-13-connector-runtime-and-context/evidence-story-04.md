# HS-13-04 evidence — Local-user pack discovery

## What shipped

- `holdspeak/connector_pack_loader.py` (new)
  - `RegisteredPack(manifest, source, module, file_path)` —
    runtime view of one pack the registry knows about.
  - `DiscoveryError(file_path, pack_id, code, message)` —
    structured rejection report. Codes: `import_failed`,
    `no_manifest`, `id_collision_first_party`,
    `id_collision_user_pack`, `not_a_directory`, plus the
    per-field codes the manifest validator already emits.
  - `DiscoveryResult(packs, errors)` with a `by_id()` helper.
  - `discover_user_packs(directory, *, forbidden_ids)` —
    walks the dir, imports each `.py` (skipping `_*.py` and
    `__init__.py`), validates the `MANIFEST`, never raises.
  - `build_registry(user_packs_dir=None)` — first-party
    (from `connector_packs.ALL_PACKS`) + user (from the
    discovered dir or env-var override). First-party always
    wins on id collisions.
  - `DEFAULT_USER_PACK_DIR = ~/.holdspeak/connector_packs`.
    `HOLDSPEAK_USER_PACKS_DIR` env var overrides it; unit
    tests pass `user_packs_dir=tmp_path/...` directly.
- `holdspeak/activity_connectors.py` — rewired to call
  `build_registry()` at import time. New module-level
  `_DISCOVERY` carries the latest `DiscoveryResult`.
  `reload_registry(user_packs_dir=...)` recomputes the
  module-level globals (`KNOWN_CONNECTORS`,
  `KNOWN_CONNECTOR_IDS`); `discovery_errors()` exposes the
  rejected packs. `ConnectorDescriptor` gained a `source`
  field (`"first-party"` / `"user"`).
- `holdspeak/web_server.py` — the connectors list payload
  surfaces `descriptor.source` so the browser can label each
  connector by provenance.
- `holdspeak/commands/doctor.py`
  - `_check_connector_packs()` — new doctor check listing
    every discovered pack by source. WARN if any discovery
    error is present, with the rejection reasons in `fix`.
  - `run_connector_packs_listing()` — focused listing for
    `holdspeak doctor --connectors`. Prints every registered
    pack with its source / kind / file path; exits 0 when no
    discovery errors, 1 otherwise.
- `holdspeak/main.py` — doctor subparser gains
  `--connectors`, dispatched in `run_doctor_command`.

## Acceptance criteria

- [x] Dropping a valid `.py` file into
  `~/.holdspeak/connector_packs/` causes the runtime to pick
  it up on next start. Verified:
  `test_valid_user_pack_loads_with_user_source` and
  `test_reload_registry_picks_up_user_packs` (the latter
  exercises the same code path through
  `activity_connectors.reload_registry`).
- [x] An invalid manifest rejects the pack with a structured
  error message; the runtime still starts. Verified:
  `test_invalid_manifest_is_rejected_with_structured_error`,
  `test_pack_without_manifest_is_rejected`,
  `test_pack_that_raises_at_import_does_not_crash`.
- [x] An id collision with a first-party pack rejects the
  user pack and logs a warning; the first-party pack wins.
  Verified: `test_id_collision_with_first_party_rejects_user_pack`
  asserts `code == "id_collision_first_party"` and the user
  pack does not appear in the registry.
- [x] `/activity` Connectors panel shows the pack's source
  (first-party / user). Verified at the API layer:
  `test_connector_list_includes_calendar_with_capabilities`
  now also asserts each connector's `source == "first-party"`.
  The browser already fans the API payload into the UI; the
  field rides through unchanged.
- [x] `holdspeak doctor` lists every pack + state.
  Verified: `test_check_connector_packs_passes_with_only_first_party`,
  `test_check_connector_packs_warns_on_user_pack_errors`,
  plus the focused-listing tests
  `test_run_connector_packs_listing_returns_zero_with_no_errors`
  and `test_run_connector_packs_listing_returns_one_when_errors_present`.

## Tests ran

```
$ uv run pytest -q tests/unit/test_connector_pack_loader.py \
    tests/unit/test_doctor_command.py
40 passed in 0.31s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1356 passed, 13 skipped in 30.29s
```

The pre-existing 13 skips (mock meeting WAV, llama-cpp /
Qwen GGUF) are unrelated. +14 over HS-13-03 reflects the new
loader cases (10), the four new doctor cases, and the
`source` assertion added to the existing connector-list
integration test.

## Trust boundary, not a sandbox

The loader runs every user pack as in-process Python. That
is intentional and stated in the story notes: a file under
`~/.holdspeak/connector_packs/` is by definition code the
user has chosen to trust on their own machine. Adding a
subprocess sandbox here would be ceremony, not safety; the
local-only single-user model already binds the trust to the
filesystem permissions on the home directory.

The loader's contributions to safety are honest — not
isolation:

  - every pack import is captured; one bad file cannot crash
    discovery,
  - manifest validation runs once at load time so a pack
    cannot ship with unknown permissions / mistyped fields,
  - first-party ids are reserved (collisions are rejected),
  - permission gates from HS-13-02 apply uniformly regardless
    of `source`, so a user pack that omits `shell:exec` still
    can't shell out.

## Greenfield

No migrations; the loader is purely additive. The default
user-pack dir does not exist on a fresh install, so
`discover_user_packs` returns `((), ())` and the registry is
the four first-party packs exactly as before.
