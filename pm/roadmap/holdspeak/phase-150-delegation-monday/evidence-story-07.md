# Evidence - HS-150-07

- **Story:** HS-150-07 - The one-door reckoning (owner-ordered rider)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T00:11:07Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_follow_through_person_enrichment.py tests/unit/test_follow_through_service.py tests/unit/test_follow_through_mcp.py tests/unit/test_web_surface_orphans.py tests/unit/test_doc_drift_guard.py && cd web && npx vitest run src/desk/pullouts/views/FollowThroughView.test.tsx src/desk/pullouts/views/BriefView.test.tsx 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6f4b28e2d898a9a79dff6b0f466f368dd4a35337

```text
..........................................................               [100%]
58 passed in 99.08s (0:01:39)

 Test Files  2 passed (2)
      Tests  11 passed (11)
   Start at  18:12:55
   Duration  4.48s (transform 1.47s, setup 1.03s, import 2.77s, tests 368ms, environment 4.07s)
```

## Orchestrator triage — 2026-08-30

- **The owner's order verbatim intent**: "nip it in the bud" — the
  entry-point sprawl. Census before ruling: FollowThroughView is NOT
  a duplicate (provenance quotes, receipts/decision jumps, reopen,
  the AttentionDrawer overdue drill) — it stays as the DEEP room;
  FollowThroughLane WAS a true orphan (unimported since 144) — dead.
- **The orphan guard is orchestrator-authored**
  (tests/unit/test_web_surface_orphans.py) and proven BOTH
  directions: red on the pre-delete tree naming exactly
  `web/src/desk/chair/lanes/FollowThroughLane.tsx` and nothing else
  (no over-fire), green after the deletion. The class that let
  BriefLane sit unmounted for six phases is dead.
- **Verified by my own hand**: 58 Python + 11 web green (the four
  route-adapter pins: mapped→person_label, unmapped→none, MCP board
  person-free with the same data planted, sidecar-unavailable
  degrades; the orphan guard; the doc guards unfiltered; the
  FollowThroughView chip/staleness/initials tests). The route probe
  showed person_label + created_at served at the adapter with the
  service untouched; holdspeak/mcp/tools.py has ZERO diff.
- **Attribution check**: the builder's "pre-existing nested-button
  jsdom warning" claim VERIFIED — the follow-through-source button
  exists on main (:228) and the diff never touches it.
- **On real glass** (assets/story-07-rig.py, bundle rebuilt first,
  ×2 green): the deep room and the Door board render the SAME cards
  in the SAME grammar in one frame (Ewa waiting 3d chip both rooms;
  unmapped Marek = initials in the deep room, `owner Marek · map…`
  on the board). Shot: assets/story-07-shots/deep-room-chips-1440.png.
- **393 honest absence**: the pullout host does not operate at
  narrow AT ALL (pre-existing — navigate event no-ops, menus hidden;
  probed, not assumed). The rig records the posture and goes loud if
  narrow reachability ever ships. Joins the 149 "People at 393"
  reachability ledger family.
