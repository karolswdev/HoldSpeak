# HS-130-03 — One deployment identity: readiness, execution, receipt agree

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** HS-130-01
- **Unblocks:** HS-130-04
- **Owner:** unassigned

## The thesis (the bar)

Readiness, execution, and the receipt must name the same deployment. Today
they diverge three ways:

- **`this_machine`:** `_this_machine_readiness` (inference_targets.py:152-179)
  checks the dictation runtime backend/model paths; execution loads
  `meeting.intel_realtime_model` (inference_targets.py:394-414,
  intel/providers.py:209-237). Ready for one model, runs another.
- **Named on-device:** readiness and identity derive from `profile.model_file`
  (inference_targets.py:232-244); execution ignores it and loads the global
  meeting model (providers.py:430-438); `build_intel_for_target` passes
  `profile.model` but never `model_file` (inference_targets.py:417-426); the
  receipt stamps `target.model` (recipe_service.py:183-185,
  placement_receipt inference_targets.py:146-147). Reports model A, runs B,
  attests A.
- **`paired_device`:** `paired_device_target` hardcodes
  `readiness_state="ready"` with no check (inference_targets.py:202-217) and
  delegates execution to a possibly-unrunnable `build_configured_meeting_intel`
  (inference_targets.py:415-416).

### What changes

1. A single **deployment identity** — the (destination, engine, model, node,
   boundary) tuple — is computed once and is the thing readiness checks,
   execution loads, and the receipt stamps. Readiness that passes means *this
   deployment will load*; a receipt names *the deployment that loaded*.
2. The on-device execution branch consumes the same `model_file`/`model` that
   made the target ready; `build_intel_for_target` carries the full deployment,
   not a partial (`profile.model` only).
3. `paired_device` readiness reflects a real check; a paired target that
   cannot run does not report ready.
4. The receipt stamp derives from the executed deployment, not the profile's
   advertised `target.model`.
5. Kept kernel-free: this story unifies the identity used by the existing
   `build_intel_for_target` path. The *immutable revision* of that identity
   (capture-at-admission, execute-exact-revision) is Phase 131 — this story
   makes the identity singular so 131 has one true thing to freeze.

## Acceptance criteria

1. For `this_machine`, named on-device, and `paired_device`: readiness, the
   executed engine's model, and the emitted receipt name the same model and
   destination.
2. A target that reports ready loads without a "model not found" at run time
   for the model readiness attested (the readiness/execution divergence tests
   reproduce on the pre-change tree and pass after).
3. `paired_device` cannot report ready when its execution path is unrunnable.
4. No receipt stamps a model the run did not load.

## Test plan

- Backend: per-target-kind tests asserting readiness-model == execution-model
  == receipt-model; a regression for the on-device A/B split; a paired-device
  unrunnable→not-ready test.
- Full backend suite read from file before flip.

## Out of scope

- Immutable deployment revisions and capture-at-admission (Phase 131).
- Egress/boundary vocabulary (HS-130-04 consumes this identity).
- Kernel admission of the run (Phase 131).
