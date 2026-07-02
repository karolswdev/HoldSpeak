# HS-73-03 — Open in-world: the pull-out

- **Status:** todo
- **Priority:** HIGH (kills the bounce-out — the single worst touch on the surface)
- **Depends on:** HS-73-01

## Goal

Tap an object and it opens *here*, in the world: a drawer slides out on the
stage beside the object — the port of the iPad's `DioPullout`
(`DeskDioramaStage.swift:~1221`) and the meeting drawer (PR #196). Today
`openObject` (`desk-app.js:400`) throws meetings to `/history?meeting=id`
and reveals every other kind inside the "Browse as a list" appendix. After
this story, the ONLY route change on the desk is the explicit "Open full"
escape hatch.

## Scope

- **In:** the pull-out component; per-kind content; the meeting drawer's
  lineage grouping; "Open full"; drag-vs-tap discrimination preserved.
- **Out:** editing inside the pull-out beyond embedding the HS-73-02 inline
  editor; the agent Run action's theater (HS-73-07 wires it; this story
  gives the agent pull-out the Run button calling the existing
  `openRun`-equivalent logic); any new backend route.

## Tasks

- [ ] Build `web/src/scripts/desk/pullout.js` + markup in
      `components/desk/DeskPullout.astro` (factory-rendered; `is:global`
      CSS): a panel that slides from the object's side (left/right chosen
      by stage half), with the object's sprite + title as its header, a
      kind-tinted edge, and the egress badge where the kind has one
      (`profileEgress`, `desk-app.js:618`, for agents with profiles).
- [ ] `openObject` (`desk-app.js:400`) becomes: tap (already
      drag-discriminated via the >4px movement threshold + `justDragged`)
      → open the pull-out. Delete the `/history` navigation and the
      reveal-in-list behavior.
- [ ] **Meeting pull-out** (the drawer): fetch detail on open
      (`GET /api/meetings/{id}` — note the repo gotcha: the detail payload
      nests `intel_status`) + `GET /api/meetings/{id}/artifacts`. Group by
      lineage exactly like the iPad's meeting drawer: derivatives whose
      `provenance.sourceCardId` or `source == title` match — the helpers
      `lineage(sources)` / `hasLineage` (`desk-app.js:853/880`) already
      encode this. Sections: summary, actions, artifacts (each row opens
      that artifact's pull-out in place — a stack of one, back returns).
- [ ] **Note/KB pull-out**: the content rendered; an Edit affordance that
      swaps in the HS-73-02 inline editor.
- [ ] **Agent pull-out**: avatar, role, prompt summary (label-style, not
      prose), profile + egress badge, and Run (behavior lands fully in
      HS-73-07).
- [ ] **Chain/workflow pull-out**: steps listed; Run button (existing run
      path).
- [ ] **"Open full"** appears only in the pull-out header: meetings →
      `/history?meeting=id`; agents/chains/workflows → their `/studio`
      surface if one exists. This is the sanctioned exit, nothing else
      navigates.
- [ ] Escape / tap-elsewhere closes; while a pull-out is open the world
      stays live (floats keep floating — do not pause the stage).

## Proof required

Playwright: tap a meeting object → the pull-out opens with grouped
derivatives → NO navigation occurred (`location` asserted unchanged); tap
an artifact row → it opens in place; "Open full" → lands on
`/history?meeting=id`. Screenshots of each kind's pull-out on a seeded
desk. Drag still files/arranges without opening (threshold test). Route
pre-flight + full suite + `npm run build` green.
