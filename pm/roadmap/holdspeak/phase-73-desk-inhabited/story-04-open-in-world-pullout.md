# HS-73-04 — Open in-world: the pull-out

- **Status:** todo
- **Priority:** HIGH (kills the bounce-out — the single worst touch on the old surface)
- **Depends on:** HS-73-01

## Goal

Tap an object and it opens *here*: a drawer slides out on the stage beside
it — the React port of the iPad's `DioPullout`
(`DeskDioramaStage.swift:~1221`) and the meeting drawer (PR #196). The
legacy `openObject` bounce-out (meetings → `/history?meeting=id`, everything
else → the admin list) does not get ported. **"Open full" is the only
navigation on the desk.**

## Scope

- **In:** the `Pullout` component; per-kind content; the meeting drawer's
  lineage grouping; "Open full"; Move-to (the no-drag filing path).
- **Out:** the agent Run's theater choreography (HS-73-07 — this story
  ships the agent pull-out with a Run button wired to the existing route);
  live-meeting content (the orb story decides what a live meeting's
  pull-out shows).

## Tasks

- [ ] `Pullout` component: slides from the object's side (chosen by stage
      half) with a `motion` spring; header = sprite + title + kind tint +
      egress badge where applicable (port `profileEgress`,
      `desk-app.js:618`); Escape/tap-elsewhere closes; the world stays
      alive behind it (floats keep floating).
- [ ] Tap-vs-drag: reuse HS-73-01's >4px threshold; a completed drag never
      opens.
- [ ] **Meeting pull-out**: on open, fetch `GET /api/meetings/{id}` (the
      payload nests `intel_status` — the repo's documented gotcha) +
      `GET /api/meetings/{id}/artifacts`. Group derivatives by lineage —
      port `lineage(sources)` / `hasLineage` (`desk-app.js:853/880`);
      sections: summary, actions, artifacts. An artifact row opens in
      place (a one-deep stack with back).
- [ ] **Note/KB pull-out**: content rendered; Edit swaps in the HS-73-03
      `InlineEditor`.
- [ ] **Agent pull-out**: avatar, role, prompt summary (label-voice),
      profile + egress badge, Run (full choreography in HS-73-07).
      **Chain/workflow pull-out**: steps listed + Run.
- [ ] **Move to…** action in every filable kind's pull-out (the no-drag /
      keyboard filing path — the lesson of iPhone filing, PR #195): a
      compact zone list writing the same
      `PUT /api/directories/{id}/members/{pid}`.
- [ ] **"Open full"** in the header only: meetings → `/history?meeting=id`;
      agents/chains/workflows → their `/studio` surface where one exists.
      Nothing else navigates.

## Proof required

Playwright: tap a meeting → pull-out with grouped derivatives →
`location` asserted unchanged; artifact row opens in place; "Open full"
navigates (the one sanctioned exit). Screenshots of each kind's pull-out on
a seeded desk. Drag still arranges/files without opening. Route pre-flight
+ full suite + `npm run build` green.
