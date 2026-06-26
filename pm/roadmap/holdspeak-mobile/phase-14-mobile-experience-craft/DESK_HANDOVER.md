# The Desk (DeskOS) — handover for the next agent

> Rewritten 2026-06-26 after a hard **owner device-walk** that overhauled the desk's interaction model: the
> Tools dock was killed for a **radial summon**, recording moved **onto the desk**, and settings became
> reachable + model-pickable. The big unlock this session: **the app's iOS Simulator build works again**, so
> you can SEE the real desk on-screen without the cabled device. This top section is the CURRENT source of
> truth; everything under "HISTORICAL" is the 3D / pre-contract era (superseded). Companion docs:
> [[THE_DESK_WHOLE_PICTURE]] and [[story-25-the-desk-interaction-system]]. Running log:
> `current-phase-status.md` "Where we are".

## 0. The 60-second orientation

DeskOS is the iPad app reimagined as a spatial, gamified **command center**: meetings, their intelligence,
the AI, your knowledge, and your integrations are all **manipulable objects on one desk**. The iPad is a
**companion to the Mac** (the host). The front door is the **2.5D motion-first diorama**
(`apple/App/MeetingCapture/DeskDioramaStage.swift` = `DioStage`). The old 3D `LivingDeskCanvas` is unused in
the tree behind `HS_REAL_DESK=1` — leave it (the owner flagged deletion as a "let's understand it first"
decision; do NOT delete on a whim).

## 1. The philosophy (internalize this before touching anything)

You are the **Interface Alchemist**. The bar: coherent, meaningful, **delightful** leaps — premium is "I'm
delighted when I use it," and delight is felt in **motion**. The hard rules, learned the painful way this
session from a furious-but-right owner:

- **No generic, default, hidden chrome.** A hamburger drawer of square tiles, a separate "old window" for
  recording, an unreachable settings screen — all betray the premise. The desk **owns** the experience; pull
  every surface INTO the world. (The Tools dock was "the least imaginative UI experience imaginable" — and it
  was also *broken*. We deleted the concept, not just the bug.)
- **Everything is an object you act on, in place.** Routing, recording, reading the transcript, configuring —
  these happen as in-world moments, not modal detours.
- **Prove the feel.** Now that the Simulator works, SEE it on-screen before claiming it's good; then walk it
  on the metal for hardware feel. The owner reviews on the cabled iPad and reacts hard — own the gap honestly,
  don't spin.

## 2. The spine — everything is a DeskPrimitive (read this first)

`apple/App/MeetingCapture/DeskPrimitive.swift`. EVERY concept declares the same facets and the **entire UI is
derived** from that declaration — the canvas object, the pull-out, the routing.

- Facets: `kind` (→ glyph + colour), `title`/`subtitle`/`preview`, `sections` (the pull-out body — ONE
  renderer), `actions`, **`emits`**, **`accepts`**, plus the visual facets `glyph`/`color`/`base`/`isSymbol`.
- Conformers: `MeetingPrimitive`, `OutputPrimitive` (a generated card — itself routable), `ModelPrimitive`
  (the AI core), `KBPrimitive`, `ConnectorPrimitive` (Slack/Webhook/GitHub), `WorkflowPrimitive` (a saved Ask).
- **⚠️ THE PROTOCOL-DISPATCH TRAP (cost us the cassette-icon bug):** a facet that a conformer **overrides**
  MUST be a **protocol requirement**, not extension-only. Accessed through `any DeskPrimitive`, an
  extension-only member dispatches **statically to the default** and ignores the override. `glyph`/`color`/
  `base`/`isSymbol` are now requirements for exactly this reason — if you add a new varying facet, declare it
  in the `protocol`, not just the extension.

## 3. The interaction system (the current desk, in `DioStage`)

- **Content on the desk** (`contentMembers()`): meetings (cassettes), generated outputs, knowledge bases.
  Free-placed (drag), positions persisted (`hs.diorama.pos`).
- **Tools are global** (`toolMembers()`): the AI core (an installed GGUF model), the connectors, saved
  workflows. They are NOT a dock anymore — they're summoned. (`toolMembers` used to be root-gated; it's global
  now so tools exist at every zone level.)
- **THE RADIAL SUMMON (replaced the dock).** Long-press a card → the tools that **`accept`** it bloom in a fan
  around your finger (connector lines, glow, labels) → **tap one to route**. Routing: `summonTargets(for:)` →
  `beginRoute(sourceId:target:)` → model→ask sheet, connector→send card, workflow→run. No "+"/create — workflow
  **creation lives in the Workbench**, the summon only surfaces things you route TO. (`DioSummonSatellite`,
  `summonPos`, `summonSource`/`summonAt`.) NOTE: it's **tap-to-pick** today; the owner picked "flick toward
  one" — a continuous press-hold-and-slide is the next refinement.
- **Zones** = resizable, free-placed fractal **areas** you file meetings into and **dive** through
  (`ZoneRec`, `hs.diorama.zones`/`hs.diorama.filed`; breadcrumb to climb out). Empty zones teach (`DioZoneEmpty`).
- **The pull-out** (`DioPullout`): the right-edge drawer; renders any primitive's `sections` + per-section
  "Route this to AI" + **act-on-an-action-item** (an action row → the "Act on this" sheet → send to a connector
  or keep as a card).
- **The first boot** (`DioFirstBoot`): a fresh desk isn't a void — a guided spine teaches objects/AI-core/zones
  and points to record. Every empty surface orients.
- **In-desk recording** (`DioRecordingConsole`): tapping the orb starts the mic and shows a desk-native console
  — live `MicWaveform` off the real mic level, the words as heard, an On-device badge, one big stop; on stop the
  meeting weaves on-device and a cassette lands. **Tap the waveform** → the transcript **tape** (`DioTranscriptTape`,
  last 3 segments + live partial) pushes out → **Expand** → the full live transcript modal
  (`DioLiveTranscriptModal`, the whole meeting so far, scrolling, still recording).
- **Settings on the desk**: a gear (top-left at root) → `SettingsView` (where intelligence runs: This iPad vs
  LAN endpoint; the **on-device LLM model picker**; the **Whisper speech-model picker**; diarization). See §6.

## 4. Integrations are GROUNDED + HOST-GATED (do not regress this)

Connectors do NOT act from the iPad. They ride the **HoldSpeak actuator framework on the Mac**
(propose→approve→execute), and the **credential is joined in memory ON THE MAC at execute time — never on the
iPad**.

- Host (Python, `holdspeak/web/routes/meetings.py`): `POST /api/companion/{slack,webhook,github}/propose` +
  `/{id}/decision`, target-scoped. Tests: `tests/integration/test_web_companion_{slack,webhook,github}.py`
  (mirror these for a new connector).
- iPad: `DeskHostLink` reuses the Mac pairing (`hs.peer.host`/`hs.peer.port`), gates on `/health`. The send
  flow is generalized (`sendOverride`) so a single action row sends without inventing a card.
- Egress = the ONE badge (local / cloud·target), no privacy prose (POSITIONING canon).

## 5. THE BUILD / VERIFY LOOP — the Simulator works now (use it)

The handover used to say "the Simulator is broken (swift-syntax)." **That was wrong.** It was a `private`
access level on the demo entry points in `CompanionMesh.swift` (`GenTheaterDemo`/`SettingsDemo`/`AgentDeskDemo`/
`DictateDemo`/`ConnectDemo`) referenced from a `#if simulator` body — made `internal`. Now you can SEE the real
desk on-screen, which is the only reason this session's UI fixes were possible.

1. **Build for the Simulator + screenshot the REAL app:**
   ```bash
   cd apple && ruby scripts/gen-meeting-capture.rb
   xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
     -destination 'generic/platform=iOS Simulator' -derivedDataPath build/mc-sim \
     -skipMacroValidation CODE_SIGNING_ALLOWED=NO build
   DEV="iPad Air 11-inch (M4)"; APP=build/mc-sim/Build/Products/Debug-iphonesimulator/HoldSpeakMobile.app
   xcrun simctl install "$DEV" "$APP"; xcrun simctl terminate "$DEV" dev.holdspeak.mobile
   SIMCTL_CHILD_HS_DESK_SUMMON=1 xcrun simctl launch "$DEV" dev.holdspeak.mobile   # then simctl io ... screenshot
   ```
   `sips -c <h> 1668 --cropOffset <y> 0 shot.png --out crop.png` zooms a region (the dock-overlap bug was only
   visible zoomed). simctl can't tap, so I added **sim-only `#if targetEnvironment(simulator)` env hooks** to
   stage states for screenshots: `HS_DESK_SUMMON=1` (radial over a seeded output), `HS_DESK_RECORD=tape|modal`
   (recording console + transcript reveal), `HS_DESK_SETTINGS=local` (settings, forced to on-device mode). These
   are harmless in production (env-gated); remove them in a cleanup pass if you like.
2. **Device-arch compile check:** same xcodebuild with `-destination 'generic/platform=iOS' -derivedDataPath
   build/mc-verify2`.
3. **Install on device:** `./scripts/meeting-capture-device.sh` then `xcrun devicectl device process launch
   --device 6B2F424D-707F-51F7-A33E-259427861CB1 dev.holdspeak.mobile`. **Error 10002 = iPad locked** (install
   still completed). Device is **AjPed**, iPad Air M4. **Do not uninstall** — it wipes the owner's meetings DB.
4. **The diorama harness (`scripts/diorama/Diorama.swift`) is a SEPARATE implementation** and it MISLED me this
   session (its dock ≠ the app's; its shots looked fine while the app's were broken). Use it only as a fast
   visual sketchpad; verify real UI on the actual Simulator build.

## 6. Model configuration (where intelligence + transcription run)

- `InferenceConfigStore` (in `SketchDiagram.swift`, UserDefaults-backed): `mode` (`.local`/`.homelab`),
  `endpointURL`/`endpointModel`/`endpointKey`, `diarizationOn`, **`localModelId`** (which installed `.gguf`
  runs on-device intelligence; empty = first installed), **`whisperModel`** (tiny/base/small/large-v3).
- `SettingsView` (`AppSettings.swift`): target cards, the **on-device model card** (menu of
  `ModelFiles.installed()` language models + a manage/import button into `ModelsView`), the **TRANSCRIPTION**
  card (Whisper picker), diarization.
- The desk's AI core resolves `cfg.localModelId` → that model's path in `callLLM`. The capture transcriber reads
  the Whisper choice from UserDefaults **at transcribe time** (key literal `"hs.inf.whisper"` — the `@MainActor`
  static `InferenceConfigStore.whisperKey` can't cross into the Sendable `makeTranscriber` closure).

## 7. What's DONE (this session, all committed on `holdspeak-mobile/the-desk`)

- **Fixed the Simulator build** (private→internal demos) — the enabling unlock.
- **The first-boot ritual** + **empty-zone state** (every empty surface teaches).
- **Act on an action item** (action row → host-gated connector send / keep-as-card).
- **The cassette-icon bug** (protocol-dispatch) + **tools-everywhere** (un-gated `toolMembers`) + the **broken,
  ugly dock** (coordinate-space bug) — then **killed the dock for the radial summon**.
- **In-desk recording console** + the **transcript tape / full modal**.
- **Settings on the desk** + **on-device LLM model picker** + **Whisper model picker**.

## 8. The work ahead (owner-steered)

- **Flick-to-route** — make the summon a continuous press-hold-and-slide (the owner's pick; we shipped
  tap-first for robustness).
- **Per-task model routing** — let dictation, meetings, and the desk's AI core each target a different
  model/endpoint, instead of one global setting.
- **Settings as a true in-world pull-out** (not a `.sheet`), so even config feels like DeskOS.
- **The post-stop "cassette arrival" beat** — a real "ready" pulse when a new meeting lands, not just a refresh.
- **Tap a transcript segment to mark the moment** (feed the on-device intelligence weighting, like the capture
  canvas tack).
- **Cleanup**: the dead dock code is unused now (`DioDockHandle`, `DioDockTile`, `kDioDockOpenHeight`,
  `dockToolPos` except via `coreTarget`, `menuItems`/`DioMenuItem`) — prune when convenient.
- **The big track — Web Parity + the Mesh (Phase 16)**: the SAME primitive model on the web (Astro, `web/src`)
  synced across Mac + iPad on one approval + egress contract. Models never sync (manifest only).

## 9. Gotchas that will bite you

- **The protocol-dispatch trap** (§2) and **the coordinate-space trap**: overlays positioned with `.position`
  live in the GeometryReader space, but chrome anchored with `.frame(maxHeight:.infinity, alignment:.bottom)` +
  `.ignoresSafeArea` is screen-anchored — the safe-area inset shifts them apart (this both broke the dock's
  drop-hit and shoved its header onto the tiles). Draw a whole overlay in ONE coordinate space.
- **Host-gated connectors / the credential rule** — never POST to a webhook from the iPad; never put a
  credential on a proposal/broadcast/response. Mirror the companion tests.
- **PMO hook**: every commit needs a fresh `.tmp/CONTRACT.md` with all `[x]`. No `--no-verify`. Merge phases via
  a PR to `main` with merge commits when CI green. Update `current-phase-status.md` every shipping commit.
- `GGML_NO_BACKTRACE` (`holdspeak/__init__.py`) + MLX-is-thread-bound are load-bearing on the Python/meeting
  side — don't remove.
- **How to work with this owner**: he gives a big vision in voice, then reacts hard. Match the energy; own the
  gap honestly (he respects that over spin); don't narrate options you won't pursue — act. Premium/modern/
  hand-driven; flat or default components are a regression. Author PMO/roadmap content yourself (don't fan out
  subagents). Don't dwell on the device being unavailable — the Simulator build now carries most of the proof.

---

## HISTORICAL — the 3D / pre-contract era (superseded; kept for reference only)

> Everything below predates the diorama + the DeskPrimitive contract. The diorama (`DioStage`) is the front
> door now; the 3D `LivingDeskCanvas` stays unused in the tree. Read the sections above for the current truth.

---

## 0. The one thing to internalize first

The owner does not want a tech demo. He has said, repeatedly and bluntly, that incremental mechanics
("draw a wall", "physics works") are **not progress** unless they add up to a **life-like, meaningful,
gamified workspace**. The bar is: *would a senior engineer keep their real meetings here and enjoy it?*
Every time something shipped that was mechanically correct but felt like "a pre-alpha developer build,"
it was rejected. **Build coherent, meaningful leaps — not patches.** When in doubt, make it more
life-like and more *meaningful* (cards that ARE the data, actions that DO something), not more featured.

The second thing: **you cannot feel the iPad through the cable.** The Simulator build is broken
(swift-syntax `_SwiftSyntaxCShims`). So you are partially blind. The escape hatch is the **offscreen
renderer** (see §4) — use it to *see* the 3D look before every device deploy. The owner got angry
every time a blind guess shipped looking bad. Compose in the renderer first.

---

## 1. What this is

HoldSpeak's iPad app is being rebuilt from a navigation-stack app into **DeskOS** — a gamified, physics-
driven 3D workspace where everything (meetings, their outputs, models, knowledge bases) is a manipulable
**object** on a desk. There are two desks:

- **2D desk** (default): `DeskPhysicsCanvas.swift` — a flat SpriteKit physics canvas. Shipping default.
- **3D Living Desk** (opt-in, the future): `LivingDeskCanvas.swift` — a SceneKit fixed-angle room.
  Toggle in the toolbar: the **cube pill ("2D"/"3D")**, persisted in `@AppStorage("hs.desk.living")`.

The shell that hosts both is `DeskHome.swift`.

## 2. How to run it (the loop)

```bash
cd apple
ruby scripts/gen-meeting-capture.rb            # stages App/MeetingCapture/** -> an .xcodeproj
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -destination 'generic/platform=iOS' -derivedDataPath build/mc-verify2 \
  -skipMacroValidation CODE_SIGNING_ALLOWED=NO build      # device-arch compile check (~2-3 min)
./scripts/meeting-capture-device.sh            # build + sign + install on the cabled iPad (AjPed)
xcrun devicectl device process launch --device 6B2F424D-707F-51F7-A33E-259427861CB1 dev.holdspeak.mobile
```

- The device is **AjPed**, an iPad Air M4, id `6B2F424D-707F-51F7-A33E-259427861CB1`, bundle
  `dev.holdspeak.mobile`.
- **Error 10002 on launch = the iPad is locked.** The *install* completes before the launch step, so the
  build IS on the device; ask the owner to unlock + tap, or relaunch with devicectl once unlocked.
- The Simulator is broken — do not rely on it.

## 3. State of the DeskOS (what works, with pointers)

**2D desk (`DeskPhysicsCanvas.swift`, shipping):** premium textured cards, lasso → bundle → file,
meeting **spill** (tap a meeting -> its Summary/Topics/Actions/Artifacts/Transcript burst out as objects),
floating app **windows**, the **Knowledge Base** crystal primitive, directories. All real, all device-proven
earlier. This is the mature surface.

**3D Living Desk (`LivingDeskCanvas.swift`, opt-in):**
- Fixed ~60-80° SceneKit camera, **pulled back** on the whole workspace by default.
- A large marble desk + a leather **desk mat** + **invisible perimeter walls** (nothing falls off).
- Real **poly.pizza CC0 props** bundled as `.scn` (lamp, plant, keyboard, books, mug).
- **Paper cards**: card-stock texture (`App/paper.png`), a die-cut **sticker** (the pixel asset) at a
  rugged angle, ink type, accent spine, tape. 4 styles (cream/kraft/blueprint/sticky), **long-press a
  card to cycle its style** (`hs.desk.cardstyles`).
- **Physics + haptics**: pick a card up (it lifts), **fling it** (it slides/spins/settles with weight),
  landing **clack** haptic. Forward-shadow lighting so cards/props/fences cast real shadows.
- **The zoned DEFAULT desk**: on the All view, meetings auto-organize into **Today / This Week / This
  Month / Earlier** — each a **fenced, labeled region** with its cards inside (`zonedLayout`).
- **The Zones toolchain**: toolbar **Zones** pill -> a **brush palette** (Area / Crayon / Pencil / Mud).
  - **Area** brush: drag a rectangle -> it fills with a **child's-crayon scribble** in a colour ->
    prompts to **name** it (a flat named zone marker).
  - **Crayon/Pencil/Mud**: draw a freehand **wall**; **dwell in place to build it taller**; real physics
    barrier that casts shadows.

## 4. The offscreen renderer — your eyes (USE THIS)

`apple/scripts/experience/living-desk-render.swift` is a **macOS SceneKit offscreen renderer** that draws
the same Living Desk scene to a PNG so you can SEE the look without a device/Simulator:

```bash
cd apple/scripts/experience
swiftc -O living-desk-render.swift -o /tmp/ldr -framework SceneKit -framework AppKit -framework Metal
/tmp/ldr /tmp/living-desk.png        # then Read /tmp/living-desk.png
```

It keeps the app's scene composition in sync (camera, lights, props, cards, mat). **Tune the look here
first, then port the values into `LivingDeskCanvas.buildScene`.** Caveat: the offscreen snapshot path
has no tone-mapping, so it renders **darker/warmer** than the device — judge composition + shadows +
shapes here, judge final brightness on device. (This is why the renderer uses `.forward` shadows; the
app was switched to match.)

## 5. The asset pipeline (poly.pizza -> SceneKit)

poly.pizza is the CC0 3D-prop source (owner's call). Pipeline, all proven:
```bash
curl -sL "https://poly.pizza/m/<id>" | grep -oE "https://static.poly.pizza/[a-f0-9-]+\.glb"   # find GLB
curl -sL "<glb-url>" -o prop.glb
uv run --with trimesh --with pillow python3 -c "import trimesh; trimesh.load('prop.glb', force='mesh').export('prop/prop.obj')"
xcrun scntool --convert prop/prop.obj --output App/prop.scn --format scn   # mkdir the output dir first!
cp prop/material_0.png App/prop_tex.png                                     # the palette atlas
```
Then add `prop.scn` + `prop_tex.png` to the resource list in `scripts/gen-meeting-capture.rb` (line ~61),
load via `Bundle.main.url(forResource:withExtension:"scn")`, re-apply the texture in code
(`UIImage(named:"prop_tex")`), and record provenance in `apple/scripts/experience/assets/CREDITS.md`.
**Gotchas:** prop native sizes vary wildly (some bbox is 500+ units) -> use **explicit per-prop scales**,
not auto-fit. `flattenedClone().boundingBox` is degenerate before render -> read the geometry boundingBox.
`.gitignore` has a broad `models/` rule -> `git add -f` for vendored CC0 assets under `App/` (they're tiny).

## 6. Known issues / rough edges (be honest with the owner)

- The 3D look is **stylized, not photoreal** — getting truly "life-like" is an ongoing art lift.
- `zonedLayout` re-lays-out on any change to the zone signature (incl. a style change), which resets
  card positions. Acceptable for the organized default but jarring on restyle; consider incremental.
- Zone **choreography** (bounds/spacing relative to props) is naive (a row of fixed slots). Owner wants
  smarter placement.
- New props scale unpredictably (a giant coffee cup happened) — tune each by eye in the renderer.
- Card face texture orientation in the *renderer stand-in* is mirrored; the *app* uses the real
  `DeskCardFace` SwiftUI view, which is correct.

## 7. The exact next steps (owner-prioritized, in order)

These are the owner's explicit, repeated asks — the road to "meaningful":

1. ~~**Drop-to-tag (the cluster-zone primitive).**~~ **DONE 2026-06-24.** A drawn+named area is now a
   persisted `DeskZone` (footprint in `hs.desk.zones`) AND a real directory (reuses the filing map →
   shows in the sidebar). Dropping a card inside a zone's footprint files it (`onFileToZone` →
   `fileToZone`); the card settles (no fling-out), haptic + zone pulse + live count placard. Drawing the
   first zone retires the auto time-fences. **Gotcha for the next agent:** a flat zone decal at a fixed
   height only works for ONE surface level — the crayon fill is at y=0.53 to sit above the leather mat
   (top 0.5); a zone drawn over bare desk (no mat) will float slightly, and a card filed onto bare desk
   could sit below the decal. The renderer (`living-desk-render.swift`, now draws a sample zone) caught
   this before device. *This was the prerequisite for everything below.*
2. ~~**Dive into a zone ([[story-24-nested-zones]]).**~~ **BUILT 2026-06-24** (live dive-feel walk pending
   an unlock). Double-tap a zone -> `diveInto` rushes the camera in + zooms -> `onDive` swaps the desk to
   that zone's contents; double-tap the empty desk climbs out; `DeskBreadcrumb` jumps to any level.
   **Recursion is real:** zones are now **path-based** (`DeskZone.name` = `Atlas/Q3`); `addZone` prefixes
   `currentPath`, `deskZones` is level-scoped (children of the current path), `cardData` shows the current
   level's members. `syncLevel` plays the directional camera settle on any depth change. **Next-agent
   notes:** the dive→settle handoff has a tiny camera discontinuity (diveInto ends on the zone center;
   syncLevel snaps to a fixed pose then eases home) — tune on device. Per-level card LAYOUT positions
   aren't persisted yet (cards re-grid each entry). Tune the dive timing/drama on the glass.
> **FOUNDATION PIVOT — 2.5D DIORAMA (2026-06-24, owner: "rethink the approach; it looks alpha").** The
> hand-rolled real-time 3D (procedural geometry + a dark blind renderer) was the alpha smell. New direction:
> a premium **art-directed 2.5D diorama** in SwiftUI using the bespoke **PixelLab** objects, **verified at
> full fidelity in the iOS Simulator**. Harness: `scripts/diorama/Diorama.swift` (self-contained, `@main`)
> + `scripts/diorama-shot.sh` (`DIO_DEVICE` iPad Air; sources sprites from `scripts/experience/assets/`;
> screenshot needs an ABSOLUTE path; the sim renders portrait — design for it, or rotate via osascript key
> code 124/123). First shot: `screenshots/desk-diorama-v1.png`. **THE LOOP TO USE NOW:** edit Diorama.swift
> → `./scripts/diorama-shot.sh /tmp/x.png` → Read it → iterate. Build the whole experience (objects, zones,
> dive, focus lens) up to this bar here FIRST, then port into the app. The 3D `LivingDeskCanvas` stays
> untouched until the diorama is genuinely better. (The old offscreen SceneKit renderer + 3D notes below
> are superseded for look work — keep them only as 3D reference.)

> **FRACTAL ZONES + DIVE — IN THE DIORAMA (2026-06-24).** The diorama (`DioStage` + harness
> `scripts/diorama/Diorama.swift`) now has **places**: premium recessed **zone trays** that hold meetings,
> a **+ New Zone** create tile, **drag-a-meeting-onto-a-tray to file** (drop-to-tag, "hot" highlight), and
> **tap-to-DIVE** (asymmetric scale-through + accent whoosh + breadcrumb). **Recursive + path-based**
> (`hs.diorama.zones` = "path|colorIdx", `hs.diorama.filed` = "objId=zonePath"); models/KBs stay at root.
> Breadcrumb climbs out; tap-empty climbs a level; the glow retints per zone. Proven in the Simulator
> harness (portrait now — the landscape Info.plist letterboxed it) by screenshot + recorded video, then
> installed on the iPad. **The dive FEEL on glass is the one acceptance left** (a static frame can't carry
> it). Tune `diveSpring`/whoosh on device. This is §7 #1 + #2 in the diorama; next: act-on-expand (§7 #3)
> + the Ask-AI atom (§7 #7), and zone choreography (#6) for many trays.
>
> **FOCUS LENS (2026-06-24, owner's vision for "expand"):** tapping a meeting in 3D no longer spills cards
> into the physics desk — it **lifts the object toward the camera** (`LivingDeskCanvas.liftToFocus`:
> kinematic + collisionBitMask 0 so it's non-solid, transform saved in `focusSaved`, animated up+scaled;
> `dropFromFocus` clips it back on exit), fogs the world under a **lens** and floats its outputs in a
> **virtual layer** (`DeskFocusOverlay` in DeskHome — radial clear→dark fog, output `DeskCardFace`s fanned
> in the air, tap-anywhere to close). State: `focusedId`/`focusOutputs`. **NEEDS DEVICE TUNING:** the lift
> target `(0,16,15)`/scale `1.5` and the fog clear-centre radius are reasoned, not eyeballed on glass yet.
>
> **REAL ASSETS — tried + parked.** Pulled CC0 poly.pizza models for the objects (cassette `/m/aR5ot8Z7_-v`
> Google, microchip `/m/tIp60lIg43` iPoly3D, crystal `/m/nBlnK8G6xw` Quaternius, book `/m/h3Wh4fxSQX`
> Quaternius) via the §5 pipeline + a `loadFit` auto-fit in the renderer. They imported **untextured**
> (tiny palette-UV PNGs → white) and read WORSE than the procedural objects, so they're parked. To finish:
> either bake proper textures, apply a clean per-kind solid tint to the real mesh, or commission Pixellab.
> The procedural `makeObject` builders stay until a real curation pass beats them.

> **OBJECT LANGUAGE (2026-06-24, owner's core ask — "stop making everything a wooden chip"):** hardware /
> containers are now REAL 3D objects in `LivingDeskCanvas`, not paper extrusions: **meeting → cassette**,
> **model → glowing cartridge** (emissive accent bar + gold pins), **kb → crystal**, **notebook → book**
> (`makeObject` dispatches by `DeskCardKind`; each keeps a box physics body). Only documents
> (summary/topics/action/transcript/artifact) stay paper. Sculpt new objects in the renderer's object
> builders FIRST. **Next on this thread:** give the paper docs real form too (transcript = scroll, action =
> sticky, summary = stacked sheets) + the act-on-expand affordance. Also: the **dive** is now **single-tap**
> a zone (a device walk found `cardNode` was eating the tap); double-tap still works.

3. **Cards with real MEANING.** ~~Snippet on the face~~ **DONE 2026-06-24** + the owner's card-craft pass:
   every card shows a real content **snippet** (`snippetFor` / output body preview), a `DeskCardKind` drives
   **type-legible** TYPE badges + **different shapes/sizes** (`renderSize`/`corner` per kind — summary big,
   transcript tall, action a slip) + a **loose sticker** (varied rotation/scale/shape/nudge). STILL OPEN
   on this item: **expand should surface real artifacts you ACT on** (file / Ask AI / run) — right now a
   tap still just spills/opens; the act-on-expand affordance (and the Ask-AI atom, #7) is the next push.
4. **Ready-made resizable rectangle fences** you drop, then **resize + raise** (drag handles) — fast
   clean enclosures, vs only freehand.
5. **By Project zones** (group by the meeting project tag) + **scroll inside a zone** when it overflows.
6. **Zone choreography** — smarter auto-zone bounds/positioning around the props.
7. **The Ask-AI atom ([[story-09-the-ask-ai-atom]])** — lasso context -> "Ask AI" -> speak a prompt -> a
   card prints out -> keep/bin. The highest-value *function*; on-device, needs no mesh.
8. Then the cross-surface arc: **Desk Environments** (Marble/Walnut/Carbon + builder,
   [[story-21-desk-environments]]), the **web Astro Desk** + **mesh sync** (Phase 16,
   [[DESK_BUILD_SEQUENCE]]).

## 8. The design canon (source of truth — read before building)

- [[story-19-the-desk]] — the DeskOS vision + pillars.
- [[story-20-the-desk-object-model]] — **the convention**: every primitive is one DeskObject filling the
  same facets; gestures (tap=open, long-press=reshape, drag=fling, lasso=select, file=classify,
  drop-on=combine, keep/bin=judge). Add a kind by declaring it.
- [[story-21-desk-environments]] — themeable environments + poly.pizza assets pipeline.
- [[story-22-the-living-desk]] — the 3D SceneKit substrate decision + buildable barriers.
- [[story-23-the-deskos-shell]] — the shell anatomy (organizer / toolbar / drawers / desk / floating).
- [[story-24-nested-zones]] — the fractal dive-into-a-zone idea.
- [[story-25-the-desk-interaction-system]] — **the coherence layer (owner-driven 2026-06-24): the
  `DeskPrimitive` contract (everything declares kind/title/preview/sections/actions/emits/accepts → ALL UI is
  derived, one renderer per surface), the gesture library, the intelligence engine (drag any output onto the
  AI core → LLM → new primitive), and integrations (drop onto a connector → propose→approve→execute). The
  diorama (`DioStage` + `DeskPrimitive.swift`) is now primitive-driven. NEXT BUILD: the keystone routing
  gesture on real metal.**
- [[DESK_BUILD_SEQUENCE]] — the dependency-ordered build order (substrate -> surface -> sync).
- Phase 16 (`../phase-16-the-desk-everywhere/`) — web parity + mesh sync; the state taxonomy
  (content / organization / **capability** / layout); the Ask atom; capability objects. **Models never
  sync (too large) — manifest only** (owner-confirmed).

## 9. Repo-wide gotchas that will bite you

- **PMO pre-commit hook**: every commit needs a fresh `.tmp/CONTRACT.md` with 7 `[x]` boxes (see
  `pm/roadmap/PMO-CONTRACT.md`). No `--no-verify`.
- The 3D desk is **opt-in** behind the cube toggle so it can't destabilize the shipping 2D desk. Keep it
  that way until it's genuinely better.
- `GGML_NO_BACKTRACE` in `holdspeak/__init__.py` and MLX-is-thread-bound (pin MLX work to one executor)
  are load-bearing on the Python/meeting side — don't remove (see prior memories).
- The owner uses real voice feedback and tests on the **actual cabled iPad** — "done" means walked on
  the device, not a seeded Simulator shot.

## 10. How to work with this owner (the meta-lesson)

- He will give you a big vision in voice, then react hard to what you ship. Match his energy; don't get
  defensive; **own the gap honestly** when something's not good enough — he respects that more than spin.
- **Compose the look in the renderer, deploy coherent leaps, and be honest about what's still half.**
  He explicitly hates being handed "tech demos" framed as near-done.
- He gets genuinely excited by the *right* ideas (the fractal nested zones) — lean into the vision, make
  the default experience a *powerhouse*, make objects *mean* something.

Good luck. The substrate is real and the canon is solid — the work now is **meaning and depth**, not
more mechanics. Build #1 (drop-to-tag) and #2 (dive) and it starts to become the thing he can see.
