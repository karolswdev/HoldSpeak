# Evidence - HS-200-15

- **Story:** HS-200-15 - Present actionable attention with controlled notifications
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-18T01:39:10Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8vIbqPtodW uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_attention.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a9a2164703162d06ad5ee45b4772f83788e2cde

```text
......................................                                   [100%]
38 passed in 1.97s
```

### Captured run — 2026-09-18T01:39:12Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.tJCsjXThCC PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_hs200_attention_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a9a2164703162d06ad5ee45b4772f83788e2cde

```text
........                                                                 [100%]
8 passed in 48.74s
```

## What was built

Five items in the first view, ranked overdue → due today → not run → no due date → waiting, then age, then id (a pure function in `holdspeak/services/attention_ranking.py` mirrored in `web/src/desk/attention.ts`, both bound to one JSON fixture `tests/fixtures/attention_ranking.json`). The display line is the true total and the caption carries the cap (`17 need you across 3 projects` / `NEEDS YOU 5 OF 17` / `12 MORE · Show all`); the Project token is withheld with one Project. Coverage rides above the answer as `CoverageRow` species, each unreadable source with its own token, observed time and verb. Duplicate projections of one obligation collapse only ACROSS sources and only when their refs agree; the `N SOURCES` disclosure lists each projection with its own title and `Open`. Notifications are set-based (`ItemSetEdge`): a changed item with the same count notifies (`· 1 new`), a class escalation notifies (`· 1 escalated`), quiet hours hold then deliver once, mute and restart re-notify nothing, recovery after a failed source never reads as an all-clear; `Nothing needs you` only when coverage is complete; items last observed before a failure stay `STILL TRUE · OBSERVED hh:mm`. Three library species promoted (`CoverageRow`, `ProjectButton`, `LedgerRemainder`); the selected `FilterTokens` token is secondary, so a face has exactly one filled primary. The 393 face is the same face: a wrapping meta line, ellipsised Project button, the sources body in the row's expansion slot, every interactive element inside the viewport (asserted per element, not by scrollWidth), the capture bar clearing the last section.

## Pre-fix failures (captured on the clean tip 7b0d5c3c)

```
E  AssertionError: {'kind': 'heartbeat.notify', 'outcome': 'held_no_edge', 'count': 3, ...}   assert 'held_no_edge' == 'sent'      # a changed item with the same count did not notify
E  AssertionError: assert ('sent' == 'held_quiet_hours'                                          # the first sweep at 23:00 fired: heartbeat_notify read datetime.now(), not the injected clock
E  At index 0 diff: ('HoldSpeak', '4 need you') != ('HoldSpeak', '4 need you · 1 new')
E  assert 'held_no_edge' == 'held_coverage_incomplete'
E  KeyError: 'last_notified_items'
8 failed, 21 deselected in 1.67s
```

## Counsel-on-built: BOUNCE, then paid

P0-1 the dedup key `(project, normalised title)` merged DISTINCT obligations (KAN-7 and KAN-12 "Rotate the staging credentials" became one row and KAN-12 vanished): `count (4 obligations in): 2` → now `4`; merge only across sources with agreeing refs; each projection openable. P0-2 a 31-char Project name pushed the Project button and the sources verb to x=443 on a 393 viewport, clipped by an ancestor so `scrollWidth` stayed 393: `elements past the viewport at 393: [... 'surface-project-button :: PAYMENTS PLATFORM MODERNISATION right=443.0']` → now `overflowing: []` at both widths, with the verb on the meta line. Conditions paid: the shared ranking fixture (the two implementations already diverged on `casefold` vs `toLowerCase`); the second filled primary (a species fix in `FilterTokens`); `last_notified_items` pruned for archived Projects and resolved Door cards while sets for cant_check/stale Projects are kept; class escalation notifies; the policy row is written only on change; the USER_GUIDE and ARCHITECTURE sentences corrected (proposal rows: `Confirm` on the row, `Open` in MORE; last-observed items survive a source outage "until the hub restarts"); shots gated behind `HOLDSPEAK_WRITE_SHOTS=1`; the 393 capture bar no longer covers the last section. The 1440 shot's outlined Project token was a hover state caught by the rig (pointer now parked before every shot). Counsel's probes re-run clean after.

## Carried to HS-200-13

Commitment rows are not attention items today; the `commitment` source, `CMT` emblem and due-driven class are built against synthetic rows. `LastKnownStore` is process-local: last-observed items do not survive a hub restart (the docs say so); persisting the last-known observation is the gap. `NOT RUN` awaits the meeting-intel producer.
