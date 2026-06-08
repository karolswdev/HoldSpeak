# Evidence — HS-53-02: the nudges API

Write-once record of the HTTP surface over the HS-53-01 engine. Two thin routes,
`TestClient`-tested over a real `MeetingWebServer` app + a seeded SQLite DB. The web UI
(HS-53-04) consumes this; nothing else changes.

## What shipped

- **New router `holdspeak/web/routes/activity/nudges.py`** (~70 lines): `build_nudges_router(ctx)`.
  Two endpoints, both small wrappers over already-built primitives:
  - `GET /api/activity/nudges?project_id&limit` — calls
    `activity_nudges.compute_nudges(db, project_id=..., limit=...)`, returns
    `{"nudges": [...], "activity_enabled": bool}`. Dismissals are already filtered by
    the engine; this route does not need its own filter pass.
  - `POST /api/activity/nudges/{nudge_id}/dismiss` — calls
    `db.activity.dismiss_nudge(nudge_id)`, returns `{"dismissed": "<key>"}`.
    Whitespace-only keys yield a clean 400 (via the repo's `ValueError`).
- **Wiring.** `web/routes/activity/__init__.py` imports `build_nudges_router` and
  `include_router`s it after the existing five sub-routers — no change to the public
  `build_activity_router(ctx)` entry point.
- **Route-table lock updated.** `tests/unit/test_activity_routes_split.py` gains the two
  new `(path, method)` pairs and the count assertion ticks from **38 to 40**. This is
  the byte-identical contract the Phase-34 split established; the assertion still locks.
- **No engine changes.** The route is intentionally thin — the engine returned
  JSON-safe nudges in HS-53-01 (`Nudge.to_dict()` is `json.dumps`-clean), so the route
  is a one-line shape over it.

## Why this is honest

- **Consent gate stays in the engine.** The route does not re-check
  `get_activity_privacy_settings()["enabled"]` — `compute_nudges` already returns `[]`
  when activity is off, and the integration test
  `test_get_nudges_is_empty_when_activity_off` proves the route inherits that gate.
- **No new state.** Dismissals go through the existing `ActivityRepository.dismiss_nudge`
  added in HS-53-01. The route is stateless.
- **Citations preserved.** The integration test
  `test_get_nudges_returns_source_cited_records` reaches into `body["nudges"][0]["citations"]`
  and asserts `source_browser` + `record_id` — the contract a `/activity` user can verify.

## Tests

`tests/integration/test_web_activity_nudges_api.py` — 5 tests, every acceptance bullet
covered, all under `pytest.mark.integration` + `pytest.mark.requires_meeting`:

- `test_get_nudges_returns_source_cited_records` — happy path; citations carry
  `source_browser` + `record_id`.
- `test_get_nudges_is_empty_when_activity_off` — the consent gate inherited from the engine.
- `test_dismiss_removes_nudge_from_subsequent_get` — the dismiss round-trip: GET shows
  the key, POST dismisses, second GET no longer shows it.
- `test_dismiss_blank_key_returns_400` — whitespace-only `nudge_id` is a clean 400, not a
  500.
- `test_get_nudges_respects_limit_query` — 6 candidate records + `?limit=2` returns
  exactly 2 nudges.

`tests/unit/test_activity_routes_split.py` — the byte-identical route-table lock:

- `test_activity_route_table_is_unchanged_after_split` — the set now contains the two new
  nudge routes and nothing else moved.
- `test_activity_route_count_is_stable` — 40 (was 38).

```
uv run pytest -q tests/integration/test_web_activity_nudges_api.py tests/unit/test_activity_routes_split.py
-> 7 passed in 1.00s

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2514 passed, 17 skipped in 75.71s
   (was 2509 at HS-53-01 close; +5 is the new integration tests; the two unit
    route-lock tests are updated in place, not added.)
```

0 `_built/` tracked; no UI bundle touched (the UI lives in HS-53-04).

## Not done here (by design)

- **The dictation-context override** ("dictate with this as context") — HS-53-03.
- **The nudge card UI** — HS-53-04.
- **The user guide** — HS-53-05.
- **Dogfood + phase close** — HS-53-06.

## Files touched

- `holdspeak/web/routes/activity/nudges.py` (new) — the router.
- `holdspeak/web/routes/activity/__init__.py` — wired the router into the composed
  `build_activity_router(ctx)`.
- `tests/unit/test_activity_routes_split.py` — extended the locked set + count.
- `tests/integration/test_web_activity_nudges_api.py` (new) — 5 `TestClient` tests.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/story-02-nudges-api.md` — status
  flipped to `done`.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/current-phase-status.md` — story
  table updated, "Where we are" updated.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
