> **STATUS: RULED (2026-08-16).** All ten laws RATIFIED — L2, L3, L4, L8,
> L9 carry counsel conditions; the three open questions are settled
> (Chair-to-Floor = dock button; fixed lane order Brief/Follow-Through/
> Meetings/Agents; ember-only on the Chair); five additions demanded
> (single-instance-per-surface window rule, .btn--sm 24px + TransportKey
> [data-compact] variants in L3, the shelf remains canonical discovery,
> accent-gradient confined to capture hero + Record Orb, etch-vs-bevel-
> inversion distinction in L1). Workers implement THIS DRAFT plus the
> full ruling record side by side: comfy-chair-laws-counsel-ruling.md.

# THE COMFY CHAIR -- DESIGN-LANGUAGE LAW BOOK

Draft 1 -- 2026-08-16
Repo: HoldSpeak main @ b4c6aced
Grounded in: owner rulings 1-10, counsel ruling (design-system-counsel-ruling.md),
kit census (kit-census-report.md), face walk (face-walk-report.md, 32 screenshots),
live token source (design-tokens.json, tokens.css), component vocabulary
(Surface.tsx, gadgets.tsx, global.css, pullout.css, chrome-menus.css, dock.css).

Every law below is binding on all future UI stories in the Comfy Chair arc
and afterward. Where a law amends or adds tokens, the canonical path is
`web/design-tokens.json`; CSS changes flow from `scripts/generate-tokens.cjs`.

---

## L1 -- DEPTH: THE LIGHT-SOURCE / BEVEL LAW

### Rule

One virtual light source sits at the top-left corner. Depth is communicated
exclusively through bevels and etches -- never through Gaussian box-shadows,
blur, or transparency. The depth grammar has exactly three states:

| State | Meaning | Visual | Token |
|-------|---------|--------|-------|
| **Raised** | Actionable / grabbable | `--desk-window-bevel`: top-left light, bottom-right dark | `--bevel-light`, `--bevel-dark` |
| **Sunken** | Content well / input / pressed tab | `--desk-window-etch`: top-left dark, bottom-right light | `--etch-light`, `--etch-dark` |
| **Flat** | Inert surface / background | No inset shadow | `box-shadow: none` or `--elev-0` |

**Pressed state timing.** When a raised element is pressed, it transitions
to sunken in `--duration-micro` (60ms) -- immediate, no ease. On release it
returns to raised in `--duration-short` (120ms) with `--ease-standard`. This
models a physical key depression: instant down, slight spring up. The
TransportKey already implements this correctly (gadgets.css:702-712); Button
uses `transform: translateY(1px)` (global.css:179) which is the
simplified variant permitted for the 28px verb species.

**Existing token map:**

- `--desk-window-bevel: inset 1px 1px 0 var(--bevel-light), inset -1px -1px 0 var(--bevel-dark)` -- raised (tokens.css:267)
- `--desk-window-etch: inset 1px 1px 0 var(--etch-dark), inset -1px -1px 0 var(--etch-light)` -- sunken (tokens.css:268)
- `--desk-window-shadow: none` -- no Gaussian shadows (tokens.css:263)
- `--desk-window-shadow-rest: none` -- no shadow distinction (tokens.css:264)
- `--elev-0` through `--elev-4` exist but `--elev-1` through `--elev-4` are reserved for the GL world canvas layer only (desk-object drop shadows on the spatial floor). No DOM element in the desk shell uses `--elev-2` or higher.
- `--gleam-1/2/3` provide top-highlight on fabricated faces (tokens.css:299-301). These are inner gleams, not elevation shadows.

### Forbids

- `box-shadow` with positive y-offset blur on any desk element (use bevel/etch).
- `backdrop-filter` anywhere (tokens.css:266 `--desk-window-blur: none`).
- Raised surfaces that are not interactive. If it has a bevel, the user can
  grab it, press it, or click it. Passive content sits flat or sunken.
- Mixing raised and sunken on the same element simultaneously.

### Worked example

A lane card on the Chair's door shows a commitment from Follow-Through.
The card body is **flat** (no shadow, sits on the surface material). Its
"Open" verb is a **raised** `.btn` with `--desk-window-bevel`. On pointer
down, the verb transitions to `transform: translateY(1px)` for 60ms. A
sunken `SurfaceWell` inside the card holds the commitment text -- it wears
`--desk-window-etch` and is never clickable.

---

## L2 -- THE DOOR: THE CHAIR'S ANATOMY

### Rule

The Chair is HOME at every width. It is a jobs-first composite surface --
not a new data model, but a composition of existing surfaces (Brief,
Follow-Through, meetings, agent receipts) into a single front door. The
spatial desk floor remains intact, one gesture away, as the power room.

**Anatomy (top to bottom at desktop width):**

```
+------------------------------------------------------+
|  MENUBAR (unchanged)                                  |
+------------------------------------------------------+
|                                                       |
|  CAPTURE HERO                                         |
|  [  mic/record center -- raised TransportKey pair  ]  |
|  (the voice-first entry point; L8 specifies narrow)   |
|                                                       |
+------------------------------------------------------+
|                                                       |
|  LANES                                                |
|  Each lane is a composed surface plugged in via the   |
|  composition contract below.                          |
|                                                       |
|  Lane: BRIEF          Lane: FOLLOW-THROUGH            |
|  Lane: MEETINGS       Lane: AGENTS                    |
|                                                       |
+------------------------------------------------------+
|  DOCK (unchanged at desktop; becomes tab bar narrow)  |
+------------------------------------------------------+
```

**The composition contract.** A lane is a React component that:

1. Accepts `maxItems: number` (the curated-dozen bound, default 12, max 24).
2. Renders using only Surface primitives (`SurfaceSection`, `SurfaceRow`,
   `SurfaceLedgerRow`, `MetricStrip`).
3. Exposes an `onOpenInWindow: (id: string) => void` callback -- every row
   action that needs deep work calls this to open a DeskWindow (or full-screen
   sheet below 960px). The lane itself never enters deep work.
4. Provides a lane header: `SurfaceSection` with a label and a trailing
   verb count (e.g., "WAITING 02"). The header's click opens the full
   surface in a DeskWindow.
5. Provides an optional lane footer: a single `SurfaceRow` showing "N more
   -- Open SURFACE_NAME" when items exceed `maxItems`.
6. Never renders its own loading spinner -- it returns `null` until data is
   ready; the Chair shows content as it arrives (no skeleton, no spinner
   per lane -- the surface itself shows `SurfaceState` only if ALL lanes
   are empty).

**Information-at-a-glance under the everything-windows ruling.** Lanes
inform: they show titles, counts, time-ago labels, status badges. They do
not show full transcripts, full text bodies, or inline editors. Every verb
that would begin work opens a DeskWindow. The door is a dashboard, not a
workspace.

**Data scale.** Lanes show curated dozens (12-24 items). Full ledgers
open in windows. No virtualization is needed on the door.

### Tokens added

- `--door-lane-gap: var(--space-5)` (1.5rem) -- vertical gap between lanes.
- `--door-lane-max-items: 12` -- default curated-dozen bound (CSS custom
  property for container-query-aware truncation).
- `--door-capture-h: 80px` -- capture hero height.

### Forbids

- Inline editing on the door (editing happens in windows).
- Any lane rendering more than `maxItems` rows without the "N more" footer.
- New data models for door content (compose from existing stores).
- Scroll containers inside individual lanes (the door itself scrolls as one
  page; individual lanes are flat lists capped at `maxItems`).

### Worked example

The BRIEF lane renders `BriefView`'s summary data: "2 things waiting."
followed by the Changed/Broke/Waiting/Decisions section headers with their
counts. Clicking "Waiting 02" opens the Intelligence pullout as a
DeskWindow. The lane footer reads "Open Intelligence" and opens the full
pullout. The FOLLOW-THROUGH lane shows the first 12 commitments from the
NOW and OVERDUE triage buckets, each as a `SurfaceLedgerRow`. Clicking a
commitment opens its detail in a DeskWindow. The MEETINGS lane shows the
last 5 meetings as `SurfaceRow` items with date, title, and segment count.

---

## L3 -- BUTTONS: THE THREE-SPECIES SPEC

### Rule

HoldSpeak has exactly three button species. No fourth species is permitted.

#### Species 1: Button (`.btn`) -- THE VERB

**What it is.** The action verb. "Deliver", "Import", "Record meeting",
"Acknowledge", "Add command". A sentence verb made physical.

**Anatomy.** 28px min-height, mono 12px/600, horizontal padding `--space-3`
(0.75rem), 1px border, square corners (radius 0), raised bevel
(`--desk-window-bevel`). Pressed: `translateY(1px)`.

**Variants.**

| Variant | Border | Background | Text | Use |
|---------|--------|------------|------|-----|
| Default | `--border` | `--surface-2` | `--text` | Most verbs |
| Primary | `--accent` | `--accent` | `--accent-on` | THE primary action on a surface |
| Ghost | transparent | transparent | `--text` | Quiet secondary actions |
| Danger | `--danger-fill` | `--danger-fill` | `--white` | Destructive verbs (delete, kill) |
| Small | (any above) | (any above) | 11px | Dense contexts (ledger row inline verbs) |

**Context.** Appears in: `SurfaceVerbs` (the sticky verb bar at surface
top), ledger row trailing slots, footer verb slots, the Components gallery.

**Never use for:** Navigation (use desk-chip). Instrument control (use
TransportKey). Status display. Labels. Any element that is not a user-
initiated action verb.

#### Species 2: desk-chip (`.desk-chip`) -- THE CHROME

**What it is.** Shell chrome and navigation furniture. Dock launchers,
menubar items, filter chips, state toggles, filing zone chips.

**Anatomy.** 27px height, padding 0 12px, mono `--font-size-sm`, 1px
border, square corners (radius 0), raised bevel (`--desk-window-bevel`).
Pressed: `scale(0.94)`. Hover: border turns `--accent`, background turns
`--accent-tint`.

**Variants.**

| Variant | Treatment | Use |
|---------|-----------|-----|
| Default | Opaque `--surface-2` fill | Dock, chrome bar |
| Quiet | `--text-muted` color | Filing chips, secondary toggles |
| Pressed | `aria-pressed="true"`, accent tint | Active filter, active zone |

**Context.** Appears in: the dock, menubar trailing chrome (search, status),
DeskFilingStrip zone/knowledge chips, filter chips in ledgers.

**Never use for:** Verbs that change data (use Button). Audio/recording
controls (use TransportKey). The primary action on any surface.

#### Species 3: TransportKey (`.gadget-transport-key`) -- THE INSTRUMENT

**What it is.** A momentary physical key for instrument-like control. TALK,
STOP, KILL, SEND, MIC, RECORD. The key IS down when active -- inverted
video, bevel flips to sunken. No glow, no pulse, ever.

**Anatomy.** 48x48px square, mono 9px/650, 1px border, square corners,
raised bevel. Active/pressed: background flips to `--accent`, color flips
to `--accent-on`, bevel inverts to `--desk-window-etch` values. Disabled:
`opacity: 0.55`.

**Variants.**

| Variant | Treatment | Use |
|---------|-----------|-----|
| Default | Standard raised | TALK, SEND |
| Danger | `--danger-signal` tint | STOP, KILL |
| Active | Inverted video (accent bg) | Mic listening, key held |

**Context.** Appears in: Speak room transport row (TALK/STOP/KILL/SEND),
MicButton (voice capture), the Chair's capture hero.

**Never use for:** Navigation. Data verbs (save, delete, export). Any
action whose state is not binary (on/off, pressed/released). If the
action has a text-label verb longer than one word, use Button instead.

### Forbids

- A fourth button species (including "card action", "link button",
  "icon-only button" as a distinct class).
- Using Button (`.btn`) where the element navigates without data mutation.
- TransportKey for any non-instrument control.
- desk-chip with a verb label that mutates data (unless the chip is a
  toggle showing `aria-pressed` state, which is a state verb, not a
  mutation verb).

---

## L4 -- SOUND: THE MECHANICAL PALETTE

### Rule

HoldSpeak ships a small mechanical sound palette: six named sounds, ON by
default, one global toggle. The character is "mechanical, dry, short" -- a
relay click, a solenoid latch, a card-edge striker. No synthesizer pads,
no notification chimes, no UI whooshes. The sounds are part of the
Workbench material: the desk has weight and moving parts.

**The six sounds:**

| # | Token | Trigger | Character | Duration |
|---|-------|---------|-----------|----------|
| 1 | `--sfx-key-down` | TransportKey pressed (MIC open, TALK start) | Relay click -- a dry snap, one cycle, no ring | <80ms |
| 2 | `--sfx-key-up` | TransportKey released (MIC close, TALK stop) | Solenoid release -- slightly softer than key-down | <60ms |
| 3 | `--sfx-latch` | Recording started / meeting capture begins | Card latch engaging -- a mechanical click with a tiny settle | <120ms |
| 4 | `--sfx-land` | Delivery landed / artifact received / result arrived | Object landing on desk -- a soft thud with no bounce | <100ms |
| 5 | `--sfx-file` | Item filed into zone / relationship toggled | Filing-cabinet drawer click -- crisp, thin | <60ms |
| 6 | `--sfx-error` | Admission refused / operation failed | A stuck key -- the same relay as key-down but doubled (click-click) | <120ms |

**Toggle behavior.** One global toggle in Settings (a `CheckGadget` under
the APPEARANCE group). Default: ON. The toggle sets a CSS class on `<html>`
and a Zustand flag. Sound playback checks both:

1. `document.documentElement.classList.contains('sfx-off')` -- immediate,
   no store subscription needed in hot paths.
2. `prefers-reduced-motion: reduce` -- automatically mutes (the same media
   query that zeros all `--duration-*` tokens in tokens.css:314-331).

Sound files are self-contained: inline base64 data URIs in a single
`sfx.ts` module (no network fetches, no CDN). Each sound is a sub-120ms
WAV or OGG. Total budget: <100KB for all six.

### Tokens added (to design-tokens.json, component layer)

```
--sfx-key-down:   url(data:audio/wav;base64,...)
--sfx-key-up:     url(data:audio/wav;base64,...)
--sfx-latch:      url(data:audio/wav;base64,...)
--sfx-land:       url(data:audio/wav;base64,...)
--sfx-file:       url(data:audio/wav;base64,...)
--sfx-error:      url(data:audio/wav;base64,...)
```

Note: CSS custom properties cannot play audio. The `--sfx-*` names are
token NAMES used by the `sfx.ts` module as keys into an AudioContext pool.
The tokens in design-tokens.json document the canonical names; the runtime
module owns the actual audio data and playback. The generated tokens.css
will emit them as comments (documentation), not as functional CSS values.

### Forbids

- Sounds longer than 150ms.
- Melodic or tonal sounds (no chimes, no synth, no voice feedback).
- Per-surface or per-feature sound toggles (one toggle rules all).
- Sound on hover, scroll, or passive observation.
- Sound that plays without a user-initiated action in the same event
  handler (no ambient, no timer-triggered).

### Worked example

User clicks the MIC TransportKey on the Chair's capture hero. On
`pointerdown`, the key visually sinks (bevel inverts), and `sfx.play('key-down')` fires. The relay-click plays in <80ms. When the user clicks
again to stop, `sfx.play('key-up')` fires the softer release sound. If a
delivery lands while the mic is open, `sfx.play('land')` fires
independently -- sounds do not queue or interrupt each other; overlapping
playback is fine for sub-120ms mechanical clicks.

---

## L5 -- COLOR: THE EMBER + KIND-TINT LAW

### Rule

**One interactive accent: ember.** Every interactive element -- buttons,
focus rings, active tabs, selected rows, links, toggles -- uses the ember
accent family exclusively:

| Token | Value | Use |
|-------|-------|-----|
| `--accent` | `#a86e4a` | Default interactive accent |
| `--accent-hover` | `#bc8058` | Hover state |
| `--accent-press` | `#936041` | Pressed state |
| `--accent-tint` | `rgba(168,110,74,0.12)` | Selection background, active chip |
| `--accent-glow` | `rgba(168,110,74,0.28)` | Focus glow, recording attention |
| `--accent-gradient` | `135deg #da9868..#834f32` | Display moments (hero gradients) |

**Status colors are functional, not decorative:**

| Token | Hex | Use |
|-------|-----|-----|
| `--ok` | `#34d399` | OK / connected / success |
| `--warn-signal` | `#fbbf24` | Warning / degraded |
| `--danger-signal` | `#f87171` | Error / destructive |
| `--info` | `#56c7f5` | Informational / local |

**Kind-tints are categorical, for objects and zones only.** The glow-pool
and zone-tint families paint desk objects and zone trays to help the user
distinguish KINDS of things at a glance:

| Kind | Glow token | Hex |
|------|-----------|-----|
| Meeting | `--glow-meeting` | `#56C7F5` |
| Note | `--glow-note` | `#34D399` |
| Knowledge | `--glow-kb` | `#FBBF24` |
| Persona/Coder | `--glow-recipe` | `#FF6B35` |
| Artifact | `--glow-artifact` | `#FF9E64` |
| Chain/Workflow | `--glow-chain` | `#A78BFA` |
| Zone/Directory | `--glow-directory` | `#E0A458` |

Kind-tints appear on: desk-object sprite glows, zone tray backgrounds
(at low alpha), lane header icons on the Chair (as a small colored dot or
glyph tint), and the glow pool in the GL layer.

**The `--accent-cool` exception.** `--accent-cool` (`#5b8def`) exists for
the Delivery/Panes surfaces (tokens.css:213). It is the ONLY non-ember
interactive accent permitted in the entire app, and it is scoped to the
delivery window family only. No new cool-accent usage is permitted without
a constitution amendment.

### Forbids

- Kind-tints on controls (buttons, toggles, inputs, links, tabs). A
  meeting-related button is still ember, not cyan.
- Kind-tints on text color (labels are `--text`, `--text-muted`, or
  `--text-faint` -- never a glow color).
- A second general-purpose interactive accent (beyond `--accent-cool`'s
  scoped exception).
- New glow-pool colors without a corresponding new DeskPrimitive kind.
- Raw hex in component CSS for any color that has a token.

### Worked example

The MEETINGS lane on the Chair door shows five meetings. Each meeting row
has a small `--glow-meeting` (#56C7F5) dot to the left of the title --
this is the kind-tint, categorizing the item. The "Open" verb on the row
is a `.btn` (default variant) with ember hover (`--accent` border on
hover). Clicking it opens the meeting in a DeskWindow. The meeting's status
badge says "INTELLIGENCE OFF" in `--text-muted` -- never in cyan, even
though meetings are cyan-kind objects.

---

## L6 -- TEXT OVERFLOW: THE LAMP / SYSTEM-MESSAGE LAW

### Rule

System text (placement lamps, status messages, error banners, long
enumerations) MUST wrap or truncate with a full-text affordance. The
current `.gadget-lamp` uses `white-space: nowrap` (gadgets.css:641) with
no overflow handling, causing text to bleed hundreds of pixels off-screen
at both 1440w and 393w (counsel P0-broken #2, face-walk finding #4).

**Three overflow treatments, chosen by context:**

| Context | Treatment | CSS | When |
|---------|-----------|-----|------|
| **Lamp/status inline** | Truncate + title tooltip | `white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;` with `title={fullText}` | The lamp sits on a row with other controls (e.g., RUNS ON picker row) |
| **System message block** | Wrap | `white-space: normal; word-break: break-word;` | The message is the primary content of its container (e.g., a placement warning that deserves reading) |
| **Ledger/list primary** | Truncate + open-in-window | `text-overflow: ellipsis` with an `onOpenInWindow` click handler | Row titles in ledgers where the full item opens in a window |

### Tokens amended

Amend `.gadget-lamp` in gadgets.css:

```css
.gadget-lamp {
  /* REMOVE: white-space: nowrap; */
  /* ADD: */
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

Add a block-message variant:

```css
.gadget-lamp.is-block {
  white-space: normal;
  word-break: break-word;
  text-overflow: clip;
}
```

New component token:

- `--desk-lamp-max-width: 100%` -- lamps respect their container's width.

### Forbids

- `white-space: nowrap` on any element that renders user-generated or
  system-generated text of unbounded length, without a paired
  `overflow: hidden; text-overflow: ellipsis; max-width` constraint.
- Lamp text that overflows its parent container's bounding box.
- Truncation without ANY affordance (title tooltip at minimum; a click-to-
  expand or open-in-window is preferred for important messages).

### Worked example

The Settings > Models DESTINATIONS section shows a placement lamp:
"ATION SELECTION IGNORED -- ASSIGNED PROFILE IS OPENAICOMPATIBLE-KIND;
RUNNING ON THE HUB ENGINE". Under this law, the lamp renders with
`.gadget-lamp.is-block` because it is a block-level placement warning. It
wraps within the Models section's container width. At 393w, it wraps to
multiple lines rather than flying 600px off-screen. The lamp's dot stays
at the start of the first line.

---

## L7 -- TABS & AFFORDANCE: THE WING TREATMENT

### Rule

Inactive tabs ("wings") on window filing strips and segment controls must
read as interactive at rest, without requiring hover to discover them.
The counsel's own-eyes finding (ruling section E, item 1) identified that
"FOLLOW-THROUGH" and "DECISIONS" look like plain text on the Intelligence
pullout -- only hover reveals them as interactive.

**The treatment.** Inactive wings already have `border: 1px solid var(--border)` and `color: var(--text-faint)` (pullout.css:298-301). The
problem is that `--text-faint` (#767e8d at ~4.7:1 contrast) combined with
a border that is nearly invisible against the dark surface makes the tab
read as a label, not a control.

**The fix -- two properties:**

1. **Inactive wing text: `--text-muted`** (not `--text-faint`). `--text-muted`
   is #9ba2b0 at ~7.1:1 contrast -- visibly lighter, reads as interactive
   text. The active wing stays `--text` (#f2f3f5).
2. **Inactive wing background: `var(--wash-1)`** (rgba 255,255,255,0.035).
   A faint fill that distinguishes the tab from the bare surface, making
   the border visible and the tab read as a distinct clickable region.

**Active wing** (unchanged): background `var(--desk-window-well)`, bevel
inverts to `--desk-window-etch`, color `--text`.

### Tokens amended

Amend `.desk-wing` in pullout.css:298-306:

```css
.desk-next .desk-wing {
  /* ... existing properties ... */
  color: var(--text-muted);     /* was: var(--text-faint) */
  background: var(--wash-1);    /* was: none */
}
```

### Forbids

- Inactive tabs with `color: var(--text-faint)` -- too faint for
  interactive affordance.
- Tabs with `background: none` or `background: transparent` as their rest
  state (a tab must have a visible fill to read as a control).
- Tab strips where the inactive state is visually indistinguishable from
  a section label or eyebrow text.

### Worked example

The Intelligence pullout's wing strip shows three tabs: BRIEF,
FOLLOW-THROUGH, DECISIONS. BRIEF is active (sunken well, full white text).
FOLLOW-THROUGH and DECISIONS are inactive: they show in #9ba2b0 muted text
on a faint wash-1 background with visible 1px borders. A user scanning the
pullout can immediately see that FOLLOW-THROUGH and DECISIONS are clickable
tabs, not decorative labels. On hover, the text brightens to `--text` and
the background lifts to `--wash-2`.

---

## L8 -- THE NARROW SHELL: TAB BAR SPEC

### Rule

Below 960px viewport width, the desktop grammar (menubar, dock, spatial
floor, multi-window) is replaced by the narrow shell. This is a ROUTING
decision (`DeskShellRouter` checks `window.innerWidth` and the
`matchMedia('(min-width: 960px)')` listener), not CSS responsive squeezing.

**The narrow shell IS the Chair.** Below 960px, the Chair fills the
viewport. Its lanes stack vertically. Every action opens a full-screen
sheet (a DeskWindow rendered at 100vw x 100vh with no drag/resize, only
a close gesture).

**Bottom tab bar anatomy:**

```
+--------------------------------------------------+
|  [Brief]  [Speak]  [ MIC ]  [Meet]  [Agents]    |
+--------------------------------------------------+
```

| Slot | Position | Content |
|------|----------|---------|
| 1 (left) | Fixed | Brief (Intelligence) -- glyph + optional badge count |
| 2 | Fixed | Speak -- glyph |
| 3 (center) | RAISED, dead-center | MIC/RECORD hero -- a TransportKey (48px raised above the bar by 12px) |
| 4 | Fixed | Meetings -- glyph + optional badge count |
| 5 (right) | Fixed | Agents -- glyph |

**Mic-center geometry.** The center slot extends 12px above the tab bar's
top edge. The MIC TransportKey sits at `bottom: 12px` relative to the
bar top, visually breaking the bar line to signal the voice-first entry
point. The bar itself is 56px tall (48px content + 8px bottom safe-area
padding for notched devices).

**Tab bar tokens:**

- `--door-tabbar-h: 56px` -- tab bar height (content).
- `--door-tabbar-safe: env(safe-area-inset-bottom, 0px)` -- notch padding.
- `--door-tabbar-hero-lift: 12px` -- mic key lift above bar.

**Sheet behavior.** Tapping a tab bar item opens its surface as a
full-screen sheet that slides up from the bottom with `--ease-emphasized`
over `--duration-medium` (200ms). The sheet has `--desk-sheet-top-radius`
(18px) at the top corners (the existing phone-sheet grip silhouette,
tokens.css:271). Swiping down or tapping the close grip dismisses the
sheet.

**What the 960px handoff preserves:**

- All Surface primitives render identically (they already adapt via
  @container queries on `.desk-surface-body`).
- The token layer is unchanged.
- DeskWindow's spring animation still fires (for the sheet slide).
- The capture hero (mic/record) keeps the same TransportKey component.
- The same verb species apply (Button, desk-chip, TransportKey).

**What changes at 960px:**

- No menubar (the title and system tray move into a minimal status bar).
- No dock (replaced by the tab bar).
- No spatial floor (the Chair lanes are the home).
- No window drag/resize/snap (sheets are full-screen).
- No multi-window tiling.

### Forbids

- CSS `@media (max-width: 959px)` hacks on the desktop shell components.
  The narrow shell is a separate component tree, not a responsive variant.
- More than 5 tab bar slots (the tab bar is a fixed menu, not a scrollable
  strip).
- The MIC hero key smaller than 48x48px on any viewport.
- A hamburger menu, drawer navigation, or "more" overflow on the tab bar.

### Worked example

On a 390px iPhone viewport, the user sees the Chair: the capture hero
(MIC key raised dead-center) sits above two lanes (BRIEF showing
"2 things waiting", FOLLOW-THROUGH showing 3 overdue items). The bottom
tab bar shows five glyphs. Tapping "Meet" slides up a full-screen sheet
showing the Meetings surface (OUTCOMES/RECORD/ARTIFACTS tabs at the top,
meeting list below). The sheet has 18px top-radius corners and a drag grip.
Swiping down dismisses it.

---

## L9 -- DENSITY & SPACING: THE ONE-DENSITY LAW

### Rule

HoldSpeak has one density. It is OS density (compact, tool-grade), not
page density (magazine, reading-grade). There is no user toggle. Density
adapts to the container, not to a preference -- the same surface shows
more columns in a wide window and fewer in a narrow sheet, via the 32
existing `@container surface` queries.

**The spacing scale.** The existing 8-step scale:

| Token | Value | Use |
|-------|-------|-----|
| `--space-1` | 0.25rem (4px) | Icon gaps, tight padding |
| `--space-2` | 0.5rem (8px) | Row internal gaps, chip gaps |
| `--space-3` | 0.75rem (12px) | Button padding, section inline padding |
| `--space-4` | 1rem (16px) | Standard padding, content gaps |
| `--space-5` | 1.5rem (24px) | Section gaps, lane gaps |
| `--space-6` | 2rem (32px) | Surface-level breathing |
| `--space-7` | 3rem (48px) | Major region separation |
| `--space-8` | 4rem (64px) | Page-level top/bottom padding |

**The sizing-token gap.** The census identified ~1100 raw px values
because there are no tokens between `--space-8` (64px) and the specific
component sizes (`--desk-window-pad-x`: 14px, `--desk-surface-row-h`:
40px, `--desk-control-h`: 36px). Builders default to raw px for mid-range
layout geometry. Fill this gap with named sizing tokens:

| New token | Value | Use |
|-----------|-------|-----|
| `--size-touch` | 40px | Minimum touch target (replaces raw `40px` in row heights) |
| `--size-control` | 36px | Alias of `--desk-control-h` (selects, dense inputs) |
| `--size-key` | 48px | TransportKey / hero instrument (replaces raw `48px`) |
| `--size-chip` | 27px | desk-chip height (replaces raw `27px`) |
| `--size-btn` | 28px | Button min-height (replaces raw `28px`) |
| `--size-dock-h` | 52px | Dock strip height (replaces raw values in snap tokens) |
| `--size-menubar-h` | 32px | Menubar height (replaces raw values) |
| `--size-icon-sm` | 16px | Small icon (glyph in button/chip) |
| `--size-icon-md` | 20px | Medium icon (dock launch, lane header) |
| `--size-icon-lg` | 32px | Large icon (desk object sprite) |

These are component-layer tokens in design-tokens.json. They do not
replace `--space-*` (spacing between things) -- they name the SIZE OF
things. The distinction: spacing tokens set gaps and padding; sizing
tokens set widths and heights of specific elements.

### Forbids

- A user-facing density toggle (compact/comfortable/spacious).
- Raw px for any value that matches a token in the table above (new code
  must use the token; existing code migrates as surfaces are touched).
- Spacing below `--space-1` (4px) between interactive elements (the
  counsel flagged 0px min-gap between interactive elements at both widths).
- Font sizes below 9px for any text the user is expected to read. The 6px
  stepper arrows (gadgets.css:356) are permitted as decorative micro-glyphs
  only.

### Worked example

A new surface needs a control row. Instead of writing `height: 40px` (raw
px), the builder writes `min-height: var(--size-touch)`. The row contains
a Button (`min-height: var(--size-btn)`) and a desk-chip (`height: var(--size-chip)`). The gap between them is `var(--space-2)` (8px). At
narrow container widths, a `@container surface` query may stack them
vertically with `gap: var(--space-2)` between. No density toggle exists;
the container query handles the reflow.

---

## L10 -- SPARSE SURFACES: THE CHROME-VS-DATA RATIO LAW

### Rule

When a surface has little or no data, it must show LESS chrome, not more.
The counsel's own-eyes finding (ruling section E, item 5) identified the
Meetings window at 1440w showing "1 RECORDS" with a redundant filter bar:
"Filter... 1" next to "Filters" -- a filter count badge next to a filter
verb, both visible when there is one record. The filter UI consumed more
visual space than the data it filtered.

**The sparse-surface rule:** A surface is "sparse" when it has fewer items
than a threshold (default: 5). Sparse surfaces must:

1. **Hide filter UI.** `LedgerFilter` and similar filter bars must not
   render when the item count is below the sparse threshold. A filter over
   3 items is noise.
2. **Collapse metric strips.** `MetricStrip` with all-zero counts should
   render as a single summary line ("Nothing here." or "1 meeting") rather
   than a strip of labeled zeros.
3. **Never show pagination controls** on sparse surfaces (no "Show more"
   when there are 2 items).
4. **Keep the verb bar.** Action verbs ("Import", "Record meeting") remain
   even on empty surfaces -- they tell the user what they CAN do. The verb
   bar is signal, not chrome.
5. **Show the empty well.** If zero items, show `SurfaceState` with
   `emptyLabel` -- the existing empty-well pattern (global.css:468) is
   correct. Do not show an empty filter bar above an empty well.

**Sparse threshold token:**

- `--sparse-threshold: 5` -- below this item count, sparse rules apply.
  This is a JS constant in a shared module, not a CSS token (sparse
  behavior is conditional rendering, not styling).

### Forbids

- Filter UI rendering when `items.length < SPARSE_THRESHOLD`.
- Metric strips with all-zero values rendering as a full strip.
- Chrome that takes up more vertical space than the data it serves.
- Empty surfaces showing anything other than: the verb bar (if it has
  verbs) + the empty well.

### Worked example

The Meetings surface opens with 1 meeting. Under the old behavior, it
shows: title bar, OUTCOMES/RECORD/ARTIFACTS tabs, "1 RECORDS" heading,
"FILTER [Filter...] 1 [Filters]" bar, one meeting row, footer. The filter
bar consumes ~40px for a feature that has no filtering work to do.

Under this law, when `items.length < 5`, the filter bar does not render.
The surface shows: title bar, tabs, "MEETINGS" section heading with "1"
count, one meeting row, footer. The filter bar reappears when the fifth
meeting is recorded. If the surface has zero meetings, it shows: title bar,
tabs, `SurfaceState` with "No meetings yet", the "Record meeting" verb in
`SurfaceVerbs`. Clean.

---

## OPEN QUESTIONS FOR COUNSEL

These are genuinely two-sided calls that the rulings did not settle and
that this law book cannot resolve unilaterally.

**Q1: Chair-to-Floor gesture on desktop.**
The Chair is HOME; the spatial floor is one gesture away. What is that
gesture? Candidates: (a) a dock button labeled "Desk" that replaces the
Chair with the floor in-place; (b) a keyboard shortcut (Cmd+Shift+D or
similar) that toggles between Chair and Floor; (c) a wing/tab on the
Chair's own header ("CHAIR / FLOOR" tabs). Option (a) is discoverable but
adds a dock item. Option (b) is fast but invisible. Option (c) is explicit
but blurs the Chair's identity as the HOME surface. The ruling says the
floor stays "one gesture away" but does not name the gesture.

**Q2: Lane ordering on the Chair.**
The ruling establishes that the Chair composites Brief, Follow-Through,
meetings, and agent receipts. It does not specify their order or whether
the order is fixed or user-reorderable. Two-sided because: fixed order
ensures the door is always predictable (the user builds muscle memory for
where things are), but reorderable lanes let the user put the most
important surface first (a meeting-heavy day vs. a coding day). A middle
ground -- fixed order with the option to HIDE lanes -- would let the user
declutter without introducing drag-and-drop complexity on the door.

**Q3: Delivery/Panes `--accent-cool` on the Chair.**
The Chair composes lanes from existing surfaces. If a Delivery lane appears
on the Chair, does it bring `--accent-cool` (#5b8def) with it, or does
everything on the Chair use ember? The color law (L5) says `--accent-cool`
is scoped to the delivery window family. But if a delivery lane is
composed into the Chair, it is no longer "in a delivery window." Either
the Delivery lane loses its cool accent on the Chair (color consistency)
or the Chair accepts the scoped exception (surface identity). This is a
genuine tension between the color law and the composition contract.
