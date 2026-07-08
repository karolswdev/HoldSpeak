# Evidence — HS-86-03 — The receipts the conveyor lacks: gh lights + belt frames

- **Shipped:** 2026-07-07
- **Commit:** (this commit)
- **Owner:** agent (Claude), owner-directed

## Files touched

- `holdspeak/missioncontrol_bridge.py` — `receipts_entry` /
  `receipts_payload`: `gh pr list --json
  number,title,url,headRefName,statusCheckRollup` with `cwd=repo`,
  injectable runner, typed `unavailable` for gh missing / nonzero /
  non-JSON / non-list.
- `holdspeak/web/routes/missioncontrol.py` — `GET
  /api/missioncontrol/receipts`; `_BELT_TREES` + `_emit_belt_frames`
  (one `scope:"belt"` frame per repo per observed
  `generated_at_tree` change; first observation is a baseline);
  the three existing reads wrapped in `asyncio.to_thread` (the
  Phase-85 event-loop rule — they were shelling a 30 s-timeout CLI
  on the loop).
- `tests/unit/test_web_routes_missioncontrol.py` — 6 new cases
  (receipts relay, typed gh failure in a 200, non-JSON, GET-only
  fitness, no-frame-on-unchanged, one-frame-on-change with the
  pinned vocabulary).
- `docs/api-surface.json` + `docs/API_SURFACE.md` regenerated
  (248 routes; consumers regen again in HS-86-04 when the web call
  site lands).

## Verification artifacts

```text
$ uv run pytest -q tests/unit/test_web_routes_missioncontrol.py
22 passed in 0.77s
```

Live receipts against the operator's real project map (gh, real
network):

```text
$ python3 -c "...receipts_payload(load_project_map())..."
{"repos": [{"name": "delivery-workbench", "path": "/Users/karol/dev/code/delivery-workbench",
  "status": "live", "prs": []}]}
```

(Zero open PRs is the truthful state: upstream PR #2 merged earlier
this session.)

```text
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3305 passed, 37 skipped, 1 warning
```

Rails verification of the previous story's trailer (owed by
HS-86-02's evidence):

```text
$ .githooks/dw verify HEAD~1..HEAD   # the HS-86-02 commit
dw verify: ok (1 commits verified, 0 pre-epoch skipped)
```

## Acceptance criteria — re-checked

- [x] Receipts for the live map relay PR lists + rollups; gh failure
      is `unavailable` inside a 200 — tests + live capture above.
- [x] Unchanged tree ⇒ zero frames; changed tree ⇒ exactly one frame
      in the pinned vocabulary — `TestBeltFrames`.
- [x] GET-only fitness over the story's additions —
      `test_receipts_route_is_get_only`.
- [x] Full suite green — appended.

## Deviations from plan

Rider fix, named: the three Phase-82 reads ran their subprocess
relays directly on the event loop; wrapped in `asyncio.to_thread`
per the Phase-85 rule while adding the fourth read.

## Follow-ups

None — HS-86-04 consumes the receipts and the frames.
