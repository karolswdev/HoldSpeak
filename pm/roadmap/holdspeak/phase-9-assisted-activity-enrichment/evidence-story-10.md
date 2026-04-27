# HS-9-10 Evidence - Meeting Candidate Recording Workflow

Date: 2026-04-27

## Delivered

- Added a manual `POST /api/activity/meeting-candidates/{candidate_id}/start` endpoint.
- The endpoint uses the existing runtime `on_start` hook; it does not auto-start from preview, save, or arm actions.
- Saved candidates now persist `started_meeting_id` after manual start.
- Started meetings receive the candidate title through the existing meeting update hook when the runtime supports it.
- `/activity` now shows a visible Start action on saved candidates and displays the linked meeting ID after start.

## Verification

```text
$ uv run pytest -q tests/unit/test_db.py -k "activity_meeting_candidates"
...                                                                      [100%]
3 passed, 58 deselected in 0.47s
```

```text
$ uv run pytest -q tests/integration/test_web_activity_api.py -k "meeting_candidate"
...                                                                      [100%]
3 passed, 6 deselected in 0.54s
```

```text
$ uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py tests/integration/test_web_activity_api.py -k "activity_meeting_candidates or activity_candidates or meeting_candidate"
.........                                                                [100%]
9 passed, 64 deselected in 0.66s
```

```text
$ git diff --check
```
