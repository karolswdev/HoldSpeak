# HS-27-04 — `requirements_extractor` real run

- **Project:** holdspeak
- **Phase:** 27
- **Status:** done
- **Depends on:** HS-27-01
- **Unblocks:** HS-27-05
- **Owner:** unassigned

## Problem

`requirements_extractor` is registered (`kind="synthesizer"`,
`artifact_type="requirements"`) but is still a `DeterministicPlugin` stub. It's
common on eng/product/planning meetings (less universal than action items or
decisions, hence after them this phase). Flipping it to real is a low-risk
re-application of the proven pattern and is the RFC's nominated "first slice"
companion to `action_owner_enforcer`.

## Scope

### In

- Real `RequirementsExtractorPlugin` (deferred, `required_capabilities=["llm"]`),
  registered in place of the stub.
- Output: `{"summary", "confidence_hint", "active_intents", "requirements":
  [{"text", "type": "functional"|"non_functional"|"constraint"|"acceptance"}]}`.
  Validate; clean low-confidence failure on garbage.
- Generic synthesis body is fine v1 (optionally a grouped list). Non-affected
  artifact bodies byte-for-byte unchanged.
- Unit + integration tests (mirror HS-27-01).

### Out

- Traceability links (requirement → source segment). Later.
- The other stubs.

## Acceptance criteria

- [x] Real `run()` returns the validated `requirements` payload; failure +
      capability-blocked paths covered.
- [x] `register_builtin_plugins` returns the real class for
      `requirements_extractor`; others unaffected.
- [x] Tests green; full sweep green.

## Test plan

- Unit: `tests/unit/test_requirements_extractor_plugin.py` (mock intel).
- Integration: transcript with requirement-flavored content → `requirements`
  artifact.
- Full sweep + (optional) inclusion in the HS-27-02 e2e demo.

## Notes / open questions

- May be cut/deferred if HS-27-01/02/03 consume the phase budget — see status
  doc "Decisions deferred". It's the lowest-priority of the three plugins here.
