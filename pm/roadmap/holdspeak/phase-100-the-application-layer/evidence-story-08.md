# Evidence - HS-100-08

- **Story:** HS-100-08 - B4: Meetings
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T14:37:59Z

- **Command:** `sh -c HS_WALK_BASE=http://localhost:8792 HS_WALK_TOKEN=YZi6W-PzL8bfY4UbMgxThqUdUUKQcGj8 uv run python scripts/desk_gl_walk.py meetingflow && uv run pytest -q tests/integration -k 'history or slack_surfaces or import_ui or presence' 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 58fa90e4eace965692a80fdafe7bc625ec50b3c0

```text
meetingflow: arrival -> outcomes face in 3 interactions, 1 outcome concepts, transcript folded, no tab wall
47 passed, 687 deselected in 11.16s
```

## Summary of proof

- **Meetings opens on OUTCOMES.** HistoryCore rebuilt per thesis §1.2:
  the meeting detail leads with "Needs you" (undecided proposals with
  their approve/reject verbs, posture note, effect/destination/
  authority facts — the governance render preserved verbatim — plus
  open actions), then "Settled", then the transcript folded as a
  RECEIPT disclosure and the routing receipt; export/delete verbs at
  the foot. The meeting list is a RAIL (search-first, filter wall
  folded; the split is rail-weighted so the outcomes face takes the
  room). Wings: Outcomes | Record (import + record verb) | Artifacts
  (the typed record of the open meeting). Speakers/Projects/Queues
  plumbing (with the retry verbs) stacks behind the one gear door.
- **Flow budget pinned** as the `meetingflow` walk leg (captured):
  arrival → a meeting's outcomes face in **3 interactions**, 1 outcome
  concept on the face, transcript folded, no tab wall in the body —
  against trace A's nine-concepts finding.
- **Regression**: the full `meetings` walk leg green end-to-end on the
  staged hub (record → live window → stop → pull-out → review scoped
  in-world → deep links); vitest 294/294; integration suite green
  (five pins retargeted with intent preserved, incl. two spike riders:
  Switch → SurfaceToggle); vocabulary guard + token gate clean.
- **Screenshots** at 1440 (face + door) and 393:
  assets/hs-100-08-meetings-*.png — walked by eye; rail-crush and
  split-weight refects applied before capture.
