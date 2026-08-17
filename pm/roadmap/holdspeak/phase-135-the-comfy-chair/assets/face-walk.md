I now have all the evidence needed to write the complete report. Here is the full audit.

---

LIVE BEHAVIORAL AUDIT -- HOLDSPEAK DESIGN SYSTEM FACE WALK
Branch main, HEAD d4acbbe7, 2026-08-16
Walked 16 surfaces x 2 viewports = 32 screenshots

All screenshots and per-surface JSON metrics are at:
`/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/f380fecb-4e2f-4c34-9ce4-e1babbe72b2a/scratchpad/face-walk/`


## SURFACE-BY-SURFACE VERDICTS

**Desk Floor** -- At 1440 this is genuinely beautiful. The dark ground, pixel-art sprites, and mono labels read as a coherent desktop metaphor. The dock is clean, the menubar is tight, the system bar states what matters ("THIS DEVICE", clock, search). At 393, the desk objects in the middle row physically overlap their text labels ("Phase 132 de/Users/karol/dHoldSpeak -- Roadmap Mobile Runtim..."). The labels collide into a single unreadable run. The dock itself overflows the viewport entirely -- items past "Meetings" are off-screen right with no scroll affordance. Evidence: `desk-floor-1440.png`, `desk-floor-393.png`.

**Live Meeting** -- At 1440 the window is proportioned well: the TRANSCRIPT section and the "Start meeting" button are breathing. The footer ("THIS DEVICE / READY") is compact and informative. At 393 the window renders as a bottom sheet and still looks usable, though the dock is hidden behind it. No cramming. Evidence: `live-meeting-1440.png`, `live-meeting-393.png`.

**Meetings List** -- At 1440, clean and sparse: 1 RECORDS, filter bar, meeting row with date/title/segment-count/intel-state. At 393, the Live Meeting window and Meetings window stack vertically; the Meetings window is truncated at the bottom but the content that shows (1 meeting row) is readable. Evidence: `meetings-list-1440.png`, `meetings-list-393.png`.

**Speak Room** -- At 1440, the Speak and Settings > Models windows tile side by side (deep-link to /profiles opens Settings alongside Speak). The Speak surface has clear state chips (PIPELINE OFF, TARGET CLAUDE CODE, MIC CLOSED, BUDGET 600 MS), the UTTERANCE textarea breathes, and the footer (LOCAL / PIPELINE OFF / Review / Export) is tidy. At 393 the Speak window fills the sheet with no cramming -- all chips wrap. Evidence: `speak-room-1440.png`, `speak-room-393.png`.

**Workbench** -- BROKEN ROUTE. Both widths render raw JSON: `{"detail":"Not Found"}` on a white background. The /workbenches deep link is declared in routes.tsx line 68 (surface: "open-workbenches") but the hub's API evidently does not serve that HTML path. The workbench is reachable by opening the desk object directly (the walk harness proves this), but the deep-link route is dead. Evidence: `workbench-1440.png`, `workbench-393.png`.

**Settings > Models (/profiles)** -- At 1440, a densely packed but functional DESTINATIONS table with NAME/KIND/ENDPOINT/MODEL/KEY/STATE columns. "UNSUPPORTED" truncates with ellipsis even at full width. The placement lamp text ("ATION SELECTION IGNORED - ASSIGNED PROFILE IS OPENAICOMPATIBLE-KIND; RUNNING ON THE HUB ENGINE") bleeds past the left edge of the window. At 393, the Destinations table is catastrophically cramped: names show single letters ("A", "L", "L", "L", "O"), KIND shows "E", ENDPOINT shows "h". The placement status lamps have computed left positions of -301px and -598px, literally hundreds of pixels off-screen left. This is the worst cram surface in the app. Evidence: `settings-models-1440.png`, `settings-models-393.png`.

**Settings General** -- At 1440, a clean icon grid (APPEARANCE, HOTKEY, TRANSCRIPTION, etc.) with a POSTURE readout at the bottom. At 393 the icon grid reflows to 3 columns and breathes. One of the best-adapting surfaces. Evidence: `settings-general-1440.png`, `settings-general-393.png`.

**Cadence** -- At 1440, the Cadence window shows "No open loops / No nudges yet" with Run now. Simple, honest, breathing. At 393, it renders in a stacked sheet with Settings above it -- still readable. Evidence: `cadence-1440.png`, `cadence-393.png`.

**Coder/Agents (companion)** -- At 1440, the Agents window shows "CREW 0 - SESSIONS 1 - BLOCKED 1" with the session path and an Answer button. Spare and functional. Evidence: `coder-companion-1440.png`.

**Activity** -- At 1440, "No activity yet" empty state with FILTER. At 393, four windows stack (Settings, Cadence, Agents, Activity) and the screen is a tower of title bars -- but each window's visible content is not cramped because the content is minimal. Evidence: `activity-1440.png`, `activity-393.png`.

**Commands** -- At 1440, "No voice commands" with Add command. At 393, the Commands window sits as a bottom sheet below Cadence -- readable but the Cadence window above it is truncated mid-sprite. Evidence: `commands-1440.png`, `commands-393.png`.

**Design Components** -- At 1440, the Components gallery shows the gadget kit: button variants (Primary/Secondary/Ghost/Destructive), dense action row (TALK/STOP/KILL/SEND), the gadget sheet (Boolean/Pick/Text/Long text/Number/Scalar). This is the only surface with a legitimate scroll container (ratio 2.82 at 1440, 2.91 at 393) -- expected for a gallery. 6px font found here. Evidence: `design-components-1440.png`, `design-components-393.png`.

**Intelligence Brief** -- At 1440, the pullout renders as a right-side panel: "2 things waiting." with Changed 00, Broke 00, Waiting 02, Your Decisions 00, and Acknowledge/Defer/Speak buttons. Clean hierarchy, mono type. At 393, the Intelligence pullout fills a bottom sheet; "Nothing here." expanded under Changed -- the user sees the detail without scrolling. The segment tabs (BRIEF / FOLLOW-THROUGH / DECISIONS) are correctly sized. Evidence: `intelligence-brief-1440.png`, `intelligence-brief-393.png`.

**Intelligence Follow-Through** -- At 1440, four triage lanes (NOW 0, WAITING 1, UNASSIGNED 1, OVERDUE 1) with commitment items, owner badges, and time-ago labels. At 393, the same lanes stack vertically in a full-width sheet. Both widths feel purposeful and clear. The "Decide the streaming-partials questi..." truncation is correct (ellipsis). Evidence: `intelligence-followthrough-1440.png`, `intelligence-followthrough-393.png`.

**Intelligence Decisions** -- At 1440, the receipts list with WHY search, WHY ONLY filter chip, ALL DECISIONS count, and two decision records with GOVERNING/SUPERSEDED badges. Compact and readable. Evidence: `intelligence-decisions-1440.png`.

**Meeting Detail** -- Could not be opened via click at either width. The desk object ("Phase 132 desk review") is visible but the menubar intercepts all pointer events on it. The walk harness uses `dispatch_event("click")` to bypass this -- a real user would have the same z-order problem. Evidence: `meeting-detail-1440.png`, `meeting-detail-393.png`.


## CRAM INDEX -- TOP 10 SCROLL CONTAINERS

Across all 32 surface-width combinations, only 4 scroll containers were detected:

| Rank | Surface | Width | Container | clientH | scrollH | Ratio | CRAM Flag | Nested |
|------|---------|-------|-----------|---------|---------|-------|-----------|--------|
| 1 | design-components | 393 | .desk-surface-body | 587 | 1709 | 2.91 | No | 0 |
| 2 | design-components | 1440 | .desk-surface-body | 541 | 1527 | 2.82 | No | 0 |
| 3 | settings-models | 393 | .desk-surface-body | 587 | 1153 | 1.96 | No | 0 |
| 4 | settings-models | 1440 | .desk-surface-body | 541 | 825 | 1.52 | No | 0 |

No containers trip the CRAM flag (clientHeight < 320px AND scrollHeight > 2x clientHeight). No nested scrollers found anywhere. The answer to "does it cram busy content into tiny scrollable areas?" is: the scroll containers themselves are full-height panels, not tiny boxes. The cramming problem is elsewhere -- it is in the CONTENT INSIDE those panels (the Destinations table at 393w) and in the DOCK overflowing off-screen.


## HORIZONTAL OVERFLOW VIOLATIONS

**SYSTEMIC at 393w.** Every single surface at 393w has the dock overflowing the viewport. The dock items extend from x=376 to x=872+ (nearly 500px past the 393px viewport edge). Elements affected:
- `.desk-chrome-tr` (top-right chrome: clock, search chip)
- `.desk-dock-launch` buttons and their labels and sprites
- `.desk-wings` (the window door controls)

Body-level horizontal scroll is not triggered (the browser does not show a scrollbar), meaning these elements are painted beyond the viewport with no access path. The dock items past "Meetings" are unreachable at 393w.

**Settings > Models specific:** `.gadget-lamp` elements at computed left=-301px and left=-598px. The placement status text literally renders hundreds of pixels to the left of the viewport.

| Surface | Offending Element | Left | Right | Viewport |
|---------|-------------------|------|-------|----------|
| ALL 393w | .desk-dock-launch (items 4+) | 376-872 | 474-872 | 393 |
| ALL 393w | .desk-chrome-tr | 271 | 428 | 393 |
| ALL 393w | .desk-clock | 271 | 428 | 393 |
| settings-models-393 | .gadget-lamp | -598 | 372 | 393 |
| settings-models-393 | .gadget-lamp | -301 | 372 | 393 |


## TRUNCATION AND CLIPPING VIOLATIONS

| Type | Surface | Element | Content |
|------|---------|---------|---------|
| silent-clip | ALL 393w | .desk-surface-window (Speak) | Entire Speak window silently clipped |
| silent-clip | ALL 393w | .desk-surface-window (Meetings) | Entire Meetings window silently clipped |
| ellipsis | settings-models-1440 | .gadget-table-cell | "UNSUPPORTED" truncated at full width |
| ellipsis | settings-models-393 | .gadget-table-cell | "NEEDS_KEY", "UNSUPPORTED" truncated |
| ellipsis | intelligence-decisions | .surface-ledger-primary | "Keep meetings..." / "Run meetings..." |
| ellipsis | intelligence-followthrough | .surface-ledger-primary | "Decide the streaming-partials..." |
| ellipsis | ALL 393w dock | .desk-dock-label | "Live meeting" truncated |
| label-overlap | desk-floor-393 | object labels | "Phase 132 de" + "/Users/karol/d" collide |

The silent clipping of background windows at 393w is expected (the sheet model hides earlier windows). The label overlap on the desk floor at 393w is a genuine readability bug.


## DENSITY AND BREATHING

| Surface | Width | Text/100k px^2 | Smallest Font | Min Gap | Small Targets (<40px) |
|---------|-------|----------------|---------------|---------|----------------------|
| design-components | 393 | 79.74 | 6px | 0 | 10 |
| settings-models | 393 | 65.70 | 6px | 0 | 10 |
| commands | 393 | 51.67 | 9px | 0 | 10 |
| activity | 393 | 48.38 | 9px | 0 | 10 |
| coder-companion | 393 | 44.80 | 9px | 0 | 10 |
| cadence | 393 | 41.21 | 9px | 0 | 10 |
| settings-general | 393 | 37.93 | 9px | 0 | 10 |
| speak-room | 393 | 30.16 | 9px | 0 | 10 |
| desk-floor | 1440 | 2.39 | 10px | 1 | 10 |

The menubar buttons at BOTH widths are 22px tall -- below the 40px touch-target guideline. MinGap between interactive elements is 0px on most surfaces, meaning interactive elements are flush against each other. The 6px font at settings-models and design-components is extremely small.


## MATERIAL CONFORMANCE

| Element | Background | Border | Font | Violations |
|---------|------------|--------|------|------------|
| .desk-menubar | rgb(28,31,39) opaque | 0px 0px 1px (bottom only) | JetBrains Mono | border: 1px not 2px |
| .desk-dock | rgb(28,31,39) opaque | 1px 0px 0px (top only) | JetBrains Mono | border: 1px not 2px |
| .desk-window | (varies) | 1px | JetBrains Mono | border: 1px not 2px |
| .desk-surface-body | rgba(0,0,0,0) transparent | -- | -- | translucent background |
| button (.desk-mark) | rgba(0,0,0,0) transparent | 0px | JetBrains Mono | transparent (OK for buttons) |
| .desk-chip | rgba(0,0,0,0) transparent | 0px | JetBrains Mono | transparent (OK for chips) |

No blur/backdrop-filter violations. The 2px border law is violated globally: menubar, dock, and all windows use 1px borders. The surface-body is transparent, which inherits its parent's background.


## CONSOLE ERRORS

ZERO across all 32 surface-width combinations. This is excellent and rare.


## UNREACHABLE SURFACES

- **Workbench via /workbenches**: Returns raw `{"detail":"Not Found"}`. Must be opened from the desk object, not the deep link.
- **Meeting detail**: Menubar z-order intercepts clicks on desk objects positioned beneath it. The walk harness works around this with `dispatch_event`, but a real pointer user cannot open these objects when they sit under the menubar's bounding box.


## TOP 10 FINDINGS FOR COUNSEL

1. **[BROKEN] /workbenches deep link returns raw JSON 404** -- The route is declared in routes.tsx:68 but the hub does not serve it. A user bookmarking or sharing this URL sees `{"detail":"Not Found"}` on a white page. Evidence: `workbench-1440.png`, `workbench-393.png`.

2. **[CRAM] Settings > Models Destinations table at 393w is illegible** -- Names reduced to single characters ("A", "L", "O"), KIND to "E", ENDPOINT to "h". The placement lamp text extends to x=-598. This is the single worst visual on the narrow viewport. Evidence: `settings-models-393.png`.

3. **[DENSITY] Dock overflow at 393w: items past "Meetings" are unreachable** -- The dock extends from x=376 to x=872 at 393px viewport width. There is no scroll, no wrap, no collapse. Everything past the third item is painted off-screen with no access path. This is systemic across every surface. Evidence: `desk-floor-393.png` and all other 393w shots.

4. **[CLIP] Placement status lamp text overflows window at 1440w** -- "ATION SELECTION IGNORED - ASSIGNED PROFILE IS OPENAICOMPATIBLE-KIND; RUNNING ON THE HUB ENGINE" extends past the left edge of the Settings window even at full desktop width. Evidence: `settings-models-1440.png`.

5. **[DENSITY] Menubar touch targets are 22px tall at both widths** -- All menubar buttons (HoldSpeak, Desk, Object, Go, Window) are 22px tall, well below the 40px mobile guideline. The min-gap between interactive elements is 0px on most surfaces. Evidence: density metrics across all surfaces.

6. **[CLIP] Desk object labels overlap at 393w** -- "Phase 132 de" and "/Users/karol/d" and "HoldSpeak -- Roadmap" and "Mobile Runtim..." run together into an unreadable string on the middle row. Evidence: `desk-floor-393.png`.

7. **[MATERIAL] 1px borders everywhere, 2px law not enforced** -- Menubar, dock, and all windows use 1px borders. The design system spec calls for 2px. Evidence: material metrics (borderWidth: "1px" on .desk-menubar, .desk-dock, .desk-window).

8. **[DELIGHT] Zero console errors across all 32 surface-width combinations** -- Not a single pageerror or console.error on any surface at any width. The runtime is clean.

9. **[DELIGHT] Intelligence pullout at both widths is the best surface in the app** -- The Brief view ("2 things waiting."), the Follow-Through lanes (NOW/WAITING/UNASSIGNED/OVERDUE), and the Decisions ledger (with search, WHY ONLY filter, GOVERNING/SUPERSEDED badges) are purposeful, readable, and breathe at both viewports. The segment tabs, triage buttons, and commitment rows adapt correctly. Evidence: `intelligence-brief-1440.png`, `intelligence-followthrough-1440.png`, `intelligence-decisions-1440.png`, `intelligence-followthrough-393.png`.

10. **[DELIGHT] Desk floor at 1440 is visually distinctive** -- The dark ground with pixel-art sprites, mono labels, dock with sprite icons, and the system menubar create a coherent "desktop OS" metaphor that reads as a real product with an identity, not a generic web app. Evidence: `desk-floor-1440.png`.