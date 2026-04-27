# HS-9-11 Evidence - Activity Dashboard Polish

Date: 2026-04-27

## Delivered

- Added clearer empty states for domains, rules, records, candidate previews, and saved candidates.
- Added panel-specific messages for domains, project rules, and meeting candidates.
- Added a saved-candidate status filter on `/activity`.
- Made preview and saved candidate cards visually distinct.
- Disabled action buttons while their async request is running and disabled no-op candidate status buttons.

## Verification

```text
$ uv run pytest -q tests/integration/test_web_activity_api.py -k "activity_page or meeting_candidate"
....                                                                     [100%]
4 passed, 5 deselected in 0.51s
```

```text
$ git diff --check
```

```text
$ curl -s http://127.0.0.1:56147/activity | rg -n "candidate-status-filter|No preview loaded|candidates-message|Start"
354:              <select id="candidate-status-filter" aria-label="Candidate status filter">
358:                <option value="started">Started</option>
367:            <p id="candidates-message" class="panel-message"></p>
535:          : `<div class="empty"><strong>No preview loaded.</strong>Preview scans imported local calendar activity without saving or starting a recording.</div>`;
557:                  <button class="primary" type="button" data-start-candidate="${escapeHtml(candidate.id)}" ${candidate.status === "started" ? "disabled" : ""}>Start</button>
```
