# Evidence — HS-17-07 — Meeting intel pushback (paged)

- **Shipped:** 2026-05-10
- **Commit:** `0c0e7cf`
- **Owner:** karol

## Files touched

### `holdspeak/device_status.py`

- New `build_intel_pages(intel) -> list[str]`: pure formatter, one
  page per non-empty section (Topics / Actions / Summary), each
  truncated to `LCD_TEXT_MAX_CHARS`, with multi-line layout (label on
  its own line, items as `- item` bullets).
- New `push_intel_to_devices(emitter, attached_ids, intel, *,
  page_dwell_s=4.0)`: spawns a daemon thread (`IntelLcdPager`) that
  emits each page with `time.sleep(page_dwell_s)` between them.
  Returns the page count scheduled (not the eventual broadcast tally,
  since those happen later on the pager thread).

### `holdspeak/web_runtime.py`

- New `_on_meeting_intel` hook pushes the intel via
  `push_intel_to_devices` against attached device IDs.

### Tests

- 9 new tests in `tests/unit/test_device_status_helpers.py`:
  - `test_build_intel_pages_full_payload`
  - `test_build_intel_pages_skips_empty_sections`
  - `test_build_intel_pages_handles_dict_action_items`
  - `test_build_intel_pages_caps_topics_and_actions`
  - `test_build_intel_pages_truncates_runaway_summary`
  - `test_build_intel_pages_returns_empty_when_nothing`
  - `test_push_intel_to_devices_schedules_pages` (uses
    `page_dwell_s=0` + `threading.enumerate` join to drain the daemon)
  - `test_push_intel_returns_zero_with_no_attached_devices`
  - `test_push_intel_returns_zero_when_nothing_to_show`
  - `test_push_intel_filters_falsy_ids`

## Verification

```
$ .venv/bin/python -m pytest tests/unit/test_device_status_helpers.py -q
103 passed in 0.08s

$ .venv/bin/python -m pytest -q     # full suite earlier
1809 passed, 21 skipped in 124.65s
```

## Live demo

llama-cpp-python is unavailable in this dev env so real intel
completion can't be triggered. Demoed the LCD path via a probe that
calls `build_intel_pages` on a fake intel object and pushes each page
through the device's `update_middle` service with the same 4 s dwell:

```
3 pages to emit:
--- page 1 (54 chars) ---
Topics:
- Auth refactor
- Q4 planning
- Latency budget
--- page 2 (49 chars) ---
Actions:
- Karol: schema doc
- Tom: latency tests
--- page 3 (100 chars) ---
Summary:
Team aligned on auth rewrite; Karol owns schema docs, Tom owns the latency benchmark suite.
```

User confirmation: *"Yes but… the line after Summary is half-cut"* →
iterated to the line-broken layout above. After iteration: *"Yes but
like — yes, looks good to me"*.

## Acceptance criteria — re-checked

All brackets `[x]` — see [`story-07-intel-pushback.md`](./story-07-intel-pushback.md). Note: the story file describes a single-payload rotation; implementation evolved to paged emit on a daemon thread during live tuning (better persistence semantics under AIPI-4-11 v2 + simpler than per-line widget paging).

## Deviations from plan

- **Paged emit on daemon thread** instead of single-payload rotation.
  Each section gets a dwell window via real time.sleep on a background
  thread; AIPI-4-11 v2's persist-until-replaced keeps each page on
  screen until the next replaces it.
- **Line-broken format** ("Topics:\n- A\n- B") instead of inline
  comma-separated. Chosen after live user feedback that the inline
  layout was hard to scan on the small middle widget.

## Follow-ups

- Live verification with real llama-cpp-python intel completion once
  available.
- `Intel queued` / `Working on intel` sticky frames (scoped in the
  story but not shipped) — can layer in if/when intel processing
  latency becomes noticeable in production.
