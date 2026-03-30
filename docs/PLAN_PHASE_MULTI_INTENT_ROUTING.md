# Phase MIR-01: Dynamic Multi-Intent Routing and Artifact Synthesis

## 1. Phase Charter

### 1.1 Objective

Implement a dynamic, multi-intent routing system that operates on rolling meeting windows (not whole-meeting labels), supports topic shifts, runs multiple plugin chains safely, and synthesizes coherent final artifacts.

### 1.2 Why This Phase Exists

Meetings routinely shift between architecture, delivery, product, incident, and communication intents. A single meeting-level classifier is insufficient and will produce low-quality or contradictory artifacts.

### 1.3 Success Criteria (Phase-Level)

1. Intent detection works at timeline granularity with multiple simultaneous intents.
2. Router emits plugin chains per window with confidence thresholds and hysteresis.
3. Outputs include lineage from transcript windows to artifacts.
4. End-of-meeting synthesis merges window artifacts without duplication.
5. Verification evidence is complete and reproducible.

## 2. Normative Language

This phase uses strict terms:

- `MUST`: required for phase acceptance.
- `SHOULD`: strongly recommended; deviations require documented rationale.
- `MAY`: optional enhancement.

## 3. Scope and Non-Scope

### 3.1 In Scope

1. Multi-label intent scoring per rolling window.
2. Intent transition detection with hysteresis.
3. Plugin routing per window and per active profile.
4. Persistence for windows, intent labels, plugin runs, and artifact lineage.
5. End-of-meeting synthesis pass.
6. Web-first UX and API surfaces for introspection and manual override.
7. Automated verification and evidence bundle generation.

### 3.2 Out of Scope

1. External plugin marketplace.
2. Full autonomous actuator execution against third-party systems.
3. Replacement of current meeting transcription pipeline.

## 4. Entry Criteria

All entry criteria MUST be true before implementation starts.

1. Baseline test suite passes on branch tip.
2. Existing deferred-intel functionality remains operational.
3. `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` exists and is treated as parent RFC.
4. Operator has write access to repository and can run `uv run pytest`.
5. Web-first runtime migration plan exists in `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`.

## 5. Architecture Delta

### 5.1 New Runtime Concepts

1. `IntentWindow`
- Sliding transcript window with deterministic boundaries.

2. `IntentScore`
- Multi-label scored output per window (example: `architecture=0.81`, `delivery=0.76`).

3. `IntentTransition`
- Event generated when dominant intent set changes beyond hysteresis threshold.

4. `PluginRun`
- One execution record for plugin + window + profile with status and timing.

5. `ArtifactLineage`
- Mapping from artifact to source window IDs and plugin runs.

### 5.2 Required Modules (Target)

1. `holdspeak/plugins/contracts.py`
2. `holdspeak/plugins/signals.py`
3. `holdspeak/plugins/router.py`
4. `holdspeak/plugins/host.py`
5. `holdspeak/plugins/synthesis.py`
6. `holdspeak/artifacts.py`
7. `holdspeak/intent_timeline.py`

### 5.3 Existing Modules to Integrate

1. `holdspeak/meeting_session.py`
2. `holdspeak/intel_queue.py`
3. `holdspeak/commands/intel.py`
4. `holdspeak/web_server.py`
5. `holdspeak/db.py`
6. `holdspeak/config.py`

## 6. Detailed Requirements

### 6.1 Functional Requirements

- `MIR-F-001` The system MUST process transcript data in rolling windows.
- `MIR-F-002` Each window MUST support multi-label intent scores (not single label).
- `MIR-F-003` Router MUST support at least 5 intents: `architecture`, `delivery`, `product`, `incident`, `comms`.
- `MIR-F-004` Router MUST allow multiple intents above threshold in the same window.
- `MIR-F-005` Router MUST apply hysteresis to avoid oscillation on borderline scores.
- `MIR-F-006` Router MUST emit deterministic plugin chain selection from profile + scores.
- `MIR-F-007` Router MUST support manual override for a specific meeting/window.
- `MIR-F-008` Plugin execution MUST be idempotent per `(meeting_id, window_id, plugin_id, transcript_hash)`.
- `MIR-F-009` System MUST suppress duplicate artifact generation from overlapping windows.
- `MIR-F-010` End-of-meeting synthesis MUST merge artifacts into a coherent final set.
- `MIR-F-011` Synthesis MUST preserve source references to input windows.
- `MIR-F-012` If scoring fails, system MUST degrade gracefully to current intel flow.

### 6.2 Data and Persistence Requirements

- `MIR-D-001` DB schema MUST store intent windows with temporal bounds.
- `MIR-D-002` DB schema MUST store per-window intent scores.
- `MIR-D-003` DB schema MUST store plugin run records and status.
- `MIR-D-004` DB schema MUST store artifact lineage (artifact to window/plugin).
- `MIR-D-005` Migration MUST be backward-compatible and idempotent.
- `MIR-D-006` Existing meetings without intent timeline MUST remain loadable.

### 6.3 API and UX Requirements

- `MIR-A-000` Web interface MUST be the flagship surface for all new MIR-01 functionality.
- `MIR-A-001` Web API MUST expose meeting intent timeline.
- `MIR-A-002` Web API MUST expose plugin run history for meeting.
- `MIR-A-003` CLI MUST provide dry-run route simulation for a meeting.
- `MIR-A-004` CLI MUST provide manual re-route for profile override.
- `MIR-A-005` UI/API output MUST show confidence values per intent label.
- `MIR-A-006` Web UI MUST provide controls for profile selection, route preview, and manual override.
- `MIR-A-007` TUI support for MIR-01 MAY lag and MUST NOT block phase completion.
- `MIR-A-008` Documentation and examples MUST present web flows before TUI flows for MIR-01 features.

### 6.4 Reliability and Performance Requirements

- `MIR-R-001` Routing for one window SHOULD complete within 300ms median on developer hardware.
- `MIR-R-002` Plugin execution MUST enforce per-plugin timeout.
- `MIR-R-003` Heavy plugin runs MUST be deferrable through queue mechanisms.
- `MIR-R-004` Failures in one plugin MUST NOT block other eligible plugins.
- `MIR-R-005` System MUST persist partial progress before meeting stop finalization.

### 6.5 Observability and Safety Requirements

- `MIR-O-001` Logs MUST include `meeting_id`, `window_id`, `intent_set`, and `plugin_id` where relevant.
- `MIR-O-002` Router MUST emit counters for routed windows and dropped windows.
- `MIR-O-003` Plugin host MUST emit success/failure/timeout counters.
- `MIR-S-001` Capability checks MUST run before plugin execution.
- `MIR-S-002` Actuator plugins MUST remain disabled by default.
- `MIR-S-003` Logs MUST avoid raw secret values.

## 7. Verification Strategy

### 7.1 Verification Methods

- `UT`: unit tests
- `IT`: integration tests
- `AT`: API-level tests
- `MT`: manual trace verification
- `LG`: log/metrics verification

### 7.2 Requirement-to-Verification Matrix

| Requirement | Method | Verification Demand | Evidence Artifact |
|---|---|---|---|
| MIR-F-001 | UT | Add tests for rolling window boundaries and overlap behavior | `10_ut_router.log` |
| MIR-F-002 | UT | Assert multi-label scoring output contains >1 label when eligible | `10_ut_router.log` |
| MIR-F-003 | UT | Assert supported intent set includes required intents | `10_ut_router.log` |
| MIR-F-004 | UT | Assert same window routes multiple intents above threshold | `10_ut_router.log` |
| MIR-F-005 | UT | Assert hysteresis suppresses oscillation across near-equal windows | `10_ut_router.log` |
| MIR-F-006 | UT | Assert deterministic chain selection for fixed input/profile | `10_ut_router.log` |
| MIR-F-007 | IT | Manual override endpoint/CLI changes routing outcome | `20_it_routing.log` |
| MIR-F-008 | UT | Duplicate run attempt returns deduped status | `10_ut_router.log` |
| MIR-F-009 | IT | Overlapping windows do not create duplicate artifact entries | `20_it_routing.log` |
| MIR-F-010 | IT | Synthesis output created on meeting finalization | `20_it_synthesis.log` |
| MIR-F-011 | IT | Synthesis artifact includes lineage refs | `20_it_synthesis.log` |
| MIR-F-012 | IT | Forced scorer failure falls back without crash | `20_it_fallback.log` |
| MIR-D-001 | AT | Query DB for persisted windows after test meeting | `30_db_checks.txt` |
| MIR-D-002 | AT | Query DB for persisted intent scores per window | `30_db_checks.txt` |
| MIR-D-003 | AT | Query DB for plugin run records and statuses | `30_db_checks.txt` |
| MIR-D-004 | AT | Query DB for artifact lineage rows | `30_db_checks.txt` |
| MIR-D-005 | MT | Re-run migration on existing DB without errors | `31_migration_checks.txt` |
| MIR-D-006 | IT | Load old fixture meetings with no timeline data | `20_it_backcompat.log` |
| MIR-A-000 | AT | Verify new MIR-01 capabilities are reachable from web UI and API without TUI | `40_api_checks.log` |
| MIR-A-001 | AT | Hit timeline API and validate schema | `40_api_checks.log` |
| MIR-A-002 | AT | Hit plugin-runs API and validate schema | `40_api_checks.log` |
| MIR-A-003 | MT | Run CLI dry-run and validate stable output | `41_cli_checks.log` |
| MIR-A-004 | MT | Run CLI re-route and validate changed profile | `41_cli_checks.log` |
| MIR-A-005 | AT | Confirm confidence values in API payload | `40_api_checks.log` |
| MIR-A-006 | IT | Validate web controls for profile, preview, and override | `40_api_checks.log` |
| MIR-A-007 | MT | Confirm phase gates pass without new TUI work | `99_phase_summary.md` |
| MIR-A-008 | MT | Verify docs updated with web-first MIR-01 examples | `99_phase_summary.md` |
| MIR-R-001 | MT | Capture routing timing sample over representative transcript | `50_perf.txt` |
| MIR-R-002 | IT | Force timeout and verify plugin marked timeout | `20_it_timeouts.log` |
| MIR-R-003 | IT | Heavy plugins enqueue instead of blocking live path | `20_it_queue.log` |
| MIR-R-004 | IT | One plugin failure does not prevent others | `20_it_isolation.log` |
| MIR-R-005 | IT | Stop meeting mid-pipeline and verify persisted partial state | `20_it_stop_path.log` |
| MIR-O-001 | LG | Verify structured log fields exist | `60_logs_sample.txt` |
| MIR-O-002 | LG | Verify router counters increment | `61_metrics_sample.txt` |
| MIR-O-003 | LG | Verify host counters for success/failure/timeout | `61_metrics_sample.txt` |
| MIR-S-001 | UT | Capability mismatch blocks plugin execution | `10_ut_security.log` |
| MIR-S-002 | UT | Actuators disabled by default path tested | `10_ut_security.log` |
| MIR-S-003 | LG | Secret redaction checks in logs | `60_logs_sample.txt` |

## 8. Evidence Bundle Contract

### 8.1 Required Output Folder

Every phase execution MUST produce:

`docs/evidence/phase-mir-01/<YYYYMMDD-HHMM>/`

### 8.2 Required Files

1. `00_manifest.md`
2. `01_env.txt`
3. `02_git_status.txt`
4. `03_traceability.md`
5. `10_ut_router.log`
6. `10_ut_security.log`
7. `20_it_routing.log`
8. `20_it_synthesis.log`
9. `20_it_fallback.log`
10. `30_db_checks.txt`
11. `31_migration_checks.txt`
12. `40_api_checks.log`
13. `41_cli_checks.log`
14. `50_perf.txt`
15. `60_logs_sample.txt`
16. `61_metrics_sample.txt`
17. `99_phase_summary.md`

### 8.3 Evidence Validity Rules

1. Logs MUST include command line used.
2. Logs MUST include timestamp and git commit hash.
3. Failing checks MUST be preserved and annotated, not deleted.
4. Phase cannot be marked complete if required files are missing.

## 9. Prescriptive Implementation Recipe

### 9.1 Step 0: Baseline Capture

1. Record baseline commit and environment.
2. Run baseline tests before changes.

Commands:

```bash
mkdir -p docs/evidence/phase-mir-01/$(date +%Y%m%d-%H%M)
uv run pytest -q tests/unit
uv run pytest -q tests/integration
```

### 9.2 Step 1: Contracts and Router Skeleton

Required edits:

1. Add contracts in `holdspeak/plugins/contracts.py`.
2. Add timeline entities in `holdspeak/intent_timeline.py`.
3. Add router skeleton in `holdspeak/plugins/router.py`.
4. Add unit tests in:
- `tests/unit/test_intent_timeline.py`
- `tests/unit/test_intent_router.py`

Verification gate:

```bash
uv run pytest -q tests/unit/test_intent_timeline.py tests/unit/test_intent_router.py
```

### 9.3 Step 2: Windowing and Multi-Label Scoring

Required edits:

1. Implement rolling window builder over transcript segments.
2. Implement deterministic lexical signal extractor in `holdspeak/plugins/signals.py`.
3. Implement score normalization and threshold logic.
4. Implement hysteresis and transition detection.

Verification gate:

```bash
uv run pytest -q tests/unit/test_intent_router.py -k "window or label or hysteresis"
```

### 9.4 Step 3: Plugin Host Integration

Required edits:

1. Implement plugin host execution semantics in `holdspeak/plugins/host.py`.
2. Add idempotency key generation and duplicate suppression.
3. Add timeout and failure isolation logic.
4. Add unit tests:
- `tests/unit/test_plugin_host.py`
- `tests/unit/test_plugin_host_idempotency.py`

Verification gate:

```bash
uv run pytest -q tests/unit/test_plugin_host.py tests/unit/test_plugin_host_idempotency.py
```

### 9.5 Step 4: Persistence and Migration

Required edits:

1. Update `holdspeak/db.py` schema version and migrations.
2. Add tables for windows, scores, plugin runs, lineage.
3. Add CRUD methods for timeline and plugin run persistence.
4. Add migration tests in `tests/unit/test_db_intent_timeline.py`.

Verification gate:

```bash
uv run pytest -q tests/unit/test_db.py tests/unit/test_db_intent_timeline.py
```

### 9.6 Step 5: Meeting Runtime Wiring

Required edits:

1. Wire router into `holdspeak/meeting_session.py` on segment updates and finalization.
2. Add fallback behavior when router/scoring fails.
3. Ensure stop path remains deadlock-safe.
4. Add integration tests:
- `tests/integration/test_multi_intent_routing.py`
- `tests/integration/test_multi_intent_stop_path.py`

Verification gate:

```bash
uv run pytest -q tests/integration/test_multi_intent_routing.py tests/integration/test_multi_intent_stop_path.py -m integration
```

### 9.7 Step 6: Synthesis Pass

Required edits:

1. Add synthesis pipeline in `holdspeak/plugins/synthesis.py`.
2. Merge window-level artifacts into final set.
3. Preserve lineage references.
4. Add tests:
- `tests/unit/test_artifact_synthesis.py`
- `tests/integration/test_artifact_synthesis_pipeline.py`

Verification gate:

```bash
uv run pytest -q tests/unit/test_artifact_synthesis.py tests/integration/test_artifact_synthesis_pipeline.py -m integration
```

### 9.8 Step 7: API and CLI Surfaces

Required edits:

1. Add timeline endpoints in `holdspeak/web_server.py`.
2. Add CLI dry-run and re-route options in `holdspeak/commands/intel.py` and `holdspeak/main.py`.
3. Add web UI controls for profile selection, route preview, and override in web meeting/history pages.
4. Add API/CLI tests:
- `tests/integration/test_web_intent_timeline_api.py`
- `tests/unit/test_intel_command.py` updates
- `tests/integration/test_web_intent_controls.py`

Verification gate:

```bash
uv run pytest -q tests/integration/test_web_intent_timeline_api.py -m requires_meeting
uv run pytest -q tests/integration/test_web_intent_controls.py -m requires_meeting
uv run pytest -q tests/unit/test_intel_command.py
```

### 9.9 Step 8: Config and Feature Flags

Required edits:

1. Extend `MeetingConfig` in `holdspeak/config.py` with:
- `intent_router_enabled: bool`
- `intent_window_seconds: int`
- `intent_step_seconds: int`
- `intent_score_threshold: float`
- `intent_hysteresis_windows: int`
- `plugin_profile: str`

2. Set conservative defaults and validation.
3. Update settings API validation in `holdspeak/web_server.py`.

Verification gate:

```bash
uv run pytest -q tests/unit/test_config.py tests/unit/test_doctor_command.py
```

### 9.10 Step 9: Observability and Hardening

Required edits:

1. Add structured logs in router and host.
2. Add counters/telemetry hooks.
3. Add tests:
- `tests/unit/test_intent_observability.py`
- `tests/integration/test_intent_failure_isolation.py`

Verification gate:

```bash
uv run pytest -q tests/unit/test_intent_observability.py tests/integration/test_intent_failure_isolation.py -m integration
```

### 9.11 Step 10: Full Regression Gate

Required command set:

```bash
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run pytest -q tests/integration -m requires_meeting
uv run python -m compileall holdspeak
```

Phase cannot complete until all required commands pass.

## 10. Verification Evidence Commands (Canonical)

Use `tee` to capture output into evidence bundle.

```bash
EVIDENCE_DIR="docs/evidence/phase-mir-01/$(date +%Y%m%d-%H%M)"
mkdir -p "$EVIDENCE_DIR"

( set -x; date; uname -a; uv --version; python --version ) | tee "$EVIDENCE_DIR/01_env.txt"
( set -x; git rev-parse HEAD; git status --short ) | tee "$EVIDENCE_DIR/02_git_status.txt"

( set -x; uv run pytest -q tests/unit/test_intent_timeline.py tests/unit/test_intent_router.py ) | tee "$EVIDENCE_DIR/10_ut_router.log"
( set -x; uv run pytest -q tests/unit/test_plugin_host.py tests/unit/test_plugin_host_idempotency.py ) | tee "$EVIDENCE_DIR/10_ut_security.log"
( set -x; uv run pytest -q tests/integration/test_multi_intent_routing.py tests/integration/test_artifact_synthesis_pipeline.py -m integration ) | tee "$EVIDENCE_DIR/20_it_routing.log"
( set -x; uv run python -m compileall holdspeak ) | tee "$EVIDENCE_DIR/99_phase_summary.md"
```

## 11. Definition of Done

All items MUST be satisfied.

1. Every `MIR-*` requirement has passing verification evidence.
2. Required evidence files exist and are non-empty.
3. Router supports dynamic intent shifts and multi-intent windows.
4. Synthesis pass runs and stores lineage links.
5. No regressions in existing deferred-intel paths.
6. Phase summary includes known gaps and deferred work.
7. Web UI exposes MIR-01 controls end-to-end without requiring TUI.

## 12. Risks and Mitigations

1. Risk: Intent oscillation produces noisy artifacts.
- Mitigation: Hysteresis windows and minimum confidence delta.

2. Risk: Plugin explosion increases cost/latency.
- Mitigation: Profile-based plugin allowlist + deferred queue.

3. Risk: Overlapping windows duplicate outputs.
- Mitigation: Idempotency key + synthesis dedupe.

4. Risk: Stop path race conditions.
- Mitigation: Persist partial progress and reuse stop-path deadlock tests.

## 13. Handoff Contract for LLM Executors

The executor MUST deliver:

1. Code changes grouped by step.
2. Updated tests for each changed behavior.
3. Evidence bundle with all required artifacts.
4. Traceability doc mapping `MIR-*` requirements to evidence files.
5. Explicit list of any unmet SHOULD/MAY items.

If any MUST item cannot be completed, executor MUST stop and document blocker with:

1. exact failing command,
2. exact error text,
3. attempted mitigations,
4. recommended next action.
