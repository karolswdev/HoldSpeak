VERDICT: **RATIFY-WITH-CONDITIONS** — PR #687 at `7a169aa3`. The product changes are sound; one face-evidence gap needs correction before merge. Phase closure also requires story 05.

FINDINGS:

1. **The 393 ITEMS proof overclaims visibility.** `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/final/20260928T172621Z-room-job/shots/room-items-393.png` is byte-identical to the head shot. The risk’s title, likelihood and impact are below the visible area. The collector accepts any element with positive height, including off-screen elements, and the shot scrolls only the first item into view. Evidence: `scripts/philo9_room_job.py:731`, `scripts/philo9_room_job.py:887`. This fails **Tenet 3’s verification of the usable face and Article IX**; it does not establish a product-layout defect.

2. **The four sessions are genuinely cold on the retained evidence.** Distinct session IDs, empty working directories, separate HOME/CODEX_HOME directories containing only authentication at launch, required isolation flags, no resume, and no repository instructions. I inspected the rollout calls: catalogue inspection and HoldSpeak calls only. All **24 MCP calls** pair with hub exchanges; unmatched exchanges are initialization and catalogue discovery. Four sessions faithfully implement the three legs, with the agent restarted after the grant. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/final/20260928T172621Z-room-job/legs.json:1`, `scripts/philo9_room_job.py:146`.

3. **The content proof is substantive.** I rechecked the retained responses and a temporary copy of the database, whose integrity check passed. The milestone, risk details, draft-only policy, completed runs, published bodies and delivery receipts exist. Priya and Tomas have separate delivery rows and operations; the agent’s run/publish operations name its grant, while delivery remains refused. The three-day lateness is correct for this fixture. **323 focused tests passed**, including mutations of real retained records; the regeneration integration test also passed. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-06-shots/final/20260928T172621Z-room-job/owner_job/readbacks.json:1`, `scripts/philo9_room_job.py:277`.

4. **Change (a) is correct, minimal, and an intentional API change.** Owner authorization, scheduler handling and authorized steward children precede the new branch. Direct agent operations outside run/stop/publish now return `owner_principal_required`; grantable operations retain their delegation refusals. Rights, refusal status and receipt production remain intact. Clients matching the old error code must account for the change; it is not merely wording. I found no remaining affected production caller relying on that equality. Both real-credential tests fail when the base revision’s `authorize` method is substituted in memory and pass on this head. Evidence: `holdspeak/kernel/project_codec.py:68`, `holdspeak/kernel/project_codec.py:93`, `tests/unit/test_philo9_owner_only_code.py:40`.

5. **Changes (b) and (c) are appropriate.** Discovery accurately directs project lookup to the list; the cold session selected it. Receipt labels distinguish missing authority from owner-only authority and retain outcome rendering. Evidence: `holdspeak/operations.py:1368`, `holdspeak/mcp/families/memory.py:16`, `web/src/desk/surface/egress.ts:105`.

6. **The three face observations do not block this job’s close.**
   - **RECEIPTS 10:** deliberate bounded summary; earlier receipts remain stored. Clarifying that these are recent receipts is a useful follow-up, not grounds for new pagination in this phase. `holdspeak/services/project_service.py:2195`.
   - **IT:** inherited fallback abbreviation from `item`, not a meaningful milestone emblem. A low-severity **Tenet 4** defect; ledger it. The adjacent title and lateness remain clear. `web/src/features/project-room/ProjectRoomCore.tsx:133`.
   - **Regenerate:** valid behavior. It creates a new draft and preserves the published update; the integration test verifies this. “New draft” could communicate the result better. `holdspeak/services/project_update_service.py:1878`, `tests/integration/test_update_routes.py:176`.

CONDITIONS:

- **Before merge:** capture the complete risk row at 393, assert actual visibility within the unobscured viewport, and correct the evidence claim. The retained cold sessions need not be repeated for this screenshot repair.
- **Before phase close:** complete PHILO-9-05’s actual atlas reruns and equivalence evidence. It remains `backlog` with unchecked criteria; this closing rehearsal does not replace it. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-05-the-atlas-cases-for-the-room.md:23`.

MISSED:

1. Historical owner-only refusals retain `project_delegation_required`; the new renderer will call those **NO GRANT**. Nonblocking historical-display debt, but avoid claiming all old receipts now distinguish the two reasons.
2. The 393 Stop reload proves persisted removal, not receipt survival during that click. This is disclosed and supported separately by story 07’s rendered transition tests at both widths. `tests/e2e/test_philo9_07_project_grant_glass.py:517`.
3. The [PR description](https://github.com/karolswdev/HoldSpeak/pull/687) still describes rehearsal one and pending face work; update it to the reviewed result.

TUESDAY: Yes—the owner can perform and recover this project job; the phone evidence must actually show the risk before calling every result observed.

UNKNOWN: No independent full-suite, fresh Codex-session or atlas rerun in this review. Clipboard and external delivery remain outside this proof; owner review remains recorded as pending. CI did not determine my verdict. The tree is unchanged.