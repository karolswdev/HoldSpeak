# Phase 49 — Meeting Aftercare ("close the loop") — Final Summary

**Status:** CLOSED (6/6). Opened and closed 2026-06-07.
**Branch:** `phase-49/story-01-aftercare-digest`. **PR:** to `main`, merged on green CI.

## Why this phase

The meeting side already had 14 real plugins, artifacts, proposals, history, and
action review. What it lacked was follow-through. The strategic review put it
plainly: "A beautiful artifact that never changes the user's next action is
decoration." A meeting produced artifacts, the user read them, and then went
somewhere else to do the work. There was no "here's your next move", no
cross-meeting view, and the transcript moment that justified a result was
invisible even though action items already carried it.

This phase made a meeting close its own loops, on the surface where the meeting
already lives, without changing how meetings are captured, how plugins run, or how
synthesis works, and without ever acting on the user's behalf without explicit
approval.

## What shipped

- **HS-49-01 — The aftercare digest.** A read-only aggregation
  (`holdspeak/meeting_aftercare.py` → `compute_meeting_aftercare`) over meetings +
  action items + the `decisions` artifact, behind
  `GET /api/meetings/{id}/aftercare`: what's still open (by owner, unassigned
  last), what was decided, and a real since-last-meeting diff (new decisions / new
  actions / closed actions vs the chronologically prior meeting). `is_empty` keeps
  it quiet when there's nothing to act on. Surfaced as a "Your next move" panel at
  the top of the meeting-detail side column, above the artifact dump.
- **HS-49-02 — Transcript provenance ("show me the moment").**
  `resolve_provenance_segment` maps a real `source_timestamp` to the transcript
  segment that justifies a result, threaded into the digest payload. A focus-safe
  "show me the moment" jump on open items, decisions, and action-item cards
  reveals + flashes that segment. It shows only when a real timestamp resolves to
  a real segment (no fake `0:00`) and never steals keyboard focus.
- **HS-49-03 — Close the loop: accepted actions to issues.** A "File as issue"
  affordance on accepted open items records a GitHub-issue actuator **proposal**
  through the existing propose → approve → execute flow
  (`POST /api/meetings/{id}/aftercare/file-issue`). A shared
  `build_github_issue_proposal` feeds the same payload the existing connector
  consumes, so there is **no new write primitive**. Off by default,
  human-approved, audited; the payload-parity gate holds; idempotent per action.
- **HS-49-04 — Draft the follow-up.** `build_followup_draft` assembles a local
  markdown summary (decisions + open items by owner + the since-last delta) from
  the digest, behind `GET /api/meetings/{id}/followup-draft`, surfaced as a "Draft
  follow-up" preview + Copy in the panel head. Preview + copy only, never sent;
  deterministic, no LLM; honest at empty (one plain line, no padding).
- **HS-49-05 — Docs.** A "Meeting Aftercare (close the loop)" section in the
  Meeting Mode guide telling the flow end to end (open/decided/changed → show me
  the moment → file an accepted action → draft the follow-up) with three real
  shipped-UI screenshots and an honest posture note; the README + docs index frame
  "close the loop"; the three new endpoints are in the API reference.
- **HS-49-06 — Closeout.** Before/after (artifact-only view vs the aftercare
  surface), a green end-to-end dogfood, full suite green, this summary, the phase
  CLOSED, and the PR to `main`.

## The one invariant, held

Nothing leaves the machine, and nothing changes state, without explicit per-action
human approval; and every "open / decided / changed" claim is real.

- Closing a loop reuses the actuator system as-is: off by default
  (`allow_actuators` + per-project allow-list + a host-injected connector), every
  execution audited, the payload-parity (TOCTOU) gate intact. No new write
  primitive, no auto-execute. The HS-49-03 executor test proves a
  proposed/unapproved proposal never egresses, and that enabling + approving
  yields `proposed → approved → executed`.
- The follow-up draft is preview + copy, assembled locally, never sent.
- Diffs and "what's open" are computed from real data; the surface stays quiet
  with no prior meeting and no change. No fabricated deltas.
- Provenance shows only where a real timestamp exists. No fake `0:00`.

## Behavior preservation

Aftercare is read-only aggregation + the existing actuator path + a local draft.
Meeting capture, plugin runs, and synthesis are untouched. Actuators remain off by
default. The only new endpoints are reads, plus one POST that records a proposal
(no execution, no egress).

## Evidence

- **Tests.** Full suite green: **2426 passed, 17 skipped** (`uv run pytest -q
  --ignore=tests/e2e/test_metal.py`; skips are pre-existing opt-in / missing
  fixture / missing model). New across the phase: `tests/unit/test_meeting_aftercare.py`
  (aggregation, provenance, follow-up draft) and the integration tests
  `tests/integration/test_web_meeting_aftercare_api.py` +
  `test_web_aftercare_file_issue.py` (the actuator safety spine).
- **Dogfood.** `scripts/dogfood_meeting_aftercare.py` →
  `dogfood-transcript.txt`: open/decided/changed → show me the moment → accept +
  file → approve + execute (audited) → draft the follow-up. No mic, no LLM, stub
  connector.
- **Before/after + screenshots.** `screenshots/story-06-before-artifact-only.png`
  (the old artifact-only view) vs `story-06-after-aftercare.png` (the panel), plus
  the per-story captures (`story-01`..`story-04`). `(cd web && npm run build)`
  clean; 0 `_built/` tracked (source-only).
- **Docs.** Doc guards green (dangling-link + embedded-image-ref); every claim
  grounded in `meeting_aftercare.py` / `actuator_executor.py` /
  `github_issue_actuator.py` / the routes.

## Follow-ups (not in this phase)

- Backfilling a transcript-moment link onto decisions at synthesis time (a schema
  touch) so more results carry provenance. HS-49-02 took the no-schema-churn path
  and surfaces it only where the data already exists.
- A richer repo picker for "file as issue" (per-project default repo) instead of a
  free-text field. The actuator path is ready for it.
- The other backlog bets (voice macros, release-readiness, privacy-at-decision
  points) remain in [`../BACKLOG.md`](../BACKLOG.md) as their own focused phases.
