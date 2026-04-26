# Phase 2 — Multi-Intent Routing (MIR-01)

**Last updated:** 2026-04-25 (phase opened — scaffolding only; no story is in-progress yet).

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
| HS-2-01 | Step 0 — Baseline capture | backlog | [story-01-baseline](./story-01-baseline.md) | — |
| HS-2-02 | Step 1 — Contracts + router skeleton | backlog | [story-02-contracts-router](./story-02-contracts-router.md) | — |
| HS-2-03 | Step 2 — Windowing + multi-label scoring | backlog | [story-03-windowing](./story-03-windowing.md) | — |
| HS-2-04 | Step 3 — Plugin host integration | backlog | [story-04-plugin-host](./story-04-plugin-host.md) | — |
| HS-2-05 | Step 4 — Persistence + migration | backlog | [story-05-persistence](./story-05-persistence.md) | — |
| HS-2-06 | Step 5 — Meeting runtime wiring | backlog | [story-06-runtime-wiring](./story-06-runtime-wiring.md) | — |
| HS-2-07 | Step 6 — Synthesis pass | backlog | [story-07-synthesis](./story-07-synthesis.md) | — |
| HS-2-08 | Step 7 — API + CLI surfaces | backlog | [story-08-api-cli](./story-08-api-cli.md) | — |
| HS-2-09 | Step 8 — Config + feature flags | backlog | [story-09-config-flags](./story-09-config-flags.md) | — |
| HS-2-10 | Step 9 — Observability + hardening | backlog | [story-10-observability](./story-10-observability.md) | — |
| HS-2-11 | Step 10 — Full regression gate + DoD | backlog | [story-11-dod](./story-11-dod.md) | — |

## Where we are

Phase opened on 2026-04-25 immediately after DIR-01 closed at
`d6db964`. No story picked up yet. Next move: user picks the first
story to break ground on (likely `HS-2-02` if Step 0 baseline is
dropped per the same "no pre-shipping measurement gate" call that
dropped HS-1-01 — but that's the user's decision, not a presumption
of this scaffold).

## Active risks

Carried forward from spec §12 verbatim:

1. Intent oscillation produces noisy artifacts. Mitigation: hysteresis windows + minimum confidence delta.
2. Plugin explosion increases cost/latency. Mitigation: profile-based plugin allowlist + deferred queue.
3. Overlapping windows duplicate outputs. Mitigation: idempotency key + synthesis dedupe.
4. Stop-path race conditions. Mitigation: persist partial progress + reuse stop-path deadlock tests.

## Decisions made (this phase)

(none yet — phase opened)

## Decisions deferred

- Whether HS-2-01 (Step 0 baseline) ships or is dropped, mirroring the DIR-01 amendment that dropped HS-1-01 and HS-1-10 (no pre-shipping measurement gate). The spec §9.1 still calls for it; the project-level memory says skip pre-measurement / validation gates. User to call.
- Choice of LLM backend(s) for window-level multi-label scoring — DIR-01 settled on `mlx-lm` (Qwen3-8B-MLX-4bit) primary + `llama-cpp-python` (Qwen2.5-3B-Q4_K_M) cross-platform default; MIR-01 is expected to reuse the `LLMRuntime` Protocol from DIR-01 but the per-stage model choice isn't fixed yet.
