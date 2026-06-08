# Evidence — HS-53-03: dictate with this as context

Write-once record of the "selected record" override on the dictation context path. When a
user clicks **Dictate with this** on a nudge, the selected `ActivityRecord` is pinned at
the front of the bundle the rewrite stage sees — by name. With **no** selection, the
default daily bundle is byte-identical to pre-Phase-53.

## What shipped

- **`build_activity_context(..., selected_record_id: Optional[int] = None)`** — a new
  keyword-only param on `holdspeak/activity_context.py`'s entry point. When set:
  - if the record is already in the default list (matched by id), it moves to
    `records[0]` (the rest of the list is preserved in original order);
  - if the record is not in the default list (older than `limit`, or filtered out by
    `project_id`), it is fetched directly via the new
    `ActivityRepository.get_activity_record(id)` and prepended;
  - an unknown id is a quiet no-op — the engine refuses to fabricate context, and the
    default bundle is returned unchanged (no `selected_record_id` key).
- **`ActivityContextBundle.selected_record_id: Optional[int] = None`** — a new dataclass
  field. `to_dict()` only emits the key when it is set, so the default bundle's JSON shape
  is unchanged byte-for-byte (the load-bearing DIR-01 invariant).
- **`ActivityContextProvider.__call__`** now reads
  `context["selected_activity_record_id"]` (preferred) or
  `context["selected_activity"]["record_id"]` (the convenience shape when a caller hands
  in a whole nudge payload). Blank / non-numeric values are ignored — the default path
  stays unchanged.
- **New `ActivityRepository.get_activity_record(record_id) -> Optional[ActivityRecord]`**
  on `holdspeak/db/activity.py`. A small read-only fetch-by-id (no new state, no import).
  Returns `None` for unknown ids and for non-integer inputs.

## Why this is honest

- **Default path byte-identical.** The new field has a `None` default; `to_dict()`
  conditionally emits it; the records list is untouched when no selection is passed. The
  two regression tests (`test_default_path_is_byte_identical`,
  `test_provider_default_path_is_unchanged`) lock this — anything that would shift the
  default JSON shape would break them.
- **Read-only.** The override calls `get_activity_record` — a `SELECT ... WHERE id = ?`
  against the existing `activity_records` table. No browser import, no network, no write.
- **No fabrication.** An unknown id does not produce a stub or a placeholder; the bundle
  is unchanged and the rewrite stage sees no selection. The test
  `test_unknown_selected_id_is_a_no_op` proves this.
- **Quiet on garbage input.** Empty strings, `None`, and non-numeric values are dropped
  on the way in (the test `test_provider_ignores_blank_or_garbage_selection`).

## Tests

`tests/unit/test_activity_context_selected.py` — 8 tests, every acceptance bullet covered:

- `test_default_path_is_byte_identical` — no selection → no `selected_record_id` in the
  bundle; records list order is the same as the existing default (last_seen DESC).
- `test_selected_record_is_pinned_at_front` — the selected record moves to `records[0]`
  and its entity is named in the bundle.
- `test_selected_record_outside_default_list_is_fetched` — a selected record that has
  fallen off the default `limit` window is fetched and prepended.
- `test_unknown_selected_id_is_a_no_op` — an id that does not exist leaves the bundle
  unchanged; no `selected_record_id` key is emitted.
- `test_provider_reads_selected_id_from_context` — `ActivityContextProvider` consumes
  both `selected_activity_record_id` and the convenience `selected_activity` shapes.
- `test_provider_default_path_is_unchanged` — the provider's default call (`{}`) emits
  no `selected_record_id`.
- `test_provider_ignores_blank_or_garbage_selection` — `""`, `None`, `"not-a-number"` →
  default path.
- `test_get_activity_record_returns_none_for_unknown` — the new repo getter is honest
  about misses.

```
uv run pytest -q tests/unit/test_activity_context_selected.py tests/unit/test_activity_context.py
-> 11 passed in 0.36s
   (8 new + 3 existing — the existing activity-context tests still pass, proving the
    default JSON shape is byte-identical.)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2522 passed, 17 skipped in 71.51s
   (was 2514 at HS-53-02 close; +8 is the new override tests.)
```

0 `_built/` tracked; no UI bundle touched (HS-53-04 wires this into the nudge card).

## Not done here (by design)

- **The "Dictate with this" button** in the nudge card — HS-53-04 (calls into this seam).
- **A separate dictation endpoint that bundles its own context** — out of scope; the
  rewrite path already builds the context via `ActivityContextProvider`, so the override
  is consumed through the existing seam.
- **The user guide** — HS-53-05.
- **Dogfood + phase close** — HS-53-06.

## Files touched

- `holdspeak/activity_context.py` — new `selected_record_id` param + bundle field +
  `_pin_selected_record` + `_selected_record_id_from_context`.
- `holdspeak/db/activity.py` — new `get_activity_record(id)` getter.
- `tests/unit/test_activity_context_selected.py` (new) — 8 tests.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/story-03-dictate-with-context.md` —
  status flipped to `done`.
- `pm/roadmap/holdspeak/phase-53-activity-prebriefing/current-phase-status.md` — story
  table updated, "Where we are" updated.
- `pm/roadmap/holdspeak/README.md` — "Last updated".
