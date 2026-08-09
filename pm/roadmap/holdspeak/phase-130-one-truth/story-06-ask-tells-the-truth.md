# HS-130-06 — Ask tells the truth: no model-name retargeting

- **Project:** holdspeak
- **Phase:** 130
- **Status:** backlog
- **Depends on:** HS-130-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Ask can silently replace an explicit destination. It accepts `model`,
`inference_target_id`, and `profile_id`; the target is resolved from the id
(ask_service.py:69-70), then if `model` does not match the resolved profile's
model, ask **scans all profiles and rebinds to the first whose model name
matches** (ask_service.py:76-77), discarding the caller's chosen destination
with no error and no receipt of the substitution; the same happens toward
`this_machine` (:78-79). And `list_models` dedupes by model name across
destinations (ask_service.py:30-47), so two destinations serving one model name
are indistinguishable and the "first match" is arbitrary (ORDER BY name). A
stale model value can retarget a run to another endpoint and another egress
boundary.

### What changes

1. **Target id selects placement. A model choice may only select a model that
   the resolved target advertises.** A mismatching model name is a refusal
   with an actionable message, never a silent hop to another destination.
2. The cross-profile model scan (ask_service.py:76-79) is removed; Ask
   resolves through HS-130-01's resolver and stays on the resolved target.
3. `list_models` stops deduping across destinations; two destinations serving
   the same model name remain distinct and addressable (id, not name, is the
   selector).
4. Ask's egress badge derives from HS-130-04's one vocabulary (the duplicated
   `_run_egress` copy in ask_service.py:171-180 is removed by HS-130-04; this
   story ensures Ask reads the shared boundary).

## Acceptance criteria

1. An Ask call with an explicit `inference_target_id` runs on that target or
   refuses; it never silently retargets by model name.
2. A model name that the target does not advertise is refused with a message
   naming the target and its available models — not substituted.
3. `list_models` returns per-destination entries; two destinations with the
   same model name are both present and distinguishable by id.
4. No Ask run crosses to a different egress boundary than the resolved
   target's.

## Test plan

- Backend: retarget-refusal test (reproduces the silent hop on the pre-change
  tree); mismatched-model refusal test; `list_models` no-dedup test;
  boundary-stability test.
- Full backend suite read from file before flip.

## Out of scope

- Routing Ask through kernel admission and the Ask definition/revision design
  beat (Phase 131 — Ask has no definition object for the codec today; that is a
  design story, not this cleanup).
