# Phase 2 — Multi-Intent Routing (MIR-01)

**Last updated:** 2026-04-26 (HS-2-10 done — 2 MIR doctor checks (`MIR routing`, `MIR telemetry`) honoring DIR-DOC-003 never-FAIL + spec-named failure-isolation integration test; 8 new tests, 973 passed end-to-end).

## Goal

Deliver MIR-01 per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md`: a
dynamic, multi-intent routing system that operates on rolling meeting
windows (not whole-meeting labels), supports topic shifts, runs
multiple plugin chains safely, and synthesizes coherent end-of-meeting
artifacts with lineage from transcript windows. This is the
meeting-side sibling to DIR-01; the two phases share
`holdspeak/plugins/contracts.py` types where they overlap (per DIR-01
§4 item 1) but otherwise have separate runtimes. This section is
**immutable** for the life of the phase.

## Scope

- **In:** Everything declared in scope by `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §3.1. Implementation tracked via stories `HS-2-01` through `HS-2-11`, mapping 1:1 onto spec §9.1–§9.11. Phase exit is gated by spec §11 "Definition of Done".
- **Out:** Everything declared out-of-scope by `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §3.2 — external plugin marketplace, autonomous third-party actuator execution, and replacing the current meeting transcription pipeline.

## Exit criteria (evidence required)

- [ ] Every `MIR-*` requirement has passing verification per spec §7.2 matrix.
- [ ] Evidence bundle at `docs/evidence/phase-mir-01/<YYYYMMDD-HHMM>/` contains every file listed in spec §8.2.
- [ ] Router supports dynamic intent shifts and multi-intent windows on a real meeting transcript end-to-end.
- [ ] Synthesis pass runs and stores `ArtifactLineage` links from artifacts back to source windows + plugin runs.
- [ ] No regressions in existing deferred-intel paths.
- [ ] Web UI exposes MIR-01 controls end-to-end without requiring TUI (per spec §11 item 7).
- [ ] Phase summary lists known gaps and explicitly defers follow-up work.

## Story status

Mapping: each story corresponds to one spec §9 step. Stories are
created ahead of time as `backlog` so the work is visible; only the
"in-progress" story has a fully fleshed-out file at any given time.
The `Status` field on each story file is the source of truth; the
table below mirrors it.

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| ~~HS-2-01~~ | ~~Step 0 — Baseline capture~~ | dropped | — | n/a — no pre-shipping measurement gate (mirrors the DIR-01 amendment that dropped HS-1-01 and HS-1-10) |
| HS-2-02 | Step 1 — Contracts + router skeleton | done | [story-02-contracts-router](./story-02-contracts-router.md) | tests pass (7 new + 10 adjacent intent cases = 17/17) + full suite green (excl. pre-existing metal hw fail) |
| HS-2-03 | Step 2 — Windowing + multi-label scoring | done | [story-03-windowing](./story-03-windowing.md) | tests pass (8 new + 21 adjacent intent cases = 29/29) + full suite green (907 passed, metal excluded) |
| HS-2-04 | Step 3 — Plugin host integration | done | [story-04-plugin-host](./story-04-plugin-host.md) | tests pass (6 new + 23 host-suite cases) + full suite green (913 passed, metal excluded) |
| HS-2-05 | Step 4 — Persistence + migration | done | [story-05-persistence](./story-05-persistence.md) | tests pass (8 new + 6 engine MIR-persistence cases) + full suite green (921 passed, metal excluded) |
| HS-2-06 | Step 5 — Meeting runtime wiring | done | [story-06-runtime-wiring](./story-06-runtime-wiring.md) | tests pass (5 unit + 6 integration) + full suite green (932 passed, metal excluded) |
| HS-2-07 | Step 6 — Synthesis pass | done | [story-07-synthesis](./story-07-synthesis.md) | tests pass (5 unit + 3 integration + 3 pre-existing synthesis = 11/11) + full suite green (940 passed, metal excluded) |
| HS-2-08 | Step 7 — API + CLI surfaces | done | [story-08-api-cli](./story-08-api-cli.md) | tests pass (6 timeline + 8 controls = 14 new + 7 pre-existing intel-command) + full suite green (954 passed, metal excluded) |
| HS-2-09 | Step 8 — Config + feature flags | done | [story-09-config-flags](./story-09-config-flags.md) | tests pass (7 unit config + 3 integration + 1 extended defaults case) + full suite green (965 passed, metal excluded) |
| HS-2-10 | Step 9 — Observability + hardening | done | [story-10-observability](./story-10-observability.md) | tests pass (5 new doctor + 3 new integration + 21 doctor + 3 pre-existing observability) + full suite green (973 passed, metal excluded) |
| HS-2-11 | Step 10 — Full regression gate + DoD | backlog | [story-11-dod](./story-11-dod.md) | — |

## Where we are

HS-2-10 done — 2 new MIR doctor checks (`MIR routing`,
`MIR telemetry`) join the dictation pair in `collect_doctor_checks`,
both honoring DIR-DOC-003 (never FAIL — MIR-01 is opt-in). The
routing check validates `plugin_profile` against `available_profiles`
so typos surface at `holdspeak doctor` rather than at meeting stop;
the telemetry check is a smoke probe that the router/host counter
APIs are callable. The spec-named integration test
`test_intent_failure_isolation.py` covers MIR-R-004 end-to-end:
one failing chain plugin → siblings still execute, the failed run
persists with `status=error`. Pre-existing
`test_intent_observability.py` already covered MIR-O-001/002/003
at the unit level (router counters, host metrics, structured logs
with secret redaction) — no new router/host code was needed.
Next: **HS-2-11 (DoD sweep)** — full §7.2 matrix verification,
evidence bundle at `docs/evidence/phase-mir-01/<YYYYMMDD-HHMM>/`,
phase summary, mark phase done. Mirrors HS-1-11.

## Active risks

Carried forward from spec §12 verbatim:

1. Intent oscillation produces noisy artifacts. Mitigation: hysteresis windows + minimum confidence delta.
2. Plugin explosion increases cost/latency. Mitigation: profile-based plugin allowlist + deferred queue.
3. Overlapping windows duplicate outputs. Mitigation: idempotency key + synthesis dedupe.
4. Stop-path race conditions. Mitigation: persist partial progress + reuse stop-path deadlock tests.

## Decisions made (this phase)

- 2026-04-25 — HS-2-01 (Step 0 baseline capture) dropped, same call as DIR-01's HS-1-01 / HS-1-10. No pre-shipping measurement gate per the standing project convention.
- 2026-04-25 — HS-2-02 keeps the existing `holdspeak/plugins/host.py::PluginRunResult` and `holdspeak/db.py::PluginRunSummary` in place rather than collapsing them into the new `PluginRun` contract. Rationale: they serve different layers (in-process result wrapper vs. persisted summary vs. canonical contract entity); collapsing is HS-2-04/HS-2-05's job once persistence and host wiring need a single shape.

## Decisions deferred

- Choice of LLM backend(s) for window-level multi-label scoring — DIR-01 settled on `mlx-lm` (Qwen3-8B-MLX-4bit) primary + `llama-cpp-python` (Qwen2.5-3B-Q4_K_M) cross-platform default; MIR-01 is expected to reuse the `LLMRuntime` Protocol from DIR-01 but the per-stage model choice isn't fixed yet.
