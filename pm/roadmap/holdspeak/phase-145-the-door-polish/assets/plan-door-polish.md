# Phase 145 plan — the Door polish (opus plan worker, 2026-08-28)

Read-only design plan produced by the opus plan worker against
`feat/hs145-door-polish` (stacked on the unpushed Phase 144 tip,
handover commit `399a0dc2`). The two [ORCH-CALL]s were ruled by the
orchestrator the same day; dispositions are recorded in the charter's
settled design. Anchors verified at plan time.

---

## ITEM A — 393px board scroll hint

**Problem.** At 393px, `chair.css:541` forces `min-width: 1120px` on
`.door-board-grid` (five columns at `minmax(224px, 1fr)`). The
`.door-board-viewport` (`chair.css:332-339`, `DoorBoardLane.tsx:354`)
is plain `overflow-x: auto` with no visual hint that three of five
columns are off-screen.

**Design: scroll-edge shadow masks.** Two options considered:

- **Option 1 — pure CSS scroll-driven animations.** `scroll-timeline`
  shipped Chrome 115+/Firefox 120+; full `animation-timeline: scroll()`
  + `animation-range` only Safari 18.2+. The repo's minimum matrix
  (chair.css:49: "Chrome 105+, Firefox 121+, Safari 15.4+") means
  Safari 15.4–18.1 would see no hint at all. Not acceptable without a
  fallback.
- **Option 2 (recommended) — tiny scroll listener + CSS class toggle.**
  A `useEffect` scroll/resize handler on the viewport `ref` reads
  `scrollLeft`/`scrollWidth`/`clientWidth`, sets
  `data-scroll-hint="none|right|left|both"` on the viewport div. CSS
  `::before`/`::after` pseudo-elements paint token-compatible edge
  gradients, toggled by the attribute. No hint when
  `scrollWidth <= clientWidth` (the 1440 case). rAF-throttled.

**Settled CSS design:** `.door-board-viewport::before/::after` —
`position: sticky; top: 0; height: 100%; width: 28px;
pointer-events: none; z-index: 1`; left shadow
`linear-gradient(to right, var(--surface-1), transparent)`, right
shadow mirrored; rendered only under the matching
`[data-scroll-hint=…]` selector; `.door-board-viewport` gains
`position: relative`. Uses the semantic `--surface-1` token so any
future theme redefinition follows automatically.

**Behavioral contract:**

1. All five columns fit → attribute absent/`"none"`, no shadows.
2. 393 initial load → `"right"` (right shadow only).
3. Fully scrolled right → `"left"`.
4. Partial scroll → `"both"`.
5. Empty board renders `SurfaceState empty` (`DoorBoardLane.tsx:438`)
   — no shadow logic runs.
6. Listener cleans up on unmount.
7. The `@media (max-height: 720px)` working-band block
   (chair.css:529-533) gives the viewport vertical scroll; sticky
   pseudo-elements paint horizontally only — no interference.

**Edit map:** `DoorBoardLane.tsx:354` (ref + listener + attribute);
`chair.css` after the `:focus-visible` block at 343 (pseudo-element
rules + `position: relative`).

**[ORCH-CALL] A1** — implementation approach. Recommendation:
Option 2 (scroll listener + data attribute); CSS-only fails the
Safari 15.4 floor.

---

## ITEM B — connect-calendar affordance on the empty rail

**Problem.** The rail's empty branch (`DoorBoardLane.tsx:253`,
`.door-upcoming-empty` at `chair.css:496-503`) says "No future time
scheduled." and dead-ends. Calendar setup (ICS subscription, Phase 144
story 02) lives under Settings→Meetings and is undiscoverable from
the Door.

### B1 — how the desk opens Settings→Meetings

Evidence chain: the Settings window is a `SurfaceWindow`
`key: "configure-settings"` (`SurfaceWindows.tsx:82`);
`useSurfaceWindows` (`SurfaceWindows.tsx:272`) exposes
`openSurfaceWindow(key, scope?)`; `SURFACE_ALIASES`
(`SurfaceWindows.tsx:294-305`) already maps e.g.
`"configure-runs-on" → { target: "configure-settings", scope: "models" }`;
`SettingsCore.tsx:190-201` resolves `scope` through `PREF_MODULES`
(`settingsPrefs.tsx:35` declares `{ id: "meetings", … }`).

**Settled:** no new store action. The affordance calls
`useSurfaceWindows.getState().openSurfaceWindow("configure-settings", "meetings")`.
New import in `DoorBoardLane.tsx`: `useSurfaceWindows` from
`../../components/SurfaceWindows`.

### B2 — when the affordance shows

Only when NO calendar subscription is configured; a
configured-but-quiet calendar must not nag. The subscription lives at
`Config.calendar.subscription` (`config/integrations.py:17-21`), read
via `validate_calendar_subscription` (used by
`calendar_ingest_conductor.py:173`). The DoorService
(`door_service.py:30-54`) exposes no calendar state today; the
projection needs **one new additive field**:

- **Name:** `calendar_configured` (boolean), top-level beside
  `board`/`upcoming`/`counts`.
- **Semantics:** `True` iff `validate_calendar_subscription(
  config.calendar.subscription)` returns a non-empty string.
- **Wiring:** `holdspeak/web/routes/door.py` and
  `holdspeak/mcp/families/door.py:39-44` both pass
  `config_loader=Config.load`; the MCP `_service()` factory already
  builds a fresh DoorService per call, so `door.get` parity is
  automatic. MCP input schema unchanged.

**[ORCH-CALL] B2a** — freshness. (a) live `config_loader` read per
`get()` (recommended; the field stays true the moment the owner
connects a calendar, one cheap `Config.load()` per Door read) vs
(b) read-once at construction (stale nag until hub restart).
Recommendation: (a).

**Guards:** no new route → no `gen_api_surface.py` regen; no new MCP
tool → the 135 count in `scripts/mcp_walk.py:187` stands; BUT
`mcp_walk.py:263-266` asserts the door aggregate key set
`{"board", "upcoming", "counts"}` — must gain
`"calendar_configured"`.

### B3 — what it looks like

Replace the dead-end empty div with a conditional branch: when
`calendar_configured` is false —

    <div className="door-upcoming-empty door-upcoming-empty--connect">
      <span>No calendar connected.</span>
      <Button dense variant="ghost" onClick={… openSurfaceWindow("configure-settings", "meetings")}>
        Connect calendar
      </Button>
    </div>

— else the existing "No future time scheduled." The `--connect`
modifier adds `justify-content: space-between; gap: var(--space-2)`.
Ghost button matches the rail header's "Schedule recording"
(`DoorBoardLane.tsx:229`). `DoorProjection` type
(`DoorBoardLane.tsx:50-61`) gains `calendar_configured: boolean`;
`UpcomingRail` gains a `calendarConfigured` prop passed from the
call site (`DoorBoardLane.tsx:439`).

**Full edit map:** `door_service.py:14-28` (constructor
`config_loader` param) + `:30-54` (`get()` computes + returns the
field); `web/routes/door.py:16-18` and `mcp/families/door.py:28-44`
(pass `Config.load`); `DoorBoardLane.tsx` type/prop/branch/import;
`chair.css` `--connect` modifier after :496-503;
`scripts/mcp_walk.py:263-266` key set.

---

## Focused test plan

Existing files: `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`,
`upcomingTime.test.ts`; `tests/unit/test_door_read_model.py`,
`test_door_routes.py`, `test_door_mcp.py`,
`test_door_transport_parity.py`; `tests/e2e/test_hs144_door_glass.py`.

- **Item A:** `DoorBoardLane.test.tsx` — scroll-hint attribute logic
  (JSDOM lacks scroll geometry; mock `scrollWidth`/`clientWidth` or
  extract + unit-test the pure computation).
- **Item B:** `test_door_read_model.py` — `calendar_configured`
  False on empty subscription / True on a valid HTTPS value;
  `test_door_routes.py` — aggregate key-set assertion gains the
  field; `test_door_mcp.py` — same; `test_door_transport_parity.py` —
  `_side()` passes the same `config_loader` on both sides (e.g.
  `lambda: Config()`); `DoorBoardLane.test.tsx` — fixture gains
  `calendar_configured`, three new tests (affordance shown when
  false+empty, quiet message when true+empty, click opens
  Settings→Meetings). `upcomingTime.test.ts` untouched.

## Risk notes

1. `mcp_walk.py:187` tool count 135 — unchanged.
2. `mcp_walk.py:263` door aggregate key set — MUST gain the field
   (fails the phase walk otherwise).
3. api-surface manifest — no regen (no new route).
4. No schema migration — the field is computed from config at read
   time; additive-only posture respected.
5. `DoorProjection` type addition is additive; the Door fetches fresh
   on mount.
6. Transport parity — both sides must receive the same
   `config_loader` in the test rig or the parity assertion breaks.
7. Working-band media block — sticky pseudo-elements are
   horizontal-only; no interference with the vertical axis.
