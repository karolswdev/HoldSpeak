VERDICT: BOUNCE — do not merge PR #659 at `86ec4ee5`.

FINDINGS:

1. **The grant body can replace the intended agent.** `PUT /api/settings/remote/delegations/path-agent` with `{"agent_identity":"body-agent"}` succeeds and grants **body-agent**. The receipt confirms `target_ref=agent:body-agent`. The body overwrites the path identity in `holdspeak/services/desk_delegation.py:46`. [Reproduction](/tmp/astra-philo702.BmMpzE/scroll-pointer.txt:3). Refuse the conflicting field; the declared body is `{expires_at?}`. **Fails Tenets 3/7 and the intended authority boundary.**

2. **Identifiable consequential refusals still escape admission.** Independently reproduced:
   - Missing HTTP supersede: **404, zero operations/receipts**; MCP equivalent: **one refused operation/receipt**.
   - Existing decision, supersede body `[1]`: **422, zero operations/receipts**.
   - Decision creation with `tags:42`: **500, zero operations/receipts**.
   - MCP deletion of a real Thought-owned note with an unexpected field—or an authority field—leaves **zero operations/receipts**.

   The first paths escape through `holdspeak/web/routes/decisions.py:88` and adapter coercion. The last is an unchartered exemption: `holdspeak/operations.py:1501` excludes every stored-state admission condition, even when the supplied note ID identifies a Thought. [HTTP/MCP counts](/tmp/astra-philo702.BmMpzE/probe.txt:15), [Thought refusals](/tmp/astra-philo702.BmMpzE/thought.txt:1). **Fails Tenet 3, R2 and XI.2.**

3. **Some receipts exist but the caller cannot retrieve them from the response.** Non-object HTTP decision creation and MCP `zone.file` missing `directory_id` each produced one refused operation and receipt, but returned neither `operation_id` nor `receipt`. [Proof](/tmp/astra-philo702.BmMpzE/probe.txt:11). Their adapters discard the returned receipt at `holdspeak/web/routes/primitives/decisions.py:60` and `holdspeak/mcp/tools.py:910`; non-object MCP and palette refusals have the same problem. The inherited tombstoned-Thought HTTP 500 may be ledgered, but carrying its newly required receipt remains in scope. **Fails Tenet 3 and the readback acceptance criterion.**

4. **The carried scroll-edge defect remains.** At 393, minimally scrolling “Issue credential” into view leaves its painted face visible, but both lower target corners hit `surface-footer-layout`—confirmed by `elementFromPoint` and actual pointer events. [Measurements](/tmp/astra-philo702.BmMpzE/scroll-pointer.txt:2), [shot](/tmp/astra-philo702.BmMpzE/glass/scroll-edge-393.png). The committed `tests/e2e/test_philo7_02_grant_glass.py:328` scrolls fully down and checks an orphan Stop above the subsequent Settings content; it does not reproduce the carried position. **Fails Tenets 5/6 and UX-CANON C.**

5. **Generated evidence and completion records need correction.** `philo_api_reference.py --check` fails locally and in [Documentation Navigation CI](https://github.com/karolswdev/HoldSpeak/actions/runs/36185652790/job/108238239259). The drift is the PUT/DELETE delegation routes’ consumers. [Local comparison](/tmp/astra-philo702.BmMpzE/api-drift.txt). The story says done while its acceptance boxes remain unchecked, including the contradicted “No other refusal where main accepted” criterion at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-02-membership-and-decisions-under-article-xi.md:52`. F23’s missing rendered fence is honestly disclosed, but remains owed. **Fails Tenet 3 and Article IX’s evidence requirement.**

6. **Rulings: (a) ratified; (b) lawful, with an explicit amendment.** Storage-LIVE orphan rows match the ratified wire contract and disappearance behavior; do not restore historical REVOKED rows. NODE and missing-principal refusals are appropriate consequences of the settled admission model: NODE has only `NODE_LINK`, and an unauthenticated caller cannot supply legitimate authority. `holdspeak/principals.py:46`. No additional owner policy ruling is needed for these direct-call cases. However, they are changed behavior: amend the story and phase record, rather than retaining “ONE named change.”

7. **The principal implementation is supported by independent verification.** **244 scoped tests passed**, including lifecycle conflicts, real remote credentials, readback, exemption and density fences. Five writes over each transport—including supersede and KB rename-plus-members—each produced exactly **one operation and one receipt**. My T9 receipt-INSERT fault left zero grant rows, the operation `claimed`, and zero terminal operations lacking receipts. My stronger restart probe killed the hub with an actual request already waiting; the new process produced `indeterminate/hub_restart_during_decision`, then filed under the original grant. [Run](/tmp/astra-philo702.BmMpzE/run.txt), [additional fences](/tmp/astra-philo702.BmMpzE/rig-run.txt), [fault](/tmp/astra-philo702.BmMpzE/probe.txt:26), [restart](/tmp/astra-philo702.BmMpzE/restart.txt).

   The module split is an honest separation of responsibilities, not a guard workaround. Residual **284 = 223 MCP + 61 HTTP**, public tools **229**, and OpenAPI/graph checks agree. The rig now carries Thought-delete revisions and executes the admitted delete: lane-01’s delete-carriage issue is paid. [Proof](/tmp/astra-philo702.BmMpzE/thought.txt:3).

CONDITIONS:

1. Fix findings 1–3; retain the named errors and protocol exemptions. Add independent failing fences for each reproduced path, checking response fields, durable receipt and unchanged domain state.
2. Repair the actual scroll-edge position and fence it. Commit the missing rendered expiry/OFF/disappearance cases; my probes confirm those states currently work at both widths.
3. Regenerate the API reference, reconcile the authority amendment and acceptance records, file the inherited HTTP-500 debt, and record this check.
4. Complete and inspect CI before merge.

MISSED:

1. Highest owner cost: a grant can target a different identity from its URL.
2. Counting receipts in SQLite does not prove the caller receives a usable receipt reference.
3. A multi-path test failing on its first call does not demonstrate red coverage of every later path.
4. The committed restart test creates its waiting operation **after** killing the first process (`tests/unit/test_philo7_grant_restart.py:139`). Preserve the stronger interrupted-request reproduction as its fence.

TUESDAY: The grant controls and surviving receipt are usable in the observed states; inaccessible refusal receipts and the clipped phone target still interrupt the job.

UNKNOWN: Full-suite results remain pending; I did not rerun the historical mutation campaign or the reported 1,946/2,872 suites. The actual existing J1 atlas case passed at both widths; new desk atlas coverage belongs to story 03. No owner-device sitting was performed. The worktree remains unchanged; all new evidence is under `/tmp/astra-philo702.BmMpzE`.