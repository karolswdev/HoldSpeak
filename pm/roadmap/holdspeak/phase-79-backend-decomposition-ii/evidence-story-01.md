# Evidence — HS-79-01 — `db/activity.py` becomes the activity package

**Status:** done (2026-07-03).

## The move

`holdspeak/db/activity.py` (1,596 lines, one `ActivityRepository`) → the
`holdspeak/db/activity/` package: six concern mixins composed over
`BaseRepository` in `__init__.py` (27 lines). The public surface is unchanged
(`from .activity import ActivityRepository` in `db/__init__.py` resolves to the
package re-export; `db.activity.<method>` call sites untouched).

| Module | Lines | Concern |
|---|---|---|
| records.py | 348 | normalizers, upsert/list/get/delete, the ledger iterator, the record row mapper |
| settings.py | 215 | import checkpoints, the privacy toggle, nudge dismissals, the checkpoint mapper |
| rules.py | 406 | domain exclusions + project-assignment rules, their mapper |
| enrichment.py | 248 | enrichment connectors + the connector-run ledger, their mappers |
| annotations.py | 138 | activity annotations, their mapper |
| candidates.py | 303 | meeting candidates, their mapper |

Largest module 406 — all under the Phase-63 module budget (600) with headroom.

## Verbatim accounting

The split was executed by line-range slicing of the original file (1,565 of
1,596 source lines moved; the remainder is the replaced module header/class
line). A programmatic check against `git show HEAD:` found **zero method-body
lines differing**; the 9 non-verbatim lines are import plumbing only:

- the package headers' model imports (the old single header list, distributed),
- `from ..activity_mapping` → `from ...activity_mapping` at the three lazy
  call sites in `rules.py` (one package level deeper),
- `datetime` added to `records.py`'s header (used by `upsert_activity_record`).

**Patch-target edits in tests: zero** (the repository is reached through
`db.activity`, never module-level patches). Tests unmodified.

## Proven

`uv run pytest -q tests/unit` **2407 passed** (unmodified) ·
`tests/integration` **685 passed** · import + MRO verified
(`ActivityRepository` composes six mixins over `BaseRepository`).
