# Check — Astra, 2026-09-25, on the Phase 7 charter draft (PR #650 @ 8f497d5a)

VERDICT: RATIFY-WITH-CONDITIONS

The bounded slice is suitable for presentation after the corrections below and Phase 6’s close. The enumeration holds. The blanket admission exemptions do not.

FINDINGS:

1. **The “plain edits” exemption hides filing effects.** The `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:147` exempts all zone/KB create, update and delete operations. However:
   - Zone deletion unfiles its contents and moves child zones to the root: `holdspeak/db/primitives.py:1182`.
   - KB create/update with `member_ids` adds or removes actual knowledge memberships: `holdspeak/db/primitives.py:401`.

   I reproduced both through `PrimitiveService` in an isolated database. Zone deletion tombstoned the membership and cleared the child’s parent; KB create added a membership and update removed it. All left zero kernel operations/receipts. Admitting the dedicated membership verbs while exempting these paths would leave bypasses. **Tenets 3/7; Articles V.1 and XI.1.** Classify these effects explicitly; keep genuinely plain edits exempt.

2. **Story 02 permits a receipt-free consequential refusal.** Its `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-02-membership-and-decisions-under-article-xi.md:24` allows the Thought filing guard to refuse “before admission or” produce a refusal receipt. This is a domain refusal of a filing attempt. Article V.2 requires a receipt for every attempt; XI.2 explicitly includes refusal. Remove that alternative and fence the unchanged membership plus the refused receipt through both transports. **Tenet 3; Articles V.2/XI.2.**

3. **The existing kernel entry is correct, but `submit` is not the complete execution path.** The cited `holdspeak/services/gate_service.py:34` calls the real kernel under the transport principal. Successful submission reaches `awaiting_decision`, however: `holdspeak/kernel/broker.py:122`. Execution authority has separate owner/delegation checks: `holdspeak/kernel/broker.py:190`. Before story 02’s brief, name the existing approval, execution and terminal-receipt path, its receipt readback contract, and its agent-parent behavior. Preserve one admission per logical operation, including two-row supersede. “No owner-only by default” must not become manufactured owner authority. **Tenets 1/3; XI.2–4.**

4. **The enumeration is correct and honest.** I reproduced **320 = 256 MCP + 64 HTTP**, matched all **36 distinct listed tuples** against the ledger at `f93e76fa`, and ran the census successfully: `RESIDUAL FENCE GREEN: 320 identities match`. The census inputs are unchanged from that base. The breakdown is **24 primitive MCP + 6 membership + 2 decision-delete + 1 supersede**, plus three HTTP constructors. **284–287** is correct. The fallback/MOVED qualification and uncounted decision HTTP bypass work are properly stated at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:131`.

5. **Discovery separates vocabulary proof from model behavior correctly.** Story 01’s real-`tools/list` mapping proves published words and argument paths; story 04 supplies the behavioral rehearsal. I counted the retained events: **25 completed shell commands in `decision_thought`, plus 3 in `import` = 28 total**. These are different scopes, not conflicting counts; say that explicitly at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:157`.

   One gap remains: an outside working directory does not itself remove repository access. `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-04-file-it-and-find-it-without-the-repo.md:17` should name a launch setup that actually withholds repository access and inherited repository instructions. Retain the complete initial context and events; keep the zero-read fence and its required rejection of the Phase 5 log. **Tenet 3; D4.**

6. **The atlas and four-story structure are sound.** I reproduced **85 cases in `atlas.json`, 36 in `atlas-phase3.json`**. The named directory/KB/membership/status/supersede browser coverage must be added; the existing directory setup step does not provide it. `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-03-the-atlas-for-the-desk.md:22` correctly preserves independent browser proof, `.op` outcomes and refusal equivalence. “Not on the face” can delimit coverage, but cannot waive story 04’s required note, review-row and brief shots.

7. **The migration scope and settled positions are lawful.** The finite explicit table, real callables, Thought revision behavior, single hub instance, compatibility tables and no automatic owner-only policy are carried correctly at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:197`. Including directory/KB update and delete completes the named families. Arithmetic clarification: **12 update/delete identities cover notes, directories and KBs together; directories and KBs alone contribute 8.** The admission correction changes how these effects execute, not the residual inventory.

8. **The form passes; two planning records need correction.** `dw check holdspeak-philo` reports no Phase 7 issue. Its sole error is Phase 6’s missing `final-summary.md`, consistent with the pending close. “Not yet grounded” is acceptable for this draft, but `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:238` moves re-estimation until after implementation begins. Supply a provisional estimate before build authorization, then calibrate it after the first kind. Phase 5’s 11–14 days was itself a provisional estimate, not measured delivery evidence. Also remove “a durable attach relationship” from the still-linked `pm/roadmap/holdspeak-philo/PHASE-6-7-CHARTER-DRAFTS.md:8`. **Tenets 2/3/7.**

CONDITIONS:

- Correct the admission table and story 01/02 boundaries for membership-changing KB writes and zone deletion; identify any other placement-changing fields explicitly.
- Require receipts for domain refusals of admitted operations.
- Settle the complete kernel execution/readback path and principal cases before story 02 builds.
- Make D4’s repository exclusion concrete; retain both discovery fences.
- Reconcile the 25/28 wording, remove the attachment promise, and place the provisional estimate before build authorization. Keep Phase 6 closure as the prerequisite.

THE FOUR ADMISSION RULINGS:

These are my readings for the owner to confirm or overrule, under `docs/internal/CONSTITUTION.md:106`.

| Operation | Ruling | Reason |
|---|---|---|
| `decision.status` | **ADMIT** | It performs the same status mutation as admitted `decision.update`; an alternate route cannot exempt the effect. `holdspeak/services/primitive_service.py:211`. |
| `zone.unfile` | **ADMIT** | It changes the filing relationship. Reversibility does not remove Article V’s filing trigger. `holdspeak/services/primitive_service.py:415`. |
| `decision.delete` | **ADMIT** | Withdrawing a decision changes its lifecycle. The current implementation is a tombstone, so “irreversible deletion” is not the factual justification. `holdspeak/db/primitives.py:318`. |
| `kb.add_member` / `kb.remove_member` | **ADMIT both** | They file/unfile durable references. Many-to-many cardinality does not change that effect. Include equivalent `member_ids` writes. `holdspeak/services/primitive_service.py:294`. |

MISSED:

1. Highest owner cost: equivalent filing effects hidden inside supposedly plain CRUD operations.
2. Next: a submission that never reaches authorized execution and a terminal receipt cannot complete the Tuesday job.
3. Lower: the attachment promise survives in the pointer, and estimate uncertainty has become an after-build checkpoint.

TUESDAY: Yes, this is a useful bounded job—provided the owner can file, find and review from ordinary words, receive the result without another confirmation, and see it on the reopened Desk without repository research.

UNKNOWN: This checks the charter at `8f497d5a`, not built Phase 7 behavior. No new browser walk, proposed fence, full suite or owner sitting was run. Verification comprised source/artifact inspection, retained event counts, census/lint and isolated real-service probes. The tree remains unchanged.