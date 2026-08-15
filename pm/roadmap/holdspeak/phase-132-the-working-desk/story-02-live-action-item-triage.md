# HS-132-02 — The live meeting is a living board

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** HS-132-01
- **Unblocks:** HS-132-03
- **Owner:** unassigned

## Problem

Phase 125's core promise — a meeting becomes a living execution board — does
not hold while the meeting is live. The PATCH routes
(`holdspeak/web/routes/meetings/action_items.py:25-35`:
`/api/action-items/{id}`, `/review`, `/edit`) resolve into
`MeetingService` implementations (`holdspeak/services/meeting_service.py:473-495`)
that only consult persisted meetings and 404 for anything still in-session.
Meanwhile the runtime callbacks that would serve live items —
`on_update_action_item`, `on_update_action_item_review`,
`on_edit_action_item` — are plumbed from `holdspeak/web_runtime.py:472-474`
through `web_server.py` into `holdspeak/web/context.py:39-41` and read by
nobody; their implementations at `holdspeak/runtime/meeting_glue.py:517-533`
delegate to `MeetingSession` mutations no HTTP path can reach. Nine tests in
`tests/integration/test_intel_streaming.py::TestActionItemPatchEndpoint` are
red on main for exactly this.

## Scope

### In

- Route the three PATCH verbs to the active session first (via the orphaned
  context callbacks), falling through to the persisted-meeting path when no
  live session owns the item.
- Preserve the persisted-path behavior for saved meetings.
- Re-green the nine `TestActionItemPatchEndpoint` tests (or rebuild them
  honestly if they are also monkeypatch-era casualties — coordinate with
  HS-132-12).

### Out

- New triage verbs or UI redesign of the action-item card.
- The realtime broadcast of triage results (HS-132-03 owns frame plumbing).

## Acceptance criteria

- [ ] During a live meeting, an intelligence-surfaced action item can be
  marked done, dismissed, reviewed, and edited; the change is visible in the
  session and survives the meeting's save.
- [ ] The same verbs still work on saved meetings.
- [ ] No orphaned callback remains: every plumbed `on_*_action_item*`
  callback has a reachable caller, or is deleted.
- [ ] The nine named tests pass in isolation and in-suite.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/integration/test_intel_streaming.py -k ActionItemPatch --tb=short`
- Focused unit tests for the live-session-first resolution order.
