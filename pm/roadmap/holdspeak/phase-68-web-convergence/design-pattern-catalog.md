# The cross-platform design-pattern catalog (HS-68-01)

**Phase:** 68 — Convergence. **Status:** authored 2026-06-22.

The single specification of the iPad Swift app's shipped design patterns, named and
defined platform-neutrally, each mapped onto the **existing** web "Signal" token system
(`web/src/styles/tokens.css`, Phase 30). It tells Phase 69 what the web already has vs
what is genuinely new. The web-side anchor it extends is
`pm/roadmap/holdspeak/phase-30-ui-ux-overhaul/evidence/design-language-signal.md`.

Every concrete claim cites `file:line`. Swift source is
`apple/App/MeetingCaptureApp.swift` (4,942 lines, one file). Web source is
`web/src/styles/{tokens,global}.css` plus `web/src/components/` and `web/src/scripts/`.

The headline finding: **the two platforms already share the Signal language byte-for-byte
at the foundation.** The iPad `Sig` palette (`apple/App/MeetingCaptureApp.swift:387-401`)
and the web tokens (`web/src/styles/tokens.css:40-54`) are the *same* hex values — same
accent `#FF6B35`, same surface ramp `#0E0F13 / #15171D / #1C1F27 / #242833`, same text
ramp. So convergence is **apply + port the higher-order patterns**, not a re-theme. The
drift that exists is in the second-tier tokens (status greens/ambers, elevation shadow
values, the top-lit hairline), tabulated in the final section.

---

## 1. Signal depth — the elevated card system

**What it is.** The shared depth treatment every surface in the app uses: a layered
fill, a **top-lit hairline** (a 1px border that is brighter at the top edge so cards
catch light like glass), a soft drop shadow, a **glyph chip** (a gradient-filled rounded
icon container), and a **pressable** scale-on-press feedback. One card modifier, applied
everywhere, so elevation is consistent and never random shadow values.

**Rules.**
- Palette: `Sig` — `bg #0E0F13`, `s1 #15171D`, `s2 #1C1F27`, `s3 #242833`, `text #F2F3F5`,
  `muted #9BA2B0`, `faint #767E8D`, `accent #FF6B35`
  (`apple/App/MeetingCaptureApp.swift:387-401`).
- Card: layered fill + top-lit hairline + shadow `black 0.38 / radius 16 / y 9` when
  elevated; default radius 18 (`apple/App/MeetingCaptureApp.swift:433-449`, the
  `SignalCard` modifier + `.signalCard()` extension).
- Top-lit hairline: a vertical gradient `white 0.12 → white 0.035`, top to bottom
  (`apple/App/MeetingCaptureApp.swift:425-428`, `Sig.topHairline`).
- Gradients: `bgGradient` (cinematic vertical wash `#191B23 → #0E0F13`),
  `accentGradient` (amber→ember diagonal `#FF9D5C → #FF6B35 → #F24A2E`), `localGradient`
  (cobalt diagonal `#7AA6FF → #5B8DEF`)
  (`apple/App/MeetingCaptureApp.swift:409-423`).
- Glyph chip: a gradient rounded rect (corner radius = size × 0.28) + a soft shadow +
  a white SF Symbol; default 46pt (`apple/App/MeetingCaptureApp.swift:452-463`).
- Press: `scale(0.975)` + `opacity 0.94` on a spring `response 0.3 / damping 0.7`
  (`apple/App/MeetingCaptureApp.swift:466-474`, `PressableCard` button style).

**Swift source.** `enum Sig` (`:387`), `Sig` depth extension incl. `topHairline` (`:409-428`),
`struct SignalCard` + `func signalCard` (`:433-449`), `struct GlyphChip` (`:452-463`),
`struct PressableCard` (`:466-474`).

**Web mapping (exists).**
- Surfaces: `--bg / --surface-1 / --surface-2 / --surface-3`
  (`web/src/styles/tokens.css:40-43`) — identical hexes.
- Text: `--text / --text-muted / --text-faint`
  (`web/src/styles/tokens.css:48-50`) — identical hexes.
- Accent + glow: `--accent #FF6B35`, `--accent-glow`, `--accent-tint`
  (`web/src/styles/tokens.css:54-58`) — identical accent.
- Elevation: `--elev-1` carries the same idea (`0 1px 2px black .40, inset 0 1px 0
  white .04`), `--elev-2/3/4` are the deeper steps
  (`web/src/styles/tokens.css:191-196`).
- Glow on the live moment: `--glow-accent` (`web/src/styles/tokens.css:196`).

**Reuse-vs-new verdict.** **Reuse, under-applied.** The tokens are all present and equal.
What is missing is the *single shared card primitive*: Swift has one `.signalCard()`
modifier; the web has elevation tokens but **no** `--elev-*`-driven `.signal-card` utility
class and **no** gradient-hairline border. The web's `inset 0 1px 0 white .04` in `--elev-1`
is a flat top highlight, not the iPad's brighter `white .12 → .035` gradient hairline. A
small new web primitive (one CSS class composing surface + the gradient hairline + elevation
+ a `.glyph-chip`) would let every surface match the iPad in one move. The `GlyphChip` and
`PressableCard` have **no** dedicated web equivalents (icons today sit in ad-hoc containers).

**Port-priority: HIGH.** This is the substrate every other pattern rides on; one card
primitive lifts the felt quality of the whole cockpit at once.

---

## 2. The node-graph Workbench

**What it is.** A visual builder: typed, draggable node cards on a pannable/zoomable
**dot-grid canvas**, wired together by **type-colored bezier cables**, with a node palette,
tap-to-inspect, and run-pulses. The user composes a meeting-intelligence workflow by
dragging primitives (sources → intelligence → transforms → outputs) and connecting ports.

**Rules.**
- Port types and colors: `signal` = cobalt (`Sig.local #5B8DEF`), `text` = amber
  (`Sig.accent #FF6B35`), `findings` = green (`Sig.ok #3ECF8E`)
  (`apple/App/MeetingCaptureApp.swift:1809-1817`, `enum PortType`). (Note the spec's
  "amber" for text resolves to the brand accent.)
- Node categories drive port topology: SOURCE / INTELLIGENCE / TRANSFORM / OUTPUT, each
  with fixed inputs/outputs (`apple/App/MeetingCaptureApp.swift:1819-1868`).
- Cable: a horizontal-tangent cubic bezier, control offset `max(46, |dx|·0.45)`
  (`apple/App/MeetingCaptureApp.swift:1989-1995`, `cablePath`); drawn at 0.85 opacity in
  the port-type color (`:2164-2178`).
- Dot grid: 34pt step, 1.3pt dots at `white 0.05`, hit-testing disabled
  (`apple/App/MeetingCaptureApp.swift:2289-2306`, `struct DotGrid`).
- Node card: a Signal card (radius 17) with a typed `GlyphChip`, a title, a category
  eyebrow, colored I/O port dots (13pt, ringed in `Sig.bg`, glowing in the port color),
  selected state = a 2px accent stroke + an accent shadow + a delete affordance
  (`apple/App/MeetingCaptureApp.swift:2309-2363`, `struct NodeCardView`).
- Model: `PatchModel` holds nodes + edges, validates port compatibility, and drives wiring
  (`apple/App/MeetingCaptureApp.swift:2004-2063`).

**Swift source.** `enum PortType` (`:1809`), `NodeKind` topology (`:1822-1868`), `cablePath`
(`:1989`), `PatchModel` (`:2004`), `struct GraphCanvasView` (`:2065`), the cable layer
(`:2160-2185`), `struct DotGrid` (`:2289`), `struct NodeCardView` (`:2309`).

**Web mapping (none).** The web has **no** node graph, **no** drag interactions, **no**
canvas. The reusable raw material: the Signal surface tokens for the node cards, `--accent`
/ `--info` (`--local`) / `--ok` for the three port colors (`web/src/styles/tokens.css:54,
61, 141`), and `--accent-glow` for the wire/run glow.

**Reuse-vs-new verdict.** **New (the largest new build).** Tokens cover the *styling* of a
node and a cable, but the entire interaction layer (SVG/canvas dot grid, pointer-driven
pan/zoom, draggable nodes, bezier wiring with hit-testing, a palette, an inspector trigger)
is net-new in the web stack. HS-68-03 owns the build approach; this is the marquee port.

**Port-priority: HIGH** (craft impact), but it is the heaviest item — likely sequenced as a
multi-story epic in Phase 69 rather than a single port.

---

## 3. The Queue HUD

**What it is.** An app-wide floating job ledger: a collapsed **Dynamic-Island-style pill**
under the status bar that expands into the full panel of what the machine is doing right
now. It lives at the app root, above every screen.

**Rules.**
- Status vocabulary: `queued / working / blocked / done / failed`, each with a label,
  color, and glyph — `working` = accent + bolt, `blocked` = warn + pause, `done` = ok +
  check, `failed` = bad + octagon, `queued` = faint + hourglass
  (`apple/App/MeetingCaptureApp.swift:2568-2588`, `enum JobStatus`).
- Job model: workflow + step + **target** ("On-device" / "Endpoint") + status + progress
  (0…1) + an optional note (e.g. "endpoint down · retry 3/4 · auto-resumes")
  (`apple/App/MeetingCaptureApp.swift:2591-2603`, `struct QueuedJob`).
- Store: ordering ranks working → blocked → queued → done → failed; live count = working +
  queued + blocked (`apple/App/MeetingCaptureApp.swift:2605-2628`, `RunQueueStore`).
- Collapsed pill: an `.ultraThinMaterial` capsule with a pulsing beacon (the most urgent
  status), a summary, a blocked-count chip, on `topHairline`
  (`apple/App/MeetingCaptureApp.swift:2651-2672`).
- Expanded panel: a Signal card (radius 24), per-job rows with a status orb, an
  accent-gradient **progress bar**, an origin/target chip, and a blocked-auto-resume
  footnote (`apple/App/MeetingCaptureApp.swift:2675-2748`).

**Swift source.** `enum JobStatus` (`:2568`), `struct QueuedJob` (`:2591`),
`RunQueueStore` (`:2605`), `struct QueueHUD` (`:2631`, pill `:2651`, panel `:2675`,
`jobRow` `:2710`). Mounted at the app root (`:36`).

**Web mapping (none as a HUD).** No app-wide queue HUD exists. But the web already has the
**status vocabulary tokens** that map one-to-one onto `JobStatus`:
`--accent` (working), `--warn` (`#FBBF24`, blocked/queued), `--ok` (`#34D399`, done),
`--danger` (`#F87171`, failed), `--text-faint` (queued/idle)
(`web/src/styles/tokens.css:54, 61, 67, 50, 118`). It also has a `Pill.astro` component
(`web/src/components/Pill.astro`) and per-surface WebSocket state in `dashboard-app.js`
that can feed real jobs.

**Reuse-vs-new verdict.** **New shell, reused tokens + data.** The status colors, the pill
primitive, and live WS state all exist; the **app-wide floating HUD container, the
collapse/expand pill, the per-job ledger row, and the progress bar** are net-new. It needs
a shared front-end store (the web has no `RunQueueStore` equivalent — state today is
per-page). Translucent material maps to a `backdrop-filter` blur on `--surface-2`.

**Port-priority: HIGH.** It is glanceable, always-on craft that makes the web feel like a
live operations surface; medium build size.

---

## 4. The generation theater

**What it is.** The "model thinking" visualization shown while intelligence is produced: a
**bespoke plasma orb** (a PixelLab asset) breathing and rotating inside concentric accent
rings + a sweeping shimmer arc, above a **constellation** of the target artifact types that
light up as each is produced (pending → in-flight → done).

**Rules.**
- Orb: 3 concentric accent rings pulsing `easeInOut 1.7s` staggered, a blurred bloom, the
  `theaterorb` pixel asset spinning `linear 9s` + breathing, and a trimmed angular-gradient
  shimmer arc spinning `1.2s` (`apple/App/MeetingCaptureApp.swift:4569-4593`).
- Constellation: per-type pills — pending (dim, `Sig.s2`), in-flight (glowing, ringed,
  tinted, scaled 1.07), done (filled in the type tint + a check), animated on a spring
  `response 0.4 / damping 0.7` (`apple/App/MeetingCaptureApp.swift:4596-4614`).
- Background: a radial accent wash `accent 0.12 → clear` from the top
  (`apple/App/MeetingCaptureApp.swift:4561-4563`).
- Honesty line: an on-device egress chip ("Running on this iPad · no network"), `Sig.local`
  (`apple/App/MeetingCaptureApp.swift:4552-4558`) — note this is the pre-badge prose idiom;
  on the web it must become the egress **badge** (see §6), per POSITIONING canon.

**Swift source.** `struct GenerationTheater` (`:4526`), `orb` (`:4569`), `constellation`
(`:4596`); the pixel asset is loaded via `pixelAsset("theaterorb", …)` (`:4579`).

**Web mapping (none).** No generation theater. The web *does* have live intel streaming
(`dashboard-app.js` WS state) to drive the per-type progression, the `--accent` /
`--accent-glow` tokens for the rings/bloom, `--ease-standard` for the settle, and
`hs-pulse` (`web/src/styles/global.css:97-101`) as a starting pulse. The PixelLab orb
asset ships only on the iPad (`apple/App/theaterorb.png`); the web has no orb sprite yet.

**Reuse-vs-new verdict.** **New.** Both the orb animation (CSS/SVG keyframes or an exported
sprite) and the type constellation are net-new web work. The streaming data and the motion
tokens exist; the bespoke visual does not.

**Port-priority: MED.** High wow, but it gates on live-intel-streaming UX and a web orb
asset; lower-frequency moment than the always-on HUD or the depth pass.

---

## 5. Premium sheets / modals

**What it is.** Custom-presented sheets with no default chrome: a real **grab handle**, a
**designed header** (glyph chip + identity + a real accent "Done" pill), a tinted glow in
the presentation background, and rounded corners — depth, not a plain dialog.

**Rules.**
- Presentation: detents `[440pt, large]`, hidden default drag indicator, corner radius 30,
  a custom `presentationBackground` = `bgGradient` + a blurred accent-tinted glow circle
  (`apple/App/MeetingCaptureApp.swift:2398-2408`).
- Grabber: a `Sig.faint 0.55` capsule, 40×5
  (`apple/App/MeetingCaptureApp.swift:2412-2415`).
- Header: a `GlyphChip` + category eyebrow + title + an accent-gradient "Done" capsule with
  an accent shadow (`apple/App/MeetingCaptureApp.swift:2417-2433`).

**Swift source.** `struct NodeInspectorSheet` (`:2369`) — `presentationCornerRadius` /
`presentationBackground` (`:2400-2408`), `grabber` (`:2412`), `headerBar` (`:2417`).

**Web mapping (partial).** The web has a native modal: `ConfirmDialog.astro` (a focus-trapped
`<dialog>` with a `confirm-dialog__header`) and drawer/panel patterns
(`web/src/components/ConfirmDialog.astro:30-39`, `web/src/components/Panel.astro`). It has
the surface + radius + elevation tokens (`--surface-2`, `--radius-lg`, `--elev-3`) and the
`--glow-accent` token.

**Reuse-vs-new verdict.** **Reuse + uplift.** The web already presents modals/drawers; what
is missing is the *craft layer* — a grab handle, the tinted radial glow background, and the
designed glyph-chip header with the accent "Done" pill. No new architecture, just applying
the depth tokens and adding two small primitives (a grabber element, a glow-background
treatment) to the existing dialog/drawer.

**Port-priority: MED.** Cheap, repeatable polish that touches every modal/drawer at once.

---

## 6. The egress badge

**What it is.** The compact, one-glance statement of where data goes:
`egress: {scope, label?}` where scope is `local` / `mixed` (local+cloud) / `cloud` (with a
target name). It is the POSITIONING-canon replacement for privacy paragraphs (Phase 62):
**a badge, never reassurance prose** (`docs/internal/POSITIONING.md:140-147`).

**Rules.**
- Scope → glyph + fallback: `local` ⌂ "Local", `mixed` ⌂+☁ "Local + cloud", `cloud` ☁
  "Leaves device" (`web/src/scripts/qlippy.js:134-138`).
- Color: `local` = `--ok` tint + border; `mixed`/`cloud` = `--accent` tint + border
  (`web/src/pages/presence.astro:292-302`).
- One badge per card, optional custom label
  (`web/src/scripts/qlippy.js:139-146`).

**Swift source.** The iPad still uses the **pre-badge prose idiom** in places:
`cfg.egressLabel` "On-device · nothing leaves" / "Sends to {host}"
(`apple/App/MeetingCaptureApp.swift:1570-1571`), the on-device chip in the theater
(`:4552-4558`), and a hand-rolled `egressBadge` ("lock + on-device")
(`:4934-4941`). The iPad has **not** fully adopted the structured `{scope,label}` badge that
the web shipped.

**Web mapping (exists, stranded).** The web already has the **canonical** structured badge:
the `EGRESS` map and render logic (`web/src/scripts/qlippy.js:134-146`), the card-author API
documenting `egress:{scope,label}` (`web/src/scripts/qlippy.js:106-110`), the events that set
it per card (`web/src/scripts/qlippy-events.js:51, 95, 103, 129, 152, 177`), the CSS
(`web/src/pages/presence.astro:280-302`), and the trust view's transcript-egress row
(`web/src/scripts/trust-view.js:52-70`). The dashboard carries a separate runtime
`egressLabel()` (`web/src/scripts/dashboard-app.js:255-256`).

**Reuse-vs-new verdict.** **Reuse — it exists; pull it into the cockpit.** The badge is the
web's own invention and is the **canonical** form both platforms should converge on. The gap
is placement: the structured badge is **stranded on Qlippy / `/presence`** and absent from
the main browser cockpit cards (history/meeting/intel surfaces). The fix is to lift the
`q-egress` render into a shared component and apply it on cockpit cards. (Cross-platform note:
the **iPad** should adopt the web's `{scope,label}` structure, the reverse direction — tracked
on the mobile roadmap, not built here.)

**Port-priority: HIGH** (cheap, and it is a POSITIONING-canon obligation: cards must carry the
badge, not prose).

---

## 7. The reactive mic waveform

**What it is.** A voice-dominant level meter: a row of bars whose **whole envelope** scales
with the mic level so silence is a calm flat line and speech makes it leap, with per-bar
wobble, a center bias, perceptual gain, and a peak glow.

**Rules.**
- Perceptual gain: `amp = min(1, pow(level, 0.62))` — a gamma < 1 expands the quiet end so
  normal speech drives full bars (`apple/App/MeetingCaptureApp.swift:3446`).
- Per-bar wobble × center bias × `amp`, plus a faint idle shimmer when active; bar fill is a
  vertical `accent → accent 0.5` gradient with an accent **glow on peaks**
  (`apple/App/MeetingCaptureApp.swift:3450-3463`).
- Driven by a `TimelineView(.animation)` at ~12 Hz phase, settle `easeOut 0.06`
  (`apple/App/MeetingCaptureApp.swift:3447, 3466`). Configurable bar count (16/32) and height
  (`:3194, 3403`).

**Swift source.** `struct MicWaveform` (`:3438`).

**Web mapping (none).** No waveform anywhere on the web. It needs a Web Audio
`AnalyserNode` (`getByteFrequencyData` / `getByteTimeDomainData`) feeding a `requestAnimationFrame`
canvas. Reusable styling only: `--accent` + `--accent-glow` for the bars/peak
(`web/src/styles/tokens.css:54, 58`).

**Reuse-vs-new verdict.** **New.** A genuinely new capability — the web has no live audio
visualization and no `AnalyserNode` wiring. Only the bar color tokens are reusable.

**Port-priority: MED.** Strong tactile signal during dictation/capture, but it depends on a
browser mic stream + the Web Audio graph, so it is more plumbing than the depth/badge ports.

---

## 8. Materialize / settle motion

**What it is.** The motion personality: cards **glow + insert on arrival**, entrances are
**staggered**, and everything moves on the "Signal settle" ease. Springs in SwiftUI; the
web equivalent is the settle cubic-bezier + a glow keyframe.

**Rules (iPad).**
- The shared press spring `response 0.3 / damping 0.7`
  (`apple/App/MeetingCaptureApp.swift:472`), the HUD expand spring `0.4 / 0.84` and the
  count-change spring `0.45 / 0.85` (`:2645-2646`), and the constellation settle spring
  `0.4 / 0.7` (`:4610-4611`). Live bubbles spring in on appear
  (`:478-485` doc, `LiveBubbleView` `:3474`). All animation is gated on
  `accessibilityReduceMotion` (e.g. `:2657, 4576`).

**Web mapping (exists, under-applied).**
- The settle ease: `--ease-standard: cubic-bezier(0.16, 1, 0.3, 1)`, plus `--ease-emphasized`
  / `--ease-decelerate` and `--duration-short/medium/long`
  (`web/src/styles/tokens.css:198-204`).
- The pulse keyframe: `@keyframes hs-pulse` + `.is-live` applying it `1.6s --ease-standard`
  (`web/src/styles/global.css:97-106`).
- Reduced-motion is already globally enforced (`web/src/styles/tokens.css:219-234`).

**Reuse-vs-new verdict.** **Reuse + extend.** The settle ease, durations, and the pulse all
exist and match the iPad's intent. What is missing: a **materialize keyframe** (glow +
insert/scale on arrival) and a **stagger utility** (per-item `animation-delay`). Today
`hs-pulse` is applied only to live dots (`global.css:103-105`), so the motion language is
*present but conservatively used*. Add one `hs-materialize` keyframe + a stagger helper and
apply them where cards arrive (intel results, history rows, queue jobs).

**Port-priority: MED.** It is the connective tissue that makes §1–§4 feel alive; small token
addition, broad application.

---

## 9. PixelLab bespoke assets

**What it is.** Generated pixel-art used as real product assets, not stock icons: the
generation-theater `theaterorb`, a `crystal`, and the Qlippy mascot sprites.

**Swift source / iPad assets.** `apple/App/theaterorb.png`, `apple/App/crystal.png`, loaded
via `pixelAsset(…)` (e.g. `apple/App/MeetingCaptureApp.swift:4579`).

**Web mapping (partial — Qlippy only).** The web already ships Qlippy as PixelLab pixel-art:
`holdspeak/static/_built/qlippy/qlippy.png`, `qlippy@4x.png`, plus `glyphs/` and `sprites/`
directories, referenced by `qlippy.js` (`GLYPH_BASE`, sprite loader,
`web/src/scripts/qlippy.js:123-125`). There is **no** web `theaterorb` or `crystal` asset.

**Reuse-vs-new verdict.** **Mixed — Qlippy reuse, orb/crystal new.** The Qlippy sprite
pipeline and assets already exist on the web (and are stranded on `/presence`, see §6). The
`theaterorb` (needed by §4) and `crystal` are iPad-only and must be generated/exported for the
web (PixelLab is the established tool, per the owner bar). No new pipeline — the web already
loads PixelLab PNGs — just new asset exports.

**Port-priority: LOW** (as an independent item — it is a dependency of §4 and §6/§2 rather than
a standalone craft win; produce the orb when the theater ships, reuse Qlippy when Qlippy lands
in the cockpit).

---

## Reconciled shared-token table

iPad `Sig` (`apple/App/MeetingCaptureApp.swift`) vs web tokens
(`web/src/styles/tokens.css`). **Aligned** = identical value, port freely. **DRIFT** = differs;
needs an owner decision on which wins.

| Concept | iPad `Sig` value (file:line) | Web token (file:line) | Status |
|---|---|---|---|
| Accent | `#FF6B35` (`:396`) | `--accent #FF6B35` (`:54`) | **Aligned** |
| Accent gradient | `#FF9D5C → #FF6B35 → #F24A2E` (`:416-418`) | none (no gradient token) | **DRIFT — add `--accent-gradient`** |
| Bg / canvas | `#0E0F13` (`:388`) | `--bg #0E0F13` (`:40`) | **Aligned** |
| Surface 1 | `#15171D` (`:389`) | `--surface-1 #15171D` (`:41`) | **Aligned** |
| Surface 2 | `#1C1F27` (`:390`) | `--surface-2 #1C1F27` (`:42`) | **Aligned** |
| Surface 3 | `#242833` (`:391`) | `--surface-3 #242833` (`:43`) | **Aligned** |
| Bg gradient | `#191B23 → #0E0F13` (`:410-413`) | none | **DRIFT — add `--bg-gradient`** |
| Text | `#F2F3F5` (`:393`) | `--text #F2F3F5` (`:48`) | **Aligned** |
| Text muted | `#9BA2B0` (`:394`) | `--text-muted #9BA2B0` (`:49`) | **Aligned** |
| Text faint | `#767E8D` (`:395`) | `--text-faint #767E8D` (`:50`) | **Aligned** |
| Local / cobalt | `local #5B8DEF` (`:400`) | `--local`→`--info #56C7F5` (`:70, 141`) | **DRIFT — different blue** |
| OK / success | `ok #3ECF8E` (`:397`) | `--ok #34D399` (`:61`) | **DRIFT — different green** |
| Warn | `warn #F2A33C` (`:398`) | `--warn #FBBF24` (`:64,118`) | **DRIFT — different amber** |
| Bad / danger | `bad #E5544B` (`:399`) | `--danger #F87171` (`:67,120`) | **DRIFT — different red** |
| Hairline (top-lit) | `white .12 → .035` gradient (`:425-427`) | `--elev-1` flat `inset white .04` (`:192`) | **DRIFT — web has no gradient hairline** |
| Card shadow | `black .38 / r16 / y9` (`:442`) | `--elev-2 black .50 / 24 / y8` (`:193`) | **DRIFT — opacity/radius differ** |
| Press scale | `0.975` (`:467`) | design-language says `0.98` (`signal §6`) | Near-aligned (cosmetic) |
| Settle ease | SwiftUI spring `0.3/0.7` (`:472`) | `--ease-standard 0.16,1,0.3,1` (`:202`) | Conceptually aligned (spring vs bezier) |
| Radius (card) | 18 / 17 (`:446, 2330`) | `--radius-5 18px` / `--radius-lg 14px` (`:188, 187`) | **Aligned** |
| Port: signal | `Sig.local` cobalt (`:1812`) | `--info`/`--local` (`:70,141`) | Same role, see "Local" drift |
| Port: text | `Sig.accent` (`:1812`) | `--accent` (`:54`) | **Aligned** |
| Port: findings | `Sig.ok` green (`:1812`) | `--ok` (`:61`) | Same role, see "OK" drift |
| Type: display | (iPad system bold) | Space Grotesk 700 (`tokens.css:80`) | Platform-native (n/a) |

### Owner decisions the drift forces

1. **Status palette (ok/warn/danger/local).** The two platforms shipped *visibly different*
   greens, ambers, reds, and blues. The web values are WCAG-tuned against `--bg`
   (design-language §10, `:196-208`); the iPad picked its own. **Decision needed:** make the
   web canonical (re-tune the iPad) or vice versa. Recommendation: **web wins** (it has the
   documented contrast math), tracked as an iPad re-tune on the mobile roadmap.
2. **Gradient tokens.** The iPad's `accentGradient` and `bgGradient` carry a lot of the felt
   depth and have **no** web token. **Decision:** add `--accent-gradient` and `--bg-gradient`
   to `tokens.css` with the iPad values (`:410-418`) so the web can reach the same hero
   surfaces. Low-risk additive.
3. **The top-lit hairline.** `--elev-1`'s flat `inset white .04` is dimmer and non-directional
   vs the iPad's `white .12 → .035` gradient border. **Decision:** add a gradient-border card
   primitive (the §1 verdict) so cards "catch light" identically.
4. **Card shadow values.** Minor (opacity .38 vs .50, radius 16 vs 24). Worth picking one
   number when the §1 card primitive lands; cosmetic, low stakes.

---

## Port-priority summary (input to HS-68-02 ordering)

| # | Pattern | Verdict | Priority |
|---|---|---|---|
| 1 | Signal depth (card + glyph chip + press) | Reuse, under-applied (needs a card primitive) | **HIGH** |
| 6 | Egress badge | Reuse — exists, pull into the cockpit | **HIGH** |
| 3 | Queue HUD | New shell, reused tokens + data | **HIGH** |
| 2 | Node-graph Workbench | New (largest build) | **HIGH** (heavy) |
| 8 | Materialize / settle motion | Reuse + extend (add materialize + stagger) | MED |
| 5 | Premium sheets / modals | Reuse + uplift | MED |
| 4 | Generation theater | New | MED |
| 7 | Reactive mic waveform | New (Web Audio AnalyserNode) | MED |
| 9 | PixelLab assets | Mixed (Qlippy reuse; orb/crystal new) | LOW (dependency) |

**Cheapest high-impact first:** §6 (badge — already built, just placement) and §1 (one card
primitive). **Heaviest:** §2 (the node canvas), de-risked in HS-68-03.
