# HS-146-01 — Multi-source plumbing (config + DB + conductor)

- **Project:** holdspeak
- **Phase:** 146
- **Status:** in-progress
- **Depends on:** —
- **Unblocks:** HS-146-02, HS-146-04
- **Owner:** unassigned

## Problem

The calendar layer knows exactly one source: one config string
(`integrations.py:17-20`), one revision, a conductor that reads it
(`calendar_ingest_conductor.py:173`), and a projection replace that
deletes EVERY row (`db/calendar_events.py:80`). A second calendar is
structurally impossible, and one bad source would wipe a good one's
events.

## Scope

### In (settled design rows 1–2; edit map in the plan)

- `CalendarSource {id, label, url, enabled}`;
  `CalendarConfig.sources: list`. One-shot `Config.load()` migration
  (old `subscription` → first source, consumed once). Exports
  updated.
- `calendar_source_revision(source_id, url)`; per-source summaries.
- Additive `source_id` + `source_label` TEXT columns on
  `calendar_events`; unique index rescoped `(source_id, uid,
  starts_at)`; `CalendarEvent` dataclass + row mapping.
- `replace_projection(source_id, revision, events, seen_at)` scoped
  `DELETE WHERE source_id = ?`; conductor iterates enabled sources
  with per-source fetch/parse/replace (`_refresh_source`), a failed
  source leaves every other source's rows intact, end-of-tick orphan
  cleanup for no-longer-enabled ids.
- If (and only if) this story changes the settings WIRE acceptance of
  the old `subscription` key, the three hardcoded seeds flip in the
  same commit (risk register row 1).

### Out

- Settings service/wire validation (02), the list editor (03), rail
  chip + seed rewrites for provenance (04), docs (05). Parser
  untouched.

## Acceptance criteria

1. Two enabled sources project independently; killing one source's
   fetch leaves the other's rows byte-untouched (per-source
   last-good proven in a test).
2. A source removed from config (or disabled) loses its rows at the
   next tick; nothing else is deleted.
3. An old config file with `calendar.subscription` loads as one
   enabled unlabeled source; the key is gone after the next save.
4. Schema reconcile adds both columns on an existing DB with rows
   (proven in test_reconcile).

## Test plan

Focused only: `tests/unit/test_calendar_events_repository.py`,
`tests/unit/test_calendar_ingest_conductor.py`,
`tests/unit/test_reconcile.py` (+ any config-load unit file found for
the migration). Isolated HOME; `uv run --python 3.13.11`.
