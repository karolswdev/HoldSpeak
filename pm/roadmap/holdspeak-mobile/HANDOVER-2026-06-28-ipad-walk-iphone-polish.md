# HANDOVER — the iPad walk + the iPhone polish (Phase 20 device pass, continued)

> Read this top to bottom before touching a view. It is built so tomorrow is execution, not
> re-derivation. Everything here was verified against `main` on 2026-06-27 (file:line included).
> Today the Phase 20 iPhone reflow (20-01..04) merged AND the app was built, installed, and launched
> on a **real iPhone 17 Pro Max** for the first time — which immediately caught a device-only bug the
> simulator hid (now fixed, #178) and surfaced **a batch of usability issues** (see §3). Tomorrow:
> **walk the iPad** at the new camera, and **polish the iPhone** against those issues.

---

## 0. The one sentence

**Phase 20 made the desk reflow from the iPad diorama to a one-thumb iPhone lane through one width
authority (`DeskCamera`); the code is merged and runs on a real iPhone, but the first hand-walk
exposed real usability problems — so tomorrow we walk the iPad surfaces (`.wide`/`.narrow`, where
nothing has been device-verified yet) and we fix the iPhone lane/teleprompter against the issue list
in §3.** The bar for "done" is still the same: walked on real metal, not seeded sim shots
([[feedback_verify_on_device_not_seeded]]).

---

## 1. Where we are right now

- **`main` is green and clean.** No open PRs. CI is fully green for the first time in a while (a
  pre-existing companion web-smoke test was fixed mid-session, #168).
- **Phase 20 (the iPhone pass) is merged 20-01..04** (#164–#167):
  - **20-01 `DeskCamera`** (`apple/App/MeetingCapture/DeskCamera.swift`): the ONE width authority,
    `horizontalSizeClass` first then width (500pt boundary), `.wide`/`.narrow`/`.lane`. Resolved once
    at `DeskDioramaStage.swift:3054`. All the old `w < 500` / `UIScreen.main.bounds` strays fold into it.
  - **20-02 the lane + the migrating pull-out** (`DeskDioramaStage.swift`): `laneColumn` (:3808) is a
    one-thumb card column; the pull-out rises from the bottom edge on `.lane` (the `let lane =
    camera.isLane` branch at :3364) and enters from the right on iPad.
  - **20-03 the capture canvas** (`MeetingCaptureApp.swift` `LiveCaptureCanvas`): docked recorder +
    one-thumb tap-to-tack.
  - **20-04 forms + the hold-bar teleprompter** (`CompanionMesh.swift` `DictateView.laneBody` :511,
    `teleprompter` :533, `holdBar` :556; `CompanionShellApp.swift` connect stack at `if isLane {`
    :656; coder/connect/zone clamps via `camera.cardWidth`).
- **20-05 (the device walk) is IN PROGRESS.** The app is **built + installed + launched on the iPhone
  17 Pro Max** (#178 fixed the device-only build break the sim hid — see §7). The owner's hand-walk
  happened and found usability issues (§3). The iPhone matrix cells stay `🟡` until the polished build
  is re-walked.
- **The iPad has NOT been walked at the new camera.** `.wide`/`.narrow` render in the simulator and on
  `main`, but no one has put the merged Phase-20 build on a physical iPad and exercised the diorama +
  the rail + (critically) **split-view**, where the pull-out is supposed to migrate right→bottom on a
  spring as you drag the divider into compact. That signature moment is unproven on metal.
- **Side quest, DONE and separate:** the **Cadence Engine** (desktop Python, `holdspeak/cadence/` +
  `pm/roadmap/holdspeak/cadence-engine/`) shipped its whole 8-phase program this session (#169–#177),
  off by default, LLM next-action proven on the `.43` endpoint. It is not mobile work; see §8 for the
  owner buttons so it isn't forgotten.

---

## 2. Tomorrow's two missions (suggested order)

**Mission A — walk the iPad (fresh ground).** Nothing on the iPad has been device-verified at the new
camera. This is quick to set up (the iPad is already cabled) and de-risks the whole "one app, every
size" claim. Walk: the lit diorama at full width; the rail at split-view/medium (`.narrow`); and the
**signature divider-drag** (split-view → compact → the pull-out migrates right edge to bottom edge on
a spring, in real time). Rotate and arrangement-restore.

**Mission B — polish the iPhone (the meat).** Fix the §3 usability issues on the lane, the rising
pull-out, the FAB, the capture canvas, the connect screen, and the hold-bar teleprompter. Iterate in
the **iPhone simulator** (fast loop, §6), then **re-install on the device** and re-walk (the sim is
for iteration only; the device is the gate).

Do A first (cheap, high-confidence), then sink the rest of the day into B. Both are the same Phase 20
story (20-05); the iPhone fixes may also touch 20-02/04's surfaces.

---

## 3. ⛳️ THE IPHONE USABILITY ISSUES — capture this FIRST, while it's fresh

> The owner walked the device and said *"omfg, a lot of usability issues."* The single highest-value
> thing for tomorrow is to **get that list out of the owner's head and into this section now**, before
> it evaporates. Each issue becomes a fix with a file:line target from §5.

Capture each as: **surface → what's wrong → what "good" looks like**. Template:

| # | Surface (lane / pull-out / FAB / capture / connect / teleprompter) | What's wrong (what you saw) | What good looks like | Likely file (see §5) |
|---|---|---|---|---|
| 1 |   |   |   |   |
| 2 |   |   |   |   |
| 3 |   |   |   |   |

**Suspected hot spots to probe deliberately while filling this in** (cheap places a lane reflow goes
wrong on a real 393pt phone with a notch/Dynamic Island + home indicator):

- **Safe-area / notch / Dynamic Island:** does the slim header (gear + connect pill + sync pill) clear
  the Island? Does the lane scroll start under it? Does the bottom (FAB, record orb, Qlippy, the rising
  pull-out's grab handle) clear the home indicator?
- **The FAB vs Qlippy vs the record orb vs the rail tab** all want the bottom-right/edge thumb zone —
  on the sim they were nudged apart (Qlippy to `y: h*0.66` on lane), but real-device crowding is the
  classic failure. Tap-target overlap is likely.
- **The rising pull-out:** height (`h * 0.74`), the grab handle, does it actually feel like a sheet, is
  it dismissible by tap-away, does its content scroll, does it cover the FAB/orb acceptably?
- **The lane rows:** glyph @44 crispness, row height, the chip rail horizontal scroll, empty/`needs
  review` states, long titles, the chevron affordance.
- **The hold-bar teleprompter:** press-and-hold ergonomics, the "no dim" reading, where the partial sits
  vs the thumb, release-to-send haptic, the egress pill placement.
- **The connect screen:** the stacked Port/Token, keyboard avoidance, the voice mic on fields
  ([[feedback_voice_mic_every_input]] — every text field needs a speak-to-fill mic; verify none were
  dropped in the lane reflow).
- **In-world editing:** New Note from the FAB edits in place (no modal, [[feedback_no_modals_in_world]])
  — does it actually feel in-world on a phone, keyboard included?

---

## 4. The device playbook (build → install → walk)

**Two devices are cabled** (confirmed via `xcrun devicectl list devices`):

| Device | devicectl id (pass THIS to the script) | HWUDID (what xcodebuild targets) |
|--------|----------------------------------------|----------------------------------|
| **iPhone 17 Pro Max** ("kczabel's iPhone") | `590C512D-66E2-5E72-B7FF-458B82B2AEC1` | `00008150-001644E421C0401C` |
| **iPad Air 11-inch (M4)** ("AjPed") | `6B2F424D-707F-51F7-A33E-259427861CB1` | `00008132-001928291E45401C` |

**Build + sign + install + launch** (the meeting-capture app = the Phase 20 surface):

```bash
cd /Users/karol/dev/tools/HoldSpeak/apple
# ALWAYS pass the device id explicitly — the script defaults to the first iPad, so without an arg an
# iPhone walk would silently install on the iPad.
scripts/meeting-capture-device.sh 590C512D-66E2-5E72-B7FF-458B82B2AEC1   # the iPhone
scripts/meeting-capture-device.sh 6B2F424D-707F-51F7-A33E-259427861CB1   # the iPad
```

Run it **with the sandbox disabled** (it clones SPM packages + talks to the device over the network).

**Gotchas hit today (all real):**

1. **The device must be UNLOCKED and stay awake** during the build, or the personalized **developer
   disk image fails to mount** (`error: The developer disk image could not be mounted on this device`).
   Unlock, leave the screen on, re-run.
2. **Developer Mode** must be on (Settings → Privacy & Security → Developer Mode; reboots the phone).
   The iPhone needed a moment to become a valid xcodebuild destination after pairing; the iPad already
   had it.
3. **`Failed to load provisioning paramter list … No provider was found.`** is **benign devicectl
   noise** — the lines that matter are `App installed:` and `== meeting-capture app launched ==`.
4. **The simulator HIDES device-only compile errors.** A green iPhone-sim `xcodebuild` is NOT proof the
   device build compiles (see §7 — `DictateDemo` was `#if targetEnvironment(simulator)` and only the
   device build caught the unconditional reference). **Device-build before claiming any Phase-20 cell
   done.**

**Launching with a seeded demo on device** (optional, for isolating one screen): the sim uses
`SIMCTL_CHILD_<VAR>`; on device the equivalent is `xcrun devicectl device process launch
--environment-variables` with the seed vars (`HS_DEMO_DICTATE`, `HS_DESK_OPEN`, `HS_DEMO_CAPTURE`,
`HS_DESK_CONNECT`, …). For the real owner walk, prefer the **real app flows** (no seed) — the seeds
were for the agent's sim screenshots.

---

## 5. The iPhone surface file map (verified `file:line` on `main`)

Where each adjustment lives:

| Surface | File:line | Notes |
|---------|-----------|-------|
| **The width authority** | `DeskDioramaStage.swift:3054` (`DeskCamera.resolve`); `DeskCamera.swift` | one place decides width; everything asks the camera |
| **The lane column** | `DeskDioramaStage.swift:3808` (`laneColumn`) | the card column + the kind-filter chip rail; rendered where `level(w,h)` used to be (the `if camera.isLane` branch ~:3015) |
| **Lane row / glyph / chip** | `DeskDioramaStage.swift:503` (`DioLaneGlyph`), `:522` (`DioLaneRow`), `:586` (`DioLaneChip`) | glyph @44 · title · BADGE · subtitle · chevron |
| **The migrating pull-out** | `DeskDioramaStage.swift:3364` (`let lane = camera.isLane`), frame at `:3372` | bottom-edge on lane (grab handle, transparent catcher); right-edge on iPad; spring keyed to `camera.isLane` |
| **The accent FAB** | search `Menu {` near the lane FAB in `DeskDioramaStage.swift` (added in 20-02) | New Note/KB/Zone; bottom-trailing, padded above Qlippy |
| **Qlippy reposition on lane** | `DioCompanion(...).position(... camera.isLane ? h*0.66 : h*0.86)` | nudged up to clear the FAB |
| **In-world note/KB on lane** | `DeskDioramaStage.swift:3136`–`3142` | clamped via `camera.cardWidth(304/288, in: w)` over a transparent catcher |
| **Fixed-card clamps** | `:3477` (zone), `:3486`/`:3494` (coder), `:3505` (connect card) | all `camera.cardWidth(N, in: w)` |
| **Capture canvas** | `MeetingCaptureApp.swift` `LiveCaptureCanvas` (~:1150); `LiveBubbleView` tack menu | docked recorder (RecorderDock.bottom default); one-thumb "Tack this moment" |
| **Hold-bar teleprompter** | `CompanionMesh.swift:511` (`laneBody`), `:533` (`teleprompter`), `:556` (`holdBar`) | `DictateView` branches by size class; bottom bar + bottom-up reflow, no dim |
| **Connect Port/Token stack** | `CompanionShellApp.swift:656` (`if isLane {`) | stacked on `.compact`, two-up on iPad |

The two user-facing app targets are `MeetingCaptureApp` (→ `DioStage`, the desk, 80% of the walk) and
`CompanionShellApp` (→ `ShellView`, connect/meetings/dictate/companion). The rest are harnesses; don't
redesign them, just keep them compiling.

---

## 6. The fast iteration loop (iPhone simulator — for fixing, before re-installing on device)

```bash
cd /Users/karol/dev/tools/HoldSpeak/apple
# Re-gen the flattened single-module project ONLY when you ADD a new .swift file (a stale flattened
# tree hides your edits/errors — the #161 lesson). Otherwise editing App/ sources is picked up.
ruby scripts/gen-meeting-capture.rb
scripts/patch-llm-macro.sh "$PWD/build/meeting-capture-dd" build/HoldSpeakMeetingCapture.xcodeproj HoldSpeakMobile
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath build/meeting-capture-dd -skipMacroValidation -disableAutomaticPackageResolution build
DEV="iPhone 17 Pro"; xcrun simctl boot "$DEV" 2>/dev/null || true
xcrun simctl install "$DEV" build/meeting-capture-dd/Build/Products/Debug-iphonesimulator/HoldSpeakMobile.app
SIMCTL_CHILD_HS_DEMO_HOME=1 xcrun simctl launch "$DEV" dev.holdspeak.mobile
sleep 4; xcrun simctl io "$DEV" screenshot /tmp/lane.png; open /tmp/lane.png
```

Seed vars (via `SIMCTL_CHILD_<VAR>`): `HS_DEMO_HOME=1` (seed content), `HS_DESK_OPEN=1` (open a
deliverable → the rising pull-out), `HS_DEMO_CAPTURE=1` (the capture canvas), `HS_DEMO_DICTATE=1` (the
teleprompter), `HS_DESK_CONNECT=1`, `HS_DESK_NOTE=1`. Phase-20 sim shots live in
`pm/roadmap/holdspeak-mobile/phase-20-one-app-every-size/screenshots/`.

**`swift test`** (`cd apple && swift test`) builds + tests Contracts/RuntimeCore/Providers only — it
does **NOT** build the App target. A green `swift test` is not proof a view compiles. Run the sim
build AND (before "done") the device build.

---

## 7. Toolchain gotchas (internalize — these bit us today and historically)

1. **The device build catches what the sim can't.** A symbol inside `#if targetEnvironment(simulator)`
   referenced from non-guarded code compiles on the sim and fails on device. This is exactly what bit
   20-04 (`DictateDemo`, fixed #178 by inlining the device-safe `NavigationStack { DictateView() }`).
   When you add any new entry point / demo seed, ask: does it reference a sim-only symbol?
2. **Xcode-beta Swift 6.3 cannot build swift-syntax.** The device + sim scripts sever the LLM.swift
   `@Generatable` macro (`scripts/patch-llm-macro.sh`) and build with
   `-disableAutomaticPackageResolution`. Don't remove this ([[reference_xcode_beta_swift_syntax_break]]).
3. **Re-gen the flattened project on every NEW .swift file** (`gen-meeting-capture.rb`); a stale tree
   hides errors.
4. **Standing iOS fixes that must never regress:** `GGML_NO_BACKTRACE` in `holdspeak/__init__.py`
   (desktop) and MLX being thread-bound (all MLX work pinned to one executor thread) — not Phase-20,
   but don't trip over them ([[project_phase60_wake_word]]).
5. **PMO gate every commit:** a fresh `.tmp/CONTRACT.md` with honest `[x]` boxes; merge phases via PR,
   watch-merge on green ([[feedback_merge_phases_via_pr]]).

---

## 8. The Cadence Engine — DONE this session (don't forget the owner buttons)

A whole separate desktop program shipped end-to-end: **the Cadence Engine** (a local-first technical
chief-of-staff). All 8 phases merged (#169–#177), off by default, the LLM next-action **proven on the
`.43` endpoint**. It is **not** mobile work and needs no more building. The only things left are the
**owner's buttons**, none of which the agent can press:

1. Turn it on: `cadence.enabled = true` (and `use_llm`, `cadence_telegram` if wanted).
2. The live dogfood walk: the new **Tier C** section in `dogfood/PROTOCOL.md`.
3. Pair a real Telegram bot: a `bot_token` + `pairing_code`, then `/pair` from a phone.

The user doc is `docs/CADENCE.md`; the program chart is
`pm/roadmap/holdspeak/cadence-engine/README.md`. Memory: [[project_cadence_engine]].

---

## 9. Pointers + memories

- **Design canon:** `EXPERIENCE-VISION-2026-06-27.md` §1 (the laws) + §4.3 (the Phase-20 adaptive iOS
  craft). Where this handover and the vision disagree, the vision wins.
- **Phase 20 master orientation:** `HANDOVER-2026-06-27-phase20-one-app-every-size.md` (the original,
  still accurate for the design intent).
- **Phase status + stories:** `phase-20-one-app-every-size/current-phase-status.md` + `story-01..05`.
- **Memories:** [[project_primitive_framework]], [[feedback_verify_on_device_not_seeded]],
  [[feedback_no_modals_in_world]], [[feedback_voice_mic_every_input]], [[feedback_no_privacy_novels]],
  [[reference_xcode_beta_swift_syntax_break]], [[reference_ios_simulator_screenshot]],
  [[feedback_high_ui_standards]] (flat/basic is rejected; apply richly, add affordances),
  [[project_cadence_engine]].

**The first move tomorrow:** fill in §3 from the owner's head, then `scripts/meeting-capture-device.sh
6B2F424D-…` to put the build on the iPad and walk Mission A while the issue list is fresh.
