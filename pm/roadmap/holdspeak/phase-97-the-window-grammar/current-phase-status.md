# Phase 97 — The Window Grammar

**Status:** IN PROGRESS (7/9, 2026-07-18) — from the owner's direct
verdict on the Desk OS state.

**Last updated:** 2026-07-18 (HS-97-07 done; one shelf, quiet chrome).

## Why this phase exists

The owner's verdict, verbatim in spirit: the windows are ugly, there is
zero cohesion between the desk and the windows it opens, zero "I'm
sitting in an operating system" feeling — so zero incentive to use what
HoldSpeak offers. A live screenshot audit against the UAT rig (run
`run-20260718T093259-572c93`, :8788) confirmed it mechanically:

- **Every window renders shadowless.** `generate-tokens.cjs` resolves a
  `{ref}` only when the value is nothing but the reference; composite
  values like `0 26px 70px {primitive.color.shadow.60}` pass through
  verbatim, so `--desk-window-shadow` and `--desk-transient-shadow` emit
  invalid CSS the browser drops. With near-identical fills and no
  elevation, stacked windows merge into one smear. The token gate never
  noticed.
- **Windows land badly.** The cascade stacks new windows onto the same
  top-left corner clipping each other's title bars while most of the
  stage sits empty; in the audit one window spawned partially off-screen
  left and the Delivery board opened mostly below the viewport (clamping
  runs on drag, not on open).
- **The arrangement forgets.** `panelOrder` (z/focus) resets on every
  reload; the persisted `min` array is force-restored on load (dead
  state). Article VII.3 says the user's arrangement is sacred and
  persists — today only rects and maximize do.
- **Focus is invisible.** The front window and the rest wear the same
  material; nothing dims, nothing lifts.
- **Motion is half a story.** Windows spring in but vanish in one frame
  on close; minimize teleports; the dock chip never receives its window.
- **The chrome menu is unstyled** (five gray default rows); on the
  phone the Panes pill occludes the sheet's action row.
- **The shelf is fragmented.** Running chips bottom-left, a Panes pill,
  a Delivery pill, a Desk memory pill bottom-right — four shelf
  fragments where an OS has one dock.
- **The title bars shout.** Mono eyebrows restate the title in a second
  vocabulary ("ATTENTION AND RECEIPTS Desk memory"); the stage floor
  carries instructional prose ("Select an item for actions").

This phase makes the window grammar an OS grammar: land well, stack
honestly, remember everything, move with intent, switch visibly, one
shelf. It executes Constitution Articles VII (one quiet grammar, the
arrangement is sacred) and VIII (native-grade craft; physics are
contracts — once shipped, a floor). Article IX governs every proof:
production bundle, real viewports, screenshots looked at.

Content re-crafting (the demoted cores' internals) and the world's
object/ground treatment are explicitly NOT this phase — they are the
staged follow-ups (Native Surfaces; The Living World).

## Scope

### In

- the token generator resolving embedded references, the emitted CSS
  free of unresolved braces by mechanical gate, shadows restored;
- an open-placement engine: windows open fully on-viewport in free
  space, clamped against the chrome band and dock; cascade only as
  saturation fallback;
- persistence completed: z order survives reload; minimize state made
  honest (persist meaningfully or stop writing it);
- focused-vs-rest window states on the one material; close/minimize/
  restore motion (reduced-motion honored);
- snap ghost preview during drag; edge resize; double-click maximize;
- an exposé overview and a visible MRU switcher;
- one dock carrying launchers and running windows; the eyebrow demoted;
  the stage prose removed;
- docs as physics floors; the closeout walk extended to the new grammar.

### Out

- redesigning the demoted cores' content (Native Surfaces, next);
- world/object art, grounding, object-to-window morph (The Living
  World, after);
- iPad/Diorama parity (the HSM track consumes this grammar later);
- new surfaces, routes, or capabilities.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-97-01 | The shadow returns | done | [story-01-shadow-returns](./story-01-shadow-returns.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-97-02 | A window lands well | done | [story-02-placement](./story-02-placement.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-97-03 | The arrangement is sacred | done | [story-03-arrangement-persists](./story-03-arrangement-persists.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-97-04 | Focus and depth | done | [story-04-focus-depth](./story-04-focus-depth.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-97-05 | Hands on the frame | done | [story-05-hands-on-frame](./story-05-hands-on-frame.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-97-06 | The switcher | done | [story-06-switcher](./story-06-switcher.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-97-07 | One shelf, quiet chrome | done | [story-07-one-shelf](./story-07-one-shelf.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-97-08 | The physics floors, written | backlog | [story-08-docs](./story-08-docs.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-97-09 | Closeout: the grammar walk | backlog | [story-09-closeout](./story-09-closeout.md) | [evidence-story-09](./evidence-story-09.md) |

## Where we are

**HS-97-07 done (2026-07-18): one shelf, quiet chrome.** The dock is
the one shelf, centered on the bottom edge: launcher verbs for Desk
memory, Delivery, and Panes (a launcher registry beside the window
registry; badges ride the chips; an open surface's launcher folds into
its window chip) with THE RECORD ORB seated at the dock's center — the
four floating fragments (`.desk-attention-launch`, `.desk-dlv-tab`,
`.desk-panepicker-launch`, `.desk-hint`) are deleted from DOM and CSS
(walk-verified at zero; allow-list 68 → 67). The chrome quiets: no
window head renders the mono eyebrow (prop kept for compatibility),
and the stage prose ("Select an item for actions") is gone per Article
VII.1. Existing walks retargeted to the dock launchers and re-proven
(`windows` leg green). Proven by the `shelf` walk at 1440 and 393
(`assets/shelf-idle-1440.png`, `assets/shelf-open-1440.png`,
`assets/shelf-393.png` LOOKED AT — the bottom edge is finally one
built thing); `npm run check` green (279 web tests). Earlier:
**HS-97-06 done (2026-07-18): the switcher.** Exposé: the dock's ⊞
verb or Ctrl+ArrowUp fans every open window into a non-overlapping
pick grid (`exposeLayout`, pure + pinned; live shells scale into their
cells via compositor transforms, minimized windows join as dimmed
cards), the world dims behind a scrim, click or Enter focuses (a
minimized pick restores), Escape or a backdrop click cancels with the
shells animating home; instant under reduced motion. Ctrl+` cycling is
finally visible: a transient strip names every open window with the
landing target highlighted, fading after settling. Proven by the
`switcher` walk on the production bundle (exposé fans 3 with 1 dim,
click focuses, Escape cancels, the strip names all and fades;
`assets/switcher-expose-1440.png` + `assets/switcher-strip-1440.png`
LOOKED AT — the strip even caught the Meetings window mid-restore
flying from its chip) and the storm inside the envelope (8.3ms median,
1 layout event); `npm run check` green (279 web tests). Earlier:
**HS-97-05 done (2026-07-18): hands on the frame.** The snap ghost:
while a head drag hovers a snap region, the landing tile renders live
as a translucent accent preview (`SnapGhost`, module-level publisher,
z transient) and the release lands exactly on it — the tiling feature
is finally discoverable. The frame resizes from its left/right/bottom
edges and the bottom-left corner (`resizeEdge`, pure and pinned by
four unit tests; the left edge keeps the right edge fixed when the
minimum bites), and double-click on the head toggles
maximize/restore. Proven by the `frame` walk on the production bundle
(ghost previews + lands exactly, three edge resizes, double-click
both ways; `assets/frame-ghost-1440.png` LOOKED AT — the ghost is
unmistakable); `npm run check` green (277 web tests). Earlier:
**HS-97-04 done (2026-07-18): focus and depth.** The front window — the
last id in the stacking order that is open and not minimized — alone
wears the full elevation plus a 1px accent keyline ring; rest windows
quiet to `--desk-window-shadow-rest` (two new component tokens; one
property, one ladder, no per-window recipes; the dock's front chip
mirrors the same rule). Motion completes the story: close animates out
(140ms scale/fade), minimize contracts into the window's own dock chip
and restore returns from it (WAAPI, compositor-only transform/opacity,
chip elements tracked by ref registry — the architecture guard forbids
selector bootstraps), everything instant under reduced motion. Proven
by the `depth` walk on the production bundle (front-only keyline,
depth follows raise, minimize/restore fly, close leaves, reduced-motion
instant; `assets/depth-three-1440.png` LOOKED AT) and the storm inside
the envelope (median 8.3ms, p95 9.9ms, 1 layout event); `npm run
check` green (273 web tests). Earlier: **HS-97-03 done (2026-07-18): the arrangement is sacred.** The stacking
order persists: `hs.desk.panels` now carries `{rects, order, max}`
(`focusPanel` writes through; a legacy `min` key is tolerated and
dropped by the loader, pinned by test), windows rehydrate at their
remembered plane (`presentPanel` keeps a known id's position, new
windows go on top, `retirePanel` drops closed ones so a reopen
presents). Minimize is honestly session-scoped — never written to
storage. The room menu wears the transient material (dark panel,
radius, shadow, left-aligned quiet rows — the unstyled gray defaults
are gone), and the pane-picker pill rides the dock band's z tokens
(under the sheet on the phone; the stale `z-index: 60` allow-list
entry removed, 69 → 68). Proven by the new `arrangement` walk: the
layout survives reload byte-identically with the front window
restored, and on 393 every sheet action row button wins the hit-test
(`assets/arrangement-menu-1440.png`, `assets/arrangement-phone-393.png`);
`npm run check` green (271 web tests). Earlier: **HS-97-02 done (2026-07-18): a window lands well.** The open-placement
engine (`placeWindow`, exported beside `snapForPointer` and pinned by
seven unit tests) seats every window opening without a persisted rect:
seeded at its CSS default home, moved off other windows' title bars by
a min-overlap scan (head occlusion dominates, then overlap area, then
distance from home), always whole inside the working band below the
chrome and clear of the dock. A persisted rect is clamped into the band
on open (`clampIntoBand`) and otherwise untouched — the arrangement is
sacred. The cascade survives only at true saturation (title bars tiling
the whole band). The old pile-up path and its off-viewport spawns are
gone. Proven by the new `placement` walk on the production bundle: five
surfaces open in sequence, every window lands whole, no two title bars
overlap (`assets/placement-five-1440.png`); `npm run check` green (267
web tests). Earlier: **HS-97-01 done (2026-07-18): the shadow returns.** `resolveReference`
now substitutes a `{ref}` anywhere inside a composite value (iterating
so a reference may resolve to a reference, still failing loudly on an
unknown path), and a new mechanical lock refuses any emitted
custom-property declaration carrying a brace — the whole
unresolved-reference class, not just the two known casualties. The
healed diff is exactly two lines: `--desk-window-shadow` and
`--desk-transient-shadow` now compute to valid shadows (the browser
reports `rgba(0, 0, 0, 0.6) 0px 26px 70px 0px` on a live window). The
gate is shown firing on a planted composite violation and passing
clean; `npm run check` is green end to end (259 web tests); the
before/after pair at 1440 (`assets/before-two-windows-1440.png` vs
`assets/after-two-windows-1440.png`) shows stacked windows separating
into planes again. Earlier: **Phase 97 SCAFFOLDED (2026-07-18)** from the owner's Desk OS verdict
and the same-day screenshot + code audit. Nine stories: the shadow
generator fix under a mechanical gate, the placement engine, completed
persistence, focus depth and window motion, richer frame physics
(ghost, edges, double-click), the exposé/switcher, the unified dock
with a quiet chrome, the physics floors written, and a closeout that
walks the whole grammar on the production bundle.
