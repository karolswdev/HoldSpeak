# HS-49-01 — The aftercare digest (open / decided / changed)

- **Project:** holdspeak
- **Phase:** 49
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-49-02, HS-49-03, HS-49-04, HS-49-05, HS-49-06
- **Owner:** unassigned

## Problem
A meeting produces artifacts and then the user has to go figure out, on their own,
what is still open, what was actually decided, and what moved since last time.
There is no "here's your next move" view, and there is no cross-meeting query at
all. The meeting result is display, not follow-through.

## Scope
- **In:**
  - A **read-only aftercare aggregation** over the existing data: **what's still
    open** (action items with `status=pending`, optionally grouped by `owner`,
    across meetings or for a meeting), **what was decided** (the `decisions`
    artifact's `structured_json`), and **what changed since the previous meeting**
    (a real diff of decisions + action items vs the chronologically prior meeting
    by `started_at`).
  - A **new API** (e.g. `GET /api/meetings/{id}/aftercare`, and/or an
    `/api/aftercare` cross-meeting "for me" rollup) returning the aggregation;
    pure read, no writes.
  - An **aftercare surface** on the meeting/history view: a calm "your next move"
    panel (open items, decisions, since-last-meeting delta). Quiet when there's
    nothing open and nothing changed. Home it where it reads as action, not a
    second artifact dump (settle the home here; favor the lightest thing).
- **Out:** the transcript-moment jump (HS-49-02); actions-to-issues (HS-49-03);
  the follow-up draft (HS-49-04); docs (HS-49-05). This story is the aggregation +
  surface.

## Acceptance criteria
- [ ] An aggregation endpoint returns honest counts over meetings + action items +
      artifacts: open items (by owner), decisions, and a real since-last-meeting
      diff (new/closed decisions + actions vs the prior meeting).
- [ ] An aftercare surface renders it on the meeting/history view; empty/no-change
      state stays quiet (no fabricated "changes"); numbers are accurate.
- [ ] Local-first and read-only: no new writes; behavior-preserving; page-content +
      API tests; `npm run build` ✓; 0 `_built/` tracked; CSS for any JS-injected
      DOM is `is:global` and screenshot-verified.

## Test plan
- Unit/integration: seed two meetings (prior + current) with decisions + action
  items; assert open-by-owner, decisions, and the since-last diff; the no-prior and
  no-change cases stay quiet; `uv run pytest -q -k "meeting or aftercare or
  action_item or artifact"`.
- Manual + screenshot: the surface reads as "next move"; quiet when nothing open.

## Notes / open questions
- Order meetings by `started_at` to find "the previous meeting"; ISO text compare.
- Reuse `list_action_items(owner=...)` and `list_artifacts(meeting_id)`; do not
  invent a second store. Decisions live in the `decisions` artifact `structured_json`.
- Decide the home (dedicated tab vs. a section in meeting-detail vs. a cross-meeting
  "for me" rollup); favor the lightest thing that does not bloat `history.astro`
  (page-density warning; prefer a partial if it grows).
