# HoldSpeak Mobile Runtime — Roadmap

**Last updated:** 2026-06-20 (**Charter Amendment 1.1 RATIFIED** — the Companion
relationship is now co-canon with Rev 1.0: Tracks M–N, "companion to the desktop
coder" promoted to a headline Vision objective, **iPhone + iPad at parity**, the
**air-gapped notetaker made its own program gate (Gate 8)** + Gates 9/10, and
**Hardening re-sequenced last** with Gate 7 extended to the companion failure
scenarios. Program risk P10 retired. Earlier the same day: **Companion track
scaffolded — Phases 12–13 (Tracks M–N), by owner steer.** The program was chartered as a standalone on-device runtime
and never planned the iPad as a **first-class companion to the desktop coder** — the
one iPad-UI phase (8) is a PencilKit notebook, and the iPad app today is a Gate-1
launch stub plus a demo harness. Two new phases close that gap without neutering the
device: **Phase 12 — The Companion Client** (point the iPad at the same server you
code against; a unified shell presenting both its own on-device runtime *and* the
server; meetings remote control — list / start / stop / live state over the existing
HTTP API), and **Phase 13 — Answer the Coder** (the AI PI payoff: the agent's
question surfaces on the iPad, you answer with a native voice note through the rich
dictation pipeline, it lands back in the coder session — never autonomous). Built
native over the desktop's existing API (owner call); the desktop already serves what
the client consumes (`/api/meetings`, `/api/meeting/start|stop`, `/api/dictation/*`,
`/api/companion/*`), the one new desktop surface being the remote-dictation inject
endpoint (HSM-13-01). Phase 8 + the on-device runtime stand untouched. Ten new story
files scaffolded; no implementation started. **Also: Phase 8 (the on-device iPad
experience) elevated to the owner's richness bar** — the **air-gapped fully-local
notetaker** (iPad at a meeting, zero connectivity, Mode A on-device) is now a
first-class scenario with its own gate (HSM-8-05), and the **magic pencil is
genuinely involved** (HSM-8-06: on-device handwriting recognition, notes/marks
promoted to artifacts, marked moments weighting MIR) rather than a parallel
scratchpad; the notebook/linking stories raised to match. The standalone on-device
paradigm and the companion track are now both first-class, in both directions.
Earlier: **Sync "do it now" orchestration — `SyncCoordinator`, host-proven.** The one-call sync the host UI drives: `syncNow()` snapshots the store →
durably queues the outbound change-set → flushes to the peer → pulls + applies
(conflict-resolved), **offline-safe by construction** (never throws on an unreachable
peer; the snapshot is queued for the next pass). `SyncQueue.enqueueNext` (clock-free)
backs the durable-first record. `swift test` **84/84** incl. `SyncCoordinatorTests`
(reachable / offline / resume). This is the mobile side of the continuity gate
(HSM-10-04 → in-progress); only the live on-device walkthrough remains. Earlier:
**HSM-10-03 (sync conflict + round-trip) DONE.**
`SyncEngine.apply` is now conflict-aware: LWW by `last_modified`, **same-time
divergence surfaced non-destructively** (kept local + reported, never silently
dropped), tombstone no-resurrect, and **idempotent** (sync twice → no change) — all
over the Phase-0 fixture; plus desktop-end push validation (malformed record → 422).
Both ends validate against the contract. `swift test` 81/81; `uv run pytest
tests/unit/test_web_routes_sync.py` 4 passed. Phase 10 now 3/4 — only the live
cross-device gate (HSM-10-04, needs the iPad) remains. Earlier: **HSM-10-02 (sync
transport) DONE — both sides of the
wire.** The desktop **Python sync receiver** landed (PR-B): `holdspeak/web/routes/sync.py`
serves the desktop's meetings/artifacts as a contract change-set on
`GET /api/sync/pull` and receives a pushed change-set into a durable inbox on
`POST /api/sync/push` (additive — no DB schema change), mounted in `web_server.py`.
Paired with the Swift `HTTPSyncProvider` + `SyncQueue` (PR-A, #75), the phone can now
push/pull change-sets to a desktop/homelab peer, offline-tolerant. `uv run pytest
tests/unit/test_web_routes_sync.py` 3 passed (+ route preflight green); `swift test`
77/77. Conflict/merge into the live store is HSM-10-03; the live cross-device run is
HSM-10-04. Earlier: **HSM-10-02 (sync transport) — the Swift HTTP transport
+ offline queue, host-proven (PR-A).** `HTTPSyncProvider` (`ISyncProvider` over
`POST /api/sync/push` + `GET /api/sync/pull`, direct to the peer, honest egress
label) + `SyncQueue` (disk FIFO; `flush` keeps the queue + never throws when the peer
is down — offline tolerated, sync off the capture path). `swift test` **77/77**
(6 opt-in skips) incl. 8 transport tests. Next (PR-B): the desktop **Python sync
receiver** (`holdspeak/web/routes/sync.py`). Earlier: **Phase 7 CLOSED ✅ — the MIR
port, host-proven.** The
profile-driven routing decision lives in RuntimeCore: `IntentScorer` (deterministic
lexical scoring of MIR-01's five intents) → `MIRRouter` (per-profile emphasis +
score-driven additions → ordered `ArtifactType` chain) → `RoutedArtifactGenerator`
driving the Phase-6 engine. Five distinct profiles; profile rides on
`Meeting.mirProfile` (Phase-0 contract). **Track-H gate PASSED**: same transcript,
balanced vs architect → artifact-type delta `{action_items, dependency_map,
risk_register}`. `swift test` **69/6-skip/0-fail**; model-free + deterministic.
See [`phase-7…/final-summary.md`](./phase-7-mir-port/final-summary.md). Earlier:
**HSM-5-03 — model packaging: both delivery paths
host-proven (Files sideload + Hugging Face download).** A `ModelCatalog` pins the
per-tier GGUFs (4B Llama-3.2-3B / 8B Llama-3.1-8B / 12B+ Mistral-Nemo, Q4_K_M; HF
URLs verified live), a Foundation `ModelStore` is the model manager (list /
sideload-import / delete / per-device `resolveActive`), and a Foundation
`ModelDownloader` does the HF download by canonical resolve-URL with real progress
(LLM.swift's built-in HF scraper is broken against current HF — we download by
pinned URL instead). `swift test` **62/62** (6 opt-in skips); the real download is
proven by an opt-in test (TinyLlama 0→100% → load → complete); `push-model-device.sh`
adds the `devicectl` dev path. Remaining: the iPad clean-install first-run (unlock).
Earlier: **HSM-5-02 — the on-device (Mode A) engine, host-proven
on Metal.** `LlamaProvider` (an `ILLMProvider` backed by **llama.cpp via LLM.swift**,
the HSM-5-01 pick) loads a GGUF and completes with no network — proven on this Mac's
Metal against Qwen2.5-7B Q4_K_M (`PONG` ~8.5s incl. cold load; a full fully-local run
transcript → engine → real decisions + action_items ~13.4s). The native engine lives
in a separate `InferenceLlama` product so the domain never links it (the Phase-6
"ProviderInterfaces" concern, resolved). `swift test` **57/57** (5 opt-in skips),
layer guard green. Remaining: the iPad airplane-mode run (gated on the device unlock)
+ model packaging (HSM-5-03). With HSM-5-06 (endpoint, Modes B/C) already shipped, the
iPad now has **both** an on-device engine and an endpoint path behind one seam.
Earlier: **Phase 10 (Sync) opened — HSM-10-01 done: the sync
object model + engine.** Following the owner's program steer (sync is next after
Phase 6), and fully host-testable (no device). Cross-device sync moves the **Phase-0
entities themselves** in a contract-layer envelope (`ChangeSet` of `Synced<T>`;
payload = the unmodified entity, `nil` ⇔ tombstone) — no parallel schema, no drift
(SERIALIZATION-CONTRACT §11). `ISyncProvider` is now a `push`/`pull` seam;
`ISyncStore` adds modified-time + soft-delete tombstones to the Phase-4 store
(SQLite schema v2, guarded migration); the RuntimeCore `SyncEngine` does
`snapshot`/`apply` (schema-validated) / `sync(local:via:)`. `swift test` **55/55**
incl. 6 sync tests (round-trip, JSON-wire round-trip, tombstone propagation,
idempotent apply, malformed-wire rejection), Phase-4 storage intact through the
migration. Next: HSM-10-02 (transport + the Python-side sync API + the envelope's
JSON Schema). Earlier: **Phase 6 CLOSED ✅ — Gate 5 (desktop-parity) PASSED.**
HSM-6-05: the parity harness over a fixed baseline meeting, with real mobile
generation through the Mode-B/C endpoint provider, scores **mean coverage 0.92 over
3 runs vs the pre-fixed 0.8 threshold (3/3 pass)** — mobile meeting intelligence is
at parity with the desktop quality baseline. Threshold fixed before the run; gaps
filed honestly; bar not moved (the owner delegated the rubric + verdict). On-device
execution is carried by HSM-5-06 (built/installed on the iPad; launch pending unlock)
+ HSM-5-02 (fully-local). HSM-6-06 (Follow-ups) stays deferred on a cross-runtime
contract decision. See [`phase-6…/final-summary.md`](./phase-6-meeting-intelligence/final-summary.md).
Earlier: **Phase 5 — HSM-5-06: the iPad runs real meeting
intelligence today via an OpenAI-compatible endpoint (charter Modes B/C).** On the
owner's steer — inference mode is a user setting (local default) and the runtime
must point at any OpenAI-compatible endpoint so the iPad need not load a resident
model — the endpoint provider ships ahead of the on-device GGUF. `OpenAIEndpointProvider`
(URLSession, Foundation only) + `RuntimeMode`/`EndpointConfig`/`InferenceProviderFactory`;
`swift test` **46/46** (+8); a live run emits real contract-shaped artifacts from a
transcript against a clean LAN `llama-server` (Qwen2.5-7B), and the **HSM-6-05 parity
mechanism scores that real output 1.00 PASS**. The Mode-C harness is **built + signed
+ installed on the physical iPad Air M4**; the on-device launch is blocked only by
the device lock screen (one command finishes it). This gives **HSM-6-05 a real
on-device `ILLMProvider`, so the parity verdict is no longer engine-blocked**
(it now awaits the owner-signed baseline + rubric). Finding: the `.43` homelab box
forces a `{"line": …}` grammar, so the proof used a clean dev-Mac endpoint over the
LAN. HSM-5-02 (on-device GGUF, Mode A, true airplane-mode local) reuses this same
seam + harness and stays the follow-on push. Earlier: **Phase 5 — HSM-5-01 done: the
inference engine is `llama.cpp` + GGUF** — a banked decision from the owner's research
canon (not a
bake-off, per the no-spikes directive); resolves the Phase-0 Track-F deferral.
Decisive axis: off-the-shelf 4B/8B GGUF availability (no Core ML conversion / MLC
compile); mature Metal; a C API behind the existing `ILLMProvider` port →
reversible (MLX is the fallback). Named models `Llama-3.2-3B`/`Llama-3.1-8B` Q4_K_M
GGUF. **HSM-5-02 is the active thrust** — wire llama.cpp + run a GGUF completion on
the connected iPad Air M4 (the device's first real on-device inference; unblocks
the Phase-6 parity verdict HSM-6-05). Earlier: **Phase 6 — HSM-6-04 done (parity
harness)** — a
deterministic, phrasing-tolerant substance-coverage scorer (`ParityRubric` /
`ParityScorer` / `ParityReport`) that operationally defines the Track-G parity
gate (per-type `mustCover` facts, fact-weighted coverage vs an owner-agreed 0.8
threshold, stable across reruns). `swift test` 38/38. The intelligence layer
(6-01/02/03) + harness are host-proven; **HSM-6-05 (the Gate-5 verdict) is blocked**
on the device/dep-gated mobile inference engine (Phase 5 — no on-device model yet,
so a real mobile-vs-desktop comparison can't run). Earlier: **HSM-6-03 done (ADR
Candidates)** — an
open-blob `Artifact(.adr)` on the seam: ties to an architectural-weight decision,
carries a `source_timestamp` + transcript source, never fabricated. `swift test`
35/35. **Follow-ups split to HSM-6-06 (blocked)** — `artifact_type` is a closed
cross-runtime enum with no follow-up type (needs a desktop+schema+fixtures contract
decision). **Program steer (owner): the iPad syncs to the server by default**
(local-first, off-LAN → queue → reconcile later); after Phase 6 closes, the sync
thrust (incl. a new Python-side sync API) is next. Earlier: **HSM-6-02 done** — the
five core artifact types (Action Items typed to `[ActionItem]`; Decisions/Risks/
Requirements open-blob; Summary → `IntelSnapshot`); fixed a Phase-5 `extractJSON`
array bug. Earlier: **HSM-6-01 done** — the
artifact-generation engine seam (`ArtifactGenerationEngine`: Phase-0 `Transcript`
+ injected `ILLMProvider` → schema-valid `Artifact` via the Phase-5
`StructuredOutput` bridge; propose-only, robust to prose). Earlier: **Gate 1
proven on real metal** — the Phase-1
runtime shell launched on a **physical iPad Air 11" (M4), iPadOS 26.5** (owner-confirmed
"contracts v0.1.0" on-device), discharging the HSM-1-04 physical-device follow-up
via new headless on-device deploy tooling (`apple/scripts/gen-device-project.rb` +
`gate1-device.sh`: build → sign → install → launch over `devicectl`). One-time
enrollment (account sign-in, Apple Developer PLA, Developer Mode, device
registration) is done and persists, so the on-device path is now repeatable for
the heavier device-gated gates (capture/Whisper/inference). Phase 1 stays CLOSED.
See [`phase-1…/gate1-ipadair-m4-realmetal.log`](./phase-1-mobile-foundation/gate1-ipadair-m4-realmetal.log).
Earlier: **Phase 5 — HSM-5-04 done + host slice** — the
structured-output bridge (`StructuredOutput`: extract JSON from messy model text →
decode through the contract → bounded repair-retry) + the per-device LLM model
policy (4B iPhone / 8B iPad / 12B+ plugged-in); `swift test` 24/24. Engine pick +
`ILLMProvider` impl + 30-min gate are device/dep. Earlier: **Phase 4 CLOSED ✅ 3/3** — `SQLiteStorage` (built-in
`SQLite3`, no dep) backs `IStorage`: contract-JSON `meetings`/`artifacts` tables,
WAL, `SCHEMA_VERSION=1`; `swift test` 18/18 incl. round-trip + crash-recovery
durability/atomicity/integrity. Fully host-verified (on-device SIGKILL noted as
the one stronger proof). Phase 5 next. Earlier: **Phase 3 — HSM-3-03/04 done** — the `WhisperLanguage`
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
**Current phase:** [phase-7-mir-port](./phase-7-mir-port/current-phase-status.md) closed; Phases 0 ✅, 1 ✅, 4 ✅, **6 ✅ Gate 5**, **7 ✅ Gate H**; Phase 5 host-complete (engine pick + structured output + endpoint Modes B/C + on-device Mode A + model packaging — all host-proven; device runs pending the iPad unlock); Phase 10 in-progress (HSM-10-01 done); 2 + 3 testable cores done, device-gated remainder; 6-06 Follow-ups deferred. **Phases 12–13 (Tracks M–N — the Companion Client + Answer the Coder) scaffolded 2026-06-20 by owner steer; no work started.**

**Highest-value direction (owner steer, 2026-06-20; ratified in charter Amendment
1.1).** The program's value now concentrates on the **two device faces, both
first-class, on iPhone + iPad at parity**: (1) the **Companion track**
— point the iPad at the server you code against and **answer the coder by voice**
(Phase 12 → 13, the Answer-the-Coder payoff), and (2) the **air-gapped fully-local
notetaker** with a magic pencil that feeds the output (Phase 8, elevated: HSM-8-05 +
HSM-8-06). **Start here →** [HSM-12-01](./phase-12-companion-client/story-01-desktop-client-seam.md)
(the desktop client seam) — the highest-value **device-free** story, fully
host-testable against a fake desktop, and the spine the whole Companion track hangs
off. The on-device richness (HSM-8-05/06) sequences behind Phase 6 + HSM-5-02 (Mode
A) and the iPad unlock; build its host-testable seams first, then gate on device.
Sync (Phase 10) continues in parallel but is plumbing, not the headline value.
**Status:** in-progress (Phases 0–1–4 closed, **Phase 6 closed (Gate 5 desktop-parity PASSED 0.92)**, **Phase 7 closed (MIR port — profile measurably changes extraction)**; Phase 5 host-complete — on-device Mode A + endpoint Modes B/C + sideload/HF packaging, device runs await the iPad unlock; Phase 10 opened (sync object model + engine). Next device-free: HSM-10-02 sync transport + Python sync API, or Phases 8/9 experience, or **Phase 12 — The Companion Client (HSM-12-01, the desktop client seam, fully host-testable against a fake desktop)**. iPad on-device batch (HSM-5-02/03/06 + Gate-4) when the device is unlocked; the companion gates (HSM-12-04 / HSM-13-04) join that device batch).

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

- [`CHARTER.md`](./CHARTER.md) — the Council Implementation Charter (Rev 1.0 +
  **Amendment 1.1**, the Companion relationship — co-canon), the authoritative spec
  for this program. Charter wins over any phase doc.
- [`research/inference-on-apple.md`](./research/inference-on-apple.md) — the
  owner's inference research brief (2026-06-18): the candidate runtimes, the
  device/quantization/memory budgeting, and the architecture mapping that ground
  Phase 5 (and inform Phases 3 and 11). Its performance numbers are planning
  estimates to be replaced by on-device measurement (HSM-5-01).
- [`../../apple/ARCHITECTURE.md`](../../apple/ARCHITECTURE.md) — the code map of the
  shipped mobile runtime (four layers, provider seams, the two inference modes, the
  meeting-intelligence + MIR path, sync). Read it to see how the roadmap's phases
  fit together in the `apple/` package.
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
| 4 | E | SQLite persistence with full crash recovery | **done (3/3)** | [phase-4](./phase-4-persistence/) |
| 5 | F | Local inference (4B/8B) — a 30-min meeting processed on-device | in-progress (engine pick + structured-output + model policy done; HSM-5-06 endpoint Modes B/C; **HSM-5-02 LlamaProvider/Mode A host-proven on Metal**; **HSM-5-03 packaging — sideload + HF download host-proven**; iPad runs + HSM-5-05 gate device) | [phase-5](./phase-5-local-inference/) |
| 6 | G | Meeting intelligence: structured-JSON artifacts at desktop parity | **Gate 5 PASSED ✅ (5/6; 6-06 deferred)** | [phase-6](./phase-6-meeting-intelligence/) |
| 7 | H | MIR port: 5 profiles measurably alter extraction | **done (4/4) ✅** | [phase-7](./phase-7-mir-port/) |
| 8 | I | iPad experience: the **air-gapped fully-local notetaker** (rich, zero-connectivity, Mode A — **Gate 8**, real-iPad-proven) + a **magic pencil that feeds the output** (PencilKit notebook, marked moments, ink → artifacts) + review | not-started (elevated 2026-06-20: +HSM-8-05 air-gapped gate, +HSM-8-06 ink-into-intelligence) | [phase-8](./phase-8-ipad-experience/) |
| 9 | J | iPhone experience: Quick Capture / Capture / Review Queue / Voice Notes — **+ companion + answer-the-coder + air-gapped notetaker at iPad parity** (Amendment 1.1) | not-started | [phase-9](./phase-9-iphone-experience/) |
| 10 | K | Sync to desktop / homelab / Tailscale — cross-device continuity | in-progress (object model + transport + conflict + `SyncCoordinator` orchestration host-proven; only the live cross-device walkthrough (device) remains) | [phase-10](./phase-10-sync/) |
| 11 | L | Hardening: the five stress scenarios **+ companion failure scenarios** (Gate 7 extended), production readiness — **runs last** (after 12–13, per Amendment 1.1) | not-started | [phase-11](./phase-11-hardening/) |
| 12 | M | **The Companion Client:** point the iPhone/iPad at the same server you code against — a unified shell (on-device runtime + server, never a dumb terminal) + meetings remote control | not-started (scaffolded 2026-06-20) | [phase-12](./phase-12-companion-client/) |
| 13 | N | **Answer the Coder:** the AI PI payoff — the agent's question surfaces on the device, you answer by native voice note, it lands back in the coder session | not-started (scaffolded 2026-06-20) | [phase-13](./phase-13-answer-the-coder/) |

**Tracks M–N (Phases 12–13)** were added by owner steer (2026-06-20) and **ratified
into the charter as Amendment 1.1 (co-canon with Rev 1.0)**. They close a gap the
owner named directly: there was no phase for the device as a **first-class companion
to the desktop coder**. The device keeps every on-device power (Phases 0–7 stand —
"not a dumb terminal"); the companion track *adds* a server-aware face, built native
over the desktop's existing HTTP API. Phase 8 (the PencilKit notebook) stays the
on-device flagship, untouched. Amendment 1.1 also: promotes "companion to the
desktop coder" to a headline Vision objective, puts **iPhone + iPad at parity** for
the companion / answer-the-coder / air-gapped notetaker (the Apple-Pencil notebook
stays iPad hardware), makes the **air-gapped notetaker its own program gate (Gate
8)**, and adds Gates 9 (Companion) / 10 (Answer the Coder).

**Sequencing (Amendment 1.1).** Hardening (Phase 11) is re-sequenced to run **last**
— after Phases 12–13 — so the complete product (companion paths included) is what
gets hardened; **Gate 7 (Production Readiness) extends** to the companion failure
scenarios. Otherwise phases follow the charter's track order; re-sequencing is the
owner's call and is recorded in each phase's "Decisions made" section. The contract
layer (Phase 0) and runtime-core seams gate everything above them; the two
experience phases (8, 9) and sync (10) can overlap once intelligence (6) is real.

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
