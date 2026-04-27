# HS-9-02 Evidence - Calendar and Outlook Meeting Candidates

## Shipped Result

HS-9-02 adds the first assisted-enrichment output type that can support
meeting scheduling without cloud access: local meeting candidates derived
from existing activity records.

The implementation adds:

- DB schema version 15
- `activity_meeting_candidates`
- `ActivityMeetingCandidate`
- candidate create/list/status-update/delete helpers
- candidate status validation for `candidate`, `armed`, `dismissed`, and
  `started`
- local candidate preview module for calendar-related activity records
- deterministic recognition of Outlook, Microsoft Teams, Google
  Calendar, and Google Meet domains
- tests for preview extraction, persistence, status updates, deletion,
  and validation

No Microsoft Graph, calendar DB reads, email scraping, automatic meeting
join, automatic recording, network calls, or external writes were added.

## Verification

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py -k "activity_meeting_candidates or activity_candidates"
4 passed, 58 deselected in 0.44s
```

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py
62 passed in 3.67s
```

```text
git diff --check
```
