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

### Captured run — 2026-08-29T23:08:33Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-150-delegation-monday/assets/walk-rig.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7a2e12230b064acc2e7803fd37e517ce4022f89f

```text
MONDAY PROBE: person-blind -> People section in the response, 3 persisted rows scanned clean
DELEGATION PROBE: scan-every-card -> chip + filter + staleness on glass
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-150-delegation-monday/assets/walk-shots
```

## The owner catch — 2026-08-29, post-close amendment (the working band made law at every height)

The owner looked at the exhibit and called it: full-page frames
showed the desk "completely fucked up" with content scrolling past
the bottom bar. Orchestrator triage had waved this off as a
screenshot-stitching artifact — WRONG. Diagnosis on real glass:

1. **The 144-04 working-band containment was gated to
   `max-height: 720px`** on the premise the normal-height Chair fits
   all at once — retired by the four-lane chair. At 1440×900 and
   393×852 the desk BODY scrolled, sliding lanes beneath the fixed
   dock and system bar.
2. **A margin-collapse bug made it worse**: the Chair's 54px
   working-band top margin collapsed through `.desk-next` → `main`
   → `body` (all padding-less), pushing the whole document exactly
   54px past the viewport — so even an otherwise-fitting desk
   body-scrolled.

Fixes (chair.css, desk.css, react-app.css): the chair-level
containment promoted to ALL heights (`.chair:not(.chair-first-value)`
capped to the band; `.chair-lanes` owns overflow-y); `display:
flow-root` on `.app-immersive` AND `.desk-next` so child margins can
never escape the shell again.

Proof: a new PERMANENT walk leg (the containment probe) at both
widths — asserts the scrolling element does not overflow, scrolls the
lane column to its bottom, and asserts the lane column's bottom stays
above the dock's top. The leg FAILED on the pre-fix tree at both
widths (findings recorded in the rig's honest vocabulary) and passes
now; walk ×2 green + the stamped capture above is the final-tree run;
door-glass e2e 9/9 re-green; the exhibit re-shot clean
(band-contained-1440/393.png are the at-rest and scrolled frames).
Prior-phase asset dirs restored after every glass run.

Lesson recorded: "screenshot artifact" is an attribution claim like
any other — walk it before waving it off.
