# HS-102-04 — The Meetings wings: Outcomes / Record / Artifacts

- **Project:** holdspeak
- **Phase:** 102
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "Meetings -> Outcomes -> Record -> Artifacts - needs the same
> treatment."

## Problem

The Meetings window (`web/src/pages/cores/HistoryCore.tsx`, wings
`outcomes` / `record` / `artifacts`) got the round-6 meeting-detail
fix and the round-7 drop well, but the wings as WHOLE FACES were
never recomposed. The round-7 inventory names the artifacts half
directly: "Artifacts wing when populated: Disclosure+SurfaceCode
dumps — should be the library composition (the artifact body as the
face)." Outcomes must read as the REVIEWING posture (dense rows,
verdict verbs inline, receipts behind disclosures — not uniform
SurfaceRows); Record must lead with its two verbs (record now /
drop-import) rather than burying them among fields; Artifacts must
be the library (canon rule 2 — content-forward tiles whose face IS
the payload, `SurfaceLibrary` exists in the kit).

## Scope

- In: the three wing faces of `HistoryCore.tsx`. Outcomes: the
  reviewing posture over real intelligence results (needs-you
  leads, verdict verbs on the rows, receipts fold). Record: the
  drop well + record verb lead; detail fields appear only once
  material exists (round-7 grammar, finished). Artifacts: the
  `SurfaceLibrary` composition — the artifact's body is the tile
  face, name at primary, provenance (which meeting, when) at
  secondary; a tile opens the artifact card (the round-9 object
  card). Facet/filter chrome shrinks to the caption step.
- Out: meeting detail (round 6, shipped); import wire routes;
  intelligence plugins; the meetingflow budget (must stay ≤ 3
  interactions — the leg pins it).

## Acceptance criteria

- [ ] Hands-first ledger recorded (headed, 1440 + 393; each wing
      empty AND populated — import material through the real wire
      first) before code.
- [ ] Outcomes: reviewing posture; no undifferentiated SurfaceRows
      wall; verdict verbs on the material.
- [ ] Record: verbs lead; no label stack before material exists.
- [ ] Artifacts: the library composition; no Disclosure+SurfaceCode
      dumps; a tile opens the object card.
- [ ] meetingflow leg still green (arrival → outcomes in ≤ 3
      interactions) plus a grown assertion for the artifacts
      library.
- [ ] Driven live on a staged hub with real imported material; both
      viewports, screenshots read.

## Test plan

- Web vitest; token gate; vocabulary + interior-canon guards;
  geometry + meetingflow walk legs (meetingflow grown, not
  loosened); the live wing drive on a staged hub, headed, both
  viewports.

## Evidence required

- The ledger; before/after per wing; walk output; guard output.
