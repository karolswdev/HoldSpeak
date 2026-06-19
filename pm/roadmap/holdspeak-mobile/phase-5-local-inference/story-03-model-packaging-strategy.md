# HSM-5-03 — Model packaging & per-device defaults

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** in-progress
- **Depends on:** HSM-5-01
- **Unblocks:** HSM-5-05
- **Owner:** unassigned

## Progress (2026-06-18)

The **per-device default policy** is done + host-tested: `InferenceModel`
(4B/8B/12B+) + `InferenceModelPolicy.defaultModel(for:)` (iPhone→4B, iPad→8B) and
`isAllowed(_:pluggedIn:)` (12B+ only when plugged in, never a default) —
`apple/Sources/Providers/Inference/InferenceModel.swift`, `swift test` green. The
**packaging/download** half (obtaining + storing the model artifacts, first-run
download) is device/dep work that lands with the engine pick (HSM-5-01) and the
chosen runtime — stays in-progress until then.

## Problem

A local model has to get onto the device and be the right size for that device.
The charter's local-model strategy is explicit: iPhone defaults to a 4B model,
iPad to 8B, and 12B+ is experimental and only when plugged in. Without a
packaging + default-resolution story, the app either ships a giant bundle or
loads a model the device can't sustain.

## Scope

- **In:** how the model artifacts are obtained (bundled vs first-run download) and
  stored; the per-device default resolution (4B iPhone / 8B iPad); the 12B+ path
  gated behind plugged-in only and never the default; first-run UX implications
  (download size, where it lives, re-use across runs).
- **Out:** the inference engine choice (HSM-5-01, pins the concrete artifacts).
  The provider implementation (HSM-5-02). Structured output (HSM-5-04). Thermal
  downgrade under stress (Phase 11 owns the hardening matrix; this story sets the
  defaults it will lean on).

## Acceptance criteria

- [ ] On a clean install, the per-device default model is obtained and usable: 4B
      resolves on iPhone, 8B on iPad — verified on real hardware of each class.
- [ ] 12B+ is selectable only when the device is plugged in and is never the
      device default (the resolver refuses it on battery).
- [ ] Models are stored once and re-used across runs (no re-download per launch);
      the storage location and size are documented.
- [ ] The concrete model artifacts (for the HSM-5-01 engine) are pinned by name +
      version, not "latest".

## Test plan

- Unit: the default-resolution logic (device class + power state → model) tested
  across the matrix (iPhone/iPad × battery/plugged).
- Manual / device: clean-install model acquisition on an iPhone and an iPad;
  confirm 12B+ is blocked on battery and allowed plugged in.

## Notes / open questions

- **Sizing is grounded by [`../research/inference-on-apple.md`](../research/inference-on-apple.md)**
  — the budgeting table (4B q4 ~2–4GB peak / 8B q4 ~5–6GB / 12B q4 ~7.5–9.5GB) and
  the feasibility matrix. The defaults: **4-bit PTQ** is the shipping default
  (3-bit only to rescue a tight fit); **4B iPhone / 8B iPad** matches the charter;
  **12B is 16GB-iPad-only or hybrid**, with **7B the practical phone upper bound**.
  Confirm against HSM-5-01's measured numbers, which override the estimates.
- Apple Intelligence itself uses ~7GB on-device — multi-GB assets are normal but
  must be budgeted explicitly; prefer **download-after-install** over bundling.
- First-run download size is a real UX cost — note it for the onboarding the
  iPhone/iPad experience phases (8–9) will surface.
- Pin exact artifacts so Gate 4 (HSM-5-05) and Phase-6 parity are measured against
  a known model, not a moving target.
