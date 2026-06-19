# HSM-5-02 — `ILLMProvider` impl + Mode A

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** in-progress
- **Depends on:** HSM-5-01
- **Unblocks:** HSM-5-04, HSM-5-05, HSM-6-01
- **Owner:** unassigned

## Progress (2026-06-18)

The seam the impl plugs into is ready + host-tested: the `ILLMProvider` protocol
(`complete(prompt:)`) and the `StructuredOutput.generate(...)` layer on top of it
(HSM-5-04) that turns a provider's text into validated contract values with a
bounded repair-retry — exercised by a fake provider. The **concrete engine-backed
`ILLMProvider`** (the HSM-5-01 engine + a model, running Mode A on a device) is
device/dep work and stays in-progress until then.

## Problem

The engine pick (HSM-5-01) is a decision, not a running provider. The runtime
needs a concrete `ILLMProvider` (Layer 3) on the chosen engine so the Runtime
Core can run inference without knowing which engine sits underneath, and so Mode
A (fully local) works end to end.

## Scope

- **In:** the `ILLMProvider` implementation on the chosen engine; loading a model
  and running a completion on-device; wiring Mode A so a transcript can reach the
  provider with no network. The provider stays behind the Layer-3 abstraction so
  Modes B (homelab) and C (endpoint) can be other implementations of the same
  interface later.
- **Out:** the engine evaluation itself (HSM-5-01). Structured/JSON output
  shaping (HSM-5-04). Model packaging/download (HSM-5-03 — this story can assume a
  model is present locally). The Mode B/C providers. Artifact prompts (Phase 6).

## Acceptance criteria

- [ ] `ILLMProvider` is implemented on the HSM-5-01 engine and returns a
      completion for a prompt on a Tier-1 device.
- [ ] Mode A runs end to end with the network disabled (airplane mode): a
      transcript reaches the provider and a response comes back, no egress.
- [ ] The Runtime Core calls only the `ILLMProvider` interface — swapping the
      engine would not touch core code (proven by the call site depending on the
      protocol, not the concrete type).
- [ ] Cold-load and warm-call behavior is documented (load time, memory) for the
      per-device default model.

## Test plan

- Unit: a fake `ILLMProvider` proves the Runtime Core depends only on the
  interface; the real provider has an on-device smoke test (load + one completion).
- Manual / device: airplane-mode Mode A run on a Tier-1 device — transcript in,
  response out, no network.

## Notes / open questions

- Keep the interface narrow and engine-agnostic; anything engine-specific
  (sampling, grammar/constrained decoding) lives behind the protocol so HSM-5-04
  can lean on it without leaking the engine into the core.
- This is where Mode A becomes real — the charter's headline "no laptop, fully
  local" promise rides on this story plus HSM-5-05.
