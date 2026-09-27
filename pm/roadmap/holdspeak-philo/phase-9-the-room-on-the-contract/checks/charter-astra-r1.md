VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The closing job promises delivery that Publish does not perform. — Tenets 3/7.** The charter promises “send my update” and an update to his boss. `publish_update` changes the local lifecycle, revision and ledgers; it has no recipient or delivery operation. The face separately offers Copy. Evidence: `holdspeak/services/project_update_service.py:1901`, `web/src/features/project-room/update/UpdatePosture.tsx:580`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-06-work-in-a-project-room-without-the-repo.md:18`.

   Recommend **“draft and publish the update in the Room”**, with owner ratification of that boundary. Actual delivery is a separate scope choice. A discovery fence must not teach the client that local publication means sending.

2. **The source-addition wall is deeper than F5, and F15 identifies the wrong working path. — Tenets 2/3.** I minted suggestions through the real transcript scanner and persistence service, then exercised the real HTTP routes:
   
   - GitHub `example/payments`, URL-encoded as the face does: **404**.
   - Jira `PAY-123`: **200**, `accepted_no_watch`; the suggestion became accepted, but no resource or watch existed afterward.

   The routes use a single-segment `{ref}` and accept the suggestion before attempting resource creation; that failure is swallowed. Evidence: `holdspeak/web/routes/projects.py:608`, `web/src/features/project-room/api.ts:178`. DB: `source_suggestions.id=ssug_3af40e1c8b90`, `status=accepted`; zero `project_resources` and `connector_watches` rows in the [isolated probe database](/private/tmp/astra-p9-hub.JCgKC4/.local/share/holdspeak/holdspeak.db).

   The normal suggested-source row already has wired Add and Dismiss buttons at `web/src/features/project-room/ProjectRoomCore.tsx:976`. F15’s handlerless button belongs to a different branch. Replace “the tools answer” with a durable, truthful source-addition outcome, including failure. Do not close this by fixing `svc` alone.

3. **Q1 repeats Phase 7’s blanket “plain edit” mistake. — Tenets 3/7; Article XI.** Archive pauses watches and disables unattended steward policy in the same transaction. I reproduced the policy changing from enabled to disabled through authenticated MCP, with zero kernel operations. It is not merely a label edit. Evidence: `holdspeak/services/project_service.py:3023`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:151`.

   Two more classifications need correction:
   
   - `project.watch.test` fetches a source **and persists test state/results**; the census calls it “no durable change.” `holdspeak/services/watch_service.py:499`, `holdspeak/services/watch_service.py:595`.
   - Bare create and Door create have different effects: the Door creates and arms watches, then baselines them. A named descriptor field alone does not settle their different admission requirements. `holdspeak/services/project_service.py:2542`, `holdspeak/services/project_door_service.py:308`.

   Recommend Q1(a)’s **effect-based approach**, after replacing its prose list with an explicit operation/argument/effect table. Q1(c) must be described as migration with outstanding constitutional debt; it cannot satisfy the Article-XI exit. Preserve existing lower-level admission paths and avoid duplicate admission.

4. **Q2(a) says “Not in this phase” while preserving agents’ ability to change authority. — Tenet 3; Article XI.4.** A real PROJECT credential issued through Settings successfully called `project.configure_steward(unattended_enabled=True)` and `project.archive`. No delegation was granted; zero kernel rows resulted. Evidence: `holdspeak/mcp/families/project.py:1419`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:155`; probe project `proj-fbdfc2b2d82c`.

   The genuine fork is: **owner execution with named refusals for undelegated consequential agent writes**, or **bounded project delegation**. Recommend the former for this slice, explicitly ratifying the behavior change. Keep genuinely exempt operations compatible. An owner-token Codex rehearsal proves OWNER behavior only.

5. **Q3 is a genuine fork, but its alternatives do not propagate into the stories. — Tenets 2/3/7.** Q3(c) removes items from the job, while story 03 still requires a visible overdue milestone and story 06 still requires adding a milestone and risk. The Out list also puts the add-item face under Q3(b), although (b) explicitly includes it. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:72`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:157`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-03-the-rooms-face-tells-the-truth.md:30`.

   Q3(a) is a reasonable small recommendation **if it plainly says owner-authenticated MCP is the item-entry path**. “By voice or through an agent” promises paths this charter does not prove. Otherwise choose the small in-world Add control.

   The closing job also needs a substantive outcome: a named attention item and a named steward result. “Nothing needs you” plus a completed run with no permitted actions can satisfy today’s wording. F3 correctly identifies false counts, but “did nothing” is too broad: COMPARE opens a review even when ACT performs no actions. `holdspeak/services/project_steward_service.py:860`.

6. **The census arithmetic is correct and reproducible; it is not a complete capability inventory.** I reproduced:

   - **284 = 223 MCP + 61 HTTP**; **229 public tools**.
   - **61 project-adjacent MCP**: 42 project, 13 provider, two connection, four adjacent tools.
   - All **38 distinct proposed MCP identities** and **six HTTP tuples** exist.
   - **284 → 240–246** is correct, with HTTP constructors retained as MOVED rather than paid.

   `scripts/residual_census.py --check` passed. Product code and census inputs are unchanged between `b37dc2fb` and `3066dccb`. Evidence: `scripts/residual_census.py:66`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:80`.

   Including provider, connection and nudge tools in the adjacent inventory is right. Deferring the ten setup tools and 13 provider tools is reasonable for a bounded job, provided “parked” means **migration deferred**, not unavailable: those MCP tools remain callable. Lack of accounts is a verification limit, not itself a scope justification.

   Add an explicit HTTP capability exception inventory. For example, update regeneration remains callable from the touched face and can request a model, but is absent from both the update enumeration and named Outs. `holdspeak/web/routes/project_updates.py:134`.

7. **Six stories and two canvases are defensible; the avoidable cost lies elsewhere. — Tenet 1.** Keep the Room canvas and the owner-mandated D2 canvas. Cut duplicate atlas authoring: each repair should ship its active fences/cases; story 05 should assemble and rerun coverage and equivalence.

   The seven item/resource tools are **new public exposure**, although their underlying capabilities exist. They need explicit scope, schema, palette and authority ratification in this charter—not another phase or framework. Do not leave those choices implicit in “first commit.” Reuse the existing receipt-read contract.

   Before story 02 builds, require one short lifecycle design for the asynchronous steward: pending handle, run/effect parentage, terminal receipt, stop and recovery. The current route returns an ID and starts a daemon thread; it cannot inherit synchronous Phase 7 completion semantics without explanation. `holdspeak/web/routes/steward.py:94`.

   Also assign the health/receipt backend edits explicitly: story 03 is described as “face files only,” but its promised repairs require `ProjectService`, already owned by story 01. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:128`.

8. **The red-first exits are mostly feasible, but the blanket requirements are false. — Tenet 3; Article IX.** The grounding contains diagnostic measurements, not executable failing assertions. For example, its D2 probe records numbers and exits normally. `docs/internal/philo/phase-9/grounding/probes/d2_probe.py.txt:139`.

   Story 05 requires every face case to fail on main at both widths. Yet the grounding explicitly records the Steward button and row menu working at 1440. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-05-the-atlas-cases-for-the-room.md:23`, `docs/internal/philo/phase-9/grounding/README.md:198`, `docs/internal/philo/phase-9/grounding/README.md:238`.

   Require **behavioral red at each affected state/width; preservation green at unaffected widths; mutations for structural invariants**. Reject missing-symbol and unknown-tool failures as behavioral proof. Fence rendered receipts after transitions, with real producers, and change existing atlas words with the corresponding product change.

9. **Story 06 specifies cold context well, but needs an exact launch and outcome contract. — Tenet 3.** Retain its scratch homes, one MCP server, no repository reads, fresh find-it-cold session and redaction requirements. However, the precedent driver defaults to **Claude and both owner/agent legs**. Reuse must explicitly select `--client codex --legs owner` under the recommended Q2 scope. `scripts/philo7_file_and_find.py:1538`.

   Require distinct session IDs and fresh homes for creation and retrieval, no resumed transcript, and only the human project name supplied to the second session. Retain the complete initial context and reconcile client events with hub exchanges. Specify the milestone date, risk facts, expected attention result, steward outcome and publication readback before the run; check content, not merely successful responses. The driver is a suitable foundation once findings 1–5 settle what “complete” means.

CONDITIONS:

- Ratify a truthful job endpoint: local publication or actual delivery.
- Correct Q1’s effect table and Q2’s authority choices; settle the steward lifecycle before implementation.
- Propagate Q3’s answer through scope, stories, discovery and closing assertions.
- Replace the suggested-source “answers” criterion with durable outcome and failure proof; correct F15.
- Add the HTTP exceptions inventory, explicit new-tool contracts, backend ownership and state/width-specific red-first matrix.
- Pin the Codex launch and substantive readbacks.

MISSED:

1. Highest direct owner cost: a source cannot be added reliably, and a locally published update has not reached anyone.
2. Highest authority cost: an agent can enable unattended work; Archive also changes that authority despite its proposed exemption.
3. Highest closure risk: green counts, an empty attention list and a no-action steward run can masquerade as a useful project job.
4. F14 deserves earlier treatment for a clean installation: the unconditional runtime import is outside base dependencies. Recommend the small packaging repair as a prerequisite, rather than leaving it unassigned behind face polish. `holdspeak/operations.py:38`, `pm/roadmap/holdspeak/BACKLOG.md:1328`.

TUESDAY: Not yet—the proposed repair gets him into the Room, but still permits “source accepted” without a source and “update sent” without delivery.

UNKNOWN: Reviewed `3066dccb` in `/Users/karol/dev/tools/wt-astra-p9`; reproduced the census, ran real isolated-hub HTTP/MCP and credential probes, inspected retained shots, and obtained `dw check: ok`. No fresh browser/atlas walk, cold Codex rehearsal, external connector execution, clean base-install boot or full suite was run. Applied the repository’s `agent/skills/holdspeak-capability-verifier/SKILL.md`. The review worktree remains clean; nothing was edited.