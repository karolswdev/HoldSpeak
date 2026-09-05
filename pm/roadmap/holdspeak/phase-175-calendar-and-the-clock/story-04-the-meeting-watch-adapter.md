# HS-175-04 — The meeting Watch adapter

- **Project:** holdspeak
- **Phase:** 175
- **Status:** backlog
- **Depends on:** HS-175-01, Phase 172 merged (the auto-intel extraction
  produces the decisions and commitments this adapter surfaces)
- **Unblocks:** HS-175-05
- **Owner:** unassigned

## Problem

Only GitHubWatchSource (watch_sources.py:58) and JiraWatchSource
(watch_sources.py:294) exist. Meetings are not observable as Watch
entities. A project Room with three meetings linked has no way to show
"2 decisions since last check" or "1 commitment overdue from the
standup" alongside its GitHub and Jira items. The arc says: "the
meeting Watch adapter" — meetings and their extracted
decisions/commitments become Watch entities in a Room.

## Scope

- In:
  - A `MeetingWatchSource` in watch_sources.py following the same
    grammar as GitHubWatchSource and JiraWatchSource: it produces
    Watch entities from meetings linked to a project Room.
  - Each meeting entity carries: title, date, participant count,
    decisions count, commitments count, latest intel run status.
  - The entity's `updated_at` reflects the latest intelligence run or
    commitment status change (so SINCE YOU LOOKED picks it up).
  - The adapter reads from the local database (meetings,
    meeting_intel_snapshots, decision_records, decision_commitments);
    zero egress (Article III).
  - The adapter is registered as a watch source type alongside GitHub
    and Jira; Rooms can include meeting watches in their SOURCES.
- Out:
  - Individual decisions as separate Watch entities (they roll into the
    meeting entity's counts; the Room's DECISIONS section already shows
    them).
  - Auto-linking meetings to Rooms (Phase 172 does this; this story
    reads the links).
  - External meeting platform integration (the adapter reads local
    meeting data, not Google Calendar or Teams APIs).

## Acceptance criteria

- [ ] MeetingWatchSource exists in watch_sources.py and follows the
      WatchSource protocol (Article II: everything is a primitive).
- [ ] Meeting entities carry title, date, participants, decisions
      count, commitments count, intel status.
- [ ] The entity's updated_at reflects the latest intel run or
      commitment change; SINCE YOU LOOKED shows the delta.
- [ ] The adapter reads from the local database; zero network calls
      (Article III).
- [ ] A Room with linked meetings shows meeting Watch entities in
      SOURCES alongside GitHub and Jira entities.
- [ ] Every evaluation is receipted (Article XI).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k meeting_watch`
  - MeetingWatchSource returns entities from seeded meetings with intel
    snapshots and commitments.
  - updated_at reflects the latest intel run.
  - A meeting without intel returns an entity with decisions=0,
    commitments=0 (Article VI: honest at zero — but the count IS zero
    here, so it is honest).
- Integration: the rig boots a hub with seeded meetings and a Room;
  the adapter produces entities; the Room's SINCE YOU LOOKED picks
  up a change.
- Manual: the owner's desk shows meeting Watch entities in a Room after
  meetings are linked.

## Notes / open questions

- The existing WatchSource protocol (watch_sources.py) expects
  `evaluate()` to return entities with a standard shape. The meeting
  entity shape may need a new `entity_type` value (`"meeting"`)
  alongside `"pull_request"`, `"issue"`, etc.
- Phase 172 must be merged for this adapter to have meaningful data
  (decisions and commitments from auto-intel). Without 172, the adapter
  can still produce meeting entities but with 0 decisions/commitments.
