# HSM-14-17 — On-device speaker diarization (who's talking, air-gapped)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-23. **The model-conversion spike SUCCEEDED** (the
  highest-risk piece). On owner request after recording was stabilised.
- **Depends on:** the live capture pipeline (`MeetingCapture`), the `Segment.speaker`/`speakerId`
  slot (already reserved), WhisperKit (transcription — does NOT diarize).
- **Owner:** unassigned

## Why / the desktop parity

The desktop diarizes (`holdspeak/speaker_intel.py`, opt-in `diarization_enabled`): resemblyzer's
`VoiceEncoder` turns each speech chunk into a **256-dim embedding**, and `SpeakerDiarizer` matches it
by **cosine similarity** against known speakers (threshold + EMA-updated profiles), labelling
"Speaker 1/2/…" with optional cross-meeting identity + rename. The iPad has the `speaker`/`speakerId`
slot wired but does nothing today (every line is "Speaker 1"). Whisper never produces speaker info, so
this is a separate pipeline on any platform.

## The spike (DONE, 2026-06-23) — the hard part is de-risked

Converted resemblyzer's `VoiceEncoder` (`LSTM(40→256)×3 + Linear(256) → 256-dim, L2-normalised`) to
**Core ML** (`apple/ml/VoiceEncoder.mlpackage`, **5.6 MB**, `mlprogram`, iOS16). Validation:
**PyTorch vs Core ML cosine = 0.99999–1.0** across runs — *bit-exact* embeddings. Conversion script:
`apple/ml/convert-voice-encoder.py` (`coremltools 9.0` on py3.13; torch 2.9). **Because it's the same
encoder, on-device embeddings are compatible with the desktop's** → cross-device speaker identity is
possible later. Input: `mels(1,160,40)` (one ~1.6s partial); output: the embedding.

## What's left (the real remaining work)

1. **Mel front-end in Swift, matching resemblyzer's exactly** — 16 kHz audio → 40-mel log spectrogram
   (resemblyzer's librosa params: 25 ms window / 10 ms hop / 40 mels). The embeddings only match the
   desktop if the mel matches librosa's. **Two options:** (a) replicate librosa's mel in Swift
   (Accelerate/vDSP); (b) **bake the mel into the Core ML model** via a `torchaudio.MelSpectrogram`
   tuned to librosa's params, so the model takes **raw 16 kHz audio → embedding** and Swift needs no
   DSP. (b) is cleaner — the next spike: prove a torchaudio mel matches librosa within tolerance, then
   re-convert audio→embedding end to end. This is the main remaining risk.
2. **The Swift diarizer (pure, host-testable NOW)** — `SpeakerDiarizer` mirroring the desktop: cosine
   similarity, a match threshold, EMA profile update (`alpha 0.3`), new-speaker creation, relative
   labels. No model/device needed to build + unit-test the matching/clustering logic.
3. **Segmentation / partials** — split the captured speech into ~1.6s partials (or VAD-bounded), embed
   each via the Core ML model, average per utterance (resemblyzer's approach), assign a speaker.
4. **Wire into capture** — set `Segment.speaker`/`speakerId` on the live + final transcript; keep it
   **opt-in** (a setting), **on-device / air-gapped** (the iPad-full-peer principle).
5. **UI** — speaker labels + colours/avatars on the transcript + bubbles; rename; (later) cross-meeting
   identity matched against a speaker store.

## Update (2026-06-23) — the ENTIRE model side is de-risked, no unknowns left

- **End-to-end audio→embedding Core ML model: DONE** (`apple/ml/AudioEmbed.mlpackage`, **3.1 MB**,
  iOS17, `convert-audio-embed.py`). It bakes the mel front-end IN — `torch.stft` (matching librosa via
  librosa's own filterbank as a constant) + the encoder — and **`torch.stft` converts to Core ML
  cleanly**. Validation: the model's embedding vs resemblyzer = **cosine 0.99993** on raw 1.6s audio.
  So **Swift needs ZERO DSP** — feed 1.6s audio slices → embedding. (The mel-only `VoiceEncoder.mlpackage`
  stays as a reference.)
- Net: encoder converts bit-exact (0.99999), mel matches (0.9993), end-to-end audio→embedding matches
  (0.99993), and the Swift matcher is host-tested (6/6). All three risk pieces answered.
- **Remaining is straightforward engineering, no research:** a Swift Core ML wrapper (load + `predict`),
  partial-slicing + averaging of the captured audio, volume-normalise to match resemblyzer's
  preprocess, wire `Segment.speaker` in the capture loop, an opt-in setting, UI labels — then the only
  real proof left: a 2-speaker recording separating on the device.

## Acceptance criteria
- [x] **Spike:** resemblyzer encoder → Core ML, bit-exact embeddings (cosine ≈ 1.0), small enough to
      bundle. (`apple/ml/VoiceEncoder.mlpackage`, 5.6 MB.)
- [x] **Mel front-end matches resemblyzer/librosa** — baked into the end-to-end Core ML model
      (`AudioEmbed.mlpackage`), validated at cosine 0.99993 vs resemblyzer. No Swift DSP needed.
- [x] **`SpeakerMatcher` (Swift) — cosine/threshold/EMA/new-speaker/cross-meeting/rename, host-tested
      6/6** (`Sources/RuntimeCore/Diarization/SpeakerMatcher.swift`, orchestrator-verified).
- [ ] Embeds real audio on-device → distinct speakers separated on a real 2+ speaker recording (device).
- [ ] Opt-in setting; labels render on the transcript; air-gapped.

## Test plan
- Host: the Swift diarizer matching logic (synthetic embeddings → correct cluster assignment); the mel
  front-end validated numerically against the Python/librosa reference (cosine of resulting embeddings).
- Device: a real 2-speaker recording separates into ≥2 speakers; owner-verified.

## Notes
- The encoder being identical to the desktop's is the unlock for **cross-device speaker identity** —
  worth preserving (don't swap encoders for convenience).
- Opt-in + on-device by default (air-gapped); a mesh path (offload to the desktop's resemblyzer when
  connected) is a bonus, not the primary. See [[feedback_verify_on_device_not_seeded]] — the device
  proof (2 real speakers separated) is the only acceptance that counts for the felt feature.
