# HS-9-09 Evidence - Meeting Candidate Dedupe and Time Hints

## Shipped Result

HS-9-09 polishes meeting candidates so repeated preview/save cycles are
less noisy.

The implementation adds:

- DB schema version 16
- `activity_meeting_candidates.dedupe_key`
- unique dedupe index for non-empty candidate keys
- merge behavior for repeated saves from the same connector/source record
- status preservation for repeated default saves
- simple local time-hint parsing from visible title/URL metadata shaped
  like `YYYY-MM-DD HH:MM[-HH:MM]`
- API coverage for repeated save behavior
- unit coverage for parser and DB merge behavior

No calendar database reads, Microsoft Graph calls, email scraping,
network calls, automatic meeting join, or automatic recording were added.

## Verification

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py tests/integration/test_web_activity_api.py -k "activity_meeting_candidates or activity_candidates or meeting_candidate"
7 passed, 64 deselected in 0.71s
```

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/integration/test_web_activity_api.py
10 passed in 0.74s
```

```text
git diff --check
```
