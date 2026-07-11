# HoldSpeak ecosystem usability audit and action plan

**Date:** 2026-07-09

**Status:** proposed execution brief

**Scope:** Apple flagship client, Web Desk, Python hub/runtime, desktop capture and ambient surfaces, shared contracts, release topology, and UAT

**Primary question:** Is HoldSpeak implemented well as “a small, powerful, AI operating system,” and what should happen next?

## Executive decision

HoldSpeak has implemented a credible local-first voice and meeting platform and a genuinely distinctive AI work-surface. It has **not yet implemented a dependable small operating system**.

The gap is not a lack of features. The gap is that a user cannot yet rely on one small, canonical product whose visible actions are reachable, truthful, recoverable, accessible, and durable across iPhone, iPad, Web Desk, and the hub.

The Apple app must be treated as a first-class product, not as a parity appendix. In fact, the Swift flagship is currently the clearest expression of the “AI operating system” idea: objects live in a place, computation has a visible destination, on-device work is real, and agent/meeting outputs materialize rather than disappear into chat history. Its strongest ideas should influence the ecosystem. But its production topology, capture durability, cross-device continuity, accessibility, and a few trust-critical paths are not release-ready.

The recommended program is therefore:

1. **Make the shipped Swift root canonical and honest.** One production app, one build identity, every claimed native workflow reachable from that app.
2. **Make capture and sync boringly durable.** A meeting must survive interruption, suspension, process death, network loss, and a failed intelligence step.
3. **Make errors visible and recoverable everywhere.** No failed create, record, send, sync, or import operation may disappear behind a dot, animation, or log.
4. **Adopt cross-surface invariants, not pixel parity.** iPad, iPhone, and web should use their form factors well while preserving the same object semantics, egress truth, consent, and lifecycle.
5. **Make physical-device and assistive-technology proof release gates.** Simulator evidence is necessary, not sufficient.

## Product doctrine

### The ecosystem has four first-class roles

| Surface | First-class role | Must work without another surface | What it should not become |
|---|---|---|---|
| **iPad Swift app** | Spatial work surface, on-device meeting capture and intelligence, mobile review, deliberate control of remote compute | Capture, transcribe, review, organize, and run an on-device workflow while disconnected | A remote control for the web app |
| **iPhone Swift app** | One-thumb capture, dictation, approval, interruption handling, and lightweight review | Capture/dictate locally, inspect state, recover work, and approve deliberately | A compressed iPad canvas |
| **Web Desk** | Dense desktop review, search, administration, multi-object work, and hub observability | Operate the local hub and complete desktop workflows without a phone | A pointer-only visual demo |
| **Python hub/runtime** | Durable authority, orchestration, sync, policy, connectors, and desktop audio | Run headlessly, preserve data, expose honest health, and refuse unsafe work | A second user interface with hidden state |

“First class” does not mean every feature is duplicated. It means a surface’s promised jobs are complete there, and shared entities have the same meaning everywhere.

### The small-OS test

For HoldSpeak to earn the operating-system claim, it must satisfy six properties:

1. **One understandable front door.** A person can identify the production app and find its principal verbs.
2. **Durable state.** Capture and authored work survive failures without special knowledge.
3. **Visible scheduling.** Users can tell what is running, where it is running, and what is waiting on them.
4. **Explicit authority.** Remote input and external actions require intelligible, scoped consent.
5. **Composable objects.** Meetings, notes, artifacts, agents, workflows, and zones share stable identity and provenance.
6. **Predictable degradation.** Offline, unavailable, unauthorized, partial, and failed are different visible states with recovery actions.

HoldSpeak is strongest today on properties 3–5. It is materially incomplete on 1, 2, and 6.

## Assessment scorecard

| Dimension | Assessment | Why |
|---|---|---|
| Product idea | **Strong** | Local voice, meeting intelligence, object-based Desk, visible run targets, and deliberate agent control form a coherent thesis. |
| Swift product concept | **Strong** | `DioStage`, `DeskCamera`, the iPhone lane, on-device capture, model management, and egress vocabulary feel like one designed product. |
| Everyday simplicity | **Mixed** | The ecosystem exposes many rooms, roots, modes, and specialist nouns before the primary loops are fully settled. |
| Production reachability | **Blocked** | Important native workflows exist only in classic/demo or separately built roots, while those roots share the production bundle identity. |
| Data durability | **Blocked** | Both native and desktop meeting capture retain the take in memory and commit the durable meeting only at stop. |
| Cross-device continuity | **Incomplete** | Native Desk primitives sync, but the flagship capture store is not wired through `SyncCoordinator`; the Desk snapshot explicitly sends no meetings. |
| Error recovery | **Weak** | Several web mutations and native post-processing failures settle into apparently normal states without a useful visible recovery path. |
| Trust and consent | **Promising but inconsistent** | Egress badges, approvals, steering grants, and Keychain profile keys are strong; false or overbroad copy and one false native dictation path undermine them. |
| Accessibility | **Not release-ready** | The flagship spatial objects are gesture views without complete accessibility actions; motion and fixed typography are not systematically adapted. Web Desk objects are also pointer-first. |
| Test foundation | **Strong below the glass** | Large Python and Swift suites exist, but current human/device acceptance and failure injection do not yet cover the production experience deeply enough. |

## Evidence base

This is a source, test, and live-surface audit—not a roadmap-summary exercise.

### Executed evidence

- Python unit suite: **2,793 passed**.
- Python integration suite: **701 passed, 1 failed, 3 skipped**, with two background-thread import warnings.
- UAT harness: **124 passed**.
- Swift package tests: **519 passed, 9 skipped**.
- Browser walk: 12 principal routes loaded without console errors.
- Web Desk failure injection: forced note-create and meeting-record failures did not produce a useful visible failure state.
- Current generated Swift app artifact installed on iPhone and iPad simulators. The staged `MeetingCaptureApp.swift` and `DeskDioramaStage.swift` matched repository sources.

### Important limits

- No physical iPhone/iPad verdict is claimed here. The existing HSM-20-05 device gate remains open.
- Simulator success does not prove microphone routing, lock/suspension behavior, Bluetooth changes, jetsam recovery, thermal stability, VoiceOver usability, or LAN behavior.
- The UAT program correctly distinguishes `ios_flagship`, `ios_companion`, and `ios_classic`; most of the historical feature evidence did not.

## What is implemented well

### Swift flagship

- The native app is an actual local runtime: microphone capture, Whisper transcription, SQLite storage, model download/import, local inference, diarization, and notebooks are not web wrappers.
- `DeskCamera` gives compact width one authority and changes the iPhone into a card lane instead of squeezing an absolute-positioned iPad canvas.
- The iPhone hold-bar dictation interaction is form-factor-specific and strong.
- The app distinguishes local, mixed, cloud, and mesh egress in its model and UI.
- Runtime profile API keys use Keychain storage and profile shapes sync without their secrets.
- Model downloads use a background URL session and can reattach after relaunch.
- The pairing card exposes its dial target, reachability result, peer name, and build string.
- Sync queues changes before network delivery and distinguishes unauthorized, hub error, contract mismatch, and unreachable states.
- Agent steering has a real grant model: pane identity, arm/disarm, TTL, named keys, result state, and explicit destructive acts.

### Hub and web

- `holdspeak doctor`, setup posture, migrations, egress modeling, runtime profiles, structured output validation, and connector approval boundaries show mature systems thinking.
- Dictation generally fails open instead of losing the user’s raw words.
- Meeting aftercare, provenance, typed artifacts, proposals, and audit records create a useful path from speech to deliberate action.
- Plugin execution has per-plugin isolation and queueing even though it remains in-process.
- The Web Desk has a small React root, a unified Zustand store, and a contract-driven primitive world rather than per-feature pages glued together ad hoc.

These are worth preserving. The action plan below is about making them reliable and legible, not replacing the product’s character with a generic dashboard.

## Stop-the-line findings

### IOS-P0-01 — There is no single trustworthy native release topology

**Evidence**

- `MeetingCaptureApp` defaults to `DioStage`; `MeetingListView`, the classic home, real 3D Desk, dictation, Commands, Workbench, and several other surfaces are selected by environment/demo roots.
- The separately generated meeting-capture, companion-shell, companion-answer, inference harness, local harness, and probe projects use `dev.holdspeak.mobile`.
- `gen-meeting-capture.rb` declares build 10, while `Capture-Info.plist` hard-codes `CFBundleVersion` to `1`; the built simulator app reports version `1`.
- The production display name is “HoldSpeak Meetings” even though the product root is now a broad Desk/agent/mesh runtime.
- `apple/README.md` still says the SwiftUI app is future Phase 8 work, and the meeting generator still says the app has no networking.

**User consequence**

The team cannot reliably answer which native product was installed, which capabilities a TestFlight build contains, or whether evidence came from the production app. A harness can replace the flagship on a device because it has the same identity. Build-number provenance is not trustworthy.

**Required action**

- Declare one canonical application target and checked-in route registry.
- Keep `MeetingCaptureApp → DioStage` as the recommended canonical root unless the owner explicitly reverses that decision.
- Merge production-worthy companion/classic capabilities into that root.
- Give every harness and experimental app a non-production bundle ID and display name.
- Move marketing version and build number to one generated source of truth; assert the final `.app` values in CI.
- Emit a build manifest containing commit, dirty state, target, bundle, build, schema, and feature-root inventory.

**Acceptance gate**

One command produces the only TestFlight artifact. The installed app displays the same bundle/build/commit recorded by UAT. No harness can install over it. Every native scenario names a route reachable without environment variables.

### IOS-P0-02 — “Talk to the desktop” does not talk to the desktop

**Evidence**

`DioRecordModePicker` offers “Talk to the desktop — dictate straight to your desktop.” Selecting it calls `startCapture(desktop: true)`, which only sets `captureDesktop`, changes UI copy to `DICTATING`, and shows mixed egress. `stopCapture()` still calls the local `MeetingCapture.stop()`, creates a meeting cassette, and runs the post-meeting lens pipeline. It never invokes `DictateModel` or `POST /api/dictation/remote`.

**User consequence**

The app claims that words are leaving for the desktop while saving a meeting locally instead. This is both a broken primary action and incorrect egress communication.

**Required action**

Choose one of two honest implementations:

- Route “Talk to the desktop” into the real `DictateView`/`DictateModel` path, including preview, delivery receipt, destination, and failure state; or
- Remove the option from the production picker until that wiring exists.

Do not keep a label-only branch.

**Acceptance gate**

A fixed canary phrase reaches the focused desktop field exactly once, the native receipt matches it, no local meeting is created, and an unreachable desktop preserves the phrase with Retry/Copy/Save as note.

### IOS-P0-03 — Native meeting capture is not crash-durable and memory grows with meeting length

**Evidence**

- `MeetingCapture` appends every 16 kHz mono PCM16 chunk to an in-memory array.
- The durable meeting row and WAV are written only in `stop()`.
- The WAV path is explicitly best-effort and its write failure is discarded.
- Final processing flattens chunks into another PCM array; diarization and WAV construction add peak copies.
- Raw PCM alone grows by about **115 MB/hour**, before arrays, chunks, inference buffers, transcript state, and final copies.
- App `scenePhase` handling controls mesh serving, not active capture. No audio background mode is declared.

**User consequence**

A crash, jetsam, forced termination, or unsupported background transition can lose the entire meeting. Long meetings create increasing memory pressure precisely when loss would be most expensive.

**Required action**

- Create a provisional meeting row at Record.
- Append PCM to an incremental, finalized-on-recovery audio journal rather than retaining the take in memory.
- Persist transcript checkpoints and capture metadata periodically.
- On launch, detect an interrupted take and offer Recover/Discard.
- Make audio-write failures visible and retryable.
- Define and implement the lock/background policy explicitly; do not imply continuous capture unless the OS configuration and device proof support it.

**Acceptance gate**

At 5, 30, and 60 minutes, force-kill the process, simulate disk-full, interrupt with a call/Siri route change, lock the device, and relaunch. The user recovers all audio up to the last bounded checkpoint, the meeting exists once, and resident memory remains approximately flat.

### IOS-P0-04 — Flagship meeting capture is not wired to cross-device meeting sync

**Evidence**

- `SyncCoordinator` is implemented and tested but has no app-layer call site.
- `DeskSyncStore.snapshot()` returns `ChangeSet(meetings: [])`.
- Incoming meetings are intentionally ignored by the Desk store because meetings are owned by the separate capture SQLite store.
- Native notes, recipes, KBs, artifacts, chains, workflows, directories, and memberships sync through a separate `@AppStorage` record system.
- Roadmap and architecture copy state that a meeting captured on mobile appears on desktop.

**User consequence**

The user sees a sync pill and a captured meeting on the iPad but does not have the promised continuity or a clear explanation that this class is local-only.

**Required action**

- Make the SQLite meeting/artifact store participate in the production sync coordinator.
- Reconcile Desk-derived artifacts with the canonical SQLite/sync representation instead of maintaining unrelated persistence islands.
- Define conflict behavior for edits and deletion before enabling two-way mutation.
- Until complete, badge meetings as “On this device” rather than “synced.”

**Acceptance gate**

Capture offline on iPhone/iPad, reconnect, and observe the meeting once on Web Desk with transcript, timing, audio availability policy, title edits, and provenance intact. Edit on both sides under controlled divergence and produce the documented keep-both/merge outcome without silent loss.

### IOS-P0-05 — The flagship is not operable as a first-class accessible client

**Evidence**

- `DioHero` is a `VStack` with drag and long-press gestures, not an accessibility button with equivalent actions.
- The collapsed tool dock is an `onTapGesture`/drag surface rather than a semantic control.
- The native Desk module contains more than 100 gesture sites but only a handful of explicit accessibility labels/actions.
- `DioStage` runs many continuous `TimelineView(.animation)` effects but does not read Reduce Motion.
- Fixed-point fonts and fixed card dimensions dominate the flagship; there is no documented Dynamic Type gate.
- The Web Desk repeats the problem: `DeskObject` is a pointer-driven `div` with no role, tab stop, keyboard open, move, select, or file actions.

**User consequence**

VoiceOver, Switch Control, keyboard, reduced-motion, and large-text users cannot reliably operate the defining product surface. This is not a secondary polish issue for an operating-system claim.

**Required action**

- Give every primitive a combined accessibility element with label, kind, sync/egress state, and actions: Open, Select, Ask, File, Move, and Delete where valid.
- Add non-spatial list access on iPad as well as iPhone; a spatial canvas cannot be the only semantic representation.
- Honor Reduce Motion by pausing continuous timelines and replacing travel/bob effects with state changes.
- Adopt text styles or scaled metrics and test at accessibility sizes.
- Bring Web Desk objects, zones, pullouts, menus, and overlays into a complete keyboard/focus model.

**Acceptance gate**

With the screen curtain on, complete: create a note, open a meeting, run an Ask, file an item, inspect egress, start/stop/recover a recording, and approve/refuse a proposal. Repeat the primary web flow using only the keyboard. No content or action is available only by drag, hover, or spatial position.

## High-priority findings

### IOS-P1-01 — Important native capability is compiled but not reachable from the flagship

The real `DictateView` and Commands board, Workbench, classic meeting home, and companion archive/aftercare/import/learning surfaces exist, but the current production root does not expose all of them. Settings and Models/Profiles are reachable from `DioStage`; that does not resolve the rest.

**Action:** Create a route/capability manifest for the canonical app. A capability can be marked shipped only if it has a user-reachable production route and a device test. Merge the daily-use companion capabilities; remove or clearly label experimental leftovers.

### IOS-P1-02 — Post-capture intelligence can fail and still settle as “Ready”

In `stopCapture()`, a failed lens breaks the pipeline, after which `weaveDone` is set to the total and the UI displays `Ready`. The meeting cassette survives, which is good, but incomplete deliverables are silently presented as completion.

**Action:** Settle into “Meeting saved · 2 of 4 insights ready,” name the failed step, and provide Retry remaining/Skip. Never backfill progress to 100% after a break.

### IOS-P1-03 — iPhone first-run teaches iPad gestures

The clean iPhone launch renders the same “Drop an object” and “Drag a meeting” instructions used by the iPad diorama. The iPhone lane actually uses tap, pullout actions, and long-press “File into…”. It also says an AI core “waits below” when no local model may be installed.

**Action:** Make onboarding camera- and readiness-aware. Teach one action by doing it: Record on both devices; on iPhone, Tap/Open and long-press/File; on iPad, drag/drop. Name model setup only when it is actually available.

### IOS-P1-04 — Secrets and transport posture are inconsistent

Runtime-profile API keys correctly use Keychain, but the hub bearer token is stored in `UserDefaults`/`@AppStorage`. The app allows arbitrary cleartext network loads so LAN and Tailscale HTTP work. The local-network permission copy says nothing leaves the network even though configured internet endpoint profiles are supported.

**Action:** Move the pairing token to Keychain, keep only non-secret peer identity in defaults, state the cleartext/private-network posture plainly, and make permission/privacy copy describe the app rather than one historical phase. Prefer TLS-capable pairing and narrowly scoped transport exceptions over a permanent arbitrary-load posture.

### IOS-P1-05 — The flagship view is too stateful to be robust

`DeskDioramaStage.swift` is about 6,379 lines. `DioStage` carries roughly 137 `@State`/`@AppStorage`/`@StateObject` properties, persistence, sync, multiple pollers, capture, routing, connector acts, agent chat, steering, games, and navigation in one view.

**Action:** Keep the visual composition but extract a `DeskSessionModel`, route coordinator, capture coordinator, sync coordinator, and poll lifecycle owner. Make the view render explicit state. Add teardown/cancellation and state-transition tests outside SwiftUI.

### WEB-P1-01 — Web Desk mutations fail silently

`createPrimitive()` does not reject non-2xx responses, and several save/file operations catch errors and assume refresh will explain them. `RecordOrb` returns to idle after start/stop failures. The store’s error is primarily rendered as a small hub dot tooltip/ARIA label, not a visible problem with recovery. Forced HTTP 500s reproduced the silence.

**Action:** Use one result/error contract for every mutation. Preserve optimistic work, show an inline error/toast with Retry, and distinguish validation, authorization, conflict, disk, and reachability failures.

### WEB-P1-02 — First-run “Skip” does not dismiss first run

The front door redirects whenever setup status reports `first_run`; the welcome page’s Skip links back to `/` but does not establish a durable dismissal. A person who cannot or does not want to complete dictation can loop back into the wizard.

**Action:** Persist an explicit onboarding disposition separate from “first successful dictation”: completed, dismissed, or needs-help. Keep setup warnings accessible without blocking Desk arrival.

### WEB-P1-03 — Web Desk is not a scalable desktop information surface

The Desk silently requests only 24 meetings and 24 artifacts, has no global search/filter, and uses an unbounded spatial world for the other primitive classes. `desk.css` has reduced-motion media queries but no responsive layout breakpoint; the 390 px browser walk showed overlapping chrome and overlays.

**Action:** Add search, kind/state filters, result counts, pagination/virtualization, and a semantic list mode. Define responsive chrome and bottom-sheet behavior. Never silently truncate a class; show “24 of N” and Load more.

### HUB-P1-01 — Desktop meeting capture has the same durability flaw at larger scale

The desktop recorder retains float32 microphone and system chunks in memory. At 16 kHz, two float32 streams are a raw lower bound of roughly **461 MB/hour**, before Python/NumPy/list overhead. A trimming method exists but is not used by the capture lifecycle. The meeting is persisted at stop.

**Action:** Stream both channels into journaled files, checkpoint metadata/transcript, bound the live-transcription window, and recover interrupted sessions exactly as on Swift. One capture durability design should govern both runtimes.

### HUB-P1-02 — Imported meetings are not recoverable jobs

Meeting import uses a daemon thread and a temporary file. Process exit can abandon the work; there is no durable job record, resume, or restart recovery. Integration tests emitted background-thread warnings when isolated stores disappeared underneath an import.

**Action:** Persist import jobs before accepting the upload, move source material to a durable staging directory, run through a supervised worker, and expose queued/running/failed/retryable/completed states.

### TRUST-P1-01 — Privacy positioning is absolute while the product supports configured cloud egress

The README says “No cloud” and comparisons say voice never leaves the machine. The product supports cloud/auto intelligence profiles, internet OpenAI-compatible endpoints, webhooks, Slack, GitHub, and mixed egress.

**Action:** Adopt one precise sentence everywhere: **“Local by default. Nothing leaves unless you configure and approve the path; every run names where it executes.”** Then test every surface against it.

### TRUST-P1-02 — Confidence is displayed with more precision than the system earns

Artifact synthesis averages plugin `confidence_hint` values, while valid built-in decision extraction can hard-code `1.0`. The companion UI then presents percentage rings. This is pipeline self-report, not calibrated factual confidence.

**Action:** Rename it to “extraction signal” or calibrate it on a labeled set. Prefer provenance coverage, validation state, model/runtime, and review status over a pseudo-probability.

## Medium-priority findings

| ID | Finding | Action |
|---|---|---|
| IOS-P2-01 | The first iPad screen is visually memorable but sparse and small relative to the canvas; principal verbs beyond Record are scattered into corner icons and rails. | After durability/reachability, conduct a five-task owner walk and promote the two most frequent non-recording verbs into labeled controls. |
| IOS-P2-02 | “Games” and decorative motion compete with still-incomplete core workflows. | Keep them as delight, but gate expansion until capture, sync, error, accessibility, and reachability gates are green. |
| IOS-P2-03 | Several native operations use `try?` or best-effort persistence without surfacing degradation. | Audit ignored errors by user consequence; render data-loss risks, log non-actionable cleanup only. |
| WEB-P2-01 | The main Dictation page begins with nine tabs and implementation terms such as Blocks. | Lead with the daily task and progressive disclosure; move diagnostics/advanced concepts behind an explicit advanced view. |
| HUB-P2-01 | Plugins execute in-process. Isolation protects the scheduler from one plugin’s exception, not the runtime from memory, CPU, filesystem, or malicious code. | Define trusted-plugin scope now; use subprocess/resource limits before third-party plugins are advertised. |
| DOC-P2-01 | Apple README, architecture, generator comments, old UX handoffs, and current production root disagree. | Generate a surface/release map from build manifests and retire or date-stamp stale handoffs. |

## Cross-surface invariant matrix

These are the product contracts the implementation and UAT should enforce.

| User concept | Invariant across Swift, web, and hub | Device-specific expression |
|---|---|---|
| **Meeting capture** | Record creates a durable provisional meeting immediately; Stop finalizes it; interruption never erases the whole take. | iPhone/iPad mic; desktop mic + system audio. |
| **Dictation** | The UI names destination before send, preview policy is explicit, delivery is exactly once, failure retains the text. | iPhone hold bar; iPad stage; desktop hotkey/HUD. |
| **Run target** | Every run names on-device, hub, mesh node, or external endpoint before execution and on the result. | Compact pill vs detailed receipt. |
| **Object identity** | A meeting/note/artifact/KB/workflow has one stable ID and one canonical lifecycle; layout is device-local. | Spatial object, lane row, or desktop list. |
| **Sync** | Local edits queue durably; synced/pending/local-only/error have precise meanings; no class appears synced if it is excluded. | Ambient pill plus per-object cue; detailed web status. |
| **Failure** | Unauthorized, unreachable, conflict, validation, disk, and partial completion are not collapsed into “offline” or silence. | Toast/card/banner appropriate to the surface. |
| **External act** | Propose → inspect target/payload → approve/reject → execute → audited receipt. No implicit connector execution. | Mobile approval is concise; web may show the full audit. |
| **Confidence/provenance** | Source coverage and review state are primary; numeric confidence is shown only if calibrated and explained. | Ring, chip, or detail row may differ. |
| **Accessibility** | Every action has a non-spatial, non-drag equivalent and deterministic focus order. | VoiceOver actions/list on Swift; keyboard/list on web. |
| **Onboarding** | Dismissal is durable; instructions describe the controls on the current device and current readiness. | iPhone teaches long press/tap; iPad may teach drag/drop. |

## Execution program

### Workstream A — Canonical Swift flagship

**Owner roles:** product owner + Apple lead

**Objective:** one native app whose shipped claims are reachable and device-proven.

| Action | Priority | Depends on | Proof |
|---|---:|---|---|
| A1. Lock the canonical target, bundle identities, version source, build manifest, and route manifest. | P0 | owner decision | CI artifact inspection + fresh install |
| A2. Remove or correctly wire “Talk to the desktop.” | P0 | A1 | canary typed exactly once + failure recovery |
| A3. Merge daily-use Dictate/Commands/Workbench/archive/aftercare routes or explicitly de-ship them. | P1 | A1 | no production capability requires an env flag or second app |
| A4. Make iPhone/iPad onboarding camera- and readiness-aware. | P1 | A1 | fresh-state physical-device walk |
| A5. Decompose `DioStage` into tested coordinators without changing the visual thesis. | P2 | A1–A4 stable routes | state-transition and lifecycle tests |

### Workstream B — Capture and continuity

**Owner roles:** Apple lead + hub lead

**Objective:** no primary speech or meeting data is held hostage by a clean Stop.

| Action | Priority | Depends on | Proof |
|---|---:|---|---|
| B1. Specify a shared append-only capture journal and provisional meeting lifecycle. | P0 | none | design review with failure matrix |
| B2. Implement native incremental audio/transcript persistence and recovery. | P0 | B1 | kill/disk/interruption/60-minute gates |
| B3. Implement desktop dual-stream incremental persistence and recovery. | P0 | B1 | kill/disk/2-hour memory gate |
| B4. Wire the flagship SQLite store through meeting/artifact sync. | P0 | A1, B2 | offline mobile capture → one web meeting |
| B5. Convert meeting import to durable supervised jobs. | P1 | hub job runner | restart/resume and retry tests |

### Workstream C — Visible, accessible surfaces

**Owner roles:** Apple lead + web lead

**Objective:** primary actions are discoverable without pointer dexterity or repository knowledge.

| Action | Priority | Depends on | Proof |
|---|---:|---|---|
| C1. Add native primitive accessibility elements/actions, Reduce Motion, and large-text adaptation. | P0 | A1 | VoiceOver + accessibility-size campaign |
| C2. Add Web Desk keyboard/focus semantics and semantic list mode. | P0 | none | automated axe/focus checks + keyboard sitting |
| C3. Establish one visible error/result component per platform and use it for all mutations. | P1 | none | forced 400/401/409/500/disk/network matrix |
| C4. Add Web Desk search/filter/count/pagination and compact layout. | P1 | stable API pagination | 1k-object and 390 px gates |
| C5. Persist onboarding completed/dismissed/needs-help. | P1 | none | fresh-user redirect tests |

### Workstream D — Trust and product canon

**Owner roles:** product owner + platform leads

**Objective:** the same words describe the same posture everywhere.

| Action | Priority | Depends on | Proof |
|---|---:|---|---|
| D1. Adopt local-by-default positioning and replace absolute no-cloud claims. | P1 | owner copy decision | repo copy lint + surface review |
| D2. Move hub pairing secrets to Keychain and document transport limits. | P1 | A1 | storage inspection + pairing migration test |
| D3. Replace/rename uncalibrated confidence percentages. | P1 | product decision | labeled-set report or new UI wording |
| D4. Generate current surface/build/capability docs; archive stale phase descriptions. | P2 | A1 route/build manifests | docs drift check in CI |

### Workstream E — Release evidence

**Owner roles:** QA/UAT owner + Apple/web/hub leads

**Objective:** release confidence comes from the shipped root under realistic failure, not from compiled code or a seeded screenshot.

| Action | Priority | Depends on | Proof |
|---|---:|---|---|
| E1. Extend UAT device registration with bundle/build/commit/device/OS/model/audio route fields. | P1 | A1 build manifest | verdict provenance is queryable |
| E2. Run Campaign 5 on physical iPhone then iPad against the exact flagship root. | P0 gate | A1–A4, B2 | signed owner verdicts |
| E3. Add destructive fault campaigns for capture, sync, import, and mutation errors. | P0 gate | B2–B5, C3 | recovery evidence attached |
| E4. Add VoiceOver, keyboard, Reduce Motion, and large-text campaigns. | P0 gate | C1–C2 | no primary-flow blocker |
| E5. Keep companion/classic campaigns quarantined until merged or intentionally shipped. | P1 | A1/A3 | no evidence cross-credit |

## Recommended sequence

### Wave 0 — Correct the product truth (0–2 weeks)

1. Decide and encode the canonical Swift target and bundle/build identity.
2. Remove or wire the false “Talk to the desktop” action.
3. Stop claiming native meeting sync until it exists.
4. Design the shared capture journal and begin native implementation.
5. Make web create/record failures visible.
6. Fix durable onboarding dismissal.

**Wave gate:** There is one identifiable production app, no visible action lies about its outcome/egress, and a failed web mutation produces a useful recovery state.

### Wave 1 — Make primary work survivable (2–6 weeks)

1. Ship native and desktop incremental capture/recovery.
2. Wire native meeting sync through the canonical store.
3. Make post-capture partial completion honest and retryable.
4. Move imports to durable jobs.
5. Add native VoiceOver/Reduce Motion/large-text support and Web Desk keyboard/list support.
6. Run the physical iPhone/iPad compact and capture walks.

**Wave gate:** A one-hour meeting, a disconnected edit, and an interrupted import survive induced failure; primary native and web flows can be completed without drag/pointer.

### Wave 2 — Make the system small again (6–12 weeks)

1. Merge/de-ship secondary native roots and expose daily workflows through one route model.
2. Decompose `DioStage` coordinators and consolidate native persistence islands.
3. Add Web Desk search/pagination/responsive behavior.
4. Normalize privacy/confidence/capability copy and generate live docs.
5. Complete the cross-surface functional campaign with per-device provenance.

**Wave gate:** The feature inventory, production routes, build artifact, docs, and UAT evidence agree without manual interpretation.

## Release gates

The following are mandatory for an “AI operating system” beta claim.

### Gate 1 — Canonical product

- Exactly one production iOS bundle/target and one version source.
- Every claimed native capability is reachable from the shipped root.
- Harnesses cannot overwrite the production app.
- Build/commit/device provenance is recorded automatically.

### Gate 2 — No catastrophic capture loss

- Native 60-minute and desktop 2-hour capture keep bounded memory.
- Kill, disk-full, interruption, and relaunch recover bounded-loss audio/transcript.
- Partial post-processing never changes a saved meeting into a failed capture.

### Gate 3 — Honest continuity

- Offline native capture syncs once after reconnect.
- Pending/synced/local-only/error are contract-tested and visibly distinct.
- Conflicts never silently discard a user edit.

### Gate 4 — Honest action and egress

- Every dictation/run/send names its target and outcome.
- No label-only or demo-only production action.
- Unapproved connector work cannot execute.
- Local/cloud/mesh copy matches observed traffic and configuration.

### Gate 5 — Accessible primary loops

- VoiceOver completes the native primary loop.
- Keyboard completes the Web Desk primary loop.
- Reduce Motion stops continuous decorative animation.
- Accessibility text sizes preserve actions and state.

### Gate 6 — Recoverable errors

- Forced 400, 401/403, 409, 500, timeout, offline, disk-full, and malformed response each produce the correct visible state and next action.
- No user-authored content disappears because a mutation failed.
- No spinner/progress UI settles as success after partial failure.

### Gate 7 — On-glass evidence

- Physical iPhone and iPad runs cover fresh install, both orientations, permission denial/recovery, lock, route change, offline, pairing, capture, sync, model run, approval, and steering.
- Companion/classic evidence is never credited to the flagship.

## First ten follow-up tickets

| Order | Ticket | Owner role | Done when |
|---:|---|---|---|
| 1 | IOS-P0-01 Canonical target, unique bundle IDs, and build manifest | Product + Apple | One artifact/identity/version truth |
| 2 | IOS-P0-02 Real desktop dictation or remove the false picker option | Apple | Canary reaches desktop exactly once |
| 3 | CAP-P0-01 Shared crash-safe capture journal design | Apple + hub | Failure semantics and format approved |
| 4 | IOS-P0-03 Native incremental capture/recovery | Apple | 60-minute kill/recover, bounded memory |
| 5 | HUB-P1-01 Desktop incremental dual-stream capture/recovery | Hub | 2-hour kill/recover, bounded memory |
| 6 | IOS-P0-04 Production meeting sync coordinator | Apple + hub | Offline capture appears once on web |
| 7 | IOS-P0-05 Native accessibility spine | Apple | VoiceOver primary loop passes |
| 8 | WEB-P1-01 Visible mutation and record failures | Web | Forced failure matrix passes |
| 9 | IOS-P1-02 Honest partial post-capture state | Apple | Failed lens shows saved + partial + Retry |
| 10 | WEB-P1-02 Durable onboarding disposition | Web + hub | Skip does not redirect-loop |

Do not start with visual polish, more mini-games, more primitive types, or another native shell. The first ten tickets remove false promises and data-loss paths from the daily loop.

## Decisions the owner must lock

Recommended defaults are included so work can proceed.

| Decision | Recommended default | Why |
|---|---|---|
| Canonical native root | `MeetingCaptureApp → DioStage` | It is already the production/TestFlight root and the strongest expression of the product thesis. |
| Fate of companion/classic apps | Merge useful routes into flagship; retain only as uniquely identified development schemes until retired | A second app with the same bundle ID is not a coherent product strategy. |
| iPhone support | First-class, with lane-specific interactions | The target already claims iPhone and substantial compact adaptation exists. |
| iPad support | First-class local runtime, not hub-dependent | This is the mobile program’s stated and architecturally valuable distinction. |
| Meeting authority | Local SQLite first, synchronized through the hub contract; layout remains device-local | Preserves offline ownership while enabling continuity. |
| Background capture | Support only after entitlement/OS behavior and recovery are device-proven; otherwise state the limit before Record | Silent suspension is worse than an explicit constraint. |
| Privacy line | “Local by default; configured and approved paths may leave the device, and every run names where it executes.” | Accurate across local, LAN, mesh, cloud, and connectors. |
| Confidence UI | Provenance/review state first; no percentage until calibrated | Avoids false precision. |

## Definition of done for each action

Every follow-up issue should use this structure:

```text
ID / title:
User goal:
Current production evidence:
Change:
Failure states:
Cross-surface invariants affected:
Acceptance criteria:
Automated proof:
Simulator/browser proof:
Physical-device or human proof:
Owner role:
Dependencies:
Documentation/capability rows changed:
```

An action is not done because code exists, compiles, or appears in a seeded screenshot. It is done when it is reachable from the production root, its error behavior is visible, its state survives the relevant failure, and the correct surface-specific acceptance proof exists.

## Evidence pointers

### Swift product and build

- `apple/App/MeetingCaptureApp.swift:19–83` — production root and environment-selected alternatives.
- `apple/scripts/gen-meeting-capture.rb:13–16, 119–128` — production bundle/build settings.
- `apple/App/Capture-Info.plist:7–16` — hard-coded display name and version.
- `apple/scripts/gen-companion-shell.rb:13–20, 49–57` — companion target sharing the production bundle identity.
- `uat/REVIEW-2026-07-09.md:23–29, 88–98` — current flagship and reachability audit.

### Swift usability and robustness

- `apple/App/MeetingCapture/DeskDioramaStage.swift:2937–3115` — `DioStage` state and production responsibilities.
- `apple/App/MeetingCapture/DeskCamera.swift:17–49` — compact-width doctrine.
- `apple/App/MeetingCapture/DeskDioramaStage.swift:1589–1600, 3594–3604, 4751–4803` — false desktop-talk branch and local stop pipeline.
- `apple/Sources/RuntimeCore/Capture/MeetingCapture.swift:35–48, 128–144, 184–238` — in-memory chunks and stop-time persistence.
- `apple/Sources/RuntimeCore/Capture/MeetingAudioStore.swift:4–16, 40–50` — stop-time best-effort WAV.
- `apple/App/MeetingCaptureApp.swift:174–178` — scene-phase handling limited to mesh serving.
- `apple/App/MeetingCapture/DeskSync.swift:59–97, 206–208` — Desk snapshot omits meetings and treats them as external/read-only.
- `apple/App/MeetingCapture/DeskDioramaStage.swift:4767–4792` — pipeline break followed by Ready/complete progress.
- `apple/App/MeetingCapture/CompanionMesh.swift:292–327` — hub token stored in UserDefaults.
- `apple/App/MeetingCapture/DeskDioramaStage.swift:316–395` — gesture-only wide-canvas object.
- `pm/roadmap/holdspeak-mobile/phase-20-one-app-every-size/current-phase-status.md` — simulator-complete compact work and open physical-device gate.

### Web and hub

- `web/src/pages/index.astro:17–29` and `web/src/pages/welcome.astro:19` — first-run redirect and non-durable Skip link.
- `web/src/desk/components/DeskObject.tsx:28–115` — pointer-driven Desk object without keyboard semantics.
- `web/src/desk/store.ts:143–180, 228–296` — mutation error swallowing.
- `web/src/desk/components/RecordOrb.tsx:62–95` — record failure returns silently to idle.
- `web/src/desk/api.ts:151–156` — silent 24-item meeting/artifact caps.
- `web/src/desk/desk.css` — reduced-motion rules but no compact-width layout rules.
- `holdspeak/meeting_recorder.py:58, 110–116, 354–380, 483, 525` — unbounded float32 capture chunks and unused trim seam.
- `holdspeak/web/routes/meeting_import.py:161, 204–220` — temporary upload and daemon worker.
- `holdspeak/plugins/synthesis.py:609–614` and `holdspeak/plugins/builtin/decision_capture.py:188–192` — self-reported confidence aggregation and hard-coded 1.0.
- `README.md:20` and `web/src/pages/settings.astro:265, 308–326` — absolute no-cloud copy versus configurable cloud paths.

## Final product judgment

The idea is implemented **well enough to be worth consolidating, but not well enough to broaden**.

HoldSpeak’s best qualities are unusually good: local-first computation is real, the system has a coherent object and provenance model, remote authority is often deliberate, the native Desk has character, and the iPhone/iPad adaptation is not merely a web view. Those are hard advantages to create later.

The immediate risk is feature abundance outrunning product truth. Multiple app roots, non-durable capture, missing meeting sync, inaccessible spatial controls, silent failures, and overconfident copy turn a powerful system into one that requires the author’s mental model to operate safely.

If the next program makes one Swift flagship canonical, makes capture/sync recoverable, and makes every failure and egress state explicit, HoldSpeak can credibly become the small AI operating system it is aiming at. If it continues adding surfaces before those invariants hold, it will remain an impressive collection of runtimes and demos rather than one dependable product.
