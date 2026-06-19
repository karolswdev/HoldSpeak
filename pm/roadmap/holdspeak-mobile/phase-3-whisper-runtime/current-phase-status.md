# Phase 3 — Whisper Runtime

**Status:** planning (scaffolded 2026-06-18). Track D of the Council
Implementation Charter. The transcription provider phase: it stands up the first
real `ITranscriber` (Layer 3) on Apple hardware via WhisperKit, feeding the audio
captured in Phase 2 through to speaker-ready segments in the Phase-0 contract
shape.

**Last updated:** 2026-06-18 (scaffolded — stories HSM-3-01..05 stubbed from the
charter Track D deliverables; no work started).

## Goal

Build the WhisperKit-backed `ITranscriber` provider for the mobile runtime:
real-time transcription, chunk transcription, language selection at parity with
the desktop's 99-language registry, and speaker-ready segmentation that emits
`Segment` shapes per the Phase-0 contracts. The phase exits when realtime
transcription latency stays below 2 seconds on Tier-1 hardware — the charter's
Track D gate and program Gate 3.

## Scope

- **In:** the WhisperKit transcriber behind the `ITranscriber` abstraction with
  per-device model loading (Whisper Base on iPhone, Whisper Small on iPad per the
  local-model strategy) (HSM-3-01); streaming realtime transcription plus chunk
  transcription over the `AudioChunk` stream from Phase 2 (HSM-3-02); language
  selection reaching 99-language parity with the desktop registry, default `auto`
  (HSM-3-03); speaker-ready segmentation emitting the Phase-0 `Segment` contract
  (HSM-3-04); the Gate-3 latency measurement and closeout (HSM-3-05).
- **Out:** any LLM/intelligence work — artifacts, MIR, summaries (Phases 5–7).
  Real speaker diarization (assigning identities to voices) — this phase produces
  *speaker-ready* segments (the shape and segment boundaries diarization will
  attach to), not diarization itself. The audio capture pipeline (Phase 2, the
  upstream `AudioChunk` source). Persistence of segments to SQLite (Phase 4).

## Exit criteria (evidence required)

- [ ] A `WhisperKitTranscriber` conforms to the `ITranscriber` abstraction and
      loads the per-device default model (Base on iPhone, Small on iPad) on a
      Tier-1 device (HSM-3-01).
- [ ] Realtime streaming transcription and discrete chunk transcription both run
      over the Phase-2 `AudioChunk` stream and return text + timings (HSM-3-02).
- [ ] Language selection covers the desktop's 99-language registry with `auto` as
      the default, and a non-`auto` selection measurably changes the decode
      (HSM-3-03).
- [ ] Emitted segments validate against the Phase-0 `Segment` JSON Schema and
      carry the speaker-ready fields (timing + a speaker slot) (HSM-3-04).
- [ ] **Track D gate / Gate 3:** measured realtime transcription latency stays
      below 2 seconds on Tier-1 hardware, recorded with the measurement method and
      raw numbers (HSM-3-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-3-01 | WhisperKit transcriber behind ITranscriber | backlog | [story-01](./story-01-whisperkit-transcriber.md) | — |
| HSM-3-02 | Realtime + chunk transcription | backlog | [story-02](./story-02-realtime-and-chunk-transcription.md) | — |
| HSM-3-03 | Language selection (99-language parity) | backlog | [story-03](./story-03-language-selection.md) | — |
| HSM-3-04 | Speaker-ready segmentation | backlog | [story-04](./story-04-speaker-ready-segmentation.md) | — |
| HSM-3-05 | Latency gate closeout (< 2s) | backlog | [story-05](./story-05-latency-closeout.md) | — |

## Where we are

Just scaffolded. The audio engine (Phase 2, Track C) supplies the `AudioChunk`
stream this phase transcribes, and the Phase-0 `Segment` contract fixes the shape
the segments must land in. The five stories are stubbed against Track D's four
responsibilities (realtime, chunk, language selection, speaker-ready
segmentation) plus the Gate-3 latency closeout that proves the < 2s bar on real
hardware. Next: pick up HSM-3-01 and stand up WhisperKit behind the
`ITranscriber` abstraction once HSM-2-03 (the `AudioChunk` shape) lands.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| WhisperKit realtime latency exceeds 2s on the iPhone Tier-2 target (Base model, A-series) | high | Measure early on iPhone, not just iPad; tune chunk window + model variant before building the segmentation layer on top | iPhone Base-model realtime latency can't get under 2s after model/window tuning — escalate the gate (per-tier latency bar) to HSM-0-05's owner Gate confirmation |
| WhisperKit's language set diverges from the desktop's 99-language registry | medium | Map WhisperKit's supported languages against the desktop registry; record any gap as a parity note, don't silently drop languages | WhisperKit supports fewer than the desktop's 99 — document the delta and confirm the parity bar with the owner before claiming parity |
| WhisperKit segment boundaries don't carry enough to be speaker-ready | medium | Define the speaker slot in the `Segment` mapping (HSM-3-04) against the Phase-0 contract; leave diarization out but reserve the field | WhisperKit gives no usable per-segment timing for a speaker slot — revisit the `Segment` contract with Phase 0 rather than forking the shape |
| Model load (Base/Small) blows the memory/thermal budget on a Tier-2 iPhone | medium | Load the per-device default only; verify on-device memory + thermal during a realtime run, not just a cold load | A realtime run thermally throttles or OOMs on iPhone 17 Pro Max — drop to a smaller variant and re-baseline the gate |
| Realtime and chunk paths drift into two transcribers | low | One `WhisperKitTranscriber`; realtime and chunk are two entry points on the same provider, not two implementations | A second transcriber class appears for chunk mode — collapse it back onto the one provider |

## Decisions made (this phase)

- 2026-06-18 — Phase 3 ships *speaker-ready* segmentation, not diarization: it
  produces the `Segment` shape (timing + a reserved speaker slot) that a later
  diarization step can populate, keeping Track D scoped to the charter's wording —
  charter Track D + scaffold.

## Decisions deferred

- Per-tier latency bar (one < 2s gate for all targets vs separate iPhone/iPad
  bars) — trigger: HSM-3-05 measurement on both tiers — default: a single < 2s
  gate measured on the worst-case Tier-1 device, with the iPhone number recorded
  alongside.
- Whether to expose a larger Whisper variant on iPad when plugged in (mirroring
  the LLM "12B+ when plugged in" strategy) — trigger: HSM-3-01 model load — default:
  ship the charter's per-device defaults (Base/Small) only; no plugged-in upgrade
  in this phase.
- Chunk window size + overlap for realtime — trigger: HSM-3-02 latency tuning —
  default: pick the smallest window that holds < 2s, record the value, don't make
  it user-configurable in this phase.
