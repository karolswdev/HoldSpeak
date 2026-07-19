# Phase 99 — The OS Chrome

**Status:** IN PROGRESS (4/8, 2026-07-18) from the owner's live verdict
on the staged Phase 98 build: "a step, but we still have soooo much
work to do to even begin dreaming of this looking and feeling like an
OS — loads of unstyled selects; those windows still deserve a huge
overhaul" — with a direct study directive: ProzillaOS
(github.com/prozilla-os/ProzillaOS, MIT), "see what we can borrow,
what we can embrace, and deliver this kind of experience."

**Last updated:** 2026-07-18 (HS-99-04 done: OS scrollbars everywhere
+ one menu vocabulary across room/head/dock).

## Why this phase exists

Phase 97 fixed how windows behave; Phase 98 fixed how interiors
compose. Both verdicts came back the same way: better, not an OS. The
ProzillaOS study names WHY — a browser desktop reads as an OS through
a small set of relentless chrome techniques we simply do not have:

- **Native scrollbars everywhere.** We ship ZERO scrollbar CSS — the
  browser's scrollbars are the loudest single "this is a webpage"
  tell on every scrolling window.
- **Native form controls.** `<select>` inherits only the field base;
  its popup, chevron, and options are the browser's. Date inputs,
  file inputs, and search inputs are raw. The owner saw it
  immediately.
- **The title bar is a card header.** Padding, a border-bottom, and
  26px hover-dot verbs — where an OS window has a two-tone bar whose
  full-height square controls reach the edges, and whose close
  hovers red.
- **No tonal depth scale.** One window fill for everything; ProzillaOS
  layers five background steps so head/toolbar/rail/well/body
  separate WITHOUT borders. Borderless tonal separation is most of
  what "solid object" means.
- **No context-menu vocabulary, no icon language, no running-app
  indicator on the dock, no shared hover/selected tint formula.**

Constitution Articles VII and VIII govern; Article X records the
borrow (MIT, attributed). What we already do BETTER than the
reference — focus keyline + rest/front shadows, per-edge resize, snap
tiling, exposé, reduced-motion honesty — are floors and must not
regress.

## The chrome moves (borrowed, named)

1. **Depth is tonal.** A five-step surface ladder (component tokens)
   under every window: head one step above body, wells one below,
   rails/toolbars between — separation by tone, not borders.
2. **The title bar is a bar.** Two-tone head, full-height square
   verb buttons (aspect-ratio 1) flush to the window edge, SVG
   glyphs, close hovers `--danger`; corners square off on maximize;
   the head owns a right-click menu (minimize/maximize/close).
3. **Scrollbars belong to the OS.** Pill thumbs on transparent
   tracks, token-colored, thin, everywhere.
4. **Controls wear the skin.** `appearance: none` selects with a
   drawn chevron and surface-colored options; skinned date/search/
   file/number inputs; every control on the well tone.
5. **One light source.** The window/transient shadows become
   directional and compositional (size/opacity/spread primitives) so
   every floating surface agrees where the light is.
6. **The dock is alive.** A running underline that grows on hover,
   icon scale on hover, the frosted two-layer material.
7. **Tint math, not guesses.** Hover = 20% mix, selected = 40% mix,
   via `color-mix` formulas as tokens.
8. **Motion has a family.** The quart/expo/back easing tokens join
   the duration tokens; chrome transitions reference them.

## Scope

### In

- the study committed as canon (attribution included) + the token
  additions (surface ladder, easings, tint formulas, scrollbar and
  control tokens, compositional shadows);
- the title bar re-craft on `DeskWindowFrame` (all windows: surface,
  pull-out, trust) + head context menu + maximize corner behavior;
- the full native-control skin (select/option, date, search, file,
  number, checkbox row) in one place, gated;
- custom scrollbars, product-wide;
- dock running-indicator + hover motion + frosted layering;
- interior archetypes where they pay: Settings gains the left-rail
  two-pane at wide containers; Meetings gains a status bar; icon
  buttons gain the halo grammar;
- docs as floors; the closeout walk gains a `chrome` leg; shots at
  1440/393 looked at.

### Out

- world/object art and object-to-window morph (The Living World);
- iPad parity (HSM consumes this after);
- new surfaces/routes/capabilities; wire contracts stay byte-identical;
- skin/theme SWITCHING (ProzillaOS's skin registry) — one skin,
  Signal, done well; the token seams it needs are recorded as a rider.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-99-01 | The study and the tokens | done | [story-01-study-and-tokens](./story-01-study-and-tokens.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-99-02 | The title bar is a bar | done | [story-02-title-bar](./story-02-title-bar.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-99-03 | Controls wear the skin | done | [story-03-controls](./story-03-controls.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-99-04 | Scrollbars and menus | done | [story-04-scrollbars-menus](./story-04-scrollbars-menus.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-99-05 | The dock is alive | backlog | [story-05-dock-alive](./story-05-dock-alive.md) | — |
| HS-99-06 | Interior archetypes | backlog | [story-06-interior-archetypes](./story-06-interior-archetypes.md) | — |
| HS-99-07 | The chrome floors, written | backlog | [story-07-docs](./story-07-docs.md) | — |
| HS-99-08 | Closeout: the chrome walk | backlog | [story-08-closeout](./story-08-closeout.md) | — |

## Where we are

**HS-99-04 done (2026-07-18): scrollbars and menus.** The drawn pill
scrollbar is product-wide (with two gotchas recorded: standard
scrollbar properties DISABLE webkit styling in modern Chromium — now
Firefox-scoped — and the headless shell suppresses custom scrollbars,
so the proof is headed, gutter 12px measured). DeskMenuList/Item is
the ONE menu vocabulary (keyboard pattern, transient material,
anchor-corner squaring) behind the room menu, the head menu, and the
new dock chip right-click menu, pinned by vitest. Windows + shelf
legs captured green. `npm run check` green (291). Next: HS-99-05 —
the dock is alive. Earlier:
**HS-99-03 done (2026-07-18): controls wear the skin.** The audit
found the real "unstyled selects": the desk's own components shipped
raw selects/inputs bypassing Signal. Bare controls inside the desk
shell now inherit the Signal foundation at zero specificity — no
component can ship an unstyled control again — at the denser desk
height, with the drawn chevron; options sit on the surface tone,
checkboxes wear the accent, the date indicator and search-cancel
glyph are drawn, and the file button is a Signal face. Config
round-trip captured green; shots looked at. `npm run check` green
(290). Next: HS-99-04 — scrollbars and menus. Earlier:
**HS-99-02 done (2026-07-18): the title bar is a bar.** The whole
window family wears a 40px two-tone head (one tonal step above the
body, no border), full-height square verb buttons flush to the edge
with inline-SVG glyphs, the close hovering `--danger-fill` via the
variable-override pattern, corners squaring off on maximize, and a
right-click head menu (Minimize/Maximize/Close) on the transient
material. The shots caught Escape-with-menu-open closing the window —
the shell now absorbs the first Escape, pinned by vitest. Frame/
depth/placement floors captured green. `npm run check` green (290).
Next: HS-99-03 — controls wear the skin. Earlier:
**HS-99-01 done (2026-07-18): the study is canon and the tokens
exist.** PROZILLAOS_STUDY.md records the borrow/embrace/skip
inventory with MIT attribution and the concrete numbers; nine
component tokens land the tonal ladder (head/rail/well around the
body), the scrollbar thumb pair, the control height, and the easing
family; DESIGN_SYSTEM.md's "The chrome ladder" spec landed BEFORE any
consumer. Token gates clean (no new allow-list entries); `npm run
check` green (289). Next: HS-99-02 — the title bar is a bar.
