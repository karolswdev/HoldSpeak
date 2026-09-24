# Check — Astra, 2026-09-24, on built: PHILO-4-03 (PR #624 @ ca8fe3d9)

VERDICT: **RATIFY-WITH-CONDITIONS** on #624 at `ca8fe3d9`. The ID repair is sound. Reconcile the verification scope before merge.

FINDINGS:

1. **The story is marked done with contradictory walk obligations.** `pm/roadmap/holdspeak-philo/phase-4-the-morning/story-03-breakage-ids-never-collide.md:17` includes the rig at 1440 and 393; its test plan requires retained observations. `pm/roadmap/holdspeak-philo/phase-4-the-morning/evidence-story-03.md:27` instead defers it to phase exit. “No face change” explains the choice but does not reconcile the charter. **Tenets 3 and 7; Article IX; ORCHESTRATION scope-honesty rule.**

2. **The original producer is identifiable.** The closure `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/closure/20260924T012420Z-case.closure.chain.s5_next_day_brief_after_triage-muaddib-393/observation.json:1194` retains `DecisionLifecycleService.get_decision failed`, event `95b68ac7-c11c-4b2e-8ad8-1713957b7886`, in the earlier brief. The hub traceback alone omits it; the observation does not. The chosen failing `shelve` covers the same mechanism: both services use `@observe_service`, and the collector builds IDs from the resulting event ID. Correct the claimed unknown; no different repair is indicated. **Tenet 3; Article VI.**

3. **The collector-order claims are too broad.** `holdspeak/services/monday_brief_service.py:202` runs coverage and waiting collectors before the existing-brief lookup. Several other collectors precede ID creation at line 268. The accurate claims are: the ID exists before **breakage collection**, and same-day generation returns before **breakage collection and new inserts**. This is inherited behavior, not a regression. Correct the wording without expanding this repair. **Tenets 1 and 3.**

4. **The repair and regression fences pass independent verification.** Both ID shapes include the brief ID; `source_ref`, title and detail remain unchanged; plain INSERT remains; no migration is introduced. See `holdspeak/services/monday_brief_service.py:558` and line 587. I collected both tests and reproduced:
   - Pre-fix: **2 failed**, both on `monday_brief_items.id` uniqueness.
   - Built: **2 passed**.
   - Listed scoped suite: **73 passed**.

   `tests/unit/test_philo4_03_breakage_ids.py:93` verifies both persisted rows, preserved day-one Ack, untouched day-two shelf, and stable same-day IDs. The connector test is lawful **producer-boundary evidence**: `holdspeak/db/activity/enrichment.py:123` generates the durable row and ID through the real writer. It does not prove an actual connector executed, and the report correctly distinguishes that.

5. **No ID-consumer incompatibility found.** Shelf operations, routes, MCP, ChairHome and BriefView use opaque IDs. The additional `holdspeak/services/recall_service.py:514` also preserves the complete ID. No web, schema, or `pm/roadmap/holdspeak/` asset changed. The API-reference diff only adds the new test to two candidate lists; its generator check and `dw check holdspeak-philo` pass. Existing wording debt remains explicitly outside this repair.

CONDITIONS:

- Supply the promised rig evidence, or record a checked scope amendment in the story and phase decision log assigning that proof to the still-open phase exit.
- Correct the producer-identification and collector-order claims.
- Read the remaining CI results before merge; unit checks were running and macOS integration/E2E checks queued at my last inspection.

MISSED:

1. **Highest owner cost:** treating this backend repair as proof that the complete morning interaction works.
2. **Investigation cost:** the retained brief already identifies the original failing producer.
3. **Maintenance cost:** inaccurate collector-order claims could mislead the next repair.

TUESDAY: This removes the reproduced collision while preserving yesterday’s Ack; the owner’s complete one-click morning remains unverified.

UNKNOWN: No new atlas walk, screenshots, full suite, or real connector execution. Tests ran in temporary archives with isolated HOME. The first scoped archive run lacked Git history; after providing read-only history access, all 73 passed. The reviewed worktree remains clean and unchanged.
