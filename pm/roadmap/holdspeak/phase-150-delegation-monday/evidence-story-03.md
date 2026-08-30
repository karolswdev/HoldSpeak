# Evidence - HS-150-03

- **Story:** HS-150-03 - The chief-of-staff overlay (person_sections)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T22:08:44Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json uv run --python 3.13.11 pytest -q tests/unit/test_person_overlay.py tests/unit/test_brief_mcp.py tests/unit/test_monday_brief_service.py tests/unit/test_people_brief.py tests/unit/test_walk_monday_brief_126.py && cd web && npx vitest run src/desk/pullouts/views/BriefView.test.tsx src/desk/chair/lanes/BriefLane.test.tsx src/desk/chair/Chair.test.tsx src/desk/chair/ChairHome.test.tsx 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 55e091886859d1e2d64a4dfa832dc1ff8a44d2a7

```text
..................................................                       [100%]
50 passed in 6.09s
 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  4 passed (4)
      Tests  57 passed (57)
   Start at  16:08:51
   Duration  933ms (transform 768ms, setup 195ms, import 1.40s, tests 474ms, environment 852ms)
```

## Orchestrator triage — 2026-08-29

- **Verified by the orchestrator's own hand**: the captured run above
  re-ran green before the flip; all five counsel pins present verbatim
  (write-count spy; pipeline_events content check; the MondayBrief
  dataclass shape pin; the F6 MCP gate with a planted leader_private;
  the L2 refusal) plus the D2 path-hygiene pin.
- **Two orchestrator-driven deltas after round 1**:
  (1) Staleness reconciled to the RULED law — `_stalest_age` now
  reads `delegated_at ?? created_at` (story 02 added created_at to
  FollowThroughCard); the `due` proxy is gone; three-case fallback
  pin in TestStalenessAgeOrder.
  (2) **BriefLane was ORPHANED**: my glass rig found the chair showed
  zero Brief presence — HS-144-03 (9a5cfce5) dropped `brief` from
  LANE_ORDER and LANE_COMPONENTS, so the D1 act state lived in an
  unmounted component with green jsdom tests. Mount restored (brief
  second, after door), Chair/ChairHome tests updated, and a registry
  pin added (every LANE_ORDER id must have a LANE_COMPONENTS entry)
  so a lane can never silently unmount again.
- **Orchestrator surgical fix**: BriefView's `person-row-*` testid
  was silently dropped by SurfaceLedgerRow (the primitive didn't
  forward it) — the primitive now accepts an optional data-testid
  (Surface.tsx, 3 lines); rig selection runs through it.
- **On real glass** (assets/story-0203-rig.py): the D1 act on the
  empty AND populated chair; Generate → the People section with
  EXACTLY the gestured person (Marek's owner-string cards did NOT
  appear — the no-inference law asserted, not just observed); row
  selection → Add-to-1:1-agenda + Open-person verbs. Shots:
  assets/story-0203-shots/ (brieflane-act / brieflane-act-populated /
  brief-person-sections / brief-person-verbs).
- **Privacy**: person_sections composes at the route/MCP adapter via
  compose_person_overlay; the persisted MondayBrief never carries it;
  the MCP overlay stays gated on access_mode()=="off".
