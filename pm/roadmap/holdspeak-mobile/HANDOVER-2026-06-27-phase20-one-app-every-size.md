# HANDOVER — Phase 20 — One app, every size (the iPhone pass)

> Read this top to bottom before touching a single view. It is built to make you ship
> the whole pass without re-deriving anything. Every file:line below was **verified against
> the working tree on 2026-06-27** (the parity-audit numbers were partly stale; the
> corrections are inline). The design is already decided — your job is to build it, not
> redesign it. Where this doc and an older note disagree, **this doc wins**; where this doc
> and `EXPERIENCE-VISION-2026-06-27.md` disagree, **the vision wins** (it is the design canon).

---

## 0. The one sentence

**Make every Apple surface reflow from the iPad diorama to a one-thumb iPhone "lane" through a
single width authority (`DeskCamera`), losing no object, glyph, or in-world law — then prove it
by hand on a cabled iPhone.** When the same desk, the same primitives, and the same long-press
"Route this" twin work at 390pt as they do at 1024pt, and the intelligence pull-out physically
migrates from the right edge to the bottom edge on a spring, the phase is done.

This is **layout debt, not capability debt** (audit theme 1). You are not inventing features.
Phases 18 and 19 built the surfaces; you make them fit through the doorway.

---

## 1. State of the world (you are starting clean)

- **`main` is green and clean.** Last merges this session: #157 (companion README + null-read
  guard), #161 (god-quality fixes), #162 (README steward), #158 (Fleet PYTHON). All landed.
  Full Python suite 2924 passing; Swift package suite 381 passing.
- **The Equilibrium program** (Phases 18–23) is the parent. Chart: `EQUILIBRIUM.md`. Phase 20 is
  **the iPhone pass**, deliberately sequenced AFTER 18/19 because "you cannot lay out at compact
  width what does not exist yet."
- **One compact adaptation already ships** — `DeskDioramaStage.swift:3085` (`let compact = w < 500`,
  the rail collapse + hidden decorative title). It is the **seed** of the pattern you generalize.
  It is also a **stray** you consolidate into `DeskCamera` (§4).
- **`@Environment(\.horizontalSizeClass)` is used in ZERO views today.** That is not a reason to
  avoid it — read §4 carefully, this is the single most important decision in the phase.

---

## 2. The design north star — read `EXPERIENCE-VISION` §4.3 in full

The vision (`EXPERIENCE-VISION-2026-06-27.md`, §4.3 "The adaptive iOS craft", lines 120–153) is
the spec. The essence:

> "The Desk is a place, and a place has to fit through a doorway. There is ONE doctrine, not two
> builds: the desk has a camera and screen width is the lens. The phone never feels like a worse
> iPad; it feels like the desk shrank to thumb-reach without losing a single object, glyph, or the
> in-world law."

**The three cameras (one authority, `DeskCamera`):**

| Camera | When | Layout |
|--------|------|--------|
| `.wide` | iPad full width | the lit diorama — absolute-positioned, drag-to-arrange, lasso |
| `.narrow` | iPad split-view / medium | the rail (the compact pattern that ships today, generalized) |
| `.lane` | iPhone (<~500pt) | a single thumb-reachable card column — **a new layout engine**, not a free reflow |

**The non-negotiable laws** (from §1 of the vision, "the rules that keep it one product"):

1. **Nothing is hidden or removed between sizes.** The same primitives reflow because they were
   all derived from one `DeskPrimitive` declaration. The lane *un-renders* the spatial arrangement;
   rotating back to `.wide` **restores the exact arrangement** (`positions[id]` is never destroyed —
   confirmed real state at `DeskDioramaStage.swift:2924`).
2. **No new modals.** The two already-shipping full-screen sheets (a meeting recording, settings)
   are sanctioned destinations. Everything else edits **in-world**. The rising bottom sheet on
   iPhone is **a hand-built offset container over a transparent catcher, NOT a dimming `.sheet`**
   ([[feedback_no_modals_in_world]]).
3. **A speak-to-fill mic on every text field** survives the reflow ([[feedback_voice_mic_every_input]]).
   `VoiceFillMic` already exists; do not drop it from any lane field.
4. **The honest egress badge rides along**, never reassurance prose ([[feedback_no_privacy_novels]]).

**The signature device moment (this is the screenshot/video that closes the phase):** in iPad
split-view, drag the multitasking divider and watch `DioPullout` physically migrate from the
right edge to the bottom edge **on a spring, in real time**. The pull-out content already travels
cheaply — it is `maxWidth/maxHeight: .infinity` — so only the entry edge and a grab handle change.

**The iPhone lane mock (from the vision, line 131):**

```
iPhone — DioStage, LANE camera (<500pt):
┌───────────────────────────┐
│ ⌶  ● synced 2m   ⚡Connect │  ← slim header: sync pill + connect
├───────────────────────────┤
│ ‹ ●meet ●models ●kb ●notes›│  ← sticky zone CHIP rail (tint pills)
├───────────────────────────┤
│ ┌───────────────────────┐ │
│ │ 📼  Standup          › │ │  ← full-width .signalCard row
│ │     CASSETTE · 3 decs  │ │     crisp pixel glyph @44pt
│ └───────────────────────┘ │
│ ┌───────────────────────┐ │
│ │ 💎  Infra KB         › │ │
│ └───────────────────────┘ │
│                      ╭───╮ │
│                      │ + │ │  ← accent FAB: New Note/KB/Zone
│                      ╰───╯ │
├═══════════════════════════┤  ← tap a row → sheet RISES from here
│ ▦ Standup        🔒 local  │     (same DioPullout content, grab handle,
│ ──────  ▁▁  ──────         │      over a transparent catcher, NOT a modal)
└───────────────────────────┘
```

The iPhone dictation surface has its own vision beat (§ "iPhone" line 65): the dictation mic
**promotes to a persistent bottom-edge HOLD BAR**; press-and-hold reflows to a bottom-up
teleprompter ("you said" muted nearest the thumb, "→ Cursor" above, destination+egress pill at
top), **no dim toward the bar** (a dim is a scrim). That is part of HSM-20-04's screen pass.

---

## 3. THE CRITICAL DOCTRINE CALL — `DeskCamera`, derived from `horizontalSizeClass` + width

**This is the decision the whole phase hangs on. Get it right in story 20-01 and the rest is
mechanical. Get it wrong and you will hand-hack twenty views and still ship something that breaks
on rotate and split-view.**

There is a tempting wrong answer: "the codebase uses `w < 500` width checks and doesn't use
`horizontalSizeClass`, so just keep adding `w < 500` checks." **Do not do this.** The vision is
explicit (line 128):

> "`DeskCamera` is introduced as the ONE width authority and the scattered `w >= 500` and
> `UIScreen.main.bounds` reads are folded into it (first story: 'DeskCamera is the only width
> authority; delete the strays')."

**The build:** introduce one `DeskCamera` enum (`.wide` / `.narrow` / `.lane`) derived from
**`horizontalSizeClass` first, geometry width second** (size class is what correctly distinguishes
an iPhone from an iPad in split-view; raw width alone lies on iPad multitasking). Plumb it once
(an `@Environment` value or a value passed from the top `GeometryReader` + `@Environment(\.horizontalSizeClass)`
read at the `DioStage` root) and **fold every stray width check into it.**

**The strays to delete (verified, exact):**

| File:line | Current stray | Folds into |
|-----------|---------------|------------|
| `DeskDioramaStage.swift:3085` | `let compact = w < 500` (rail collapse) | `camera != .wide` |
| `DeskDioramaStage.swift:2977` | `... && w >= 500 ? 1 : 0` (hidden title) | `camera == .wide` |
| `DeskDioramaStage.swift:2035` | `.frame(height: UIScreen.main.bounds.height * 0.62)` | geometry height, not `UIScreen` |
| `DeskDioramaStage.swift:3546` | `let b = UIScreen.main.bounds` | the camera's geometry |

After 20-01 there should be **exactly one** place that decides "how wide are we," and it returns a
`DeskCamera`. Everything else asks the camera.

---

## 4. The verified code map — what overflows, where (your work list)

All line numbers **verified 2026-06-27**. Where the parity-audit / status doc was wrong, the
correction is called out.

### 4a. The existing compact pattern (your seed — read it first)

`DeskDioramaStage.swift:3085–3115`. `let compact = w < 500`. When `compact && !railOpen` the
agent rail collapses to a slim trailing-edge tab (tap to expand); when `compact && railOpen` a
transparent canvas overlay dismisses it on tap; rail padding tightens (`compact ? 6 : 10`). The
decorative "HoldSpeak / drag a meeting" title is hidden via the `w >= 500` opacity at line 2977.
**This is the quality bar and the migration seed — generalize it into `DeskCamera`, don't bypass it.**

### 4b. Fixed dimensions that overflow ~390pt (the panels/cards/overlays)

| Component | File:line | Fixed dim | Note |
|-----------|-----------|-----------|------|
| `DioZoneEditor` (hero) | `DeskDioramaStage.swift:641` | `width: 380` | status doc CORRECT |
| `DioZoneEditor` (scroll wrap) | `DeskDioramaStage.swift:698` | `width: 380` | status doc CORRECT |
| `DioConnectCard` | `DeskDioramaStage.swift:1009` | `width: 380` | in-world card; cap to width−pad |
| `DioInlineNoteCard` | `DeskDioramaStage.swift:885` | `width: 304` | already near-safe; verify at 390 |
| `DioInlineKBCard` | `DeskDioramaStage.swift:927` | `width: 288` | already near-safe; verify at 390 |
| `DioRecordModePicker` | `DeskDioramaStage.swift:1400` | `width: 296` | safe-ish; center on lane |
| `DioLiveIntelCard` | `DeskDioramaStage.swift:2137` | `maxWidth: 440` | clamp to width−pad |
| `DioRunTargetSheet` | `DeskDioramaStage.swift:2137`-area | `maxWidth: 440` | clamp |
| `DioRouteSheet` | `DeskDioramaStage.swift:2241` | `maxWidth: 460` | clamp |
| `DioZoneEditor` (run result) | `DeskDioramaStage.swift:2315` | `maxWidth: 480, maxHeight: 520` | clamp |
| `DioSendCard` | `DeskDioramaStage.swift:2442` | `maxWidth: 460` | clamp |
| `DioActSheet` | `DeskDioramaStage.swift:2501` | `maxWidth: 460` | clamp |
| `DioCoderSession` | **`DeskCoder.swift:183`** | `width: 480, height: 560` | **status doc said `DeskDioramaStage` — WRONG FILE.** It's `DeskCoder.swift` |
| `DioCoderAnswer` | **`DeskCoder.swift:367`** | `width: 400` | **same correction — `DeskCoder.swift`** |
| `AgentEditor` | `DeskAgents.swift:625` | `maxWidth: 560, maxHeight: 740` | the agent builder modal |
| `ChainEditor` | `DeskAgents.swift:961` | `maxWidth: 560` | the chain builder modal |
| `ChainEditor` member picker | `DeskAgents.swift:1015` | `maxWidth: 420` | clamp |

`maxWidth: N` is *mostly* safe (it caps, doesn't force) but combined with horizontal padding it
can still touch edges at 390pt; the rule for the lane is **`maxWidth: min(N, width − 2*margin)`**
via the camera's helper. The hard `width: N` ones (380/480/400/304/288/296) are the real overflow.

### 4c. The dim-scrim overlays (the "modal hells" — kill or reframe)

Each is `ZStack { Color.black.opacity(...).ignoresSafeArea(); <fixed card> }`. The owner rejects
this pattern ([[feedback_no_modals_in_world]]); 20-02 reframes them as in-world or as the
hand-built rising bottom sheet (NOT `.sheet`):

| Overlay | File:line | Scrim |
|---------|-----------|-------|
| `DioZoneEditor` | `DeskDioramaStage.swift:635` | 0.78 |
| `DioRecordModePicker` | `DeskDioramaStage.swift:1394` | 0.40 |
| `DioRunTargetSheet` | `DeskDioramaStage.swift:2110` | 0.60 |
| `DioRouteSheet` | `DeskDioramaStage.swift:2191` | 0.55 |
| `DioSendCard` | `DeskDioramaStage.swift:2413` | 0.70 |
| `DioActSheet` | `DeskDioramaStage.swift:2463` | 0.70 |
| `DioCoderSession` | `DeskCoder.swift:160` | 0.74 |
| `DioCoderAnswer` | `DeskCoder.swift:322` | 0.78 |
| `AgentEditor` | `DeskAgents.swift:618` | 0.62 |
| `ChainEditor` | `DeskAgents.swift:906` | 0.62 |

**Already in-world (no scrim — the GOOD pattern to copy):** `DioInlineNoteCard` (841–894),
`DioInlineKBCard` (899–937), `DioConnectCard` (942–1017) — lift in place, dismiss on Done or
tap-away over a transparent catcher. This is the template for reframing the scrim overlays.

### 4d. The keystone: `DioPullout` (the migrating intelligence pane)

`struct DioPullout` at `DeskDioramaStage.swift:1200`, rendered at `:3197`. Its content is already
`maxWidth/maxHeight: .infinity` (the vision counted on this — confirmed). **It is the object that
migrates right-edge→bottom-edge on a spring** in the signature moment. 20-02 changes only its
entry edge + a grab handle by camera, not its content.

### 4e. The capture canvas — the responsive exemplar (mostly already correct)

`LiveCaptureCanvas` at `MeetingCaptureApp.swift:1137–1186`. Root is `GeometryReader`; tack zone is
`min(264, size.width − 72)`; stream is an unconstrained `VStack`. **It already scales** — use it
as the reference for how the lane should compute sizes. 20-03 mostly verifies it at 390pt and
docks the floating recorder + wraps any chip rows; it is the *least* broken surface.

### 4f. The connect screen + chip rows (HSM-20-04)

- **CORRECTION:** the status doc cites the unwrapped Port+Token row at `MeetingCaptureApp.swift:1641`.
  That is **the wrong location.** The real two-up row is `CompanionShellApp.swift:651–653`
  (`field("Port", ...).frame(width: 130)` next to `field("Token", ...)` inside `maxWidth: 560`).
  On lane, stack it vertically or make Port flexible.
- The **good** wrapping layouts to copy: `FlowChips` (`CompanionShellApp.swift:738`),
  `DioConstellationWeave` agent flow (`DeskDioramaStage.swift:1428`). Both wrap correctly.

### 4g. The app targets (what actually renders)

Two user-facing apps; the rest are harnesses. **Phase 20 owns the two below; ignore the harnesses
except to keep them compiling.**

- **`MeetingCaptureApp`** (`MeetingCaptureApp.swift:19`, `@main`) → `DioStage()` (the desk; the
  main surface). This is 80% of the phase.
- **`CompanionShellApp`** (`CompanionShellApp.swift:11`, `@main`) → `ShellView` (connect / meetings
  / dictate / companion). The connect + dictate screens are HSM-20-04.
- Harnesses (`HoldSpeakApp`, `SpeakHarnessApp`, `CompanionAnswerApp`, `InferenceHarnessApp`,
  `LocalHarnessApp`, `CompanionProbeApp`) — not user-facing; do not redesign, just don't break.

---

## 5. The stories (this phase ships its stories with the chart — build in order)

`20-01 leads` (the foundation). `20-02/03/04` are parallelizable once 20-01 lands (disjoint
surfaces). `20-05` is the gate. Full per-story detail is in the story files
(`story-01..05`); the one-liners:

| ID | Title | The crux |
|----|-------|----------|
| HSM-20-01 | The `DeskCamera` foundation | one width authority from `horizontalSizeClass`+width; delete the 4 strays; the lane card-sizing helper |
| HSM-20-02 | The desk at compact width | the lane card column; `DioPullout` migrates edge→edge on a spring; scrim overlays reframed; arrangement restored on rotate |
| HSM-20-03 | The capture canvas at compact width | `LiveCaptureCanvas` verified at 390pt; docked recorder; wrapped chips |
| HSM-20-04 | The forms + screens at compact width | connect (vertical Port/Token), settings, send/act sheets, the iPhone HOLD-BAR teleprompter |
| HSM-20-05 | On-device proof | every compact screen walked on a real iPhone — **the only thing that closes a row** |

---

## 6. Build + screenshot pipeline (copy-paste; this is exactly how you iterate)

**Toolchain caveat (load-bearing):** the Xcode-beta Swift 6.3 toolchain cannot build swift-syntax.
Always sever the LLM.swift macro and disable package re-resolution
([[reference_xcode_beta_swift_syntax_break]]).

### Simulator build + screenshot (the iteration loop)

```bash
cd /Users/karol/dev/tools/HoldSpeak/apple

# 1. Generate the flattened single-module xcodeproj (ONLY when you ADD a new .swift file;
#    otherwise cp your edited file into build/meeting-capture-sources/ and skip this — a stale
#    flattened tree will HIDE your compile errors, the #161 lesson).
ruby scripts/gen-meeting-capture.rb

# 2. Sever the LLM macro (idempotent).
scripts/patch-llm-macro.sh "$PWD/build/meeting-capture-dd" \
  build/HoldSpeakMeetingCapture.xcodeproj HoldSpeakMobile

# 3. Build for the iPHONE simulator (the whole point of this phase — NOT the iPad sim).
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
  -derivedDataPath build/meeting-capture-dd \
  -skipMacroValidation -disableAutomaticPackageResolution build
#   List available iPhone sims first: xcrun simctl list devices available | grep iPhone

# 4. Install + launch on the iPhone sim with a seeded desk (so the lane has cards to lay out).
DEV="iPhone 16 Pro"
xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl install "$DEV" \
  build/meeting-capture-dd/Build/Products/Debug-iphonesimulator/HoldSpeakMobile.app
SIMCTL_CHILD_HS_DEMO_HOME=1 xcrun simctl launch "$DEV" dev.holdspeak.mobile
sleep 4
xcrun simctl io "$DEV" screenshot /tmp/lane.png   # ABSOLUTE path required
open /tmp/lane.png
```

**Seed env vars (via `SIMCTL_CHILD_<VAR>`), so the lane isn't empty:** `HS_DEMO_HOME=1` (seeds
home content), `HS_DESK_CONNECT=1` (in-world Connect card), `HS_DESK_NOTE=1` (fresh note),
`HS_DESK_RECORD=transcript`, `HS_DESK_ZONE=<n>`, `HS_DESK_SETTINGS=1`. For the companion shell:
`HS_SHELL_TAB=<Tab>`, `HS_SHELL_DEMO=teleprompter|aftercare|artifacts`,
`HS_DESKTOP_HOST/PORT/TOKEN`.

### What `swift test` does and does NOT cover

`cd apple && swift test` is host-hermetic and fast — it builds + tests **Contracts / RuntimeCore /
Providers / InferenceLlama only**. It does **NOT** build the `Hosts` (SwiftUI app) target.
**A green `swift test` is NOT proof your view compiles** — only the `xcodebuild` sim build above is
([[feedback_verify_on_device_not_seeded]]). Run BOTH every iteration.

### Where screenshots go

`pm/roadmap/holdspeak-mobile/phase-20-one-app-every-size/screenshots/` (commit source + shots;
`build/` is gitignored). Name them by surface + camera, e.g. `desk-lane.png`,
`pullout-migrate-narrow.png`, `connect-lane.png`.

### The device build (for 20-05 — the owner runs this, but know it)

```bash
# Real iPhone (NOT a sim). Requires the device cabled + UNLOCKED; clones packages, so run it
# with the sandbox disabled.
scripts/meeting-capture-device.sh <iphone-udid>   # xcrun devicectl list devices  → find the udid
```

---

## 7. The hard-won lessons (internalize — these have bitten every prior mobile session)

1. **Seeded Simulator ≠ device proof.** A sim screenshot is for *your* iteration, never a closeout
   claim. Only the owner can walk the cabled iPhone, and **he will not send screenshots** — asking
   has angered him before. Diagnose from CODE; let HSM-20-05 be his button.
   ([[feedback_verify_on_device_not_seeded]]).
2. **A stale flattened source tree hides compile errors.** If you add a new file and forget
   `gen-meeting-capture.rb`, the build passes on the OLD sources and you ship something that won't
   actually compile (the #161 god-quality bug). Re-gen on every NEW file.
3. **No modals.** Reframing the scrim overlays in-world is half the phase's craft, not a footnote.
   The rising bottom sheet is a hand-built offset container over a transparent catcher, never a
   `.sheet`/`.fullScreenCover` ([[feedback_no_modals_in_world]]).
4. **The mic stays on every field** through the reflow ([[feedback_voice_mic_every_input]]). A lane
   text field with no `VoiceFillMic` is a regression.
5. **Egress badge, never prose** ([[feedback_no_privacy_novels]]). The badge rides the migrating
   pull-out; do not narrate privacy.
6. **Nothing is removed between sizes.** If a primitive exists on `.wide` it exists on `.lane`. The
   lane drops only *gestures the thumb can't do* (cross-desk drag → the long-press "Route this"
   twin that already ships), never *objects*.
7. **PMO gate every commit:** a fresh `.tmp/CONTRACT.md` with 7 honest `[x]` boxes per
   `pm/roadmap/PMO-CONTRACT.md`. The `Tests ran` box means you actually ran `swift test` + the sim
   build and read the output.
8. **Merge the green:** branch off `main`, build a story (or a few), open a PR, watch CI, merge
   with `--merge --delete-branch` ([[feedback_merge_phases_via_pr]]). Each story is mergeable alone.

---

## 8. Definition of done (the closeout bar)

- [ ] `DeskCamera` is the **only** width authority; the 4 strays (§3) are gone; `grep` for
      `UIScreen.main.bounds` and `w < 500`/`w >= 500` in the App targets returns only the camera.
- [ ] Every fixed-dimension card/overlay in §4b/§4c fits inside 390pt with margins, at `.lane`.
- [ ] The desk renders as the lane card column on iPhone; the FAB, the zone chip rail, and the
      slim header match the vision mock (§2).
- [ ] `DioPullout` migrates right-edge→bottom-edge on a spring (the signature moment), captured.
- [ ] The scrim overlays are reframed in-world / as the hand-built rising sheet (no `.sheet` dims).
- [ ] The connect Port/Token row and every chip row wrap/stack at 390pt; the iPhone HOLD-BAR
      teleprompter reflows bottom-up.
- [ ] `positions[id]` arrangement is restored exactly on rotate `.lane`→`.wide` (nothing destroyed).
- [ ] `swift test` green AND the iPhone-sim `xcodebuild` green for both apps.
- [ ] **HSM-20-05:** every compact screen walked on a real iPhone by the owner. **This is the only
      thing that promotes an iPhone matrix cell from forward-constraint to proven.** Until then,
      every cell stays `🟡`.

---

## 9. Pointers

- **Design canon:** `EXPERIENCE-VISION-2026-06-27.md` §1 (the laws) + §4.3 (Phase 20).
- **Program chart:** `EQUILIBRIUM.md` (Phase 20 row + the wave log).
- **Audit evidence:** `PARITY-AUDIT-2026-06-27.md` (theme 1).
- **Phase status + stories:** `phase-20-one-app-every-size/current-phase-status.md` + `story-01..05`.
- **Primitive contract:** `apple/Sources/Contracts/{Primitives,Sync,Coding,Models}.swift`;
  spec `contracts/THE_PRIMITIVE_FRAMEWORK.md`.
- **Memories:** [[project_primitive_framework]], [[project_equilibrium_program]],
  [[feedback_verify_on_device_not_seeded]], [[feedback_no_modals_in_world]],
  [[feedback_voice_mic_every_input]], [[feedback_no_privacy_novels]],
  [[reference_xcode_beta_swift_syntax_break]], [[reference_ios_simulator_screenshot]].
</content>
</invoke>
