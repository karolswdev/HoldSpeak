# PHILO-11-05 - The faces: the well on every document, Destinations with Slack

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** backlog
- **Depends on:** PHILO-11-03 ratified; PHILO-11-04; PHILO-11-02 for the Slack face
- **Unblocks:** PHILO-11-06, PHILO-11-07
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/faces.md` F2, F5, F6, F7, F8; rulings R4, R5, R7
- **Design:** `design/document-sources.md` sections 4–6
- **Canvas:** A, B, C, D, as ratified in story 03

## Problem

A brief, a decision or a meeting summary has no Send (faces.md §1). The meeting record carries an old Slack door that proposes instead of sending (§4); Settings carries a second Slack home under Destinations (`web/src/pages/cores/SettingsCore.tsx:2311-2338`).

## Scope

- **In:** the species composed, as the canvases draw it, on: the Chair BRIEF section (`web/src/desk/chair/ChairHome.tsx:1304-1420`) and the Intelligence BRIEF view (`web/src/desk/pullouts/views/BriefView.tsx`); the decision window (`web/src/desk/pullouts/DecisionPullout.tsx`), the Room's DECISIONS & COMMITMENTS rows (`web/src/features/project-room/ProjectRoomCore.tsx:1431-1530`) and Intelligence → DECISIONS (`web/src/desk/pullouts/views/DecisionsView.tsx:124`), both `decision_record:<id>`, including Room rows marked `source="meeting"` (Astra r1 finding 1); no well for `meeting_decision` unless story 03 found a rendered seat (design §6a); the Meetings record under SUMMARY (`web/src/pages/cores/history/MeetingDetail.tsx:171-173`), the meeting window (`web/src/desk/pullouts/MeetingPullout.tsx`), the Chair MEETINGS row. Destinations with Slack (`web/src/pages/cores/connections/Destinations.tsx`; `web/src/features/channels/channels.ts`: `slack` in `CHANNELS`, `CHANNEL_WORD`, `SENT_WORD`), one list, no filter (R5). Removed: `AftercareGadgets` and its mount (`web/src/pages/cores/history/MeetingDetail.tsx:190-195`), the `Slack webhook` row in Credentials (`web/src/pages/cores/SettingsCore.tsx:84`, `:2311-2321`). Copy on the decision window unchanged (R8). The desk's free-text Slack affordance parked (`web/src/desk/contextual.ts:130`; D1).
- **Out:** a well on the other briefs (charter Out); the MD and SRT downloads (unchanged, faces.md F9).

## Acceptance criteria

- [ ] Every ratified board built and fenced through the real hub at 1440 and 393; the face's outcome equals the hub's record and receipt in the same fence.
- [ ] Each face sends its own `document_ref`; a fence per face reads the prepared row's `document_ref` (a Room row marked `source="meeting"` sends `decision_record:<id>`).
- [ ] Rendered-transition fences at both widths (design §6b): the over-limit Slack refusal word (never `NO ANSWER`); `preview_changed` → a fresh preview → another press that sends; the Chair after its last brief item is triaged, the well still there. The same send receipt (state, target, time) stays on screen after the Chair's branch change at both widths and equals the hub's send row; well presence alone is not the receipt assertion (Astra canvas check r2, condition 2).
- [ ] Story 05 owns the face-word fences for every exact pair in `assets/story-02-logs/missing-face-words.json`: `[unknown, ack_missing]`, `[failed, action_prohibited]`, `[failed, channel_is_archived]`, `[failed, channel_not_found]`, `[failed, invalid_payload]`, `[failed, payload_too_large:slack]`, `[unknown, plan_refused]`, `[unknown, rollup_error]`, `[refused, slack_channel_label_invalid]`, `[refused, slack_key_ref_invalid]`, `[failed, slack_key_store_locked]`, `[refused, slack_key_store_locked]`, `[unknown, slack_key_store_locked]`, `[failed, slack_key_store_not_native]`, `[refused, slack_key_store_not_native]`, `[unknown, slack_key_store_not_native]`, `[failed, slack_webhook_invalid]`, `[refused, slack_webhook_invalid]`, `[unknown, slack_webhook_invalid]`, `[failed, slack_webhook_missing]`, `[refused, slack_webhook_missing]`, `[unknown, slack_webhook_missing]` (22 pairs total).
- [ ] No verb offers the parked free-text Slack send.
- [ ] Nothing covers Send at 393 or in the real-width decision and Meetings windows at 1440 (F7).
- [ ] A Slack destination saved from the form; the webhook never shown again; POSTED with no link.
- [ ] No `DIGEST → SLACK` row and no `Slack webhook` Credentials row on screen, with or without a Slack destination.
- [ ] Every verb the library Button; the egress chip on each row that leaves the machine; no modal; the web baseline zero branch-new.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days.

## Test plan

- **Glass:** Playwright fences through the real hub on an isolated HOME at both widths; shots under `.tmp/evidence-shots/` unless the story ships them.
- **Web unit:** the Destinations form's Slack fields.

## Notes

- 2026-09-30 — PHILO-11-02 counsel C3 assigns the 22 exact missing face-word pairs above to Story 05. This criterion update ships atomically with the Story 02 counsel response; Story 05 remains backlog, and no face implementation ships in that commit.
- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
