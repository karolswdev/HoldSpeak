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
- [x] The Phase 7, 8, 9 and 10 atlas cases still pass.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on main and green on the phase head; runs retained per case.

## Notes

- 2026-10-01 — Part 2 walks and the full suite are complete; the story remains in progress because the literal baseline-red condition has one valid control exception. All 101 Phase 11 head rows pass (45 face rows at each width plus 11 `.op` rows). The 90 face rows were run against pre-Phase-11 `332d9158`: 88 fail at the intended missing capability, while the two C4 `no_summary` control rows pass at both widths because the product already has no summary and no SEND well in that state. The same two C4 rows pass on head. Their observations are retained in `assets/story-06-runs/p11-r9-c4-control-final/`; the baseline red rows are in `p11-r9-red-332d9158/`, and the head matrix is `p11-r10-head-final/`. No guard or acceptance text was changed to conceal this. The first acceptance criterion stays unchecked pending an owner ruling on the C4 control exception.
- The full Phase 7–10 atlas run has 149/149 passing case×width rows, including the four Phase 9 steward `.op` cases walked on merged head `5e82b65d`. The final green matrix with full captures is `assets/story-06-runs/regressions-r7-head-final/`. Earlier blocked attempts, serial retries and the P8 quiet-host blocked→pass pair are retained in the neighboring `regressions-r5-post-merge-*`, `regressions-r6-*` and `regressions-r7-p8-current-*` directories. These disclose the timing flakes; no guard was weakened.
- The post-merge full suite used Python 3.13, `-n auto`, isolated HOME and basetemp, and excluded `tests/e2e/test_metal.py`: 28 failed, 13,524 passed, 116 skipped, 4 xfailed, and 119 errors. Exact serial reruns passed 146 of the 147 red node ids; the remaining Mermaid renderer node skipped in both serial attempts because the environment lacks a usable renderer. See `assets/story-06-proof/logs/full-r2-classification.json` and its linked logs. The post-merge Phase 7–11 graph and phase-atlas selection passed 357 tests: `assets/story-06-proof/logs/atlas-tests-r3-post-merge.log`.
- 2026-09-30 — dispatched in two parts by Muad'Dib. Part 1 covers the seven new document-kind `.op` file lifecycles and the four recorded Slack outcomes. Story 05 merged at `22c0acc4`; Part 2 added the real-face cases below. The retained walks and suite are now complete; the first acceptance criterion remains open only for the C4 baseline control recorded above.
- Part 1 proof and full-suite dispositions: [lane-06-astra.md](lane-06-astra.md). Final operation matrix: 11/11 pass; old-main matrix: 11 blocked before Send. Final focused tests: 411 pass. The inherited face-word guard remains for story 05.
- Part 2 face-case manifest: each listed case was run at **1440 and 393**. The three suffixes listed in a row are separate cases; each reads the hub outcome in the same observation. The merged story 05 faces are the targets.

  | Kind / seat | Case ids |
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
  | Design §6b: limit refusal remains on the well; assert the PREVIEW refusal's top-level integer size/limit | `case.p11.transition.slack_limit` |
  | Design §6b: changed preview, refresh, second Send | `case.p11.transition.preview_changed` |
  | Design §6b: last brief item leaves the Chair branch | `case.p11.transition.brief_last_ack`, `case.p11.transition.brief_last_defer` |

- `meeting_decision` remains `.op` only (design §6a); part 2 adds no face for it. The two last-item cases cover both gestures in the third §6b transition.
- Additional face cases from Muad'Dib's part-1 counsel: C4 `case.p11.meeting_summary.meetings_record.no_summary`; R7 removals `case.p11.r7.no_digest_slack` and `case.p11.r7.no_credentials_slack`; Slack destination form D1/D2a/D2b/D3 `case.p11.slack.destination.d1`, `.d2a`, `.d2b`, `.d3`. The four Slack outcome faces are `case.p11.slack.posted.face`, `.failed.face`, `.unknown.face`, `.too_large.face`.
- 2026-09-30 — round two: paid Muad'Dib's adopted C1–C3 in the prior commit. The Slack reason facts name the pinned replies; their two passing walks and four negative controls are retained in `assets/story-06-runs/p11-r2-slack-c1-c3/`, and `revision_source` identifies the provenance source. The three Meetings record rows follow the settled seats. Muad'Dib's r2 RATIFY is recorded in `checks/story-06-part1-built-muaddib-r2.md`.
- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
