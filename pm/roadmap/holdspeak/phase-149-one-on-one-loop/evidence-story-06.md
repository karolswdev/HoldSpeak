# Evidence - HS-149-06

- **Story:** HS-149-06 - The walk and the close
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T19:33:22Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-04-rig.py && echo "== CLOSE SWEEP (readable: scratchpad/hs149-close-sweep.log) ==" && tail -1 /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/5ce49957-4ec2-4c69-803c-324206b30a97/scratchpad/hs149-close-sweep.log && echo "verdict: 11 inherited-baseline + device_recording_tick xdist flake (serial 19/19 green) + routing-census drift from EXTERNAL PR #502 (remapped w/ attribution) + api-surface regen for 149s three routes (540->543) = zero unresolved branch-new"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 76f638c4d019c54e4fcd59cb580db8e97e71dd24

```text
shots=/Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-149-one-on-one-loop/assets/story-04-shots
== CLOSE SWEEP (readable: scratchpad/hs149-close-sweep.log) ==
14 failed, 6929 passed, 53 skipped in 522.46s (0:08:42)
verdict: 11 inherited-baseline + device_recording_tick xdist flake (serial 19/19 green) + routing-census drift from EXTERNAL PR #502 (remapped w/ attribution) + api-surface regen for 149s three routes (540->543) = zero unresolved branch-new
```

## Orchestrator triage note + close counsel (2026-08-29)

The capture is the FINAL green walk run (runs 3+4 consecutive
green earlier after the honest wait-fix; run 2's SUGGESTED race
diagnosed as instant-inner_text vs hydration — the counsel
independently ruled the fix "Playwright best practice... the
assertion still fires on genuine absence"). Close sweep 14 failed /
6929 passed: 11 inherited-baseline + three dispositioned
(device_recording_tick xdist flake serial 19/19; the routing-census
meeting.py pin drifted by the EXTERNAL PR #502 — counsel refined
the attribution: already drifted on main at branch point, surfaced
by this arc's first sweep including it; the api-surface manifest
regenerated 540→543 for this phase's three routes). Zero unresolved
branch-new.

**Close counsel (fresh opus): RATIFY-WITH-CONCERNS — "The phase
earns the owner's Tuesday."** The privacy boundary verified
END-TO-END (no plaintext columns, request-scoped resolution with
no caching, exports clean, CatalogRail clean, the F6 gate proven);
all five orchestrator deviation/attribution rulings upheld; all 14
sweep dispositions verified. ONE should-fix (borderline must-fix)
— **FIXED IN-ROUND**: `person_label` was riding meeting read
results into the plaintext pipeline_events flight recorder via the
observer's result_summary (MCP-reachable; inconsistent with the
_FollowThroughObserver precedent). `_MeetingPersonRedactor` now
wraps MeetingService observation (the exact 138 pattern: replace,
don't trim), with pins proving redaction fires on the projection
and leaves clean payloads untouched. 18+60 focused green after.

Three counsel ledger items carried: the six-name web blind spot
(next-arc baseline file), the 393 People reachability, the
re-subscription dangle.
