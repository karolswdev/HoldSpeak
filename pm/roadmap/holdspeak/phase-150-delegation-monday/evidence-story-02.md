# Evidence - HS-150-02

- **Story:** HS-150-02 - The delegation lane (chips, filter, staleness)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T22:06:34Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_door_read_model.py tests/unit/test_follow_through_service.py tests/unit/test_owner_gesture.py tests/unit/test_door_routes.py tests/unit/test_door_transport_parity.py tests/unit/test_door_mcp.py && cd web && npx vitest run src/desk/chair/lanes/DoorBoardLane.test.tsx src/pages/cores/__tests__/peopleCore.test.tsx 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 727017801822d7f8efc3b4ccf68262cb5b62bd51

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 13.89s
 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  67 passed (67)
   Start at  16:06:49
   Duration  1.50s (transform 491ms, setup 89ms, import 740ms, tests 1.30s, environment 358ms)
```

## Orchestrator triage — 2026-08-29

- **Verified by the orchestrator's own hand**: the captured run above
  (90 Python + 67 web) re-ran green under the story-01 seam before the
  flip; output read from the file, not chained.
- **On real glass** (assets/story-0203-rig.py, bundle rebuilt first,
  fresh contexts + occlusion tells): the REAL map gesture on Marek's
  card opened the picker; Ewa's mapped cards wear the person chip +
  `waiting 4d` staleness; the Everyone/Ewa filter flips the board; the
  unmapped card shows `owner Marek · map…` and NOTHING else — the
  no-inference law visible. Shots: assets/story-0203-shots/
  (board-unmapped / map-picker / board-mapped-chips /
  board-filtered-ewa / board-mapped-393 / people-owner-aliases).
- **Orchestrator surgical fixes folded into this story**:
  (1) DoorBoardLane.test.tsx:915 — the zero-auto-map pin typed its
  filter param as `[string]`, the one branch-new tsc error on the
  whole tree; retyped, 52/52 green after. Attribution: the other nine
  tsc-erroring files are unmodified on this branch (inherited).
  (2) The rig scoped People-window clicks to `.desk-surface-windows` —
  story 02's own board chips put "Ewa" text BEHIND the window (a new
  interception scar for walk briefs).
- **Staleness law**: `delegated_at ?? created_at` — `created_at` added
  to FollowThroughCard here (follow_through_service.py:82/:183) and
  consumed by story 03's overlay (reconciled there, three-case pin).
- **Privacy**: board() stays person-free (Door-only enrichment in
  door_service._follow_through_card); observer redaction pinned at
  test_door_read_model.py:696-728; zero-auto-map pinned.
