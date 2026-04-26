# Command: manual phase-exit bundle assembly for HS-4-06
# Captured: 2026-04-26 15:37:36 MDT
# Git: 0868153 (pre-commit; working tree contains HS-4-05/HS-4-06 changes)

# Phase WFS-01 evidence bundle - manifest

**Bundle path:** `docs/evidence/phase-wfs-01/20260426-1537/`
**Phase:** 4 (HoldSpeak roadmap) - WFS-01 extended
**Spec:** `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`
**Story:** HS-4-06 (Definition of Done sweep)

## Files

Original WFS-01 spec files plus five WFS-CFG amendment files:

| File | Purpose | Status |
|---|---|---|
| `00_manifest.md` | This manifest | present |
| `01_env.txt` | OS, Python, uv, git environment | present |
| `02_git_status.txt` | Working-tree state and recent commits | present |
| `03_traceability.md` | WFS / WFS-CFG requirement to evidence matrix | present |
| `10_ut_runtime_mode.log` | CLI/runtime-mode unit coverage | present |
| `20_it_web_start.log` | Web runtime startup and independent-route coverage | present |
| `20_it_web_meeting_controls.log` | Meeting start/stop API coverage | present |
| `20_it_web_intent_controls.log` | MIR intent control API coverage | present |
| `20_it_web_idle_routes.log` | Idle `/history` and `/settings` coverage | present |
| `20_it_shutdown.log` | Runtime start/stop lifecycle coverage | present |
| `20_it_startup_failures.log` | Startup failure/degraded-state coverage | present |
| `40_api_runtime.log` | Runtime/status API coverage | present |
| `41_cli_contract.log` | CLI command-contract coverage | present |
| `42_cli_subcommands.log` | Existing subcommand regression coverage | present |
| `50_cfg_blocks.log` | WFS-CFG-001/002 block editor API/UI coverage | present |
| `51_cfg_project_kb.log` | WFS-CFG-003 project-KB API/UI coverage | present |
| `52_cfg_runtime_settings.log` | WFS-CFG-004 runtime settings API/UI coverage | present |
| `53_cfg_dry_run.log` | WFS-CFG-005 dry-run API/UI coverage | present |
| `54_cfg_atomic_validation.log` | WFS-CFG-006/007 atomic write + validation coverage | present |
| `60_logs_sample.txt` | Log/mode/startup observability sample | present |
| `70_regression.log` | Full non-metal regression | present |
| `99_phase_summary.md` | Final phase outcome and deferreds | present |

## Validity

Each artifact starts with `# Command`, `# Captured`, and `# Git`.
The full regression passed with 1072 tests and 13 skips. Metal e2e
tests remain excluded per the project test plan.
