# HS-77-01 — The agent's pinned context survives the hub

- **Status:** done
- **Severity:** HIGH
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; the schema-sensitive guards
  (snapshot/matrix/serialization) updated per the documented recipes when
  they fire; full suite green at ship.

## Done

Shipped. Schema v7 (additive guarded ALTERs, the v4 recipe); every hub
layer speaks the two fields (record/wire, upsert/row, REST with
partial-PUT preservation, the sync merge map); the pushed-agent round
trip is byte-faithful (the exact Phase-72 loss, now a test); the
v6-facsimile upgrade proven with the pre-migration backup; the Swift
tolerant-decode comment records the loss ending with zero functional
Swift change. 4/4 first try; both fired guards updated honestly. See
[evidence-story-01.md](./evidence-story-01.md).
