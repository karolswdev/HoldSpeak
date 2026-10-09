# Phase 16 — The Compositor: the window grammar of HoldSpeak

Owner, 2026-10-08: "The interface is now such a cacophony … too sterile. It's
too close to Workbench 2.0+ and too far away from 'on steroids.' … how bad all
of the windows are. There's clearly zero concept of a compositor. There's
clearly zero regard to delighting the user." And: "a real, real, real OS-like
way of composing windows … an extremely delightful set of guidelines and
implementations that keeps us still in the ballpark of Workbench 2.0+ but
really pushing the envelope."

This document is the guideline set. The canvas beside it
(`01-canvas/compositor.html`) is the same grammar, moving. Build what the
owner ratifies on the canvas. Where this disagrees with `DESIGN_SYSTEM.md`
HS-110-01 ("no shadows, no gradient, opaque"), THIS wins: HS-110-01 took the
shadows away to kill the frosted-glass look; it also took the light away.
The light comes back. The glass stays dead.

## 0. The diagnosis (what the shots show)

- No figure and ground: window body, floor and dock are one flat dark tone.
- Depth is one pen colour: the front frame is blue, the rest steel. No
  recession, no shadow gradation, no veil on back windows.
- Occlusion is brutal: a window cuts across another's title bar; a minimized
  window is an orphan nub at the top left.
- One type voice: menu bar, title bars, dock labels, eyebrows are all the
  same mono at the same weight.
- Motion is half there: the entrance spring exists; raise, stack, close,
  arrange have no choreography.
- The steel is a border declaration, not a material with light on it.
- Mechanically there is no compositor: every window is a DOM node with an
  inline z-index. Nothing above them owns depth, light, focus or motion.

Owner, 2026-10-08, on canvas v1: "The content. Why is it still black inside? It
causes such a weird disconnect from everything else. Intelligence flowing
outside of the button's boundaries looks ugly af. Icons, on the other hand, a
big, and positive, change. A lot more effort going into the design system, the
way 'internal apps' are laid out (a lot more common components, please)."
Canvas v2 answers: the interior joins the material (§2, §11); the dock tile
is as wide as its word; the icons stay.

## 1. The one sentence

**One compositor owns every window: it lights the front, recedes the rest,
animates every change of plane, seats windows beside what opened them, and
offers an arrangement grammar (tile, stage, exposé, gather) as a first-class
thing. The steel stays. The steel gets light.**

## 2. The four pens stay; the light is new

Workbench 2.0 drew with four pens: steel (`--wb-steel`), ink (`--wb-ink`),
paper (`--wb-paper`), blue (`--wb-blue`). They stay. What Workbench never had,
and what makes a window a thing instead of a rectangle, is a light.

- **One light, top-left.** It is the light Workbench's own bevel already
  implies (hi top-left, lo bottom-right). Every shadow, gradient and shine
  on the desk is cast by it. Never two lights.
- **The steel is a plate under that light.** A frame plate is `--wb-steel`
  with a 1 px shine on its top and left (`--wb-hi`) and a 1 px shade on its
  bottom and right (`--wb-lo`). It already does this. The change: the plate
  of a back window is in shade (`--wb-steel-dim`, new token, steel at 82 %).
- **The interior is the same material as the frame (v2, owner bounce).**
  The dark Signal well is retired inside windows: it was the disconnect.
  The window ground is slate (`--wb-field` #cdd2db, lit to `--wb-field-hi`
  at the top where the light falls), ink text, and every well a window
  holds (a ledger, an input, an icon grid) is sunken paper (`--wb-well`,
  `--wb-sunken`). Gadgets and verbs are raised steel plates. The selection
  is Workbench blue with paper on it. This is Workbench 2.0's own interior
  (grey ground, black ink, white wells, blue selection), lit. No blur, no
  vibrancy, no transparency: the glass stays dead (HS-110-01). The ember
  accent stays for lamps, asks and the Talk key, never as a ground.
- **The floor is a backdrop, not a void.** The desk floor is the Workbench
  backdrop (`--wb-backdrop` with the 4 px `--wb-dither` checker, already the
  Chair screen) with the light's vignette on it: brighter top-left, falling
  to the foot. Dark windows on a mid backdrop is the figure and ground the
  shots lack. The GL atmospheres stay as a choice on top of it; the backdrop
  is the default.

## 3. The depth ladder (planes)

A window is on a plane. The compositor assigns planes from the stacking
order and draws every window from its plane alone. One ladder; a window
never carries its own recipe.

| Plane | Which | Frame | Title bar | Body | Shadow |
|---|---|---|---|---|---|
| **Front** | the one front window | `--wb-blue`, lit | blue, fine stripes (title bar B), ink title | full | the hard drop `4px 4px 0` + the umbra `0 18px 40px rgba(0,0,0,.45)` |
| **Near** | the window directly behind | `--wb-steel`, lit | steel, flat, `--wb-ink-dim` title | veil 6 % | the hard drop + umbra at half |
| **Far** | every other open window | `--wb-steel-dim`, in shade | steel-dim, flat | veil 14 % | the hard drop only |
| **Seated** | minimized | none | a dock seat with the object's icon and lamp | none | none |

The veil is an ink wash over the body (`::after`, pointer-events none); it
dims and slightly desaturates. Never `opacity` on the window: a back window's
words stay readable, they are simply further away.

The hard drop is the Workbench pixel. The umbra is the steroid. Both come
from the one light: the drop offsets down-right; the umbra falls down.

## 4. The title bar (title bar B, ratified 2026-10-03, plus three things)

B stays: fine stripes on the front bar only, inactive bars flat, the title on
the bar's own cut-out, one gadget grid, 393 keeps 44 px. Three additions:

1. **The object's icon** sits left of the title (the same sprite as on the
   floor). A window is its object; the icon says so.
2. **The title is sans.** `--font-sans` 13/600; mono stays for counts, times,
   hosts. One type voice in the chrome was half the sterility.
3. **A lamp** at the right of the title: the object's IconLamp tone (ask,
   info, warn, ok). A window that needs you glows in the bar before you read
   it.

The gadgets keep Workbench 2.0's layout: close at the left; depth
(front/back) and zoom at the right; the sizing gadget bottom-right. Every
gadget presses (sunken one frame, `--wb-sunken`) and does the thing with
motion (see §6). The depth gadget sends the window to the Far plane and the
Near window comes forward; it is no longer a no-op swap.

## 5. The composition grammar (the OS part)

These are the verbs of the Window menu and the keys. Each is one gesture,
each moves every affected window with motion (§6), each is undoable by its
opposite. The compositor draws them; a window does nothing itself.

| Verb | Gesture | What happens |
|---|---|---|
| **Raise** | click anywhere on a window; `⌘\`` cycles | the window comes to Front; the old Front steps to Near |
| **Send back** | the depth gadget; `⌘⇧\`` | to Far; Near comes forward |
| **Seat** (minimize) | the seat gadget; `⌘M` | shrinks along a curve into its dock seat |
| **Close** | the close gadget; `⌘W` | shrinks into the object it opened from (or its dock app) |
| **Zoom** | the zoom gadget; `⌘⇧Z` | fills the working band; remembers both rects (C2) |
| **Tile** | drag to a screen edge (snap ghost); Window ▸ Tile left / right; `⌘⌥←` `→` | two windows share the band with a steel divider you can drag |
| **Stage** | Window ▸ Stage; `⌘⏎` | the Front takes the centre (76 % of the band); the rest slide to a left shelf as scaled live plates, Near on top; click a plate to swap |
| **Exposé** | Window ▸ All windows; `⌘⇧E`; four-finger spread | every window scales into a grid of live plates with its title plate; click to pick; Esc returns |
| **Gather** | Window ▸ Gather `<Room>`; `⌘G` | the windows of one Room (they share the Room's ink tag in the bar) tile together in one move |
| **Cascade** | Window ▸ Cascade | re-seats every window from the top-left, 26 px steps (the existing engine) |

Rules the grammar obeys:

- **Seated windows live in the dock, nowhere else.** The top-left nub tabs
  are retired. A seat is the app's dock tile with the window's lamp and a
  count when there are two.
- **Open beside the object** (exists): a window opened from a floor icon
  seats on the icon's right flank, or left when the right does not fit.
- **Never cover a title bar whole.** Placement nudges off other title bars
  (exists); the compositor also keeps 72 px of every back window's bar
  visible when it can, so every window is findable by its bar.
- **The band is sacred.** No window under the dock, over the screen bar, or
  off the edge (exists, `clampIntoBand`).
- **The user's arrangement is sacred.** A persisted rect is never animated
  under the user except by a verb the user pressed.

## 6. The motion grammar (four moments, one easing)

UX-CANON allows four named motion moments per face. The compositor's four:

1. **Raise** (180 ms): the window lifts (scale 1 → 1.012 → 1), the umbra
   grows, the frame turns blue; the old Front settles back (veil fades in,
   umbra halves). Both at once.
2. **Open** (240 ms, exists for origin windows): the window flies out of
   its object. The frame draws first (steel at 60 ms), the body follows.
3. **Seat and Close** (200 ms): the window shrinks along a quadratic curve
   into its dock seat (seat) or into its object (close), opacity to 0 in
   the last 40 %.
4. **Arrange** (220 ms): tile, stage, exposé, gather, cascade. Every window
   glides to its new rect, ease-out, no spring. Never teleport.

One easing for everything: `cubic-bezier(.2,.8,.2,1)`. A dropped drag settles
with a 60 ms, 2 px overshoot. `prefers-reduced-motion` makes every moment
instant and keeps the end states.

Idle never moves. A window at rest has no animation. The only ambient motion
on the desk is a lamp's pulse when an agent asks.

## 7. The chrome type ladder

| Where | Face |
|---|---|
| Screen title bar | mono 12, `--wb-ink` on paper (unchanged) |
| Window title | sans 13/600 ink (Front), ink-dim (Near, Far) |
| Window tags (Room, host) | mono 11 upper, 0.06 em |
| Dock labels | mono 11, ink on steel |
| Stage and exposé plates | the window's own title bar, scaled; no extra label |

## 11. The interior kit (v2): every internal app is laid out from these

An "internal app" (Needs you, a Room, the Conductor, a meeting, People,
Delivery, Settings) is a window whose interior is composed from the kit
below and nothing else. The kit is the library's existing species in the
new material; a face that needs a thing the kit lacks adds it to the kit.
Every window on the canvas is built from exactly these, in this order.

| Species | What it is | Rule |
|---|---|---|
| **AppHead** | the one big fact (display 26/650) with the **StatusStrip** on the same baseline | once per window; the strip is tokens (lamp square + word), never prose |
| **FilterBar** | CycleGadgets on one rail; the active one is the selection blue, sunken | one per window at most; a trailing verb group sits at the rail's right |
| **Section** | caption (mono 11 upper) + count + hairline, with an optional verb | the caption reads `Name · count`; no counters of zero |
| **Ledger** | a sunken paper well of **LedgerRows**: kind plate (raised steel, 44 px) · name (sans 15/500) · meta (mono 11 upper, `ask` or `ok` tone) | hover tints the row selection-blue at 12 %; verbs appear on hover (existing SurfaceLedgerRow) |
| **IconGrid** | objects in a sunken paper well, five across, icon + two-line name | the same sprites as the floor; hover tints |
| **AskWell** | a sunken input with the MicButton on its right edge | the voice law: a mic on every input |
| **Foot** | the steel foot: egress chip (paper plate) · receipt · verbs | egress exactly where egress happens; verbs right |
| **Verb** | the library Button as a raised steel plate; `pri` = selection blue, `danger` = red, both with paper text | every verb; a raw button is a bounce |

Spacing: the interior is a column with a 10 px gap; 12 px by 14 px padding.
Type: display 26 · name 15 sans · body 13 · meta and captions 11 mono upper.
Colour inside a window: ink, muted ink (`--wb-muted`, 7.0:1 on slate), the
lamp tones, the selection blue. Nothing else.

The dock: a tile is as wide as its word (minimum 72 px); a label never
leaves its tile.

## 12. How an internal app is composed (v3, owner: "consider UX really, really hard")

Owner, 2026-10-08, on canvas v2: "Style? Freaking love it. But now comes the
time to also think about how those internal apps will be composed for the
most delightful UX. For example, I fucking hate the way we configure models,
it's so finicky, so un-interesting, so not-dynamic and quite frankly boring."

The style is ratified. This section is the composition doctrine, derived from
the Models case and binding on every internal app (Needs you, Rooms, the
Conductor, Meetings, People, Delivery, Settings, Runs on).

### The seven rules

1. **Show the thing, not a form about the thing.** Runs on shows the wiring
   between what HoldSpeak does and what you have. People shows the people.
   Delivery shows the destinations. The picture IS the state; there is no
   separate "status" to read.
2. **Direct manipulation.** Drag, press, speak. A change applies the moment
   it is made, with a receipt in the foot and Undo. No Save, no Apply, no
   "Use these", no review step. (A5 one screen; A4 no modals; ledger not gate.)
3. **Live.** Every object carries a lamp (ok, busy, warn, broken, off);
   latency sits on the wire; a download fills its bar on the object itself.
   The app is never a snapshot that must be reopened.
4. **Try it, everywhere.** Every configured thing can be exercised on the
   spot, through the real route, with the real answer and its time. For
   speech, you speak and it shows what it heard. Joy is immediate feedback.
5. **Found before asked.** The app discovers (loopback ports, LAN servers,
   keys in the Keychain, model files on disk) and offers each as a found row
   with one verb. The user accepts; the user never types what the machine
   already knows. Egress and cloud still wait for the press (Article III).
6. **Five state words.** READY · LIMITED · BROKEN · WAITING · OFF, drawn as
   the plug's colour and said once. Never eleven. A limitation is a token on
   the wire (`WITHOUT VISION`), not a state.
7. **The kit, plus one species of its own.** An app is the §11 kit and at
   most ONE species that is the app's own picture (here the Switchboard),
   added to the library and `contract.md`, never hand-rolled.

### The exemplar: Runs on (the Models app), as a Switchboard

Today (the Concierge, `web/src/features/concierge/`): eleven state words,
two commit verbs ("Use these" and "Use this for summaries"), an Adjust that
does nothing (A11), downloads that never report, fallback chains reachable
only from object pullouts, cloud engines invisible until a key profile
exists, and five faces that disagree about whether there is a model (B33).
`DESIGN_SYSTEM.md:450` already specifies the `SurfaceSwitchboard` species;
nothing renders it.

The board (canvas Board 2):

- **Left column, WHAT HOLDSPEAK DOES:** the six owner groups as jobs
  (Speech · Writing & dictation · Thoughts & notes · Meetings · Agents &
  tools · Background) and a seventh, **Default for AI work**, which every
  job without a wire of its own follows. Each job: name, its tasks as a
  token line, a plug on its right edge coloured by state, and **Try it**.
- **Right column, WHAT YOU HAVE:** every engine as a raised steel plate with
  an emblem (MAC · LAN · API), name, token line (size, runtime, context,
  tools, vision, cost, latency), a live lamp, and a plug on its left. Below,
  **FOUND**: engines the concierge detected but you have not accepted
  (Ollama on a port, LM Studio, an OpenRouter key in the Keychain, a model
  file on disk), each with **Use it**.
- **Between them, the wires.** A solid wire is the job's engine; dashed
  wires are its fallbacks, in order. An amber wire is LIMITED (the token
  says why); a red broken wire is a repair, and the one verb to mend it sits
  on the engine (Download · Fix address · Key).
- **Drag an engine onto a job** to patch it (the wire draws in 220 ms, the
  foot says `PATCHED · Meetings → qwen3.8 27B` with the host chip and Undo).
  Hold ⌥ to add it as a fallback. A job that cannot take the engine refuses
  on hover (Speech takes speech engines only).
- **Try it** runs one real request down the wire: the wire pulses, the
  engine's lamp goes busy, the result lands on the job (`READY · qwen3.8
  27B · 412 ms · WITHOUT VISION`; for Speech, `HEARD: "…"`).
- **Download** fills the bar on the engine's own plate; when it lands, the
  wire that needed it mends by itself.
- **393:** the board becomes the job list; a job opens to its engine and
  the alternatives; tap to patch; Try it in the foot.

What this retires: the picker wells, the Adjust table, "Use these", "Use
this for summaries" (summaries get the exact capability row when Meetings
is patched; the service principal rule stays in the backend), the
AssignmentEditor sheet (fallbacks are dashed wires), and the two Settings
tiles that only redirect. One name: **Runs on** (the canon term in
`product-language.json`).

Build mechanics: `SurfaceSwitchboard` in `web/src/desk/surface/`; the board
reads `/api/concierge/detect` + `/api/inference/assignments` and writes
through `inference_assignment_set` per drop (CAS; 409 → Undo and redraw);
Try it is `/api/concierge/probe` with `task:true`; found rows come from
detect's loopback and profile scans plus the Keychain key probe; downloads
poll `/api/inference/acquisitions/{job}` into the bar (the TODO in
`useConciergeController.ts:624` is paid).

## 13. Software design: what we take from PhreshOS (owner ask, 2026-10-09)

Read: `github.com/PhreshOS/system` at 0.1.118 (the System service + its
Desktop; TypeScript; `source/server/core/link-manager/.../process-manager/
window.ts`, `source/client/view/components/window-manager/{window-manager,
presentations,window-geometry,shared-resize}.ts`, `.../desktop/windows/
window.tsx`, `window-geometry-motion.ts`, `shared/window-layers.ts`,
`opening-manager.ts`, `system.ts`, 72 behaviour-named tests) and its docs
(the-system, desktop, concepts). Not UI: the design underneath. Ten lessons,
each with what it changes here.

**L1. The System owns the windows; the browser shows them and holds none.**
In PhreshOS a Window (title, position, size, depth, minimized, maximized,
layer) is authoritative state on the server, per running Client; every
browser is one view of the same Desktop; the `phresh` CLI and an agent reach
the same windows. HoldSpeak keeps window rects and stacking in a zustand
slice persisted to localStorage per browser (`store/compositorSlice.ts`,
`workspaceStorage.ts`). So the Mac and the iPad have two different desks,
and no agent can open, raise or arrange a window.
→ **The hub owns the desk's windows.** A `DeskWindowService` (open · close ·
move · resize · raise · send back · seat · zoom · arrange), one row per open
window per desk, a `desk-changed` event the browser already listens to
(`useOnDeskChanged`), and MCP tools `desk_window_*` so the Conductor's
agents compose windows alongside the owner (the thing PhreshOS calls "agents
alongside you"). The browser's compositor becomes a presentation of that
state. The 393 sheet on the iPad is the same desk, seated windows and all.

**L2. Anticipate, then follow.** `Presentations.anticipate(process, change,
request)`: a person's action shows at once, holds while its request is in
flight (a pending count per window; several changes hold together until the
last settles), and then the System's truth replaces it, accepted or not. An
anticipated front ranks above every depth the System has assigned.
→ The compositor module's one write primitive is `anticipate(id, change,
request)`. This retires the whole class of "stale is-front, two blue title
bars" bugs (`windowRegistry.ts:140`) by construction.

**L3. Depth is a counter the authority increments; front is derived.**
`window.depth = ++this.highest` per layer; the front window of a layer is
the shown one with the greatest depth; a minimized window keeps its depth
and is simply not front; nothing reorders an array.
→ `panelOrder` (an array we splice) becomes `depth` numbers assigned by the
hub; the §3 planes (FRONT · NEAR · FAR) are derived from rank by depth among
shown windows. Reload keeps planes because the numbers are the state.

**L4. Layers are a type with rules, not z-index numbers.** `wallpaper ·
under · window · over · shell`; per layer: who designs the frame (the
Desktop for `window`, the Program for raw layers), what it is anchored to
(the plane or the viewport), whether it can be moved. Enforced by
`requireRawPresentation`, `requireAnchorable`, `requirePresentationMoveGesture`.
→ Our z ladder (`--desk-z-*` tokens: canvas 0 · world-overlay 25 · chrome 30
· window 42+ · waveform 78 · dock 80 · transient 81 · popover 82) is the same
idea by number. The compositor names it as a type: `floor · world · window ·
chrome · transient`, every surface declares its layer, z is derived, and the
rules (what the compositor designs, what can move, what raises) are per layer.

**L5. Geometry is shares plus pixels, resolved by each view.** A value is
`"50% + 10"` or `-1/2`: one relative coefficient and one pixel offset,
resolved against the view that draws it; the plane's zero is the view's
centre; a snap "names a share of the surface rather than pixels, so every
client resolves it in its own space"; a Window keeps its view on every
screen. HoldSpeak stores absolute pixels and clamps them per viewport
(`clampIntoBand`), so the same desk on 1440, 1920 and the iPad reflows by
clamping, not by design.
→ Window geometry is stored as share+px. Tile, stage, zoom and gather are
written as shares (`tile left = x:-1/2, w:1/2`) and resolved at draw. The
same arrangement is the same arrangement on every screen.

**L6. One owner of the visible pixels; the record is the destination.**
Motion values own what is on screen "from rest, through a gesture, and into
the next target"; the System's record stays the truth; `timing("window",
{distance, leaving, tempo})` derives a duration from how far a box travels,
whether it leaves sight, and the person's tempo; `seenOnly`: a window moves
visibly only when the person can see where it starts or ends, otherwise it
is simply there.
→ §6's fixed milliseconds become one `timing()` (distance-based, with a
per-browser tempo in Appearance); arrangements of off-screen windows do not
animate; and `DeskWindow.tsx`'s transform-stripping `measure()` hack goes,
because one motion owner means the measured rect is always the destination.

**L7. Departure is representation.** A closing window keeps one immutable
visual snapshot until its exit animation reports done, while the
authoritative collection drops it at once; windows present at mount are
"inherited" and never replay an entrance.
→ Seat and Close (§6 moment 3) animate a retained snapshot, never the live
component; a reload never replays Open. Both derived in the same event so no
render shows a window in neither list.

**L8. Touching edges are one boundary.** `sharedResizeBoundaries` finds
contacts between opposite edges of visible windows, groups them by
connectivity, and drags the group as one boundary, preserving every far edge
and clamping to minimum sizes.
→ §5's "steel divider" is not a tile mode; it is derived: any two windows
whose edges touch get the divider, and dragging it resizes both. Tile and
Gather just produce touching windows.

**L9. One row teaches one rule.** The taskbar lists windows, not processes:
"every entry in it is a thing you can focus, minimise and restore, and a row
whose entries do not all answer the same press is one row teaching two
rules."
→ The Dock is two rows in one today (launchers and open windows). The rule:
every tile in a row answers the same press. Seats (open and seated windows)
are one row; launchers are another strip, or the same tile only when a press
on it always means focus-or-launch. Decide on the Dock canvas.

**L10. The transport implements nothing.** "A transport may validate,
authenticate, serialize, or stream an operation, but it does not implement
System behavior"; handles hold no copy and every read is current; events
only after subscribe; a ten-second deadline; failure is a rejection with a
reason. Programs are a registry (identity, icon, what types they open, one
Process or many) and the Desktop itself is Programs on the System.
→ Confirms the 2026-09-23 ruling (MCP flows through services). For the
compositor: `applications.ts` becomes the registry (layer, default geometry
as shares, `opens: [object types]`, find-or-create vs many), the compositor
knows no app's internals, and `openObject.ts` goes through the registry.

Two things we do not take: Programs as sandboxed iframes (ours are
first-party React; the registry and the service boundary give the
discipline without the isolation cost), and the 5×5 plane with a Map (our
Floor already has Places; windows stay in the view; revisit if Exposé is not
enough).

### §9 revised: the build mechanics

1. **`holdspeak/services/desk_window_service.py`** (L1, L3): the desk's
   windows: `open(app, object, geometry?)`, `close`, `move`, `resize`,
   `raise` (depth = ++highest), `send_back`, `seat`, `zoom`, `arrange(map)`;
   geometry as share+px (L5); one `desk-changed` event per change; MCP
   `desk_window_list|open|close|raise|arrange`. Tests beside it.
2. **`web/src/desk/compositor/`** (new): `planes.ts` (rank by depth →
   plane), `anticipate.ts` (L2), `layers.ts` (the type, L4), `geometry.ts`
   (share+px resolve, snap/tile/stage/gather as shares, L5), `timing.ts`
   (L6), `departure.ts` (L7), `sharedResize.ts` (L8). Pure logic, no DOM;
   `__tests__/` one file each. The DOM side is one `useCompositor()` that
   writes `data-plane`/`data-layer` and owns the motion values.
3. `DeskWindow.tsx` keeps the physics hook (drag, resize) and loses
   placement, order, `is-front`, `measure()`; `window-chrome.css` becomes
   the §3 ladder by `data-plane`.
4. `applications.ts` = the registry (L10); `openObject.ts` resolves through it.
5. The Dock gains seats; one rule per row (L9); the nub chips are parked.
6. Phasing: **16a** the presentation (2–5 above, state still local) so the
   look and the grammar land first; **16b** window authority to the hub (1),
   the browser store becomes a cache of the hub's rows; **16c** Runs on as
   the exemplar app on the kit. 16a and 16c can run as parallel lanes.

## 8. What this is NOT

- Not glass: no `backdrop-filter`, no translucent bodies.
- Not rounded: radius stays 0 on frames (2 px on transients only).
- Not springy: one ease-out; springs stayed in the entrance only because
  the open moment is the one place a window "arrives".
- Not a million interfaces: nine verbs, four moments, four planes. A
  window never needs a setting.

## 9. The mechanics (for the build brief)

- `web/src/desk/compositor/` (new): one module that owns planes, the light
  and the arrangement verbs. It reads the registry and the store's
  `panelOrder` and writes `data-plane` on every `.desk-window-shell` and a
  `--plane` custom property; CSS draws from `data-plane` alone. Every
  arrangement verb computes rects and calls the existing geometry engine
  (`windowGeometry.ts`) through one `arrange(rects)` that animates with WAAPI.
- `DeskWindow.tsx` loses the per-window `is-front` recipe; it keeps the
  physics hook (drag, resize, clamp).
- `window-chrome.css` becomes the ladder: four `data-plane` blocks.
- Tokens: `--wb-steel-dim`, `--wb-umbra`, `--wb-umbra-near`, `--desk-floor`
  (the backdrop with vignette), `--desk-window-fall` (the slate ground, lit),
  `--desk-veil-near`, `--desk-veil-far`, `--wb-field`, `--wb-field-hi`,
  `--wb-well`, `--wb-muted`, `--wb-sel`, `--wb-rule-soft`.
  `--desk-window-fill` becomes the slate; the interior tokens (`--surface-*`,
  `--text*` inside `.desk-window`) are remapped in one block, so every face
  moves at once and the kit is then swept face by face.
- The Dock gains seats; the top-left nub chips retire (parked).
- Stage, Gather and Tile-with-divider are new; Exposé and Switcher are
  redrawn with scaled live plates.
- Tests: `web/src/desk/compositor/__tests__/planes.test.ts` (the ladder from
  an order), `arrange.test.ts` (tile, stage, gather rects), one glass file
  at 1440 and 393 with the depth shot (three windows open: blue, steel,
  steel-dim).

## 10. Open questions for the canvas

0. Interior: slate ground with paper wells (v2 default; Workbench 2.0's
   own interior, lit). The dark interior remains only as "Before".
1. Floor: the Workbench backdrop as default (§2) replaces the near-black
   floor in every shot. The canvas shows both; the owner picks.
2. Title in sans (§4.2): shown as the default on the canvas; the mono
   control is a toggle.
3. Stage's shelf on the left or the right. Left on the canvas (the light
   is top-left; the shelf sits in it).
