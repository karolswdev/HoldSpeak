# H-C4 — meeting list attendees

LANE: H-C4, backend handoff for PHILO-13-14 / C4 PR #754. Astra owns
the meeting list projection, calendar attendee persistence, backend fences
and this record. Worktree: `../wt-philo-13-hc4-astra`; branch:
`fix/philo-13-hc4-attendees`. Source base:
`ecb4e0f1d04e7872884adf31f24e569ff22a8513`. Date: 2026-10-03.

OUTCOME: built and verified for the scoped backend merge. This handoff does
not close PHILO-13-14. Tuesday: C4 receives the data needed to find a meeting
by a participant whose name is absent from the title (Tenets 1, 3 and 7).

## Contract for C4

Every row in `GET /api/meetings` has `attendees: string[]`, including the
search, faceted and parked list paths. With no participants it is `[]`,
never null or absent. The list combines saved segment speakers and the
attendees of the event referenced by `calendar_event_id`. It trims outer
whitespace, excludes blank strings, removes exact duplicates and sorts by
Python's case-sensitive string order. Commas and Unicode remain intact.

Calendar values retain the existing ICS parser's semantics: lowercase
email addresses with `mailto:` removed. This change does not resolve email
addresses to People names or read the ICS `CN` display name. A missing
calendar projection contributes no attendees; the meeting's speakers stay.
Previously projected events acquire their attendee data on the next feed
refresh. The response shape and search membership otherwise stay as they
were; attendee search in the palette belongs to C4's web lane.

## PROOF

Records live under [assets/h-c4](assets/h-c4).

- `collect-new.log`: six collected regression tests.
- `red.log`: all six fail before the product change, in 8.00 seconds. One
  reports the missing calendar model field; the five route fences reach
  their own missing `attendees` key. No producer or response is substituted.
- The producer chain is local ICS → calendar ingest conductor → persisted
  calendar event → `POST /api/scheduled-recordings` → the returned event id
  → `save_meeting` → `GET /api/meetings`. It exercises the real HTTP arm
  link and meeting persistence, not the scheduler's live recording loop.
- The fences cover transcript-only, calendar-only, combined, empty, search
  and parked rows. Names are absent from meeting titles. Assertions include
  exact overlap removal, blank speakers, outer whitespace, comma-containing
  names, Unicode, lexical order, repeated reads and repository/API agreement.
- `collect-final.log`: 256 collected nodes. `focused-final.log`: **256
  passed in 63.55 seconds**. Astra ran and read these results in the quiet
  lane tree. The command is below; all runs use isolated HOME. No full
  suite or Metal test was run.

```sh
HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH uv run pytest -q \
  tests/integration/test_philo13_meeting_attendees_api.py \
  tests/integration/test_web_meetings_facets_api.py \
  tests/unit/test_calendar_events_repository.py \
  tests/unit/test_calendar_parser.py \
  tests/unit/test_calendar_ingest.py \
  tests/unit/test_calendar_ingest_conductor.py \
  tests/unit/test_calendar_snapshot_route.py \
  tests/unit/test_scheduled_recording_routes.py \
  tests/unit/test_hs175_event_recordings.py \
  tests/unit/test_hs175_calendar_wire.py \
  tests/unit/test_db.py \
  tests/unit/test_reconcile.py \
  tests/unit/test_philo13_a3h_meeting_summary.py \
  tests/unit/test_philo13_meeting_parking.py
```

- `docs-checks.log`: API reference, OpenAPI, boundary census, configuration
  reference, graph, architecture validation and generated capabilities and
  coverage pass. API reference and OpenAPI changed with the route docstring
  and new test candidates; the graph changed only its OpenAPI input hash.
  The initial graph drift and successful regeneration are both retained.

## LEDGER

- Paid defect (b): calendar persistence dropped parsed attendees, and the
  meeting list had no participant projection. Both now pass the producer
  fences.
- Old fence (a): `focused-before-schema-fence.log` records 255 passed and
  one failed in 63.24 seconds. The calendar reconciliation test's exact
  schema-text replacement no longer matched after the new column was
  added. Its old-schema construction is corrected in the same commit,
  retaining the assertions that reconciliation preserves the row and
  adding `attendees_json == '[]'` plus a second, no-op reconciliation.
- The graph generator reports its existing 14 subtype-conflict notes.
  This lane changes no atlas, observation or claim review.
- Environment: Homebrew Node cannot load `libllhttp.9.3`. The existing
  Node 22.21.0 installation is used through command-local PATH. No owner
  installation or machine setting was changed.

## AMENDMENTS

The dispatch explicitly authorizes “Open a PR to main, self-merge it on
scoped proof, and post the merge record.” This is the authority for this
backend handoff's scoped verification and self-merge. No full-suite result
or fresh Muad'Dib counsel-on-built is claimed. The same dispatch assigns
`web/src/desk/api.ts`, the Meeting type, DeskToolShelf and full-path glass
at 1440 and 393 to C4's worker. This lane changes none of those files and
makes no C4 story-status flip. The original C4 check remains the caller's
record; this is a backend handoff, not a substitute C4 close.

## UNKNOWN

No owner sitting, scheduled live recording, full suite or palette glass is
proved by this backend handoff. The C4 lane must wire the field and prove
the rendered search transition at both widths before closing its story.
