# HoldSpeak Mobile Runtime — Roadmap

**Last updated:** 2026-06-21 (**HSM-8-04 DONE — artifact review + the TRACK I GATE ACHIEVED
(Phase 8 now 4/6).** `ReviewModel` (RuntimeCore) groups a meeting's artifacts by type in
the MIR profile's emphasis + approve/reject (never executes). The meeting app generates
Phase-6 artifacts **on-device** (the `ArtifactGenerationEngine` over the on-device
`LlamaProvider`/GGUF) and reviews them with Approve/Dismiss + an on-device egress badge.
The full **record → transcript → notebook → linked moments → on-device review** workflow
ran end to end on a physical iPad (owner-witnessed, no network). A real-metal `[BLANK_AUDIO]`
bug was caught + fixed (`WhisperText.clean` strips non-speech markers; `MeetingCapture.stop`
keeps the last good live transcript). `swift test` 165/6-skip/0-fail (+11). On-device 4B
latency is a few minutes per meeting (streamed + trimmed). HSM-8-05 (air-gapped gate) +
HSM-8-06 (ink-into-intelligence) remain. Earlier: **HSM-8-03 DONE — transcript linking (Phase 8 now 3/6).**
`TranscriptLinker` (RuntimeCore) anchors a note/mark on a `Segment` start time (stable
across re-render/sync, not text offsets), resolves to the containing/nearest segment (nil
when no transcript — graceful), bidirectionally, persisted per meeting via a `LinkStore`
seam. The app gained a ★ "Mark this moment" button during recording + a marked-moments
list in the detail that taps to jump to the transcript. `swift test` 154/6-skip/0-fail
(+8); run live on a physical iPad (granular per-segment jumps await HSM-3-02's
segmentation; the anchor logic is already right for it). Earlier: **HSM-8-02 DONE — the PencilKit notebook (Phase 8 now 2/6).**
A `Notebook` view-model (RuntimeCore) round-trips PencilKit pages (serialized `PKDrawing`
blobs) through a `NotebookStore` seam, keyed per meeting + versioned, UIKit-free,
corrupt-safe. The app gained a real PencilKit canvas + the system tool picker
(pen/highlighter/eraser), multi-page nav, a `FileNotebookStore` behind the seam, a
Transcript/Notes segmented control so ink + the live transcript coexist, and a notebook
reload on the meeting detail. `swift test` 146/6-skip/0-fail (+6); the rich surface is
screenshot-verified + run live on a physical iPad. The owner's "magic pencil" is real.
Earlier: **HSM-8-01 DONE — the iPad on-device meeting-capture loop (Phase 8 opened, 1/6).** `MeetingCapture` (RuntimeCore) composes capture + a transcriber
factory + a `MeetingStore` seam: record → **windowed live transcript** → persist →
reopen-intact, fully on-device. `MeetingCaptureApp` is a Signal iPad shell (meeting list +
Record/Stop + live transcript + reopen) over a `WhisperKitTranscriber` + `SQLiteMeetingStore`;
public `Meeting`/`IntelStatus`/`Bookmark` inits added (Codable/schema unchanged). `swift
test` 140/6-skip/0-fail (+7); the on-device transcription is the same WhisperKit path proven
on metal in HSM-13-04; built + run live on a physical iPad. The standalone on-device
paradigm (Track I) is underway. Earlier: **HSM-12-03 DONE — the unified Companion shell (Phase 12
now 3/4).** `CompanionShell` (RuntimeCore) composes the HSM-12-01 link + HSM-12-02
meetings with the iPad's own `LocalRuntimeSummary` into one state; an unreachable desktop
is a calm `localOnly` mode, never a blocked app. `CompanionShellApp` is a custom Signal
shell — a 3-tab bottom bar (Meetings / Dictate / Companion), connect onboarding, meetings
start/stop, and the "THIS iPAD" on-device peer shown first-class **alongside** the
"DESKTOP" server card (the "not a dumb terminal" principle, made visible). `swift test`
133/6-skip/0-fail (+4); screenshot-verified on the iPad-Pro sim (connected + unreachable)
and run live on a physical iPad. Only HSM-12-04 (the Track M gate) remains in Phase 12.
Earlier: **HSM-13-03 DONE — the Companion board; PHASE 13 — ANSWER THE CODER COMPLETE (4/4).** A `CompanionBoard` seam (`companionStatus`/`select`/`dismiss`/
`pin` over `/api/companion/*`) + RuntimeCore view-model surface the waiting coder(s) and
make the selected reply target unmistakable; selection is server-side so the answer
delivers to it with no silent default. `CompanionAnswerApp` renders the board (each
waiting coder + its question, confidence, pin/stale; "Answer this one"). `swift test`
129/6-skip/0-fail (+7 `CompanionBoardTests`); app builds for device. The companion track's
payoff is real end to end: point the iPad at the server you code against, see the agent's
question, pick the target, answer **by voice** — on-device transcription, delivered into
the coder, never autonomous. Earlier: **HSM-13-04 DONE — the answer-the-coder gate
ACHIEVED by voice (Track N / Gate 10).** A `CompanionAnswerApp` surfaces the waiting coder's question,
records a spoken answer, transcribes it **on-device** with WhisperKit (a real
`WhisperKitTranscriber` driving the HSM-13-02 `VoiceNoteComposer` over `AudioCaptureService`),
review, and delivers it into the coder. **Proven on a physical iPad Air M4:** question
surfaced → a spoken answer → on-device WhisperKit → landed in a live tmux coder pane, never
autonomously. The first run caught a Whisper control-token leak in the delivered text —
fixed with the pure, unit-tested `WhisperText.clean` (+5 tests) and redeployed. `swift test`
122/6-skip/0-fail; the voice app builds + links WhisperKit for device. Only HSM-13-03 (the
Companion board, multi-target selection) remains in Phase 13. Earlier: **HSM-13-04 — the
answer-the-coder gate, delivery half proven on real metal.** The keystone HSM-13-01 deferred — real delivery — is wired:
`WebRuntime._deliver_remote_dictation` delivers a companion answer into the waiting
coder via the EXACT path local dictation uses (`_try_tmux_agent_reply` → `tmux
send-keys`, `typer` fallback), deliver-only and **raises** when undeliverable (no false
ack). Proven end-to-end: a **real** Stop-hook awaiting session → an answer
**originating on a physical iPad** (the CompanionProbe grew an "Answer the coder" send)
→ **landed in a live tmux coder pane** (`tmux capture-pane` committed). `uv run pytest`
(delivery) 5 / sweep 315 passed; the iPad harness builds for device. The gate stays
**in-progress** — the iPad sent typed text, not a native voice note (needs on-device
Whisper, a pending Phase-3 device gate), and the HSM-13-03 board remains. Next:
HSM-13-03, then close the gate by voice. Earlier: **HSM-13-02 done — the native
voice-note composer (Phase 13 now 2/4).** `VoiceNoteComposer` (RuntimeCore) is a state machine —
record → transcribe on-device → review/edit → deliver — over three seams it does not
own: the Phase-2 `IAudioCapture`, a `([AudioChunk]) -> ITranscriber` factory (built
over the captured audio; no second transcription path, MLX discipline stays inside the
transcriber), and the HSM-13-01 `sendRemoteDictation`. The owner's hard line is
structural: `stopAndTranscribe()` always lands in `.review` and `send()` is separate —
**nothing is delivered before an explicit send**; an empty note is guarded. `swift
test` 117/6-skip/0-fail (+10 over fake seams); the live on-device walkthrough folds
into HSM-13-04. Next: HSM-13-03 (the Companion board). Earlier: **HSM-13-01 done — the
remote-dictation inject path, LAN-proven (Phase 13 opened, 1/4).** The desktop's first answer-the-coder surface:
`POST /api/dictation/remote` runs a client-dictated answer through the **same rich
pipeline** as the browser dry-run (corrections/blocks/plugins) and hands the
*processed* text to a new `on_remote_dictation` host hook (no hook → process-only;
hook raises → `502`, never autonomous). The Swift seam
`IDesktopClient.sendRemoteDictation` + `RemoteDictationResult` posts it, token joined
at call time. A new `HOLDSPEAK_WEB_HOST` override lets the desktop bind off-loopback
(default `127.0.0.1` unchanged) so a companion can reach it — token-enforced. **Proven
on real metal:** a physical iPad Air M4 ran a new `CompanionProbe` device harness
(`gen-companion-probe.rb` + `companion-probe-device.sh`) and established a live
connection to this Mac's desktop runtime over the LAN (`192.168.1.28:8000 ←
192.168.1.67`), with off-loopback auth verified `401`-without-token → `200`-with —
the HSM-12-01 seam on real metal, seeding the HSM-12-03 shell. `uv run pytest` (route)
7 passed; `swift test` 107/6-skip/0-fail. Next: HSM-13-02 (native voice-note capture).
Earlier: **HSM-12-02 done — meetings remote control (host-proven).**
The `IDesktopClient` seam grew the meeting verbs — `listMeetings` / `runtimeState` /
`startMeeting` / `stopMeeting` — over the desktop's existing endpoints (`/api/meetings`,
`/api/meeting/start|stop`, `/api/runtime/status`), decoded to the server's exact wire
shape; the RuntimeCore `CompanionMeetings` view-model returns `Result`s so an
unreachable desktop degrades to a rendered failure (never a throw on the caller path).
`swift test` **105 passed / 6 skipped / 0 failed** (+9). Next: HSM-12-03 (the shell).
Earlier: **HSM-12-01 done — the Companion track's first code ships: the desktop client seam.** `IDesktopClient` is a non-throwing `handshake()
async -> DesktopConnection` seam (an unreachable desktop is a state, never an error);
`HTTPDesktopClient` + `DesktopPeer` pair host/port + token and probe `/health` +
`/api/runtime/status` over the desktop's existing API, honest `local + LAN → <host>`
egress, token joined at call time. The RuntimeCore `CompanionLink` holds the
interface — the core depends on the seam, not a transport — and a test proves
on-device work runs unaffected while the desktop is down ("not a dumb terminal",
made structural). `swift test` **96 passed / 6 skipped / 0 failed** (+12). Earlier
the same day: **Charter Amendment 1.1 RATIFIED** — the Companion relationship is now
co-canon with Rev 1.0: Tracks M–N, "companion to the desktop
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
**Current phase:** [phase-7-mir-port](./phase-7-mir-port/current-phase-status.md) closed; Phases 0 ✅, 1 ✅, 4 ✅, **6 ✅ Gate 5**, **7 ✅ Gate H**; Phase 5 host-complete (engine pick + structured output + endpoint Modes B/C + on-device Mode A + model packaging — all host-proven; device runs pending the iPad unlock); Phase 10 in-progress (HSM-10-01 done); 2 + 3 testable cores done, device-gated remainder; 6-06 Follow-ups deferred. **Phases 12–13 (Tracks M–N — the Companion Client + Answer the Coder) in progress (owner steer 2026-06-20): Phase 12 2/4 (HSM-12-01 seam + HSM-12-02 meetings remote, merged); **Phase 13 — Answer the Coder COMPLETE (4/4): HSM-13-01 inject, 13-02 voice-note composer, 13-03 Companion board, 13-04 Track N gate ACHIEVED by voice** (a spoken answer from a physical iPad, transcribed on-device, lands in a live tmux coder). Companion track (Tracks M–N) is now Phase 12 3/4 (12-01 seam, 12-02 meetings, 12-03 unified shell; only 12-04 gate remains) + Phase 13 done. **Phase 8 (Track I — the iPad on-device experience) 4/6: HSM-8-01 capture + 8-02 notebook + 8-03 linking + 8-04 on-device artifact review (the Track I workflow gate ACHIEVED on a physical iPad) done; HSM-8-05 (air-gapped gate) + 8-06 (ink-into-intelligence) remain.**

**Highest-value direction (owner steer, 2026-06-20; ratified in charter Amendment
1.1).** The program's value now concentrates on the **two device faces, both
first-class, on iPhone + iPad at parity**: (1) the **Companion track**
— point the iPad at the server you code against and **answer the coder by voice**
(Phase 12 → 13, the Answer-the-Coder payoff), and (2) the **air-gapped fully-local
notetaker** with a magic pencil that feeds the output (Phase 8, elevated: HSM-8-05 +
HSM-8-06). **HSM-12-01 (seam) + HSM-12-02 (meetings remote control) are done.** Next →
[HSM-12-03](./phase-12-companion-client/story-03-unified-companion-shell.md) (the
unified Signal shell that renders the seam — on-device runtime + server in one app).
The on-device richness (HSM-8-05/06) sequences behind Phase 6 + HSM-5-02 (Mode A) and
the iPad unlock; build its host-testable seams first, then gate on device.
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
| 12 | M | **The Companion Client:** point the iPhone/iPad at the same server you code against — a unified shell (on-device runtime + server, never a dumb terminal) + meetings remote control | **in-progress (2/4 — HSM-12-01 seam + HSM-12-02 meetings remote control done)** | [phase-12](./phase-12-companion-client/) |
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
