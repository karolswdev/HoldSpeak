# PHILO-11-06 - The atlas cases for the new kinds and Slack

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** in-progress
- **Depends on:** PHILO-11-01, PHILO-11-02, PHILO-11-05
- **Unblocks:** PHILO-11-07
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** the charter's exit 7
- **Design:** `design/document-sources.md`
- **Canvas:** none

## Problem

The atlas has Send cases for the update only (`docs/internal/philo/graph/atlas-phase10.json`). A regression on a new kind or on Slack would not be caught.

## Scope

- **In:** for each new kind with a face seat, cases for picked, SENT and PREPARED at 1440 and 393 (`meeting_decision`: `.op` cases only, design §6a); the three failure transitions (design §6b); for Slack, POSTED, FAILED, UNKNOWN and the long-document refusal, through a recording HTTPS edge in the rig's hub (the Phase 10 story 07 pattern); `.op` siblings where the outcome is durable; each case through `scripts/graph_walk.py`, one case per run.
- **Out:** real sends (07).

## Acceptance criteria

- [ ] Each new face case fails on main and passes on the phase head; each `.op` reads the hub's record and receipt.
- [ ] The Phase 7, 8, 9 and 10 atlas cases still pass.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on main and green on the phase head; runs retained per case.

## Notes

- 2026-09-30 — dispatched in two parts by Muad'Dib. Part 1 covers the seven new document-kind `.op` file lifecycles and the four recorded Slack outcomes. Part 2 starts on a new dispatch after story 05 merges. This progress commit does **not** close the story or claim the face acceptance criterion. Part 1 remains **DRAFT — UNCHECKED, awaiting Muad'Dib**.
- Part 1 proof and full-suite dispositions: [lane-06-astra.md](lane-06-astra.md). Final operation matrix: 11/11 pass; old-main matrix: 11 blocked before Send. Final focused tests: 411 pass. The inherited face-word guard remains for story 05. No story criterion is flipped.
- Part 2 TODO: run each of these planned face ids at **1440 and 393**. The three suffixes listed in a row are three separate cases; each reads the hub outcome in the same observation. Confirm selectors against the merged story 05 build, not the canvas shim.

  | Kind / seat | Planned case ids |
  |---|---|
  | Brief, Chair | `case.p11.monday_brief.chair.picked`, `case.p11.monday_brief.chair.sent`, `case.p11.monday_brief.chair.prepared` |
  | Brief, Intelligence | `case.p11.monday_brief.intelligence.picked`, `case.p11.monday_brief.intelligence.sent`, `case.p11.monday_brief.intelligence.prepared` |
  | Desk decision, decision window | `case.p11.desk_decision.window.picked`, `case.p11.desk_decision.window.sent`, `case.p11.desk_decision.window.prepared` |
  | Decision record, Intelligence | `case.p11.decision_record.intelligence.picked`, `case.p11.decision_record.intelligence.sent`, `case.p11.decision_record.intelligence.prepared` |
  | Decision record, Room row | `case.p11.decision_record.room.picked`, `case.p11.decision_record.room.sent`, `case.p11.decision_record.room.prepared` |
  | Meeting summary, meeting window | `case.p11.meeting_summary.window.picked`, `case.p11.meeting_summary.window.sent`, `case.p11.meeting_summary.window.prepared` |
  | Meeting summary, Chair row | `case.p11.meeting_summary.chair.picked`, `case.p11.meeting_summary.chair.sent`, `case.p11.meeting_summary.chair.prepared` |
  | Meeting summary, Meetings record | `case.p11.meeting_summary.meetings_record.picked`, `case.p11.meeting_summary.meetings_record.sent`, `case.p11.meeting_summary.meetings_record.prepared` |
  | Meeting digest, Meetings record | `case.p11.meeting_digest.meetings_record.picked`, `case.p11.meeting_digest.meetings_record.sent`, `case.p11.meeting_digest.meetings_record.prepared` |
  | Meeting follow-up, Meetings record | `case.p11.meeting_followup.meetings_record.picked`, `case.p11.meeting_followup.meetings_record.sent`, `case.p11.meeting_followup.meetings_record.prepared` |
  | Slack outcomes on a document face | `case.p11.slack.posted`, `case.p11.slack.failed`, `case.p11.slack.unknown`, `case.p11.slack.too_large` |
  | Design §6b: limit refusal remains on the well | `case.p11.transition.slack_limit` |
  | Design §6b: changed preview, refresh, second Send | `case.p11.transition.preview_changed` |
  | Design §6b: last brief item leaves the Chair branch | `case.p11.transition.brief_last_ack`, `case.p11.transition.brief_last_defer` |

- `meeting_decision` remains `.op` only (design §6a); part 2 adds no face for it. The two last-item cases cover both gestures in the third §6b transition. These ids reserve the remaining work; they are not executed-case claims.
- 2026-09-30 — round two: paid Muad'Dib's adopted C1–C3 in the progress commit. The Slack reason facts now name the pinned replies, their two passing walks and four negative controls are retained in `assets/story-06-runs/p11-r2-slack-c1-c3/`, and `revision_source` identifies the provenance source. The three Meetings record TODO rows above follow the settled seats. Story 06 remains in progress; part 2 waits for story 05 and a new dispatch.
- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
