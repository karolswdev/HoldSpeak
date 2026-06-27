# HANDOVER — 2026-06-27 — The Primitive Framework + the device-reality gap

> Read this before touching the iPad. The framework is merged and strong; the **on-device
> experience is broken** and the owner is (rightly) furious. There is a precise punch-list.

## RESOLUTION — branch `holdspeak-mobile/desk-inworld-craft` (the one in-world pass)

The full punch-list is built and compiles (`xcodebuild` sim build SUCCEEDED; layouts
sanity-checked in the iPad 13" simulator — **simulator renders, NOT device proof; owner walks
the device**):

1. **Mic on every input** — a reusable `VoiceFillMic` (on-device WhisperKit, bound to any
   `String`) is now on the note title/body, KB name, the agent-builder fields + context + chat
   composer, the chain name + run input, the route "Ask" prompt, the Workbench node prompt, and
   the Connect name/host. (Credentials/ports are paste/number fields by design — not dictation.)
2. **No modals** — `DioNoteEditor`/`DioKBEditor` dim-scrim modals are **deleted**. Notes + KBs
   now edit IN-WORLD on the desk (`DioInlineNoteCard`/`DioInlineKBCard`): the card lifts where it
   sits, no scrim, commit on Done or a tap-away (transparent catcher).
3. **New Note / New KB** — instant card on the desk → straight into in-world edit. The create
   cluster (New Note/KB/Zone) is now always at hand (was gated off on empty/first-run).
4. **Connect on the desk** — `DioConnectCard` (host · port · **token** · Test · Connect/Forget),
   reachable from an always-visible "Connect your Mac" pill when unpaired and a manage gear when
   paired. No more classic-home-only pairing.

Also fixed in this pass: the **auth-token threading** (sync + the `DeskHostLink` companion path
both now ride `Authorization: Bearer <token>`, so LAN sends stop 401-ing) and the **schema
version bump** (v1→v2 so an existing device DB gains the framework tables on next launch).

STILL device-pending (only the owner can confirm on metal): the real cabled-iPad walk of each
of the four, and a note-made-on-iPad → web sync proof.

## TL;DR

- **The Primitive Framework is MERGED to `main`** (PRs #140, #141, #142). Every primitive class —
  content / capability / presence / organization — is first-class across **desktop hub + iPad + web**,
  one canonical contract. Execution (run Agent/Chain/Workflow), provenance/lineage, and a linear
  workflow-graph runner all landed, gate-passed, green.
- **BUT every screenshot that "proved" it this session was Simulator SEED DATA** (`SIMCTL_CHILD_*`
  hooks). The physical iPad has none of it. When the owner finally walked the real device, it was bad.
- **The owner's punch-list (NOT done — do this next, as ONE in-world pass):**
  1. **A mic on EVERY text input** (speak-to-fill, on-device Whisper). It's a voice product with no
     voice on its own fields. Most egregious miss.
  2. **NO MODALS** — note/KB editing must be **in-world on the desk** (edit the card in place), not the
     dimmed-form modal pattern. `DioNoteEditor`/`DioKBEditor` (and the coder sheets / run-target sheet)
     are the rejected pattern. Kill them.
  3. **New Note must actually create a note** — a card on the desk the instant you tap, editable in
     place. On device it "does nothing."
  4. **Connect/pair on the desk** — host/port/token pairing on `DioStage`. Today pairing only exists in
     the classic `MeetingListView` (gated behind `HS_CLASSIC_HOME`), which is **unreachable from the
     desk** (the front door on device). Owner: "nowhere to connect."

## Hard-won lessons (why it kept failing — internalize these)

- **Seeded Simulator ≠ device proof.** Every "wonderful" shot was seed data. [[feedback_verify_on_device_not_seeded]].
  Do NOT present a sim screenshot as proof again.
- **You cannot screenshot a physical iPad** via CLI (idb broken; `devicectl` has no screenshot). The
  owner is the only one who can see the device **and refuses to send screenshots** — asking pissed him
  off. So verification = ship to device, owner walks it. Diagnose from CODE, not by asking for shots.
- The owner walked the device: it is **full of meetings/zones/content** (NOT first-run; the `firstRun`
  empty-state theory was wrong). New Note dead, editors are "modal hells," no mic, no connect.
- Match seriousness. Own gaps flatly. No excuses, no seed claims, no screenshot requests.

## Git state

- On branch **`holdspeak-mobile/framework-provenance`** (already merged via #142) with **UNCOMMITTED,
  IMPORTANT edits** in `apple/App/MeetingCapture/DeskDioramaStage.swift` + `DeskSync.swift` — the
  **auth-token-threading fix** (a real bug the metal test caught; see below). DO NOT lose these.
  Recommended: branch fresh from `main`, carry these edits, build the punch-list on top, PR → merge.
- `main` = #140 (waves 1–4) + #141 (execution) + #142 (provenance/graph). The two prior feature branches
  (`desk-parity`, `framework-execution`) are on origin, merged.

## Two REAL bugs the metal test already caught

1. **Schema version never bumped.** The framework tables (`notes`, `directories`, `directory_memberships`,
   `agents`, `chains`, `workflows`, `kbs`) were added to `holdspeak/db/core.py:SCHEMA_SQL` but
   `SCHEMA_VERSION` stayed **1** → existing DBs (v1 == code v1) never get the tables → `no such table:
   notes` (500s on every framework route). **Worked around live** by running `SCHEMA_SQL` against the DB.
   **Code fix owed:** bump `SCHEMA_VERSION` + add a migration that creates the new tables.
2. **iPad sync dropped the auth token.** `DeskSyncDriver.make(host:port:)` built `HTTPSyncProvider` with
   **no `apiKey`** → LAN sync goes out unauthenticated → the token-gated hub 401s. **FIXED (uncommitted):**
   `make(host:port:token:)` now threads it; `DeskDioramaStage` added `@AppStorage("hs.peer.token")
   peerToken` and passes it. Commit this.

## The metal-test rig (live right now)

- **Hub running:** `HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_WEB_PORT=8765 uv run holdspeak web --no-open`
  → **`http://192.168.1.36:8765`**, token **`Fa-l2RbMr6tvqN8ACA7V-doJ89doNf-s`** (background pid 27307;
  may need restart with `dangerouslyDisableSandbox` to bind LAN; ensure the token via
  `web_auth.ensure_web_token`). LAN bind REQUIRES the token (`web_auth.nonloopback_bind_blocked`).
  Server-side loop PROVEN: `POST /api/notes` → appears in `GET /api/sync/pull` (send header
  `X-HoldSpeak-Token: <token>`).
- **Device:** AjPed = iPad Air 11-inch (M4), udid **`6B2F424D-707F-51F7-A33E-259427861CB1`**. The latest
  app IS installed (`dev.holdspeak.mobile`) but it's the broken-punch-list build. Keep iPad **UNLOCKED**
  for install/launch (`meeting-capture-device.sh` install/launch fails on a locked screen).
- iPad pairs via `DictatePeerStore` (`hs.peer.host`/`hs.peer.port`/`hs.peer.token`). `HTTPSyncProvider`
  + `HTTPDesktopClient` send `Authorization: Bearer <token>`. There IS a `ConnectView`/manual entry in
  `CompanionMesh.swift` — but only reachable from the classic `MeetingListView`, NOT the desk (punch-list #4).

## Build / deploy

- Toolchain is broken (Xcode-beta Swift 6.3 can't build swift-syntax). Workaround:
  `scripts/patch-llm-macro.sh` + build with `-disableAutomaticPackageResolution -skipMacroValidation`.
  [[reference_xcode_beta_swift_syntax_break]].
- **Sim:** `ruby scripts/gen-meeting-capture.rb` → `scripts/patch-llm-macro.sh "$PWD/build/meeting-capture-dd"
  build/HoldSpeakMeetingCapture.xcodeproj HoldSpeakMobile` → `xcodebuild ... -sdk iphonesimulator
  -destination 'platform=iOS Simulator,name=iPad Air 13-inch (M4)' -derivedDataPath build/meeting-capture-dd
  -skipMacroValidation -disableAutomaticPackageResolution build`. (New source file ⇒ re-gen; else `cp` the
  edited file into `build/meeting-capture-sources/` and skip re-gen.)
- **Device:** `scripts/meeting-capture-device.sh 6B2F424D-707F-51F7-A33E-259427861CB1` (run with
  `dangerouslyDisableSandbox` — it git-clones packages). iPad unlocked.
- PMO gate: every commit needs a fresh `.tmp/CONTRACT.md` (7 `[x]`), per `pm/roadmap/PMO-CONTRACT.md`.

## Key files

- **iPad desk:** `apple/App/MeetingCapture/DeskDioramaStage.swift` — `DioStage`. New Note/KB/Zone cluster
  ~L3311 (gated `selected==nil && !firstRun && !emptyZone`); `createNote()` ~L4289; modal editor
  presentations ~L3030 (`editingNote`/`editingKB`/`answeringCoder`/`openCoderSession`); `firstRun` ~L2584;
  `syncDesk(reason:)` ~L4180; `peerHost/peerPort/peerToken` ~L2510.
- **Modals to kill / rework in-world:** `DioNoteEditor` (~L755), `DioKBEditor`, `DioCoderAnswer`,
  `DioCoderSession` in `DeskCoder.swift`, `DioZoneEditor` (zone-as-hero — owner ACCEPTED this one;
  but he now lumps all dim-scrim overlays as modals — confirm direction). The voice-mic + in-world
  pattern should be ONE reusable thing applied everywhere.
- **Voice capture building block (for the mic-on-every-field):** `VoiceCaptureState` in
  `apple/App/MeetingCaptureApp.swift` (start mic → `stopAndTranscribe()` WhisperKit → `.text`). Build a
  reusable "speak-to-fill" mic bound to any `String`.
- **@main routing:** `apple/App/MeetingCaptureApp.swift` — no env ⇒ `DioStage()`; `HS_CLASSIC_HOME` ⇒
  `MeetingListView` (the only place with the Connect CTA + ConnectView).
- **Contract:** `apple/Sources/Contracts/{Primitives,Sync,Coding,Models}.swift`. Canonical spec:
  `pm/roadmap/holdspeak-mobile/contracts/THE_PRIMITIVE_FRAMEWORK.md`.
- **Hub:** `holdspeak/web/routes/{primitives,sync,workflow_graph}.py`, `holdspeak/db/{core,models,primitives}.py`,
  `holdspeak/web_auth.py`.

## Open follow-ups (lower priority than the punch-list)

- Schema-version bump + migration (bug #1 above).
- Branching-graph execution (needs a Blueprints runtime on the hub; linear case ships, branches refuse).
- `source_type` vocab pin (iPad "card" vs hub "input"; non-breaking).
- The full cabled-iPad sync proof (a note made on iPad → web) — blocked on the punch-list making the
  desk usable first.

See [[project_primitive_framework]], [[project_phase17_agent_sync]], [[feedback_verify_on_device_not_seeded]],
[[reference_xcode_beta_swift_syntax_break]].
