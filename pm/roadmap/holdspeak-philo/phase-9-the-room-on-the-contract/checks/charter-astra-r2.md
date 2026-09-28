VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The admission table still exempts effects it otherwise admits. — Tenets 3/7; Article XI.**

   Two concrete errors remain:

   - **Door count performs egress.** The HTTP inventory labels it a read requiring no admission. Its service fetches GitHub or Jira snapshots, including `gh pr list`; the subprocess read path checks permissions but creates no kernel operation. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:177`, `holdspeak/services/project_door_service.py:146`, `holdspeak/services/watch_sources.py:75`, `holdspeak/connector_runtime.py:175`.
   - **`connection.list` is not simply a stored read.** List calls `_github_entry`, which probes authentication and persists connection state. GitHub Recheck calls that same helper. Classifying List as exempt and Recheck as admitted therefore distinguishes names, not effects. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:119`, `holdspeak/services/connections_service.py:113`, `holdspeak/services/connections_service.py:180`, `holdspeak/services/github_provider.py:183`.

   Admit the active probes, or explicitly charter a cached List operation. Also distinguish provider cases: `connection.recheck(calendar|models)` returns local readiness, unlike the GitHub/Jira paths.

2. **Proposal Dismiss is a decision, despite its exemption. — Tenets 3/7; Article XI.4.**

   The table admits Accept/Edit Accept but exempts Defer/Dismiss. Dismiss records `decided_by_ref`, changes the proposal to `dismissed`, and writes the basis that suppresses recurrence. Defer likewise records a decision and controls its return. These are substantive review decisions.

   Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:128`, `holdspeak/services/project_delta_service.py:988`, `holdspeak/services/project_delta_service.py:1012`, `holdspeak/services/project_delta_service.py:1292`.

   Under the proposed Q2(a), these exemptions preserve an undelegated agent’s ability to dispose of the owner’s proposals. Admit all four decision verbs and apply the corresponding refusal contract.

3. **The seven-tool table is explicit, but several contracts are inaccurate or unfinished. — Tenets 3/7.**

   `project.item.list` promises `{items, total}` “as GET”, with `limit ≤ 200`. The existing service returns `{items, limit, offset}`, permits up to **1000**, and supplies no total. I confirmed HTTP accepts `limit=201`. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:105`, `holdspeak/services/project_service.py:4254`, `holdspeak/services/project_service.py:4287`.

   The proposed `invalid_item_type`, `details_invalid`, `invalid_lifecycle` and `project_not_found` names also differ from the existing service’s `validation` and `not_found` errors; HTTP often returns only an error message. Evidence: `holdspeak/services/project_service.py:3642`, `holdspeak/services/project_service.py:4310`, `holdspeak/services/errors.py:19`, `holdspeak/web/routes/projects.py:440`.

   New contracts can differ deliberately. The charter must specify those differences and their compatibility mapping before requiring both exact table compliance and HTTP equivalence. Complete the accepted patch fields and lifecycle/severity vocabularies as well; `patch` alone is not a settled closed schema.

   **The palette proposal is sound.** Seven tools in the project family reach PROJECT and SWEEP. Reusing `kernel.receipt` avoids another public tool, and its existing read path restricts agents to their own principal’s operations. Preserve that restriction and fence own/foreign receipt reads through the expanded palettes. Evidence: `holdspeak/mcp/palettes.py:46`, `holdspeak/kernel/broker.py:54`.

4. **The recommended fixture works further than the lane verified, but exposes a missing backend repair. — Tenets 3/7.**

   On an isolated real hub, I created the specified milestone and risk through production HTTP routes, configured `["draft_update"]`, and ran the steward through MCP:

   - One draft effect completed.
   - The draft named **Cutover rehearsal** and **Old ledger freeze slips**.
   - Publication persisted across readback.
   - A subsequent edit was refused with `published_update`.

   However, the steward recorded `compare.review_id=""` although the review existed. `_phase_compare` reads `review.get("id")`; the real producer returns `review_id`. Evidence: `holdspeak/services/project_steward_service.py:869`, `holdspeak/services/project_delta_service.py:1848`. Assign this repair and its real-producer fence to story 02; “show the review” cannot be solely a face repair.

   Probe rows: run `pstrun_aee671c2319c4d00ad51d15dae12024a`, review `prev_34d7867155cf42509b0f2b2fe1eca11f`, update `pupd_1d86640c7ab64a5ba6f3c9e82b6179c8`. Records: [probe.json](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p9-r2-bp4fqv19/probe.json), [publication readback](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p9-r2-bp4fqv19/readback.json).

   **Q3(c) remains conditional.** An open review alone does not enter NEEDS YOU; pending proposals are required. My review existed with zero proposals and zero attention items. The linked-meeting/resource alternative needs a concrete producer fixture that creates the expected proposal. Story 06’s acceptance criterion also still unconditionally names milestone and risk facts. Evidence: `holdspeak/services/project_service.py:814`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-06-work-in-a-project-room-without-the-repo.md:31`.

5. **R1 payment is substantial, but “every finding paid” overstates it.**

   “Paid” here means corrected in the charter, not implemented.

   | R1 | Assessment and evidence |
   |---|---|
   | F1 — publication versus delivery | **Paid.** Local endpoint, discovery constraint and delivery backlog: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:72`, `pm/roadmap/holdspeak/BACKLOG.md:1330`. |
   | F2 — source addition/F15 | **Paid as a repair contract.** Durable resource-plus-watch or named refusal with pending suggestion; F15 corrected. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:63`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-02-the-steward-and-the-connectors-under-article-xi.md:28`. |
   | F3 — effect classifications | **Partial.** Archive, watch-test persistence, Door creation and Q1(c) improved; findings 1–2 remain. |
   | F4 — agent authority | **Policy choice paid.** Q2 now names the behavior change and refusal receipt; its coverage depends on correcting Q1. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:288`. |
   | F5 — Q3/substantive job | **Paid for recommended Q3(a); incomplete for (c).** Explicit entry path and meaningful fixture: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:149`. Finding 4 identifies the remainder. |
   | F6 — inventory/deferrals | **Mostly paid.** “Migration deferred, still callable” is accurate; HTTP inventory exists but misclassifies Door count. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:80`. |
   | F7 — cost, contracts, lifecycle, ownership | **Partial.** Per-story fences, assembly-only story 05, lifecycle beat and backend ownership are paid. New-tool contracts need finding 3’s corrections. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:161`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:256`. |
   | F8 — red-first requirements | **Paid.** Affected-width reds, preservation greens and structural mutations are separated. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:188`. |
   | F9 — closing launch | **Paid as a specification.** Client/leg, isolation, fresh retrieval session and content checks are pinned. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:221`. |
   | MISSED 4 — packaging | **Paid as sequencing.** F14 is story 01’s first commit. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-01-the-rooms-operations-on-the-contract.md:18`. |

6. **Q0–Q3 now expose the right principal choices; retain the recommendations.**

   Recommend **Q0(a)** local publication, **Q1(a)** corrected effect-based admission, **Q2(a)** owner execution plus consequential-agent refusals, and **Q3(a)** visible items with explicitly owner-authenticated MCP entry.

   Q1(c) honestly leaves exit 4 unmet. Q3(c) needs the qualified closing fixture above. Q0(b) and Q2(b) require the stated scope expansion. None requires another framework.

CONDITIONS:

- Correct the probe and proposal-decision classifications, with the resulting Q2 refusal coverage.
- Reconcile the seven new schemas, results and refusals with HTTP compatibility and equivalence.
- Assign the steward review-ID repair; finish Q3(c)’s fixture and conditional acceptance wording.
- Clarify that exempt wrappers can retain admitted lower-level effects: “exempt rows leave none” currently conflicts with the model draft’s preserved `inference.invoke`.
- Correct the verification assignment at `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:256`: repository instructions assign the quiet full suite to the orchestrator, not exclusively CI.

MISSED:

1. **Highest authority cost:** an undelegated agent can still dismiss or defer proposals under the proposed exemptions.
2. **Highest admission gap:** operations called List and Count perform active provider work.
3. **Highest closure risk:** the review exists but its steward reference is blank; an empty review supplies no attention item.
4. **Avoidable implementation cost:** workers must reconcile contradictory tool contracts and equivalence requirements unless the charter settles them first.

TUESDAY: The recommended job is credible for an owner using MCP for entry and the Room for review; I would present it for his word after these corrections, explicitly ending at local publication.

UNKNOWN: Reviewed `f72db808` in `/Users/karol/dev/tools/wt-astra-p9-r2`. Product code is unchanged from the grounding base. Census passed at 284 identities; `dw check holdspeak-philo` passed. Ran isolated-hub diagnostic probes through real producers, including draft/publication readback; no fresh browser/atlas walk, cold Codex rehearsal, external connector execution, clean base-install boot or full suite. Chair/shade/recall callers and the handlerless branch remain code-read only. Applied the repository’s `agent/skills/holdspeak-capability-verifier/SKILL.md`. No repository files changed; the review worktree is clean.