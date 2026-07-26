# HS-103-04 - Endpoint health — honest fallback across Runs-on destinations

- **Project:** holdspeak
- **Phase:** 103
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The research finding (the bar)

A research pass over `ViuGiaLai/researchmind` (MIT-licensed, examined
for carry-over ideas only) found `backend/chat/provider_resilience.py`
— a small (~50-line), self-contained, thread-safe circuit breaker:
`ProviderHealth` opens a cooldown after a consecutive-failure
threshold, `score()` blends a Laplace-smoothed success ratio with
measured latency, and `rank()` reorders a configured provider list by
that score while preserving the caller's original order for endpoints
it hasn't seen fail yet. Two independent analyst agents (architecture
and feasibility, run separately with no shared context) landed on this
same file unprompted — a stronger signal than either report alone.

HoldSpeak today has multiple registered "Runs on" destinations
(`holdspeak/intel/providers.py` — `resolve_intel_provider`,
`effective_intel_cloud`, `effective_dictation_llm`, plus the mesh-relay
routing in `holdspeak/intel/mesh_relay.py`) and no ranking or
circuit-breaking between them: a profile pointing at an unreachable
endpoint fails per-request with no memory, and there's no honest
"this endpoint has been down for the last N calls" signal anywhere in
the doctor/health surface. The feasibility analyst's objection — "you
only have one live provider today, so you don't need failover" — is
only half right: the real value isn't redundant-provider failover, it's
not hammering a dead endpoint and giving an honest, measured signal
instead of a bare per-call timeout.

## Problem

There is no shared health/circuit-breaker state across HoldSpeak's LLM
endpoint call sites (dictation runtime, meeting intel, mesh relay,
Ask-AI). A misconfigured or temporarily-down profile degrades silently
per-call with no memory and no honest surfaced state.

## Scope

- In: a small, dependency-free `EndpointHealth`/circuit-breaker module
  (adapt the researchmind pattern directly — it's short and clean
  enough to reimplement from scratch rather than vendor, consistent
  with this project's greenfield/no-vendoring posture) keyed by
  endpoint identity (profile id / base URL), recording
  success/failure/latency per call and exposing a `snapshot()` for a
  doctor/health surface. Wire it into AT LEAST the dictation-runtime
  and meeting-intel call sites in `holdspeak/intel/providers.py` (the
  two most user-visible paths) so a call to a circuit-open endpoint
  fails fast with an honest "this endpoint has been unreachable" reason
  instead of a bare timeout, and the health snapshot is reachable from
  the existing doctor checks (`collect_doctor_checks()` /
  `holdspeak doctor`).
- Out: the mesh-relay routing logic itself (unchanged — this adds a
  health layer alongside it, doesn't redesign routing); any UI surface
  beyond exposing the snapshot through the existing doctor/health
  plumbing (a dedicated health dashboard, if wanted, is a follow-up,
  not this story); provider RANKING/reordering when only one endpoint
  is configured (the common case today) — the breaker's value here is
  honest circuit-open state, not reordering a list of one.

## Acceptance criteria

- [ ] A pure, unit-testable `EndpointHealth` class/module exists
      (success/failure recording, cooldown-after-N-failures, a
      `score()`/`snapshot()` read path) with tests covering: healthy
      endpoint stays closed, N consecutive failures opens the circuit,
      circuit-open calls fail fast without attempting the network call,
      and the circuit recovers after cooldown.
- [ ] At least the dictation-runtime and meeting-intel provider-resolution
      paths consult it before calling out, and record the outcome
      after.
- [ ] `holdspeak doctor` (or the existing doctor-check collection)
      surfaces circuit-open endpoints as an honest, named check —
      verified live by pointing a profile at a deliberately unreachable
      address and confirming the doctor output names it after the
      failure threshold trips.
- [ ] No behavior change for the common single-healthy-endpoint case
      (confirm the full existing intel/dictation test suite stays
      green — this is additive instrumentation, not a routing
      rewrite).

## Test plan

- Unit: a new `tests/unit/test_endpoint_health.py` covering the
  breaker in isolation (open/close/cooldown/score), plus targeted
  tests on the two wired call sites confirming a circuit-open endpoint
  short-circuits.
- Integration: `uv run pytest -q` on `tests/unit/test_intel_*` and
  dictation-runtime tests to confirm no regression in existing routing
  behavior.
- Manual / device: point a `Runs on` profile at an unreachable address,
  make several calls, confirm fast honest failure and a doctor-visible
  circuit-open state; restore reachability and confirm recovery after
  cooldown.

## Notes / open questions

Reimplement from scratch rather than copy researchmind's file verbatim
— it's ~50 lines, MIT-licensed (compatible, but this project's
constitution favors precise from-scratch craft over vendoring per
`docs/internal/CONSTITUTION.md`), and HoldSpeak's call sites are
synchronous/async-mixed in a way that likely needs its own
threading/asyncio-lock shape rather than a line-for-line port. Decide
the failure-threshold and cooldown-duration constants deliberately
(name them, comment why) rather than copying researchmind's defaults
unexamined.
