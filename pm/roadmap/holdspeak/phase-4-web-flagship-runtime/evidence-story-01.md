# Evidence — HS-4-01: audit + integration coverage for existing web-flagship surfaces

- **Phase:** 4 (Web Flagship Runtime + Configurability)
- **Story:** HS-4-01
- **Captured at HEAD:** `8cfd676` (pre-commit)
- **Date:** 2026-04-26

## What shipped

A new `tests/integration/test_web_flagship_audit.py` (5 tests)
covering the small set of WFS-* requirements that weren't already
explicitly asserted in the existing test suite. The audit's main
value is the requirement-to-test traceability documented below —
it confirms the runtime/CLI/meeting-control halves of WFS-01 are
*already shipped* and stable to build the WFS-CFG-* configurability
work on top of.

## WFS-* requirement coverage matrix

| Requirement | Spec line | Already covered by | New coverage in HS-4-01 |
|---|---|---|---|
| WFS-P-001 | Web UI default for `holdspeak` | `test_main_modes.py::test_main_defaults_to_web_mode` | — |
| WFS-P-002 | Meeting controls without TUI | `test_web_server.py::TestRuntimeControlEndpoints` (happy path) | `test_wfs_p_002_meeting_routes_mounted_and_return_json` (route mounted) |
| WFS-P-003 | Runtime state surface | partial via `test_web_server.py` dashboard tests | `test_wfs_p_003_runtime_state_endpoint_exposes_required_shape` (`mode="web"`, `meeting_active`, `status="ok"`) |
| WFS-P-004 | MIR-01 controls in web | `test_web_intent_controls.py` (HS-2-08 phase 2 coverage) | — |
| WFS-P-005 | Web-first docs | `README.md` "Web Runtime (Default)" section | — |
| WFS-C-001 | `holdspeak` → web | `test_main_modes.py::test_main_defaults_to_web_mode` | — |
| WFS-C-002 | `holdspeak tui` | `test_main_modes.py::test_main_tui_subcommand_routes_to_tui_mode` | — |
| WFS-C-003 | `--no-tui` deprecated | `test_main_modes.py::test_no_tui_is_deprecated_and_aliases_to_web_headless` | — |
| WFS-C-004 | Subcommands unchanged | `test_main_modes.py::test_doctor_subcommand_still_exits_with_command_return_code` + `test_meeting_subcommand_is_unchanged` | — |
| WFS-C-005 | Migration examples in docs | `README.md` Web Runtime section | — |
| WFS-R-001 | Web runtime independent of meeting | `test_web_server.py::TestDashboardLifecycleStateTransitions` | `test_wfs_r_001_r_002_idle_runtime_serves_history_and_settings` (idle access asserted explicitly) |
| WFS-R-002 | `/history` + `/settings` while idle | `test_web_server.py::TestHistoryUiSmoke` | (above) |
| WFS-R-003 | Meeting control API | `test_web_server.py::TestRuntimeControlEndpoints` | — |
| WFS-R-004 | Loopback bind default | implicit via fixture; not explicitly asserted | `test_wfs_r_004_default_host_is_loopback` + `test_wfs_r_004_explicit_host_override_honored` |
| WFS-R-005 | Graceful start/stop | `test_web_runtime_lifecycle.py` (existing) | — |
| WFS-O-001 | Mode logging | partial — not explicitly tested as "mode" string | **gap noted; deferred** (low value to add a string-match test) |
| WFS-O-002 | Startup log includes URL+bind | implicit; not explicitly asserted | **gap noted; deferred** |
| WFS-O-003 | Startup-failure remediation text | not asserted | **gap noted; deferred** |
| WFS-O-004 | Meeting persistence + intel queue not regressed | `test_intel_streaming.py` etc. (existing) | — |

## Gaps the audit found

3 WFS-O-* operational requirements aren't strictly *tested*: mode
logging consistency (O-001), startup log content (O-002),
startup-failure remediation text (O-003). These are observability
properties — easy to read by eye in `web_runtime.py`'s `log.info`
calls but not asserted in tests. **Deferred to a follow-up story** if
dogfood reveals a real gap. The audit captures them here so a
future operator doesn't think they're unknown unknowns.

## Test output

### Targeted

```
$ uv run pytest tests/integration/test_web_flagship_audit.py -v --timeout=30
... (output snipped)
collected 5 items

tests/integration/test_web_flagship_audit.py::test_wfs_r_004_default_host_is_loopback PASSED
tests/integration/test_web_flagship_audit.py::test_wfs_r_004_explicit_host_override_honored PASSED
tests/integration/test_web_flagship_audit.py::test_wfs_r_001_r_002_idle_runtime_serves_history_and_settings PASSED
tests/integration/test_web_flagship_audit.py::test_wfs_p_003_runtime_state_endpoint_exposes_required_shape PASSED
tests/integration/test_web_flagship_audit.py::test_wfs_p_002_meeting_routes_mounted_and_return_json PASSED

============================== 5 passed in 0.30s ===============================
```

### Discovered + corrected during implementation

Two of the audit tests initially failed because I'd guessed the
runtime-status payload shape and the meeting-routes status codes
without reading the source first. Both fixes were trivial after
inspecting `_normalize_runtime_status_payload` and the 501-on-no-callback
behaviour:

- `WFS-P-003` test asserted `version` or `runtime_started_at` — actual
  payload has `status="ok"` + `mode="web"` + `meeting_active`. Fixed.
- `WFS-P-002` test omitted 501 from acceptable status codes — 501 is
  the documented "callback not wired" status (not 503). Fixed.

Documented inline so the next operator doesn't guess.

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1012 passed, 13 skipped in 17.97s
```

Pass delta vs. HS-3-06 baseline (1007 passed): **+5** (5 audit
tests). 13 skipped is unchanged.

## Practical effect

HS-4-02..05 can build on the existing web-runtime surface with
confidence: the bind-address default, idle-mode serving,
meeting-control API, and CLI command contract are all under test.
Three WFS-O-* observability properties are documented as deferred
gaps — none block phase 4 progress.

## Out-of-scope (deferred per story)

- Test additions for WFS-O-001..003 (mode logging consistency,
  startup-log content, startup-failure remediation). Documented in
  this evidence file's "Gaps" section.
- Any new product code in `web_runtime.py` / `web_server.py` /
  `main.py` — the audit found no concrete bugs to fix.
- TUI execution coverage beyond what `test_main_modes.py` does
  (driving the TUI loop through tests is genuinely out of scope).
