# HS-144-02 — Calendar ingest (ICS first): implementation plan

**Planning baseline:** `feat/hs144-01-door-read-model`, read 2026-08-27. This is a backend/projection story. It creates one persisted calendar subscription contract and one bounded background reader; it does **not** put calendar glass under `web/src/`. HS-144-04 owns the Settings and Door presentation, including its required 1440/393 mic/egress shots. The settled Phase 144 design §4 (ICS first; one file-or-HTTPS subscription; no OWA, CalDAV, auth headers, or credential storage) and Story 01 plan §3 are accepted input, not reopened.

## 0. Non-negotiable contract and guardrails

1. **One source, not a connector platform.** A nonempty `calendar.subscription` is either an absolute/local file-path source or an `https://` source. It is not an account, OAuth grant, CalDAV endpoint, header bag, or a plural list. A URL with userinfo, a non-HTTPS scheme, or a redirect is refused at the settings/fetch boundary; a file source makes no network request.
2. **Projection, never authority.** `calendar_events` is a replace-on-success projection of the one source. It stores only the fields Story 02 needs, does not write meetings or schedules, and does not auto-create a recording.
3. **Do not blank a working Door.** Fetch failure or a feed-level parse failure retains the last known-good projection. A successful parse applies its whole desired set atomically; therefore a vanished event vanishes honestly. An individual bad `VEVENT` is skipped, named by a receipt, and cannot abort its neighbours or the hub.
4. **The Story-01 upcoming shape is fixed.** Calendar rows join server-side as `{id, source: "calendar_event", target_ref, title, starts_at, ends_at, location, meeting_url, state: "scheduled"}`. Instants are UTC ISO-8601; the aggregate retains Story 01's `(starts_at, source, id)` sort and derives `upcoming_today` from the completed merged timeline. No browser merge and no shape/version migration.
5. **All expensive/untrusted input is bounded.** Read at most 5 MiB from either source, reject a redirect, use a 10-second socket timeout, accept at most 2,000 raw `VEVENT`s, 4,000 projected rows per refresh, and 128 occurrences per recurring master. Expand only `[now, now + 14 days)`. A `SECONDLY` or unbounded RRULE therefore cannot turn a settings value into an unbounded loop.
6. **No silent background work.** Successful routine refreshes do not mint 96 ledger rows/day. A malformed event or failed refresh gets a deduplicated existing-kernel receipt; no new receipt table, UI system, or free-form event log is invented.
7. **Verification hygiene.** Every command which could load a DB uses `HOME="$(mktemp -d)" uv run --python 3.13.11 ...` from repository root. This plan deliberately names focused tests only; it does not authorize a full suite.

## 1. Obligation register

| Story acceptance obligation | Implementation slice(s) | Binding proof |
| --- | --- | --- |
| A file path and an HTTPS subscription both project events; a successful re-read updates fields and removes vanished events. | S1, S3 | `tests/unit/test_calendar_ingest.py::test_file_subscription_projects_then_honestly_removes_vanished_events`; `::test_https_subscription_projects_the_same_contract_without_auth_headers`; `::test_successful_refresh_updates_existing_occurrence_and_removes_absent_one`. |
| A hostile/malformed feed skips bad events with named receipts and never crashes boot or `GET /api/door`. | S2, S3, S4 | `tests/unit/test_calendar_parser.py::test_bad_event_is_skipped_with_deduplicated_kernel_receipt`; `::test_garbage_feed_preserves_last_known_good_projection`; `tests/unit/test_calendar_ingest_conductor.py::test_boot_and_tick_contain_fetch_and_parse_failures`; Door route/read-model regression in S4. |
| RRULE expansion is horizon-bounded and TZID-bearing events become the correct UTC instants. | S2 | `tests/unit/test_calendar_parser.py::test_tzid_event_projects_the_correct_utc_instants`; `::test_rrule_expands_only_the_fourteen_day_window_and_hard_occurrence_cap`; fixtures contain a real IANA TZID and a high-frequency hostile RRULE. |
| `GET /api/door` returns calendar events and scheduled recording fires in one ordered `upcoming` timeline. | S4 | Story-01 planned `tests/unit/test_door_read_model.py::test_upcoming_filters_and_orders_enabled_next_fire_records_with_calendar_ready_shape` is extended with real `calendar_events`; add `::test_upcoming_merges_calendar_events_and_scheduled_recordings_in_one_stable_order`; route proof `tests/unit/test_door_routes.py::test_get_door_returns_one_complete_aggregate_from_real_service`. |
| The subscription settings surface has a URL egress badge and a mic text input, proven in HS-144-04 shots. | S1 now; HS-144-04 glass hand-off | S1 makes `GET/PUT /api/settings` and `settings.get/update` carry/validate `calendar.subscription` plus a derived source/host/cadence fact. HS-144-04 adds the Meetings tile row with `StringGadget` (mic defaults true) and the one `EgressChip` only for HTTPS, then captures the required shots. |

## 2. Verified inventory and implementation anchors

### 2.1 Declarative schema and snapshot law

| Concern | Verified live anchor | Consequence |
| --- | --- | --- |
| Canonical DDL | `holdspeak/db/schema.py:7-11` says `SCHEMA_VERSION` is informational and shape changes come from `SCHEMA_SQL`; the final existing table is `scheduled_recordings` at `:3353-3375`. | Add `calendar_events` plus its chronology/identity indexes to `SCHEMA_SQL` immediately before its closing triple quote. Do **not** bump the informational version merely for this table. |
| Additive reconciler | `holdspeak/db/reconcile.py:1-7` promises CREATE/ALTER only, never DROP/DELETE; `:359-388` defines A1–A5; `:404-420` executes canonical DDL then adds missing columns; `:601-634` derives missing columns from an in-memory canonical schema. | A newly declared table self-creates on every open. Add a fresh/old-shape reconciliation test proving existing arbitrary rows survive and the table is created. No numbered migration and no data-destroying table rebuild. |
| Repository convention | `holdspeak/db/core.py:19-33` imports every repository module for `BaseRepository` registration; `:140-147` creates every registered `table` attribute. `holdspeak/db/scheduled_recordings.py:15-120` is the closest row-model/repository pattern. | Create `holdspeak/db/calendar_events.py`, import it from `core.py`, optionally re-export its model/repository in `holdspeak/db/__init__.py`, and use `db.calendar_events` rather than raw repeat SQL from Door/conductor code. |
| Snapshot guard | `tests/unit/test_db.py:1731-1758` creates a fresh `Database`, normalizes whitespace with its effectively no-op regex, and byte-compares `tests/fixtures/db_schema_canonical.txt`. | Regenerate the committed snapshot in the same change, then run `TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot`. There is no helper script: reuse the test's exact fresh-DB/select/whitespace-normalization procedure, writing only `tests/fixtures/db_schema_canonical.txt`; inspect its diff so only the new table/index lines change. |

**Recommended projection DDL contract** (exact spelling may follow surrounding formatting):

```sql
CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    location TEXT,
    meeting_url TEXT,
    last_seen_at REAL NOT NULL,
    subscription_revision TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_events_source_uid_start
ON calendar_events(subscription_revision, uid, starts_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_upcoming
ON calendar_events(starts_at, id);
```

`subscription_revision` is the stable SHA-256 fingerprint of the normalized configured source (not the global Settings `_revision`, which changes for unrelated dials). `id` is a stable `ce_` hash of that fingerprint, UID, and occurrence start. In one write transaction, a successful refresh removes rows from an old source revision, upserts desired current-revision rows, then deletes current-revision rows not marked with this refresh's `last_seen_at`. This gives both source-change replacement and vanished-event honesty without a second state table.

### 2.2 Settings storage and transport

| Concern | Verified live anchor | Consequence |
| --- | --- | --- |
| Config owns `config.json` | `holdspeak/config/core.py:1-5`, `:183-203`, `:205-293`. Config sections are typed dataclasses; `load()` explicitly constructs each known section at `:239-266`; `save()` serializes `asdict` at `:283-293`. | Add a small `CalendarConfig` (default `subscription: str = ""`) in the appropriate config-domain module, import it in `core.py`, add `calendar` to `Config`, and explicitly `_coerce` it in `Config.load()`. This is the one persisted subscription field, not a DB settings table. |
| Generic partial update | `SettingsService.update_settings()` checks optimistic revision at `holdspeak/services/settings_service.py:236-285`; `_update()` deep-merges at `:309-315`, builds its explicit config replacement at `:892-905`, and returns redacted settings at `:936`. | Validate/normalize the `calendar` patch alongside the existing typed sections, construct `CalendarConfig` in `replace(...)`, and keep the `_revision` behavior unchanged. Validate empty (disabled), file-path, or HTTPS URL at save time; reject http/other schemes, userinfo, and malformed URLs with 400 instead of leaving a later conductor surprise. |
| HTTP transport | `holdspeak/web/routes/system/settings.py:30-71` exposes the one GET and PUT and maps `ValidationError` to 400, conflict to 409. | No calendar-specific HTTP route: the generic `GET/PUT /api/settings` is the lawful surface. It already reaches `SettingsService` through `WebContext`. |
| MCP transport | `holdspeak/mcp/families/settings.py:11-47` declares `settings.get` and partial `settings.update`; `:51-74` calls the same `SettingsService`. | The field automatically travels through both transports. Update the `settings.update` EGRESS description only enough to state that an HTTPS calendar source is fetched from the hub with no credential/header facility; do not create a calendar MCP family/tool. Preserve the current tools/list catalogue membership. |
| Phase-139 tile law | Phase 139 close says the room is seven action-named tiles at `current-phase-status.md:117-124`; `web/src/pages/cores/settingsPrefs.tsx:28-46` maps source keys to tiles; `SettingsCore.tsx:747-854` is the authored Meetings tile. | The future glass belongs under **Meetings**, with `"calendar"` added to that tile's key ownership—not System and not an eighth tile. HS-144-02 does not touch it; HS-144-04 owns the row, its single egress chip, and its mic/shot proofs. |
| Mic law | `web/src/desk/surface/gadgets.tsx:215-239` sets `StringGadget` `mic = true` and documents every ordinary text well's speak-to-fill mic. | HS-144-04 must use `StringGadget` without `mic={false}` for the subscription field. No bespoke input or text-entry exception. |

### 2.3 Tick, receipts, egress, and Door composition

| Concern | Verified live anchor | Consequence |
| --- | --- | --- |
| Scheduled-recording tick precedent | `holdspeak/scheduled_recording_conductor.py:77-143` supplies injectable dependencies and start/stop; `:157-168` performs boot reconciliation, catches tick exceptions, and waits a bounded interval; `:338-367` is the clock-injected tick. | Use a **sibling** `holdspeak/calendar_ingest_conductor.py`, not another branch in the recording state machine. It has a narrow injected `clock`, `db_factory`, `source_reader`, and 900-second tick interval. It refreshes immediately after boot and re-reads `Config.load().calendar` every tick, so a settings change needs no server restart. |
| Hub lifecycle | `holdspeak/web_server.py:932-997` starts background work, including scheduled recordings at `:972-995`; its shutdown cancellation list is `:999-1018`. | Start the calendar sibling once in startup and explicitly stop it in shutdown. **Anchor surprise:** this shutdown block does not call `stop_scheduled_recording_conductor()` despite its global daemon helper. Do not copy that omission; decide separately whether the existing scheduled conductor needs a narrow lifecycle repair, rather than silently expanding Story 02. |
| Scheduled background receipt | `ScheduledRecordingConductor._write_receipt()` directly inserts `kernel_operations` and `kernel_receipts` at `holdspeak/scheduled_recording_conductor.py:176-227`; misses/refusals invoke it at `:293-334` and `:451-467`. | Calendar malformed-event/fetch-failure receipts use these existing two tables and state/outcome vocabulary—no new receipt projection/table. Use a deterministic idempotency key to avoid a permanent bad event producing a receipt every 15 minutes. |
| Rails receipt/frozen-boundary precedent | `holdspeak/rails_observer.py:322-349` records a pre-route refusal; `:399-430` closes the parent with a receipt and retains the egress derived from frozen route entries. `web_server.py:1121-1215` shows its re-read/catch-every-tick loop. | A plain configured ICS URL has no inference route legs to claim. Its display truth must derive from the validated subscription itself: `source_kind`, URL host, and fixed cadence. Do not borrow a model boundary/frozen-route badge for a non-model fetch. |
| Existing visual badge | `EgressChip` is the sole chip species at `web/src/desk/surface/gadgets.tsx:714-758`; it takes an explicit label/title/scope. Existing model screens derive cloud chips from their projected boundary, e.g. `AssignmentModelChooser.tsx:6-7,63`. | `redacted_settings()` should add a derived, nonpersisted `_calendar_subscription` fact such as `{kind: "https", host: "calendar.example", refresh_seconds: 900, egress: true}` (or `{kind: "file", egress: false}`). HS-144-04 renders exactly one URL-only `EgressChip` from that fact, e.g. `FETCHES CALENDAR.EXAMPLE · 15 MIN`; title may say it fetches that URL without credentials/headers. It never appears for a file path. |
| Door contract | Story-01 plan §3, especially `assets/story-01-door-read-model-plan.md:120-138`, fixes `upcoming` as a future UTC ordered timeline and reserves `source: "calendar_event"`, nullable location/URL fields, and server-side counts. | Extend the injected Door reader with `CalendarEventRepository.list_upcoming(now)`. It maps rows directly to the reserved shape and merges before the one established sort. Do not query `calendar_events` from a route or client, and do not alter board/count shape. |

## 3. [ORCH-CALL] — parser package and recurrence implementation

**[ORCH-CALL] Recommend a visible core dependency on `icalendar>=7.3.0`, and use its resolved `python-dateutil` transitively for `dateutil.rrule.rrulestr`; do not write a stdlib or vendored RFC parser.**

### Dependency facts actually checked

- `pyproject.toml:40-61` has a deliberately small core dependency list and contains neither `icalendar` nor `python-dateutil`.
- `uv.lock` has neither package and an isolated `uv run --python 3.13.11` import probe found both unavailable.
- `HOME="$(mktemp -d)" uv tree --python 3.13.11 --depth 2` likewise had no calendar/dateutil package in this project's resolved tree.
- A no-install resolver probe for `icalendar>=6.0` selected `icalendar==7.3.0`, `python-dateutil==2.9.0.post0`, and `tzdata==2026.3`. Inspection of the selected distribution metadata confirms `icalendar 7.3.0` requires `python-dateutil` and `tzdata>=2025.3` (and `typing-extensions` only below Python 3.13). The project supports 3.10–3.13, so the lock must be reviewed on all declared markers rather than treating the local 3.13 result as the whole package contract.
- Inspection of `icalendar 7.3.0` exposed parsing/value/recurrence-property support but **no occurrence-expansion API**. Adding it solves RFC folding, parameter parsing, escaped property values, `TZID`, and structured component parsing; it does not magically solve recurrence expansion.

### Why this is the least dishonest choice

- **Stdlib-only:** `datetime`, `zoneinfo`, and `urllib` are adequate for conversion/fetch, but there is no stdlib iCalendar parser or RRULE engine. Correctly implementing line folding, escaped text, property parameters, TZID, RRULE frequencies/BY* rules, `UNTIL`/`COUNT`, exclusions, and hostile input is the actual hard work—not a small parser helper. Reject.
- **Vendored minimal parser:** would still need a recurrence engine and would become a private, weak RFC subset precisely where the charter calls for real-world/timezone fixtures. Reject.
- **`python-dateutil` alone:** it supplies the essential recurrence engine, but a hand-written ICS unfolder/property parser would still need to carry the untrusted-format burden. It is a useful middle layer, but not enough by itself.
- **`icalendar` + its transitive `python-dateutil`:** a visible three-package lock expansion buys a maintained parser and UTC/TZID values, while a small, tested adapter retains the deliberately narrow projection scope. Recommend.

### Required narrow adapter behavior

Create `holdspeak/calendar_ingest.py` as a pure, clock-injected parser/projection module. It accepts bounded bytes plus `now`, returns valid projected occurrence candidates and structured skip records, and never opens a file, URL, DB, or web context.

1. Parse `VCALENDAR`/`VEVENT` through `icalendar.Calendar.from_ical`; convert decoded DTSTART/DTEND with `zoneinfo`/calendar-provided TZID to UTC ISO strings.
2. A non-recurring timed VEVENT produces one candidate if its start is in the 14-day future horizon. Missing/invalid UID, DTSTART, end/duration, or unresolvable TZID becomes one `calendar_event_skipped` record; it never raises beyond the module boundary.
3. For a master RRULE, call `dateutil.rrule.rrulestr(..., dtstart=dtstart)` and ask only for occurrences in `[now, now + 14 days)`. Enforce the 128-per-master and 4,000-feed projection caps regardless of RRULE frequency. Preserve master duration for each occurrence. Apply decoded `EXDATE` values before projecting; honor explicit `RDATE` only if it is a decoded date-time of the same temporal kind. A malformed recurrence property skips that master with a named receipt rather than degrading to an untruthful one-off.
4. This first slice deliberately does **not** pretend that arbitrary `RECURRENCE-ID` override/cancellation semantics are solved by `icalendar`. The builder must either implement UID-grouped override replacement plus tests before claiming it, or skip those override components with `calendar_event_skipped_unsupported_recurrence_override`. The latter is honest and within the charter; silently showing both master and override is prohibited.
5. Date-only/all-day VEVENTs are likewise skipped with `calendar_event_skipped_unsupported_date_only` rather than inventing a meeting instant. `LOCATION` is retained; only a parsed `URL` property becomes `meeting_url` (no description scraping).

**Disposition recommended:** accept. It is the smallest dependency addition that actually meets folding/TZID/RRULE obligations while honestly bounding the remaining recurrence surface.

## 4. Ordered implementation slices

### S1 — Persist the one-source settings and the additive calendar projection

**Create**

- `holdspeak/db/calendar_events.py`
- `tests/unit/test_calendar_events_repository.py`
- `tests/integration/test_calendar_settings.py`

**Edit**

- `pyproject.toml` and `uv.lock` — add the visible `icalendar` dependency and lock its `python-dateutil`/`tzdata` closure.
- `holdspeak/db/schema.py` — add `calendar_events` and the two indexes in §2.1.
- `holdspeak/db/core.py`, `holdspeak/db/__init__.py` — register/export the repository using the existing automatic registry convention.
- `holdspeak/config/integrations.py` and `holdspeak/config/core.py` — typed `CalendarConfig`, `Config` field, explicit load coercion.
- `holdspeak/services/settings_service.py` — validation, typed construction, and derived `_calendar_subscription` fact.
- `holdspeak/mcp/families/settings.py` — concise honest URL-egress wording only.
- `tests/fixtures/db_schema_canonical.txt` — regenerated, never hand-edited.

**Implementation details**

1. Make the repository expose only the aggregate's needs: `replace_projection(subscription_revision, events, seen_at)` (one transaction), `list_upcoming(now_iso)`, and a small test/read helper. A caller cannot incrementally patch calendar rows, because the source is authoritative.
2. Store no raw ICS body, credentials, headers, email/attendee data, or arbitrary DESCRIPTION; only the story's required projected fields.
3. `calendar.subscription` normalizes whitespace. Empty means disabled/file-or-URL absent. An HTTPS URL must have host, no username/password, no fragment, and no nonstandard scheme; all non-URL text is treated as a file path. The source revision is the hash of the normalized accepted source, not a user-writable revision dial.
4. `redacted_settings()` calculates (does not persist) the source summary. It names the URL host/cadence but has no title/body or credential material. File summaries report local/no egress.

**Named proofs**

- `tests/unit/test_calendar_events_repository.py::test_replace_projection_upserts_and_removes_vanished_rows_atomically`
- `tests/unit/test_calendar_events_repository.py::test_list_upcoming_orders_future_rows_without_raw_sql_in_consumers`
- `tests/integration/test_calendar_settings.py::test_empty_file_and_https_calendar_subscription_round_trip_through_http_and_mcp_service`
- `tests/integration/test_calendar_settings.py::test_calendar_subscription_rejects_http_userinfo_and_malformed_https`
- `tests/integration/test_calendar_settings.py::test_settings_projection_derives_url_host_cadence_and_file_no_egress`
- `tests/unit/test_reconcile.py::test_reconcile_adds_calendar_events_to_old_shape_without_touching_rows`
- `tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_calendar_events_repository.py \
  tests/integration/test_calendar_settings.py \
  tests/unit/test_reconcile.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot \
  tests/unit/test_mcp_phase133_settings.py --tb=short
```

### S2 — Make a pure bounded ICS parser, with hostile fixtures before I/O

**Create**

- `holdspeak/calendar_ingest.py`
- `tests/unit/test_calendar_parser.py`
- `tests/fixtures/calendar/basic.ics`
- `tests/fixtures/calendar/folded-url.ics`
- `tests/fixtures/calendar/tzid-new-york.ics`
- `tests/fixtures/calendar/rrule-bound.ics`
- `tests/fixtures/calendar/mixed-bad-event.ics`
- `tests/fixtures/calendar/garbage-bytes.ics`

**Implementation details**

1. Keep parser code transport- and DB-free. `parse_calendar_bytes(raw, *, now, subscription_revision) -> ParseResult` is the one untrusted-input boundary, with typed valid candidates and typed `{event_ref, reason}` skips.
2. Decode raw byte failures, malformed calendars, component errors, invalid property values, unknown TZID, and recurrence errors into data; let only programmer mistakes escape tests. A feed-level failure is distinguishable from a per-VEVENT skip so S3 can retain prior projection only in the former case.
3. Normalize all correct temporal values to `YYYY-MM-DDTHH:MM:SSZ`; source strings never flow to the Door directly. Use the fixed injected `now` so DST and horizon tests cannot depend on wall-clock date.
4. Enforce the byte/event/occurrence/projection limits in the parser interface, not only in a conductor caller. A cap produces a structured named skip, not a truncated silent list.

**Hostile-fixture inventory**

| Fixture | What it proves |
| --- | --- |
| `basic.ics` | Ordinary DTSTART/DTEND, UID, SUMMARY, LOCATION, and URL map to the exact projection fields. |
| `folded-url.ics` | RFC folded content line/escaped text reassembles correctly; a URL property remains one value. |
| `tzid-new-york.ics` | `TZID=America/New_York` during DST becomes the precise UTC instant, not server-local time. |
| `rrule-bound.ics` | An RRULE with a large/infinite count returns only future occurrences inside 14 days and stops at the occurrence cap. |
| `mixed-bad-event.ics` | One good VEVENT survives while a sibling lacking a decodable DTSTART/DTEND gets the specific skip reason. |
| `garbage-bytes.ics` | Invalid UTF-8/invalid ICS is a feed-level parse failure, not a process exception. |
| dynamic huge feed | Test creates `MAX_FEED_BYTES + 1` bytes through the reader seam; parser/I/O rejects before component construction. |
| dynamic recurrence edge rows | `SECONDLY` RRULE, unresolved TZID, date-only event, malformed RRULE, EXDATE, and `RECURRENCE-ID` override each prove an explicit bounded disposition. |

**Named proofs**

- `tests/unit/test_calendar_parser.py::test_folded_ics_and_url_property_project_without_a_hand_rolled_parser`
- `tests/unit/test_calendar_parser.py::test_tzid_event_projects_the_correct_utc_instants`
- `tests/unit/test_calendar_parser.py::test_rrule_expands_only_the_fourteen_day_window_and_hard_occurrence_cap`
- `tests/unit/test_calendar_parser.py::test_exdate_removes_a_recurring_occurrence`
- `tests/unit/test_calendar_parser.py::test_malformed_event_becomes_a_named_skip_while_good_sibling_survives`
- `tests/unit/test_calendar_parser.py::test_garbage_bytes_and_huge_feed_are_bounded_feed_failures`
- `tests/unit/test_calendar_parser.py::test_date_only_and_recurrence_override_are_explicitly_skipped_not_misrepresented`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_calendar_parser.py \
  tests/unit/test_calendar_events_repository.py --tb=short
```

### S3 — Refresh safely on boot and a bounded cadence, retaining a good projection on failure

**Create**

- `holdspeak/calendar_ingest_conductor.py`
- `tests/unit/test_calendar_ingest.py`
- `tests/unit/test_calendar_ingest_conductor.py`

**Edit**

- `holdspeak/web_server.py` — start exactly one calendar conductor in startup; stop it explicitly in shutdown.

**Implementation details**

1. `CalendarIngestConductor` follows the scheduled conductor's injection/lifecycle shape, but owns no recording state, mic floor, cron, broadcast, or route-plan semantics. Its boot sequence performs one refresh before waiting; every later tick reloads `Config.load().calendar` and no-ops when subscription is empty.
2. `CalendarSourceReader` determines source kind from the already validated config. File reads use the same byte cap. HTTPS uses a dedicated no-redirect opener, 10-second timeout, 5 MiB maximum, and no added headers—especially no `Authorization`, cookie, or stored token. A redirect is a named fetch failure, not a quiet request to an unbadged host.
3. On a successful parsed feed (including a valid zero-event feed), call repository replacement atomically. On reader failure or feed-level parser failure, retain prior rows. On individual bad events, write good candidates and receipts for only the skips.
4. Mint receipts through existing `kernel_operations`/`kernel_receipts`, modeled on `ScheduledRecordingConductor._write_receipt`. For a per-event invalidity use terminal `state="refused"`, `outcome="calendar_event_skipped"`, and a non-content result ref like `calendar-event:<uid-hash>:invalid_dtstart`. Use stable `(source revision, UID/hash, reason)` idempotency so the same persisted bad event writes one receipt, not one per tick. For a source/read/feed failure use `state="failed"`, `outcome="calendar_refresh_failed"`, a source-revision/error-class result ref, and preserve the last known good rows. These are existing receipt vocabulary/records, not a calendar receipt subsystem.

**Named proofs**

- `tests/unit/test_calendar_ingest.py::test_file_subscription_projects_then_honestly_removes_vanished_events`
- `tests/unit/test_calendar_ingest.py::test_https_subscription_projects_the_same_contract_without_auth_headers`
- `tests/unit/test_calendar_ingest.py::test_reader_rejects_redirect_timeout_and_oversize_before_projection`
- `tests/unit/test_calendar_ingest.py::test_bad_event_is_skipped_with_deduplicated_kernel_receipt`
- `tests/unit/test_calendar_ingest.py::test_feed_failure_retains_last_known_good_projection_and_receipts_once`
- `tests/unit/test_calendar_ingest_conductor.py::test_boot_refreshes_once_and_periodic_tick_rereads_current_subscription`
- `tests/unit/test_calendar_ingest_conductor.py::test_boot_and_tick_contain_fetch_and_parse_failures`
- `tests/unit/test_calendar_ingest_conductor.py::test_stop_joins_the_calendar_thread_and_prevents_later_refresh`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_calendar_ingest.py \
  tests/unit/test_calendar_ingest_conductor.py \
  tests/unit/test_scheduled_recording_conductor.py \
  tests/unit/test_rails_observer.py --tb=short
```

### S4 — Join the established Door aggregate without moving its shape

**Create:** none expected beyond the S1–S3 proof files.

**Edit**

- `holdspeak/services/door_service.py` — the Story-01-owned aggregate gains an injected calendar repository/read authority and maps its projections into the already reserved timeline row.
- `holdspeak/web/context.py` and `holdspeak/web_server.py` only if Story 01's final composition needs the new injected dependency; coordinate with the Story-01 implementer rather than treating a dirty partial file as canon.
- `tests/unit/test_door_read_model.py`
- `tests/unit/test_door_routes.py`

**Implementation details**

1. Use the exact Story-01 plan §3 wire contract. Calendar's nullable `location`/`meeting_url` must remain present even when absent. `state: "scheduled"` is a truthful calendar scheduled state—not an invented recording lifecycle.
2. The Door service, not `GET /api/door`, calls the repository once alongside its already injected scheduled-recording reader. Merge the two lists before its one deterministic sort and count calculation.
3. Use fresh real `Database`, real calendar repository, real scheduled-recording repository, and real Door service in the tests. No fake timeline map or client merge. The existing transport parity test naturally receives calendar rows once both HTTP/MCP compose the same Door service.

**Named proofs**

- `tests/unit/test_door_read_model.py::test_upcoming_merges_calendar_events_and_scheduled_recordings_in_one_stable_order`
- `tests/unit/test_door_read_model.py::test_calendar_timeline_rows_preserve_the_reserved_nullable_fields_and_do_not_change_counts_shape`
- `tests/unit/test_door_routes.py::test_get_door_returns_one_complete_aggregate_from_real_service`
- `tests/unit/test_door_transport_parity.py::test_door_get_http_and_mcp_parity_on_fresh_production_compositions`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_calendar_parser.py \
  tests/unit/test_calendar_events_repository.py \
  tests/unit/test_calendar_ingest.py \
  tests/unit/test_calendar_ingest_conductor.py \
  tests/unit/test_door_read_model.py \
  tests/unit/test_door_routes.py \
  tests/unit/test_door_transport_parity.py --tb=short
```

### S5 — Regenerate truthful schema/inventory facts and run the bounded cross-net

**Edit only after S1–S4 focused behavior is green and its output has been read**

- `tests/fixtures/db_schema_canonical.txt` — test-derived snapshot regeneration.
- No generated HTTP/API manifest is expected: Story 02 does not add a route. If implementation accidentally adds one, stop and either remove it or explicitly reopen the story boundary.

**Proof sequence**

1. Run S1's old-shape reconcile and fresh snapshot test after regenerating the snapshot through the test's exact normalized `sqlite_master` procedure.
2. Confirm the schema diff is only the table/index addition; `SCHEMA_VERSION` is not a gate and needs no ceremonial bump.
3. Run the cross-cutting net below. Read output before any status flip/evidence capture.

## 5. Further [ORCH-CALL]s and recommended dispositions

1. **[ORCH-CALL] Settings home — recommend one `calendar` config section, displayed under the existing Meetings tile in HS-144-04; backend settings contract in HS-144-02, no `web/src` edits here.** Phase 139 explicitly protects the seven action-named tile rule, and `SettingsCore`'s authored Meetings module is the lawful owner of a future-meeting source. This keeps the source available to the hub now but leaves one coherent visual/shot story to HS-144-04. **Recommend accept.**

2. **[ORCH-CALL] Fetch envelope — recommend HTTPS-only, no userinfo/headers/cookies/redirects, 10-second timeout, and 5 MiB maximum bytes for both URL and file input.** The no-redirect rule is important: otherwise a badge naming `calendar.example` could quietly fetch a different host. File input gets the same size cap; rejection leaves known-good projection intact. **Recommend accept.**

3. **[ORCH-CALL] Cadence — recommend refresh once synchronously at conductor boot and every 900 seconds (15 minutes) thereafter, with Config re-read on each tick.** It is frequent enough for a Door's next meeting without turning an ICS URL into a minute-by-minute poller. A nonempty subscription is the user's bounded approval of this exact source/cadence; empty disables future reads. Do not add a manual refresh verb or live-change push in this story. **Recommend accept.**

4. **[ORCH-CALL] Skipped-event receipt — recommend an existing kernel receipt with `state=refused`, `outcome=calendar_event_skipped`, and content-free result ref `calendar-event:<uid-hash>:<reason>`, idempotent per source revision/event/reason.** This matches scheduled recording's terminal outcome vocabulary and the ledger-not-gate policy. A feed/transport failure is separately `failed/calendar_refresh_failed` and preserves old projection; neither is a new receipts UI. **Recommend accept.**

5. **[ORCH-CALL] Egress truth — recommend a derived settings fact from the validated URL host plus `refresh_seconds`, rendered as exactly one URL-only existing `EgressChip` in HS-144-04, rather than a Phase-143 model-route boundary.** ICS is a configured ordinary HTTPS fetch, not inference; route-leg provenance would be fabricated. The app must reject redirects so this derivation remains true at execution. **Recommend accept.**

6. **[ORCH-CALL] Conductor ownership — recommend a sibling `CalendarIngestConductor`, explicitly stopped by the hub shutdown hook, not a scheduled-recording conditional.** The two systems share only clock/lifecycle mechanics; sharing the conductor would import recording state/mic/cron concerns and obscure calendar failure behavior. **Recommend accept.**

## 6. Cross-cutting net

### Existing settings route/service/MCP consumers

These existing files directly call `/api/settings`, construct `SettingsService`, or lock its source/mutable tool surface; all remain in the final focused settings net because adding a new Config section touches full-document merge, redaction, and revision behavior:

- `tests/integration/test_web_dictation_settings_api.py`
- `tests/integration/test_settings_version_guard.py`
- `tests/integration/test_settings_placement_provenance.py`
- `tests/integration/test_settings_language_ui.py`
- `tests/integration/test_settings_spoken_symbols.py`
- `tests/integration/test_settings_wake_word.py`
- `tests/integration/test_web_settings_presence.py`
- `tests/integration/test_presence_mascot_gate.py`
- `tests/integration/test_web_settings_secrets.py`
- `tests/integration/test_web_slack_export.py`
- `tests/integration/test_web_server.py`
- `tests/unit/test_dictation_preview.py`
- `tests/unit/test_dictation_profile_resolution.py`
- `tests/unit/test_intel_profile_resolution.py`
- `tests/unit/test_mcp_phase133_settings.py`
- `tests/unit/test_mcp_tools.py`
- `tests/unit/test_rails_observer.py` (its marker-gated settings authority test)
- `tests/unit/test_phase143_routing_authority_census.py`

Static/glass consumers are intentionally not credited as Story-02 UI proof, but must stay truthful when HS-144-04 adds the field: `tests/integration/test_web_settings_page.py`, `tests/integration/test_web_flagship_audit.py`, `tests/integration/test_web_commands_board.py`, `tests/integration/test_history_slack_surfaces.py`, `tests/integration/test_web_presence_onboarding.py`, and `tests/e2e/test_hs141_models_setup_glass.py`.

### Schema, cadence, receipt, and Door authorities

- `tests/unit/test_reconcile.py` — fresh/old-shape, no-delete, no-version-gate behavior; add the calendar old-shape case.
- `tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` — byte-for-byte DDL snapshot.
- `tests/unit/test_scheduled_recording_conductor.py` — tick/dedupe/boot/restart timing and direct kernel-receipt precedent; especially `test_single_fire_across_multiple_ticks`, `test_fire_creates_kernel_receipt`, `test_restart_*`, and bounded catch-up cases.
- `tests/unit/test_rails_observer.py` — background tick containment, receipt closing, and frozen egress truth precedent; especially `test_routed_rails_persists_one_frozen_egress_badge_for_local_and_cloud`.
- Story-01 planned `tests/unit/test_door_read_model.py`, `tests/unit/test_door_routes.py`, `tests/unit/test_door_mcp.py`, and `tests/unit/test_door_transport_parity.py` — calendar join must not make HTTP/MCP or aggregate shape diverge.
- `tests/unit/test_scheduled_recording_routes.py` and `tests/unit/test_scheduled_recording_mcp.py` — schedule timeline source and its existing readers remain authoritative.

### Bounded final commands

```bash
# Calendar behavior + Door join.
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_calendar_parser.py \
  tests/unit/test_calendar_events_repository.py \
  tests/unit/test_calendar_ingest.py \
  tests/unit/test_calendar_ingest_conductor.py \
  tests/unit/test_door_read_model.py \
  tests/unit/test_door_routes.py \
  tests/unit/test_door_mcp.py \
  tests/unit/test_door_transport_parity.py \
  tests/unit/test_scheduled_recording_conductor.py \
  tests/unit/test_scheduled_recording_routes.py \
  tests/unit/test_scheduled_recording_mcp.py --tb=short

# Settings/schema/receipt net; no full suite.
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_reconcile.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot \
  tests/integration/test_calendar_settings.py \
  tests/integration/test_web_dictation_settings_api.py \
  tests/integration/test_settings_version_guard.py \
  tests/integration/test_settings_placement_provenance.py \
  tests/integration/test_settings_language_ui.py \
  tests/integration/test_settings_spoken_symbols.py \
  tests/integration/test_settings_wake_word.py \
  tests/integration/test_web_settings_presence.py \
  tests/integration/test_presence_mascot_gate.py \
  tests/integration/test_web_settings_secrets.py \
  tests/integration/test_web_slack_export.py \
  tests/integration/test_web_server.py \
  tests/unit/test_mcp_phase133_settings.py \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_rails_observer.py \
  tests/unit/test_phase143_routing_authority_census.py --tb=short
```

## 7. Stop signals

| Stop signal | Required correction |
| --- | --- |
| Parser code hand-splits ICS lines or reimplements RRULE. | Stop; use `icalendar` parser plus `dateutil.rrule`, with tests demonstrating the dependency's actual role. |
| One malformed VEVENT throws through a tick, boot, or Door read. | Stop; turn it into a structured skip plus named existing-kernel receipt. |
| A failed URL/file parse empties a previously good projection. | Stop; commit replacement only after feed-level parse success. |
| A successful zero-event feed leaves stale rows. | Stop; it must atomically clear the current projection. |
| URL follows a redirect or sends/accepts credentials. | Stop; reject redirect/userinfo and use no header/cookie/token facility. |
| Door has a second timeline serializer or a client-side calendar merge. | Stop; inject repository into the Story-01 service and use its fixed timeline contract. |
| The source becomes an eighth Settings tile, System RAW debris, or Story-02 `web/src` change. | Stop; `calendar` belongs in the existing Meetings tile and HS-144-04 owns glass. |
| A recurrent hostile feed can emit unlimited rows/receipts. | Stop; enforce bytes/raw events/occurrences/projected rows, plus receipt idempotency. |
| Schema change lacks the old-shape reconcile proof or canonical snapshot update. | Stop; reconcile and fresh-snapshot tests are part of the same slice, not closeout cleanup. |

## Orchestrator dispositions (ruled 2026-08-27)

1. **Parser: ACCEPTED.** `icalendar>=7.3.0` enters `pyproject.toml`
   visibly (transitive `python-dateutil` + `tzdata` accepted);
   occurrence expansion via `dateutil.rrule.rrulestr` under the plan's
   hard horizon/count caps. Stdlib-only and vendoring are rejected as
   recommended — hand-rolled folding/TZID/RRULE is a bug farm, and the
   product is not released enough to fear a dependency.
2. **Glass boundary: ACCEPTED.** HS-144-04 owns all glass; this story
   is backend + settings truth only.
3. **Fetch posture: ACCEPTED.** HTTPS-only, no redirects, no auth
   headers, 10s timeout, 5 MiB cap. A redirecting feed refuses with a
   named receipt that shows the redirect target — honest egress beats
   convenience; the owner can paste the final URL.
4. **Cadence: ACCEPTED.** Boot + 15-minute refresh.
5. **Receipts: ACCEPTED.** Deduplicated `calendar_event_skipped`
   refusal receipts in the existing vocabulary.
6. **The shutdown surprise (scheduled-recording conductor's stop
   helper not called on shutdown): the NEW calendar conductor gets
   explicit lawful shutdown as the plan requires. The pre-existing
   scheduled-recording gap may be repaired IN this story ONLY if the
   fix is the one-line stop call in the existing shutdown handler with
   an existing-pattern test; anything larger is a LEDGER NOTE for the
   phase close.** Fix-when-cheaper-than-ledgering, bounded.

Build order: after HS-144-01 closes (single-writer tree; this story's
S1 regenerates the schema snapshot and cannot overlap story 01's
inventory regens).
