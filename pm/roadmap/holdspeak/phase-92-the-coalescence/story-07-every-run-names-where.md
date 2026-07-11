# HS-92-07 — Every run names where it happens

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress
- **Depends on:** HS-92-01, HS-92-02, HS-92-06
- **Unblocks:** HS-92-08, HS-92-09
- **Owner:** unassigned

## Problem

`Profile`, provider, backend, model, endpoint, desktop, mesh, local, cloud, and
mixed combine engine choice, placement, topology, fallback, and trust. Current
RuntimeProfile infrastructure is real and should be adapted, not rebuilt. The
user needs one “Runs on” answer before execution and an actual-placement answer
afterward.

## Scope

- **In:** Additive `InferenceTarget` contract/API name over ProfileRecord;
  model/engine/routing/selection/placement separation; named destination
  boundary/owner/transport/data scope; one Runs-on picker for primary run paths;
  actual placement in attempt/receipt; profile wire aliases and secret behavior;
  offline/missing-key/unsupported target recovery; docs/doctor.
- **Out:** Deleting legacy headless config fallbacks; forcing one model on all
  capabilities; calling a user-owned paired/LAN target same-device local.
- **Paths:** `holdspeak/db/primitives.py`, `holdspeak/intel/providers.py`,
  `holdspeak/intel/engine.py`, `holdspeak/intel/mesh_relay.py`,
  `holdspeak/web/routes/primitives/profiles.py`,
  `holdspeak/web/routes/primitives/ask.py`, `holdspeak/setup_status.py`,
  `web/src/pages/ProfilesPage.tsx`, Desk run/chat pickers,
  `apple/Sources/Providers/Inference/`,
  `apple/Sources/Contracts/EgressScope.swift`, `apple/App/MeetingCapture/AppSettings.swift`,
  `apple/App/MeetingCapture/ProfileKeyStore.swift`, and placement/egress tests.

## Acceptance criteria

- [ ] `InferenceTarget` identifies this device, paired device, private endpoint
      or mesh node, and external service independently of `InferenceEngine`,
      model asset, and fallback/routing policy.
- [ ] Existing `/api/profiles` and sync `profile` shapes remain versioned aliases;
      new canonical reads/writes round-trip through old clients without keys or
      field loss and publish a removal/version plan.
- [ ] Desk Ask, Persona, Workflow, meeting intelligence, dictation rewrite,
      Rails observer, and native run paths use the same Runs-on picker/view model
      and show unavailable targets without capability-by-error probing.
- [ ] Before Run, the UI names target identity and data classes; after Run, the
      Artifact/receipt names actual target, model/engine, fallback reason, and
      boundary used.
- [ ] Same-device local never falls back remotely; automatic fallback that
      crosses a boundary follows ControlMode/authority policy and is visible,
      never inferred from a generic `auto` label.
- [ ] Missing key, unsupported client/target kind, dead endpoint, offline node,
      rejected token, and stale manifest refuse by name with an alternate target
      action that never silently retargets.
- [ ] Web and Swift product strings no longer expose generic Profiles,
      cloud-capable, Local+Cloud, or paired-as-cloud in the primary journeys.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_intel_profile_resolution.py tests/unit/test_dictation_profile_resolution.py tests/unit/test_mesh_relay_provider.py tests/unit/test_mesh_liveness_surfaces.py tests/unit/test_doctor_runtime_profiles.py`; Web picker/receipt tests; Swift RuntimeProfile compatibility and EgressScope replacement fixtures.
- **Integration:** `uv run pytest -q tests/integration/test_runtime_llama_cpp.py tests/integration/test_runtime_mlx.py tests/integration/test_intel_streaming.py tests/integration/test_web_dictation_readiness_api.py`; UAT profile, mesh, endpoint-dead, and egress scenarios.
- **Manual / device:** One control/treatment run each on this device, a paired
  Mac, named mesh node, private LAN endpoint, and external endpoint; kill each
  remote target and verify named refusal, retained input, and no silent fallback.

## Notes / open questions

The canonical product term is the control label **Runs on**. `InferenceTarget`
is the architecture noun. “Cloud” may remain as a boundary detail for a genuine
public service, never as the generic endpoint provider name.
