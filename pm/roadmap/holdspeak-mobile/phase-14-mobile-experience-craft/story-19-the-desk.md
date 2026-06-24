# HSM-14-19 — The Desk: the shell as a physics-driven, gamified, generative workspace

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-23. The owner's decisive direction after the base shell was
  judged "a poor excuse… loser frames." The whole app becomes **The Desk** — and this is canon for both
  the iPad (SwiftUI) and the web (Astro) surfaces.
- **Depends on:** the Signal/`DS` design system, the Workbench (HSM-14-15/16), the live capture canvas
  (HSM-14-11), the meeting/model/workflow data already in the app. PixelLab MCP for bespoke assets.
- **Owner:** unassigned

## The vision (owner, distilled)

> Not screens — a **Desk**. A dynamic, physics-driven surface where everything is a manipulable object
> scattered in space; gamified for joy, yet a rich **organizational OS** that's a pleasure to use
> effectively. Playful when you want; ruthless and fast when you're working.

The app is a tactile dark **workspace**, not a navigation stack. You don't browse lists — you handle
**objects** and **play around the landscape to get immediate outcomes**.

## The pillars

1. **Physics objects, not frames.** Every primitive is a real object with weight, thickness, material,
   light — dragged with momentum, lifted on grab, settling with a spring, snapping to the desk. Bespoke
   **PixelLab pixel-art** objects, NOT styled rectangles: a **meeting is a cassette tape** you play, the
   **model is a game cartridge** you slot in, the **recorder is a desk mic**, directories are **folders**,
   intelligence blocks are **crystals**, outputs are **sticky notes**.

2. **A real organizational OS — directories.** A Finder-style file tree (Smart folders / Projects with
   nesting / Library), a breadcrumb path, a spotlight command bar (⌘K), and folders that are *also*
   objects on the canvas you file into. **Tidy** is the hinge: one gesture snaps the scatter into an
   aligned grid; pull apart to play.

3. **Inputs come from DRAWERS.** Each canvas has set areas — a **Models drawer**, a **Recordings drawer**,
   a **Blocks drawer** — recessed trays where the standard pieces lie around. You **pull a piece onto the
   landscape**, wire it, and get an outcome. The drawers are the input library; the canvas is the bench.

4. **Live sources + the lasso.** In a live meeting the source isn't a static cassette — it's a **flowing
   transcript stream**: paragraph slips drift up as people talk. You **lasso** a few (a playful loop
   gesture), they cluster into a selection, and an **action ring** lets you do anything with exactly those
   lines: **Extract** (intelligence on just that thread), **Tack** (mark the MIR moment — the model weights
   it), **Note**, **Ask**. The lassoed group becomes an input object like any other.

5. **Immediate outcomes.** Drop a cassette (meeting) + a cartridge (model) onto the Workflow machine → it
   runs → a result note blooms out. Play *is* productivity, the same gesture. The Workbench token travels
   the wire so you watch your program think.

6. **One system, two surfaces.** iPad (SwiftUI) and web (Astro) share the metaphor, the directory OS, the
   drawers, the lasso, the physics — proven in parity.

## Prototypes shipped (Simulator / Chromium, direction-locking)

Built as compiled SwiftUI in the iOS Simulator harness (`apple/scripts/experience/`,
`experience-shot.sh`) and as a real HTML/CSS/JS page in headless Chromium — each a real build, not a
mockup:

- **Desk v1–v2** — the physics canvas + the OS spine (spotlight, zone rail, Today stack, dock, Tidy).
- **iPad v3** — the directory system (Finder tree, breadcrumb, folders as objects).
- **Web twin** — the browser-native equivalent (same tree, breadcrumb, physics objects, dock).
- **v5** — bespoke **PixelLab** primitives (cassette meetings, AI-CORE cartridge, desk mic, folder).
- **v6** — the **drawers** (Models/Recordings/Blocks) + a wired workflow → a "3 Decisions" outcome.
- **v7** — the **live lasso**: transcript slips flowing up, a lasso grouping 3 lines, the action ring.

Bespoke assets live in `apple/scripts/experience/assets/` (cassette, cassette2, cartridge, mic, folder;
+ crystal, sticky-note, robot in flight). The harness bundles them; `Sprite`/`SpriteObject` load them
crisp.

## The Desk is an OS — architecture (and the decomposition vehicle)

The Desk is not a screen; it is a **native desktop environment** — a shell/OS — and the rest of the app
are **apps** that open on it. This reframes the whole structure, FOR THE BETTER, and gives us the
decomposition we already badly need.

**The monster:** `apple/App/MeetingCaptureApp.swift` is **~7,500 lines** — home + capture + detail +
intel review + generation theater + the Workbench + settings + the model manager + diarize wiring, all
in one file. The Desk rebuild is the decomposition: carve it into an OS shell + apps + shared primitives
(the Phase-54 frontend / Phase-63 backend decomposition pattern, applied here).

```
DeskOS/            the shell: desk surface, directory OS, drawers, the app/window manager, Fun Mode
Apps/
  MeetingApp/      capture → live lasso → detail → intel review → generation theater
  WorkbenchApp/    the visual workflow builder — an APP-WITHIN-THE-APP (the exec-graph IDE on the desk)
  ModelsApp/       the model manager (cartridges)
  SettingsApp/     settings
Primitives/        Sprite objects, DeskObject physics, the bespoke PixelLab assets
DesignSystem/      DS tokens, motion, haptics
ViewModels/        MeetingReviewState, CaptureModel, … (lifted out of the view file)
```

- **Apps open on the Desk** as objects/windows/full-screens; the OS owns navigation, the directory
  tree, drawers, search, Tidy, and Fun Mode. Apps own their own surface.
- **The Workbench is the flagship app-within-the-app** — its node-graph IDE (HSM-14-15/16) is launched
  on the desk, not buried in a tab.
- **Fun Mode (CoreMotion):** `CMMotionManager` attitude/acceleration → forces on the same `DeskObject`
  physics. Tilt → objects slide; **shake → everything scatters** (impulse), with haptics. A settings
  toggle, reduce-motion-aware, device-only. The play layer made physical. (Yes — doable, lol.)

## Build plan — converging to the real shell

1. **Lock the canon** (this doc) + the asset set. *(this slice)*
2. **Real iPad shell** — replace the `MeetingCaptureApp` home with the Desk; objects wired to real
   meetings, the loaded GGUF (the cartridge), real workflows; the directory tree over real projects/tags;
   device-proven on the Air M4.
3. **The drawers + drag-to-run** — pull a model/recording/block from a drawer onto the canvas; drop a
   meeting on the Workflow → real `generate()` runs; the result note is a real `Artifact`.
4. **The live lasso** — over the real live transcript (the HSM-14-12 stream): lasso → point-in-polygon
   hit-test the slips → the action ring routes the selection (Extract → routed `generate`; Tack →
   `markMoment`/MIR; Note; Ask).
5. **The web Desk** — build it into `web/src` (Astro) against the real `/api/meetings` etc., same metaphor.
6. **Motion + polish** — slips drifting, the lasso trail, the token down the wire, the Tidy morph,
   haptics; accessibility + reduce-motion.

## Acceptance criteria
- [x] The Desk direction is locked as canon (this doc) with prototypes on both surfaces. *(this slice)*
- [ ] The real iPad shell replaces the home, wired to real data, device-proven.
- [ ] Drawers + drag-to-run produce a real artifact on a real meeting.
- [ ] The live lasso groups real transcript lines and routes the selection (Extract/Tack/Note/Ask).
- [ ] The web Desk reaches parity in `web/src`.
- [ ] Motion + a11y polish pass.

## Notes
- **The object convention is canon in [[story-20-the-desk-object-model]]** — every primitive (meeting,
  output, model, directory, knowledge base, …) is one **DeskObject** filling in the same facets; add a
  kind by declaring it, not by coding it. Knowledge Base is the first primitive built *on* that convention.
- **The desk is a *place* — [[story-21-desk-environments]]** is canon for themeable environments (a lamp
  on a marble table, a mousepad, real light) with **3 shipped environments + a builder**, from free CC0
  assets. Pixel-art objects on rich material surfaces under real light is the signature look.
- Craft bar: bespoke objects over SF glyphs/CSS shapes (lean on PixelLab — [[project_qlippy_mascot]]).
- The contrast — pixel-art **objects** on **sleek** dark chrome — is the premium feel; keep both.
- Prove on the device, not seeded shots, for anything claimed `done` (see
  [[feedback_verify_on_device_not_seeded]]); the Simulator harness is for direction, the app is the proof.
