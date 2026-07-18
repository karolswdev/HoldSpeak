# Phase 95 — The Desk OS

**Status:** IN PROGRESS (2/10; HS-95-02 done 2026-07-17).

**Last updated:** 2026-07-17 (HS-95-02, OS-grade windows, done).

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
| HS-95-03 | The shell: dock, switching, layouts | backlog | [story-03-the-shell](./story-03-the-shell.md) | — |
| HS-95-04 | Embeddable page cores | backlog | [story-04-embeddable-page-cores](./story-04-embeddable-page-cores.md) | — |
| HS-95-05 | Dictation through the desk | backlog | [story-05-dictation-through-the-desk](./story-05-dictation-through-the-desk.md) | — |
| HS-95-06 | Meetings and recording through the desk | backlog | [story-06-meetings-through-the-desk](./story-06-meetings-through-the-desk.md) | — |
| HS-95-07 | Configuration through the desk | backlog | [story-07-configuration-through-the-desk](./story-07-configuration-through-the-desk.md) | — |
| HS-95-08 | Studio, sessions, and the last exits | backlog | [story-08-studio-sessions-last-exits](./story-08-studio-sessions-last-exits.md) | — |
| HS-95-09 | Docs: the Desk OS is the documented product | backlog | [story-09-docs](./story-09-docs.md) | — |
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

Next: HS-95-03 (dock/switching/layouts) and HS-95-04 (page cores); the
Phase 93 physics contract remains the regression floor.
