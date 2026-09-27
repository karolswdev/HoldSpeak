VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The recommended job can go to the owner; r2 is not wholly paid.** Retain Q0(a), Q1(a), Q2(a), Q3(a). These are charter conditions, not demands to implement before ratification.

   | R2 condition | Assessment at `c5cdd126` |
   |---|---|
   | Correct admission and refusal coverage | **Classification substantially paid:** Door Count and all four proposal decisions are admitted. Connection behavior and HTTP refusal coverage still need findings 2 and 4. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:127`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:137`. |
   | Reconcile seven tools with HTTP | **Partial.** Pagination, vocabularies and receipt ownership fences are corrected; finding 3 remains. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-01-the-rooms-operations-on-the-contract.md:28`. |
   | Assign F20; finish conditional Q3 acceptance | **F20 and acceptance wording paid.** The real-producer fence is explicit. Q3(c) now names a plausible chain, but the exact producer call and reachability remain deferred. `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-02-the-steward-and-the-connectors-under-article-xi.md:33`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-06-work-in-a-project-room-without-the-repo.md:23`. |
   | Preserve admissions inside exempt wrappers | **Paid.** Explicit at `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:122`. |
   | Remove CI-exclusive verification assignment | **Paid.** Orchestrator execution is restored at `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:265`; the standing quiet-suite responsibility still applies. |

2. **Cached List needs a complete refresh contract and a face owner. — Tenets 2/3; Article VI.**

   The change is reasonable, but “each provider’s last stored state” is too broad:

   - Connections loads List on mount. GitHub and Jira have Recheck controls, so refresh remains reachable. However, the footer displays the **newest timestamp across all providers**, formatted as time only; it cannot communicate each cached row’s age. A new “never checked” state would currently decode to `not_configured`, displayed as “Off” or “Not set up.” Evidence: `web/src/pages/cores/connections/ConnectionsPane.tsx:502`, `:509`, `:65`; `web/src/pages/cores/connections/api.ts:65`.
   - Calendar and Models currently project live local configuration without egress. Their face controls open settings; neither offers Recheck. Preserve those live reads rather than accidentally freezing them with the remote caches. Evidence: `holdspeak/services/connections_service.py:392`, `:431`; `ConnectionsPane.tsx:608`.
   - **Confluence Recheck does not probe today.** It calls `_confluence_entry`, whose adapter readiness reads stored rows and binary availability. I created a connection through the real adapter producer and called Recheck: zero subprocess calls, persisted state still `disconnected`, `last_checked_at=null`. Evidence: `holdspeak/services/connections_service.py:135`, `:314`; `holdspeak/services/confluence_provider.py:502`; [probe record](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p9-r3-xlmcuuor/confluence.json).
   - The setup interview also consumes List for proposal annotations. It therefore inherits this behavior change despite being migration-deferred. Evidence: `holdspeak/services/project_setup_service.py:1431`.

   Assign the Connections face changes and fences explicitly. Charter Confluence’s real probe as a repair, rather than describing it as existing behavior.

3. **The compatibility mapping still contradicts production HTTP behavior. — Tenets 3/7.**

   The new resource tools accept `expected_revision` and `command_id`; the HTTP resource routes forward neither as service keyword arguments. On the isolated hub, two PUTs with `expected_revision=-1`, the same command ID and different relationships both returned **200**. Project `proj-feb228e16585` advanced from revision **1 to 3**; no command row existed under the supplied ID. This cannot satisfy the promised equivalence without an explicit HTTP repair or declared difference. Evidence: `holdspeak/web/routes/projects.py:303`, `:316`; `holdspeak/services/project_service.py:3172`.

   Two smaller corrections belong in the same table:

   - `project.item.transition` also returns `idempotency_conflict`: I reproduced HTTP **409** by reusing its command ID for a different transition. The table omits that refusal. Evidence: `holdspeak/services/project_service.py:4149`, `:4454`; charter:113.
   - HTTP error bodies are not uniformly `{success:false,error}`. Invalid item-list filters and resource references returned `{error}`. Evidence: `holdspeak/web/routes/projects.py:425`, `:309`; charter:118.

   [The retained HTTP/DB probe records all three discrepancies.](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p9-r3-xlmcuuor/probe.json)

4. **Q2’s HTTP refusal promise needs an explicit edge repair. — Tenet 3; Article XI.**

   With a real Settings-issued PROJECT credential, Door Count, Door Create with sources, and GitHub Recheck each returned **403 `principal_right_required`**, missing right `owner`; together they created **zero kernel operations**.

   The central HTTP gate rejects these requests before the route or declared operation runs. Adding admission inside the service cannot produce the promised `delegation_required` receipt by itself. Evidence: `holdspeak/principals.py:354`, `holdspeak/web_server.py:655`; [probe record](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p9-r3-xlmcuuor/probe.json).

   Story 02 must name this boundary and test real authenticated HTTP requests, including the HTTP-only Door operations. Preserve Phase 7’s distinction between identifiable consequential refusals and unknown/read/exempt protocol failures.

CONDITIONS:

- Before briefing story 02, settle remote-cache versus live-local reads, truthful never-checked/age presentation, Confluence probing, affected callers, and ownership of the Connections face and transition fences.
- Before briefing story 01, settle resource-route revision/idempotency behavior and correct the per-tool refusal/envelope mapping.
- Assign the HTTP edge refusal repair and production-credential fences to story 02.
- Keep Q3(c) conditional until its exact producer call and proposal chain are proved. This does not block the recommended Q3(a).

MISSED:

1. **Owner confusion:** cached connection badges can look current; Confluence’s refresh presently performs no probe.
2. **Lost contract guarantees:** HTTP resource writes ignore the proposed revision and command-ID arguments.
3. **Missing evidence:** HTTP authorization can refuse an admitted operation before its receipt path.

TUESDAY: Yes, the recommended job is credible—owner-authenticated MCP for entry, the Room for review and local publication—provided connection freshness and refusals remain understandable.

UNKNOWN: Reviewed `c5cdd1265` in fresh worktree `/Users/karol/dev/tools/wt-philo9-check-r3-c5cdd126`. `dw check` passed; residual census passed at 284 identities. Ran isolated-hub HTTP/credential/DB probes and a real-adapter Confluence diagnostic. No fresh browser/atlas walk, Q3(c) producer-chain run, external provider execution, cold Codex rehearsal or full suite. F22 remains code-read. The worktree is clean; no repository files changed.