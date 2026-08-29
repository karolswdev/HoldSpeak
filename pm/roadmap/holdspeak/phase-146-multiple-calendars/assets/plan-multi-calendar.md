# Phase 146 plan — Multiple Calendars (opus plan worker, 2026-08-28)

Read-only design plan against `feat/hs146-multi-calendar` (= main
`4c08a613`, Phases 144+145 included). All seven [ORCH-CALL]s were
ruled by the orchestrator the same day; dispositions live in the
charter's settled design. Anchors verified at plan time.

## Anchored current architecture (single-calendar)

| Layer | Anchor | Shape |
|---|---|---|
| Config | `holdspeak/config/integrations.py:17-20` | `CalendarConfig.subscription: str`; `validate_calendar_subscription` :26-63; `calendar_subscription_revision` :66-69; `calendar_subscription_summary` :72-103 |
| Config persistence | `holdspeak/config/core.py:210, :273-274, :299` | dataclass field; `_coerce` on load; `json.dump(asdict)` on save |
| Parser | `holdspeak/calendar_ingest.py:66-133` | pure, source-agnostic; `_projection_id(subscription_revision, uid, starts_at)` :381-385 |
| Conductor | `holdspeak/calendar_ingest_conductor.py:132-218` | ONE source per tick (:173); `replace_projection` on success (:209-211) |
| DB | `holdspeak/db/schema.py:3378-3392`; `holdspeak/db/calendar_events.py:58-107` | `replace_projection` does `DELETE FROM calendar_events` (ALL rows, :80) then inserts; unique index `(subscription_revision, uid, starts_at)` |
| Door | `holdspeak/services/door_service.py:60-68` (`_calendar_configured`), :167-178 (`_upcoming`), :197-209 (`_calendar_event_item`) | MCP twin `holdspeak/mcp/families/door.py:29-46` |
| Settings service | `holdspeak/services/settings_service.py:127-129` (`_calendar_subscription` fact), :659 (strip on write), :902-912 (validation) | wire `{calendar: {subscription}}` |
| Settings UI | `web/src/pages/cores/SettingsCore.tsx:766-785` (one StringGadget + EgressChip), :119-133 (`calendarEgressChipProps`); types `core-types.ts:94-99` | GadgetTable idiom proven at :621-665 (spoken symbols) |
| Rail | `web/src/desk/chair/lanes/DoorBoardLane.tsx:39-49` (`DoorUpcomingItem`), :237-282 | no provenance field today |
| Guards/walks | `scripts/mcp_walk.py:263-264` (door keys — UNCHANGED by this phase); `scripts/door_walk_hs144.py:714-753` (leg 5 fills the single "Calendar subscription" textbox) | |
| Single-subscription seeds | `tests/e2e/test_hs144_door_glass.py:222-224`; `tests/e2e/test_hs145_door_polish_glass.py:370`; `door_walk_hs144.py:751` | all seed `{"calendar": {"subscription": str}}` |
| "One subscription" prose | `docs/USER_GUIDE.md:486-497`; `docs/SECURITY.md:355`; `holdspeak/mcp/families/settings.py:28`; docstrings in `integrations.py:18`, `calendar_ingest_conductor.py:1`, `db/calendar_events.py:53` | six sites |

## Settled decisions (as ruled)

1. **Config shape:** `CalendarSource {id (uuid4, minted on add), label,
   url, enabled}`; `CalendarConfig.sources: list[CalendarSource]`.
   Migration in `Config.load()`: old `calendar.subscription` →
   `sources=[{id: uuid4, label: "", url: old, enabled: True}]`,
   consumed exactly once, old key dropped on next save. No compat
   alias. `validate_calendar_subscription` stays per-URL;
   `calendar_source_revision(source_id, url)` replaces the revision
   fn (source id enters the hash → per-source projection namespace).
2. **Conductor:** iterate enabled sources per tick, each with its own
   fetch/parse/replace; `replace_projection(source_id, revision,
   events, seen_at)` deletes only `WHERE source_id = ?` — a failed
   source leaves every other source's last-good rows intact
   (per-source last-good law). End-of-tick orphan cleanup:
   `DELETE ... WHERE source_id NOT IN (<enabled ids>)` — removed or
   disabled sources disappear from the rail; re-enabling refetches.
   New additive columns `source_id TEXT NOT NULL DEFAULT ''`,
   `source_label TEXT NOT NULL DEFAULT ''`; unique index rescoped to
   `(source_id, uid, starts_at)`.
3. **Rail provenance:** a mono label chip per EVENT row, rendered
   ONLY when >1 distinct source is configured; text = source label,
   falling back to hostname, then "LOCAL". Conductor stamps
   `source_label` at projection time; `_calendar_event_item` projects
   it; `DoorUpcomingItem.source_label?: string`.
4. **`calendar_configured`:** true iff ≥1 ENABLED source passes
   validation. (Confirmed sole consumers: door_service,
   DoorBoardLane, tests.)
5. **Settings surface (the JOY criterion):** the single field becomes
   a `GadgetTable` list editor — per row: label StringGadget (mic),
   url StringGadget (mic), enabled CheckGadget; add mints
   `{id: uuid4, label: "", url: "", enabled: true}`; delete verb
   "REMOVE?" per the house idiom; egress truth = one EgressChip per
   HTTPS-enabled source (or the no-egress fact). Wire:
   `{calendar: {sources: [...]}}`; derived fact `_calendar_sources:
   [{id, kind, host, refresh_seconds, egress, label}]` (replaces
   `_calendar_subscription`, stripped on write the same way).
6. **Dedupe: NONE.** ICS UIDs are per-feed, not global; two copies
   with provenance beat a wrong merge; single-user reality.
7. **Guards:** `/api/settings` path unchanged → no api-surface regen
   (gen_api_surface hashes routes, not schemas); door aggregate key
   set unchanged → no mcp_walk edit; MCP settings family description
   text updated; six "one subscription" prose sites updated in the
   docs story.

## Story cut (5)

- **HS-146-01** Config + DB + conductor: the multi-source plumbing
  (shape, migration, columns, scoped replace, per-source last-good,
  orphan cleanup, revisions). Tests:
  test_calendar_events_repository, test_calendar_ingest_conductor,
  test_reconcile (column adds).
- **HS-146-02** Settings service + wire: sources validation,
  `_calendar_sources` fact, egress derivation, MCP description,
  `calendar_configured` ≥1-enabled-valid semantics. Tests:
  test_door_read_model, settings validation units.
- **HS-146-03** Settings UI: the JOYFUL GadgetTable list editor +
  per-source egress chips + types. Tests: SettingsCalendar.test.tsx;
  shots 1440+393.
- **HS-146-04** Rail provenance + seed repairs: source_label through
  the projection to the chip (>1 source only); the three
  single-subscription e2e/walk seeds updated; walk leg 5 rewritten
  against the list editor. Tests: DoorBoardLane.test.tsx, both door
  glass e2es.
- **HS-146-05** Docs + walk + close: the six prose sites, full
  shots, cold walk, sweep, final summary.

## Risk notes

1. **Reconcile:** `NOT NULL DEFAULT ''` TEXT column adds are exactly
   the reconciler's `_add_missing_columns` path
   (`reconcile.py:601-634`, `_constant_default_for` :565); existing
   rows get `''` (pre-multi-source era — correct).
2. **Seed coordination:** the three single-subscription seeds MUST
   flip in the same commit as the config shape change or the e2es
   fail (story 01/04 coordination — the charter assigns the seed
   flips to the SAME commit lane as the shape change lands).
3. **Walk leg 5** must be rewritten against the list editor (story
   04/05).
4. **Orphan rows:** handled by the ruled end-of-tick cleanup.
5. **`_projection_id` namespace:** per-source revision feeds the
   parser's `subscription_revision` param — each source is its own
   namespace; the parser itself is untouched.
6. **Old-binary fallback:** an older binary reading `sources` falls
   back to empty config — acceptable per the not-really-released law;
   no compat ceremony.
