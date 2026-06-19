# HSM-5-04 — Structured / JSON output

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** backlog
- **Depends on:** HSM-5-02, HSM-0-02
- **Unblocks:** HSM-5-05, HSM-6-01
- **Owner:** unassigned

## Problem

Meeting intelligence (Phase 6) needs the model to return artifacts in the Phase-0
contract shapes, not free prose. On-device models drift from a requested JSON
shape more than hosted ones, so the runtime needs a structured-output path with
validation and a bounded repair/retry — otherwise Phase 6 builds on sand.

## Scope

- **In:** the plumbing that makes the `ILLMProvider` emit structured JSON
  conforming to the Phase-0 schemas (constrained decoding / grammar if the engine
  supports it, else a validate-and-repair loop); validation of the output against
  the Phase-0 JSON Schemas; a bounded retry budget on validation failure.
- **Out:** the specific artifact prompts and types (Phase 6 / HSM-6-02). The
  parity bar (Phase 6). The provider/engine itself (HSM-5-01/02).

## Acceptance criteria

- [ ] The provider can be asked for output conforming to a Phase-0 schema and the
      result validates against that schema (zero errors) on real meetings.
- [ ] On a validation failure, a bounded repair/retry runs; if it still fails, the
      failure is surfaced honestly (not a silent empty artifact).
- [ ] Constrained decoding is used where the HSM-5-01 engine supports it; where it
      doesn't, the validate-and-repair path is the documented fallback.
- [ ] The retry budget is configurable and recorded (so Phase-6 parity runs aren't
      secretly burning unlimited retries).

## Test plan

- Unit: feed a transcript fixture → request a `Decision`/`ActionItem` shape →
  assert schema-valid output; inject a malformed model response → assert the
  repair/retry path engages and either fixes it or fails loudly.
- Manual / device: structured generation on-device for a real short meeting.

## Notes / open questions

- This is the bridge between "a model runs locally" (HSM-5-02) and "intelligence
  is contract-shaped" (Phase 6). If the engine can't reliably do structured
  output even with repair, that's an HSM-5-01 engine-choice signal — escalate.
- Validation reuses the Phase-0 JSON Schemas (HSM-0-02) — one schema set, both
  runtimes.
