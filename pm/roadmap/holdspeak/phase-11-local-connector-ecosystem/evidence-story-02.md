# HS-11-02 evidence — Connector fixture and dry-run test harness

## Files shipped

- `holdspeak/connector_fixtures.py` (new) — the harness:
  - `ConnectorFixture` frozen dataclass: id, connector, limit,
    activity_records to seed, and an `expect` block.
  - `ConnectorFixtureExpectation`: every field optional; if
    `None` the harness skips that assertion. Lets a fixture
    express only the invariants it cares about (an empty-ledger
    fixture asserts `command_count: 0` + a `warnings_contain`
    string without re-locking `kind`).
  - `load_fixture(path)` and `discover_fixtures(directory)` for
    JSON loading.
  - `run_fixture(db, fixture)` seeds the activity_records,
    snapshots `activity_annotations` + `activity_meeting_candidates`
    row counts, calls
    `holdspeak.activity_connector_preview.dry_run()`, asserts
    every populated `expect` field, then re-snapshots and
    asserts neither table moved.
  - `FixtureRunResult.diff_report()` renders failures as one
    line per drifted field plus a summary of the actual
    payload (kind, capabilities, counts, warnings, permission
    notes). On a real failure the operator can copy the
    summary block back into the fixture's `expect` block if
    the drift is intentional.
- `tests/fixtures/connectors/` (new) — six golden fixtures, two
  per first-party connector:
  - `gh-happy-path.json` (PR + issue → 2 commands, 2
    annotations, "disabled" permission note).
  - `gh-empty-ledger.json` (no records → 0 commands, "No
    GitHub" warning).
  - `jira-happy-path.json` (2 tickets → 2 commands, 2
    annotations).
  - `jira-empty-ledger.json` (no records → "No Jira" warning).
  - `calendar-happy-path.json` (calendar + meet → candidates
    proposed; cli_required null).
  - `calendar-empty-ledger.json` (no records → "calendar"
    warning).
- `tests/unit/test_connector_fixture_harness.py` (new) —
  parametrizes `pytest` over every JSON file under
  `FIXTURES_DIR`. Adding a new fixture is the only step
  required to extend coverage; the test surface auto-grows.

## Tests

```
$ uv run pytest tests/unit/test_connector_fixture_harness.py -q
…
8 passed in 0.25s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1277 passed, 13 skipped in 29.00s
```

8 new tests:

| Test | What it locks down |
|---|---|
| `test_fixture_dry_run_matches_expectation[gh-happy-path]` | gh seeds 2 records → 2 commands, 2 proposed annotations, disabled note. |
| `test_fixture_dry_run_matches_expectation[gh-empty-ledger]` | gh on empty ledger → 0 commands, "No GitHub" warning. |
| `test_fixture_dry_run_matches_expectation[jira-happy-path]` | jira seeds 2 tickets → 2 commands, 2 annotations. |
| `test_fixture_dry_run_matches_expectation[jira-empty-ledger]` | jira on empty ledger → "No Jira" warning. |
| `test_fixture_dry_run_matches_expectation[calendar-happy-path]` | calendar_activity seeds calendar + meet records → candidate_inference kind, cli_required null. |
| `test_fixture_dry_run_matches_expectation[calendar-empty-ledger]` | calendar_activity on empty ledger → "calendar" warning. |
| `test_discover_fixtures_finds_every_committed_fixture` | sanity — loader returns the six in stable id order. |
| `test_fixture_failure_reports_readable_diff` | builds a deliberately-wrong fixture, asserts every drifted field appears in the failure report alongside actual values. |

The mutation-free guarantee is locked down by the harness
itself — every fixture run asserts `annotations_after ==
annotations_before` and the same for candidates. Add any new
fixture and you get the no-mutation check for free.

## How acceptance criteria are met

- **Fixtures can drive connector preview behavior.** Six JSON
  fixtures committed; the harness dispatches them through
  `dry_run()` (the same entry point the `/api/activity/.../dry-run`
  endpoint and the `/activity` connector cards use).
- **Dry-run tests assert no database mutation.** `run_fixture()`
  does pre/post row-count snapshots and adds a failure entry
  when either count moved; the parametrized test then asserts
  on the result.
- **First-party connectors can share the same harness.** The
  six fixtures span all three known connectors (`gh`, `jira`,
  `calendar_activity`) using the same `expect` schema.
- **Fixture failures show readable diffs.** Verified by
  `test_fixture_failure_reports_readable_diff` — operators see
  every drifted field with expected + actual values and a
  payload summary they can paste back as the new expectation
  if the drift is intentional.

## Notes

The harness is deliberately *additive* — phase-11 connector
packs (HS-11-03..05) drop a JSON fixture and inherit the full
no-mutation + shape-assertion test surface. The fixture format
is JSON (not YAML, not Python) so connector-pack authors don't
need to touch test infrastructure to add coverage.
