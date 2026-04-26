# Command: manual traceability audit against docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md
# Captured: 2026-04-26 15:37:36 MDT
# Git: 0868153 (pre-commit; working tree contains HS-4-05/HS-4-06 changes)

# WFS-01 traceability matrix

## Product and UX requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| WFS-P-001 | IT/MT | `20_it_web_start.log`, `41_cli_contract.log` | `holdspeak` routes to web runtime by default. |
| WFS-P-002 | IT | `20_it_web_meeting_controls.log` | `/api/meeting/start` and `/api/meeting/stop` routes are mounted and covered. |
| WFS-P-003 | AT | `40_api_runtime.log` | `/api/runtime/status` exposes mode/status/meeting shape. |
| WFS-P-004 | IT | `20_it_web_intent_controls.log` | MIR profile, override, and preview controls are covered by web API tests. |
| WFS-P-005 | MT | `99_phase_summary.md`, `README.md` | README leads with web runtime usage before TUI. |

## CLI and compatibility requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| WFS-C-001 | UT | `41_cli_contract.log` | default invocation starts web runtime. |
| WFS-C-002 | UT | `41_cli_contract.log` | `holdspeak tui` remains explicit fallback. |
| WFS-C-003 | UT | `41_cli_contract.log` | legacy `--no-tui` path emits deprecation and aliases to web headless. |
| WFS-C-004 | RG | `42_cli_subcommands.log`, `70_regression.log` | existing CLI subcommands remain covered in full regression. |
| WFS-C-005 | MT | `README.md`, `99_phase_summary.md` | command migration examples are documented. |

## Runtime and API requirements

| Req | Method | Evidence | Notes |
|---|---|---|---|
| WFS-R-001 | IT | `20_it_web_start.log`, `20_it_web_idle_routes.log` | runtime serves before any meeting is active. |
| WFS-R-002 | IT | `20_it_web_idle_routes.log` | `/history` and `/settings` are accessible idle. |
| WFS-R-003 | AT | `20_it_web_meeting_controls.log` | meeting control API is mounted and callback-shaped. |
| WFS-R-004 | AT | `40_api_runtime.log` | default bind address is `127.0.0.1`; explicit override is honored. |
| WFS-R-005 | IT | `20_it_shutdown.log` | web runtime unit lifecycle tests cover start/stop path. |

## Reliability and operations

| Req | Method | Evidence | Notes |
|---|---|---|---|
| WFS-O-001 | UT/LG | `10_ut_runtime_mode.log`, `60_logs_sample.txt` | runtime mode is represented by CLI routing and API payloads. |
| WFS-O-002 | LG | `60_logs_sample.txt` | startup sample includes bind URL. |
| WFS-O-003 | IT | `20_it_startup_failures.log` | degraded/missing-callback startup failure states return actionable HTTP status rather than route failure. |
| WFS-O-004 | RG | `70_regression.log` | full regression covers meeting persistence and deferred-intel paths. |

## Configurability amendment

| Req | Method | Evidence | Notes |
|---|---|---|---|
| WFS-CFG-001 | IT | `50_cfg_blocks.log` | global block CRUD + UI anchors. |
| WFS-CFG-002 | IT | `50_cfg_blocks.log` | project block CRUD + no-project branch. |
| WFS-CFG-003 | IT | `51_cfg_project_kb.log` | project context + `<root>/.holdspeak/project.yaml` `kb.*` editor. |
| WFS-CFG-004 | IT | `52_cfg_runtime_settings.log` | dictation runtime settings, counters, and session state. |
| WFS-CFG-005 | IT | `53_cfg_dry_run.log` | full pipeline dry-run preview and UI anchors. |
| WFS-CFG-006 | IT | `54_cfg_atomic_validation.log` | bad block/project-KB writes leave existing files unchanged; settings writes validated before save. |
| WFS-CFG-007 | IT | `54_cfg_atomic_validation.log` | validation errors surface as 4xx with actionable messages/details. |

## Outcome

Every original `WFS-*` and amended `WFS-CFG-*` requirement has a
passing artifact. Phase 4 is eligible to close.
