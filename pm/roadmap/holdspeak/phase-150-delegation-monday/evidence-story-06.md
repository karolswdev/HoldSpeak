# Evidence - HS-150-06

- **Story:** HS-150-06 - The walk and the close
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T22:18:32Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-150-delegation-monday/assets/walk-rig.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 61c5363db35914e6a60759eb9ce116e7293589f8

```text
MONDAY PROBE: person-blind -> People section in the response, 3 persisted rows scanned clean
DELEGATION PROBE: scan-every-card -> chip + filter + staleness on glass
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-150-delegation-monday/assets/walk-shots
```

## Close sweep — 2026-08-29 (readable: scratchpad/hs150-close-sweep.log + hs150-webbase.log)

**Pytest:** 15 failed / 6985 passed / 53 skipped (8:55, -n auto,
isolated HOME). Verdict: **11 inherited-baseline + 4 dispositioned =
zero unresolved branch-new.** Diffed name-by-name against 149's close
sweep (the ruled zero-unresolved set); 149's device_recording_tick
xdist flake did not recur. The four dispositions, each healed and
re-run green:

1. test_api_surface manifest — 543→545: EXACTLY story 01's two
   owner-alias routes (POST/DELETE …/owner-aliases). Lawful regen via
   scripts/gen_api_surface.py; diff verified ours-only.
2. phase143 routing census — models/__init__.py resolver_profile_id
   1123→1124: one-line shift from story 01's delegated_at field on
   ActionItemSummary. Remapped 1:1 with attribution.
3. phase143 inference census — tools.py dispatch 609/613→641/645:
   shift from story 03's MCP overlay adapter above them. Remapped 1:1
   with attribution.
4. test_hs144_door_glass band law — REAL branch-new consequence of
   the ruled BriefLane mount: the 144 "meetings+agents one equal
   band" pin met a four-lane chair. Ruled to the new truth
   (BRIEF+MEETINGS form the equal band; AGENTS spans full width
   below via a new dangling-even-last-lane CSS rule — killing the
   orphaned half-width lane the mount would otherwise leave, the joy
   fix). File green ×2 SERIAL after the fix; the walk rig re-run
   green under the new geometry; prior-phase asset dirs (141–149)
   restored after every glass run.

**Web (story 04's checker, --run):** 1425 passed / 6 failed —
**"baseline-subset/exact, zero branch-new"** (verdict verbatim);
the six failures are the six baseline names exactly, each matched.
