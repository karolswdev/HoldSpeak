# HoldSpeak Mobile Runtime — Roadmap

**Last updated:** 2026-06-18 (**Phase 3 — HSM-3-03/04 done** — the `WhisperLanguage`
registry generated at parity with desktop (100 codes, auto default) + the
transcription→`Segment` speaker-ready mapping; `swift test` 13/13. WhisperKit
dep/impl + latency Gate 3 are device-gated; the seam (model policy, config) is in.
Earlier: **Phase 2 started — HSM-2-02/03 done** — the audio
engine's testable core: `AudioChunk` + bounded `AudioAccumulator` and the
16 kHz-mono-PCM16 `WavWriter`, host-tested (`swift test` 8/8); the `AVAudioEngine`
capture service (HSM-2-01) is authored + iOS-type-checked, device-pending, and the
1-hour Gate 2 (HSM-2-04) is hardware-gated. Earlier: **Phase 1 CLOSED ✅ 4/4** —
Gate 1 proven (the shell
launched on the iPhone 17 Pro Max + iPad Pro M5 iOS-26.5 simulators, screenshots
committed) and CI is **green on a hosted run** (Actions 27801601150, pushed to
GitHub). The `apple/` package builds + `swift test` 5/5 + CI green. **Phase 2
(Audio Engine) is next.** Earlier: the real Swift codebase landed at
[`../../../apple/`](../../apple/README.md): a four-layer
SPM package (`Contracts`/`RuntimeCore`/`Providers`/`Hosts`, core layers UI-free)
whose `Contracts` `Codable` types round-trip the Phase-0 golden fixtures —
`swift test` 5/5 green on Swift 6.3, the same fixtures the Python validator
checks. Remaining in Phase 1: CI (HSM-1-03) + the on-device launch (HSM-1-04).
Earlier today: **Phase 0 CLOSED ✅ 5/5** — the contract layer ships:
the entity catalog, 9 JSON schemas, the serialization contract (10 locked rules),
two golden fixtures, and `validate.py` green across 10 checks; HSM-0-04 broadened
the fixtures (actuator proposal + balanced/architect intent windows + a round-trip
+ MIR-profile check) and HSM-0-05 closed the charter reconciliation (program risk
register seeded, `holdspeak` cross-link added). See
[`phase-0…/final-summary.md`](./phase-0-contracts-and-charter-lock/final-summary.md).
**Phase 1 (Mobile Foundation) is next.** Earlier: **owner confirmations locked** —
Quality Gates 3–7
confirmed as-reconstructed (CHARTER de-flagged) and instants standardized to
**UTC `Z`** (folded into the serialization contract + fixture + a green validator
UTC-Z check); HSM-0-05's owner-gated calls are done. Earlier today —
**Phase 0: HSM-0-01 + HSM-0-02 built** — the entity
catalog ([`contracts/ENTITY-CATALOG.md`](./contracts/ENTITY-CATALOG.md)) is
cross-checked against a live desktop serialization, and seven draft-2020-12 JSON
Schemas ([`contracts/schemas/`](./contracts/schemas/)) validate a real payload with
zero errors + reject a corrupted one ([`contracts/validate.py`](./contracts/validate.py)
green); and HSM-0-03 ([`contracts/SERIALIZATION-CONTRACT.md`](./contracts/SERIALIZATION-CONTRACT.md))
locks the ten cross-runtime rules + the package home. Three of five Phase-0 stories
built, awaiting commit; Phase 1 is unblocked. Next: HSM-0-04 (broaden fixtures).
Also today: the owner's **inference research brief** landed early and is captured
as canon ([`research/inference-on-apple.md`](./research/inference-on-apple.md)),
grounding Phase 5 (candidate set Core ML / llama.cpp+GGUF / MLC-LLM; Ollama/vLLM
are Mode-B/C companions; 4-bit PTQ default; charter model tiers confirmed).
Earlier today: **program scaffolded** — the Council Implementation
Charter (Rev 1.0) mapped onto a 12-phase roadmap (Phase 0 Contract Extraction →
Phase 11 Hardening), charter captured as [`CHARTER.md`](./CHARTER.md), every phase
folder carrying a `current-phase-status.md` + story stubs grounded in its track.)
**Current phase:** [phase-4-persistence](./phase-4-persistence/current-phase-status.md) (Phases 0 ✅, 1 ✅; 2 + 3 cores done, hardware/device-gated remainder)
**Status:** in-progress (Phases 0–1 closed; Phase 2 + 3 testable cores shipped; Phase 4 next).

## Vision

> The objective is not to build an "iPad version of HoldSpeak." The objective is
> to build the **first mobile runtime of the HoldSpeak ecosystem.**
> — [`CHARTER.md`](./CHARTER.md)

HoldSpeak already has local transcription, local intelligence, meeting
intelligence and aftercare, MIR (Meeting Intelligence Routing), action-lifecycle
management, dictation intelligence, a local-first architecture, and a provider
abstraction. The mobile effort does **not** re-invent any of that. It builds a
new **runtime host** that executes HoldSpeak workloads on Apple mobile hardware
(iPhone, iPad) while staying fully compatible with the existing desktop and
server runtimes through a set of shared, language-neutral contracts.

A user should be able to walk into a meeting, open HoldSpeak on an iPad or
iPhone, press Record, and leave with artifacts — action items, decisions, risks,
requirements, ADR candidates, follow-ups, a summary — generated fully on-device
(Mode A), against a homelab LLM (Mode B, recommended), or against any configured
endpoint (Mode C). The Propose → Review → Approve → Execute lifecycle is
preserved end to end; the mobile runtime never acts autonomously.

The architectural spine is the charter's four layers: **Contracts** (the
language-neutral schema, deliverable `holdspeak-contracts`), **Runtime Core**
(meeting engine, artifact generation, MIR, persistence, settings, sync — no UI),
**Providers** (`ITranscriber` / `ILLMProvider` / `IAudioCapture` / `IStorage` /
`ISyncProvider`), and **Platform Hosts** (desktop = existing HoldSpeak, mobile =
the new runtime). Business logic depends on none of SwiftUI, FastAPI, Python,
WebView, or UIKit.

## Source canon

- [`CHARTER.md`](./CHARTER.md) — the Council Implementation Charter (Rev 1.0),
  the authoritative spec for this program. Charter wins over any phase doc.
- [`research/inference-on-apple.md`](./research/inference-on-apple.md) — the
  owner's inference research brief (2026-06-18): the candidate runtimes, the
  device/quantization/memory budgeting, and the architecture mapping that ground
  Phase 5 (and inform Phases 3 and 11). Its performance numbers are planning
  estimates to be replaced by on-device measurement (HSM-5-01).
- `../holdspeak/README.md` and the existing `holdspeak` phase corpus — the
  shipped desktop/web product whose entities Phase 0 extracts into contracts.
- `/docs/internal/POSITIONING.md` — the positioning canon ("one copilot, two
  modes", developers, named honest comparisons). The mobile runtime is the same
  copilot on new hardware; its surfaces inherit the voice rules.
- `/docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md` (MIR-01) — the meeting-side
  routing the MIR port (Phase 7) must match.
- `/docs/ARCHITECTURE.md` — the shipped runtime data-flow map Phase 0 reads to
  build the entity catalog.

## Phase index

| Phase | Track | Goal (one line) | Status | Folder |
|---|---|---|---|---|
| 0 | A | Extract the desktop domain into language-neutral contracts (`holdspeak-contracts`) | **done (5/5)** | [phase-0](./phase-0-contracts-and-charter-lock/) |
| 1 | B | Mobile foundation: Xcode workspace, SPM layout, CI, launches on device | **done (4/4)** | [phase-1](./phase-1-mobile-foundation/) |
| 2 | C | Audio engine: AVAudioEngine streaming capture + WAV export, 1-hour stable | in-progress (2/4; rest hardware-gated) | [phase-2](./phase-2-audio-engine/) |
| 3 | D | Whisper runtime via WhisperKit, realtime latency < 2s | in-progress (2/5; lang+segment done, WhisperKit/latency device-gated) | [phase-3](./phase-3-whisper-runtime/) |
| 4 | E | SQLite persistence with full crash recovery | not-started | [phase-4](./phase-4-persistence/) |
| 5 | F | Local inference (4B/8B) — a 30-min meeting processed on-device | not-started | [phase-5](./phase-5-local-inference/) |
| 6 | G | Meeting intelligence: structured-JSON artifacts at desktop parity | not-started | [phase-6](./phase-6-meeting-intelligence/) |
| 7 | H | MIR port: 5 profiles measurably alter extraction | not-started | [phase-7](./phase-7-mir-port/) |
| 8 | I | iPad experience: PencilKit notebook + transcript linking + review | not-started | [phase-8](./phase-8-ipad-experience/) |
| 9 | J | iPhone experience: Quick Capture / Capture / Review Queue / Voice Notes | not-started | [phase-9](./phase-9-iphone-experience/) |
| 10 | K | Sync to desktop / homelab / Tailscale — cross-device continuity | not-started | [phase-10](./phase-10-sync/) |
| 11 | L | Hardening: the five stress scenarios, production readiness | not-started | [phase-11](./phase-11-hardening/) |

Phases are sequenced as the charter lists the tracks. The contract layer (Phase
0) and runtime-core seams gate everything above them; the two experience phases
(8, 9) and sync (10) can overlap once intelligence (6) is real. Re-sequencing is
the owner's call and is recorded in each phase's "Decisions made" section.

## Operating cadence

This roadmap inherits the repo's standing cadence (see
`../roadmap-builder.md` §7 and `../PMO-CONTRACT.md`). Every shipping commit:

- flips the story-file header status (`backlog → ready → in-progress → done`);
- updates the phase's `current-phase-status.md` story row + "Where we are";
- updates this README's "Last updated" line;
- writes `evidence-story-{n}.md` with real command/build output when a story
  ships (a green Xcode build log or `swift test` output is the evidence — a
  type-check or a compile is not validation of behavior);
- touches any canon doc the story names ([`CHARTER.md`](./CHARTER.md), this
  README's phase index).

One story = one PR. Evidence is required for every `done`. Each phase closes with
a `final-summary.md` once its charter gate is met or explicitly deferred.

**Prefix:** `HSM` (HoldSpeak Mobile). Story IDs are `HSM-{phase}-{seq}`
(`HSM-0-01`, `HSM-5-03`). IDs are stable forever and never reused.

**Relationship to the `holdspeak` roadmap.** This is a separate project folder
with its own phase lineage; it does not renumber or interrupt the desktop/web
roadmap (Phases 0–67 in `../holdspeak/`). Phase 0's contract-extraction work is
the one place the two touch — it reads the shipped Python/web entities to define
the shared schema.

## Glossary

- **Runtime host** — a platform-specific shell that executes HoldSpeak workloads
  (desktop = the existing Python/web app; mobile = the new Apple app). Hosts are
  Layer 4; they depend on the Runtime Core, never the reverse.
- **`holdspeak-contracts`** — the language-neutral schema package (Layer 1):
  `Meeting`, `Transcript`, `Speaker`, `Segment`, `ActionItem`, `Decision`,
  `Risk`, `Requirement`, `Artifact`, `IntelJob`. The interop spine.
- **MIR** — Meeting Intelligence Routing: the profile-driven extraction system
  (Balanced / Architect / Delivery / Product / Incident) ported in Phase 7.
- **Mode A / B / C** — Fully Local / Hybrid (recommended) / Endpoint. The three
  inference topologies (see [`CHARTER.md`](./CHARTER.md) §"Runtime modes").
- **Gate** — a charter pass criterion. Each phase's exit criteria include its
  track gate; the program-level Quality Gates are tracked in `CHARTER.md`.
