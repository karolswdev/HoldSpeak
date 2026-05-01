# HS-13-02 evidence — Permission enforcement at runtime gates

## What shipped

- `holdspeak/connector_runtime.py` (new) — defines:
  - `PermissionGate(manifest)` — wraps the privileged operations
    a pack might invoke. Methods: `run_subprocess`,
    `open_outbound_socket`, `accept_loopback_event`, `read_file`.
    Each consults `_OPERATION_PERMISSIONS` (the operation →
    permission table) and raises `PermissionDenied` *before*
    delegating to the underlying call.
  - `PermissionDenied(Exception)` — operator-readable. Carries
    `connector_id`, `operation`, `required_permission`,
    `declared_permissions`. The `str(...)` form is suitable for
    direct persistence into `connector.last_error`.
  - `SubprocessRunner` type alias for the existing `run_command`
    injection point used by the gh/jira runners.
- `holdspeak/activity_github.py` — `run_github_cli_enrichment`
  routes its subprocess call through
  `PermissionGate(github_cli_pack.MANIFEST).run_subprocess(
   plan.command, runner=run_command, …)`. A `PermissionDenied`
  is caught long enough to persist `last_error` via
  `db.record_activity_enrichment_run`, then re-raised so the
  caller sees the abort. The honest path (gh manifest already
  declares `shell:exec`) is unchanged — every existing
  `test_activity_github` case still passes byte-identically.
- `holdspeak/activity_jira.py` — same wiring against the
  `jira_cli` pack manifest.
- `holdspeak/web_server.py` — the
  `/api/activity/extension/events` endpoint consults
  `PermissionGate(firefox_ext.MANIFEST).accept_loopback_event()`
  *before* parsing the payload. A pack that drops
  `loopback:http` returns 403 immediately, no event ever lands
  in the ledger.

## Acceptance criteria

- [x] `PermissionGate.run_subprocess` raises `PermissionDenied`
  when the calling pack's manifest lacks `shell:exec`.
  Verified: `test_run_subprocess_requires_shell_exec_permission`.
- [x] Same for `open_outbound_socket` (`network:outbound`),
  `accept_loopback_event` (`loopback:http`), and `read_file`
  (`fs:read`). Verified: matching `_requires_*` tests.
- [x] gh/jira pack runs route through the gate. Verified:
  `test_first_party_cli_packs_pass_run_subprocess_gate`
  (positive path) plus the existing
  `test_run_github_cli_enrichment_writes_annotations` /
  `_writes_json_annotations` cases (still pass after wiring).
- [x] A `PermissionDenied` exception bubbles up to the runtime
  and is persisted as `connector.last_error`. Verified:
  `test_run_github_cli_enrichment_persists_permission_denied` —
  monkeypatches the gh pack manifest to drop `shell:exec`,
  asserts the runner re-raises `PermissionDenied`, asserts the
  connector state's `last_error` names the missing permission.
- [x] Unit tests cover every (operation, permission) pair.
  Verified: 12 cases in `tests/unit/test_connector_runtime.py`.
- [x] Existing pack run tests still pass (the gh/jira packs
  declare the right permissions; behaviour unchanged for honest
  packs). Verified: full sweep below.

## Tests ran

```
$ uv run pytest -q tests/unit/test_connector_runtime.py \
    tests/unit/test_activity_github.py \
    tests/unit/test_activity_jira.py \
    tests/unit/test_connector_packs.py \
    tests/unit/test_activity_connector_preview.py \
    tests/unit/test_connector_fixture_harness.py \
    tests/integration/test_web_activity_api.py
88 passed in 3.16s
```

Full sweep (still excluding `tests/e2e/test_metal.py` per the
project skip list):

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1320 passed, 13 skipped in 35.73s
```

The pre-existing 13 skips (mock meeting WAV, llama-cpp /
Qwen GGUF) are unrelated to this story. +12 over the HS-13-01
total reflects the new `test_connector_runtime.py` cases plus
the `test_run_github_cli_enrichment_persists_permission_denied`
integration assertion.

## Why an in-process gate is enough (and where it isn't)

`PermissionGate` is honest enforcement, not a security
boundary — a malicious pack can still call `subprocess.run`
directly. The point of the gate is that an *honest* pack which
under-declares its permissions or invokes an operation it
doesn't claim trips loud, in tests, every time. That gives the
runtime one auditable surface ("what does this pack actually
need") for HS-13-03..05 to build settings, run history, and
local-user pack discovery on top of, without any sandbox /
subprocess-isolation work that's deliberately out-of-scope.

## Greenfield

No migrations, no shims. Existing call sites change shape
(runners route through the gate) but the test contract for
each runner — same kwargs, same `run_command` injection point,
same return shape — is byte-stable.
