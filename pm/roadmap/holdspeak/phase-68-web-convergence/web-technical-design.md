# The web technical design (HS-68-03)

**Phase:** 68 — Convergence. **Status:** authored 2026-06-22.

How each marquee iPad pattern is actually built in the **web stack** —
Astro 6.3 static build + Alpine.js 3.15 + vanilla ES modules + Open Props + the
"Signal" tokens (`web/src/styles/tokens.css`). No framework swap. This is the
concrete, de-risked build plan that Phase 69's delivery stories are written
from. It consumes HS-68-01 (`design-pattern-catalog.md`) — the catalog's
reuse-vs-new verdicts and the web-wins status palette are taken as given here.

The owner bar carried across (per `current-phase-status.md`): no prose in the
product (the egress **badge**, never reassurance sentences — POSITIONING canon);
premium/native craft; PixelLab for bespoke assets; reduced-motion honored; and
the standing lesson — *the web already runs the same Signal language, so this is
apply + port, not redesign*.

---

## 0. The stack constraints every approach must honor (grounded)

These are facts of the stack, traced, that shape every recommendation below:

- **Static build, FastAPI-served.** Astro builds to `holdspeak/static/_built/`,
  base `/_built`, `format: "directory"`, **intentionally un-minified client**
  (`web/astro.config.mjs:9-41`). There is no SSR, no Node at runtime — pages are
  static HTML + ES modules the FastAPI app serves. Anything "app-wide" must be a
  **component placed in the shell** (`web/src/layouts/AppLayout.astro`) plus a
  vanilla ES module, because the shell must work **with or without Alpine** —
  Alpine loads per-page, not globally (`AppLayout.astro:7-9`, the existing shell
  scripts are deliberately plain IIFEs at `:85-173`).
- **No client-side audio anywhere today.** A repo-wide grep for
  `getUserMedia` / `AudioContext` / `AnalyserNode` / `MediaRecorder` in
  `web/src` and `holdspeak/static` returns **nothing**. Capture is server-side
  (the runtime owns the mic). This is the central constraint for §5 (waveform).
- **The live data bus is the `/ws` WebSocket.** Two consumers exist:
  `presence-app.js` (tiny, framework-free, re-dispatches every frame as a DOM
  `hs-activity` / `hs-broadcast` CustomEvent — `presence-app.js:51, 89-94`) and
  `dashboard-app.js` (Alpine, full message router at `:733`). Message types that
  already flow: `runtime_activity`, `segment`, `intel`, `intel_status`,
  **`intel_token`** (streamed tokens — `dashboard-app.js:756-762`),
  `intel_complete`, `bookmark`, `duration`. This is the data source for §2/§3/§4.
- **Qlippy already exists and is framework-free** (`qlippy.js`) but is
  **mounted only on `/presence`** (`presence.astro:79-81`) and **double-gated**
  on `presence.enabled && presence.mascot` (`qlippy.js:227-238`). It already
  owns the canonical egress badge (`qlippy.js:134-146`).
- **Existing reusable primitives:** `Panel.astro` (raised surface + elev-1 +
  eyebrow header), `Pill.astro`, `Button.astro`, `ListRow.astro`,
  `ConfirmDialog.astro`, `Toolbar.astro`, `TrustChip.astro`. TopNav is
  `position: sticky; top: 0; z-index: var(--z-sticky)` = 10
  (`TopNav.astro:110-113`). Z-scale: sticky 10, overlay 100, dialog 200,
  toast 300 (`tokens.css:211-216`).
- **The "Workflow" model is already canonical and linear.** The engine's
  `Workflow` (`apple/Sources/RuntimeCore/Workbench/Workflow.swift:102-142`) is a
  **Codable linear pipeline**: `source` (one of full-transcript / tacked /
  selection) → ordered `steps[]` (lens / extract / summarize / rewrite / keepIf /
  **custom llmCall**) → one `output` (artifacts / note / slack). It is **not** a
  free graph — the doc comment is explicit: *"a deliberately linear pipeline (not
  a free node graph) so the builder has crushing usability."* The iPad's visual
  node-canvas (`PatchModel`, `MeetingCaptureApp.swift:2004`) is a **presentation
  layer that binds to that linear `Workflow`**. **This is the single biggest
  de-risker in the whole set** — see §1.

---

## 1. The node-graph Workbench (heaviest)

**Goal.** A pannable/zoomable dot-grid canvas with typed draggable node cards
wired by type-colored bezier cables, a node palette, tap-to-inspect, and
run-pulses — reaching the iPad's `GraphCanvasView` bar on the web.

### The reframe that de-risks it (read first)
The canonical runnable model is a **linear `Workflow`** (§0). The free node-graph
is *visual sugar over a linear pipeline*. So the web build does **not** need a
general DAG engine, arbitrary fan-in/fan-out, or cycle detection. It needs:

1. a **typed linear model** mirroring `Workflow` (source → steps → output), and
2. a **canvas renderer** that lays that model out as a left-to-right chain of
   node cards joined by cables, with drag-to-reorder and the custom-`llmCall`
   node editable inline.

This is a *layout + interaction* problem over a known, validated, serializable
shape — not a graph-engine problem. Treat "free wiring" as a later, optional
enhancement; ship the linear builder first.

### Recommended approach: **SVG cables + HTML/CSS node cards in one transformed world layer** (pure vanilla, no lib)

A single `.wb-world` container holds two siblings:
- an absolutely-positioned **`<svg>` cable layer** (the bezier wires), and
- **HTML node cards** (real DOM — they reuse the §6 depth-card primitive, the
  glyph chip, and get focus/keyboard/`aria` for free).

Pan/zoom is **one CSS transform on `.wb-world`**:
`transform: translate(panX, panY) scale(z)`. Nodes store **world coordinates**;
the transform maps world→screen. Cables are drawn in **world space** inside the
SVG (which shares the same transform), so wires and nodes never desync.

**Why SVG cables + DOM nodes (not `<canvas>`, not a lib):**
- **DOM nodes = free accessibility + reuse.** Node cards are the same depth
  cards as everywhere else; they get real focus rings, `aria-label`, tab order,
  and tap-to-inspect via a normal click handler. A `<canvas>` build would force
  re-implementing all of that and hit-testing by hand.
- **SVG `<path>` beziers are trivial and match the iPad cable math 1:1.** The
  iPad's `cablePath` is a horizontal-tangent cubic with control offset
  `max(46, |dx|·0.45)` (`MeetingCaptureApp.swift:1989-1995`). That is one SVG
  `d="M x0 y0 C ..."` string per edge — port the exact formula. Type color =
  `stroke: var(--accent)` / `var(--info)` / `var(--ok)` at 0.85 opacity.
- **Un-minified, readable, framework-free** matches the repo's stated stance
  (`astro.config.mjs:21-40`) and the Qlippy/presence precedent.
- **Performance is a non-issue** at this scale: a meeting workflow is a handful
  of nodes, not a 500-node ETL graph. SVG handles dozens of nodes fluidly.

**Pan/zoom/drag in vanilla JS (Pointer Events, the standard hit-test-free path):**
- **Pan:** `pointerdown` on empty canvas → track deltas → update `panX/panY` →
  rewrite the world transform. `setPointerCapture` so a drag that leaves the
  element keeps tracking.
- **Zoom:** `wheel` (ctrl/⌘ or plain, owner's call) → adjust `z` about the
  cursor: convert cursor to world coords, scale, re-translate so the point under
  the cursor stays put. Clamp `z ∈ [0.4, 2.0]`.
- **Node drag:** `pointerdown` on a node → `pointermove` deltas **÷ z** (screen
  px → world px) → update that node's world `x/y` → re-layout its cables.
  Hit-testing is **free** — it is a DOM element, the browser routes the event.
- **Port wiring (the optional enhancement):** `pointerdown` on a port dot starts
  a "live cable" following the cursor; `pointerup` over a compatible input port
  commits an edge. Compatibility reuses the iPad's `PortType` rules
  (`MeetingCaptureApp.swift:2033`). For the **linear-first** slice, wiring is
  implicit (each step reads the previous), so this is deferred.

**Where the model lives & how it maps to `Workflow`.** A vanilla module
`web/src/scripts/workbench/model.js` holds a plain JS object that is the **exact
shape of the engine `Workflow` JSON**: `{ id, name, source, steps:[...], output }`
where each step is `{ kind: "lens"|"extract"|"summarize"|"rewrite"|"keepIf"|"llmCall", ... }`.
Serialize/deserialize is `JSON.stringify` of that object — **byte-compatible with
`Workflow`'s Codable form** (`Workflow.swift:102`), so a web-built workflow and an
iPad-built one are the same artifact. Persistence: `POST` to a runtime endpoint
(parity with the iPad's `WorkflowStore`, `MeetingCaptureApp.swift:1784`) or, for
the first slice, `localStorage` under `hs.workflows.v1` (the iPad's exact key).
The renderer is a pure function `model → DOM` (re-render on change), Alpine-free
to match the canvas's interaction-heavy nature; Alpine may wrap the *page chrome*
(palette, save button) but the canvas itself is vanilla.

**Files to add:**
- `web/src/pages/workbench.astro` — the page shell (uses `AppLayout`, adds a
  `workbench` route to the `Route` union in `AppLayout.astro:18` + `TopNav`).
- `web/src/scripts/workbench/model.js` — the `Workflow`-shaped model + presets
  (port `WorkflowPresets.all`, `Workflow.swift:146-162`) + `plan` string
  (`Workflow.swift:123`).
- `web/src/scripts/workbench/canvas.js` — pan/zoom/drag, the SVG cable layer,
  the dot-grid, render loop.
- `web/src/components/workbench/NodeCard.astro` (or a JS render fn) — the node
  card built on the §6 depth primitive + glyph chip + typed port dots.
- Dot grid: a CSS `background-image: radial-gradient(var dots)` on `.wb-world`
  with `background-size` = 34px·z (the iPad's 34pt step,
  `MeetingCaptureApp.swift:2289-2306`), so the grid pans/zooms with the world for
  free — **no per-dot DOM**.

**Data source.** Static (the user composes); on **run**, the workflow JSON is
POSTed to the runtime, and run-pulses are driven by the existing `intel_status` /
`intel_token` WS frames (§4 shares this).

**Reduced-motion / a11y.** Node cards are focusable; arrow-key nudge + Enter to
inspect. Run-pulse cable animation is CSS and dies under the global
`prefers-reduced-motion` block (`tokens.css:219-234`). Pan/zoom has a "fit"
button so it is operable without a trackpad gesture.

**Main risk + de-risk.** *Risk:* over-building a general graph engine and
drowning in pointer-math/hit-testing. *De-risk — smallest proof first:* a
**read-only linear renderer** — take a preset `Workflow` from `model.js`, render
it as a horizontal chain of static node cards joined by SVG beziers on a dot
grid, with **pan + zoom only** (no node drag, no wiring). That proves the world
transform, the cable math, and the depth cards in one screenshot. Then add node
drag-to-reorder (still linear), then the inspector, then *optionally* free port
wiring as a separate story. This sequences naturally into a Phase-69 epic.

**Owner decision needed:** **pure-vanilla SVG (recommended) vs. add a tiny
canvas/graph lib.** Recommendation: **pure vanilla** — the linear reframe makes a
lib unnecessary, it keeps the un-minified/framework-free stance, and it avoids a
dependency for a feature that is mostly CSS-transform layout. A lib
(e.g. a Svelte-Flow-style package) would buy free wiring/minimap at the cost of a
heavy dep + a framework mismatch (most are React). **Flagged, not silently
picked.**

---

## 2. The app-wide Queue HUD

**Goal.** A Dynamic-Island-style collapsed pill under the nav that expands into a
live per-job ledger, present on **every** page (the iPad `QueueHUD` mounted at app
root, `MeetingCaptureApp.swift:36`).

**Recommended approach: a shell component in `AppLayout.astro` + a shared vanilla
store fed by the WS, Alpine-free.** Because the shell must not depend on Alpine
(`AppLayout.astro:7-9`), the HUD is a small ES module with its own tiny reactive
store — exactly the Qlippy/presence pattern. It subscribes to the **existing
`/ws`**: it can either open its own socket (like `presence-app.js`) or, cleaner,
**listen for the `hs-broadcast` DOM event** that `presence-app.js` already
re-dispatches for every frame (`presence-app.js:92-94`) — but that only fires on
`/presence`. So the robust choice is the HUD **owns a thin shared socket module**
(`web/src/scripts/runtime-bus.js`) that any shell component (HUD, future Qlippy)
subscribes to, so we don't open N sockets per page.

**The store (the missing `RunQueueStore`).** Port the iPad model
(`MeetingCaptureApp.swift:2605-2628`): a `jobs[]` map keyed by job id, each
`{ workflow, step, target, status, progress, note }`; ordering ranks
**working → blocked → queued → done → failed**; the live count = working +
queued + blocked. Status vocabulary maps **1:1 to the web tokens** (catalog §3):
`working`→`--accent`+bolt, `blocked`→`--warn`+pause, `done`→`--ok`+check,
`failed`→`--danger`+octagon, `queued`→`--text-faint`+hourglass
(`tokens.css:54,61,67,118,50`). Per the web-wins palette decision, these are the
canonical colors.

**Data source.** The WS frames already carry this: `runtime_activity` (state +
detail), `intel_status` (queued/running/ready/failed — `dashboard-app.js:752`),
`intel_token`/`intel_complete` (progress signal). The HUD synthesizes "jobs" from
these. If a richer per-job feed is wanted later, a `runtime_queue` message type is
an additive backend story (note for Phase 69 / the parity backlog, not built
here). For v1, derive jobs from the existing frames — **no backend change**.

**Pill → ledger.** Collapsed pill = a `backdrop-filter: blur()` capsule on
`--surface-2` (the catalog's mapping of `.ultraThinMaterial`) on the top-lit
hairline, with a pulsing beacon in the most-urgent status color (reuse
`hs-pulse`, `global.css:97`) + a summary count + a blocked chip. Click expands
into a `Panel`-style ledger (radius-lg, `--elev-3`) with per-job rows: a status
orb, an **accent-gradient progress bar** (`--accent-gradient` — added per catalog
drift decision #2), an origin/target chip (On-device / Endpoint), and the
blocked-auto-resume footnote.

**Coexistence with nav.** TopNav is `sticky; top:0; z-index:10`
(`TopNav.astro:110-113`). Mount the HUD `position: fixed; top: <nav height>;`
centered, `z-index: var(--z-overlay)` (100) so it floats above content but below
dialogs (200). It rides in `AppLayout.astro` right after the `<TopNav>` block so
every route gets it. It must **not** collide with the mobile nav toggle — on
narrow widths, dock it as a slim bar rather than a centered island.

**Files:** `web/src/components/QueueHud.astro` (markup + scoped CSS),
`web/src/scripts/queue-hud.js` (store + render), `web/src/scripts/runtime-bus.js`
(shared socket), one mount line in `AppLayout.astro`. Gate it behind a config flag
initially (like Qlippy) so it ships dark until proven.

**Reduced-motion / a11y.** Pill is a `<button aria-expanded>`; ledger is a
labelled region with `aria-live="polite"` for status changes. Beacon pulse +
progress shimmer die under the global reduced-motion block.

**Main risk + de-risk.** *Risk:* **N sockets** — naively opening a `/ws` per shell
component (HUD + Qlippy + the page's own dashboard socket). *De-risk:* the shared
`runtime-bus.js` is the smallest first proof — one socket, a pub/sub, the HUD as
its first subscriber; verify a single connection in devtools before adding Qlippy
(§4) as a second subscriber. Second risk: synthesizing fake jobs from coarse
frames looks wrong — de-risk by shipping the **idle/empty pill first** (it
correctly shows "nothing running"), then map one real job type (intel) end-to-end.

---

## 3. The generation theater

**Goal.** The "model thinking" visualization while intelligence streams: a
breathing/rotating orb in concentric accent rings + a shimmer arc, above a
**constellation** of target artifact types that light up pending → in-flight →
done (the iPad `GenerationTheater`, `MeetingCaptureApp.swift:4526-4614`).

**Recommended approach: pure CSS/SVG keyframes driven by the existing
`intel_*` WS stream; no `<canvas>` for v1.** The orb is achievable with stacked
absolutely-positioned elements:
- 3 concentric rings = 3 `<div>`s with `border: 2px solid var(--accent)` +
  staggered `@keyframes` pulse (`easeInOut 1.7s` — port the iPad timing) on
  `--ease-standard`.
- the bloom = a blurred radial-gradient circle (`filter: blur()`).
- the core = the **`theaterorb` PixelLab sprite** (catalog §9: iPad-only today,
  **must be exported for the web** — a dependency, generate via PixelLab per the
  owner bar) on a `linear 9s` rotation + a slow breathing `scale`.
- the shimmer arc = an SVG `<circle>` with `stroke-dasharray` trimmed to an arc,
  on a `1.2s` rotation, in an accent angular feel.

**The constellation.** A row of per-type pills (reuse `Pill.astro` shape): state
machine `pending` (dim, `--surface-2`) → `in-flight` (glowing, ringed, tinted,
`scale(1.07)`) → `done` (filled in the type tint + a check). Spring-settle maps to
`--ease-standard` (`tokens.css:202`). The artifact-type set comes from
`Workflow.producedTypes(...)` (`Workflow.swift:129-141`) so the constellation
previews exactly what this run will surface — *the same source the canvas (§1)
uses*.

**Data source.** The live `intel` pipeline already streams over `/ws`:
`intel_status` flips the theater on (`state: running/live`), **`intel_token`**
frames are the heartbeat that drives "in-flight" shimmer (`dashboard-app.js:756`),
and `intel`/`intel_complete` flips each type to `done`
(`dashboard-app.js:748,764`). No new backend.

**No prose.** The iPad theater carries a prose honesty line ("Running on this
iPad · no network", `MeetingCaptureApp.swift:4552`) — the **pre-badge idiom**. On
the web this is **forbidden** (POSITIONING). Use the **egress badge** (§6 / §4
Qlippy) instead: one `q-egress`-style chip, no sentence.

**Files:** a `web/src/components/GenerationTheater.astro` + a small driver in the
page that already owns the intel socket (the meeting/dashboard view), plus the
`theaterorb` asset under `holdspeak/static/_built/` (mirrors the Qlippy asset
path, `qlippy.js:21-22`).

**Reduced-motion.** The orb rotation/breathing/shimmer and the constellation
spring all die under the global reduced-motion block; the **reduced path** is a
static orb + the constellation still flips state (instant, no scale/glow) so the
*information* (what's being produced) survives motion-off. Gate the whole orb
animation on a `matchMedia('(prefers-reduced-motion: reduce)')` check too, since
some of it is JS-timed.

**Main risk + de-risk.** *Risk:* it gates on **two** dependencies — a streaming
intel UX *and* a web orb asset — so it can stall. *De-risk:* build the
**constellation first, orb second**. The constellation is pure tokens (no asset),
proves the `intel_*`→state wiring end-to-end, and is the *informative* half. Ship
it driven by a real `.43`-style intel run (per the standing "prove on real metal"
lesson), then drop in the orb sprite as a cosmetic upgrade. That removes the
asset from the critical path.

---

## 4. Qlippy into the cockpit

**Goal.** Lift Qlippy's dock + cards + egress badge out of `/presence`-only into
the **main browser cockpit** (every route), without breaking the frameless
`/presence` HUD that also uses `qlippy.js`.

**Recommended approach: move the Qlippy DOM + script mount from `presence.astro`
into `AppLayout.astro`, behind its existing double gate.** `qlippy.js` is already
framework-free and self-gating (`qlippy.js:227-238` — it stays fully hidden unless
`presence.enabled && presence.mascot`), so mounting it in the shell is **safe by
construction**: on a page where the flags are off, every node stays `hidden` and
no listener fires (the file's own contract, `qlippy.js:7-9`).

**The one real coupling to fix.** `qlippy.js`'s activity dock listens for the DOM
`hs-activity` event, which is **dispatched only by `presence-app.js`**
(`presence-app.js:51`) — and `presence-app.js` runs only on `/presence`. So on
cockpit pages today there is no `hs-activity` source. Fix: have the shared
**`runtime-bus.js`** (§2) re-dispatch `hs-activity` / `hs-broadcast` from the
single shell socket, exactly as `presence-app.js` does, and load it in the shell.
Then both Qlippy (cockpit) and the frameless presence HUD get fed; `/presence`
keeps its own `presence-app.js` (which is also the presence *ring* renderer, not
just the bus) so **nothing on `/presence` regresses** — the bus is additive.

**Egress badge comes along for free.** Qlippy already renders the canonical
`{scope,label}` badge (`qlippy.js:134-146`), and the CSS lives inline in
`presence.astro:280-302`. Lifting Qlippy into the shell means **extracting that
egress CSS into a shared place** (a `q-egress` rule in `global.css` or a tiny
component) so cockpit cards render it. This is the catalog §6 obligation — "pull
the badge into the cockpit" — satisfied as a side effect.

**Files:** move the `#qlippy` markup block (`presence.astro:49-76`) into
`AppLayout.astro` (after `<main>`); load `qlippy.js` + `qlippy-events.js` +
`runtime-bus.js` in the shell; extract `.q-egress` (and the dock/card CSS) from
`presence.astro` into `global.css` / a shared style; have `/presence` stop
double-mounting (it keeps `presence-app.js` for the ring + bus, the shell provides
Qlippy).

**Reduced-motion / a11y.** Unchanged — `qlippy.js` already crossfades-only and
pauses sprite loops under reduced motion (`qlippy.js:17-18`), and has an
`aria-live` announcer (`qlippy.js:53,168`).

**Main risk + de-risk.** *Risk:* **double-mount / double-socket on `/presence`**
(both the shell and the page mounting Qlippy or opening `/ws`). *De-risk:* the
smallest proof is a **single page (the dashboard) with Qlippy mounted from the
shell**, verified to (a) show a card on a real activity frame and (b) open exactly
one socket; then migrate `/presence` to consume the shell mount. Guard the gate:
screenshot a flags-**off** cockpit page to confirm Qlippy is invisible (the
`/presence`-equals-ring-only contract still holds, `qlippy.js:7-9`).

---

## 5. The reactive mic waveform

**Goal.** A voice-dominant level meter (perceptual gain + per-bar wobble + peak
glow) — the iPad `MicWaveform` (`MeetingCaptureApp.swift:3438-3466`).

**The blocking question, answered: where is the audio?** Today **the browser has
no audio stream** (§0 — zero `getUserMedia` in the codebase; capture is
server-side). So there are two genuinely different builds, and the right one is an
**owner/orchestrator decision** because it changes the data source:

**Option A — client mic via Web Audio (the iPad-faithful build).** If/when a
cockpit surface captures audio in the browser (`navigator.mediaDevices.getUserMedia`),
wire a Web Audio graph: `MediaStreamSource → AnalyserNode`, then a
`requestAnimationFrame` loop reading `getByteTimeDomainData` (or frequency data)
to drive a row of bars on an SVG/`<canvas>`. Port the iPad math exactly:
perceptual gain `amp = min(1, pow(level, 0.62))` (`MeetingCaptureApp.swift:3446`),
per-bar wobble × center bias × `amp`, a vertical `accent → accent .5` bar gradient
(`--accent` / `--accent-glow`, `tokens.css:54,58`) with a peak glow. This is the
real waveform. **Cost:** it requires a browser capture path that does not exist
yet — a feature dependency, possibly a new product surface.

**Option B — level over the WS (the no-new-capture build).** If the runtime
emits a periodic audio **level** value on `/ws` (a small `audio_level` frame —
an additive backend story, not built here), the web renders the *same bar
visualization* driven by that scalar instead of a local `AnalyserNode`. No browser
mic, no permission prompt, works with the existing server-side capture. **Cost:** a
small backend addition + it is a level meter, not a true spectral waveform.

**Recommendation:** present both; **lean Option B** for parity with the
server-side-capture reality (it is honest about where audio lives and needs no new
browser capture surface), and reserve Option A for a future surface that genuinely
captures in-browser. **Flagged for owner — do not silently pick**, because A
implies a new capture surface and a mic-permission UX.

**Files (either option):** `web/src/components/MicWaveform.astro` (the bars + CSS)
+ `web/src/scripts/waveform.js` (the rAF render loop; the *source* swaps between
`AnalyserNode` (A) and a WS level subscription via `runtime-bus.js` (B)). Render
target: `<canvas>` is the right call **here specifically** — it is a per-frame
numeric viz with no per-element semantics, so canvas is cheaper than 16–32
animated DOM bars and there is nothing to make accessible per-bar.

**Reduced-motion / a11y.** A waveform is decorative; under reduced motion, freeze
to a flat baseline. Pair it with a text/`aria` "Listening" state (the presence
label already exists) so motion-off users aren't told *less*.

**Main risk + de-risk.** *Risk:* building Option A and discovering there is no
in-browser capture surface to attach to (dead end). *De-risk:* decide A-vs-B
**before** building; then the smallest proof for B is rendering the bars off a
**faked level oscillator** (a sine in JS) to nail the gain/gamma/peak-glow visual,
then swap the source to the real WS frame — the visual is proven independent of
the data wiring.

---

## 6. The motion / depth uplift

**Goal.** Apply the under-used `--elev-*` / `--ease-standard` tokens broadly, add
the missing **gradient top-lit hairline**, a shared **depth-card primitive**, a
new **`hs-materialize`** keyframe, and a **stagger helper** — so §1–§4 ride a
consistent, alive surface (catalog §1 + §8).

**Recommended approach: additive CSS only — one card class + two keyframes + a
few tokens.** No JS, no architecture. Concretely:

1. **Add the drift tokens** (catalog decisions #1–#3, low-risk additive) to
   `tokens.css`: `--accent-gradient` (`#FF9D5C → #FF6B35 → #F24A2E`, the iPad
   `accentGradient`, `MeetingCaptureApp.swift:416-418`) and `--bg-gradient`
   (`#191B23 → #0E0F13`, `:410-413`). Per the **web-wins** status-palette
   decision (`current-phase-status.md`), the existing `--ok/--warn/--danger/--info`
   stay canonical — no change.
2. **The gradient top-lit hairline + depth card.** Today `--elev-1` carries a
   **flat** `inset 0 1px 0 white .04` (`tokens.css:192`) — dimmer and
   non-directional vs the iPad's `white .12 → .035` gradient border
   (`MeetingCaptureApp.swift:425-427`). Add a **`.signal-card`** utility class
   that composes: `background: var(--surface-1)`, `border-radius: var(--radius-5)`,
   `box-shadow: var(--elev-2)`, **plus the gradient hairline** via a
   `border-image` or a `::before` 1px inset gradient ring (top brighter). This is
   the one primitive the whole cockpit adopts; it makes every surface "catch
   light" like the iPad in one move. Add a sibling **`.glyph-chip`** (a
   `--accent-gradient`-filled rounded-rect icon container, radius = size·0.28 per
   `MeetingCaptureApp.swift:452-463`) and a **`.is-pressable`** (`:active { transform: scale(.98) }`
   on `--ease-standard` — the catalog notes web spec is .98 vs iPad .975, cosmetic).
3. **`@keyframes hs-materialize`** in `global.css` (next to `hs-pulse`,
   `global.css:97`): glow + insert (opacity 0→1, `translateY(6px)→0`, a brief
   `box-shadow` accent-glow that settles) on `--ease-standard`, applied to cards
   as they arrive (intel results, history rows, queue jobs).
4. **A stagger helper:** a tiny utility — either a `[style*="--i:"]` pattern with
   `animation-delay: calc(var(--i) * 40ms)`, or a one-line JS that sets
   `--i` on inserted children — so lists materialize in sequence, not all at once.

**Where to apply.** The `.signal-card` primitive replaces ad-hoc card CSS on the
high-traffic cockpit surfaces (history rows, intel cards, the dashboard meeting
card), and is the base class for §1's node cards, §2's ledger rows, §3's
constellation pills, and §4's Qlippy card.

**Files:** `tokens.css` (the 2 gradient tokens), `global.css` (the `.signal-card`
/ `.glyph-chip` / `.is-pressable` utilities + `hs-materialize` + the stagger
helper). All additive; nothing removed.

**Reduced-motion / a11y.** `hs-materialize` and the stagger die under the global
reduced-motion block (`tokens.css:219-234`) — items still appear, just instantly.
The depth/hairline/glyph-chip are static (motion-independent), so the *craft*
survives motion-off; only the entrance animates.

**Main risk + de-risk.** *Risk:* the gradient hairline via `border-image` renders
inconsistently across the corner radius (a known CSS papercut). *De-risk:* prove
the hairline on **one card in isolation** first (a `::before` inset gradient ring
is the more reliable technique than `border-image` for rounded corners) and
screenshot it before rolling `.signal-card` across the cockpit. This is the
cheapest, highest-leverage item — it should land first (it is the substrate §1–§4
ride on).

---

## Cross-cutting: the one shared dependency

Three of the six (§2 Queue HUD, §4 Qlippy-in-cockpit, optionally §5-Option-B)
need **live WS data in the shell, framework-free, one socket**. Build
**`web/src/scripts/runtime-bus.js`** once — a single `/ws` connection that
re-dispatches `hs-activity` / `hs-broadcast` (mirroring `presence-app.js:89-94`)
and exposes a `subscribe(type, fn)` pub/sub. Every shell-level live component
subscribes to it. This is the connective backbone of the convergence and should be
an **early Phase-69 story** (it unblocks §2 and §4).

---

## Build-order recommendation (input to Phase 69 sequencing)

1. **§6 the depth/motion uplift** — cheapest, highest leverage, the substrate.
2. **`runtime-bus.js`** (shared socket) — unblocks the live shell components.
3. **§4 Qlippy-into-cockpit** — mostly placement; pulls the egress badge in (a
   POSITIONING obligation); proves the bus.
4. **§2 Queue HUD** — second bus subscriber; always-on glanceable craft.
5. **§3 generation theater** — constellation first (tokens only), orb second.
6. **§1 the Workbench** — the heavy epic; read-only linear renderer first, then
   drag, then inspector, then optional free wiring.
7. **§5 waveform** — after the A-vs-B owner decision; gated on a capture source.

---

## Open decisions for the owner / orchestrator (collected)

1. **§1 Workbench: pure-vanilla SVG (recommended) vs. a tiny canvas/graph lib.**
   The linear-`Workflow` reframe makes vanilla viable and keeps the
   framework-free/un-minified stance; a lib buys free wiring/minimap at a heavy
   dep + framework-mismatch cost. **Recommend vanilla.**
2. **§5 waveform: Option A (client `getUserMedia` + `AnalyserNode`) vs.
   Option B (a server `audio_level` WS frame).** A needs a new in-browser capture
   surface + mic-permission UX that does not exist today; B needs a small additive
   backend frame and matches the server-side-capture reality. **Recommend B**,
   with A reserved for a future in-browser capture surface.
3. **§2 Queue HUD job feed:** derive jobs from existing `intel_*`/`runtime_activity`
   frames (v1, no backend change) vs. add a richer `runtime_queue` message type
   (a later additive backend story). **Recommend derive-first.**

(All three are flagged per the brief — none silently chosen.)
