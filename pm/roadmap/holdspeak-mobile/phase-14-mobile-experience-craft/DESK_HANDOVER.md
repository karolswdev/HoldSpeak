# The Desk — handover for the next agent

> Written 2026-06-24 at the end of a long build session. Read this top-to-bottom before touching code.
> The branch is `holdspeak-mobile/the-desk`; **PR #133** is open to `main` (33 commits, not merged).
> Everything is committed + pushed. The owner asked for a fresh mind — this is the running start.

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
