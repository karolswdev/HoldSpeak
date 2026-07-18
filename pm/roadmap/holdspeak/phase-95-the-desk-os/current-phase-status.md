# Phase 95 — The Desk OS

**Status:** IN PROGRESS (9/10; HS-95-09 done 2026-07-18).

**Last updated:** 2026-07-18 (HS-95-09, docs under the Constitution, done).

## Why this phase exists

The owner ran the first live UAT sitting (2026-07-17, Campaign 1 territory)
and the verdict was blunt: the desk experience is confusing and convoluted,
because the desk is a front door that keeps throwing you out of it. Actions
like "Dictate" leave the desk for `/dictation` — a flat page under a
completely different shell, look, and feel — and the same is true for
meetings, settings, studio, workbench, profiles, commands, cadence, and
activity. On top of that, the world itself is DOM/CSS: every sprite, zone,
and drag is layout-engine work, and it feels clunky rather than native.

Phase 93 shipped the desk-window *contract* (floating panels drag, resize,
persist, raise, coexist; one chrome; a documented z ladder). What it did not
ship is the *content*: the windows host nine hand-wired panels while the
product's real surfaces still live on sixteen flat routes. This phase closes
that gap and gives the desk a real engine. The outcome the owner named: a
native-like OS desk where you interact with everything **through the desk**,
WebGL-accelerated, with OS-grade behavior, design, and features.

## The thesis (owner's charter, 2026-07-17)

The services were built to system-primitive quality — the dictation runtime,
meeting intelligence, steering and the factory, profiles and the mesh, the
delivery runtime, configuration. The DeskOS philosophy was always that those
services get *integrated through OS primitives*: desk objects, windows, the
dock — never through screens of their own. Instead, each service accreted a
page-shaped UI, and the product became a desk-flavored lobby in front of
sixteen other lobbies. This phase is the inversion, and it is the rule every
story enforces: **features do not own surfaces; the OS owns surfaces and
features plug into them.** A service exposes a core; the OS decides where
and how it appears. Any future surface that ships as a route instead of a
primitive is a regression against this charter (the HS-95-08 guard makes
that mechanical).

The charter is ratified as the
[Constitution of HoldSpeak](../../../docs/internal/CONSTITUTION.md), the
supreme canon this and every future phase is measured against. This phase
executes Articles I (the Desk is the operating surface), II (everything is a
primitive), VII (the interface serves), VIII (native-grade craft), and IX
(proof over claim); Articles III–VI are standing law it must not regress.

## The measured starting point (survey 2026-07-17)

- One React 19 SPA, react-router, two shells selected by an `immersive` flag
  (`web/src/App.tsx`, `web/src/components/AppShell.tsx`): the desk is
  immersive; sixteen routes render under the flat `AppShell` top-nav chrome
  with `styles/react-app.css`, visually alien to `desk/desk.css`.
- Nineteen desk→page escape hatches: the DeskChrome room menu (Dictation /
  Meetings / Studio / Settings), DeskStartActions "Dictate", seven
  DeskToolShelf tools, three DeskToolInspector edit links, six Pullout links,
  and FirstWords onboarding links. All are `<Link>`s out of the world.
- The window system is `useDeskWindow` (`desk/components/DeskWindow.tsx`) — a
  hook each panel hand-wires; there is no `<DeskWindow>` container with a
  content slot, so arbitrary content cannot be hosted in a window today.
- Rendering is DOM/CSS end to end. `Stage.tsx` is a 78-line 2D-canvas mote
  background; no WebGL anywhere; `motion` and `@use-gesture/react` are
  already dependencies.
- Pages own their data via `useResource`/`apiFetch` over the one shared
  `lib/api.ts` client and the one `RuntimeBus`; they do not depend on
  `AppShell` for data. Mounting a page core in a window is a chrome/style
  refactor, not a rewrite. Precedent exists: the meeting recovery panels and
  `RunsOnPicker` already render on both sides of the boundary.

## Goal

The desk is the product's operating surface. The world (room, zones, objects,
ambient) renders on a WebGL scene graph at a 60fps interaction budget. Every
daily surface — dictation, meetings and live recording, settings, profiles,
integrations, commands, cadence, studio, workbench, personas and coder
sessions, activity — opens as an OS-grade desk window in place, with a dock,
minimize/restore, focus order, and layout persistence. Flat routes survive
only as deep links that open the desk with the right window. No desk action
navigates away from the desk.

## Scope

### In

- A WebGL-accelerated stage for the world layer; DOM retained for text-heavy
  windows composited above it.
- A generic `<DeskWindow>` container (content slot, one chrome, lifecycle:
  open / focus / minimize / restore / close) over the Phase 93 physics, and
  migration of the nine existing hand-wired panels onto it.
- OS shell furniture: dock/taskbar of open and minimized windows, window
  switching, snap targets, per-desk layout persistence, the phone bottom-sheet
  window grammar.
- Chrome-optional page cores extracted from the flat pages, then re-homed
  into desk windows domain by domain (dictation; meetings/live; configuration;
  studio/workbench/sessions).
- Retirement of every desk→page escape hatch; flat routes become deep-link
  openers into the desk.
- Docs and a closeout with a machine-verified performance proof, a production
  screenshot walk (1440 and 393 viewports), and an owner walk on the UAT rig.

### Out

- Native Swift Desk parity (tracked by the HSM belt; contracts only ride
  along where free).
- New backend routes or hub behavior (the phase re-homes existing surfaces;
  it does not add product capabilities).
- The control-posture remainder (BACKLOG candidate X) and the physical proof
  program (BACKLOG candidate Y).
- Qlippy/theater behavior changes beyond what the stage migration requires.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-95-01 | The WebGL stage | done | [story-01-the-webgl-stage](./story-01-the-webgl-stage.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-95-02 | OS-grade windows | done | [story-02-os-grade-windows](./story-02-os-grade-windows.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-95-03 | The shell: dock, switching, layouts | done | [story-03-the-shell](./story-03-the-shell.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-95-04 | Embeddable page cores | done | [story-04-embeddable-page-cores](./story-04-embeddable-page-cores.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-95-05 | Dictation through the desk | done | [story-05-dictation-through-the-desk](./story-05-dictation-through-the-desk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-95-06 | Meetings and recording through the desk | done | [story-06-meetings-through-the-desk](./story-06-meetings-through-the-desk.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-95-07 | Configuration through the desk | done | [story-07-configuration-through-the-desk](./story-07-configuration-through-the-desk.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-95-08 | Studio, sessions, and the last exits | done | [story-08-studio-sessions-last-exits](./story-08-studio-sessions-last-exits.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-95-09 | Docs: the Desk OS is the documented product | done | [story-09-docs](./story-09-docs.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-95-10 | Closeout: performance proof, screenshot walk, owner walk | backlog | [story-10-closeout-owner-walk](./story-10-closeout-owner-walk.md) | — |

## Where we are

**HS-95-01 done (2026-07-17): the world renders on the GPU.** One pixi v8
canvas draws zones, objects, selection, drag, and the ambient motes from a
pure scene model (`web/src/desk/gl/`); the store stays the only truth;
`World.tsx`/`DeskObject.tsx`/`Stage.tsx` and ~9 KB of world CSS are deleted
— one renderer. Interactions ported at HS-71 semantics (4px threshold,
fresh-rect rule upgraded to a cached rect refreshed on resize/scroll,
tap/drag discrimination, zone drop/dive/rename/resize, the lasso) and
proven by a Playwright smoke through the real canvas (tap-open, 330px
object drag, zone drag, lasso rope). The storm on the production bundle,
real GPU, seeded desk: **median 8.3ms, p95 9.9ms, max 10.3ms over 962
frames, with 1 Layout and 2 Paint events in 8 seconds of continuous
object drags** — React re-renders are surgically absent from the drag path
(fine-grained selectors). Before/after parity shots at 1440 and 393 in
`assets/`. A visually-hidden a11y layer preserves the keyboard contract.
Deviation noted honestly: the room's base gradient + spotlight pulse stay
CSS (compositor-only transform/opacity — zero per-frame paint); the motes
moved into the GL scene; `Stage.tsx` retired.

**HS-95-02 done (2026-07-17): windows are OS citizens.** `DeskWindowFrame`
is the ONE container (icon · eyebrow · title · actions · minimize/maximize/
close over the Phase 93 physics; children as the content slot); all nine
panels migrated with their private wiring deleted and the physics hook
folded module-private. Lifecycle lives in the store (`panelMin`/`panelMax`,
persisted in `hs.desk.panels` with a tolerant reader for the Phase 93 flat
shape). Designed in-story and pinned by the walk: opening a window always
PRESENTS it (minimize is session-scoped; rects + maximize persist), and
the minimized tray is shell furniture riding above the window band — the
walk caught a maximized window burying it. The phone form is a bottom
sheet from the same component and state. Proof: web suite 244/244; the
production windows walk at 1440 (three windows, drag, park/restore,
reload persistence, reopen-maximized) and 393 (sheet); chrome screenshots
in `assets/`.

**HS-95-03 done (2026-07-17): the desk has a shell.** The dock (one band
above the launcher strip) shows every open window as a chip — tap focuses,
a parked chip restores, hover reveals ✕, ⟲ resets the layout; Ctrl+`
cycles focus in MRU order restoring as it lands; releasing a window drag
at a screen edge snaps half/quarter tiles that clear the chrome band and
the dock; the DeskChrome menu now dispatches through the shell's surface
registry (`desk/shell.ts`) with the legacy route as the not-yet-registered
fallback HS-95-05..08 retire. Windows are `role="region"` — the Phase 73
mechanical locks (no modal roles on the desk, no global selector state)
caught the initial `role="dialog"` chrome in CI and the guards now pass.
Proof: guards + web suite 253/253; the windows and shell production walks
(dock, snap, cycle, park/restore, dock-close, reset, menu dispatch);
`assets/shell-1440.png`.

**HS-95-04 done (2026-07-17): one core, two hosts.** The pattern:
`pages/cores/<Name>Core.tsx` is host-agnostic (no router hooks, no page
chrome, scope by prop — `tests/unit/test_page_cores_guard.py` enforces it
mechanically), owns its verbs, and hands them to a `hero` render-slot so
each host picks the chrome. Flat routes are thin wrappers; the desk hosts
cores through `SurfaceWindows` (one table row per surface: shell key,
window id, lazy core) with a left-flank default home that respects the
z ladder (chrome sits UNDER the window band). The tool shelf's mechanism
converted to the shell dispatcher (registered surfaces open in-world;
unregistered fall back to the legacy route until HS-95-08). Proven on
Activity and Commands: cores guard + web suite 257/257 + the cores walk
(both windows in-world chrome-free; flat routes keep the hero);
`assets/cores-1440.png`; the authoring note lives in `web/README.md`.

**HS-95-05 done (2026-07-17): dictation lives in-world.** The full daily
cockpit (readiness, Try it, blocks, memory, knowledge, journal, runtime,
hooks, nudges) is `DictationCore`, hosted in a desk window; every dictation
exit (the Dictate start chip, the DeskChrome room, the Pullout's "Dictate
about this", the inspector's project-context) opens it in place through
the shell — the URL never leaves the desk. "Dictate about this" scopes
the window with a product-label chip (hosts resolve titles; no raw refs).
The Try-it utterance gained its standing-rule mic, and the proof is a REAL
voice path: Chromium's fake mic device fed a `say`-generated wav through
the window's speak-to-fill into the hub's real Whisper — "Hello world from
the desk" landed in the box (`assets/dictation-voice-1440.png`). Mic
authority is single-owner (a second capture takes over and the first's
tracks stop; pinned by test). The app shell delegates navigate to
`desk/shell.ts` so cores/chrome fall back to legacy routes without router
imports. Suite 258/258; the dictation walk covers all beats plus the flat
route for deep links.

**HS-95-06 done (2026-07-18): meetings live in-world.** `LiveCore` and
`HistoryCore` host the meeting room and the meeting memory as desk
windows; Record (chip and orb) opens the live window with the recorder —
the URL never leaves the desk; Stop inside the window settles every
surface (one recorder truth); "Return to saved Meeting" opens the
pull-out via the shell's `openPrimitive` (refresh-then-open, the arrival
path's exact behavior); "Review meeting" hosts the memory core scoped to
the meeting. The proof is PHYSICAL: the hub records the real microphone
(Phase 73 lock — never the browser), so the walk speaks a generated
meeting through the speakers; Whisper transcribed it, and the .43 model
titled the meeting, wrote the summary, and the window wears "Intelligence
ready" — live, twice (two staged runs). Named deferrals: the meeting
detail keeps the flat page's Dialog grammar inside the window (Article
VII drift for HS-95-09/10 to name), and the seeded-desk-43 deck's intel
keys were shadowed by DB-backed settings on this staged run (the walk
enabled intel through the product's own settings route; a UAT-rig
observation worth a BACKLOG row at closeout).

**HS-95-07 done (2026-07-18): configuration lives in-world.** Settings,
Runs on, Cadence, and Setup are cores hosted as desk windows (Commands
landed in 04); the shelf's Integrations entry is an alias opening the
Settings window scoped to integrations (the scope chip); the inspector's
edit affordances (Configure Runs on, Configure <integration>, the
Pullout's capability row) open scoped windows in place — the inspector
never navigates; FirstWords' Setup/Runs on go through the shell. Proven
by the config walk: a real presence toggle round-trips through
`/api/settings` and survives reload, Runs on/Cadence/Integrations open
in-world (three windows cascaded in `assets/config-1440.png`), and the
flat routes still answer. Suite 258/258.

**HS-95-08 done (2026-07-18): the two-worlds architecture is dead.**
Workbench, Studio, Companion, the runtime guide, and the component gallery
are cores hosted as desk windows (Workbench opens MAXIMIZED and saved a
real desk-created workflow through the hub, scoped from its pull-out).
The sessions surface reconciled: the Companion core is the one roster; a
persona opens the one chat window, a session opens the one session window.
The desk carries ZERO router imports/links (the chrome menu and tool shelf
are pure dispatchers), locked by `tests/unit/test_desk_no_exit_guard.py` —
the evidence shows the guard firing on a planted violation. All fifteen
flat routes are DEMOTED: `routes.tsx` renders three surfaces (Desk,
Welcome, Presence) and maps every legacy path to a deep link that queues
its window open (`openSurfaceWhenReady`) and lands on the desk — the walk
cold-hits all fifteen and each arrives with the right window. `AppShell`
is the one immersive frame (header/PRIMARY_NAV/trust dialog deleted);
the page wrappers, PageHero, and WorkroomBar are gone; the bundle carries
only Welcome/Presence page chunks. Suite 256/256; guards green.

**HS-95-09 done (2026-07-18): the Desk OS is the documented product.**
POSITIONING's Phase 70 four-destination IA is amended under Article I with
the canon rule (services are system primitives; windows/objects/the dock
are how they appear); GETTING_STARTED, USER_GUIDE, WEB_DESK, README, and
SECURITY now speak windows and deep links, never pages; WEB_DESK gains the
window-system section (drag/snap/dock/Ctrl+`/sheets) with a fresh
two-window screenshot; ARCHITECTURE and the web-frontend decomposition doc
are redrawn to the three-surface + demotion world with the mermaid render
guard green; web/README's add-a-surface path covers the demotion row and
the no-exit lock. Fresh entry screenshots at 1440/393 from the shipped
build. A real fix rode along: an open chrome menu now rides above the
window band (a window's default home buried it — caught by the screenshot
run). Guards: doc drift 18/18, copy census, mermaid renders, and
`npm run check` (architecture census + typecheck + suite + build) all
green.

Next: HS-95-10 — the closeout (performance proof, the production
screenshot walk, the UAT campaign rider, and the live owner walk).
