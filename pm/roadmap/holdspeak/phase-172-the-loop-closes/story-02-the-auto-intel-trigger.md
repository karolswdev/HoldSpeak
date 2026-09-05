# HS-172-02 — The auto-intel trigger

- **Project:** holdspeak
- **Phase:** 172
- **Status:** done
- **Depends on:** HS-172-01
- **Unblocks:** HS-172-03
- **Owner:** unassigned

## Problem

Meeting intelligence has NEVER run on the owner's desk (census: 0
plugin runs, 0 intel snapshots, 6 of 8 meetings with intelligence
disabled). The `run_intelligence` verb (meeting_intel_service.py:48) is
manual: the user must click it per meeting. The arc says intelligence
must run by default after every meeting linked to a Room, on the local
model (170's assignment). The Room link is the consent (Article V: the
user chose to link the meeting to a project; that is the arming act).

## Scope

- In:
  - After `stop_capture` (or meeting save) for a meeting linked to a
    Room via `meeting_projects`, automatically enqueue an intelligence
    job for that meeting.
  - The trigger respects the model assignment from 170 (the
    `intel_realtime_model` in the config); if no model is assigned the
    job queues but does not run (honest failure: "no model assigned").
  - Intelligence enabled by default for Room-linked meetings;
    intelligence disabled by default for unlinked meetings (the
    existing per-meeting toggle preserved as an override).
  - The auto-enqueue is idempotent: if the meeting already has a
    completed intel job for the same transcript hash, no new job is
    queued (intel_queue.py's existing dedup by transcript_hash).
  - Every enqueue and run receipted through the kernel (Article XI).
- Out:
  - New intelligence plugins (use the existing 14+ plugins).
  - Automatic filing of extracted items (that is HS-172-03).
  - Running intelligence on import (import meetings may trigger
    differently; backlog).
  - External sends or writes.

## Acceptance criteria

- [x] A meeting linked to a Room via `meeting_projects` triggers an
      intel job automatically after capture stops; verified by a rig
      that boots a hub, creates a Room-linked meeting, stops capture,
      and asserts an intel job exists for that meeting.
- [x] A meeting NOT linked to any Room does NOT auto-trigger intel
      (unless manually enabled via the per-meeting toggle).
- [x] If no model is assigned (no 170 concierge), the job queues with
      status "no_model_assigned" and the Room shows "No model" (Article
      VI: honest at zero).
- [x] Duplicate enqueue is idempotent (same transcript hash = no new
      job); verified by calling `stop_capture` twice.
- [x] Every enqueue leaves a kernel receipt (Article XI.2).
- [x] Zero egress; the model runs locally (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k auto_intel_trigger`
  - Room-linked meeting auto-enqueues on stop_capture.
  - Unlinked meeting does not auto-enqueue.
  - Duplicate transcript hash is idempotent.
  - Missing model assignment produces honest status.
- Integration: the rig boots a hub, links a meeting to a Room, stops
  capture, and reads the intel job status.
- Manual: the owner's desk shows an intel job after a test meeting.

## Notes / open questions

- The trigger point: `stop_capture` (meeting_service.py:360) or a
  post-save hook? The natural point is `stop_capture` because that is
  when the transcript is final. If the meeting is imported (not
  captured), the trigger point may differ.
- The per-meeting intelligence toggle (which 6/8 of his meetings have
  disabled) may need a migration to flip the default for Room-linked
  meetings.
