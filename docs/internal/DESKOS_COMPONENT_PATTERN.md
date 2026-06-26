# The DeskOS Component Pattern

> The canon for how a surface on the iPad desk (DeskOS) should look and behave,
> distilled from the one we got right: **the ambient recorder**. When you add a
> new desk capability (a clip tool, a translate tool, a timer, a scratch note,
> whatever), build it to this shape. If a future component disagrees with this
> doc, either the component is wrong or this doc is — reconcile, don't drift.
>
> Companion docs: [[DESK_HANDOVER]] (the running desk state), the
> `DeskPrimitive` contract (story-25), and `POSITIONING.md` (the egress-badge rule).
> The reference implementation is `apple/App/MeetingCapture/DeskDioramaStage.swift`
> (`DioRecordOrb` → `DioRecordModePicker` → `DioAmbientRecorder` → `DioWindowSlider`
> → `DioLiveIntelCard`).

---

## 0. The north star

The desk is a **place**, not a stack of screens. Everything lives *in the world*
and you act on it *in place*. A component that yanks you into a full-screen modal,
a hamburger drawer, or a separate "window" breaks the premise — it says "the desk
was just a launcher." The recorder proves the opposite: you tap a small mic in the
corner and the act of recording **happens on the desk**, radiating from where the
mic sits, while the rest of the desk stays visible and alive behind it. You never
leave. That feeling — *I am still in my world, the tool came to me* — is the whole
game.

The bar is the owner's bar: **coherent, meaningful, delightful.** Premium is "I am
delighted when I use it," and delight is felt in **motion**.

---

## 1. The nine laws

A perfect DeskOS component obeys all nine. The recorder is cited as proof on each.

### Law 1 — Anchored, never modal
The component has a **home**: a stable, (ideally persisted) dock point on the desk.
It never takes the whole screen. The desk stays drawn and interactive behind it.
A full-screen scrim that blacks out the world is a confession that you couldn't fit
the idea into the desk.
> *Recorder:* `orbPos(w,h)` is the home (bottom-left corner). During capture,
> `DioAmbientRecorder` draws anchored to that point with `alignment: .bottomLeading`
> and **no** full-screen background — the desk, the cassettes, the zones all stay
> visible. (The thing it replaced, `DioRecordingConsole`, painted a full-screen
> gradient and owned everything. We deleted it.)

### Law 2 — Radiate from the anchor
When active, the component **sprawls outward from its home** — signal, readout, and
actions fan around the anchor. It does not open a detached panel somewhere else on
screen. The eye stays at one point.
> *Recorder:* faint angled `MicWaveform` sprawls fan up-and-right from the orb; the
> live transcript, the marker row, and the result cards stack upward from the same
> corner. One locus.

### Law 3 — Quiet at rest, alive in motion
At rest the component is **small and tucked** — an invitation, not a billboard. It
earns space only when active, then it breathes (pulses, bobs, ripples). Idle chrome
is a tax on every glance.
> *Recorder:* at rest it is a 64pt `DioRecordOrb` plus a quiet "Record" label in the
> corner (it used to be a 96pt center-stage orb — too loud; the owner had us shrink
> and tuck it). Active, it pulses red, the waveforms react to mic level, the cards
> animate in.

### Law 4 — Intent before action, in place
When a tap forks ("which kind of thing am I starting?"), present the fork as a
**small hovering chooser anchored to the component**, not a settings screen or a
new route. Two or three big, legible choices, then commit.
> *Recorder:* tapping the mic opens `DioRecordModePicker` — a popup that hovers right
> over the orb with two choices ("Start a meeting" / "Talk to the desktop"). The desk
> shows through behind it. Pick one and you are recording.

### Law 5 — Act in place, on a scope
The component surfaces its **actions where you already are**, and lets you **scope**
them with the lightest possible control. No detour to configure, no full form.
> *Recorder:* the intelligence markers sit in the ambient body. Firing one opens
> `DioWindowSlider` — a single pleasant slider (0:30 to 5:00, default 0:30) to scope
> the action to a window of the live transcript. One drag, then "Go".

### Law 6 — Harvest, never dead-end
A component's output returns as a **small, keepable artifact** that drops into the
desk's shared currency, so it is routable again. Results are never a one-way
notification you cannot grab.
> *Recorder:* a fired lens/agent/crew returns a `DioLiveIntelCard` floating by the
> mic; "Keep" turns it into an `OutputRecord` on the desk — the same card type every
> other surface produces, so you can route it onward (to an agent, a connector, a KB).

### Law 7 — Compose, don't reinvent
A component is a **new doorway into the existing world**, not a new world. It reuses
the shared grammar: the `DeskPrimitive` contract, the one inference seam
(`callLLM` → on-device GGUF or the endpoint), agents, crews, the routing theater,
the `OutputRecord` card. If you find yourself building a parallel mechanism, stop —
route into the one that exists.
> *Recorder:* the live markers are not a bespoke feature. They are the **same**
> agents and crews you build elsewhere (`LiveTarget` = a quick lens, one of your
> agents, or a chain), fired through the **same** `agentReply` / `callLLM` seam. The
> recorder, agents, and chains became **one pipeline** because the recorder composed
> instead of reinventing.

### Law 8 — One badge of truth
A component states where work runs and where data goes with **one quiet badge**, not
a paragraph. This is POSITIONING canon: local / local+cloud / cloud, plus a target.
No privacy novels.
> *Recorder:* a single small badge reads "on device" (mint) or "to your Mac"
> (cobalt). Nothing more.

### Law 9 — Gated, never autonomous
The component fires **only on a tap**. Nothing leaves the device, acts on the world,
or spends a model call without an explicit human gesture. Host-side actions ride the
propose → approve → execute actuator path; the credential never sits on the iPad.
> *Recorder:* every live lens, every "Keep", every send is a tap. "Talk to the
> desktop" gates on Mac pairing before it will record toward the Mac.

**And the craftsmanship rule that underwrites Law 1 and 2:** draw the whole
component in **one coordinate space**. Overlays placed with `.position` live in the
`GeometryReader` space; chrome anchored with `.frame(maxHeight:.infinity, alignment:)`
plus `.ignoresSafeArea` is screen-anchored, and the safe-area inset shifts the two
apart. Mixing them is the bug that broke the old dock. Anchor everything to the same
origin (the component's home point).

---

## 2. The anatomy

Every component decomposes into the same parts. The recorder names them; yours
should map one-to-one.

| Part | What it is | Recorder example |
| --- | --- | --- |
| **The anchor** | a stable home point (persist it if the user can move it) | `orbPos(w,h)` |
| **The rest state** | small, tucked, one-tap, inviting | `DioRecordOrb` + "Record" |
| **The intent picker** | a hovering, anchored fork (only if there is one) | `DioRecordModePicker` |
| **The active body** | radiates from the anchor: signal + readout + actions | `DioAmbientRecorder` |
| **The scope control** | the lightest possible way to bound an action | `DioWindowSlider` |
| **The result** | a small, keepable artifact in the shared currency | `DioLiveIntelCard` → `OutputRecord` |
| **The badge** | one quiet line of egress/run truth | "on device" / "to your Mac" |

Not every component needs every part (a component with no fork skips the intent
picker; a component with no scoped action skips the scope control). But it never
*adds* parts outside this set — no separate settings screen, no detached panel, no
full-screen takeover.

---

## 3. The build checklist

Before a new desk component is "done", it clears this. Treat a failed line as a bug,
not a preference.

1. **It has a home and never goes full-screen.** The desk is visible behind it at
   every state. (Law 1)
2. **Its active state radiates from that home.** No detached panel. (Law 2)
3. **At rest it is small and quiet.** It does not compete with content for the eye.
   (Law 3)
4. **Any fork is a hovering, anchored chooser.** Not a route, not a sheet that owns
   the screen. (Law 4)
5. **Its actions are in place and scoped with one light control.** (Law 5)
6. **Its output is a keepable `OutputRecord`-class card.** It can be routed again.
   (Law 6)
7. **It reuses the shared seams** (`DeskPrimitive`, `callLLM`, agents/crews, the
   routing theater). No parallel mechanism. (Law 7)
8. **It carries exactly one egress badge.** No privacy prose. (Law 8)
9. **Every effectful thing is a tap; host actions are gated and credential-free.**
   (Law 9)
10. **It is drawn in one coordinate space**, anchored to its home. (the trap)
11. **It is felt in motion** — at least one earned animation on entry, on activity,
    and on result.
12. **It is proven in the Simulator first, then walked on real metal.** Add a
    `#if targetEnvironment(simulator)` env hook to stage its states for screenshots
    (the recorder uses `HS_DESK_RECORD=picker|ambient|intel|desktop`), then deploy to
    the cabled iPad and judge the feel with a real model.

---

## 4. The worked example, end to end

The recorder is the pattern made concrete. The full flow:

1. **Rest.** A 64pt `DioRecordOrb` sits at `orbPos` (bottom-left) with a "Record"
   label. Quiet. (Laws 1, 3)
2. **Intent.** Tap it. `DioRecordModePicker` blooms over the orb: "Start a meeting"
   or "Talk to the desktop". The desk shows through. (Law 4)
3. **Active, ambient.** Pick "Start a meeting". `DioAmbientRecorder` takes over *the
   corner*, not the screen: angled waveform sprawls fan from the mic, a small live
   transcript reads what it hears, a row of intelligence markers waits, a compact
   REC + timer + stop sits at the base, and a single "on device" badge. The desk is
   fully alive behind it. (Laws 1, 2, 3, 8)
4. **Act in place, scoped.** Tap a marker — a built-in lens, or **your** Scout agent,
   or **your** Refine crew (`LiveTarget`). `DioWindowSlider` opens: scope it to the
   last 0:30 to 5:00. "Go". (Laws 5, 7)
5. **While Whisper keeps running.** `fireLive` dispatches to `fireLiveIntel` /
   `fireLiveAgent` / `fireLiveChain`; it slices the transcript window
   (`windowedTranscript` over `liveTimeline` samples) and runs it through the same
   `callLLM` / `agentReply` seam the rest of the desk uses. Recording never pauses.
   (Law 7)
6. **Harvest.** The result floats up as a `DioLiveIntelCard` by the mic. "Keep" drops
   it on the desk as an `OutputRecord` you can route onward. (Law 6)
7. **Gated throughout.** Every step was a tap. (Law 9)

That is the shape. A new component swaps the nouns (mic → camera, transcript →
frames, lenses → filters) but keeps the skeleton.

---

## 5. Anti-patterns we killed (do not bring them back)

- **The Tools dock.** A drawer of square tiles at the screen edge. It was generic,
  it stole space, and a coordinate-space bug made it misalign. We deleted the
  concept, replaced by the **radial summon** (long-press a card, its valid tools
  bloom around your finger). Lesson: tools come *to the work*, the work does not go
  to a drawer.
- **The full-screen recording console.** `DioRecordingConsole` owned the whole
  screen while recording. It violated Law 1 and made recording feel like leaving the
  desk. Replaced by `DioAmbientRecorder`. Lesson: capture is a desk activity, not a
  destination.
- **Silent, one-way output.** Artifacts that "just appear" with no way to grab or
  route them. Every result is now a keepable card (Law 6).

## 6. The traps that will bite you

- **The coordinate-space trap** (see §1): never mix `GeometryReader`-positioned
  overlays with screen-anchored, safe-area-ignoring chrome in the same component.
- **The protocol-dispatch trap** (from the `DeskPrimitive` contract): a facet a
  conformer overrides must be a *protocol requirement*, not extension-only, or it
  dispatches statically to the default through `any DeskPrimitive`.
- **Judging feel from a screenshot.** A static frame cannot carry motion or latency.
  The Simulator proves layout and composition; only the cabled iPad with a real
  model proves the feel. Both, in that order, every time.
