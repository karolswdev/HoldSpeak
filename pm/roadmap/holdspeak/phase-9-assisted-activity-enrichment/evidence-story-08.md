# HS-9-08 Evidence - Meeting Candidate Browser Controls

## Shipped Result

HS-9-08 adds a Meeting Candidates panel to `/activity`.

The browser surface can now:

- preview local calendar/Outlook candidates
- save a preview candidate
- refresh saved candidates
- arm a saved candidate
- dismiss a saved candidate
- reset a saved candidate to `candidate`
- clear dismissed candidates

The panel uses the local API shipped in HS-9-07. It does not introduce
automatic recording, external calendar access, Microsoft Graph, calendar
database reads, email scraping, network calls, or external writes.

## Verification

```text
uv run pytest -q tests/integration/test_web_activity_api.py -k "activity_page or meeting_candidate"
2 passed, 5 deselected in 0.45s
```

```text
uv run pytest -q tests/unit/test_activity_candidates.py tests/integration/test_web_activity_api.py
9 passed in 0.67s
```

```text
git diff --check
```
