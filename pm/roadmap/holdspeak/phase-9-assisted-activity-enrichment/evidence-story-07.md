# HS-9-07 Evidence - Meeting Candidate API Surface

## Shipped Result

HS-9-07 makes calendar/Outlook meeting candidates directly testable
through the local web API.

The implementation adds:

- `GET /api/activity/meeting-candidates/preview`
- `POST /api/activity/meeting-candidates`
- `GET /api/activity/meeting-candidates`
- `PUT /api/activity/meeting-candidates/{candidate_id}/status`
- `DELETE /api/activity/meeting-candidates`
- serialization for candidate preview and stored candidate payloads
- integration coverage for preview, persist, list, arm, and delete

The preview endpoint only reads existing local activity records. No
Microsoft Graph, calendar DB reads, email scraping, network calls,
automatic meeting join, or automatic recording were added.

## Curl-Style Flow

1. Refresh or seed local activity records.
2. Preview candidates:
   `GET /api/activity/meeting-candidates/preview`
3. Persist a candidate from preview data:
   `POST /api/activity/meeting-candidates`
4. Arm or dismiss it:
   `PUT /api/activity/meeting-candidates/{id}/status`
5. Clear candidates:
   `DELETE /api/activity/meeting-candidates?status=armed`

## Verification

```text
uv run pytest -q tests/integration/test_web_activity_api.py -k meeting_candidate
1 passed, 6 deselected in 0.37s
```

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/integration/test_web_activity_api.py
9 passed in 0.69s
```

```text
git diff --check
```
