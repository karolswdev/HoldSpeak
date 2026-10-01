VERDICT: RATIFY-WITH-CONDITIONS
F1: the new cases are real. Re-run in a separate worktree: too_large.op, meeting_decision.op and failed.op pass; provenance is clean and loopback only; one opener with the RecordingEdge; memory keystore.
F2: the Slack FAILED case is weak. It passes when the edge serves nothing: the hub records reason `connect_refused` because an unmatched request raises ConnectionRefusedError (graph_walk.py ~2939). With a changed fixture (404 channel_not_found) it also passes. UNKNOWN (atlas-phase11-slack.json:493) has the same gap.
F3: "11 blocked on 332d9158" is honest (the 404 slack-webhooks route; preview took update_id only), but it does not show that each kind is missing. The rig does not retain the failing step's response.
F4: the rig changes weaken no existing guard. Two widen the rig's trust surface, both disclosed: provenance revision and dirty flag from the environment (graph_walk.py:365), and the patched ModelLibraryApplicationService._profile_body (graph_walk.py:2787). The 149 combinations include two cases (p7 zone_create, p8 delete_twice) re-run until green; they are disclosed flakes.
F5: queue_meeting_intelligence is a repository call labelled `cli`. Accepted as disclosed.
F6: the face-word red is from main 8a6b807d; story 05 owns it.
F7: tests/unit/_philo11_proof_inputs.py:13 imports rig_run.py and retain.py from an evidence assets folder. Low severity.
CONDITIONS:
C1: add fact sends.0.reason = invalid_payload to case.p11.slack.failed.op, and sends.0.reason = rollup_error to case.p11.slack.unknown.op. Re-run both on the head. Show that each now fails when the edge serves nothing or a different pinned pair.
C2: fix the planned part-2 IDs in story-06-the-atlas-cases.md:50-51. There is no "aftercare" seat; R7 removed those rows. Digest and follow-up are forms in the one meeting well's picker (boards C5, C5b, C5c on the Meetings record). Add the Meetings record seat for the summary (C1, C2, C3, C3b).
C3: when the revision comes from the environment, stamp it in provenance (for example `revision_source`).
RECOMMENDED for part 2, not conditions:
- add a fact on the PREVIEW refusal's integer size/limit, because the face reads preview;
- run T1 on a meeting summary as drawn, not on project_update;
- add face cases for C4 (no summary, no well), the R7 removals (0a/C5, D4) and the Slack destination form (D1, D2a, D2b, D3), unless story 05's fences already own them;
- consider moving the proof-input loader out of the evidence folder (F7).
