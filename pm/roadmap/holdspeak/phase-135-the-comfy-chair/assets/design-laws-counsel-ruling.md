I have now read all required materials, examined the screenshots, and spot-checked every load-bearing token and component claim. Here is the ruling.

---

COUNSEL RULING -- THE COMFY CHAIR DESIGN-LANGUAGE LAW BOOK

Examined: comfy-chair-design-laws-draft.md (10 laws + 3 open questions), five-jobs-baseline-report.md (5 jobs, 10 friction findings), design-system-counsel-ruling.md (the EXTEND verdict + ranked work list), 4 screenshots (intelligence-brief-1440.png, job4-speak-open.png, job3-search-shelf.png, job3-cadence-open.png), and direct verification against the source files: design-tokens.json, tokens.css (332 lines), global.css (lines 128-214), gadgets.css (lines 633-747), chrome-menus.css (lines 175-217), pullout.css (lines 285-331), Surface.tsx, gadgets.tsx.

This ruling is bound by the owner's eleven rulings. I do not relitigate them.

---

## A. LAW-BY-LAW VERDICTS

**L1 -- DEPTH: THE LIGHT-SOURCE / BEVEL LAW -- RATIFY.**

Every token the law cites exists at the stated location and carries the stated value. `--desk-window-bevel` (tokens.css:267), `--desk-window-etch` (tokens.css:268), `--bevel-light/dark` (tokens.css:116-117), `--etch-light/dark` (tokens.css:118-119), `--desk-window-shadow: none` (tokens.css:263), `--desk-window-blur: none` (tokens.css:266) are all verified. The pressed-state timing claims are correct: TransportKey bevel-inversion at gadgets.css:702-712, Button translateY(1px) at global.css:178-181. The three-state grammar (raised/sunken/flat) is a truthful description of existing behavior, not aspirational. The forbids codify what the material model already enforces. One minor documentation note: `--elev-1` through `--elev-4` are described as "reserved for the GL world canvas layer only," but they are defined with concrete shadow values at tokens.css:190-193 and nothing prevents a component author from using them. The law should say "MUST NOT be used on DOM elements in the desk shell" rather than "reserved," so the forbid has teeth. This does not block ratification.

**L2 -- THE DOOR: THE CHAIR'S ANATOMY -- RATIFY-WITH-CONDITION.**

The anatomy, the six-point composition contract, and the information-at-a-glance doctrine under the everything-windows ruling are sound. The contract is specific enough to implement: `maxItems`, Surface-primitive rendering, `onOpenInWindow` callback, header-click-opens-window, optional footer, no per-lane spinners. Two conditions:

(1) Remove `--door-lane-max-items: 12` as a CSS custom property. It is a conditional rendering bound (how many React children to render), not a style. The `maxItems` prop on the lane component is the right contract and the law already defines it. A CSS property for this is architecturally misleading -- changing it in DevTools would do nothing. Keep it as a JS constant or a React prop default.

(2) The "no skeleton, no spinner per lane" rule is a loading-UX bet, not a structural law. If the hub is slow, a door rendering as a blank viewport for seconds before lanes arrive is hostile. The prior counsel flagged missing skeleton loading as P2-kit-gap #13. Condition: if ALL lanes return null during initial load lasting more than 300ms, show a single SurfaceState. Individual lane loading indicators remain deferred, but the total-blank case must have a fallback. Workers should implement the single-fallback SurfaceState, not per-lane skeletons.

**L3 -- BUTTONS: THE THREE-SPECIES SPEC -- RATIFY-WITH-CONDITION.**

All three species verified in source. Heights: `.btn` min-height 28px (global.css:129), `.desk-chip` height 27px (chrome-menus.css:178), `.gadget-transport-key` 48x48px (gadgets.css:672-673). Pressed behaviors: Button translateY(1px) (global.css:178), desk-chip scale(0.94) (chrome-menus.css:207-208), TransportKey bevel inversion (gadgets.css:709 swaps bevel-dark and bevel-light positions). All correct. Condition:

(1) The "Small" variant row says font 11px and shows "(any above)" for height, implying 28px. The real `.btn--sm` has `min-height: 24px` (global.css:149-150). The law must state this explicitly: "Small: 24px min-height, 11px font." A builder reading "(any above)" would assume 28px and write the wrong spec.

(2) TransportKey has a `[data-compact]` variant at gadgets.css:737-746 that collapses to `height: 28px` with `width: auto; min-width: 44px`. This is used for inline row contexts. The law must document this variant; omitting it invites a fourth species when a builder encounters a row-height instrument control.

**L4 -- SOUND: THE MECHANICAL PALETTE -- RATIFY-WITH-CONDITION.**

The six-sound palette, the "mechanical, dry, short" character, and the global toggle design are correct. No sound tokens exist anywhere in the codebase (confirmed by grep), so this is net-new. The reduced-motion mute via the same media query that zeros duration tokens (tokens.css:314-331) is elegant. Three conditions:

(1) The law proposes `--sfx-*` as CSS custom properties in design-tokens.json, then admits in the same paragraph that "CSS custom properties cannot play audio" and will be emitted as "comments." This is confused. Drop the `--sfx-*` CSS properties entirely. Define the six canonical names in a `"sound"` section of design-tokens.json for documentation only. The runtime API is `sfx.play('key-down')` from an `sfx.ts` module with a typed enum. The CSS token layer documents colors, spacing, and shadows; it does not document audio.

(2) The law says "sounds do not queue or interrupt each other; overlapping playback is fine." This needs a pool-size cap. Rapid-fire pointer events (frantic clicking) could spawn unbounded concurrent AudioBuffer nodes. Cap concurrent instances of any one sound name at 3. Beyond that, the oldest instance is silently dropped.

(3) The 100KB total budget for six sub-120ms WAVs is tight but achievable only with OGG. A 120ms mono WAV at 22050Hz 16-bit is roughly 5KB; six at that spec total 30KB as WAV, well under budget. But if the sounds are higher sample rate or stereo, the budget is blown. Condition: specify mono, 22050Hz or 44100Hz, 16-bit, OGG-preferred with WAV fallback.

**L5 -- COLOR: THE EMBER + KIND-TINT LAW -- RATIFY.**

Every token value verified: `--accent: #a86e4a` (tokens.css:94), `--accent-hover: #bc8058` (tokens.css:95), `--accent-press: #936041` (tokens.css:96), `--accent-tint: rgba(168,110,74,0.12)` (tokens.css:97), `--accent-glow: rgba(168,110,74,0.28)` (tokens.css:98), `--accent-cool: #5b8def` (tokens.css:213). All seven glow-pool tokens verified at tokens.css:243-249. All four status colors verified at tokens.css:101-112. The forbids (kind-tints never on controls, never on text color, no second general-purpose accent, no raw hex) are sound and codify what the material model already practices. The `--accent-gradient` value matches the primitive orange.300/500/700 series in design-tokens.json. Nothing wrong here.

**L6 -- TEXT OVERFLOW: THE LAMP / SYSTEM-MESSAGE LAW -- RATIFY.**

The lamp overflow is confirmed P0-broken by the prior counsel, the face walk, and my own eyes on the intelligence-brief-1440.png and the Speak screenshots. The source confirms `white-space: nowrap` at gadgets.css:641 with no overflow handling. The three-treatment table (truncate+title for inline, wrap for block messages, truncate+open-in-window for ledger rows) is the right graduated approach. The `.is-block` variant for block-level messages is correct. One amendment: drop the proposed `--desk-lamp-max-width: 100%` token. `max-width: 100%` is a CSS property value, not a meaningful design token. Apply the CSS fix directly in gadgets.css. The token layer should not have tokens that are just aliases for CSS defaults.

**L7 -- TABS & AFFORDANCE: THE WING TREATMENT -- RATIFY.**

Confirmed by source and screenshot. Pullout.css:300-301 shows `background: none; color: var(--text-faint)`. My own eyes on intelligence-brief-1440.png confirm: FOLLOW-THROUGH and DECISIONS look like labels, not tabs. The proposed fix (inactive wings get `color: var(--text-muted)` + `background: var(--wash-1)`) is conservative and correct. The visual distance between inactive (`wash-1` = rgba(255,255,255,0.035)) and active (`desk-window-well` = rgba(0,0,0,0.28), with etch bevel) is sufficient -- they are on opposite sides of the brightness spectrum. The hover escalation to `color: var(--text); background: var(--wash-1)` already exists at pullout.css:318-320, but should escalate to `wash-2` to preserve a hover step above the new rest state. This is already what the law proposes. No issues.

**L8 -- THE NARROW SHELL: TAB BAR SPEC -- RATIFY-WITH-CONDITION.**

The dual-grammar concept (960px routing decision, separate component tree) is exactly what the prior counsel recommended (section C, option iii). The 5-slot tab bar with MIC dead-center is the owner's ruling codified. The sheet behavior leveraging existing tokens (`--desk-sheet-top-radius: 18px` at tokens.css:271, motion tokens) is sound. Two conditions:

(1) `DeskShellRouter` does not exist in the codebase (confirmed by grep). The law references it as if it is an existing component. The implementation note must be clear this is NEW infrastructure. The router must be a dedicated module with its own story, not a conditional branch stuffed into the existing DeskShell. This is a dependency: the narrow shell's lane rendering depends on the Chair surface (Phase 135) existing first. Call this out as a sequencing constraint.

(2) The forbid "No CSS @media (max-width: 959px) hacks on the desktop shell components" is the right principle but needs a carve-out. The tab bar itself needs media queries or `env()` for safe-area insets and notch handling. Amend: "No responsive media queries that make desktop shell components behave differently at narrow widths. The narrow shell is a separate component tree. Media queries within the narrow shell's own components for device-specific adaptation (safe-area, notch) are permitted."

**L9 -- DENSITY & SPACING: THE ONE-DENSITY LAW -- RATIFY-WITH-CONDITION.**

The one-density ruling is an owner ruling. The 8-step spacing scale verified at tokens.css:172-179. The sizing-token gap is real (the census flagged ~1100 raw px values). No proposed `--size-*` token names collide with existing names (confirmed by grep). One condition:

`--size-control: 36px` is described as "Alias of `--desk-control-h`." But `--desk-control-h: 36px` already exists at tokens.css:289. Similarly, `--size-dock-h: 52px` and `--size-menubar-h: 32px` overlap with the snap tokens that already encode those geometries (`--desk-snap-bottom: 52px` at tokens.css:240, `--desk-snap-top: 54px` at tokens.css:239). Having two token names for the same concept creates confusion about which to use. Condition: the sizing tokens must not duplicate existing component-layer tokens. Retain from the proposed list: `--size-touch` (40px, genuinely new -- replaces raw 40px in row heights that `--desk-surface-row-h` also covers but with a semantic meaning of "minimum touch target"), `--size-key` (48px), `--size-chip` (27px), `--size-btn` (28px), `--size-icon-sm` (16px), `--size-icon-md` (20px), `--size-icon-lg` (32px). Drop `--size-control` (use `--desk-control-h`), `--size-dock-h` (use `--desk-snap-bottom`), `--size-menubar-h` (use `--desk-snap-top` minus margin). Migration of existing raw px to existing tokens is housekeeping; migration to new tokens is for genuinely unrepresented values.

**L10 -- SPARSE SURFACES: THE CHROME-VS-DATA RATIO LAW -- RATIFY.**

The finding is real. Job3-cadence-open.png shows the Cadence window rendering full NOW/NUDGE HISTORY sections with "No open loops" / "No nudges yet" and a "Run now" button for zero data. The prior counsel's own-eyes finding (E, item 5) identified the Meetings "1 RECORDS" with redundant filter bar. The sparse-threshold rule (below 5 items: hide filter, collapse zero metrics, keep verbs, show empty well) is a sound progressive-disclosure pattern. `SPARSE_THRESHOLD` as a JS constant (not CSS token) is correct -- conditional rendering is JS. No collision found in the codebase (confirmed by grep). The rule that the verb bar remains on empty surfaces is important and correct: verbs tell the user what they CAN do.

---

## B. OPEN QUESTIONS -- SETTLED

**Q1: Chair-to-Floor gesture on desktop.**

VERDICT: (a) A dock button with a desk-floor glyph. The button reads as "Floor" or shows the spatial-grid glyph. It replaces the Chair with the floor in-place within the desktop shell viewport.

Rationale: The owner says "one gesture away," which means discoverable. A keyboard shortcut (b) is invisible and fails the discoverability test. Tabs on the Chair header (c) make the floor a peer of the Chair, which contradicts "Chair is HOME" -- HOME does not share a tab strip with its alternatives. A dock button is the existing grammar for "open a power surface." The floor IS a power surface. At narrow width (below 960px), the dock button does not appear because the floor's spatial metaphor does not work on a phone; the narrow shell IS the Chair and the floor is not reachable. This is acceptable because the narrow shell's sheets provide full access to every surface the floor shows.

**Q2: Lane ordering on the Chair.**

VERDICT: Fixed order, no reordering. The order is: Brief, Follow-Through, Meetings, Agents. This is an urgency gradient: what happened (information) -> what you owe (obligations) -> what is scheduled (calendar) -> what is running (automation). Lane hiding (the ability to collapse or remove a lane) is deferred to a future product story, not part of the Chair arc.

Rationale: The Chair is a jobs-first door. Muscle memory demands predictable placement. A user should know that "Meetings is always third" without thinking. Drag-and-drop reordering adds implementation complexity (persistence state, animation, edge cases) for marginal benefit on a surface with only four lanes. The fixed order is a product decision the owner can amend later; building reordering now and then deciding on a fixed order later wastes the work.

**Q3: Delivery/Panes `--accent-cool` on the Chair.**

VERDICT: Everything on the Chair uses ember. A Delivery lane on the Chair does NOT bring `--accent-cool` with it.

Rationale: L5 scopes `--accent-cool` to "the delivery window family." A lane composed into the Chair is not a delivery window -- it is a summary rendered on the Chair's material. The Chair has one accent: ember. When the user clicks "Open Delivery" and the full surface opens in a DeskWindow, that window gets its cool accent per L5. On the Chair door, the Delivery lane's verbs and interactive elements use ember. This preserves the Chair's visual unity. Mixing accents on the door would signal that different lanes belong to different products, which they do not -- they are all HoldSpeak.

---

## C. STOPWATCH FINDINGS -- SCOPE CLASSIFICATION

**F1 (P0, no TODO home): Wave-2 product language. NOT in the Chair arc charter.**

The baseline proves it: Job 3 falls back to a Note because no TODO verb exists. The Cadence surface has zero "Add commitment" affordance (job3-cadence-open.png). The search shelf (job3-search-shelf.png) lists "New Note, New Decision, New Knowledge, New Agent, New Workflow, New Workbench" -- no "New TODO." Follow-Through commitments are meeting-derived only.

But adding a TODO primitive is a new data model. The owner ruling says "composite door, no new data model." The Chair composites what exists; it cannot composite what does not exist yet. Putting "New TODO" in the Chair arc would silently expand the arc from "build the door" to "build the door AND invent a new primitive type AND wire it through the store AND add intelligence extraction." That is unbounded scope.

The Chair arc charter SHOULD include one forward-compatible accommodation: the Follow-Through lane's header verb slot must accept a "New commitment" verb prop (initially null/hidden), so that when Wave-2 lands manual commitment creation, the Chair's door shows it with zero Chair-side work.

**F2 (P1, two ask doors): Partially IN the Chair arc, scoped to capture hero definition.**

The Chair's capture hero (L2, L8) IS the voice-first entry point. The story that defines the capture hero must settle what happens when the user speaks on the Chair: is it a meeting recording? A question? A dictation? This is a capture-hero-scope story, not a "merge Speak and Ask AI" story. The full two-doors resolution (whether Speak and Ask AI merge, whether Ask AI gets a dock slot) is Wave-2 product language.

The Chair arc story should: (a) put the MIC TransportKey on the Chair, (b) define the capture hero's verb grammar (the hero should default to "Record meeting" on tap, with voice-triggered mode selection as a future story), (c) ensure Ask AI is one tap from the Chair via a verb or lane action.

**F3 (P1, silent Deliver failure): NOT in the Chair arc. Elsewhere.**

This is a general error-handling story for the Speak/Delivery pipeline. The Chair's door does not perform deliveries -- it opens surfaces in windows. The standing direction "Errors never overlap UI; error path = mandatory shot leg" (feedback_error_surfaces_never_overlap.md) already mandates fixing this. It belongs in a pipeline-reliability phase or as a rider on the next Speak surface story.

**F4 (P1, no auto-save on Note): NOT in the Chair arc. Wave-2 product language.**

The Chair does not create notes. It opens surfaces in windows. Auto-save on the Note editor is a Note-surface improvement independent of the door. When the user taps "New Note" from the Chair and a DeskWindow opens, the editor's save behavior is the Note surface's concern, not the Chair's.

**F5 (P2, no voice trigger on Record): IN the Chair arc, scoped to capture hero.**

The Chair's capture hero IS the voice-first entry point. The MIC TransportKey on the Chair should support a voice command to start recording (e.g., "start meeting"), not just a pointer click. This is a natural part of the capture hero's definition and falls within the Chair arc's scope. It does not require inventing a new wake-word system -- it requires wiring the existing MicButton's transcription output to the Record verb when the transcription matches a command.

---

## D. ARC SHAPE RECOMMENDATION

Two phases, sequenced. The narrow shell depends on the Chair surface existing.

**Phase 135: The Comfy Chair (12 stories)**

Stories 1-3: LAW CODIFICATION (token amendments + bug fixes from the laws). Story 1: L6 lamp overflow fix + L7 wing affordance fix (both are CSS amendments to existing gadgets.css/pullout.css, small scope, can bundle). Story 2: L9 sizing tokens added to design-tokens.json, generate-tokens.cjs run, migration of the highest-traffic raw px values. Story 3: L10 sparse-surface rule implemented as a shared `SPARSE_THRESHOLD` constant + conditional rendering in LedgerFilter and MetricStrip.

Stories 4-5: CHAIR SURFACE SHELL. Story 4: The Chair component, lane composition contract, capture hero placeholder (MIC TransportKey, Record verb). Story 5: Chair-to-Floor dock button (Q1 settled), fixed lane layout (Q2 settled), Chair as the default HOME surface at desktop width.

Stories 6-9: FOUR LANES. Story 6: Brief lane (composites BriefView summary data). Story 7: Follow-Through lane (composites NOW/OVERDUE triage, with forward-compatible verb slot for future "New commitment"). Story 8: Meetings lane (composites recent meetings, status badges). Story 9: Agents lane (composites sessions, blocked-first sort).

Story 10: CAPTURE HERO DEFINITION. The capture hero's verb grammar: MIC tap starts meeting recording (F5 voice trigger wired), the hero's relationship to Ask AI (one-tap access via a lane verb or hero mode, per F2 scoping).

Story 11: SOUND PALETTE. The sfx.ts module with 6 sounds, AudioContext pool, global toggle in Settings, reduced-motion mute. This is self-contained and does not depend on other stories.

Story 12: WALK + DOCS. Screenshot walk at 1440px and 960px. Update ENTRY docs. Close the phase.

Dependencies on Phase 134 (One Owner): None of the Chair stories require One Owner to land first. The Chair composites existing surfaces (Brief, Follow-Through, Meetings, Agents) that already exist. If Phase 134 changes store shapes, the lane components adapt at integration time. Recommendation: start Phase 135 in parallel with Phase 134; integrate at the end.

**Phase 136: The Narrow Shell (8 stories)**

Story 1: DeskShellRouter -- the 960px routing decision, separate component tree. Story 2: Bottom tab bar (5 slots, MIC hero dead-center, safe-area handling). Story 3: Sheet behavior (full-screen sheets with 18px top-radius, swipe-to-dismiss). Story 4: Chair-at-narrow rendering (lanes stack vertically, capture hero adapts). Story 5-6: Two critical narrow-width bug fixes from the prior counsel P1-face list (dock overflow at 393w, menubar chrome clipped at 393w -- these are eliminated by the narrow shell, but the components must gracefully degrade if the router fails). Story 7: Walk at 393px and 390px (iPhone). Story 8: Docs + close.

Dependencies: Phase 136 depends on Phase 135 stories 4-9 (the Chair surface and its lanes must exist before the narrow shell can render them).

---

## E. WHAT THE LAW BOOK IS MISSING

**1. No window-lifecycle law.**

The baseline finding F7 says windows from previous jobs leak: by Job 4, the Speak window opens alongside a persisted Live meeting window from Job 1. The law book says the Chair opens DeskWindows via `onOpenInWindow`, but says nothing about whether the Chair manages window lifecycle. Under the everything-windows ruling, every lane verb opens a window. If windows never auto-close, a user performing four jobs accumulates four windows. The law book needs a window-management position: does the Chair track which windows it opened and offer a "close all Chair windows" verb, or does the user manage windows manually via the existing close gadgets? The prior counsel did not flag this, but the baseline proves it is a real friction source. My recommendation: the Chair does not auto-close windows. The user manages windows manually, which is consistent with the desktop OS metaphor. But the Chair should not open DUPLICATE windows for the same surface -- if the user clicks "Open Intelligence" twice, the existing Intelligence window focuses rather than spawning a second. This is a single-instance-per-surface rule, not lifecycle management.

**2. The `.btn--sm` height discrepancy.**

The L3 law says the Small variant uses "11px" font but shows "(any above)" for height, implying 28px. The actual `.btn--sm` has `min-height: 24px` (global.css:149-150). The law must state "Small: 24px min-height" explicitly. Similarly, the TransportKey `[data-compact]` variant at gadgets.css:737-746 is `height: 28px; width: auto; min-width: 44px` -- an inline instrument control used in row-height contexts. The law omits this variant entirely. A builder encountering a dense instrument row without knowing about `[data-compact]` would invent a fourth species. Both variants must appear in the L3 table.

**3. No law for the search shelf's role alongside the Chair.**

The baseline finding F10 says the shelf (Cmd+K) is the ONLY discovery mechanism for 15+ programs and every verb. The Chair's door reduces discovery friction for the four main lanes, but everything outside those lanes (Cadence, Context, Activity, Processes, Integrations, Commands, Runs on, Delivery, Panes, and all Settings subsections) remains shelf-dependent. The law book should acknowledge this: the shelf remains the canonical discovery surface. The Chair's lanes do not replace it. The Chair should not attempt to surface everything the shelf surfaces -- that would make the door a second shelf, not a jobs-first front door.

**4. No law for accent-gradient usage boundaries.**

L5 documents `--accent-gradient` (135deg #da9868..#834f32) and says it is for "display moments (hero gradients)." But it does not define what a "display moment" is or where the gradient may appear. The Record Orb already uses the gradient. The capture hero might use it. A lane header might use it. Without a boundary, the gradient will creep onto buttons, cards, and backgrounds, diluting its signal. The law should specify: the accent gradient appears only on the capture hero's MIC key and the Record Orb. Everywhere else, use flat `--accent`.

**5. The TransportKey active state uses `box-shadow: inset 1px 1px 0 var(--bevel-dark), inset -1px -1px 0 var(--bevel-light)` (gadgets.css:709) -- but L1 describes the sunken state as `--desk-window-etch` which is `inset 1px 1px 0 var(--etch-dark), inset -1px -1px 0 var(--etch-light)` (tokens.css:268).** These are different values. The TransportKey active state swaps bevel-light and bevel-dark (high-contrast highlights/shadows) rather than using etch-light and etch-dark (lower-contrast). This means the TransportKey's pressed state is NOT the same as L1's "sunken" state -- it is a bevel inversion, which is visually stronger. The law should note this distinction: sunken wells use `--desk-window-etch` (soft); pressed instrument keys use bevel inversion (hard). Both are "physically depressed" but at different visual intensities, which is correct for their roles (a well is passive; a pressed key demands attention).

---

End of ruling.