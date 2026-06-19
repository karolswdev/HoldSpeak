# HSM-5-06 — OpenAI-compatible endpoint provider (Modes B/C) + runtime-mode setting

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** in-progress (provider + setting + host/live proof done; on-device
  launch pending the iPad unlock)
- **Depends on:** HSM-5-04 (structured-output bridge), HSM-6-01 (artifact engine)
- **Unblocks:** HSM-6-05 (a real on-device `ILLMProvider` now exists)
- **Owner:** unassigned

## Why this story exists (owner steer 2026-06-19)

The owner steered, mid-Phase: **inference mode should be a user setting** (local is
the privacy default), **and the runtime must support any OpenAI-compatible
endpoint** — because a laptop/homelab is often on the same LAN, and you'd rather
point at an always-available endpoint than spend the iPad's unified memory on a
resident model. That is exactly the charter's Mode B (homelab, recommended) and
Mode C (endpoint). It is also the *fastest* path to real on-device inference: an
HTTP provider has no native dep, no GGUF download, and no Metal build, so it makes
the iPad genuinely useful for meetings now and **unblocks the blocked Phase-6
parity verdict (HSM-6-05)** — which needs *an* on-device `ILLMProvider`, not
specifically the local one.

This story therefore ships ahead of HSM-5-02 (on-device GGUF, Mode A), which
remains the follow-on push for true airplane-mode-local inference.

## Scope

- **In:** `OpenAIEndpointProvider` (an `ILLMProvider` over `POST {base}/chat/
  completions`, Foundation/URLSession only); a `RuntimeMode` setting
  (`.local`/`.homelab`/`.endpoint`) + `EndpointConfig` + an
  `InferenceProviderFactory` that turns the setting into a provider; host unit
  tests (stubbed `URLProtocol`); a live integration proof against a real endpoint;
  an on-device harness (Mode C) that generates artifacts on the iPad.
- **Out:** the on-device GGUF engine (Mode A — HSM-5-02). Model packaging
  (HSM-5-03). The Phase-8/9 production UI (this is a dev harness). The formal
  Gate-5 verdict (HSM-6-05 — needs the owner-signed baseline + rubric).

## Acceptance criteria

- [x] `OpenAIEndpointProvider` implements `ILLMProvider` and returns a completion
      from an OpenAI-compatible endpoint; engine-specific concerns stay behind the
      protocol so the Runtime Core is unchanged.
- [x] Inference mode is a setting: `RuntimeMode` + `EndpointConfig` +
      `InferenceProviderFactory.make(mode:endpoint:)`; `.local` returns a clear
      `localEngineUnavailable` until HSM-5-02 lands (no crash).
- [x] Host tests prove request shaping, response parse, and error handling without
      a network (stubbed `URLProtocol`); RuntimeCore depends only on the interface.
- [x] A live run generates real, contract-shaped artifacts from a transcript
      against a real endpoint (host-side rehearsal of the device path).
- [ ] The harness runs on the **physical iPad Air M4**: transcript → endpoint →
      artifacts on-device (pending the device unlock to launch).

## Test plan

- Unit: `OpenAIEndpointProvider` via `URLProtocol` stub + factory tests
  (`apple/Tests/ProvidersTests/EndpointProviderTests.swift`).
- Live (opt-in, `HS_LIVE_ENDPOINT`): transcript → engine → artifacts + a parity
  scorer run on the real output
  (`apple/Tests/RuntimeCoreTests/LiveEndpointIntegrationTests.swift`).
- Device: `apple/scripts/harness-device.sh` builds/signs/installs/launches the
  Mode-C harness on the iPad.

## Progress & evidence (2026-06-19)

Proof captured ahead of `done`; the standalone `evidence-story-06.md` ships when the
on-device launch lands and this story flips to `done`.

- **Host suite:** `cd apple && swift test` → **46/46** (was 38; +8 endpoint tests),
  48 with the 2 opt-in live tests (skipped without `HS_LIVE_ENDPOINT`).
- **Live, real model** (`HS_LIVE_ENDPOINT=http://192.168.1.13:8081/v1`, clean
  `llama-server` Qwen2.5-7B-Instruct Q4_K_M on the LAN): transcript → engine →
  real contract-shaped artifacts (decisions / action_items / requirements), and the
  HSM-6-05 parity *mechanism* scores that real output **coverage 1.00, PASS**
  (threshold 0.8).
- **iPad Air M4 ("AjPed"):** `apple/scripts/harness-device.sh` →
  `** BUILD SUCCEEDED **` → `App installed: bundleID dev.holdspeak.mobile`. Launch
  blocked only by `FBSOpenApplicationErrorDomain Locked` (device lock screen). One
  `xcrun devicectl … process launch` finishes it once unlocked.

## Notes / open questions

- The owner's `.43` homelab box currently forces every response into a
  `{"line": "<string>"}` grammar (server-side), so it is not a clean
  general-purpose endpoint for arbitrary structured output. The live proof used a
  clean `llama-server` (Qwen2.5-7B-Instruct Q4_K_M) on the dev Mac over the LAN —
  itself the canonical Mode-B scenario. Open: do we want `.43` relaunched without
  the forced grammar, or is per-call `response_format` the contract we target?
- iOS Local Network privacy: the harness declares `NSLocalNetworkUsageDescription`
  and ATS local-networking; the device prompts once for Local Network permission
  (owner taps Allow).
- The default mode is a product decision: local-as-privacy-default vs
  homelab-as-recommended (charter calls Mode B "recommended"). Surfaced to owner.
