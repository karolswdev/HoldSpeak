VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The separate grant table is justified. — Tenet 1 satisfied.** I would not require generalizing Phase 7’s table in this phase. Its operations are already stored per row; the actual limitation is its agent-only uniqueness, lookup and replacement behavior. Adding `project_id` alone would leave those semantics wrong: granting one project could replace another grant. Evidence: `holdspeak/db/schema.py:1850`, `holdspeak/kernel/desk.py:127`, `holdspeak/kernel/desk.py:192`.

   A sibling table avoids changing existing grants and their scope. The two nullable delivery columns and that table are a proportionate additive schema for the recommended cardinality. Reuse the existing hashing and atomic receipt machinery; a second lifecycle engine is unnecessary. The reconciler already supports missing columns and tables: `holdspeak/db/reconcile.py:655`.

2. **The grant needs an explicit execution contract for agent-started children. — Tenets 3/7; Article XI.** The proposed bound is sufficient for the intended job, and **agent publication does not conflict with Q0**: publication remains local; the owner confirms delivery.

   However, the existing kernel rejects an agent’s child operation unless its ancestry establishes a live owner continuation—even when the agent is the parent’s own principal. A project grant on `run_steward` does not automatically repair this. Evidence: `holdspeak/kernel/causation.py:28`. The charter promises admitted children but its lifecycle beat explicitly addresses policy authority only for scheduler-started runs: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:203`.

   Settle how the agent’s grant and the owner’s policy authorize each child, including effects whose direct operation is outside the grant. Today proposal application passes the initiating principal into `decide_proposal`: `holdspeak/services/project_steward_service.py:1313`. State the revoke/expiry cutoff without manufacturing an owner principal.

   Also, “stop a run it started” is stricter than agent × project × operation. The proposed admission test omits run ownership. The existing producer already records `requested_by`, so this needs no additional column: `holdspeak/services/project_steward_service.py:460`. Resolve project scope from the stored run/update and fence another actor’s run in the same project.

3. **Delivery is minimal and substantially truthful, with one wording correction and one persistence boundary. — Tenets 1/3; Article VI.** Copy, optional To, owner-only Mark delivered and a stored confirmation implement Q0. Admission is appropriate for the proposed final declaration; the click itself supplies approval.

   But “its receipt is the proof of delivery” overstates what HoldSpeak knows. It proves **the owner recorded confirmation**, not that a recipient received anything. Define `delivered_at` as the confirmation time and correct that wording: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:152`.

   The existing repository rejects edits to published updates. Specify a narrow delivery-metadata write while retaining immutable body, claims and source manifest; do not relax the general published-update guard. Evidence: `holdspeak/db/updates.py:244`. Two columns suffice; no delivery-history table is needed for the recommended single confirmation.

4. **Story 01’s acceptance reaches forward into its dependents. — Tenet 3; Article XI.** Story 01 requires delivery refusal **even with a project grant**, while story 07 creates that grant after story 02; story 02 supplies the general admission path after story 01. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-01-the-rooms-operations-on-the-contract.md:24`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-01-the-rooms-operations-on-the-contract.md:39`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-07-the-project-delegation-grant.md:6`.

   Assign Mark delivered’s admission to the same landing as its exposure. Move the real-grant refusal case to story 07. A fabricated grant in story 01 would not prove the promised boundary.

5. **The new canvases need return and disappearance states. — Tenets 2/3.** The owner copies, leaves to deliver, then returns. Existing Copy feedback expires after two seconds: `web/src/features/project-room/update/useUpdateController.ts:169`. The charter’s “after a successful Copy” must not become a transient gate that hides Mark delivered when he returns. Keep confirmation reachable for the published update without adding persisted clipboard state.

   Likewise, a restart can leave a live grant without a credential row. Phase 7 already exposes such grants and their stop action: `holdspeak/services/desk_delegation.py:109`. Explicitly carry that state into the project-grant canvas, including Remote Access OFF. “On the credential row” alone is insufficient.

6. **The closing contract contradicts its story. — Tenet 3.** The charter specifies **two sessions**; story 06 specifies **three**, separating owner creation, owner find-it-cold and agent execution. Use the latter consistently: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:267`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-06-work-in-a-project-room-without-the-repo.md:20`.

   Reading `body_md` and recording a simulated owner confirmation proves the MCP contract. It does not prove clipboard behavior or external delivery. Keep those evidence claims separate.

CONDITIONS:

- Before briefing story 02, settle agent-run child authority, policy bounds and execution cutoff; carry them into story 07’s beat and real-credential fences.
- Before briefing story 01, resolve delivery admission ownership, move the future-grant test, and specify confirmation semantics plus the metadata-only write.
- Before canvas ratification, include returning after Copy and grants without credential rows; fence the rendered transitions.
- Reconcile the closing contract to three sessions and explicitly include story 07’s cases in atlas assembly.

These are charter/design conditions, not demands to build before ratification. Q0–Q3 stand.

MISSED:

1. **Highest cost:** the agent parent can be admitted while its children remain unauthorized.
2. **Owner interruption:** confirmation or grant controls can disappear when he returns or restarts.
3. **Delivery rework:** published-row immutability and the story dependency order need explicit treatment.
4. **Evidence drift:** two versus three sessions, and confirmation versus actual delivery.

TUESDAY: Yes, conditionally—he can copy, deliver elsewhere, return and confirm; his agent can draft and publish once child authority is settled.

UNKNOWN: Reviewed `0066bebc` in fresh worktree `/Users/karol/dev/tools/wt-philo-p9-check-r4-0066bebc`. `dw check holdspeak-philo` passed; the worktree is clean. This was a charter and code-path review: no fresh browser/atlas walk, runtime probe, cold-client rehearsal or full suite. The new behavior and canvases are not built. No repository files changed.