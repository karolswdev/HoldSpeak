# Phase 14 — Mobile Experience & Craft

**Status:** in-progress (opened 2026-06-21 in direct response to the owner: usability,
design, and modern hand-driven mobile practice were never in the roadmap, and the app
shipped as a bare functional shell, not a crafted product. This phase makes the
**experience** first-class.)

**Last updated:** 2026-06-24 (**the diorama gets fractal zones + the dive** — see the latest "Where we are"
entry; the 2.5D front door now has recursive places you file meetings into and dive through, on the iPad).

**(Historical) 2026-06-21 (**opened + first craft delivered.** The owner chose the
**Tactile Sheets** design direction from three concrete mockups (gesture-first: swipeable
cards, draggable action sheet, big targets, haptic-forward). HSM-14-01 in progress: a native
`DS` design system (color/spacing/radii/elevation tokens + reusable swipeable-card / action-
sheet / chip components, `haptic()` wired) built and **proven on the hero meeting +
intelligence screen — committed Simulator screenshot** (`./screenshots/tactile-sheets.png`,
iPhone 17 Pro Max). Swipe-to-approve reveal, draggable Regenerate/Ink sheet, egress as the
single `Local` badge (caught + removed a banned "privacy novel" line mid-build). Built as a
one-module `swiftc` simulator harness so craft is shown **without the device**. **HSM-14-03 started + on device:** the Tactile Sheets
`SwipeableArtifactCard` is now adopted into the REAL app (`MeetingCaptureApp`) — swipe
left→approve / right→dismiss with haptics, type-tinted over all 15 artifact types, elevated —
wired to the live `review.approve`/`review.reject`, built + deployed to the iPad Air M4. Next
under 14-03: the header + transcript card + a draggable bottom action sheet. — the missing dimension. The mobile roadmap was all
engineering tracks (Council Charter A–N); there was no track that owned whether the app is
**usable, designed, and modern** as a hand-driven (touch + Apple Pencil) product. Phase 14
is that track. It is **proven in the iOS Simulator with committed screenshots** — design and
interaction craft do NOT need the physical device to be delivered and shown — with the device
reserved only for true hardware feel (haptics latency, Pencil pressure). Owner bar: flat /
basic / default-SwiftUI components are a failure; the app must feel like a premium, modern,
native iOS app.)

## Why this phase exists

The HoldSpeak Mobile runtime is engineering-complete (Phases 0–13) but the **product** — the
felt, hand-driven experience — was never crafted or even tracked. Recording, the meeting
list, the transcript, the PencilKit notebook, and the intelligence review are functional but
plain: default styling, abrupt states, no gesture/haptic craft, no considered empty/loading/
error moments, no accessibility pass. For an app whose whole premise is *"pick it up, press
record, leave with artifacts"*, the experience IS the product. This phase elevates it to the
owner's bar and keeps it there.

## Goal

Make the iPad/iPhone app a **premium, modern, hand-driven native experience**: a real native
design system, every core screen recrafted, interaction craft (gesture, haptic, motion,
Pencil), accessibility + adaptivity, and a polish pass — each delivered with committed
**Simulator screenshots** as visible proof, so design is shown without the physical device.

## Scope

- **In:** the design system as native SwiftUI tokens + reusable components (HSM-14-01); the
  **capture** experience recrafted — record → live transcript, the flagship moment
  (HSM-14-02); the **meeting + intelligence** surface recrafted — list → detail → review,
  with felt-good states and gestures (HSM-14-03); **interaction craft** — gestures, haptics,
  motion/transitions, Pencil affordances (HSM-14-04); **accessibility + adaptivity** —
  Dynamic Type, VoiceOver, dark/light, size classes / multitasking, reduce-motion
  (HSM-14-05); a **polish & craft-QA** pass — empty/loading/error everywhere, micro-copy,
  edge cases, a screenshot gallery (HSM-14-06).
- **Out:** new runtime features or engines (Phases 1–13 own those — this phase recrafts how
  they're *presented*, not what they do). Backend logic in views (stays in the Runtime Core).
  App Store / TestFlight logistics (a release step).

## Exit criteria (evidence required)

- [ ] A **native design system** (typography scale, color + elevation tokens, spacing,
      motion) with reusable components (cards, buttons, chips, sheets, states) replaces ad-hoc
      styling — Simulator-screenshot-verified (HSM-14-01).
- [ ] The **capture** screen is a crafted flagship moment (live level/feedback, fluid
      record/stop, haptics, considered states) — screenshot + device-feel verified (HSM-14-02).
- [ ] The **meeting + intelligence** surface is recrafted: modern cards, swipe/gesture
      actions, clear empty/loading/generating/error states, a felt-good regenerate/approve
      flow — screenshot-verified (HSM-14-03).
- [ ] **Interaction craft**: gesture, haptic, motion, and Pencil affordances make it feel
      hand-driven, not tapped-through — verified (HSM-14-04).
- [ ] **Accessibility + adaptivity**: Dynamic Type, VoiceOver labels, dark/light, size
      classes / iPad multitasking, reduce-motion — verified (HSM-14-05).
- [ ] **Polish & craft QA**: every surface has its empty/loading/error state, micro-copy is
      considered, and a committed Simulator screenshot gallery is the proof of bar (HSM-14-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-14-01 | Native design system (Signal → SwiftUI tokens + components) | in-progress | [story-01](./story-01-native-design-system.md) | [shot](./screenshots/tactile-sheets.png) |
| HSM-14-02 | The capture experience, recrafted (flagship moment) | in-progress | story-02 | floating draggable recorder + full-bleed canvas + mic-reactive waveform + faster transcription |
| HSM-14-03 | The meeting + intelligence surface, recrafted | in-progress | [story-03](./story-03-meeting-intelligence-recrafted.md) | cards materialize (glow+insert) + MIR-as-lens, on device |
| HSM-14-04 | Interaction craft (gesture, haptic, motion, Pencil) | backlog | story-04 | — |
| HSM-14-05 | Accessibility + adaptivity | backlog | story-05 | — |
| HSM-14-06 | Polish & craft QA (states, micro-copy, screenshot gallery) | backlog | story-06 | — |
| HSM-14-07 | Voice correction — reject by voice → local model re-routes | in-progress | [story-07](./story-07-voice-correction.md) | host-tested + on iPad |
| HSM-14-08 | The Pencil as a diagram language (sketch → Mermaid) | in-progress | [story-08](./story-08-pencil-diagram-language.md) | engine host-tested (209/0) |
| HSM-14-09 | Local vision model (Gemma 4) seam + ambiguity resolution | in-progress | [story-09](./story-09-local-vision-model.md) | seam host-tested (211/0) |
| HSM-14-10 | Models, front and center (import + manage, AirDrop-ready) | in-progress | [story-10](./story-10-model-import.md) | device-built |
| HSM-14-11 | The live capture canvas (transcription bubbles + tack-to-board) | in-progress | [story-11](./story-11-live-capture-canvas.md) | built + on iPad + Simulator-proven |
| HSM-14-12 | Constant-time live transcription (sliding window + commit) | in-progress (built + host-proven + sim-shown; device cadence pending) | [story-12](./story-12-constant-time-transcription.md) | [shot](./screenshots/constant-time-transcription-canvas.png) + story "Evidence" |
| HSM-14-13 | The spatial workspace (OS-like capture surface) | in-progress (deliverables 1–4 built + host-proven + sim-shown; stretch 5–6 + device feel remain) | [story-13](./story-13-spatial-workspace.md) | [docked](./screenshots/recorder-docked-top.png) / [orb](./screenshots/recorder-minimized-orb.png) / [free-place vs tack](./screenshots/recorder-freeplace-vs-tack.png) / [resize](./screenshots/recorder-resizable-card.png) / [tidy](./screenshots/recorder-tidy-grid.png) |
| HSM-14-15 | The Workbench (visual intelligence builder) | in-progress (engine + gamified canvas + run-from-meeting shipped; transforms/outputs next) | [story-15](./story-15-workbench.md) | [builder](./screenshots/workbench-builder.png) + `WorkflowTests` (7) |
| HSM-14-17 | On-device speaker diarization (who's talking, air-gapped) | in-progress (model spike + Swift matcher/diarizer host-tested; capture-wiring + UI + 2-speaker device proof pending) | [story-17](./story-17-on-device-diarization.md) | `SpeakerMatcher`/`SpeakerDiarizer`/`SpeakerClustering` tests + `AudioEmbed.mlpackage` (cosine 0.99993 vs resemblyzer) |
| HSM-14-18 | Real-time MIR (live intelligence on the iPad, configurable) | in-progress (the cadence/trigger brain `LiveIntelCadence` host-tested; runner + Queue HUD + setup screen + device proof pending) | [story-18](./story-18-realtime-mir.md) | `LiveIntelCadenceTests` (6/0) |

## Where we are

Just opened, in direct response to owner feedback that craft/usability/design was absent from
the roadmap and undelivered. The runtime is done; this phase is about the **experience on top
of it**. It runs design-first: each story is built, then **screenshotted in the Simulator and
committed**, so the owner can see and judge the craft without the physical iPad — the device
is only for final hardware feel. The design direction (the visual + interaction language) is
the owner's call and is being set before HSM-14-01 lands, so the system is built to the right
target, not guessed.

**2026-06-21 — the intelligence pane + the live capture canvas.** Owner: artifacts "just
start appearing, no effect, no nothing," and the balanced/architect/delivery/product/incident
profiles "don't do shit — all it does is change the order." Fixed both. Cards now
**materialize**: a type-tint ring flashes around each as it lands + the insert is animated, so
a generated insight announces itself. The MIR profile became a real **lens** — a pill row with
a per-profile icon, a one-line blurb of what it surfaces, and emphasized-type chips, and the
Generate button names the lens it runs through (HSM-14-03). And the flagship: the live
transcript "wall of text" is replaced by the **live capture canvas** (HSM-14-11) — utterances
float up as bubbles, the live fragment breathes as a caption, and you grab a bubble with the
Pencil and **tack it to a pin board**, which marks the moment so the on-device intelligence
weights it. Three bespoke **Pixellab** pixel-art assets (Qlippy mascot, brass pushpin, waveform
orb) bundled offline. Built + installed on the iPad Air M4; Simulator screenshot committed.

**2026-06-22 — shipped the live-dynamism batch + planned the next two.** PRs #117/#118 landed:
the transcription slowness was root-caused (the Whisper model reloaded every tick → cached;
3 s → 1.2 s cadence), an **audio-reactive waveform** off the real mic level, the recording
controls collapsed into a **draggable floating recorder** (no big button), the canvas became
**one free-form dot-grid desktop** (fling a bubble anywhere to tack), and note cards now
**promote to real `needs_review` artifacts**. Then the owner asked to **plan, not build, the next
two properly**: **HSM-14-12** (constant-time live transcription — a timestamp-driven sliding
window so long meetings stay immediate; the model-cache fixed the acute pain but per-tick cost
still grows O(length)) and **HSM-14-13** (the spatial workspace — dockable/minimizable recorder,
free-place vs tack, resizable cards, tidy, and stretch: minimap + windowed panes). Both are
written up as stories with architecture, acceptance criteria, and test plans; implementation is
deferred.

**2026-06-22 (later) — HSM-14-12 built.** Constant-time live transcription landed: `MeetingCapture`
keeps a **committed prefix + a bounded active window**, so `tick()` re-transcribes only the audio
since the last commit (≤ `commitThreshold + overlap` seconds) instead of the whole take — the live
transcript stays `committed + tail` (complete, monotonic) and costs the same to recompute at minute
40 as at minute 1. The enabler was teaching `WhisperKitTranscriber` to return WhisperKit's **real
per-segment timestamps** (it had collapsed them to one zero-stamp segment). Production thresholds
plus the existing tests' 1-frame chunks mean **no existing test ever commits**, so the short-meeting
path is byte-identical and all 211 prior tests pass unchanged; three new `SlidingWindowTests` prove
the bound, the no-loss/no-dup seam (the fake capture encodes absolute audio position so a gap shows
up as a wrong word sequence), and the blank-window safety. `swift test` **214/6/0**; the app builds
for the Simulator and the live canvas it feeds renders intact (committed shot). Remaining: the owner
eyeballs the cadence at the end of a ≥10-minute real meeting on the iPad (acceptance #6).

**2026-06-22 (later still) — HSM-14-13 deliverable 1 built.** The "OS-like" recorder: the
`FloatingRecorder` now **docks** to the top/bottom edge on drag-release (magnetic snap + haptic) or
**floats** clamped-on-screen where you drop it, and **minimizes** to a compact breathing **rec orb**
(tap to re-expand every control — the "never trap" rule). The dock/float/minimized state persists on
`CaptureModel` across pane switches + re-entry. The snap/dock math is a **pure RuntimeCore function**
(`RecorderSnap`, 9 host tests); `swift test` **223/6/0**. Built for the Simulator; the top-docked
capsule + the minimized orb are committed shots. Deliverables 2–4 (free-place vs tack, resizable
cards, tidy) remain on the story.

**2026-06-22 — HSM-14-13 deliverable 2 (free-place vs tack) built.** A dragged bubble now lands two
ways: a plain drop below the stream places it as a **loose card** (no marked moment), and a drop on
the **tack target** (a dashed pill that appears only mid-drag and lights up when you're over it)
**tacks** it — a pushpin + tilt that calls `markMoment` so the on-device intelligence weights it. A
loose card promotes to a moment later via "Tack as moment". The drop decision is RuntimeCore's pure
`BubblePlacement` (5 host tests); `swift test` **228/6/0**. Two committed shots (the mixed canvas
with the honest "1 tacked · 1 placed" footer, and the lit tack target). Deliverables 3–4 remain.

**2026-06-22 — HSM-14-13 deliverables 3 + 4 built.** (3) **Resizable cards**: a corner-drag grip on
each workspace card resizes its width, text reflows, the width is clamped to a readable range by the
pure `CardSize.clampWidth` and persists. (4) **One-tap tidy + undo**: a "Tidy" control re-flows the
loose cards into a centered grid below the stream (tacked moments stay put) via the pure
`WorkspaceTidy.layout`, with a single Undo that restores the prior arrangement. Both decisions are
host-tested (`CardLayoutTests`, +5); `swift test` **233/6/0**. Two committed shots (a reflowed wide
card with its grip; five loose cards tidied into a grid with the Undo·Tidy control). **HSM-14-13 is
now deliverables 1–4 complete**; only the stretch 5–6 (minimap, windowed panes → candidate
HSM-14-14) and the device hardware-feel pass remain.

**2026-06-22 — craft elevation pass begins (owner: "push the UI/UX a lot more").** On owner
feedback that the shipped effects were "low-level / basic," the Signal design system gained real
**depth + motion primitives** (`Sig.bgGradient`/`accentGradient`/`localGradient`/`topHairline`, a
shared `SignalCard` elevation treatment, a `GlyphChip` gradient icon container, a `PressableCard`
press style, reduce-motion-aware entrances) and the **home screen was rebuilt to a flagship bar**
(adopting HSM-14-01 into a real screen): a cinematic gradient background with soft accent/cobalt
glows, an "ON-DEVICE · NOTHING LEAVES" badge, a hero Record CTA on the accent gradient with a
pulsing mic ring, side-by-side gradient-chip tiles, elevated meeting cards with staggered entrance,
a count chip, and a considered empty state. Built for the Simulator AND installed live on the iPad
Air M4; before/after + empty-state shots committed. This kicks off a standing elevation of every
surface (capture chrome + intelligence pane next).

**2026-06-22 — the generation theater (HSM-14-03), on owner feedback that the post-meeting
generation was "the most boring effect imaginable."** The 1pt spinner is replaced by a living,
narrative on-device moment: a breathing **thinking orb** (concentric accent-pulse rings + a rotating
conic shimmer + a gradient core), a **constellation of the lens's target types** that light up one
by one — pending (dim) → in-flight (glowing, ringed) → done (filled + check, with a light haptic) —
as the model drafts each, the named lens, and a "Running on this iPad · no network" pill; a heavier
haptic + an "N insights ready" flourish banner on completion. Driven by REAL per-type progress
(`MeetingReviewState.genTypes`/`genDone`/`genCurrent`/`genFlourish`, set inside `generate()`), so the
animation tracks the actual model work. Built for Simulator + installed live on the iPad; committed
shot (`generation-theater.png`). **Next: the Workbench (visual intelligence builder) + App Settings
(inference endpoint/target).**

**2026-06-22 — App Settings (inference target), on owner feedback ("where in the frig are our app
settings… we can't specify the endpoint and type").** A real, persisted Settings surface (gear in
the home header → `SettingsView`): choose **where intelligence runs** — *This iPad* (Mode A,
on-device, nothing leaves) or a *LAN endpoint* (Modes B/C, any OpenAI-compatible server) — with the
endpoint URL/model/optional-key fields and a live **Test connection** (pings the endpoint via
`OpenAIEndpointProvider.complete`). Persisted in `InferenceConfigStore` (UserDefaults; the key never
leaves the store) and **wired into `generate()`**, which now branches the provider on the setting
(LlamaProvider for local, OpenAIEndpointProvider for an endpoint) and refuses cleanly when the
chosen target isn't ready — so the owner can finally point inference at the `.43` box. Signal depth
throughout (gradient target cards with accent-selected border, glyph chips, an honest egress pill).
Built for Simulator + device; committed shot (`settings-intelligence.png`). Reuses the HSM-5-06
`RuntimeMode`/`EndpointConfig` seam. **Still next: the Workbench (visual intelligence builder).**

**2026-06-22 — the Workbench begins (HSM-14-15), on the owner's vision of a gamified visual
intelligence builder.** The flagship is scoped + its **engine foundation shipped + host-tested**:
`Sources/RuntimeCore/Workbench/Workflow.swift` — a user-defined workflow is a *linear pipeline*
(SOURCE → STEPs → OUTPUT; the deliberate usability bet over a node-and-wire graph), with the basic
logic blocks (lens / extract / summarize / rewrite / keep-if), egress-aware outputs, a human-readable
`plan`, derived produced-types, and one-tap `WorkflowPresets`. `WorkflowTests` (7), `swift test`
**240/6/0**. The design is in [`story-15`](./story-15-workbench.md). **Next build: the gamified
canvas** (tap blocks from a palette, drag to reorder, run through the configured `ILLMProvider` with
the generation-theater treatment, results to the chosen output).

**2026-06-22 — three owner-flagged fixes (prose / hand-typed model / unused PixelLab).** (1) **No
prose**: Settings' chatty test-result sentences ("Reachable — the model replied") are gone; the
endpoint state is now a tight chip ("3 found" ✓ / "no connection" ✗). (2) **Fetched model picker**:
the model is no longer typed by hand — a fetch button calls the endpoint's `GET /v1/models`
(`InferenceConfigStore.fetchModels`) and you **pick** from the real list in a menu; the fetch
doubles as the reachability check. (3) **PixelLab, used for real**: a bespoke generated **plasma
energy core** (PixelLab `theaterorb.png`, bundled offline) is now the centerpiece of the generation
theater — a swirling sprite that slowly rotates + breathes inside the accent pulse rings, replacing
the SF-symbol glyph. Built for Simulator + device; shots `settings-models-fetched.png`,
`generation-theater-pixel-orb.png`. Standing note: lean on the PixelLab MCP for craft, not SF glyphs.

**2026-06-22 — the Workbench canvas (HSM-14-15) is live.** The gamified visual builder the owner
asked for: `WorkbenchView` (a flagship Workbench tile on the home) is a vertical **SOURCE → STEPs →
OUTPUT** pipeline of Signal blocks with flowing connectors — tap a block from the **ADD A STEP**
palette (lens/extract/summarize/rewrite/filter), configure each inline (menus), reorder (per-step
up/down) and remove, with four one-tap **presets** and a header **PixelLab crystal**. **Save** writes
to `WorkflowStore` (UserDefaults). And it **runs**: a meeting's detail gains a **"Run a workflow"**
menu → `MeetingReviewState.generate(workflowTypes:)` executes the saved workflow's produced types
through the configured provider (on-device or LAN) with the full generation-theater treatment.
Built for Simulator + device; shot `workbench-builder.png`. Crushing-usability linear-pipeline bet,
no prose. Remaining: the non-extract transforms (summarize/rewrite/keepIf) + note/Slack outputs.

**2026-06-22 — the Workbench becomes a real builder (HSM-14-15), on owner feedback ("this is not a
builder").** Two gaps closed: (1) a fully **custom node** — `WorkflowStep.llmCall(name, prompt,
input)` — where you write your own prompt over a chosen input (the meeting or the previous step),
first-class alongside the curated lens/extract blocks (palette-led + emphasized); and (2) the
**building interaction** — cramped inline menus are gone; **every block is tap-to-configure**, opening
a real editor sheet (`WorkbenchEditorSheet`) with selectable choice lists and, for the LLM-call node,
a NAME field + an INPUT selector + a full multi-line **prompt editor** (with `{input}` injection).
`swift test` **241/6/0** (+1 llmCall test). Built for Simulator + device; shots
`workbench-custom-node.png`, `workbench-llm-editor.png`. Remaining: execute the custom prompt + the
other transforms/outputs.

**2026-06-23 — HSM-14-17 opened, the model side is fully de-risked + the Swift matcher landed (host
slice).** On-device speaker diarization brings desktop parity (the desktop diarizes via resemblyzer +
cosine matching; the iPad's `Segment.speaker`/`speakerId` slot did nothing — every line "Speaker 1").
Whisper never produces speaker info, so this is a separate on-device pipeline. The highest-risk pieces
are answered: resemblyzer's `VoiceEncoder` converts to Core ML **bit-exact** (cosine 0.99999), and an
end-to-end **audio→embedding** model (`apple/ml/AudioEmbed.mlpackage`, 3.1 MB) bakes the mel front-end
in (`torch.stft`) and matches resemblyzer at **cosine 0.99993** — so Swift needs ZERO DSP, and the
encoder being identical to the desktop's unlocks cross-device speaker identity later. The pure Swift
side ships host-tested: `SpeakerMatcher` (cosine/threshold/EMA/new-speaker/rename) + `SpeakerDiarizer`
(over an injected `AudioEmbedding` seam; `AudioEmbedder` is the on-device CoreML conformance) +
clustering, all green. `swift test` green. Remaining on the story: the CoreML wrapper wiring into the
capture loop, the opt-in setting, transcript speaker labels, and the only proof that counts — a real
2+ speaker recording separating on the device.

**2026-06-23 — HSM-14-18 opened, the cadence/trigger brain landed (host slice).** Real-time MIR closes
the parity gap where the iPad only runs intelligence *post-meeting* while the desktop runs it **live**.
The first verifiable, device-free slice ships: `LiveIntelCadence` (`Sources/RuntimeCore/Capture/`) — a
pure decision struct answering *should a live intel pass fire now, and why*. Two INDEPENDENT,
user-tunable triggers: **tack** (the user flagged a moment ⇒ fire immediately — the cheapest, most
useful real-time signal) always wins when enabled; **cadence** fires only when BOTH floors are met
(`minNewSegments` new transcript AND `minSecondsBetweenRuns` elapsed) so a live pass never fights
Whisper + diarization on one chip. Both toggle + tune independently. `LiveIntelCadenceTests` 6/0;
`swift test` green. Remaining on the story: the live-intel runner, the gamified tack moment + Queue
HUD, the setup screen (incl. an OpenRouter endpoint with a fetched model picker), and the device proof.

**2026-06-24 — the desk's zones now HOLD things (drop-to-tag, handover §7 #1).** The 3D Living Desk's
drawn zones were beautiful and *empty* — you could scribble a crayon area, name it "Project Atlas," and
nothing could live in it; the drawn zones existed only as ephemeral SceneKit nodes the data model never
knew about. This leap makes a zone a **real, persisted place that holds cards**: a `DeskZone` (named
footprint, persisted in `hs.desk.zones`) is created when you name an area, and **a zone IS a directory**
(it reuses the existing filing map, so it also appears in the sidebar and opens in 2D). **Dropping a card
inside a zone's footprint files it** — the card settles in (a deliberate drop no longer flings back out),
a medium haptic fires, the zone pulses, and its count placard ticks up (`Project Atlas · 3`). Drawing
your first zone retires the auto time-fences (the desk becomes your manual workspace). Composed in the
offscreen renderer first — which caught a real layering bug (the zone fill was hidden *under* the leather
mat) before any device build; heights retuned (fill at y=0.53, above the mat top at 0.5) and ported 1:1.
`xcodebuild` device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air M4** (live
launch pending an unlock — the install completes regardless). This is the prerequisite for
[[story-24-nested-zones]] (dive-into-a-zone): a zone you can dive into must first have contents. Next: the
dive. See [[DESK_HANDOVER]] §7.

**2026-06-24 — a boundary becomes a doorway (dive into a zone, HSM-14-24).** The owner's most-excited
idea, built right on top of drop-to-tag: **double-tap a zone and you fall INTO it** — the camera rushes in
and zooms, and the zone *becomes* the whole desk, showing exactly the cards filed into it, with room for
its own sub-zones. It's **recursive**: zones are now **path-based containers** (`Atlas`, `Atlas/Q3`), so
drawing a zone while inside "Atlas" makes the child "Atlas/Q3" — a sub-zone is just a child directory
(Phase-16 organization sync carries it for free). Every level is **backable**: a `DeskBreadcrumb`
(`Desk › Atlas › Q3`, each crumb a tap-to-jump) plus a symmetric **double-tap the empty desk to climb
out**. The transition is gamified, not a cut — `syncLevel` settles the camera home from a directional
offset (dive = drop in from close; back = pull out from wide) with haptics. The nested-desk state was
composed in the offscreen renderer first (Atlas's members + a "Q3 Planning · 2" sub-zone reads as a place
inside a place). `xcodebuild` device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air
M4** (the live dive-FEEL walk is the last acceptance criterion — the one thing a static renderer can't
show). Handover §7 #1 + #2 are now both done; the desk is becoming the fractal workspace the owner can see.

**2026-06-24 — cards that MEAN something + the owner's card-craft feedback (handover §7 #3).** Cards were
title-and-metadata chips, all the same rounded rect. Now a card is a **window into its content**: every
card carries a real **snippet** (a meeting's actual summary, else its topics, else the first thing said;
an output card shows its body preview). And on the owner's sharp feedback — *"some cards should be more
obvious what they are, cards should come in different shapes and sizes, and the sticker needs to be less
regulated"* — a new `DeskCardKind` (parsed from the id) drives **form**: (1) **type-legible** — a tinted
TYPE badge (SUMMARY / TOPICS / ACTION / TRANSCRIPT / ARTIFACT / MODEL / KNOWLEDGE; a meeting needs none)
plus per-type colour; (2) **different shapes + sizes** — a summary is a big wide document, a transcript a
tall page, an action a small slip, each with its own corner radius, flowing through both canvases
(`renderSize`/`corner` replace the one-size `mode.size`) and the snippet line-count flexes with height;
(3) a **loose sticker** — the die-cut now varies rotation (±15°), scale, shape (rounded/circle/square)
and nudge per card with a lifted-corner shadow, instead of one regulated tile. Composed in the offscreen
renderer (a `faces` contact-sheet mode added) so the badges/snippets/sticker variety were judged at full
clarity first. `xcodebuild` device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air
M4**. Handover §7 #1/#2/#3 are now done; the desk reads like a real workspace, not a tech demo.

**2026-06-24 — the OBJECT LANGUAGE + the dive fix (owner feedback on the device walk).** Two things from
walking the build. (1) **Dive was broken** — `cardNode(at:)` returned ANY named node, so a tap on a zone
hit the zone's own node, fired `onTap("zone:…")` (a no-op) and ate the gesture; double-tap was unreliable
on top of that. Fixed: zones are excluded from `cardNode`, and **a single tap on a zone now dives in**
(double-tap still works too; double-tap empty climbs out), with a `›` "enter" cue on the placard.
(2) The bigger one — *"why would everything be this wooden chip with shit written on it instead of doing
something proper?"* Right. Introduced an **object language**: hardware/containers are now real 3D things,
not paper chips — a **meeting is a cassette** (body, reels, tinted title label — a recording), a **model
is a glowing cartridge** (glossy slab, an emissive accent bar = loaded/alive, gold contact pins; the owner
singled models out), a **knowledge base is a crystal**, a **notebook is a book**. Only actual **documents**
(summary / topics / action / transcript / artifact) stay paper — appropriate, since they're what a meeting
spills into. `makeObject` dispatches by `DeskCardKind`; each object keeps a box physics body so it still
flings/stacks/files. Sculpted in the offscreen renderer first (cassettes + cartridge-with-glow + crystal +
book, judged together) then ported 1:1. `xcodebuild` device-arch **BUILD SUCCEEDED**; built + signed +
**launched live on the iPad Air M4** (unlocked this time). Next: extend the object language to the paper
documents (a scroll for transcript, a sticky for action, a stack for summary) + the act-on-expand affordance.

**2026-06-24 — the FOCUS LENS (lift-to-inspect) + long-press fix (owner feedback on a device walk).**
(1) **Long-press churned the whole desk** — it cycled a card's paper *style*, and the default desk's
zone-layout rebuilds *everything* when any card's style signature changes. Gated: long-press only cycles
style on **paper documents**, so it's a no-op on the cassette/cartridge objects (and the default desk).
(2) The big one — the owner's vision for **expand**: selecting an object should **lift it toward the
camera**, and during the lift it goes **non-solid** (so it doesn't shove the desk), with its desk
position **saved** so it **clips back** on exit; the world goes **under a fog lens** (clear centre on the
lifted object, denser fog toward the edges); and its **outputs float in a VIRTUAL layer** around it
instead of spilling into the physics desk. Built: tapping a meeting in 3D enters focus (`focusedId`) →
`LivingDeskCanvas` lifts the node (kinematic + collisionless, transform saved, animated up + scaled) and
drops it back on exit; a SwiftUI `DeskFocusOverlay` fogs the desk (radial clear→dark) and fans the
meeting's output cards (real `DeskCardFace`, readable) in the air with a staggered spring; tap anywhere to
close. `xcodebuild` device-arch **BUILD SUCCEEDED**; installed on the iPad Air M4 (launch pending an
unlock). **Needs an on-device tuning pass:** the lift target/scale + the fog's clear-centre radius are set
by reason, not yet eyeballed on the glass. **Real-asset note:** tried CC0 poly.pizza models
(cassette/microchip/crystal/book) for the objects — they imported untextured/rough (palette-UV → white)
and read worse than the procedural objects, so they're set aside pending a real texturing/curation pass
(IDs + pipeline saved in the handover). The procedural objects stay for now.

**2026-06-24 — levitation idle on the focus lens (owner: "make them hover, unsettled, like they're
floating").** The lifted object and its floating outputs were frozen once settled — reads as stuck. Now
both **levitate**: the 3D lifted object runs a slow bob + drift + tiny tumble on three different periods
(so the motion never looks like a loop), started on lift-settle and removed before it clips back; each
floating output card drifts + sways on its own phase (a `TimelineView` with a per-card seed). Subtle
amplitude — a few points / fractions of a unit. `xcodebuild` **BUILD SUCCEEDED**; installed on the iPad
Air M4 (launch pending an unlock).

**2026-06-24 — FOUNDATION PIVOT: the Desk becomes a premium 2.5D diorama (owner: "rethink the
approach").** After a run of features that were mechanically present but read as an *alpha* build, the
owner called it — and chose, from a direct question, to **rethink the foundation** rather than keep
polishing the hand-rolled real-time 3D. The honest root causes: (a) procedural box-geometry is
programmer-art by construction, (b) I was rendering **blind** (the offscreen renderer is dark/untone-mapped
and the device kept locking), so every pass was a guess. New direction (owner-picked): a **crafted,
art-directed 2.5D diorama** — the bespoke **PixelLab** objects (cassette = meeting, AI-core cartridge =
model, crystal = knowledge) on a warm, lit desk that recedes into space, with grounding shadows, a leather
work mat, depth haze, wood grain, and elegant zone trays. The decisive win: it's built in SwiftUI and
**verified at FULL fidelity in the iOS Simulator** (`scripts/diorama/` + `scripts/diorama-shot.sh`, a clean
one-module harness isolated from the macOS SceneKit CLI) — quality stops being a guess. First composition
proven + committed ([shot](./screenshots/desk-diorama-v1.png)). The 3D `LivingDeskCanvas` stays in the app
untouched for now; the diorama is the new target to build the experience (objects, zones, the dive, the
focus lens) up to — at this bar, screenshot-verified each step.

**2026-06-24 — DELIGHT, found (owner: "the exact simplicity and delightfulness I was looking for. Keep
expanding").** The static-diorama screenshot was rightly called embarrassing; the unlock was the owner's
definition — *"premium = I'm delighted when I use it."* Delight is **felt in motion**, which a screenshot
can never carry — so the proof medium changed to **Simulator VIDEO** and the craft to **motion + character**.
What landed: a clean dark stage, the bespoke PixelLab objects **springing in with overshoot** (staggered),
then never sitting still (breathe / drift / tilt on their own rhythms), a pulsing stage glow, and **Qlippy
with real character** (sways, hops). Then **expanded to respond to touch**: tap a meeting → it springs to
centre, the others recede + dim, and its intelligence **blooms** out as clean cards (Summary / Actions /
Transcript) with a staggered spring; Qlippy gets excited; tap empty → everything springs home. Built
interactive AND auto-played (`DIO_DEMO=1`) so the whole flow records in motion. Proof:
[stage](./screenshots/delight-stage.png) · [focus bloom](./screenshots/delight-focus.png) + the recorded
clips. The lesson, locked: **stop proving feel with frozen frames — record motion, then feel it on device.**

**2026-06-24 — expanded the loop: the capture moment (record → listen → a meeting is BORN).** On "keep
expanding on it," added the app's core action in the same alive style: a breathing **record orb** → a calm
**Listening…** state (a voice core — breathing orb + expanding rings + a ring of reactive bars — with live
words rising and fading) → Stop, and the recording **crystallises into a new cassette** that pops onto the
stage with a spring + a success haptic, then opens to its intelligence. Create and consume, both delightful,
both verified in motion. Auto-played tour under `DIO_DEMO=1`. Proof:
[listening](./screenshots/delight-listening.png) · [born](./screenshots/delight-born.png) + the recorded
clip. Next candidate expansions (keep it simple): the model/KB objects responding on tap, acting on a card
(send/approve), and the fractal dive — then port the whole feel into the real app + onto the device.

**2026-06-24 — the diorama is ON THE DEVICE (owner: "let's get it on my iPad").** Integrated the
motion-first 2.5D stage into the real app as `DioStage` (`App/MeetingCapture/DeskDioramaStage.swift`,
Dio-prefixed to avoid collisions, reuses `DeskSprite` + the app's `Color(hex:)`), and made it the app's
**front door** (`MeetingCaptureApp`): the 3D object desk is now behind `HS_REAL_DESK=1`, the classic list
behind `HS_CLASSIC_HOME=1`. Device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air
M4** via the proven `meeting-capture-device.sh` pipeline (launch pended on the lock screen). This is the
real test the owner asked for — feel it on glass (haptics on tap/record live). Next: tune the feel WITH
him on the device, then keep expanding (other objects respond, act-on-card, the dive).

**2026-06-24 — unwound the device bugs the owner hit (drag / hit-testing / per-type content).** First real
device walk of `DioStage` surfaced three: (1) **no drag** — objects couldn't be moved; added a per-object
`DragGesture(minimumDistance:0)` that distinguishes tap (<9pt → open) from drag (→ reposition, persisted in
a unit-coord `positions` map, clamped on-desk), with a light haptic. (2) **unreliable taps** — the hit zone
was the object's ~2× glow, so the big AI Core swallowed the crystal's taps; tightened each hit zone to the
sprite footprint (`.frame(s,s).contentShape`). (3) **every object showed meeting cards** — added per-type
`contentFor(id)` (meeting → Summary/Actions/Transcript; KB → docs/decisions/ask; model → on-device status).
Also killed the jump: the focused object had been swapping between two `ForEach`es (identity loss → broken
animation) — now ONE z-ordered list. Device-arch **BUILD SUCCEEDED**; **launched live on the iPad Air M4**
(unlocked). Awaiting the owner's feel pass on drag + per-object taps.

**2026-06-24 — the diorama becomes a real ENGINE + the drag root-cause fix (owner: "build out a full
engine... and still can't drag").** Drag never worked because the `DragGesture` was attached INSIDE the
per-frame idle `TimelineView` (rebuilt ~60×/s → the in-progress drag was torn down every frame; taps
squeaked through, continuous drags died). Fix: split `DioHero` so the gesture + `.position` live on a STABLE
outer view and only the idle motion stays in `DioHeroVisual`'s TimelineView. Then wired the **real engine**:
`DioStage` now owns a `CaptureModel` and renders **real objects** — your recent meetings as cassettes,
installed models (`ModelFiles`) as AI-core cartridges, knowledge bases as crystals — each with **real
content** in the bloom (a meeting's actual summary/actions/transcript counts; model status; KB item count),
**drag positions persisted** in `@AppStorage`, the record orb opening the **real `CaptureView`** (a captured
meeting refreshes onto the desk), and a meeting card opening the **real `MeetingDetailView`**. Reinstalled
clean (uninstall → fresh install) to kill the stale-build worry. Device-arch **BUILD SUCCEEDED**; installed
on the iPad Air M4 (launch pended on the lock screen).

**2026-06-24 — the diorama gets PLACES: fractal zones + the dive (owner's most-excited idea, now in the
2.5D front door).** The pivot diorama could show your meetings but had no structure — a flat stage of loose
objects. This leap gives it **places**. A **zone tray** is a premium recessed drawer that HOLDS meetings: a
tinted label + count, member previews idling inside, an empty-state nudge, and a teaching **DIVE IN** cue.
You **make a place** (a dashed **+ New Zone** tile → name it), **drag a meeting onto a tray to file it**
(drop-to-tag — the tray lights up "hot" as you hover, a success haptic + count tick on drop), and **tap the
tray to DIVE in**: a gamified camera rush (asymmetric scale-through + an accent **whoosh** flare + heavy
haptic) where the zone *becomes the whole desk*, showing its members and its own **sub-zones** —
**recursive**, path-based (`Atlas` → `Atlas/Q3`). A **breadcrumb** (`🏠 Desk › Project Atlas › Q3 Planning`,
each crumb tap-to-jump) shows where you are; tap empty climbs out a level; the accent glow **retints to each
zone's colour** as you descend. Built in the **harness first** (`scripts/diorama/Diorama.swift`) and
**screenshot- + VIDEO-proven in the Simulator** — the dive is motion a frozen frame can't carry, so the
auto-tour (`DIO_DEMO=1`) was recorded and the mid-dive frames confirm the camera-rush + breadcrumb-extend +
interior-materialize reads right. Then **ported to the real app** (`DioStage`) against the live
`CaptureModel`: real meetings file into real zones (`hs.diorama.zones`/`hs.diorama.filed`, path-based,
persisted), models (cartridges) + KBs (crystals) stay at root, drag-to-file hit-tests the trays. Harness
switched to **portrait full-screen** (the landscape Info.plist was letterboxing the canvas into a short band).
Device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air M4** (launch pended on the lock
screen — the install completes regardless). Proof: [root](./screenshots/fractal-desk-root.png) ·
[inside Atlas](./screenshots/fractal-desk-atlas.png) · [mid-dive](./screenshots/fractal-dive-transition.png) ·
[deep in Q3](./screenshots/fractal-zone-q3.png). This is handover §7 #2 (dive) + #1 (drop-to-tag) brought
into the diorama, and the start of #5 (zones). Next: feel the dive on glass with the owner, then act-on-expand
(§7 #3) + the Ask-AI atom (§7 #7).

**2026-06-24 — zones go LOW-PROFILE + intelligence becomes a PULL-OUT (owner feedback on the device walk).**
The owner walked the first cut and hit real failures: (1) **no way out of a zone** — the small "Desk" crumb
fell through to the "+ New Zone" handler underneath; (2) after recording, **stray taps outside the menus
triggered things** (a receded object still ate the tap); (3) tapping a meeting's contents opened **"the plane,
super boring old-ass window"** (the `MeetingDetailView` nav sheet) — "the biggest and laziest shortcut," when
the whole point is a **seamless drawer experience with first-class primitives**. Plus a direction: zones should
be **lower-profile** to leave room for **"pull-outs such as intelligence."** All addressed, composed in the
harness first then ported to `DioStage`: (1) **a big always-on-top Back bar** (a 44pt "‹ Back" pill + the
breadcrumb, `zIndex 100`) — no tile can steal its tap; (2) **a focus fog** that catches outside taps → close,
and a receded object no longer accepts taps; (3) the centered modal/nav sheet is gone — a tapped object's
intelligence now **PULLS OUT from the right edge** as a rich in-world drawer (real **Summary / Actions (owner ·
due) / Topics chips / Transcript**, an On-device badge, a subtle "Open full editor" fallback) while the object
stays spotlit on the left over the fog; (4) **zones are now a compact top shelf** of labeled trays (icon +
name + member dots + dive cue), not dominating boxes — the canvas stays open for the pull-outs. Drag-to-file
still hit-tests the shelf trays. Harness screenshot-proven (root shelf, the intel pull-out, the in-zone Back
bar); device-arch **BUILD SUCCEEDED**; built + signed + **launched live on the iPad Air M4** (unlocked). Proof:
[root shelf](./screenshots/fractal-desk-root.png) · [intel pull-out](./screenshots/fractal-intel-pullout.png) ·
[in-zone Back bar](./screenshots/fractal-desk-atlas.png). Next: feel it on glass + the act-on-card affordance
inside the pull-out (approve an action → task/issue) + the Ask-AI atom (§7 #7).

**2026-06-24 — THE PRIMITIVE CONTRACT (owner: "literally everything should be a primitive, emitting a
standard UI integration pattern you can rely on"; chose "contract refactor first").** The interactions had
been built one-off, so the desk "felt weird." Designed the coherence layer ([[story-25-the-desk-interaction-system]])
and built its foundation: a `DeskPrimitive` protocol (`DeskPrimitive.swift`) — every desk concept declares the
same facets (`kind` → glyph + colour, `title`, `subtitle`, `preview`, **`sections`**, **`actions`**, `emits`,
`accepts`) and the **entire UI is DERIVED from that declaration**: the canvas object (`DioHero`), the card,
and the right-edge **pull-out** (`DioPullout` — ONE renderer that draws any primitive's `sections`/`actions`,
no per-type code). `MeetingPrimitive`/`ModelPrimitive`/`KBPrimitive` conform; `DioStage` now holds
`[any DeskPrimitive]` and renders uniformly. Adding a platform concept = declaring one primitive; its whole UI
appears for free. `emits`/`accepts`/compat are declared now so the **keystone routing gesture** (drag an
output onto the AI core → LLM → a new primitive prints) is trivial to add next — that's the agreed next build.
Proven: the SAME pull-out renderer draws a meeting (summary/actions/topics/transcript) and the AI core (model
status) identically — [meeting](./screenshots/fractal-intel-pullout.png) vs
[AI core](./screenshots/primitive-model-pullout.png). Device-arch **BUILD SUCCEEDED**; built + signed +
**launched live on the iPad Air M4**. The whole design canon is in
[story-25](./story-25-the-desk-interaction-system.md) (gesture library · intelligence engine · integrations ·
build order). Next: the keystone routing gesture (drag → AI core → real LLM → new card) on real metal.

**2026-06-25 — THE KEYSTONE: route any primitive through the AI core → a real LLM → a new primitive
(owner: "keep building an ecosystem!").** The intelligence engine, made tactile. **Drag a primitive (a
meeting, or a kept output) onto the AI-core cartridge** — it lights up "hot" (accent ring) when a compatible
target is under it (`accepts ∋ kind`, from the Primitive contract) — and on drop a **route sheet** opens:
pick a **lens** (Summarize / Action items / Risks / Decisions / Draft email) or edit the prompt freely. "Ask"
runs it through the **real `ILLMProvider`** — on-device `LlamaProvider` (GGUF) or the configured endpoint, via
`InferenceConfigStore.makeProvider` — grounded in the source's `routableText` (derived generically from its
sections), with a **generation theater** (the thinking orb + "on this iPad · no network"). The result
**prints as a NEW first-class primitive** (`OutputPrimitive`, kind `.artifact`) → **Keep on desk** (it lands,
persisted in `hs.diorama.outputs`, and can be routed AGAIN — every output is an input) or **Bin**. Routing is
generic over the contract: drop is `target.receive(source)`; the AI core `accepts` everything, a KB accepts
notes/artifacts. Composed + screenshot-proven in the harness ([sheet](./screenshots/route-sheet.png) ·
[theater](./screenshots/route-theater.png) · [printed](./screenshots/route-printed.png)), wired to the real
provider in `DioStage`. Device-arch **BUILD SUCCEEDED**; built + signed + **installed on the iPad Air M4**
(launch pended on the lock screen). This is story-25 build-order #1 — the smallest thing that makes the whole
ecosystem real. Owner runs the real on-metal route (needs an on-device model or a configured endpoint). Next:
the visible route arc, the long-press "Route to…/Send to…" menu, and connectors-as-primitives (drop an output
on Slack → propose→approve→execute).

**2026-06-25 — THE INTEGRATIONS HALF: connectors as primitives (owner: "keep going").** The loop closes —
capture → route into the AI core → judge → **act into the world**. A **`ConnectorPrimitive`** (a Slack tile)
is a first-class primitive like any other, but rendered from an **SF Symbol** (the contract gained
`isSymbol` — connectors are tools, not pixel recordings) and it `accepts` outputs. **Drop a kept output (or a
meeting) onto Slack** → it lights up hot (same `accepts ∋ kind` grammar as the AI core) → a **send card**:
propose→approve→execute, showing *what*, *where*, and the **one egress badge** (`Cloud · Slack`, per
POSITIONING canon — no privacy prose). **Approve & send** POSTs to a Slack **incoming webhook** (real
`URLSession`), stored on-device (`hs.diorama.slack`, pasted via a Connect sheet on the connector's pull-out
action), with a sent toast / honest failure. Routing is now fully generic: `beginRoute` switches on
`target.kind` (model → ask the LLM, connector → send), and *the AI core and a connector are reached by the
exact same drag gesture*. Harness-proven ([Slack on the desk](./screenshots/desk-with-connector.png) ·
[send card + egress badge](./screenshots/connector-send-card.png)); device-arch **BUILD SUCCEEDED**; built +
signed + **installed on the iPad Air M4** (launch pended on the lock screen). story-25 build-order #4. The
ecosystem now does the full arc: **record → route → keep → send.** Next: the visible route arc (cable
motion) + the long-press "Route to…/Send to…" menu (the discoverable twin of the drag).

**2026-06-25 — GROUNDED: connectors ride the HoldSpeak actuator framework, gated on host PC connectivity
(owner: "I hope this is all grounded in those HoldSpeak actuators… this should be gated on host PC
connectivity").** Owned the gap honestly: the first connector was an ad-hoc iPad→Slack webhook POST — NOT
grounded in the Phase 37/38/61 actuator framework, and it held the credential on the iPad. Refactored end to
end so the connector is a faithful **propose→approve→execute** actuator routed **through the paired Mac**:
- **Host (Python), grounded in the real framework:** two new companion endpoints —
  `POST /api/companion/slack/propose` (records a `proposed` `ActuatorProposal`: target `slack`, action
  `post_message`, preview == the exact wire body, payload `{body:{text}}`, idempotent on content hash; a
  hidden sentinel `companion` meeting satisfies the proposals FK and is excluded from `list_meetings`) and
  `POST /api/companion/slack/{id}/decision` (approve → executes **immediately through the existing
  `_execute_slack_proposal` / `build_slack_connector` / `ActuatorExecutor`** guard stack — status gate,
  payload parity, manifest allow-list). **The webhook URL is joined in memory ON THE MAC at execute time —
  never accepted from or returned to the iPad, never on the proposal, never broadcast.** `/api/companion/status`
  now reports `connectors.slack_configured` (bool, no URL) so the iPad can gate. **13 new tests**
  (`tests/integration/test_web_companion_slack.py`) prove the matrix incl. the credential rule; existing
  slack-export (24) + meetings/history (43) green, no regressions. (One pre-existing, unrelated dashboard
  `egressLabel()` failure — confirmed failing on a clean tree, a stale gitignored web bundle.)
- **iPad (Swift):** the connector no longer holds a webhook. It reuses the desk's **Mac pairing**
  (`hs.peer.host`/`hs.peer.port`), is **gated on connectivity** (a `DeskHostLink.reachable()` `/health`
  check before any send; "your Mac isn't reachable" otherwise), and on **Approve & send** does
  propose→decide over the host endpoints — the iPad sends only text, receives only a preview/status. The
  connector tile now says "via your Mac"; the connect action pairs the Mac (host:port), not a webhook.
- The **egress badge** stays the one badge (`Cloud · Slack`); the send card reads "approve → your Mac posts
  it." Device-arch **BUILD SUCCEEDED**; harness send-card reshot
  ([send card](./screenshots/connector-send-card.png)). This is the right grounding the owner asked for —
  the iPad is a companion, the host owns the actuators and the credential.

**2026-06-25 — the route made VISIBLE: the cable + traveling token (story-25 #2).** Routing used to jump to
a centred modal — the gesture didn't read. Now a route DRAWS itself: a glowing dashed **cable** arcs from the
source primitive to its target with **tokens traveling the wire** while the model works (the Blueprints
"token travels wires" viz from the canon, on the desk), the target **pulses** as it runs, and the desk dims
behind — no modal. The modal `DioRoutingTheater` was replaced with this **on-desk** treatment fed by the real
source/target screen positions (captured at drop: `routeFrom` = source centre, `routeTo` = target centre via
`objectHit`). One mechanism, both routes (into the AI core, out to a connector). Composed + **video-proven**
in the harness (tokens visibly travel the cable frame-to-frame), ported to `DioStage`; device-arch **BUILD
SUCCEEDED**. Proof: [route arc](./screenshots/route-arc.png) + the recorded clip. Next on the list: the
long-press "Route to…/Send to…" menu (discoverable twin) + lasso→bundle→Ask + a second grounded connector.

## Operating principle (standing, beyond this phase)

Design/usability/craft is now a **standing quality bar on every mobile surface**, not a
one-time pass: any new mobile UI meets the HSM-14-01 design system, has its states, and ships
a Simulator screenshot. Flat/default/unconsidered components are a regression.
