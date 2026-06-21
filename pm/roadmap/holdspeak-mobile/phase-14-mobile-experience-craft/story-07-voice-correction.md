# HSM-14-07 — Voice correction: reject by voice → the local model re-routes

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (host core tested + app built + deployed to the iPad; on-device voice→correct proof = owner verification)
- **Depends on:** HSM-14-03 (the artifact surface), HSM-6-01 (engine), HSM-5-02 (Mode A), HSM-3 (WhisperKit)
- **Owner:** unassigned

## Problem (owner's vision)

> "Allow the user to reject a specific deliverable and quickly, orally say what is wrong with
> it, so it can be re-routed to the local model — the output + what the user said is wrong —
> to regenerate the output correctly. Corrections with local AI, using our voice."

A world-class on-device intelligence engine should let you **fix a wrong artifact by talking
to it** — no typing, no cloud. And the owner's follow-up: when the rejected card regenerates,
that must be **visually pleasing and extremely smooth** — an extreme-proficiency moment.

## Scope

- **In (host, tested):** `ArtifactCorrection` (RuntimeCore) — a pure prompt that **fuses the
  original output + the user's spoken correction + the transcript**, and `corrected(...)`
  that runs the existing engine over the local provider and returns a corrected `.draft` of
  the same type, stamped with a `voice_correction` source. Host-tested (prompt fusion +
  same-type draft + provenance).
- **In (app, on device):** a short **on-device voice capture** (`VoiceCaptureState`:
  `AudioCaptureService` → `WhisperKitTranscriber`, no meeting created); a **VoiceCorrectionSheet**
  ("What's wrong?" → big animated mic → transcribed correction, or type it → Regenerate);
  `MeetingReviewState.correct(_:spoken:)` which re-routes to `LlamaProvider` and **regenerates
  the artifact IN PLACE** (same id → the card morphs, no duplicate).
- **In (the smooth moment):** while a card regenerates it shows a **"re-thinking" effect** —
  a tint **shimmer sweep**, a **glowing border**, a pulsing **sparkle badge** over the blurred
  old content; the corrected content is revealed underneath as the overlay fades. Submitting
  the correction closes back to the meeting so the owner watches the card itself transform.
- **Out:** multi-turn correction conversations; correcting non-model artifacts; cloud anything
  (fully local). Per-field structured edits (this regenerates the artifact body).

## Acceptance criteria

- [x] **Correction engine (host-tested):** the prompt fuses original + spoken correction +
      transcript; `corrected()` returns a same-type `.draft` with `voice_correction` provenance.
- [x] **Say what's wrong on-device:** record → WhisperKit transcribes the correction (type
      fallback), no network, no meeting created.
- [x] **Re-route + regenerate in place:** the local model regenerates the artifact addressing
      the correction; same id so the card updates, not duplicates (propose-and-confirm draft).
- [x] **The smooth moment:** the regenerating card shows the shimmer + glow + sparkle
      "re-thinking" effect, then morphs to the corrected content.
- [ ] **Owner-verified on the iPad:** speak a correction on a real artifact and watch it
      re-think + come back corrected (the LLM-shaped proof — pending the owner at the device).

## Evidence

`ArtifactCorrection.swift` + `ArtifactCorrectionTests.swift` (`swift test` → 203/0, +2).
`MeetingCaptureApp.swift` — `VoiceCaptureState`, `VoiceCorrectionSheet`,
`MeetingReviewState.correct`, and the `regenerating` card effect. **Device build SUCCEEDED**;
installed + launched on the iPad Air M4. Mic permission already declared (meeting capture).

## Notes

- Regenerates **in place** (same id) deliberately — the rejected card *becomes* the corrected
  one, which is both cleaner and the canvas for the smooth re-thinking effect (owner's ask).
- Fully local: WhisperKit (voice) + LlamaProvider (regeneration), no network — keeps the
  air-gapped posture ([[project_phase8_...]] HSM-8-05) intact.
