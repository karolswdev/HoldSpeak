# The Desk (DeskOS) — handover for the next agent

> Rewritten 2026-06-25 after **PR #133 merged to `main`** (the whole DeskPrimitive era — 70+ commits). This
> top section is the CURRENT source of truth; the 3D / pre-contract notes further down are HISTORICAL (the
> diorama + contract superseded them). Companion docs: [[THE_DESK_WHOLE_PICTURE]] (the holistic map + its
> rendered `the-desk-map.png`) and [[story-25-the-desk-interaction-system]] (the contract detail). The
> running log is `current-phase-status.md` "Where we are".

## 0. The 60-second orientation

DeskOS is the iPad app reimagined as a spatial, gamified **command center**: meetings, their intelligence,
the AI, your knowledge, and your integrations are all **manipulable objects on one desk**. The iPad is a
**companion to the Mac** (the host). The shipping front door is the **2.5D motion-first diorama**
(`apple/App/MeetingCapture/DeskDioramaStage.swift` = `DioStage`), NOT the old 3D `LivingDeskCanvas` (which
stays unused in the tree behind `HS_REAL_DESK=1`).

Owner's bar (unchanged): coherent, meaningful, **delightful** leaps — not tech-demo mechanics. Premium =
"I'm delighted when I use it," and delight is felt in MOTION. Prove feel with Simulator video/screenshots,
then on the device.

## 1. The spine — everything is a DeskPrimitive (read this first)

`apple/App/MeetingCapture/DeskPrimitive.swift`. EVERY concept declares the same facets and the **entire UI is
derived** from that declaration — the canvas object, the card, the pull-out, the menu, the routing. Add a
concept = declare one primitive; its whole UI appears for free.

- Facets: `kind` (→ glyph + colour; `isSymbol` = an SF-symbol tool, not a pixel sprite), `title`/`subtitle`/
  `preview`, `sections` (the pull-out body — text/actions/chips/transcript, ONE renderer), `actions`,
  **`emits`**, **`accepts`**, `routableText` (the LLM input, derived generically from sections).
- Conformers: `MeetingPrimitive`, `OutputPrimitive` (a generated card — itself routable), `ModelPrimitive`
  (the AI core), `KBPrimitive`, `ConnectorPrimitive` (Slack/Webhook/GitHub), `WorkflowPrimitive` (a saved Ask).
- Routing is generic: a drop is allowed iff `target.accepts ∋ source.kind`; `beginRoute` switches on
  `target.kind` (model → ask the LLM, connector → send, workflow → run the saved prompt).

**DO NOT add bespoke per-type screens.** If you're tempted, you're fighting the contract — declare a primitive.

## 2. The anatomy of DioStage (where things live)

- **Content on the desk** (`contentMembers()`): meetings, outputs, knowledge bases. Free-placed (drag),
  positions persisted (`hs.diorama.pos`).
- **Tools in the dock** (`toolMembers()`): the AI core, connectors, saved workflows — a swipe-out **bottom
  Tool Dock** in the thumb zone (`DioDockChrome`/`DioDockTile`). A content drag auto-opens it; drop a card on
  a tool to route/send (`dockHit` / `dockToolPos`); tap a tool → its pull-out. (Built because the owner said
  the tooling wasn't reachable in the lower screen + wanted a docked chooser.)
- **Zones** = resizable, free-placed 2D **areas** (`ZoneRec`: path/color/cx/cy/w/h; drag to arrange, corner
  grip to resize, tap to dive — fractal/recursive, path-based; `hs.diorama.zones`). Drop a meeting in one to
  file it (`hs.diorama.filed`).
- **The pull-out** (`DioPullout`): the right-edge drawer; renders any primitive's `sections` + a per-section
  "Route this to AI" (act-on-section) + `actions`.
- **The intelligence engine:** drag / lasso / long-press → the route sheet (pick a lens or prompt; "Save as a
  reusable tool" → a `WorkflowPrimitive`) → the real `ILLMProvider` (on-device GGUF or an endpoint, via
  `InferenceConfigStore.makeProvider`) → the **visible cable** (`RouteArc`, a token travels the wire) → a new
  `OutputPrimitive` prints → keep/bin (`hs.diorama.outputs`).
- **Three ways to route:** drag onto a target, **lasso** a bundle (the Ask-AI atom), **long-press** a menu.

## 3. Integrations are GROUNDED + HOST-GATED (do not regress this)

The owner was emphatic: connectors do NOT act from the iPad. They ride the **HoldSpeak actuator framework on
the Mac** (propose→approve→execute, permission manifest, guarded executor), and the **credential is joined in
memory ON THE MAC at execute time — never on the iPad, never on a proposal/broadcast/response**.

- Host (Python, `holdspeak/web/routes/meetings.py`): `POST /api/companion/{slack,webhook,github}/propose` +
  `/{id}/decision`, **target-scoped so they can't cross**; reuse `build_slack_connector` /
  `build_url_webhook_connector` / `build_github_issue_connector` + `ActuatorExecutor`. Config:
  `slack_webhook_url` / `companion_webhook_url` / `companion_github_repo`. Status: `/api/companion/status` →
  `connectors.{slack,webhook,github}_configured` (no URL leaks). A sentinel `companion` meeting satisfies the
  proposals FK (excluded from `list_meetings`). Tests:
  `tests/integration/test_web_companion_{slack,webhook,github}.py` (30 — MIRROR these for the next connector).
- iPad: `DeskHostLink` (in DioStage) reuses the desk's Mac pairing (`hs.peer.host`/`hs.peer.port`), gates on
  `/health` reachability, and propose→decide by `target`. **A new connector = one `ConnectorPrimitive` + one
  thin host endpoint pair + its tests.**
- Egress = the ONE badge (local / cloud·target), no privacy prose (POSITIONING canon).

## 4. The build / verify loop (USE THIS)

1. **Compose the FEEL in the harness first** (the Simulator works for it; the full app's Simulator build does
   not). `apple/scripts/diorama/Diorama.swift` mirrors DioStage's look; `./scripts/diorama-shot.sh /tmp/x.png`
   builds + screenshots in **PORTRAIT**. Deterministic env hooks (via `SIMCTL_CHILD_*`): `DIO_SELECT`,
   `DIO_PATH`, `DIO_ROUTE_STAGE` (sheet/theater/wire/send/printed), `DIO_LASSO=1`, `DIO_DOCK=open`. Record
   motion with `simctl io recordVideo` — delight is felt in motion.
2. **Port to DioStage + device-arch compile-check:** `cd apple && ruby scripts/gen-meeting-capture.rb &&
   xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile -destination
   'generic/platform=iOS' -derivedDataPath build/mc-verify2 -skipMacroValidation CODE_SIGNING_ALLOWED=NO build`.
3. **Install on device:** `./scripts/meeting-capture-device.sh` then `xcrun devicectl device process launch
   --device 6B2F424D-707F-51F7-A33E-259427861CB1 dev.holdspeak.mobile`. Error 10002 = iPad locked (the install
   still completed). The owner walks it on the cabled iPad Air M4 (AjPed).
4. **Host side:** `uv run pytest -q ...` — the companion-connector tests are the pattern.

## 5. What's DONE (all on `main` via PR #133)

The DeskPrimitive contract; fractal + resizable zones with the dive; the right-edge pull-out; the keystone LLM
routing + the visible cable; the Ask-AI atom (lasso) + long-press menu + act-on-section; three host-grounded
connectors (Slack/Webhook/GitHub, 30 tests); workflows as primitives; the swipe-out tool dock. The earlier 3D
era (LivingDeskCanvas, paper cards, fences) is in the tree but superseded by the diorama.

## 6. The path forward (owner: "momentum on DeskOS, then Web Parity")

**A) Finish + polish DeskOS (near-term).**
- **Walk it on the device and tune the feel** — the dock auto-open timing, the zone resize clamps + overlap,
  the cable, the record-orb position while the dock is open. (The device was unavailable at the end of the
  last session, so the dock / resizable zones / connectors are arch-verified + harness-proven but **not yet
  hand-walked** — that's the first thing to do.)
- **The real-metal proof the owner prizes:** a real on-device LLM route (drag a meeting → AI core → a card
  prints) AND a live Slack/GitHub send via the Mac. Control-vs-treatment, not a no-LLM plumbing pass.
- Smaller: the desk's empty/first-run state; surfacing per-connector config; "act on an action item" (an
  action row → send/file); retiring the old 3D `LivingDeskCanvas` so the diorama is the only desk.

**B) WEB PARITY + the Mesh (Phase 16, the next big track) — `../phase-16-the-desk-everywhere/`.**
- Goal: the SAME desk on the **web (Astro, `web/src`)** and synced across Mac + iPad, on **one approval +
  egress contract**. Build it on the SAME primitive model — the web desk and the iPad desk must be ONE model,
  not two builds. The Mac already owns the actuators + the companion API + the web frontend, so the web desk
  is a new surface over the same engine, **not a reimplementation**.
- The mesh seam exists: `HTTPDesktopClient` + `/api/companion/*`; `holdspeak/mesh.py` + `/api/mesh/*` (Phase
  15 LAN discovery). Models never sync (manifest only — owner-confirmed). Any web→world action reuses the
  grounded actuator path.

## 7. Gotchas that will bite you

- **The contract is load-bearing** — routing, the pull-out, the dock, all derive from DeskPrimitive. Change a
  facet, not a screen.
- **Host-gated connectors / the credential rule** — never POST to a webhook from the iPad; never put a
  credential on a proposal/broadcast/response. Mirror the 30 companion tests.
- **The harness renders PORTRAIT** (a landscape Info.plist was letterboxing it). Compose for portrait; the
  device adapts via GeometryReader fractions.
- **CI lessons from merging #133:** the Phase-15 mesh tests need `pytest.importorskip("zeroconf")` (zeroconf
  is a `[meeting]` extra; the Unit Tests job is base-install). Any web change that renames a dashboard helper
  must update `tests/integration/test_web_server.py` (HS-69-01 swapped `egressLabel()` → the structured
  `egress-badge`). The web bundle `holdspeak/static/_built/` is **gitignored** — CI builds it; `cd web && npm
  run build` to verify locally.
- **PMO hook:** every commit needs a fresh `.tmp/CONTRACT.md` with 7 `[x]`. No `--no-verify`. Merge phases via
  a PR to `main` with **merge commits** when CI is green.
- `GGML_NO_BACKTRACE` (`holdspeak/__init__.py`) + MLX-is-thread-bound are load-bearing on the Python/meeting
  side — don't remove.

## 8. How to work with this owner (the meta-lessons)

- He gives a big vision in voice, then reacts hard. Match the energy; **own the gap honestly** when something
  isn't good enough (he respects that more than spin). Don't narrate options you won't pursue — act.
- **Build coherent, meaningful, DELIGHTFUL leaps.** Prove feel in MOTION (Simulator video), then on the metal.
- **Declutter + reachability matter** (the tool dock came straight from "the tooling isn't in the lower part
  of my screen"). Premium, modern, hand-driven; flat/default components are a regression.
- He wants the HOLISTIC picture, not just a feature stream — keep `THE_DESK_WHOLE_PICTURE.md` true.
- When you finish a chunk: screenshot/video proof → update `current-phase-status.md` → commit (fresh contract).
  Don't fan out subagents for PMO/roadmap writing — author it yourself. Don't dwell on the device being
  unavailable — keep building and arch-verify.

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
