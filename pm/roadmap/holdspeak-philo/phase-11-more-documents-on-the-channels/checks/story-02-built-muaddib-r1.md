# Check: Muad'Dib, counsel on built r1, 2026-09-30

Artifact: PR #709, PHILO-11-02 "the Slack channel and the aftercare rewrite", Astra's lane (session `01a0f10f-b5f5-78c1-9caf-789d80225786`), commits `49a04d9c8`, `d1fb22edf`.
Muad'Dib (Claude Opus 5.5, session https://claude.ai/code/session_01L3k9v1STCS3ur6wJYy5AgF) ran this check through a Fedaykin (Opus 5.5) reviewer. The reviewer read the lane's tree without writing to it and ran probes in a separate worktree with an isolated HOME. Muad'Dib adopts the report as his check.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS (short form; each was probed):
1. The size refusal contract holds at the producer (`channel_slack.py:421-444`, `channel_service.py:394-398`) and at the HTTP route (`web/routes/channels.py:77-80`). The fence turns red when `**context` is dropped from the route, and red when size/limit is dropped from the serializer (`KeyError: 'size'`). It matches #708's `channels.ts:452-454`.
2. Custody holds. The URL is held by HTTP only and stored in the native keyring slot `slack:<key_ref>`. Settings excludes `meeting.slack_webhook_url` from reads and writes in both serializers; the base-red capture shows the leak existed before.
3. Egress holds: the exact host and port are checked; the opener is bare; redirects are refused; exceptions become codes; the egress child's parent, principal and digest are asserted.
4. The pinned outcomes match the design: only an exact `ok` is POSTED, with no link and no id; FAILED comes only from the pins; everything else is UNKNOWN; there is no repost.
5. The posture auto-execute path is gone (the base-red shows the old path posted). D1 is parked honestly (`actuator_service.py:87-106`).
6. Minor: a historical *proposed* Slack proposal can still be approved into a dangling `approved` state that will never execute. It tells him something false.
7. The chat palette gains no tool.
8. Two of the three held reds are BRANCH reds, and story 06 does not own them. `test_philo_graph_reference::test_committed_join_validates` and `test_api_surface::test_clients_only_call_served_routes` are both red because the lane DELETED `POST /api/meetings/{meeting_id}/export/slack` (cited by the sealed `static-astra.json:69115`, and still called by `useMeetingData.tsx:183`). The face-word red (22 kind/code pairs) is face-owned, but no story's criteria name those pairs.
9. Fence weakening outside the ledger. Shared desk-actuator guards were deleted with the Slack test file, but the code they guard is still live for the webhook and GitHub targets (`actuator_service.py:29-44`):
   - source identity → desk subject;
   - must be a known qualified kind;
   - must resolve to live material;
   - identical content dedupes;
   - posture never widens an existing proposal;
   - decision on an unknown proposal → 404;
   - `test_github_approvals_keep_todays_behavior`.
   `test_trust_destinations.py:29-35` dropped the doctor-naming assertion instead of switching its vehicle.
10. The test doubles are honest: the recording edge replaces only the HTTPS open, and the documents are minted by the real producers.

CONDITIONS:
C1. PARK the meeting export route; do not delete it (owner law: never delete, park). `POST /api/meetings/{meeting_id}/export/slack` answers `slack_moved_to_channel` in the same D1 shape as the desk route. The lane's own tests assert the named refusal with `calls == []`. Regenerate openapi and the graph. Guards 1 and 2 must turn green without editing either guard.
C2. Rehome the deleted shared guards (finding 9) onto the webhook target, and restore the meeting GitHub approve-does-not-execute guard. Restore the trust-doctor naming assertion with `companion_webhook_url`.
C3. Give the face-word red a written owner. Muad'Dib rules: story 05 owns it. Add the 22 pairs from `missing-face-words.json` to story 05's criteria by name, and correct the ledger's "held for 06" wording. Main then carries one named red with a named payer (CI does not gate merges).
C4. Minor: `MeetingAftercareService.decide_proposal` refuses `approved` when `target == "slack"`, with `slack_moved_to_channel`. Reject still works.

MISSED: the ledger omits the lost shared guards; guard ownership was asserted without reading the owning stories; orphaned keychain slots are never cleaned (noted only, Tenet 1).
TUESDAY: once he has a webhook and story 05 draws the Destinations form, a saved digest or follow-up posts to Slack. Until then the old Slack rows simply disappear.
UNKNOWN: no real keychain round trip and no live Slack post were observed; C1's regeneration effect is reasoned, not run; no full suite yet (Muad'Dib runs it after the conditions are paid and main is merged).
