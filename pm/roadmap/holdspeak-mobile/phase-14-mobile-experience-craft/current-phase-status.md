# Phase 14 — Mobile Experience & Craft

**Status:** in-progress (opened 2026-06-21 in direct response to the owner: usability,
design, and modern hand-driven mobile practice were never in the roadmap, and the app
shipped as a bare functional shell, not a crafted product. This phase makes the
**experience** first-class.)

**Last updated:** 2026-06-21 (**opened + first craft delivered.** The owner chose the
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

## Operating principle (standing, beyond this phase)

Design/usability/craft is now a **standing quality bar on every mobile surface**, not a
one-time pass: any new mobile UI meets the HSM-14-01 design system, has its states, and ships
a Simulator screenshot. Flat/default/unconsidered components are a regression.
