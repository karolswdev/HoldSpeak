# Evidence — HS-49-03: Close the loop (accepted actions -> issues)

Write-once record of the loop-closer. The rule that matters: nothing leaves the
machine and nothing changes state without an explicit, audited, per-action human
approval. This reuses the Phase 37/38 actuator system as-is — no new write
primitive, off by default, the payload-parity gate holds.

## What shipped

**Backend**
- `holdspeak/plugins/builtin/github_issue_actuator.py` — factored the proposal
  shape into `build_github_issue_proposal(task, owner, due, meeting_title, repo)`,
  the single source shared by `GithubIssueActuator.run` (the "first unowned" path)
  and the aftercare "file this accepted action" path. It honors the real owner
  (the unowned path passes `owner=None`). The `{repo, title, body}` payload is
  exactly what `build_github_issue_connector` already consumes — so a filed,
  approved proposal executes through the existing connector unchanged.
- `holdspeak/web/routes/meetings.py` — `POST /api/meetings/{id}/aftercare/file-issue`
  (`{action_item_id, repo}`). Loads the action item, refuses anything not
  belonging to the meeting (404) and anything whose `review_state != accepted`
  (400 — this is "track what I just accepted", not auto-filing), then records a
  `proposed` proposal via the existing `ActuatorRepository.record_proposal`.
  Idempotent on `aftercare-issue:{meeting_id}:{item_id}`, so re-filing the same
  action returns the same proposal (no duplicate, no extra audit row). Records
  only — no execution, no egress.
- `holdspeak/meeting_aftercare.py` — open items now carry `review_state` so the
  surface can gate the affordance on accepted items.
- `holdspeak/web_requests.py` — `_AftercareFileIssueRequest`.

The existing read + decision endpoints (`GET .../proposals`,
`POST .../proposals/{pid}/decision`) and the `ActuatorExecutor` are untouched:
the filed proposal lists, approves, and executes through them as any other
proposal does.

**UI** (`web/src/pages/history.astro` + `web/src/scripts/history-app.js`)
- A "File as issue" button on an aftercare open item, shown only when
  `review_state === 'accepted'`. It reveals an inline form (a `owner/repo` input,
  "Create proposal" / "Cancel") with a privacy note kept at the point of action:
  "Creates a proposal only. Nothing is sent until you approve it below, and
  execution needs actuators enabled."
- `fileActionAsIssue(item, repo)` POSTs the request and drops the returned
  proposal into the existing "Proposed actions" section (deduped on id, since the
  endpoint is idempotent). The user then approves/rejects with the existing
  controls; the existing "Nothing runs without your approval" copy already frames
  it.

## Tests (ran, read the output)

- `tests/integration/test_web_aftercare_file_issue.py` (5):
  - filing an accepted action creates a `proposed` GitHub proposal that lists via
    the existing read endpoint;
  - a non-accepted action is refused (400); a blank repo (400) and an unknown
    action (404) are refused;
  - filing is idempotent (same proposal id twice);
  - **the safety spine:** a `proposed` proposal is refused by the executor
    (`ActuatorExecutionError`, no connector call); after approval it is still
    refused while `allow_actuators` is off (`ActuatorPolicyError`, no connector
    call); only enabled + allow-listed + approved does the stub connector run,
    and the audit trail reads `proposed -> approved -> executed`.
- `tests/unit/test_github_issue_actuator.py` (12) still green after the
  proposal-builder refactor (substring assertions on title/body/preview hold).
- `uv run pytest -q -k "actuator or proposal or meeting or aftercare or action_item or github" --ignore=tests/e2e/test_metal.py`
  → **523 passed, 12 skipped**.

## Build + screenshots

- `(cd web && npm run build)` clean; `git ls-files holdspeak/static/_built` →
  empty (0 tracked).
- `scripts/screenshot_aftercare_close_loop.py`:
  - `screenshots/story-03-file-issue-form.png` — the inline form on the accepted
    "Wire the rate limiter" item with the privacy note; the unassigned (un-accepted)
    item shows no File-as-issue affordance.
  - `screenshots/story-03-proposal-created.png` — the resulting `create_issue ->
    github` proposal in the existing Proposed actions section (Awaiting Approval,
    full payload preview with `Owner: Priya`, Approve/Reject, "Nothing runs
    without your approval").

## Honesty / invariants held

- **No new write primitive.** Filing records a proposal through the existing
  `record_proposal`; execution is the unchanged `ActuatorExecutor` + the existing
  `build_github_issue_connector`.
- **Off by default, human-approved, audited.** Execution needs `allow_actuators`
  + the per-project allow-list + a host-injected connector + a separate approval;
  the payload-parity (TOCTOU) gate and audit trail are untouched. Proven by the
  executor test above.
- **Privacy posture at the point of action.** The form states what it does and
  that nothing is sent without approval; the preview shows exactly what would be
  filed.
- Behavior-preserving: routing, capture, plugins, and synthesis are untouched;
  actuators remain off by default.
