# HS-95-06 — Meetings and recording through the desk

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-02, HS-95-04
- **Unblocks:** HS-95-08

## Problem

The desk already starts and stops the recorder (RecordOrb drives the same
`/api/meeting/start|stop` as LivePage), but everything after the first
second leaves the world: the live meeting view exists only on `/live`, and
review — history, intelligence cards, aftercare, "show me the moment" —
only on `/history`. The Pullout links out for both ("review-meeting",
"record-follow-up"), and the meeting recovery panels are the one precedent
already rendering on both sides of the boundary.

## Scope

- In:
  - the live meeting window: the LivePage core in a desk window — live
    state, markers, stop/finish — opened automatically by the desk's Record
    verb, so recording never navigates away;
  - the meeting review window: the HistoryPage core (meeting detail,
    intelligence cards, artifacts, aftercare, moment jump, facets) hosted in
    a window; a meeting object's Pullout opens it scoped to that meeting;
  - recovery panels (conflict/intel) render only through the shared
    components in both hosts — no divergence;
  - all meeting escape hatches rewired: DeskChrome "Meetings", Pullout
    "review-meeting" and "record-follow-up";
  - flat `/history`, `/meetings`, `/live` kept as wrappers for deep links.
- Out:
  - capture pipeline, plugin chain, artifact types (untouched);
  - meeting import/transcript import flows beyond their existing entry
    points surviving in the core;
  - aftercare/actuator semantics (render-only re-homing).

## Acceptance criteria

- [ ] Pressing Record on the desk opens the live window; a real recorded
      meeting runs start-to-intelligence entirely in-world, against the real
      hub (live proof, `.43` for intelligence).
- [ ] A meeting object's Pullout opens the review window scoped to that
      meeting: cards, artifacts, aftercare, and moment jump all work inside
      the window (moment jump scrolls the in-window transcript).
- [ ] No desk surface links to `/history`, `/meetings`, or `/live`
      (grep-verified across `web/src/desk/`); each former exit opens the
      right window at the right scope.
- [ ] Deep links to the three flat routes still render via wrappers.
- [ ] The review window at 393px presents the bottom-sheet form with cards
      and transcript usable (the phone meeting-review path the flagship
      pass compares against).
- [ ] Recording state is honest across surfaces: RecordOrb, the live
      window, and the dock icon agree at all times; stopping from any one
      of them settles all.

## Test plan

- `npm --prefix web test` — core-mount and scope-prop tests for both
  windows; recorder state-sharing tests.
- Live proof: one real short meeting through mic → stop → intelligence on
  `.43` → aftercare, all in-world (evidence-captured).
- Playwright walk at 1440 and 393: record-open, review-open from Pullout,
  moment jump inside the window.

## Implementation direction

- One recorder authority: the desk store's existing
  `startRecording`/`stopRecording` remain the only callers; the live core
  subscribes, it does not own.
- Scope rides the context prop from HS-95-04 (meeting id), mirroring the
  Pullout's existing object identity; no `?room=`/`?open=` encoding for
  in-world opens.
- The history core is the heaviest extraction in the phase — extract
  mechanically first (HS-95-04 rule), resist redesigning cards while
  moving them.
- Moment jump must target the in-window transcript container, not
  `window.scrollTo`.

## Evidence required

- captured test runs;
- the live meeting proof (commands + outputs, control-vs-treatment where
  intelligence is judged);
- screenshots: record → live window, Pullout → scoped review window, 393px
  sheet;
- the grep sweep output for the three routes across `web/src/desk/`.
