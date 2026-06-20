# HoldSpeak Runtime for Apple Platforms — Council Implementation Charter

**Revision:** 1.0 (+ **Amendment 1.1 — RATIFIED 2026-06-20**, the Companion
relationship (Tracks M–N) + the air-gapped elevation; see the amendment at the end
of this file. Rev 1.0 and Amendment 1.1 are co-canon.)
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

### Companion to the desktop coder *(headline objective — added by Amendment 1.1, 2026-06-20)*

Users should be able to point the phone or iPad at the same HoldSpeak server their
coding session runs against and have it act as a **first-class companion** to that
work: see and start meetings on the server, and — when the agent raises a question
— answer it with a **native voice note** that lands back in the coder session. This
companion role is **additive**: it never reduces the device, which remains a full
standalone runtime (Modes A/B/C). iPhone and iPad carry this at the same priority.

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

---

## Amendment 1.1 — The Companion Relationship (Tracks M–N) + the air-gapped elevation

**Status:** **RATIFIED co-canon (2026-06-20).** The owner answered the open
questions below and ratified this amendment; it now carries the same authority as
Rev 1.0. The phase docs' "flagged for an owner-blessed amendment" notes are
discharged and program risk **P10** (charter drift) is retired.
**Origin:** owner steer, 2026-06-20 (the `/remote-control` session). Captured into
the roadmap so it survives outside the conversation, per the charter's standing
practice.

### Why this amendment exists

Rev 1.0 chartered "the first mobile runtime" as a **standalone on-device** app and
never planned the iPad as a **first-class companion to the desktop coder**. The
owner named the gap directly and added two requirements:

1. **The companion relationship.** When the iPad is pointed at the same server a
   coding session runs against (tmux + hooks → server), it should be a first-class
   window into that runtime: list/start meetings, and — the payoff — when the agent
   raises a question, surface it on the iPad and answer it with a **native voice
   note** that lands back in the coder session.
2. **Not a dumb terminal; the air-gapped notetaker is paradigm.** The iPad must keep
   every on-device power. The fully-local, zero-connectivity meeting notetaker is
   "the paradigm" and must be **rich**, with the "magic pencil" **involved** in the
   intelligence, not a parallel scratchpad.

### What this amendment does NOT change (the reconciliations)

- **"Not an iPad version of HoldSpeak" still holds.** The mobile runtime remains a
  full, first-class runtime. The companion relationship is **additive** — the iPad
  *also* becomes a companion; it is never demoted to a remote.
- **The WebView principle (Architecture §Principle) is untouched.** The companion is
  **native over the desktop's existing HTTP API**, with the client logic behind a
  Runtime-Core provider seam. No WebView; business logic stays out of the views.
- **The Agentic-automation non-goal holds.** Answering the coder is
  **deliver-on-command** — the user always presses send; nothing is injected
  autonomously. Propose → Review → Approve → Execute is preserved end to end.
- **Runtime modes A/B/C are unchanged.** They describe the *inference* topology; the
  companion relationship is **orthogonal** to them (see below).

### What it adds

**A runtime-to-runtime relationship in the ecosystem.** The mobile runtime can act
as a first-class **companion** to a desktop/server runtime, in addition to standing
alone. Crucially, the companion relationship is **orthogonal to the inference
mode**: an iPad running **Mode A (fully local)** is simultaneously a valid
companion. The device is enriched in both directions and reduced in neither — the
"not a dumb terminal" / "stands its own ground" principle, made structural.

```
HoldSpeak Ecosystem (amended)
  Desktop Runtime ─────────────┐
    ├─ macOS                   │  companion relationship
    └─ Linux                   │  (native, over the desktop HTTP API;
  Mobile Runtime ◄─────────────┘   list/start meetings + answer the coder)
    ├─ iPhone        … also a standalone runtime (Modes A/B/C)
    └─ iPad          … also a standalone runtime (Modes A/B/C)
```

**A new Layer-3 provider.** Layer 3 (Providers) gains **`IDesktopClient`** — the
seam the companion drives the desktop HTTP API through (pairing/health, meetings
remote control, the remote-dictation inject). Business logic stays in the Runtime
Core; the host presents it.

**Device scope — iPhone and iPad at the same priority** *(owner, Q4)*. The
companion (Track M), answer-the-coder (Track N), and the rich air-gapped notetaker
all target **iPhone and iPad at parity** — answering a waiting coder from the phone
in your pocket is at least as valuable as from the iPad. The one hardware-bound
exception is the **Apple Pencil**: the PencilKit notebook + ink-into-intelligence
(HSM-8-02 / HSM-8-06) stay an iPad capability; iPhone reaches the same
meeting-intelligence outcomes through Track J's capture/voice paths without the
pencil.

### New development tracks

| Track | Phase | Title | Duration (est.) | Gate (pass criterion) |
|---|---|---|---|---|
| M | 12 | Companion Client | 2 weeks | First-class companion proven: point an iPhone/iPad at a real server, remote-control meetings (list / start / stop / live), and the on-device runtime still fully works — on real hardware |
| N | 13 | Answer the Coder | 2 weeks | Answer-the-coder end to end: an agent's question raised in a real coding session is surfaced on the device, answered by a native voice note, and lands back in that session — never autonomous — on real hardware |

**Track M — Companion Client (2 weeks).** Features: the `IDesktopClient` seam +
pairing, meetings remote control over the existing endpoints, a unified Signal shell
presenting both the on-device runtime and the server. iPhone + iPad at parity. Gate:
first-class companion proven on device, on-device runtime intact.

**Track N — Answer the Coder (2 weeks).** Features: the remote-dictation inject path
(one new desktop endpoint, `POST /api/dictation/remote`, through the rich dictation
pipeline), native voice-note capture, the AI PI companion board (surface the
agent's question + pick the target). iPhone + iPad at parity. Gate: answer-the-coder
end to end, deliver-on-command only.

### Sequencing *(owner delegated, Q1 — call made 2026-06-20)*

Tracks M–N run **before** Hardening. Hardening (Track L / Phase 11) is re-sequenced
to be the program's **final** phase, after Phases 12–13 (Sync / Phase 10 also lands
before it). Rationale: you harden the complete product, not a subset — adding the
headline companion surface *after* hardening would ship it unhardened. **Gate 7
(Production Readiness) is extended** to cover companion failure scenarios (server
unreachable mid-answer, token expiry, stale companion state, airplane-mode
transitions) alongside the original five.

### Track I sharpened (the air-gapped elevation)

Track I (iPad Experience) keeps its "meeting notebook workflow complete" gate and is
**sharpened** by the owner's paradigm steer (no new track):

- The fully-local, **air-gapped** notetaker (Mode A, zero connectivity) must be a
  rich, first-class experience, not a degraded fallback (HSM-8-05).
- The **magic pencil is involved in the intelligence**: on-device handwriting
  recognition, promote a note/marked-moment to a contract artifact
  (propose-and-confirm), marked moments weight MIR extraction (HSM-8-06).

### New / amended Quality Gates

In execution order, three new capability gates precede Hardening; **Gate 7
(Production Readiness) remains the program's final gate** and now also hardens the
companion paths.

- **Gate 8 — Air-gapped Notetaker (Track I).** On a real iPad with the radios off
  (and iPhone at parity, per the same-priority steer), the fully-local Mode-A
  notetaker runs the whole workflow **and is rich in functionality** — not a
  degraded fallback. *Owner (Q3): "we're gonna have to gate it on an actual iPad …
  needs to be rich in functionality for us to even make anything out of it."*
- **Gate 9 — Companion (Track M).** An iPhone/iPad is a first-class companion to a
  real desktop, with its on-device runtime provably intact ("not a dumb terminal").
- **Gate 10 — Answer the Coder (Track N).** An agent's question is answered by a
  native voice note from the device and received back in the coder session, never
  autonomously.

### Owner decisions (resolved 2026-06-20)

| # | Question | Decision |
|---|---|---|
| Q1 | Sequencing vs Hardening | **Owner delegated → call made:** M–N run **before** Hardening; Hardening is the final phase; **Gate 7 extended** to cover companion failure scenarios. |
| Q2 | Charter identity wording | Keep the Executive Summary's "not an iPad version" **verbatim**, **and promote** "first-class companion to the desktop coder" to a **headline objective in the Vision** (added above). |
| Q3 | Air-gapped gate status | **Its own gate (Gate 8)** — proven on a real iPad (iPhone at parity), and the gate **requires rich functionality**, not just an offline run. |
| Q4 | iPhone scope | **iPhone at the same priority as iPad** for the companion, answer-the-coder, and the air-gapped notetaker. The Apple-Pencil notebook stays an iPad capability (hardware). |
| Q5 | Cross-roadmap desktop dependency | **Authorized** to add `POST /api/dictation/remote` to the desktop `holdspeak` roadmap; default mechanism = route through the existing dictation runtime so the **AI PI delivery path + the rich pipeline** both apply. |
