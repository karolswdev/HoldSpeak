# HS-173-06 — The walk

- **Project:** holdspeak
- **Phase:** 173
- **Status:** backlog
- **Depends on:** HS-173-02, HS-173-04, HS-173-05
- **Unblocks:** HS-173-07
- **Owner:** unassigned

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
The Steward's Hand and Voice introduces the model-drafted update, the
reviewer nudge (the first external write), health signals, and the
release-readiness scorecard. These must be proven on his real desk with
his real projects.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. The steward drafts an update from real deltas; the model
       rewrites it; unverified claims are marked; the egress chip is
       on the card.
    2. He edits two sentences and publishes.
    3. The Room shows reviewer-latency rows (a person with PRs
       waiting).
    4. The steward proposes a nudge on a PR; the nudge card shows the
       proposed comment.
    5. He approves; the comment posts; the receipt shows the URL.
    6. Flaky-CI and merge-queue depth tokens appear in the Room.
    7. The release-readiness scorecard shows per-signal indicators.
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 02-05).
  - Linux walk.

## Acceptance criteria

- [ ] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [ ] The model-drafted update is readable, claims are referenced,
      unverified claims are marked.
- [ ] The nudge comment posts to a real PR; the receipt shows the URL.
- [ ] Health signals and the release-readiness scorecard reflect his
      real project data.
- [ ] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on: (a) at least one project with Watch data, (b)
  the model drafter configured (170's concierge), (c) a PR with a
  pending reviewer for the nudge. If his desk lacks these, they must
  be arranged during the walk.
- The nudge walk is the first external write from HoldSpeak on his
  desk. The receipt must be shown and his verdict recorded.
