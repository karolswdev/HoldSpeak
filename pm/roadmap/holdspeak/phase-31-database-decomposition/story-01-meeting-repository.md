# HS-31-01 — Repository seam + `MeetingRepository` (pilot pattern)

**Status:** not-started.

## Goal

Establish the repository pattern that the rest of the phase follows, and migrate
the meetings domain — the largest, most central cluster — out of `MeetingDatabase`
verbatim. After this story the seam exists and the meetings methods read/write
through `MeetingRepository`; every later story copies this shape.

**Posture: greenfield/aggressive** — clean end state, not a compat facade. The
`Database` container is the new API; `MeetingDatabase` is on its way out (deleted
in HS-31-03 once empty).

## Scope

- Create the `holdspeak/db/` package: a `Database` container that owns the one
  connection and exposes repos as attributes (`db.meetings`), a shared
  connection/transaction helper, and a `BaseRepository` holding the injected connection.
- Move the meetings cluster verbatim into `MeetingRepository`:
  `meetings, segments, speakers, topics, bookmarks, action_items, meeting_tags,
  meeting_projects` — including `save_meeting()` and its `_save_segments`/
  `_save_bookmarks` helpers and the late `from .meeting_session import ...` guard.
- **Update the meetings call sites** to `db.meetings.<method>(...)` and remove
  those methods from `MeetingDatabase` (the god-class shrinks each story until
  HS-31-03 deletes the remainder). Establish the pattern every later story copies.

## Test plan

- Rewrite the meetings portion of `tests/unit/test_db.py` to the repo API.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- Add an import test pinning "no circular import" for the new package.

## Done when

- [ ] `holdspeak/db/` package exists with `Database` container + `BaseRepository` + conn helper.
- [ ] Meetings cluster lives in `MeetingRepository`; call sites use `db.meetings.*`.
- [ ] Those methods removed from `MeetingDatabase`; full suite green; ruff clean.
- [ ] Pattern documented in the package + `MeetingRepository` docstrings.
