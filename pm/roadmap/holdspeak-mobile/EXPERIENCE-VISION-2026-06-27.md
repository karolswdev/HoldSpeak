# HoldSpeak Experience Vision

_Authored 2026-06-27. One product, three surfaces (web, iPad, iPhone), two modes (dictation, meetings). This is the design spine for Phases 18 through 23. Every direction here ties to a contract phase so design and plan are one document._

---

## 1. Design philosophy

HoldSpeak is a debugger for trust. The user is a skeptical local-first developer dictating into their real buffer or sitting in a real meeting, and the cost of the tool being wrong lands in their editor, not ours. So the product is masterful when it ships the receipt a half-second before the action: the rewrite you watch resolve before a keystroke leaves the app, the artifact that wears its confidence and points at the transcript moment that justifies it, the egress badge that flips green to amber the instant a run touches your Mac without narrating a word about it. We do not have a flat web cockpit and a separate iPad toy. We have one system, "Signal," wearing two skins: on the web it is dark, technical, and flat; on the iPad it is Signal made physical, a lit desk where a meeting is a cassette, a model a cartridge, a KB a crystal, and confidence is the mass an object lands with. The same near-black canvas, the same ember-orange accent spent only on the live moment, the same card recipe with the top-lit hairline, the same one honest egress badge that is the only sentence either surface is ever allowed to say about privacy. Delight here is not confetti. It is the tool being fast enough to vanish, honest enough to show its work, local without a sermon, and able to act only after you approve. The best day with HoldSpeak is a boring one: every instrument green, nothing to read, your words landing where you aimed them.

---

## 2. The cross-surface doctrine (the reusable spine)

These rules keep web, iPad, and iPhone one product. They are not per-phase; they govern every screen.

### The shared visual spine (never moves between surfaces)
- **Near-black canvas, elevation by lightness.** `#0E0F13` ground, `#15171D / #1C1F27 / #242833` steps. No light mode. No heavy borders for depth; depth comes from lightness plus shadow plus the hairline.
- **One ember-orange accent `#FF6B35`, plus its 135 degree amber-to-ember gradient** (`#FF9D5C → #FF6B35 → #F24A2E`), spent only on primary, live, or focus. This is the number-one same-product tell. The desk adds exactly four sanctioned kind-colors (accent, cobalt `#5B8DEF`, violet `#9B6BFF`, mint `#3ECF8E`) and nothing else.
- **The Signal card recipe is identical:** layered fill, soft drop shadow, a `white .12 → .035` top-lit hairline, radius 18. `.signal-card` (web) and `.signalCard()` (iPad) are the same recipe. The card sets surface plus elevation only, never a status color on its body.
- **The gradient glyph chip** (radius roughly size times 0.28, accent-gradient fill) is the one icon and CTA container on every surface.
- **The uppercase-tracked eyebrow** (letter-spacing 0.06em, uppercase) is the technical label cue everywhere: section headers, kind badges, trace events.
- **Type:** Space Grotesk for display and brand, Inter for UI and body, JetBrains Mono for data and stats. The iPad uses system-rounded as its native analogue.

### The adaptive law: wide canvas to thumb column
The iOS app is ONE adaptive app, iPad and iPhone, governed by a single width authority (`DeskCamera`, derived from `horizontalSizeClass` plus width): `.wide` (the diorama), `.narrow` (split-view, the rail), `.lane` (iPhone, the single column). **Nothing is hidden or removed between sizes; the same primitives reflow because they were all derived from one `DeskPrimitive` declaration.** The desk has a camera and screen width is the lens: wide pulls back to the lit diorama, the phone pushes in until you are standing at the near end of one desk looking down its length. The right-edge intelligence pull-out becomes a bottom sheet that rises from the near edge (same card, same hairline, same lift, only the entry edge changes). The zone shelf becomes a horizontally scrolling chip rail. Cross-desk drag-to-route, which you cannot do with one thumb, degrades to the long-press "Route this to AI" twin that already ships. **The user's hand-arranged desk positions are never destroyed; the lane un-renders them and `.wide` restores the exact arrangement.** `DeskCamera` is the only width authority; scattered ad-hoc width checks get folded into it.

### The in-world law (never a dim-scrim modal)
Primitives are created and edited in place, lifting off the desk on a transparent catcher (tap-away commits), never behind a dimmed form. This governs primitive editing (note, KB, zone, connect, dictation, a node inspector). It does not govern full-screen destinations (a meeting recording, app settings), which are sanctioned full-screen sheets, not in-world edits. On the phone the rising bottom sheet uses a hand-built offset container over a transparent (no-scrim) catcher, not SwiftUI `.sheet` (which dims by default); the existing top-grabber drag pattern is the precedent.

### The mic-on-every-field law
Every text input on every surface carries a speak-to-fill Whisper mic (`VoiceCaptureState` / `VoiceFillMic` on iOS). This is a voice product; a voiceless input is a bug. On the phone the mic is the primary input and sits at the field's trailing edge in the thumb arc.

### The honest-egress law
The egress badge (`{scope, label}`: green `local` / orange `mixed` "Local + cloud" with the endpoint host as the label / `cloud` with the target named) is the ONLY way either surface talks about privacy. Never a prose sentence, never a reassurance paragraph. The badge reads the run's REAL location, never a default. Canonical scope is `mixed`, class `.is-mixed`, glyph `⌂+☁`, fallback word "Local + cloud."

### The motion contract (the "Signal settle")
Arrival is fade plus 6px lift plus scale .985 to 1 with a `--i`-indexed stagger on `cubic-bezier(0.16, 1, 0.3, 1)` (web `hs-materialize`) or the matching SwiftUI spring (iPad). Press-to-scale on every tappable (.98 web / .975 iPad). Live state pulses the DOT, never the text, so text never jumps. Everything honors `prefers-reduced-motion`: the craft (depth, hairline, run-state, confidence) is static and survives motion-off; only the entrance is killed. iPad haptics are tiered: `.light` for touch and selection, `.medium` for commit, `.rigid` for picking a node or zone up, `UINotificationFeedbackGenerator(.success)` on a completed action.

---

## 3. The signature moments (what a user screenshots)

1. **The macro fires as an object, not text** (web, iPad, iPhone — Phase 18). You say a macro keyword and the dictation preview does not show the word; it materializes a small Signal chip "fires: launch Terminal" with the macro's glyph and an egress badge if it touches the network. The actuator canon made visible at the moment of speech, and the old silent-relay failure heals itself into a one-tap "would fire — relay not connected · Connect" warn chip.
2. **The confidence ring drop** (iPad — Phase 19). A meeting artifact lands on the desk and its pixel-glyph is wrapped by an arc that fills to its confidence as it settles; a 92% decision drops heavy and almost fully lit, a 41% one lands light and danger-hollow and sits visibly UNSETTLED until a human accepts it. You read the machine's certainty across the whole desk by light and weight.
3. **The chip that refuses to lie** (iPad, web — Phase 21). You route a KB crystal through an agent, pick "On your Mac," and the moment the result prints the egress chip flips green to amber "Cloud · your Mac" with one breath and a success-haptic. Nobody narrated it. And because the scope is now persisted on the record, the kept card still tells the truth tomorrow.
4. **Walk the lineage by touch** (iPad — Phase 19, 21). The lineage rail is not text; it is the actual sprites that made this artifact (the cassette, an accent arrow, the agent's avatar, your note). Tap the cassette and the pull-out closes while the origin meeting LIFTS off the desk with an accent ring. You touched a receipt and it dove to its source.
5. **The branch forks in front of you** (iPad, web ladder — Phase 22). On `branchTaken` the ember token visibly splits, the taken wire stays lit ember with a ✓, the untaken branch dims to faint with an ✗. You SEE your program choose, a real ExecutionEvent trace turned into a spectacle, proven on real metal over a resolved source.
6. **The disk-vault seals** (web, iPad — Phase 23). The schema-safety guard made physical: a vault whose lid shuts and locks green when your store matches the build, and shows a red chain across a sealed lid ("v3, newer than this build, will not be touched") when a newer DB would have silently risked your data. The invisible data-loss risk becomes a thing you can see is protected.

---

## 4. Per-experience direction

### 4.1 Dictation (Phase 18)

**Thesis.** The dictation surface is a teleprompter, not a settings panel. A developer dictating into their real buffer does not want to tune knobs; they want to SEE what is about to land before it lands. So one thing is the hero on every surface: a preview where what you said sits beside the destination it will type into, and you watch the rewrite resolve BEFORE a single keystroke leaves the app. The config cockpit does not die; it collapses into a quiet "Tune" drawer you open only when the preview shows you something to change. Trust is the feature; rewrite-before-inject is how trust becomes a screen.

**The v1 honesty.** We stream the RAW transcript live (the meeting capture loop already windows Whisper and bubbles a partial) and resolve the rewrite ONCE on hold-release. The spoken-symbol flash plays on that single settle. We keep the entire trust thesis (the receipt before the action) while dropping incremental partial-stable rewriting, which fights a whole-utterance dry-run endpoint. No shimmer-skeleton loading state; the destination pill breathes (the desk's `DioSyncStatus` idiom) and the egress badge already explains an endpoint wait.

**Web.** `/dictation` rebuilt around a Console that replaces the cockpit-hero. A one-row readiness strip (one glyph chip, four inline status dots Mic / Model / Project / Language pulsing green via `hs-pulse`, the egress badge right-aligned) is the whole readiness surface at rest. The Console is one wide card split into two panes that share a baseline, but the column headers name the ROUTE, not the genre: left "YOU SAID," right "→ CURSOR" (the actual frontmost-app target the trace returns). A browser mic (net-new `getUserMedia`, the AppMark keycap mark) streams to the dictation pipeline. Below, a single destination line and the accent-gradient "Hold to type" CTA. The rule that makes it trustworthy: what is in the right pane is byte-identical to what gets typed. The trace accordion lives collapsed under the Console, labeled "trace" in the eyebrow. Activity nudges sit above as dismissible source-cited chips; accepting one grounds the rewrite with a "grounded in &lt;source&gt;" footnote.

**iPad.** Dictation is a real first-class concept on the desk, not a placeholder. **We resolve the component honesty up front:** either dictation becomes `case dictation` in `PrimitiveKind` (glyph, accent kind-color, a `DictationRecord`) so the lift idiom and drop-to-route are legitimate, OR it is declared a launcher and we drop the primitive-lift language. We take the first path: dictation is a primitive. Tapping its mic object LIFTS a teleprompter card in place (no scrim), same recipe as `DioInlineNoteCard` (rounded-24, accent-tinted stroke, double shadow). Because `VoiceFillMic`/`VoiceCaptureState` is tap-toggle with no streaming partial, the dictation card is backed by the meeting `CaptureModel` loop (which already bubbles a partial) plus press-and-hold gesture handling; **we state plainly this is NOT free reuse of the shared field mic.** Inside: a "you said" line (muted paper text) and a "→ types on your Mac" line, with the destination row showing the paired-Mac target or the always-visible "Connect your Mac" pill when unpaired, so "nowhere to send" is answered in the flow. Drop-to-route: drag the result onto a Note (becomes body), the AI core (rewrite), or the paired-Mac sprite (type there).

**iPhone.** The dictation mic promotes to a persistent bottom-edge HOLD BAR (accent-gradient capsule, thumb zone) on every desk screen. Press-and-hold; on hold the screen reflows to a single-column teleprompter that fills bottom-up from the bar so your thumb stays put while text grows above it: "you said" (muted, nearest the thumb), "→ Cursor" (full weight) above, destination plus egress as one pill at the top. **No dim toward the bar** (a dim is a scrim); the bar's elevation and the rising stack carry focus. Release commits (`.medium` haptic, `.success` on land). Trace is a single "trace ›" link that pushes a full screen with a working `topBack`.

```
WEB — /dictation Console (hero):
┌──────────────────────────────────────────────────────────────────────┐
│ DICTATION                                                    [ gear ⚙ ]│
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ◈  ●Mic  ●Model  ●Project  ●Lang        [ ● local ]               │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌─ CONSOLE ────────────────────────────────────────────────────────┐ │
│ │  YOU SAID                       │  → CURSOR                       │ │
│ │  ───────────────────────────────│─────────────────────────────── │ │
│ │  def handle underscore event    │  def handle_event(             │ │
│ │  open paren▌                    │            (settled from accent)│ │
│ │  [ ⌁ fires: launch Terminal ]  ← macro renders as a chip, not text│ │
│ │  ───────────────────────────────────────────────────────────────│ │
│ │  → types into Cursor           route: code · grounded in PLAN.md │ │
│ │           (  ◉ Hold to type  )         ⌥Space                     │ │
│ └───────────────────────────────────────────────────────────────────┘ │
│   trace ›  (collapsed)                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

**Ties to:** Phase 18 (readiness, dry-run preview, macro board, language/symbols, activity nudges). The macro-as-object beat is the lead screenshot and the cheapest high-value item; the empty state copy leads with the byte-identical promise ("what's on the right is exactly what lands in your editor"), run through the voice guard, never AI-assistant house style.

### 4.2 Meetings (Phase 19)

**Thesis.** A meeting artifact is a CLAIM the machine makes about what was said, and a developer trusts a claim only when it shows its work. So every one of the 14 artifacts wears its confidence and its sources on its face, and you can always jump from the claim back to the exact transcript moment that justifies it. Confidence is rendered as ONE language across all three surfaces (an arc that fills), the sources are a tappable lineage, and the review verb (draft / needs_review / accepted) is the verb of the whole surface.

**The contract honesty.** `artifact_status_from_confidence` is BINARY at 0.55 (below = needs_review, else draft). We render two states (lit accent above 0.55, danger-hollow plus "needs review" below), byte-true to the function. We do not invent a 0.75 amber band unless we add that status to the contract first. **"Show me the moment" is a backend story FIRST:** today an `ArtifactSourceRef` carries only `source_type` and `source_ref` (production emits `intent_window` and `plugin_run`, never a transcript timestamp). The jump is built by resolving `source_ref(window_id) → the window's start_seconds → nearest transcript segment`. Until that ships, a source pill renders what actually exists ("from intent window w0003," a quiet muted chip) and only resolved windows get the tappable accent pulse. An honest inert pill beats a beautiful broken one.

**Web / iPhone.** The meeting detail is "what the lenses found" (not a generic "Board"; "the lenses" is live vocabulary). Each artifact is identity-first: an eyebrow type label, a leading **circular confidence gauge** (the same arc geometry as the desk ring, flattened to 2D, mono digit inside it — one confidence language, not a progress bar) and a body. A `DioSourceRow`-equivalent of source chips sits under the body; a transcript-resolved one is tappable and pulses the transcript, a window or plugin one is a quiet muted chip. One "Accept" flips draft to accepted. The aftercare rollup (open / decided / changed, honest at zero) is the pinned top card. Facets are server-side, including an artifact-type multi-select and a min-confidence sweep for "every needs_review decision."

**iPad.** The desk is where the gap is worst and the payoff biggest. Each of the 14 artifacts arrives as a small primitive whose glyph wears a CONFIDENCE RING (arc-filled to the fraction, danger-hollow below 0.55), and high-confidence artifacts land with a heavier `PressableCard` settle so a confident result feels like it has more mass. **A needs_review artifact sits visibly UNSETTLED** (a faint wobble, lower rest height, never fully seated) until a human accepts it, so the unsure thing literally has not landed. The one `SectionBody` renderer learns the new cases (`.timeline`, `.diagram`; `.chips`/`.actions` exist) so all 14 types look native. The lineage is a **new `DioSourceRow`** (NOT `DioLineageRow`, which tells a from-via RunProvenance story artifacts do not have): a row of source chips, the transcript-resolved one tappable to pulse the transcript. Accept is a press-and-settle commit (`.medium` haptic, success notification, ring snaps solid, a tick rides the glyph). Aftercare comes to the desk as a Qlippy-surfaced in-world card (double-gated, never autonomous). Facets dim the non-matching cassettes PHYSICALLY (they lose their key-light and cast shadow; the matching ones keep theirs), so the archive narrows by light, not opacity.

```
WEB — meeting detail, what the lenses found:
┌──────────────────────────────────────────────────────────────┐
│  Q3 KICKOFF · 42 min · 4 speakers          [local]   ⌄ facets │
├──────────────────────────────────────────────────────────────┤
│  AFTERCARE        ● 3 open  ● 2 decided  ● 1 changed   ▸ jump  │
├──────────────────────────────────────────────────────────────┤
│ ◔92 DECISIONS              │ ◔48 RISK REGISTER  ⚠ needs review │
│  Web-first is the Q3 bet.  │  verify before you trust this     │
│  src: transcript·04:12 ›   │  src: from window w0007 (inert)   │
│  [ Accept ]                │  [ Accept ]                       │
├────────────────────────────┼──────────────────────────────────┤
│ ◔78 ACTION ITEMS           │ ◔85 INCIDENT TIMELINE             │
│  ☐ Karol — mesh sync       │  09:02 alert → 09:14 rollback     │
└────────────────────────────┴──────────────────────────────────┘
gauge: arc fill, lit accent ≥0.55 / danger-hollow <0.55 (binary, contract-true)
```

**Ties to:** Phase 19 (capture, live intelligence, 14 provenance-bearing artifacts, aftercare, faceted archive). The confidence ring drop and the unsettled-until-accepted state are the desk-native trust moments; "show me the moment" ships only after its backend story.

### 4.3 The adaptive iOS craft (Phase 20)

**Thesis.** The Desk is a place, and a place has to fit through a doorway. There is ONE doctrine, not two builds: the desk has a camera and screen width is the lens. The phone never feels like a worse iPad; it feels like the desk shrank to thumb-reach without losing a single object, glyph, or the in-world law.

**Honest scope.** The lane is a NEW renderer, not a free reflow: the wide desk is absolute-positioned with drag-to-arrange and lasso, and a vertical card lane is a different layout engine gated on `DeskCamera.lane`. We budget it as a real screen. The user's spatial arrangement (`positions[id]`) is never destroyed; the lane sorts by recency and zone, and rotating back to `.wide` restores the exact arrangement. The two already-shipping full-screen sheets (a meeting recording, settings) are sanctioned destinations, not in-world edits; the no-modal law governs primitive editing only. The rising bottom sheet is a hand-built offset container over a transparent catcher, not a dimming `.sheet`.

**Web.** The web is the desk's hub-side mirror and names the camera for the developer. A single segmented control, "Desk · Rail · Lane," **continuously interpolates** the layout as you drag the divider or resize: the right intelligence rail physically TRAVELS from right-edge to bottom-edge on a spring, the egress badge riding along. This is documentation-as-interface; it is the iPad-to-iPhone reflow happening live on your own screen, the thing you screenshot to show a teammate "it's literally one app." (The web masonry of glyph-chip cards is reuse of the shipped Signal vocabulary, not the hero; the segmented control is the move.)

**iPad and iPhone.** `DeskCamera` is introduced as the ONE width authority and the scattered `w >= 500` and `UIScreen.main.bounds` reads are folded into it (first story: "DeskCamera is the only width authority; delete the strays"). The pull-out content travels cheaply (it is already `maxWidth/maxHeight: .infinity`); only the entry edge and a grab handle change. The signature device moment: in split-view, drag the multitasking divider and watch `DioPullout` physically migrate right-edge to bottom-edge on a spring, IN REAL TIME, proven by hand on the cabled iPad (not seeded screenshots). The crisp `.interpolation(.none)` sprite at 96pt or 44pt and the long-press "Route this" twin are cohesion INVARIANTS that survive the reflow, not new delights; the lane simply drops cross-desk drag and leans on the twin that already ships.

```
iPhone — DioStage, LANE camera (<500pt):
┌───────────────────────────┐
│ ⌶  ● synced 2m   ⚡Connect │  ← slim header: sync pill + connect
├───────────────────────────┤
│ ‹ ●meet ●models ●kb ●notes›│  ← sticky zone CHIP rail (tint pills)
├───────────────────────────┤
│ ┌───────────────────────┐ │
│ │ 📼  Standup          › │ │  ← full-width .signalCard row
│ │     CASSETTE · 3 decs  │ │     crisp pixel glyph @44pt
│ └───────────────────────┘ │
│ ┌───────────────────────┐ │
│ │ 💎  Infra KB         › │ │
│ └───────────────────────┘ │
│                      ╭───╮ │
│                      │ + │ │  ← accent FAB: New Note/KB/Zone
│                      ╰───╯ │
├═══════════════════════════┤  ← tap a row → sheet RISES from here
│ ▦ Standup        🔒 local  │     (same DioPullout content, grab handle,
│ ──────  ▁▁  ──────         │      over a transparent catcher, NOT a modal)
└───────────────────────────┘
```

**Ties to:** Phase 20 (the iPad-to-iPhone adaptive craft). The first story consolidates width authority; the device split-view reflow is the proof on metal; the spatial-arrangement persistence repairs the "nothing is removed" claim.

### 4.4 Trust and honesty (Phase 21)

**Thesis.** Honesty is the receipt that ships WITH every output, by construction. One object says two true things at a glance: WHERE IT CAME FROM (from &lt;card&gt; · via &lt;agent&gt;) and WHERE THE WORK HAPPENED (the egress badge). Today the iPad pull-out hard-codes "On device" on EVERY primitive even when the run crossed the LAN to your Mac. The fix is the story.

**The spine that has to ship first: persist the receipt.** Add a stored `egress` scope (and the typed provenance) to `OutputRecord`, write it through `toContract()` / `init(contract:)` so it survives sync and reopen, and stop driving the printed card from transient `@State`. The SAME field powers the pull-out via the `DeskPrimitive` contract so the ONE renderer reads egress for ANY primitive. Without this, "the receipt IS the delight" is a card with amnesia tomorrow. **The smallest honest win, shipped alone first:** replace the hard-coded "On device" capsule with a real `EgressBadge(scope:)`, screenshot the green-to-amber on a real "your Mac" run, then build outward.

**Web parity is NOT free.** The web dashboard reads a GLOBAL `intelEgress` posture, not per-card sources. The real story: both surfaces gain per-card egress from one new stored field, read per card. We do not claim web already does this end to end.

**Web.** A `.provenance-rail` inside the card, under the title: row 1 the egress chip (real scope, never a default, no prose); row 2 the lineage spine ("FROM &lt;source pill&gt; → VIA &lt;agent pill&gt;," the source pill scrolls-and-pulses the origin card). **No confidence meter in v1** (the desk path hard-codes confidence 1.0; a meter would show 3 solid bars on every iPad-born card, a confident lie inside a trust feature). The multi-hop "Show lineage" tree is DEFERRED until per-hop scoped-egress data exists; if teased at all, only as the iPhone accordion dot-strip "● ● ◐," which survives a narrow column.

**iPad.** Lead with **walk-the-lineage-by-touch** as the daily-use hero (the mid-run chip-flip is the demo/onboarding moment). The lineage is the 28px `.interpolation(.none)` sprite shelf rendered IN THE PULL-OUT (which has no lineage today), fed by the existing lineage data: the source card's actual glyph → an accent arrow → the agent avatar → this artifact's glyph. Tap the source sprite and the pull-out closes while the origin primitive LIFTS with an accent ring and a `.medium` haptic. `.mixed` is added to the iPad `EgressBadge` (mint-to-amber gradient capsule) but ONLY wired to a run that actually crosses a boundary (a chain whose step 1 is on-device and step 2 is your Mac); we do not ship a case the system cannot reach.

```
WEB — artifact detail card (hero):
┌──────────────────────────────────────────────────────────┐
│ ▢ Release notes draft                          [⋯]  [↗]  │
│ ⌂+☁ Local + cloud · your Mac          ◀ egress chip (real)│
│ FROM ▣ Sprint sync  →  VIA ◆ Scout    ◀ lineage spine     │
│ ──────────────────────────────────────────────────────────│
│  ## What shipped                                           │
│  - Egress badge replaces privacy prose …                  │
│  [ Route this again ]   [ Copy as markdown ]              │
└──────────────────────────────────────────────────────────┘
   click ▣ Sprint sync → origin card pulses (materialize + accent glow)
```

**Ties to:** Phase 21 (provenance plus egress on every output). Persistence is the actual phase spine; the pull-out fix is the first shippable beat; the meter and the multi-hop tree are deferred until their data exists.

### 4.5 Workflow / graph (Phase 22)

**Thesis.** A workflow is the one HoldSpeak artifact a developer BUILDS rather than dictates, so it must feel like a debugger you watch, not a config form. Three promises kept visibly: what you author is what runs and what travels (one canonical `graph_json`, no demo text, no silent linear downgrade); you watch your program think (the real `ExecutionEvent` stream as one ember token walking the exec wires); and the tool is honest about what each surface can run.

**The web honesty (the biggest correction).** There is no web node-graph editor and we do not build one; that is a from-scratch second renderer of the entire Blueprint model and it contradicts the "one desk everywhere" canon. **The web reuses the iPhone LADDER as its renderer**: a read-and-watch ladder plus author-the-chain, inside the existing desk-app workflow capability shell. This matches the phase story ("web authors a linear graph or honest scope"), and the cross-surface replay becomes "iPad canvas → web ladder watches the same `ExecutionEvent` token climb the same cards while the Mac runs it," which is buildable this phase and still the screenshot.

**The model honesty.** `BPNode` carries `failurePolicy` (true, keep it) but NOT `runsOn`; per-node RUNS ON is NET-NEW (add `runsOn` to `BPNode`, the serializer, and the hub's `GraphNode`). The inspector's RUNS ON section is the audit FIX, written as work, not reuse. The honest-scope chip is a real contract: the hub's `linearize()` returns its refusal REASON STRING on validate and the chip renders that exact string ("node b1 is control-flow; the hub runs linear-only"), so it is never a client-side guess. Component names are the shipped ones (`QueuePresence`, not "QueueHud"; `VoiceCaptureState` is the literal mic).

**iPad (the center of gravity).** Retire the single-wire v1 canvas and make the two-wire `BlueprintCanvasView` (currently demo-gated, mid-build) the home, driven by the REAL `BlueprintInterpreter.events` stream over a RESOLVED source (a tacked meeting moment), killing the seeded "Standup transcript…" demo text. "What you author is what runs" is only true once this cutover ships. Exec pins are square white-cabled (control flow); data pins are round and type-colored. The inspector lifts as an in-world card (never a scrim). **SAVE is a quiet, weighty commit:** the canvas physically LOWERS back to the desk (the zone-dive reverse), the Workflow object lands with a breathing `DioSyncStatus` pill, and Qlippy is SILENT (no result yet); Qlippy's double-gated card is reserved for `runFinished`-with-output only.

**iPhone.** The phone does not host a free-pan 2D canvas; it is the ladder, honestly. The exec graph is a single thumb-reachable column of node cards in execution order; branches are labelled stubs you expand inline (read one path at a time, like code); a forEach is an indented body with a live "3/10" counter. Watching is the phone's superpower: on a run (yours or a mesh run from the Mac) the ladder auto-scrolls to keep the active card centered, it ignites with the run-pip and breathe, `branchTaken` collapses the untaken accordion with an ✗ and keeps the taken (✓). Authoring is scoped to linear chains; a complex re-wire shows a quiet "edit branches on iPad or web" handoff, the honest-scope posture again.

```
iPhone — WATCH mode (the exec ladder mid-run):
┌──────────────────────────────┐
│ standup-triage               │
│ [⬤ branches→device] [◐local] │  ← honest-scope + egress pills
├──────────────────────────────┤
│ ┃ ╭──────────────────────────╮│
│ ┗▶│◆ branch ·contains deploy ││  ← active card: lit, ⚡pip, breathe
│   │  ✓ true →   ✗ false ┈┈┈  ││  ← untaken accordion collapsed, ✗
│   ╰──────────────────────────╯│
│     ╭────────────────────────╮│
│     │▣ llm  MODEL    3/10 ↻  ││  ← loop counter ticks in place
│     │ "deploy approved by…"  ││  ← 80-char produced preview (honored)
│     ╰────────────────────────╯│
├──────────────────────────────┤
│ ⬤live · PRODUCED  ▸ timeline  │  ← QueuePresence pill; tap = event sheet
│         [ + add node ]  [🎙]   │  ← author the chain; mic primary
└──────────────────────────────┘
```

**Ties to:** Phase 22 (Blueprints authoring, one `graph_json`, live `ExecutionEvent` replay). The serializer (lower to canonical `graph_json`, round-tripped against `linearize`) is the lead story; the v1-to-v2 cutover is the iPad center of gravity; the branch-fork over a real source is the screenshot this phase, the thumb-to-web replay is the north star.

### 4.6 Onboarding and health (Phase 23)

**Thesis.** Onboarding and health are the same surface at two moments. The first time it is a checklist that walks you to your first words; every time after it is a console you glance at to confirm the tool is still trustworthy. The masterful version is a READINESS CONSOLE that reads like `holdspeak doctor` rendered as instruments, boring on a good day and surgically honest on a bad one.

**The split.** Ship the WEB readiness console plus the schema disk-vault as Phase 23 (a re-skin of a shipped page over existing data, high confidence). The iPad "desk coming online" is a later phase, blocked on an unanswered question.

**The unanswered question, answered.** The doctor checks describe the desktop HUB (its mic, hotkey, ffmpeg, web runtime). The iPad has its own distinct readiness. So the iPad readiness pull-out shows TWO instrument clusters: THIS DEVICE (its own mic grant, its on-device GGUF cartridge, its DeskSync pairing, from a small iPad-local probe) and YOUR HUB (the desktop's setup-status over the existing API, shown dimmed/remote). The disk-vault on the desk is explicitly "your Mac's store." This is MORE honest and more on-brand (the mesh) than pretending one doctor feed covers both.

**Web.** `/setup` is the Readiness Console; `/welcome` borrows the same instruments. Failing and warn checks are full rows up top (severity-sorted); passing checks stay a flat tick-grid (the shipped instinct, calmer than click-to-expand bands). **The good day does one HoldSpeak-only thing:** the all-green verdict quotes your last real dictation as proof of life ("Ready. Last words landed 2h ago — 'ship the thing' → VS Code, 380ms"), read from the journal. A status page that can quote your last successful action is signature; a green dot is not. **The disk-vault is a real state machine** driven by the existing Database doctor check: MATCH (lid shut, green padlock), OLDER (lid ajar, amber, the doctor's own backup fix string plus a working "Back up now" that shells `holdspeak backup`), NEWER (red chain across a sealed lid, the doctor's verbatim refuse string, "Upgrade" plus "Restore a backup"). The three branches map 1:1 to the doctor's three Database outputs. The first-words reward already ships; we do not re-claim it as new.

**iPad.** Fold the `DioFirstBoot` metaphor INTO the boot sequence so the tutorial and the health check become ONE thing: each metaphor step lights as its real check passes (meetings → capture-ready, AI core → model-ready, zones → store-ready), the violet-to-ember guiding trail flowing into the record orb. Qlippy is the health narrator, double-gated, surfacing exactly ONE fix card on a bad day and never nagging a green desk. New PixelLab assets (a violet disk-vault, a cobalt cartridge sprite) are budgeted as real line items, kept as DeskSprites with `.interpolation(.none)`.

```
WEB — /setup, good-day verdict (the HoldSpeak-only proof of life):
┌──────────────────────────────────────────────────────────────┐
│ READINESS                                          ● local    │
│  Ready. Last words landed 2h ago —                            │
│  "ship the thing" → VS Code · 380ms          ▁▁▁ (breathes)   │
│ PERMISSIONS · 3 ready   MODEL · 4 ready   (flat tick-grid)     │
│ STORE                                                          │
│ ┌────────────────────────────────────────────────────────┐    │
│ │ [▣green] Database   Schema v2 · matches build  🔒 ✓     │    │
│ └────────────────────────────────────────────────────────┘    │
│ (NEWER variant: red chain across a sealed lid, doctor's        │
│  verbatim refuse string, [Upgrade] [Restore a backup])        │
└──────────────────────────────────────────────────────────────┘
```

**Ties to:** Phase 23 (release-readiness made first-run-and-daily). Web ships now over `collect_doctor_checks` / `build_setup_status`; the iPad two-cluster readiness and the disk-vault asset work are sequenced after.

---

## 5. What masterful looks like vs merely done

| Beat | Merely done | Masterful |
|---|---|---|
| Dictation preview | A raw/clean two-column transcript box | The right column names the DESTINATION (→ Cursor), the macro fires as a chip not text, what you see is byte-identical to what types |
| Meeting artifact | A card with an "82% confidence" pill | One arc-fill confidence language across surfaces; on the desk it lands with mass and sits unsettled until you accept it |
| Provenance | A grey "via Scout" subtitle | A sprite shelf you tap to dive to the source; the egress scope persisted on the record so it is honest tomorrow |
| Egress | A "nothing leaves your machine" sentence | One badge that flips green-to-amber the instant a run touches your Mac, narrated by nothing |
| Loading | A shimmer skeleton in the text | The status dot breathes; text never moves; the egress badge already explains an endpoint wait |
| Graph run | A log line saying the branch was taken | The ember token forks in front of you, the taken wire lit with a ✓, over a real source on real metal |
| Adaptive | A separate iPhone build with features cut | One desk through a closer lens; the pull-out migrates edge-to-edge on a spring, the arrangement restored on rotate |
| Health | A green dot that says "ready" | The verdict quotes your last real dictation; the disk-vault seals with a red chain when a newer DB would have risked your data |
| Qlippy | A mascot that appears and is cute | One earned interruption with a one-tap fix that actually acts, silent on a green desk |

---

## 6. The sharpening pass (final cohesion integration)

The design-director draft (sections 1 through 5) read as one product by construction, but a final
cohesion critic found three places where a surface was merely correct, not masterful. The most
important is the one that matters most to "whenever I say iPad I also mean iPhone." These are the
fixes, now part of the contract.

### 6.1 The iPhone meeting-review is a first-class signature surface (the highest-leverage upgrade)

The draft folded the iPhone meeting artifact into "Web / iPhone" and gave it the flat web card (a
circular gauge, source chips, a label-flip Accept) while the iPad got the whole trust spectacle (the
confidence-ring drop, the unsettled wobble, lineage-by-touch). That is backwards. **Phone-in-hand
after a call is the most realistic place a developer reviews a meeting at all**, so it is exactly
where the thesis (every artifact wears its confidence, jump to the moment that justifies it) most
needs to land. The phone does not inherit the web card; it inherits the desk's physicality, reflowed
into the lane.

- **Confidence is mass in the column.** A `needs_review` artifact rests visibly lower in the lane
  with the same arc-fill ring as the desk (flattened to the card's leading edge), and it **wobbles**
  on a slow idle until it is dealt with. A 92% decision sits high and almost fully lit; a 41% one
  sits low, danger-hollow, asking for you.
- **Thumb-accept re-seats it.** One tap on the card's Accept (in the bottom thumb arc, not a tiny
  trailing link) snaps the ring solid, re-seats the card up to its resting line with the Signal
  settle, fires a `.medium` haptic and a success notification. The review verb finally has a body on
  the surface whose whole job is reviewing.
- **"Show me the moment" is a thumb jump.** The card's primary affordance is not "read more"; it is
  a transcript-moment jump that scrolls the capture to the utterance that justifies the claim, the
  phone analogue of lineage-by-touch (the multi-hop sprite shelf stays an iPad daily-hero; the phone
  gets the one hop that matters in one thumb-reach).

```
iPHONE — meeting review, lane (phone-after-the-call):
┌───────────────────────────────┐
│  Q3 kickoff · 14m      ● local │
│  ────────────────────────────  │
│  ◗92  DECISION                 │   ← high, ring almost full, settled
│  Ship the desk to web by Fri.  │
│  ▸ show me the moment          │
│  ────────────────────────────  │
│                                │
│   ◖41  RISK        (wobbles)   │   ← rests LOWER, danger-hollow ring
│   No owner for mesh sync yet.  │
│   ▸ show me the moment         │
│        [  Accept  ]            │   ← thumb-arc; tap re-seats + ring snaps
└───────────────────────────────┘
   (Accept: ring → solid, card rises to the line, .medium haptic, ✓)
```

**Ties to:** Phase 19 (artifact provenance render) and Phase 20 (the lane). This is the proof the
iPhone is the third equal voice in the chorus, not a degraded reader. The Workflow WATCH ladder
(section 4.5) already proved the phone can carry a signature moment; meetings must match it.

### 6.2 The disk-vault gets a motion verb (not three static states)

Signature moment 6 was specified as three images (match / older / newer), not a beat with weight. It
joins the ring-drop and the branch-fork only if it MOVES: on a real newer-DB detection the lid falls
with mass and lands heavy, the chain snaps taut across it with a `.rigid` haptic, and the doctor's
verbatim refuse string types in beneath. A match is the quieter twin: the lid lowers and the lock
rolls green with a single `.success` tick. The data-loss stopper should feel like a stopper.

### 6.3 The web and iPhone Accept earn their own beat

On the iPad, accepting an artifact is choreographed (the ring snaps solid, a tick rides the glyph,
`.medium` haptic). On the surfaces whose entire verb is review (`draft → needs_review → accepted`),
Accept cannot be a label flip. The web/iPhone accept completes the confidence gauge's arc in one
sweep and re-seats the card on the Signal settle, so the most-used verb on the most-used review
surface has the same weight as its desk twin.

---

_This document is the design contract. Where a direction disagrees with shipped code, the code wins and the direction is sharpened to match (the critiques are integrated above, including the final cohesion pass in section 6). Where a beat depends on data the contract does not carry, the backend story ships first and the surface renders only what is true._
