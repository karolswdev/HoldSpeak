# HS-27-03 — `decision_capture`: decisions + open questions (net-new, ubiquitous)

- **Project:** holdspeak
- **Phase:** 27
- **Status:** backlog
- **Depends on:** HS-27-01 (pattern for a text artifact + new-plugin registration)
- **Unblocks:** HS-27-05
- **Owner:** unassigned

## Problem

The single most *ubiquitous* meeting output isn't in the stub list at all:
**decisions made** and **open questions left unresolved**. Nearly every meeting
produces both, and capturing them is high-value across every role. This is the
phase's "more ubiquitous than `customer_signal_extractor`" plugin — but it is
**net-new** (no existing stub), so it adds a `_BUILTIN_PLUGIN_DEFS` entry + an
artifact type, not just a stub flip.

## Scope

### In

- New `decision_capture` plugin (`kind="synthesizer"`, deferred,
  `required_capabilities=["llm"]`) following the Phase-16 pattern.
- Register a new `_BUILTIN_PLUGIN_DEFS` entry + map an `artifact_type`
  (e.g. `"decisions"`) in `_ARTIFACT_TYPE_BY_PLUGIN`.
- Output: `{"summary", "confidence_hint", "active_intents", "decisions":
  [{"decision", "rationale"|null}], "open_questions": [str]}`. Validate; clean
  low-confidence failure on garbage.
- Routing: add `decision_capture` to the relevant intent chains (it should run
  on most meeting types — review the MIR router policy and wire it broadly).
- Synthesis body: generic body is acceptable v1; optionally a two-section body
  ("Decisions" / "Open questions"), with non-`decisions` bodies byte-for-byte
  unchanged.
- Unit + integration tests (mirror HS-27-01).

### Out

- `decision_conflict_detector` (cross-meeting contradiction detection) — that's
  a richer, separate RFC candidate; this story is single-meeting capture only.
- Linking decisions to a persistent decision log. Later.

## Acceptance criteria

- [ ] New `decision_capture` plugin registered + artifact type mapped; real
      `run()` returns the validated decisions/open-questions payload.
- [ ] Routed onto the common meeting intent chains (fires broadly, not niche).
- [ ] Parse-failure + capability-blocked paths covered; non-`decisions` bodies
      byte-for-byte unchanged if a custom body is added.
- [ ] Tests green; full sweep green.

## Test plan

- Unit: `tests/unit/test_decision_capture_plugin.py` (mock intel).
- Integration: synthesis + routing — a transcript with a clear decision + an
  unresolved question produces a `decisions` artifact.
- Full sweep + (optional) inclusion in the HS-27-02 e2e demo.

## Notes / open questions

- Confirm ordering vs HS-27-04 (`requirements_extractor`) — see status doc
  "Decisions deferred". Default: do this one first (higher ubiquity).
- Keep on the `.43` Q6 endpoint (no reasoning-leak); no `reasoning_content`
  fallback (project decision).
