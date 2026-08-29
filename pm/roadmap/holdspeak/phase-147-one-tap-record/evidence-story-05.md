# Evidence - HS-147-05

- **Story:** HS-147-05 - Snapshot polish riders (the 146 ledger pair)
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-29T05:35:27Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_calendar_snapshot_production_path.py tests/unit/test_calendar_snapshot_service.py tests/unit/test_calendar_snapshot_route.py && (cd web && npx vitest run src/pages/cores/__tests__/SettingsCalendar.test.tsx src/pages/cores/__tests__/CalendarSnapshotReviewCore.test.tsx)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1153762a30b6b4406677a7c94d11607175fb69a3

```text
.....................................                                    [100%]
37 passed in 6.48s

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  21 passed (21)
   Start at  23:35:34
   Duration  1.25s (transform 406ms, setup 133ms, import 648ms, tests 486ms, environment 606ms)
```

## Orchestrator triage note (2026-08-29)

Verified independently of the builder: diff eyeballed (the bare catch
at SettingsCore.tsx:879 replaced with the same
`setRefusal(readableError(error))` surface the settings module already
uses — matching the drop path's honesty at GlassDropLayer.tsx:70-72;
the `_vision_capable` pre-filter consults the v2 capability manifest
first, kind-heuristic fallback for unbound legacy profiles, and the
non-vision `resolve_placement` fallback is REMOVED so
`no_vision_model_assigned` fires with zero dispatches — asserted by
call count in the new tests). Focused runs re-executed by the
orchestrator and read from files: 37 Python passed (isolated HOME),
21 web passed (readable logs paired with this capture per protocol).
Full-sweep verification deferred to the next quiet-tree window
(story 01's builder was editing the shared tree at ship time) — the
sweep verdict lands in a later story's evidence per the quiet-tree
rule.
