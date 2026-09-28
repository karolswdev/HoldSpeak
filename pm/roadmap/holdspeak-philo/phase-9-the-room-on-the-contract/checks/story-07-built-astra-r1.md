VERDICT: **DO-NOT-RATIFY**

PR #685 at `7a432a29`; story 07 delta only. Two reproduced blockers. Repository trees unchanged.

FINDINGS:

1. **Stop-own-run checks the identity string but loses the actor kind.** A real PROJECT credential named `owner-session`, with a real project grant, successfully stopped an OWNER-created run over **both MCP and HTTP**. Both runs acquired `stop_requested_at`; both stop operations received successful receipts. The comparison at `holdspeak/kernel/project_codec.py:100` cannot distinguish those actors because `holdspeak/services/steward_contract.py:238` stores the same requester string. This breaks Q2/R4-1’s exact bound and **Tenet 3**. [Reproduction and receipts](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-probes.log:1).

2. **Archiving a project hides Stop while its grant remains effective.** Settings still displays `RUN AND PUBLISH ALLOWED`, but its disclosure lists only active projects: `web/src/pages/cores/SettingsCore.tsx:910`, `web/src/pages/cores/SettingsCore.tsx:1028`. I reproduced the missing control at [1440](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-archived-1440.png) and [393](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-archived-393.png). The agent could still publish an existing draft under that grant: operation `op_941101efd3b74a3a8d68491ae3ee2f52` succeeded. This fails **Tenet 3**. The active-project-only omission exists in the canvas too; the build faithfully carries it forward.

3. **The remaining tested authority and lifecycle boundaries held.** Independently collected and ran the 53 story tests: [53 passed](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-tests.log:1). Additional real-credential probes covered outside-bound HTTP/MCP operations, including HTTP-only Door operations, and mid-run expiry/regrant. Frozen G1, approval/claim checks, restart/reissue, and agent actor preservation held in these cases. Grant/revoke remain owner-only and HTTP-only. The implementation reuses Phase 7’s checks, hashing and atomic receipt transaction. Four additional interruption probes verified durable-first credential revocation across **both owner routes**, including rollback during the second grant write, interruption before token removal, and successful retry. [Interruption proof](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-durable.log:1).

4. **The supplied face states match the ratified canvas at both widths.** I inspected all 24 built shots: set A words, Projects disclosure, DESK naming, orphan Stop with transport ON/OFF, and receipts surviving removal of the last row. The `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-shots/11-credential-revoked-393.png` preserves the receipt. Finding 2 is the missing lifecycle state.

5. **The model gap is acceptable as an explicit deterministic-only limit for this story.** Normal steward drafting `holdspeak/services/project_steward_service.py:1510`. When I exercised model selection through a real deployment-revision producer, broker and inference runner, `inference.invoke` was refused with `parent_continuation_identity_required`; no engine dispatched, and the draft became `deterministic:no_output`. [Observed proof](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-685-review-soh0lt8f/counsel-model.log:1). Replace “likely refused/unverified” in the beat with this result. Model drafting needs its own admission and causal-chain proof before it is enabled; it need not expand this fix.

CONDITIONS:

- Bind stop ownership to the stored authenticated **actor kind and identity**. Add real-producer regressions for same-string owner/agent and scheduler/agent identities over both transports; retain successful own-agent stop.
- Keep existing LIVE grants visible and stoppable when their projects are archived. Archived rows need Stop, without offering new grants. Update the canvas/beat and fence **archive → Stop → retained receipt**, ON/OFF, at 1440/393.
- Show those regressions fail before the fixes and pass afterward. Record this verdict and the observed model limitation with the corrected evidence.

MISSED:

1. Highest owner cost: a matching name was treated as the same authenticated actor.
2. Next: authority survives longer than the active-project picker’s contents.
3. Lower: absent model execution was mistaken for an inability to verify admission; that boundary can be tested without a model.

TUESDAY: The drawn states support the job; after archiving a project, the owner cannot stop that project’s grant from its Settings row.

UNKNOWN: I did not independently rerun the full repository suite, all mutations, or actual atlas walks, and did not execute a model. The unnamed standalone Vitest failure remains unclassified; the later recorded 2931/2931 pass does not establish its cause. The single-footer-receipt limitation remains the named backlog item. CI status did not determine this verdict.