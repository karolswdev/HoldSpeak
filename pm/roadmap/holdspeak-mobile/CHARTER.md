# HoldSpeak Runtime for Apple Platforms — Council Implementation Charter

**Revision:** 1.0
**Status:** source canon for the `holdspeak-mobile` roadmap. If a phase or story
disagrees with this charter, the charter wins (record the disagreement in the
story's "Notes / open questions").
**Captured:** 2026-06-18, transcribed verbatim from the owner's charter into the
roadmap so it survives outside the conversation.

> **Transmission note.** The charter as delivered was truncated mid-"Quality
> Gates" at Gate 3. Gates 1 and 2 are transcribed verbatim below; Gates 3–7 were
> reconstructed from the per-track gates (each track states its own pass
> criterion) and **confirmed as-reconstructed by the owner on 2026-06-18** — the
> reconstruction below IS the official gate list. See
> `phase-0-contracts-and-charter-lock/` (HSM-0-05).

---

## Executive summary

The objective is not to build an "iPad version of HoldSpeak."

The objective is to build the **first mobile runtime of the HoldSpeak
ecosystem**.

HoldSpeak already possesses:

- Local transcription
- Local intelligence
- Meeting intelligence
- Meeting aftercare
- MIR (Meeting Intelligence Routing)
- Action lifecycle management
- Dictation intelligence
- Local-first architecture
- Provider abstraction

The mobile effort therefore focuses on creating a **new runtime host** capable
of executing HoldSpeak workloads on Apple mobile hardware while remaining fully
compatible with existing HoldSpeak desktop and server runtimes.

The resulting ecosystem becomes:

```
HoldSpeak Ecosystem
  Desktop Runtime
    ├─ macOS
    └─ Linux
  Mobile Runtime
    ├─ iPhone
    └─ iPad
  Inference Providers
    ├─ Local Mobile
    ├─ Local Desktop
    ├─ Homelab
    └─ Cloud Compatible
  Shared Contracts
    ├─ Meetings
    ├─ Transcripts
    ├─ Artifacts
    ├─ Actions
    ├─ MIR
    └─ Intelligence Jobs
```

---

## Vision

HoldSpeak Mobile Runtime must enable:

### Meeting capture

Users can record meetings, interviews, architecture reviews, requirements
sessions, and design workshops, while remaining fully local.

### Intelligence

Users receive Action Items, Decisions, Risks, Requirements, ADR Candidates,
Follow-ups, and Meeting Summaries, generated entirely on-device or through a
configured endpoint.

### Dictation

Users can capture ideas, create notes, record architecture thoughts, capture
code explanations, and create tasks, using voice.

### Mobility

Users should be able to walk into a meeting, open HoldSpeak, press Record, and
leave with artifacts, without needing a laptop.

---

## Non-goals (explicitly out of scope for Version 1)

- **Windows** — no Windows runtime.
- **Android** — no Android runtime.
- **Full desktop replacement** — mobile complements desktop. Desktop remains
  better for coding, long-form review, and administrative workflows.
- **Agentic automation** — no autonomous actions. The Propose → Review →
  Approve → Execute lifecycle is maintained throughout.

---

## Product targets

| Tier | Device | Status |
|---|---|---|
| 1 | iPad Air M4 | Primary target |
| 1 | iPad Pro M4 | Primary target |
| 2 | iPhone 17 Pro Max | Primary target |
| 2 | Future flagship iPhones | Must remain compatible |

---

## Architecture

### Principle

Business logic must not depend on SwiftUI, FastAPI, Python, WebView, or UIKit.
The domain model is independent.

### Layers

**Layer 1 — Contracts.** Canonical schema definitions: `Meeting`, `Transcript`,
`Speaker`, `Segment`, `ActionItem`, `Decision`, `Risk`, `Requirement`,
`Artifact`, `IntelJob`. Deliverable: `holdspeak-contracts`.

**Layer 2 — Runtime Core.** Meeting engine, artifact generation, MIR engine,
persistence, settings, sync. No UI.

**Layer 3 — Providers.** Abstractions: `ITranscriber`, `ILLMProvider`,
`IAudioCapture`, `IStorage`, `ISyncProvider`.

**Layer 4 — Platform Hosts.** Desktop = existing HoldSpeak. Mobile = the new
HoldSpeak Runtime.

---

## Development tracks

Each track maps to one roadmap phase. Durations are the charter's estimates.

| Track | Phase | Title | Duration | Gate (pass criterion) |
|---|---|---|---|---|
| A | 0 | Contract Extraction | 1 week | All desktop entities mapped |
| B | 1 | Mobile Foundation | 1 week | App launches on iPhone + iPad |
| C | 2 | Audio Engine | 2 weeks | 1-hour continuous recording |
| D | 3 | Whisper Runtime | 2 weeks | Realtime latency below 2 seconds |
| E | 4 | Persistence | 1 week | Full recovery after crash |
| F | 5 | Local Inference | 3 weeks | 30-minute meeting processed locally |
| G | 6 | Meeting Intelligence | 3 weeks | Parity with desktop quality baseline |
| H | 7 | MIR Port | 2 weeks | Profile changes measurably alter extraction |
| I | 8 | iPad Experience | 2 weeks | Meeting notebook workflow complete |
| J | 9 | iPhone Experience | 2 weeks | Pocket workflow complete |
| K | 10 | Sync | 2 weeks | Cross-device continuity |
| L | 11 | Hardening | 3 weeks | Production readiness |

### Track A — Contract Extraction (1 week)

Goal: extract all domain entities from the existing HoldSpeak implementation.
Deliverables: Entity Catalog, JSON Schemas, Serialization Contracts. Gate: all
desktop entities mapped.

### Track B — Mobile Foundation (1 week)

Deliverables: Xcode Workspace, Swift Package Layout, CI Pipeline, Test Harness.
Gate: application launches on iPhone and iPad.

### Track C — Audio Engine (2 weeks)

Features: AVAudioEngine, streaming capture, recording, WAV export.
Deliverables: `AudioCaptureService`, `AudioSession`, `AudioChunk`. Gate: 1-hour
continuous recording.

### Track D — Whisper Runtime (2 weeks)

Technology: WhisperKit. Responsibilities: real-time transcription, chunk
transcription, language selection, speaker-ready segmentation. Gate: realtime
latency below 2 seconds.

### Track E — Persistence (1 week)

Technology: SQLite. Stores: Meetings, Segments, Artifacts, Actions. Gate: full
recovery after crash.

### Track F — Local Inference (3 weeks)

Technology evaluation: MLC-LLM, llama.cpp, CoreML-native candidates. Target
models: Tier 1 = 4B models, Tier 2 = 8B models, Experimental = 12B+. Gate:
30-minute meeting processed locally.

> **Grounded 2026-06-18** by [`research/inference-on-apple.md`](./research/inference-on-apple.md)
> (owner's brief): the in-app candidate set is **Core ML / llama.cpp+GGUF /
> MLC-LLM** (Ollama and vLLM are Mode-B/C server companions, NOT in-app
> runtimes); 4-bit PTQ is the shipping default; the charter's per-device model
> strategy (4B iPhone / 8B iPad / 12B-experimental-plugged-in) is confirmed
> consistent, with 7B as the practical phone upper bound and 12B an
> iPad-16GB/hybrid target. The final engine pick stays a Phase-5 measured
> decision (HSM-5-01).

### Track G — Meeting Intelligence (3 weeks)

Artifacts: Action Items, Decisions, Risks, Requirements, Summaries. Output:
structured JSON. Gate: parity with desktop quality baseline.

### Track H — MIR Port (2 weeks)

Profiles: Balanced, Architect, Delivery, Product, Incident. Gate: profile
changes measurably alter extraction.

### Track I — iPad Experience (2 weeks)

Technology: PencilKit. Features: handwritten notes, notebook mode, transcript
linking, artifact review. Gate: meeting notebook workflow complete.

### Track J — iPhone Experience (2 weeks)

Features: Quick Capture, Meeting Capture, Review Queue, Voice Notes. Gate:
pocket workflow complete.

### Track K — Sync (2 weeks)

Targets: HoldSpeak Desktop, Homelab, Tailscale networks. Objects: Meetings,
Actions, Artifacts. Gate: cross-device continuity.

### Track L — Hardening (3 weeks)

Scenarios: 4-hour meeting, airplane mode, low battery, thermal stress, app
suspend/resume. Gate: production readiness.

---

## Runtime modes

**Mode A — Fully Local.** Audio → Whisper → LLM → Artifacts. No network.

**Mode B — Hybrid (recommended).** Audio → Local Whisper → Homelab LLM →
Artifacts.

**Mode C — Endpoint (compatibility mode).** Audio → Endpoint → Artifacts.

---

## Local model strategy

| Device | Default Whisper | Default LLM | Experimental |
|---|---|---|---|
| iPhone | Whisper Base | 4B LLM | — |
| iPad | Whisper Small | 8B LLM | 12B+ post-meeting processing, only when plugged in |

---

## Quality gates

**Gate 1 — Runtime Launch.** Pass criteria: application launches on all targets.

**Gate 2 — Audio Stability.** Pass criteria: 1 hour continuous recording.

**Gate 3+ — (owner-confirmed 2026-06-18).** The original transmission was
truncated at Gate 3; the owner confirmed the reconstruction below as the official
gate list. From the per-track gates, the remaining program-level gates are:

- **Gate 3 — Transcription Latency.** Realtime latency below 2 seconds (Track D).
- **Gate 4 — Local Inference.** A 30-minute meeting processed locally (Track F).
- **Gate 5 — Intelligence Parity.** Artifact quality at parity with the desktop
  baseline (Track G).
- **Gate 6 — Cross-device Continuity.** Sync round-trips meetings/actions/
  artifacts across devices (Track K).
- **Gate 7 — Production Readiness.** Survives the five hardening scenarios
  (Track L).

Confirmed by the owner on 2026-06-18 (HSM-0-05); this is the program's Quality
Gate list of record.
