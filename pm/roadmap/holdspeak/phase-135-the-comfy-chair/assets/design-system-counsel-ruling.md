I now have everything needed to rule. Here is my complete analysis.

---

## COUNSEL RULING: HOLDSPEAK DESIGN SYSTEM -- INVEST / EXTEND / REBUILD

Examined: structural census (kit-census-report.md), live face walk (face-walk-report.md, 32 screenshots across 16 surfaces x 2 viewports), and spot-checked load-bearing claims directly in the repo at HEAD d4acbbe7.

---

### A. THE VERDICT: EXTEND

**How does it look?** At 1440w, this is a real product with a real identity. The desk floor (desk-floor-1440.png) is genuinely beautiful -- pixel-art sprites on a dark Workbench ground with mono labels, ember accents, and a dock that reads as "this is an operating system, not a web app." The Intelligence pullout (intelligence-brief-1440.png, intelligence-followthrough-1440.png, intelligence-decisions-1440.png) is the best surface in the entire app: purposeful hierarchy, breathing lanes, triage buttons, and search with filter chips that feel like a tool built for a job. The Components gallery (design-components-1440.png) proves this is a real kit: four button variants, transport keys, the full gadget sheet -- all rendered on the surface idiom. At 393w, two surfaces are genuinely broken (Settings > Models is illegible, dock items are unreachable), but most surfaces adapt correctly via @container queries.

**How does it render?** Zero console errors across all 32 surface-width combinations. This is rare and excellent. Motion tokens are thorough (6 durations, 6 easings) with a complete prefers-reduced-motion sweep (tokens.css:314-331). The surface kit uses 32 @container queries to adapt window content to available width. Windows spring-animate via motion/react. The runtime is clean.

**Does it cram busy content into tiny scrollable areas?** No. The face walk found only 4 scroll containers across all 32 combinations, all of them full-height panels (the lowest clientHeight is 541px at 1440w). There are no tiny scrollable boxes. BUT: the cramming problem manifests differently -- it is content density inside well-sized containers. The Settings > Models Destinations table at 393w (settings-models-393.png) reduces destination names to single characters ("A", "L", "L", "L", "O"), KIND to "E", ENDPOINT to "h". The placement lamp text renders at x=-598 (literally 600 pixels off-screen left). This is the single worst visual in the entire product. The problem is not the container; it is a dense table being asked to fit a width it was never designed for.

**Does it have enough primitives to build nearly anything?** Nearly. The surface kit (Surface.tsx + gadgets.tsx, ~2000 lines, 50+ exported components) is comprehensive and heavily adopted: ~214 import references, pullouts at ~95% kit composition, most cores at 70-85%. The no-modal law is perfectly observed (zero `<dialog>` elements in production). In-world editing exists (EditInPlace, InlineEditor, ConfirmVerb). Roving focus and unified keymap provide real keyboard/a11y foundation. The specific gaps are: no virtualized list (DeskListView.tsx:27 explicitly rejects it), no date/time picker, no general combobox/select primitive, no reusable progress bar, no skeleton loading (Signal.tsx:2 documents explicit removal). These are enumerable gaps, not architectural failures. They can be filled without rebuilding anything.

**Therefore: EXTEND.** The kit is real, adopted, and architecturally sound. The three-layer token system is mature. The surface primitives are comprehensive. What is needed is targeted extension of specific gaps and a design-language study to settle the questions the Comfy Chair front door will ask. A rebuild would destroy a working system; an investment without direction would add primitives nobody uses. Extension -- filling the gaps the census identified, fixing the face bugs the walk found, and answering the design-language questions before building the front door -- is the right move.

---

### B. MERGED, RANKED WORK LIST

**P0-broken -- the product is visibly broken here today**

1. **/workbenches deep link returns raw JSON 404.** The route is declared at routes.tsx:66-67 (`path: "/workbenches"`, `surface: "open-workbenches"`) but the hub API does not serve it. A user bookmarking or sharing this URL sees `{"detail":"Not Found"}` on a bare white page with zero desk chrome. Evidence: workbench-1440.png.

2. **Placement lamp text overflows at BOTH widths.** At 1440w (settings-models-1440.png), "ATION SELECTION IGNORED - ASSIGNED PROFILE IS OPENAICOMPATIBLE-KIND; RUNNING ON THE HUB ENGINE" bleeds past the left window edge. A second lamp ("Q6_K - NOT RUNNABLE - NO LANGUAGE MODEL ON THIS HUB. PICK ONE IN SETTINGS UNDER INTELLIGENCE.") bleeds past both edges. At 393w (settings-models-393.png), the lamps compute to x=-598 and x=-301 -- hundreds of pixels off-screen. The gadget-lamp element (gadgets.css:633) uses `white-space: nowrap` with no overflow handling for long system messages. This is broken at desktop width, not just narrow.

**P1-face -- the face is wrong; a user sees this and loses confidence**

3. **Settings > Models Destinations table at 393w is illegible.** Names show single characters. KIND shows "E". This is the single worst visual in the product. The GadgetTable (gadgets.tsx:483) has no responsive strategy for its column count -- it renders every column at every width.

4. **Dock overflow at 393w is systemic.** The dock (dock.css:2-16) is `display: flex` with no `flex-wrap`, no `overflow: auto`, positioned `left: 50%; transform: translateX(-50%)`. At 393w it extends from x=376 to x=872+ -- nearly 500px past the viewport edge. Items past "Meetings" are unreachable with no scroll affordance. This affects EVERY surface at 393w.

5. **Desk floor object labels collide at 393w.** Four labels in the middle row merge into one unreadable string: "Phase 132 de/Users/karol/dHoldSpeak -- Roadmap Mobile Runtim...". Evidence: desk-floor-393.png.

6. **Menubar chrome clipped at 393w.** The clock, search chip, and right-side chrome extend past x=393 with no way to reach them.

7. **Window title-bar traffic lights are precision targets at both widths.** The close/minimize/maximize dots are ~10-12px with near-zero padding between them. Visible in every windowed screenshot. This is a motor-precision issue beyond the menubar finding. (The face walk noted menubar touch targets at 22px but missed the window controls being even smaller.)

**P2-kit-gap -- the kit cannot build this; a future surface will be blocked**

8. **No virtualized list.** DeskListView.tsx:27: "Rows per page -- a plain 'show more' pagination, no virtualization dep." Any surface with 500+ items (artifact archives, meeting history over months, large zones) will hit this wall.

9. **No date/time picker.** No kit component wraps date or time selection. Native `<input type="date">` would inherit base control styling (global.css:83) but would break the Workbench material (chrome styling, dark ground, mono type).

10. **No general combobox/select primitive.** InletAutocomplete (350 lines), RailsPicker (182 lines), RunsOnPicker (94 lines), WorkbenchTemplatePicker (148 lines) are all domain-specific one-offs. A new surface needing a searchable dropdown must build its own.

11. **No reusable progress bar.** WorkbenchWindow.tsx has ad-hoc `runProgress` state. The next surface with long-running operations must reinvent this.

12. **Sound tokens absent.** Motion tokens are thorough (6 durations, 6 easings, reduced-motion sweep). Zero audio tokens exist anywhere. Voice is a core product surface (MicButton, RecordOrb, dictation pipeline). Mic open/close, recording start/stop, delivery landed -- all lack audio feedback design tokens.

13. **No skeleton loading.** Signal.tsx:2 documents explicit removal in the gadget-kit sweep. SurfaceState handles loading with a spinner. No content-shape skeleton exists for perceived-performance during data fetches.

**P3-debt -- it works but the house is not in order**

14. **~1100 raw px values bypass spacing tokens.** The six heaviest CSS files (surface.css:304, gadgets.css:181, chrome-menus.css:142, attention.css:110, mission-control.css:108, workbench-config.css:98) use raw px for layout geometry. The token layer provides 8 spacing steps but no layout-specific sizing tokens between `--space-8` (4rem) and `--desk-window-pad-x` (14px), making raw px the practical default.

15. **react-app.css: 414 lines of legacy pre-desk styles loaded globally.** 29 legacy class selectors (`.signal-panel`, `.welcome-*`, `.presence-*`, `.dialog-form`) serve only WelcomePage and PresencePage -- two routes that use zero kit components. Loaded via main.tsx:8.

16. **Three button faces are documented but not codified.** Button (verb), desk-chip (chrome), TransportKey (instrument) are three deliberate species per Signal.tsx:1-7. The documentation says when to use each, but there is no visual spec or Storybook-like reference beyond the Components gallery. A new builder would have to read source comments to know which to use.

**Where my ranking differs from the auditors:**

The face walk's finding #7 ("1px borders everywhere, 2px law not enforced") is **wrong**. I spot-checked the tokens directly. The "2px" in Phase 110's material model ("opaque, beveled, 2px, mono") refers to RADII, not border width. Evidence:
- `--radius-xs` through `--radius-pill` are all `2px` (tokens.css:180-184, design-tokens.json:590-608)
- `--desk-window-radius: 2px` (tokens.css:262)
- Borders are intentionally 1px per HS-110-01: `--border: #2a2e3e; /* HS-110-01: solid 1px border, not alpha wash */` (tokens.css:114)
- Windows additionally wear `--desk-glass-edge: inset 0 0 0 1px var(--border)` (tokens.css:293), giving them 1px CSS border + 1px inset shadow = ~2px visual weight
- The window-chrome.css:14 comment reads: "1px keyline ring; rest windows quiet down"

There is no border-width violation. The 2px contract is the radius contract, and it is perfectly enforced. I have excluded this from the work list.

The census flagged the 6px font as concerning. I spot-checked: `font-size: 6px` at gadgets.css:356 is the stepper arrow buttons -- tiny up/down chevron glyphs in StepperGadget. This is a decorative micro-element, not readable content. The face walk's density metrics picked it up because it scanned computed font sizes, but it is not a real readability issue. Not included in the work list.

I promoted the placement lamp overflow from the face walk's finding #4 to P0-broken because my eyes confirm it is broken at 1440w too (settings-models-1440.png shows two full lines of lamp text bleeding past window edges at desktop width), not only at 393w.

---

### C. THE NARROW-VIEWPORT QUESTION

**Recommendation: (iii) Dual grammar -- the desktop shell has a minimum supported width; below it, serve a distinct narrow grammar using the same surface primitives.**

Rationale in three parts:

**Why not (i) "first-class responsive":** The desk metaphor IS the product. The multi-window model (DeskWindow with drag/resize/snap), the spatial floor (desk objects with pixel sprites), the dock (fixed-position flex centered taskbar), and the menubar (5 menu items + system tray) are architecturally a desktop operating system. The dock alone (dock.css:2-16) is `position: fixed; left: 50%; transform: translateX(-50%); display: flex` with no wrap or scroll -- it physically cannot fit at 393px. The window model assumes drag handles, snap zones, and a field larger than a single window. Trying to make this responsive with CSS media queries would be like making macOS Finder responsive -- it is the wrong tool for the job, and it would compromise the desktop experience that gives HoldSpeak its identity. Standing direction: "web = React+Vite, desk-first /" -- first, not only, but the desk grammar should not be degraded.

**Why not (ii) "explicitly de-scope narrow":** Because the SURFACE PRIMITIVES already work at narrow widths. The Intelligence Follow-Through at 393w (intelligence-followthrough-393.png) is proof: the triage lanes (NOW/WAITING/UNASSIGNED/OVERDUE) stack vertically, commitment items show their text and time-ago labels, the segment tabs size correctly. SurfaceSection, SurfaceLedgerRow, SurfaceRow, the gadget kit -- they all adapt via 32 @container queries. The problem is not the content; it is the desktop SHELL. De-scoping narrow entirely would throw away working surface adaptation.

**Why (iii) dual grammar:** Declare a minimum supported width for the desktop grammar (960px). Below that, the router serves a narrow grammar: a stacked list of surfaces (Intelligence, Speak, Meetings, Agents, Settings) using the same Surface primitives, with a tab bar or navigation list instead of the dock, and no DeskWindow/DeskMenuBar/desk floor. The surface kit is the shared contract between both grammars. The desktop grammar is today's desk. The narrow grammar is a distinct entry point that reuses the same room content. This is a ROUTING decision (which shell to render at what width), not a CSS responsive decision. The Comfy Chair front door could be the narrow grammar's natural home -- "one beautiful jobs-first front door" is already a different shell from the spatial desk floor.

---

### D. DESIGN-LANGUAGE BEAT: QUESTIONS THE STUDY MUST SETTLE BEFORE THE COMFY CHAIR

1. **What is the entry grammar?** The desk floor arranges everything spatially (pixel sprites in a field). The Comfy Chair implies a jobs-first list ("what do I need to do"). Are these two entry points to the same desk, or does the Comfy Chair replace the spatial floor? If both coexist, which is the default?

2. **Which content is a window and which is a view?** Today everything lives inside a DeskWindow (draggable, resizable, closeable). The Comfy Chair implies some content should be embedded views (Intelligence brief inline, meeting list inline) rather than windows. Where is the line between "this opens in a window" and "this is part of the front door surface"?

3. **One button language or three codified species?** Today: Button (`.btn`, 4 variants -- verb), desk-chip (`.desk-chip`, 205 uses -- chrome), TransportKey (`.gadget-transport-key` -- instrument). Signal.tsx:1-7 documents the split. Does Workbench 2.0 carry all three, retire one, or add a fourth (e.g., a "card action" for the Comfy Chair)? If all three survive, produce a one-page visual spec (context/example/never-use) so builders do not guess.

4. **What is the narrow shell?** Per section C, the dual grammar needs a narrow entry: tab bar, hamburger, bottom sheet stack, or something else. The Comfy Chair might BE the narrow shell. Settle the navigation pattern before building any routing.

5. **What is the color hierarchy beyond ember?** The accent is ember orange (`--accent: #a86e4a`). Status colors are established (ok/warn/danger/info). But `--p-color-blue-450: #5b8def` exists for delivery/panes surfaces, the glow pool has 6 distinct tints, and zone tints add 6 more. Does the Comfy Chair introduce a second accent? Are glow-pool colors decorative only, or do they extend to UI elements (badges, tags, category indicators)?

6. **What is the data-scale contract?** DeskListView.tsx:27 rejects virtualization at 100-row pagination. The Comfy Chair front door will aggregate items from meetings, commitments, decisions, and activity into one view. How many items does the front door need to handle: dozens (no virtualization needed), hundreds (pagination sufficient), or thousands (virtualization required)? This determines whether item #8 in the work list is P2 or P0.

7. **Sound tokens: yes or no?** Motion is thorough. Sound is absent. Voice is a core product surface. Does the Comfy Chair acknowledge audio feedback (mic open/close clicks, recording-started tones, delivery-landed chimes), or is HoldSpeak silent-by-design? If yes, define the token layer (`--sfx-*`) before building surfaces that need it.

8. **What is the density contract?** The surface kit adapts via @container queries (32 total) but has no user-toggled density mode. The Comfy Chair as a "jobs-first front door" may show 3 items or 30. Does it offer a compact/comfortable toggle, or is one density the law?

9. **What does the front door own vs. compose?** Today the desk floor shows everything. The Comfy Chair implies filtering by urgency/job. Is the front door a curated composite of existing surfaces (Intelligence brief + overdue commitments + recent meetings), or a new surface type with its own data model? If composite, define the composition contract (which surface primitives plug in, what props they accept, how they communicate selection).

10. **What is the minimum supported desktop width?** The current kit has no declared minimum. The desk floor works at 1440w but some content (Settings > Models) is already dense. Is the minimum 960px, 1024px, or 1280px? This bounds every layout decision in the Comfy Chair.

---

### E. WHAT BOTH AUDITS MISSED

These observations come from my own eyes on the screenshots, not from either audit's findings.

1. **Inactive tab affordance is weak on the Intelligence pullout.** In intelligence-brief-1440.png, the active tab "BRIEF" has a clear bordered treatment with ember accent. But "FOLLOW-THROUGH" and "DECISIONS" look like plain text -- no border, no background, no underline. Only hover reveals them as interactive. This repeats at intelligence-followthrough-393.png. The same pattern appears on the window filing strips (SPEAK/JOURNAL/BLOCKS on the Speak window, SETTINGS/GUIDE on Settings, OUTCOMES/RECORD/ARTIFACTS on Meetings). The active state is clear; the inactive affordance is not.

2. **Two lamp-text overflows at 1440w, not one.** The face walk identified one placement lamp overflow. Looking at settings-models-1440.png, there are TWO full-width system messages overflowing the window: the first about "ATION SELECTION IGNORED" and the second about "Q6_K - NOT RUNNABLE - NO LANGUAGE MODEL ON THIS HUB." Both bleed past window edges at desktop width. The gadget-lamp uses `white-space: nowrap` (gadgets.css:641) and the system-message text is not truncated or wrapped.

3. **The Speak room footer has two visual grammars in one bar.** In speak-room-1440.png, the footer's left side shows status text ("LOCAL / PIPELINE OFF") with a colored dot, while the right side shows bordered verb buttons ("Review / Export"). These are two different visual idioms in the same horizontal bar. The Intelligence pullout footer ("Acknowledge / Defer / Speak" at intelligence-brief-1440.png) uses the verb-button idiom consistently. The Speak footer mixes status-readout and verb-buttons without a visual separator.

4. **The Components gallery has no anchor navigation.** In design-components-1440.png, "Scalar" is cut off at the bottom of the viewport. The gallery scrolls (ratio 2.82) but has no table of contents, section anchors, or sidebar navigation. A builder reviewing the kit must scroll linearly through the entire gallery to find a specific component. This matters more as the kit grows.

5. **The Meetings window at 1440w (speak-room-1440.png, left window) shows "1 RECORDS" with a redundant filter bar.** The filter shows "Filter... 1" next to "Filters" -- a filter count badge next to a filter verb, both visible when there is only one record. At low data volumes, the filter UI consumes more visual space than the data it filters. Neither audit flagged the information-to-chrome ratio on sparse surfaces.

---

End of ruling.