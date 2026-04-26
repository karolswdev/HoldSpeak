# Phase WFS-01: Web Flagship Runtime and UX Migration

## 1. Phase Charter

### 1.1 Objective

Make the web interface the primary product surface and runtime entrypoint for HoldSpeak, with TUI retained as secondary/legacy.

### 1.2 Rationale

Current behavior still centers the TUI (`holdspeak` launches terminal UI), while web capabilities are rich but mostly attached to meeting sessions. This creates product-direction drift and slows delivery of plugin-centric workflows.

### 1.3 Phase-Level Outcomes

1. `holdspeak` defaults to web-first operation.
2. Web control plane runs independently of active meetings.
3. Core workflows are operable from browser without requiring TUI.
4. TUI remains available as explicit fallback (`holdspeak tui`) and does not block new feature delivery.

## 2. Scope

### 2.1 In Scope

1. CLI command-contract migration to web-first defaults.
2. Always-on local web control plane runtime.
3. Browser-first meeting lifecycle control.
4. Browser-first access to MIR-01 controls (intent timeline, routing profile, overrides).
5. Backward-compatible migration path and user messaging.
6. Test and evidence framework for web-first acceptance.

### 2.2 Out of Scope

1. Removal of TUI codebase.
2. Full redesign of web visual system.
3. Cloud-hosted multi-user deployment.

## 3. Normative Command Contract

These command semantics are mandatory for WFS-01 completion.

1. `holdspeak`
- MUST start the web flagship runtime.
- SHOULD auto-open browser when configured.

2. `holdspeak web`
- MUST explicitly start web flagship runtime.
- MUST support `--no-open` for headless local service mode.

3. `holdspeak tui`
- MUST explicitly start existing TUI experience.
- MUST remain functional for compatibility.

4. `holdspeak --no-tui`
- MUST be deprecated with clear guidance.
- MAY remain as alias to `holdspeak web --no-open` for one transition release.

## 4. Architecture Delta

### 4.1 Required Runtime Separation

Web server lifecycle MUST be decoupled from `MeetingSession.start()`.

Current (problematic for flagship):
- web server starts as side effect of active meeting.

Target:
- web control plane starts at app runtime bootstrap.
- meeting dashboards are mounted as route/state within the same runtime.

### 4.2 Required Modules (Target)

1. `holdspeak/web_runtime.py`
- long-lived web runtime and lifecycle management.

2. `holdspeak/web_server.py` (existing)
- refactor from per-meeting server assumptions to runtime-wide server.

3. `holdspeak/main.py`
- command contract changes and mode routing.

4. `holdspeak/controller.py`
- expose meeting lifecycle hooks callable from web runtime.

5. `holdspeak/config.py`
- web-first defaults and transition flags.

## 5. Detailed Requirements

### 5.1 Product and UX Requirements

- `WFS-P-001` Web UI MUST be the default interaction path for new sessions started via `holdspeak`.
- `WFS-P-002` Web UI MUST expose start/stop meeting controls without requiring TUI keybindings.
- `WFS-P-003` Web UI MUST expose current runtime state (idle, recording, transcribing, meeting_active, intel_status).
- `WFS-P-004` Web UI MUST expose MIR-01 controls (profile, route preview, override) once MIR-01 is enabled.
- `WFS-P-005` Docs and examples MUST present web-first flows before TUI flows.

### 5.2 CLI and Compatibility Requirements

- `WFS-C-001` `holdspeak` MUST launch web runtime by default.
- `WFS-C-002` `holdspeak tui` MUST launch TUI explicitly.
- `WFS-C-003` Legacy `--no-tui` behavior MUST emit deprecation notice.
- `WFS-C-004` Existing subcommands (`doctor`, `history`, `actions`, `intel`, `meeting --setup`) MUST remain unchanged.
- `WFS-C-005` Upgrade notes MUST include command migration examples.

### 5.3 Runtime and API Requirements

- `WFS-R-001` Web runtime MUST start independent of meeting lifecycle.
- `WFS-R-002` Web runtime MUST continue serving `/history` and `/settings` even when no meeting is active.
- `WFS-R-003` Runtime MUST provide a meeting control API (`start`, `stop`, `status`) callable from web UI.
- `WFS-R-004` Runtime MUST preserve local-only binding defaults (`127.0.0.1`) unless explicitly configured otherwise.
- `WFS-R-005` Runtime start/stop MUST be graceful and leak-free.

### 5.4 Reliability and Operational Requirements

- `WFS-O-001` Logs MUST state active mode (`web`, `tui`, `cli`).
- `WFS-O-002` Logs MUST include server URL and bind address at startup.
- `WFS-O-003` Startup failures MUST produce actionable remediation text.
- `WFS-O-004` Existing meeting persistence and deferred-intel flows MUST not regress.

### 5.5 Configurability Requirements (amendment, 2026-04-26)

Original WFS-01 §5.1 only required *exposure* of state and MIR-01 controls
in the web UI. The current operator audit (2026-04-26) found that core
DIR-01 dictation surfaces still require hand-rolled YAML editing —
specifically `~/.config/holdspeak/blocks.yaml`,
`<root>/.holdspeak/blocks.yaml`, `<root>/.holdspeak/project.yaml`, and
the dictation pipeline + runtime fields of `~/.config/holdspeak/config.json`.
The amendment below adds a `WFS-CFG-*` requirement family covering
interactive configuration of those surfaces from the web UI. This is a
strict superset of the original WFS-01 scope.

- `WFS-CFG-001` Web UI MUST expose CRUD over global blocks (`~/.config/holdspeak/blocks.yaml`) without requiring the user to edit YAML by hand. List, create, edit, delete; client-side validation mirroring `holdspeak.plugins.dictation.blocks.BlockConfigError`.
- `WFS-CFG-002` Web UI MUST expose the same CRUD over per-project blocks (`<project_root>/.holdspeak/blocks.yaml`) when a project is detected by `detect_project_for_cwd()`.
- `WFS-CFG-003` Web UI MUST expose the auto-detected `ProjectContext` (`name`, `root`, `anchor`) and a form-driven editor for `<root>/.holdspeak/project.yaml` `kb.*` fields. The kb keys are user-defined; the editor MUST allow add/remove/rename of arbitrary string-valued kb fields.
- `WFS-CFG-004` Web UI MUST expose `dictation.pipeline.enabled`, `dictation.pipeline.max_total_latency_ms`, `dictation.runtime.backend`, `dictation.runtime.mlx_model`, `dictation.runtime.llama_cpp_model_path`, `dictation.runtime.warm_on_start` as editable settings, and surface the live `runtime_counters.get_counters()` snapshot + `runtime_counters.get_session_status()` flag inline.
- `WFS-CFG-005` Web UI MUST expose a "dry-run" preview that runs the full DictationPipeline against a user-provided utterance string without touching the keyboard, mirroring `holdspeak dictation dry-run`. Output MUST show per-stage `elapsed_ms`, the matched intent (or no-match), and the final enriched text.
- `WFS-CFG-006` All configurability writes MUST be local-only (loopback bind preserved per WFS-R-004) and MUST atomically persist to disk (write-temp + rename) so concurrent reads never see partial files.
- `WFS-CFG-007` Configurability writes MUST validate before persisting and surface validation errors as actionable HTTP 4xx responses with field-level detail. Bad writes MUST NOT clobber existing valid files.

## 6. Verification Strategy

### 6.1 Verification Methods

- `UT`: unit tests
- `IT`: integration tests
- `AT`: API tests
- `MT`: manual command-contract checks
- `RG`: regression suite checks

### 6.2 Requirement-to-Verification Matrix

| Requirement | Method | Verification Demand | Evidence Artifact |
|---|---|---|---|
| WFS-P-001 | IT | Launch `holdspeak` and verify web runtime starts | `20_it_web_start.log` |
| WFS-P-002 | IT | Start/stop meeting via web UI/API without TUI | `20_it_web_meeting_controls.log` |
| WFS-P-003 | AT | Validate runtime-state API payload fields | `40_api_runtime.log` |
| WFS-P-004 | IT | Validate MIR-01 controls visible in web UI when enabled | `20_it_web_intent_controls.log` |
| WFS-P-005 | MT | Verify docs show web-first usage examples | `99_phase_summary.md` |
| WFS-C-001 | MT | `holdspeak` launches web mode by default | `41_cli_contract.log` |
| WFS-C-002 | MT | `holdspeak tui` launches TUI mode | `41_cli_contract.log` |
| WFS-C-003 | MT | `--no-tui` shows deprecation guidance | `41_cli_contract.log` |
| WFS-C-004 | RG | Existing subcommands remain operational | `42_cli_subcommands.log` |
| WFS-C-005 | MT | Migration examples present in docs | `99_phase_summary.md` |
| WFS-R-001 | IT | Web runtime available before meeting starts | `20_it_web_start.log` |
| WFS-R-002 | IT | `/history` and `/settings` accessible when idle | `20_it_web_idle_routes.log` |
| WFS-R-003 | AT | Meeting control API contract validated | `40_api_runtime.log` |
| WFS-R-004 | AT | Bind address defaults to loopback | `40_api_runtime.log` |
| WFS-R-005 | IT | Clean shutdown with no orphan workers | `20_it_shutdown.log` |
| WFS-O-001 | UT | Mode logging emitted consistently | `10_ut_runtime_mode.log` |
| WFS-O-002 | IT | Startup log includes URL and bind address | `60_logs_sample.txt` |
| WFS-O-003 | IT | Simulated startup failure returns actionable message | `20_it_startup_failures.log` |
| WFS-O-004 | RG | Deferred-intel and meeting persistence tests still pass | `70_regression.log` |

## 7. Evidence Bundle Contract

### 7.1 Required Output Folder

`docs/evidence/phase-wfs-01/<YYYYMMDD-HHMM>/`

### 7.2 Required Files

1. `00_manifest.md`
2. `01_env.txt`
3. `02_git_status.txt`
4. `03_traceability.md`
5. `10_ut_runtime_mode.log`
6. `20_it_web_start.log`
7. `20_it_web_meeting_controls.log`
8. `20_it_web_intent_controls.log`
9. `20_it_web_idle_routes.log`
10. `20_it_shutdown.log`
11. `20_it_startup_failures.log`
12. `40_api_runtime.log`
13. `41_cli_contract.log`
14. `42_cli_subcommands.log`
15. `60_logs_sample.txt`
16. `70_regression.log`
17. `99_phase_summary.md`

### 7.3 Evidence Validity Rules

1. Each log MUST include command used.
2. `git rev-parse HEAD` MUST be captured in evidence.
3. Failed attempts MUST be preserved with notes.
4. Phase cannot be marked complete if any required evidence file is missing.

## 8. Prescriptive Implementation Recipe

### 8.1 Step 0: Baseline and Branch Guard

Commands:

```bash
uv run pytest -q tests/unit
uv run pytest -q tests/integration
```

### 8.2 Step 1: Command Contract Refactor

Required edits:

1. Update parser and default mode logic in `holdspeak/main.py`.
2. Add `web` and `tui` subcommands.
3. Add deprecation behavior for `--no-tui`.

Tests:

- `tests/unit/test_main_modes.py` (new)
- update existing CLI-mode tests as needed.

Gate:

```bash
uv run pytest -q tests/unit/test_main_modes.py
```

### 8.3 Step 2: Web Runtime Lifecycle

Required edits:

1. Add `holdspeak/web_runtime.py`.
2. Move startup/shutdown ownership from meeting session to runtime service.
3. Ensure runtime survives idle (no meeting active).

Tests:

- `tests/unit/test_web_runtime.py` (new)
- `tests/integration/test_web_runtime_lifecycle.py` (new)

Gate:

```bash
uv run pytest -q tests/unit/test_web_runtime.py tests/integration/test_web_runtime_lifecycle.py -m requires_meeting
```

### 8.4 Step 3: Meeting Control API Wiring

Required edits:

1. Add runtime-level meeting control endpoints in `holdspeak/web_server.py`.
2. Wire endpoints to controller hooks in `holdspeak/controller.py`.
3. Maintain thread-safety and stop-path correctness.

Tests:

- `tests/integration/test_web_meeting_controls.py` (new)
- adjust existing `tests/integration/test_web_server.py` coverage.

Gate:

```bash
uv run pytest -q tests/integration/test_web_meeting_controls.py tests/integration/test_web_server.py -m requires_meeting
```

### 8.5 Step 4: Web-First UX and Docs Migration

Required edits:

1. Update web pages for clear flagship entry and mode status.
2. Update `README.md` and `docs/MEETING_MODE_GUIDE.md` for web-first usage.
3. Document TUI as explicit secondary mode.

Gate:

```bash
uv run pytest -q tests/integration/test_web_server.py -m requires_meeting
```

### 8.6 Step 5: Regression Protection

Required checks:

1. Deferred-intel queue behavior unchanged.
2. Meeting save/stop semantics unchanged.
3. CLI subcommands unchanged.

Gate:

```bash
uv run pytest -q tests/unit/test_intel_queue.py tests/unit/test_meeting_session.py tests/unit/test_intel_command.py
uv run pytest -q tests/integration/test_intel_streaming.py -m requires_meeting
```

### 8.7 Step 6: Full Gate

```bash
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run pytest -q tests/integration -m requires_meeting
uv run python -m compileall holdspeak
```

## 9. Definition of Done

All MUST conditions below are required:

1. `holdspeak` starts web flagship runtime by default.
2. Web interface can manage meeting lifecycle without TUI.
3. MIR-01 web controls are integrated or clearly feature-flagged with stable hooks.
4. TUI remains accessible via explicit command and is non-blocking for web-first releases.
5. Required evidence bundle is complete and traceable.
6. Regression suite passes.

## 10. Risks and Mitigations

1. Risk: Breaking long-time TUI user habits.
- Mitigation: explicit `holdspeak tui` path, deprecation notice, migration docs.

2. Risk: Web runtime startup failures block app usage.
- Mitigation: actionable errors plus fallback suggestion (`holdspeak tui`).

3. Risk: Meeting control race conditions via API.
- Mitigation: controller-level locking and stop-path tests.

4. Risk: Scope creep into full web redesign.
- Mitigation: WFS-01 limits to runtime and control-plane migration.

## 11. Handoff Contract for LLM Executors

Executor MUST deliver:

1. Requirement traceability (`WFS-*` -> evidence file).
2. Code changes grouped by implementation step.
3. Full evidence bundle.
4. Explicit list of deferred items.

If any `MUST` cannot be satisfied, executor MUST stop and document:

1. failing command,
2. full error output,
3. attempted mitigations,
4. recommended unblock path.
