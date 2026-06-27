# Parity Audit, 2026-06-27

## Equilibrium across desktop, web, iPad, iPhone

Equilibrium means full contract parity for every HoldSpeak feature across all four
surfaces (desktop hub, the web flagship, the iPad desk, and iPhone/compact width).
The desktop hub is the execution and persistence center; web and iPad are authoring
ports; iPhone is the same Apple codebase rendered at compact width. A feature is in
equilibrium when its contract is honored everywhere it belongs, with honest n/a calls
where a surface genuinely cannot host it (a browser cannot type into other OS apps; iOS
cannot capture system audio; the native desktop presence overlay has no analog inside a
sandboxed app). This audit grades each feature per surface, lists the confirmed gaps in
severity order with file:symbol pointers, and names the systemic patterns pulling the
surfaces out of balance. Every cell is honest, including the deliberate parked gaps.

Legend: ✅ full · 🟡 partial · ❌ missing · ➖ n/a

## Parity matrix

### Dictation

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Voice typing (hold-to-talk) | ✅ canonical home | ❌ cockpit only, no mic | 🟡 own-fields + remote-to-Mac | 🟡 logic ok, layout unproven |
| The dictation pipeline (route/rewrite/KB) | ✅ DIR-01 end to end | ✅ full cockpit | 🟡 remote-processed only | 🟡 placeholder tab |
| Voice command macros | ✅ board + dispatch | ✅ authoring port | ❌ absent, relay never fires | ❌ absent |
| The wake word + armed window | ✅ preview-by-default | ✅ settings + card | ❌ manual toggle only | ❌ absent |
| Spoken language + symbol dictionary | ✅ one knob, all paths | ✅ picker + editor | ❌ always auto-detect | ❌ absent |
| Activity pre-briefing (cited nudges) | ✅ full loop | ✅ nudge cards | ❌ no client | ❌ absent |

### Meetings

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Meeting capture (mic/system, speakers) | ✅ mic + system audio | ✅ live transcript | ✅ mic-only (iOS cap) | 🟡 canvas not compact-tuned |
| Multi-intent routing + plugin host | ✅ full MIR-01 host | 🟡 control yes, no timeline | 🟡 routing-decision subset | 🟡 chip overflow risk |
| Meeting import (recordings + transcript) | ✅ engine + CLI + route | ✅ drop zone | ❌ no file picker | ❌ absent |
| Faceted meeting archive (history/search) | ✅ SQL facets | ✅ facet row + search | 🟡 flat list, no facets | 🟡 worse on phone |
| Meeting aftercare (close-the-loop) | ✅ digest + file-issue | ✅ full card | ❌ no aftercare fetch | ❌ absent |

### Intelligence

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Visible learning loop (journal/correct/replay) | ✅ full contract | ✅ dedicated surface | ❌ parked (Phase 9) | ❌ absent |
| Meeting intelligence artifacts (14 plugins) | ✅ full wire shape | ✅ per-type renderers | 🟡 no confidence/sources | ❌ desk overflows phone |

### Actuators and connectors

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Actuators (propose, approve, execute) | ✅ full guard stack | ✅ byte-identical decide | 🟡 originate yes, no review list | 🟡 inherits + modal |
| Write connectors (GitHub/Slack/webhook) | ✅ gated framework | 🟡 Slack only configurable | 🟡 GitHub repo unpickable | 🟡 inherits gap |

### Config, presence, onboarding

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Config cockpit (settings) | ✅ every knob round-trips | ✅ sectioned + search | 🟡 local inference only | 🟡 same scope divergence |
| Desktop presence + Qlippy | ✅ native overlay | ✅ dock + cards | ➖ no in-app analog | ➖ no in-app analog |
| Egress / trust badge | ✅ machine-readable posture | ✅ compact chip | 🟡 hard-coded local badge | 🟡 inherits + unverified |
| Onboarding / first-run setup | ✅ doctor-backed wizard | ✅ welcome funnel | 🟡 desk orientation only | 🟡 connect screen cramped |

### Framework

| Feature | Desktop | Web | iPad | iPhone |
|---|---|---|---|---|
| Doctor, schema safety, release readiness | ✅ refuse-newer matrix | ✅ 1:1 doctor surface | 🟡 no refuse-newer, no doctor | 🟡 inherits gaps |
| The Primitive Framework (Note/KB/Agent/Chain/Workflow) | ✅ CRUD + run + sync | ✅ live authoring | ✅ in-world + sync | 🟡 fixed canvas, scrim sheets |
| The Workbench / Blueprints (node-graph) | 🟡 linear runner only | 🟡 prompt-only form | 🟡 rich canvas, no save/sync | 🟡 not compact-tuned |

## Prioritized equilibrium backlog

High severity

- [ ] (high·ipad) The dictation pipeline — no on-device or authoring surface; HTTPDesktopClient.swift implements only sendRemoteDictation, CompanionShellApp.swift:228 dictateScreen is a static placeholder → add client methods for /api/dictation/readiness, /blocks(+CRUD), /block-templates, /dry-run, /project-context and a SwiftUI authoring/preview screen; wire the Dictate tab to a real push-to-talk dry-run.
- [ ] (high·iphone) The dictation pipeline — same missing authoring/preview capability at compact width (CompanionShellApp.swift:228 placeholder regardless of width) → same fix as iPad, then verify single-column reflow at <500pt.
- [ ] (high·ipad) Voice command macros — relay silently never fires; api_dictation_remote (pipeline.py:299-369) goes straight to _run_dictation_dry_run_text and never calls dispatch_voice_command → gate on config.dictation.macros.enabled and call dispatch_voice_command before the dry-run, return {fired: kind}; add a remote-path test.
- [ ] (high·ipad) Spoken language setting — all three WhisperKit call sites (Stores.swift:42, CompanionAnswerApp.swift:44, SpeakHarnessApp.swift:108) omit DecodingOptions(language:) → wire the existing Providers WhisperLanguage registry, add whisperLanguage to InferenceConfigStore, pass the code (nil when auto) at all three call sites.
- [ ] (high·ipad) Spoken-symbol dictionary — no TextProcessor/spoken_symbols port exists in Swift; WhisperText.clean only strips control tokens → port TextProcessor (built-in tables + user symbols, one longest-first pass, user-wins) run after WhisperText.clean, add an editor in AppSettings.
- [ ] (high·ipad) Meeting intelligence artifacts — render without contract-required confidence and sources; ReviewUI.swift:530/611 bind type/title/body/status only though Models.swift carries them → add a confidence pill and N-sources chip matching history.astro:966-968, render the sources list in detail.
- [ ] (high·iphone) Meeting intelligence artifacts — DioStage front door uses fixed 380pt panels (DeskDioramaStage.swift:641/698) with no horizontalSizeClass branch, overflowing ~390pt iPhone portrait → restrict TARGETED_DEVICE_FAMILY to iPad, or add a compact path swapping fixed panels for a width-relative single-column meeting+artifact list.
- [ ] (high·ipad) Meeting aftercare — no digest fetch/render anywhere in apple/; HTTPDesktopClient has no /api/meetings/{id}/aftercare → add the client method and an aftercare card mirroring history.astro (open_items.by_owner, decisions, since_last_meeting diff; skip when is_empty).
- [ ] (high·ipad) Meeting aftercare — no file-an-accepted-action-as-issue; POST /api/meetings/{id}/aftercare/file-issue (meetings.py:999) never called from Swift → add a host call from an accepted action item, surface the proposal in the existing DeskHostLink.decide approval UI.
- [ ] (high·iphone) Meeting aftercare — absent at compact width (consequence of iPad gap) → once iPad aftercare exists, verify the card, by-owner groups, file-issue form, and follow-up sheet stay usable at <500pt.
- [ ] (high·ipad) Faceted meeting archive — flat lists only (MeetingListView L580, CompanionShellApp.swift L205); listMeetings() sends zero query params, no /api/meetings/facets caller → add facet/search params to listMeetings + a listFacets() and a SwiftUI search field plus filter row mirroring web /history.
- [ ] (high·iphone) Faceted meeting archive — long archive unusable without filtering; shared MeetingListView, no .searchable, no compact branch → ship the iPad search+facet row, collapse the facet row into a single Filter sheet at compact width.
- [ ] (high·web) Write connectors — the iPad companion's Webhook and GitHub connectors cannot be configured from web; settings.astro binds only slack_webhook_url (L274), system.py persists only Slack (857-877) → add companion_webhook_url and companion_github_repo inputs and persist them with the same consent hint and host-validation.
- [ ] (high·ipad) Write connectors — GitHub tile presents as ready whenever paired but DeskHostLink.propose (DeskDioramaStage.swift:2548) never sends repo and ignores github_configured → either pass a repo through propose for target github, or gate the tile's configured state on the host-reported github_configured flag.
- [ ] (high·ipad) Egress / trust badge — DioPullout (DeskDioramaStage.swift:1221-1224) hard-codes a 'lock.fill / On device' capsule for every primitive; DeskPrimitive has no egress property → add `var egress: EgressBadge.Scope` to the protocol (default .local), override on Mac-backed primitives, replace the inline capsule with EgressBadge(scope: prim.egress).
- [ ] (high·ipad) Doctor / schema safety — SQLiteStorage.swift:51-61 migrates only userVersion<2 then unconditionally stamps user_version=2, silently downgrading a newer-build DB (the exact data-loss case desktop refuses) → read user_version before migrate/stamp, throw StorageError.tooNew and refuse to open for writes when it exceeds schemaVersion.
- [ ] (high·ipad) The Workbench / Blueprints — the rich GraphCanvasView is disconnected from graph_json; no Save button, no serializer, startRun() runs against demo text and never persists → serialize the lowered Blueprint into WorkflowDefinition.graphJson (snake_case two-wire shape), add Save that upserts a WorkflowRecord and syncs via DeskSync; round-trip against workflow_graph.py:linearize.

Medium severity

- [ ] (med·web) Voice typing — /dictation has no in-browser mic; the only capture-shaped affordance is the typed dry-run (dryrun.js reads #dry-utterance) → add a browser-mic dry-run widget (getUserMedia → transcribe-preview endpoint reusing Transcriber + text_processor.py), framed as preview-not-inject.
- [ ] (med·iphone) Voice typing — zero size-class adaptation; dictate entry points hosted on iPad-canvas-first views (DeskDioramaStage absolute frames) → add a horizontalSizeClass==.compact branch (single column, full-width press-and-hold, simplified header), screenshot-verify the Dictate screen and a voice-fill field.
- [ ] (med·web) The dictation pipeline — user-facing copy calls it 'intelligent typing', a banned synonym (POSITIONING.md:105) in 5 strings (dictation.astro:51, index.astro:144, welcome.astro:204, setup.astro:120, HooksSection.astro:21) → replace with 'the dictation pipeline'/'dictation', add the term to _BANNED_NAMES, broaden the guard to scan web/src/**/*.astro.
- [ ] (med·iphone) Meeting capture — CaptureView/LiveCaptureCanvas (MeetingCaptureApp.swift) has zero compact-width adaptation; free-drag bubble stream + floating recorder + tack target assume a wide board and overlap at iPhone width → add a .compact path: vertical utterance list with tap-to-tack, pin FloatingRecorder to a fixed bottom dock.
- [ ] (med·web) Multi-intent routing — the two persisted per-meeting read routes /intent-timeline and /plugin-runs (meetings.py:578/629) have no web consumer; only the live route preview is shown → add an intent-timeline strip + plugin-run table to the history meeting-detail view.
- [ ] (med·ipad) Multi-intent routing — mark-free review.generate (ReviewUI.swift:120-122) uses bare MIRRouter.baseEmphasis[profile] and never calls IntentScorer, so off-profile above-threshold artifacts never fire → route mark-free generation through MIRRouter().route(profile:scores: IntentScorer.score(transcript)) via RoutedArtifactGenerator.
- [ ] (med·ipad) Meeting import — no way to import a recording or transcript; the only .fileImporter (ModelManager.swift:93) is GGUF-gated → add a .fileImporter for audio/text UTTypes and POST multipart to the paired desktop's /api/meetings/import via the DeskSync seam.
- [ ] (med·iphone) Meeting import — identical missing capability at compact width → when the iPad affordance lands, keep the picker, fields, and honest timestamp/ffmpeg note legible below 500pt; prefer an in-world desk affordance over a dimmed modal.
- [ ] (med·ipad) Visible learning loop — no journal/correction/digest/replay client; HTTPDesktopClient has no method for these routes (POSITIONING pillar 2 gap, deliberately parked per ENTITY-CATALOG.md:234-235) → add a read-first Learning/journal-review primitive consuming the existing hub routes; defer on-device journaling to Phase 9.
- [ ] (med·ipad) Artifacts — iPad never reads the hub's persisted /artifacts or /all-action-items, relying solely on changeset sync → add a getMeetingArtifacts read path, or guarantee+document the sync push as the single source of truth.
- [ ] (med·ipad) Actuators — no surface reads GET /api/meetings/{id}/proposals to review proposals generated elsewhere; only iPad-initiated sends are approve-after-preview → add a proposals review surface (Approve/Reject against the decision route) mirroring history-app.js.
- [ ] (med·ipad) Actuators — sendNow (DeskDioramaStage.swift ~4162) calls propose then immediately decide(approved:true), collapsing propose→review→approve into one tap → split the flow: propose first, render the server proposal preview/id, require a separate explicit approve tap.
- [ ] (med·ipad) Voice command macros — no authoring surface; web /commands board has zero Apple equivalent → add a CommandsBoard screen reading/writing settings.dictation.macros via PUT /api/settings, Test via /api/commands/test, four kinds, the 'runs code' honesty mark, and a speak-to-fill mic.
- [ ] (med·ipad) Activity pre-briefing — no activity client; the iPad never calls any /api/activity/* route → add an activity client rendering source-cited dismissible nudge cards, wire 'Dictate with this' to /api/activity/nudges/select before the next /api/dictation/remote.
- [ ] (med·ipad) Config cockpit — the 'Settings' screen is backed by local InferenceConfigStore UserDefaults; no GET/PUT /api/settings call exists, so the bare 'Settings' label implies hub parity it does not have → either rename to 'Inference'/'Where intelligence runs', or add a hub-config section over /api/settings for the safe shared knobs.
- [ ] (med·ipad) Egress badge — EgressBadge.Scope has only .local and .cloud; the canonical contract names three (local/mixed/cloud) and CompanionMesh hand-builds 'ON-DEVICE · …' text → add case mixed(String) rendering '⌂+☁ Local + <target>', have CompanionMesh use EgressBadge(scope: .mixed(...)).
- [ ] (med·ipad) Onboarding — no doctor-backed first-run wizard; DioFirstBoot verifies nothing (no permission/model/test/reward, no /api/setup/status) → add a one-time full-screen onboarding sheet (mic permission up front, model/endpoint pick + live test, first-capture reward, local first_run flag) mirroring welcome-app.js.
- [ ] (med·ipad) Doctor / schema safety — no backup-then-apply before migration and no backup/restore equivalent; SQLiteStorage runs the v1→v2 ALTERs in place → copy meetings.sqlite to a timestamped backup before migrateIfNeeded; expose a minimal backup/restore affordance.
- [ ] (med·ipad) Doctor / schema safety — no honest readiness panel; no view reports mic permission, model presence, store/schema health, or app version → add a System/readiness card to SettingsView (mic, on-device model, store integrity + userVersion, CFBundleShortVersionString).
- [ ] (med·iphone) Primitive Framework — the fixed spatial diorama crowds at ~375pt; prim.base card sizes and the create cluster never scale, only the rail/title are compact-aware → add a compact layout pass scaling card sizes and the cluster, or a vertically-stacked phone fallback list authoring the same records.
- [ ] (med·iphone) Primitive Framework — run/coder/zone overlays are fixed-size dim-scrim cards that overflow a phone (DioCoderSession 480x560, DioCoderAnswer 400, DioZoneEditor 380) → apply the in-world card pattern or compact-aware sizing + presentationDetents.
- [ ] (med·web) The Workbench — the web Desk cannot author a graph; submitWorkflow hardcodes graph_json:{} yet primitives.ts marks workflow authorable:true → build a minimal linear-chain builder emitting the same snake_case graph_json, or scope the web claim honestly (prompt-only) with a 'graphed on iPad' affordance.

Low severity

- [ ] (low·ipad) Voice typing — lands in own fields or remotely on the paired Mac; no native cross-app inject, remote degrades to Reach.asleep when the Mac is unreachable → document the iPad model in README/ARCHITECTURE; optionally add a share/keyboard extension.
- [ ] (low·web) Voice typing — hotkey editing (settings-app.js:144) only saves the trigger key; no armed indicator off runtime status → add a live hotkey-armed indicator driven off text_injection_enabled plus a last-press heartbeat.
- [ ] (low·ipad) The dictation pipeline — CompanionShellApp.swift:187 and MeetingCaptureApp.swift:845 narrate 'nothing leaves' reassurance prose, forbidden by POSITIONING.md:140-143 → replace with the standard compact egress badge (scope local).
- [ ] (low·iphone) Visible learning loop — no compact experience exists; dense journal/replay/correction layouts historically overflow narrow widths → when the iPad surface is built, single-column the entry list, wrap replay diff rows, full-height correction sheet.
- [ ] (low·iphone) Voice command macros — no compact layout because absent from Apple; dependent on the iPad board → build it compact-first (single-column cards, full-width fields, wrapping shell box, sticky Test/Save).
- [ ] (low·ipad) The wake word — desktop-only capability with no Apple analog; not even an n/a row in the Primitive Framework matrix → decide explicitly: document desktop-only in ARCHITECTURE with an n/a footnote, or add an iPad armed-window preview→confirm fork over WhisperKit.
- [ ] (low·iphone) The wake word — absent at compact width (feature absent on Apple) → forward constraint: any future Apple wake word renders the armed-window preview + single Type-it as a compact dismissible sheet with the 'not typed yet' badge.
- [ ] (low·iphone) Spoken language — no language picker or symbol UI to evaluate (feature absent) → when porting, build the language Menu and symbol rows to reflow vertically below 500pt.
- [ ] (low·ipad) Activity pre-briefing — dismiss persistence and briefing/records views also absent (no /records, /briefing, /nudges/{id}/dismiss calls) → add a records/briefing panel with per-card dismiss POSTing server-side.
- [ ] (low·iphone) Activity pre-briefing — missing at compact width (dependent on iPad gap) → give the nudge card a single-column compact variant: stacked citation chips, full-width primary action, reachable dismiss/clear.
- [ ] (low·ipad) Meeting capture — on-device speaker labels are session-scoped 'Speaker N' with no rename UI though SpeakerMatcher.rename exists; ReviewUI shows labels read-only → add an in-meeting or post-meeting rename sheet driving the existing rename seam, mirroring PATCH /api/speakers.
- [ ] (low·iphone) Meeting capture — lobbyBody's 440pt-min canvas + segmented picker + header can push the Record button toward the fold on an SE-class phone → relax LiveCaptureCanvas minHeight and/or collapse the Transcript/Notes picker so Record stays reachable.
- [ ] (low·ipad) Multi-intent routing — no plugin-host chain, intent windowing, or run/window lineage persistence (explicitly parked in MIRRouter.swift:6-17) → accept as a mobile-scope decision in a parity matrix, or fetch the hub's /plugin-runs + /intent-timeline read-only.
- [ ] (low·iphone) Multi-intent routing — the baseEmphasis type-chip row (MeetingCaptureApp.swift:1641) is a plain HStack with no scroll/wrap; 4 chips can overflow at iPhone width while the sibling lens row is wrapped → wrap the chip HStack in a horizontal ScrollView like line 1613 or use a flow layout.
- [ ] (low·ipad) Meeting import — AppSettings.swift:232 and SketchDiagram.swift:534 comment 'for recording + import', advertising an unwired capability → implement import (preferred) or correct both comments to 'for recording' until it lands.
- [ ] (low·ipad) Artifacts confidence/sources — covered under the high-severity render gap; the metadata is carried but not shown → render confidence pill + sources list in card and detail.
- [ ] (low·ipad) Actuators — DioSendCard/DioActSheet are full-screen dimmed scrims (Color.black.opacity(0.7)), the 'modal hells' pattern the owner rejects → reframe the send confirmation as an in-world card near the connector tile.
- [ ] (low·iphone) Actuators — DioSendCard does not adapt for compact width; header + 5-line preview + egress badge can push Approve/Cancel below the fold → at compact width stack the egress badge below the title and trim the preview lineLimit.
- [ ] (low·iphone) Write connectors — inherits the GitHub-no-repo gap; DioActSheet/DioSendCard are fixed VStacks with no ScrollView and can overflow a compact phone height → wrap content in a ScrollView and verify the send flow at <500pt on real metal.
- [ ] (low·ipad) Write connectors — the user approves a GitHub send before the resolved repo is shown (propose then immediate decide; preview never names the destination) → split the flow so propose runs first, display the host preview that names the repo, require a second confirm tap.
- [ ] (low·iphone) Egress badge — no compact-width on-device verification exists; a long cloud/mixed label could crowd or truncate against the DioPullout close button → after the DioPullout fix and the .mixed case land, capture a compact-width screenshot of a cloud/mesh-routed pull-out plus a CompanionMesh card.
- [ ] (low·ipad) Onboarding — no setup-status adapter parity; the companion never calls GET /api/setup/status when paired → fetch it via HTTPDesktopClient and show a readiness card (model configured? mic? first dictation done?).
- [ ] (low·ipad) Onboarding — no ambient/persistent TrustChip on the desk or connect screen; EgressBadge is only per-action → add an ambient egress/trust chip to the diorama chrome and connect screen, reusing the existing EgressBadge view.
- [ ] (low·iphone) Onboarding — CompanionShellApp.connectScreen is fixed at maxWidth 560 with a two-up Port+Token row and no compact branch → gate on horizontalSizeClass: stack Port and Token vertically and reduce the cap below 500pt.
- [ ] (low·iphone) Doctor / schema safety — no readiness surface to assess at compact width (consequence of iPad gap) → when added, follow the SettingsView ScrollView + maxWidth-760 + leading VStack idiom and provide an explicit dismiss control.
- [ ] (low·web) Primitive Framework — type drift: primitives.ts:153 declares Workflow.graphJson?: string but the wire and desk-app.js treat graph_json as an object → change to Record<string, unknown> | null.
- [ ] (low·ipad) Primitive Framework — WorkflowDefinition→WorkflowRecord is lossy and never round-trips graphJson; source_type vocab is unpinned ('card' vs 'input') → land the graph_json bridge and pin the source_type vocabulary across iPad and hub.
- [ ] (low·desktop) Primitive Framework — /api/sync/push inboxes meetings/artifacts to a JSON inbox rather than merging them live (HSM-10-03 territory) → complete the meeting/artifact live-merge so content primitives round-trip on push.
- [ ] (low·desktop) Desktop presence — the pyproject [presence] extra comment (lines 91-101) is stale forward-looking wording; the Linux libnotify/tray + GTK overlay renderers already ship → update the comment to state the shipped Linux renderers, drop the 'land with HS-41-05' phrasing.
- [ ] (low·iphone) The Workbench — no compact-width tuning for the node canvas; fixed 210pt node cards + dual port handles + cable drag are cramped on a phone → scale node cards / default zoom for compact, keep 42-52pt port targets, collapse the header below ~500pt.
- [ ] (low·web) The Workbench — the run UI drops the hub's honest signals; submitWorkflowRun ignores data.warning and data.steps → surface the warning as a visible notice and render steps as a per-node trail.
- [ ] (low·desktop) The Workbench — the hub linearizer drops per-node failure_policy and runs_on (GraphNode holds only id/kind/payload) while the Swift model carries them → read and apply per-node policy/target in the linear runner, or document the omission in the api_run_workflow docstring.

## Biggest equilibrium themes

1. **iPhone is layout debt, not capability debt.** Compact width (<500pt) exists in
   exactly one place (DeskDioramaStage.swift:3085) and only collapses the rail and hides
   the title. Every other Apple surface inherits the iPad layout: fixed 380pt panels,
   fixed-size dim-scrim overlays (DioCoderSession 480x560, DioSendCard, DioZoneEditor),
   free-drag capture canvases, and unwrapped chip rows. Most iPhone gaps are the same
   finding twice (the feature is absent on Apple, so there is nothing to lay out), so the
   real work is a deliberate horizontalSizeClass pass plus on-device proof.

2. **The iPad is an authoring port for the desk primitives but a tourist for the
   dictation and meeting-aftercare contracts.** Note/KB/Agent/Chain/Workflow/Directory are
   first-class and synced, but the dictation pipeline, journal/learning loop, voice macros,
   activity nudges, aftercare digest, meeting import, and faceted archive have no Swift
   client at all. HTTPDesktopClient implements a narrow slice (remote dictation, meetings
   summaries, companion, agent/chain run) and never touches the rich read routes the hub
   already exposes.

3. **Hub routes exist but are not surfaced.** Several gaps are pure plumbing-to-UI:
   web never consumes /intent-timeline or /plugin-runs; web cannot configure two of three
   companion connectors; the iPad never calls /api/setup/status, /api/meetings/facets,
   /artifacts, /aftercare, or /api/settings. The backend honors the contract; the ports
   leave it dark.

4. **Honesty drift in trust and provenance.** The egress contract is partly cosmetic on
   iPad (DioPullout hard-codes 'On device' for every primitive, the Scope enum lacks the
   canonical .mixed case), artifacts render without their confidence/sources provenance,
   reassurance prose forbidden by POSITIONING reappears in two Swift sites, and web copy
   uses the banned 'intelligent typing' name unguarded. The badges and names exist; they
   are not consistently driven by the real posture.

5. **The Workbench graph is authored richly on iPad but cannot travel.** The full
   Blueprint interpreter (two wires, control flow, typed edges, event stream) runs on
   device but never serializes to graph_json, so an authored graph runs once and is lost.
   The hub deliberately runs only a linear chain (dropping control flow, failure policy,
   and per-node targets), and web cannot author a graph at all. The graph-bridge is the
   keystone the cross-surface workflow story is waiting on.

6. **Mobile schema safety lags the desktop matrix.** The iPad's local store silently
   downgrade-stamps a newer-build DB (the exact data-loss case desktop refuses), with no
   backup-then-apply and no doctor/readiness panel. As sync brings newer peers into the
   mesh, this is the highest-leverage framework gap on the Apple side.

## Caveats (from the completeness critic)

This is a strong v1, but it has known blind spots, recorded here so a green cell never
reads as more certain than it is:

- **The iPad Primitive Framework ✅ reflects the post-#143 in-world pass**, not the older
  device-gap handover (which described New Note dead, modals, no input mics, no Connect on
  desk, all since fixed). The grade is current, but it is still the most compressed cell in
  the matrix: six primitives (Note / KB / Directory / Agent / Chain / Workflow) plus run +
  sync collapsed into one status, so a working Note can hide a weaker Agent or Directory.
  A v2 should explode this into one row per primitive with separate CRUD / run / sync /
  egress grades.
- **Agent Sync (the coder-as-synced-primitive, Phase 17)** and the **DeskOS desk shell /
  Directory-as-zone** have no rows of their own; they are folded into other cells.
- **"Voice mic on every input"** is a cross-cutting, owner-flagged contract and deserves its
  own parity line verified against real iPad fields.
- **Desktop is graded as the baseline, not independently verified.** Real desktop-contract
  holes (the workflow linearizer dropping `failure_policy` / `runs_on`, the sync
  push-inbox-vs-live-merge behavior, the serialization contract) are filed as low-severity
  footnotes rather than first-class findings.
- **The iPhone column is a forward constraint, not metal-proven.** Most iPhone rows are "the
  same finding twice" (absent on Apple, nothing to lay out); every 🟡/❌ there is unproven on
  a physical device per the verify-on-device rule.
