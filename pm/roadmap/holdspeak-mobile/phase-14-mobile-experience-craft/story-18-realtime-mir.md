# HSM-14-18 — Real-time MIR (live intelligence on the iPad, configurable)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-23. The iPad's intelligence is post-meeting only; the
  desktop runs it **live**. Closes that parity gap, with the owner's refinements (config surfaces,
  gamified tack moment, any-endpoint offload) as first-class.
- **Depends on:** the live capture loop + tacking (HSM-8-03), `InferenceConfigStore` (the inference
  target seam), the Queue HUD (`RunQueueStore`), the generation-theater treatment.
- **Owner:** unassigned

## The parity gap (grounded)

The desktop runs intelligence **during** the meeting: `meeting_session/intel_analysis.py` (*"the live
intel cadence"*) fires `_run_intel_analysis(final=False)` repeatedly over the partial transcript,
**streaming**; `transcribe_loop.py` streams each segment via `on_segment`; `session.py` wires a
`mir_segment_probe` so MIR routes live. The iPad does NONE of this — `MeetingReviewState.generate`
runs at review; tacking only *marks* a moment for that later pass.

## The design (owner-refined)

### 1. Cadence-gated, user-tunable
A live intel pass fires periodically over the growing transcript — never per-segment (it must not
fight Whisper + diarization on one chip). Cadence is **user-configurable** (interval + min-new-segments).

### 2. Tack-triggered — and it's a MOMENT, not a silent task
Tacking fires an intel pass *immediately* on the recent context (the most useful real-time signal:
intelligence on the thing you just flagged). It must be:
- **Explicit** — the tacked card shows a "thinking" state right on the flagged moment.
- **Queued** — a real job populates the **Queue HUD** ("Intel · this moment · {target} · working"), so
  it rides the transparency surface; you see what's asked + where it runs.
- **Gamified** — the result *materializes* with the generation-theater treatment + haptic, not a silent
  append. Tacking → watching intelligence bloom from that moment should feel great.

### 3. Configurable inference target — on-device / mesh / ANY OpenAI endpoint (OpenRouter)
Reuses `InferenceConfigStore` (Mode A on-device / Mode B mesh / Mode C endpoint with URL+key+a model
**fetched** from `/v1/models`). Point Mode C at **`openrouter.ai/api/v1`** → **any model** (GPT-5,
Claude, a cheap fast model for the live cadence), user-chosen + swappable. Egress-honest: the badge
says cloud → {model} when it leaves the device. Resource-aware: offload to the mesh/endpoint when
connected; gentler on-device cadence when air-gapped.

### 4. The SETUP surface (first-class, the owner's emphasis)
A "Real-time intelligence" settings screen where the user actually sets this up: on/off, the cadence
(interval + threshold), tack-trigger on/off, the inference target + endpoint (URL/key/**fetched model
picker**, an OpenRouter preset), and the egress posture made plain.

## Build plan (verifiable pieces; device wiring waits for the iPad's return)
1. **The cadence/trigger brain (host-testable, NOW)** — `LiveIntelCadence`: given (now, lastRun,
   newSegmentsSinceLastRun, tackPending) → fire `.tack` / `.cadence` / nothing; tack-trigger + cadence
   independently toggleable + tunable. Pure, unit-tested.
2. **The live-intel runner** — on a cadence/tack, select the context window, route through the MIR
   profile + the configured provider (`InferenceConfigStore.makeProvider`), produce artifacts
   incrementally; reuse the post-meeting engine where possible.
3. **The Queue HUD + the gamified tack moment** — a live-intel job per pass; the tacked-card "thinking"
   state; the materialize/theater reveal of the result.
4. **The setup screen** — the config UI (cadence, target, OpenRouter endpoint + fetched model picker,
   egress badge).
5. **Device proof** — a real meeting where tacking a moment fires live intel against on-device AND an
   OpenRouter model, with the Queue HUD + the gamified reveal — owner-verified.

## Acceptance criteria
- [ ] `LiveIntelCadence` host-tested (tack always fires when enabled; cadence respects interval +
      min-segments; both independently toggleable). *(this slice)*
- [ ] Live intel runs on cadence + on tack over the partial transcript through the configured target.
- [ ] Tack is explicit (card thinking-state) + populates the Queue HUD + a gamified materialize reveal.
- [ ] Inference target configurable incl. an OpenAI endpoint (OpenRouter) with a fetched model picker;
      egress-honest.
- [ ] A "Real-time intelligence" setup screen exposes all of it.
- [ ] Device-proven: tack → live intel, on-device and via OpenRouter.

## Notes
- Resource reality: on-device LLM during capture competes with Whisper + diarization — hence
  cadence-gating + offload. Don't firehose. See [[project_phase15_the_mesh]] (the iPad-full-peer /
  mesh-additive principle), [[feedback_verify_on_device_not_seeded]].
