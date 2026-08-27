# HS-143-14 closeout plan — Chaos, Glass, and Closeout

**Planning snapshot:** `main` at `85b8c0e7`; Stories 01–13 are merged and
closed. Story 15 is a **startable sibling**, but it is a prerequisite to
Story 14's final close flip. This plan neither changes a story status nor
makes a close claim.

## 0. Closeout law

This is a proof-and-ledger story, not an opportunity to reopen the router.
Every new proof uses an isolated HOME and a fresh database/artifact root. The
write-once closeout ledger records only immutable evidence facts: criterion,
constitutional basis, source commit/test/evidence capture, result, and any
narrow carry. It does not become a mutable issue tracker.

The ledger must cite the Constitution at the point of each claim:

- **III.1–2** — a saved local→cloud boundary is the only lawful egress
  authority and must be visible at decision time.
- **V.2–4** and **XI.1–4** — every model/tool attempt is admitted, bounded by
  derived authority, and terminally receipted; unknown outcomes do not license
  another act.
- **VI.1–3** — unavailable, stale, unsupported, or indeterminate state is
  named rather than smoothed over.
- **VIII.3** and **IX.1–4** — phone glass is first-class and a UI assertion is
  evidence only after a real-hub walk and the owner's verdict where required.

## 1. Kill-criteria ledger plan

The wording in the first column is verbatim from
`assets/architecture-contract.md` §Kill criteria. “Evidenced” means a shipped
production-path or fail-closed census proof already exists and must be copied
by reference into the immutable ledger. “Needs proof” means Story 14 must add
or repair a production-path proof before it may make the row PASS.

| # | Kill criterion (verbatim) | Status and existing evidence | Story-14 ledger/proof action |
|---:|---|---|---|
| 1 | A capability resolves a mutable profile after admission. | **EVIDENCED.** Story 05 route/request-plan suite (`tests/unit/test_phase143_inference_route_plans.py`) freezes exact revisions; Story 07 production-adoption proof covers assignment-edit-after-freeze; Story 10’s 16-case production-entry matrix repeats freeze/mutate/later-admission across Recipe, Workbench, Agent, voice, Sequence, Workflow, and retired `inference.run` (`evidence-story-10.md`). | Ledger links the three captures and, in the chaos row, shows an assignment mutation cannot retarget the already-admitted Recipe route. |
| 2 | An engine/provider adapter performs a hidden retry or fallback. | **EVIDENCED.** `tests/unit/test_phase143_inference_fallback_controller.py`, `test_inference_runner.py`, and Story 06’s controller evidence establish controller-owned attempts; Story 07 retires application retry loops; Story 09’s `ToolModelAdapter` render-once/transport-once contract and tool-turn suites prove the tool dialect cannot loop (`story-09...md` Progress A5/B3). | Ledger cites controller, coordinator, and tool-adapter seams; cross-product run asserts the exact persisted attempt count, rather than trusting a provider-call counter. |
| 3 | A physical model call bypasses `InferenceRunner`. | **EVIDENCED FOR SHIPPED PYTHON/WEB PATHS, WITH A HELD SWIFT SCOPE DECLARATION.** Stories 01/10 generated censuses and Story 10’s production-entry matrix show zero Python placement forks and runner-child linkage. The seven Swift leaves are explicitly HELD by the owner’s web-first ruling, not falsely reported as zero (`story-10...md:30–37, 98–113`; `evidence-story-10.md:149–152`). | Ledger must name the seven held leaves, hold branch `hold/hs143-10-slice5-swift-bridge`, and future Swift-recreation owner. It must not write an unqualified whole-repository PASS; see ORCH-CALL 1. |
| 4 | An unknown/indeterminate/effectful outcome advances fallback. | **EVIDENCED.** Story 06 disposition/controller tests fence unknown dispatch; Story 09 B3/B4 proves unknown effect completion, permission denial, Stop, and lease expiry never advance, while receipted effects are adopted (`tests/integration/test_phase143_tool_turn_boundaries.py::test_b4_restart_boundaries_and_stop_races_leave_no_new_egress`). | Ledger includes the generic-controller and tool-turn boundary receipts. The chaos run reopens an unknown dispatched turn and verifies terminal/zero-new-egress. |
| 5 | Local→cloud fallback occurs without a saved visible boundary crossing. | **EVIDENCED.** Story 06’s named production proof `test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress` proves an available unsaved cloud profile receives zero calls; Story 07 repeats it on a migrated adopter. | Ledger records saved-chain disclosure, actual boundary, and the unsaved-cloud zero-egress control under Articles III and V. |
| 6 | A tool-incompatible deployment can be saved or selected for required tools. | **EVIDENCED.** Story 09 B1/B3 rejects unqualified candidates pre-dispatch and rechecks each fallback; Story 10’s real `RecipeService.chat` adopter reaches the ToolTurn controller through `InferenceRunner` (`story-09...md:83–105, 109–133`; `story-10...md:69–88`). | Ledger cites both qualification rejection and the first actual adopter; no new tool selector is permitted. |
| 7 | Browser code invents capability compatibility, readiness, or fallback law. | **EVIDENCED.** Story 13’s canonical `AssignmentEditorProjection@1` supplies server-filtered candidates, policy issues, and ABA-safe clear; Story 12 makes Models one aggregate; Story 11 removes browser compatibility write-throughs and the dead `dataSlice` key (`story-11...md:59–72`). | Ledger ties the server projection/e2e evidence to the source/census guard. The closeout does not add browser-side “helpful” reconciliation. |
| 8 | Config and the assignment store remain competing authority after migration. | **EVIDENCED.** Stories 04, 07, 08, and 10 supply one-way markers, post-marker refusal/write-through rules, and zero-Python-fork census; Story 11 retires stale target fields and compatibility writers. | Ledger lists the migration census artifacts plus the Story 10 real-entry matrix. Chaos mutation checks the frozen route and assignment store, never Config, after restart. |
| 9 | The default UI grows one permanent row per capability or becomes a matrix. | **NEEDS PROOF — existing evidence is real-hub but unstable.** Story 13 proves seven rows/no selects/393 targets in `test_assignments_overview_real_hub`, but `[populated-393]` fails about one serial run in three (`evidence-story-11.md:140–148`). | Stabilise that test’s hydration barrier, then capture repeatable real-hub 1440/393 plus 200% proof. The ledger may cite the existing shots only after the stable rerun. |
| 10 | HTTP/MCP/Desk produce different assignment, plan, attempt, or receipt truth. | **EVIDENCED.** Story 11’s 12-vector reciprocal harness checks owner denial, replay, CAS, and immutable `committed_effect` across fresh HTTP/MCP compositions (`tests/unit/test_phase143_transport_parity.py`); Story 13’s real Desk glass invokes the same HTTP application seam and receives Next-run truth. | Ledger explicitly says Desk is the real web owner surface over HTTP, not a third router. Add the final cross-product receipt comparison only; do not invent a duplicate Desk transport harness. |
| 11 | Sync import starts/resumes inference or rewrites hub-local assignments. | **EVIDENCED.** Story 11’s compound hostile-sync production-object proof refuses v2 router state before merge, omits it on pull, and proves the v1 bucket cannot mint v2 authority (`story-11...md:59–70`). | Ledger records zero execution, zero v2 assignment/binding creation, and safe omission under Articles III, V, VI, and XI. |
| 12 | A receipt cannot explain primary, attempts, fallback reason, actual model, boundary, and terminal outcome without reading current settings. | **NEEDS A CROSS-PRODUCT PRODUCTION-PATH PROOF.** Stories 06/07/09/10 separately prove durable route/controller/tool receipts and reconstruction, but no one compact proof mutates current assignments while simultaneously carrying a real routed workload through a hub restart and then reads the receipt. | Add the narrow closeout-chaos scenario in §3: freeze a Recipe chat/run, mutate the assignment after admission, restart once, and read the receipt/reconstructed plan without Config/current-profile resolution. Assert primary/attempt ordinals, reason, model/deployment, boundary, and terminal outcome. |

**Ledger count at planning time:** 10 evidenced rows; 2 proof rows (criterion
9 evidence stability and criterion 12 cross-product receipt reconstruction).
Criterion 3 additionally requires the explicit, owner-ruled Swift scope line
before its otherwise evidenced Python/web result can be recorded honestly.

## 2. Exit-criteria mapping

| Exit criterion | Evidence already available | Honest residue before it is checked |
|---|---|---|
| Every production inference call site belongs to one versioned capability. | Story 01 census; Story 02 sealed registry; Story 08 adoption close; Story 10 regenerated capability/routing censuses and 16-entry production matrix. | Re-run the generated censuses on the final tree; record held Swift leaves as scope, never as a zero. |
| Every execution freezes one immutable route plan before first egress. | Story 05 route-plan suite; Story 07 coordinator proof; Stories 08–10 frozen adopter matrices. | Chaos scenario must show one post-freeze assignment edit and one restart preserve the route ID/revisions. |
| Every physical generation remains a separately admitted `InferenceRunner` / `inference.invoke@1` child. | Stories 01, 06–10 censuses/matrices; Story 09 separately proves model and tool children. | Final census plus the Swift scope declaration in the closeout ledger. |
| Ordered fallback advances only for a closed eligible disposition and its receipt explains every leg, child, boundary, and terminal outcome. | Story 06 controller/disposition suite; Story 09 B3/B4 table and tool boundary restarts; Story 07 saved-boundary adopter. | Criterion-12 closeout scenario must read all receipt facts after mutation/restart. |
| Config/profile/subject legacy pointers have one-way migrations and no competing authority remains after each family crosses. | Stories 04, 07, 08, 10, and 11 migration markers, source guards, retired field sweep. | Regenerate/execute the three censuses on final tree; no new migration design. |
| Adding/downloading/connecting a model changes zero assignments. | Story 12 assignment-head-before/after checks on every library command; Story 11 parity vectors repeat the invariant. | Include a Model Library command in the chaos fixture and compare assignment-head bytes across the restart. |
| Model Library and bounded Assignments glass pass at 1440, 393, and 200% zoom with keyboard/screen-reader/reduced-motion proof. | Story 12 e2e matrix (11 tests) and 1440/393/200% shots; Story 13 real-hub editor/contextual walks, roving radio, live region, Escape, Mod+Enter, 44px, zoom, overflow proof. | Repair/repeat the genuine `[populated-393]` timing flake; reconfirm existing owner-shot disposition rather than pretending a screenshot exists because an e2e passed. |
| HTTP/MCP parity, OWNER boundary, hub-local sync, restart, privacy, schema, API inventory, one-path census, full tests, and production build are green. | Story 11 parity/hostile-sync/retirement suite; Stories 03/05/08/09/10 restart and schema proofs; Stories 12/13 secret/egress/glass proof; API/census regeneration in Stories 10/11. | Final isolated-HOME production build and suite capture. Raw pytest remains expected-red for the inherited baseline; the ledger must prove exact-baseline/no-branch-new rather than claim a zero-failure suite. |
| All kill criteria in `assets/architecture-contract.md` have production-path evidence in Story 14's write-once ledger. | The source evidence mapped in §1. | Create and fill `assets/phase-143-closeout-ledger.md` only after S1/S2 evidence exists; the final check is ledger completeness, links, immutable identifiers, and no waived row. |

## 3. Chaos gap analysis

### What is already proven by family

- **Freeze/restart:** Story 07 reconstructs routed Thought work; Story 08
  reconstructs Queue/Meeting/Speech work; Story 10 reconstructs Sequence;
  Story 09 proves model/tool/effect boundary restarts and Stop races.
- **Hostile/state-changing input:** Story 04 covers assignment CAS, replay, and
  concurrent edits; Story 11 covers closed HTTP/MCP payloads, owner denial,
  event loss→GET, and hostile sync; Story 12 covers provider command replay,
  custody failure, and secret redaction.
- **Concurrency/failure:** Story 06 owns reservation/budget/terminal election;
  Story 08 owns executor leases, epoch effect fencing, Stop handoff, and
  recovery; Story 09 owns tool/effect adoption and unknown terminality.

These are substantial production-shaped proofs. They do **not** demonstrate
that a single persisted hub state containing all three current owner jobs
(routed work, model-library mutation, and assignment mutation) remains
truthful after one restart. That is the genuinely useful cross-product gap;
creating a combinatorial matrix of every adopter would be ceremony, not proof.

### One narrow cross-product proof

Add `tests/integration/test_phase143_closeout_chaos.py` using a real SQLite
Database and the production broker/application composition, with only external
network/model transport bounded at its existing adapter seam. It is a
reproducible **one-restart runbook**, not a browser mock and not a literal
`SIGKILL` theatre:

1. Seed a local primary and saved, visibly disclosed cloud fallback; start the
   production `RecipeService.chat` routed path (the first tool-capable adopter)
   and pause at a durable, already-admitted boundary.
2. Start a real Model Library command through its application service, pause at
   its durable command/replay boundary, and start an assignment command with a
   stable request ID. Arrange the interruption only after each relevant durable
   record exists; no fake router/receipt/projection is allowed.
3. Tear down the composition as a hub crash, reopen the same database once in a
   fresh production composition, and replay/reconcile each operation.
4. Assert: the assignment command is exactly idempotent or CAS-refused (never
   partial); library command preserves assignment-head bytes and has no leaked
   secret/path; the frozen Recipe route does not retarget; each receipt explains
   route legs/attempt/boundary/terminal result from durable evidence; unknown
   dispatch/effect produces no fallback/no new egress; one known receipt is
   adopted rather than re-executed.
5. Feed one hostile v2 router-shaped sync payload after restart and assert the
   existing Story-11 zero-authority result. This is a composition check of the
   existing guard, not a second sync implementation.

A full subprocess kill is not recommended unless the existing UAT conductor
already offers a deterministic hub-kill seam: the durable DB + fresh production
composition boundary is the actual recovery contract, while a timing-dependent
OS kill would add a flaky second mechanism. The runbook must say that plainly.

## 4. Intake dispositions

### A. Named real-hub 393 timing flake

**Diagnosis.** `test_assignments_overview_real_hub[populated-393]` has no
hydration barrier. `_open_assignments()` returns when generic `.prefs-module`
exists (lines 64–72), which is true before `CapabilityAssignmentsCore` has
finished `useEffect → getAssignmentSummary → setSummary`. The next assertion
uses `rows.count()` (line 142), a synchronous snapshot that may be zero. The
same gap exists before model-name/geometry assertions. The 393 layout makes the
race visible often enough serially; the 1440 failure family is ordinarily xdist
load-sensitive and must not be conflated with this defect.

**Fix and proof.** In
`tests/e2e/test_hs143_assignments_glass.py`, make `_open_assignments()` await
the owner-specific ready condition (Assignments heading and/or the seventh
`.capability-assignment-row` visible), then use Playwright expectation-style
count/visibility assertions before measuring boxes. Do not add sleeps, retries,
or an application-side fake loading delay. Run the populated-393 node serially
at least 12 fresh isolated-HOME repetitions, then the full assignments e2e
file both serially and under `-n auto`; preserve the separate 1440 xdist note
if it still reproduces only under load. This is a **test-stability repair**,
not evidence of a product defect.

### B. Story 13 audit ledger, already closed by Story 11

| Item | Disposition | Evidence / rationale |
|---|---|---|
| Dead browser `dataSlice` `profile_id` key. | **CLOSE-WITH-EVIDENCE.** | Story 11 retirement sweep deletes it (`story-11-http-mcp-sync-compatibility.md:59–72`); its plan explicitly names the Story 13 audit origin. |
| Browser-unreachable compatibility write-throughs. | **CLOSE-WITH-EVIDENCE.** | Story 11 converts them to typed post-marker refusals with no-side-effect proof. |
| Assignment receipt could echo the committed chain. | **CLOSE-WITH-EVIDENCE.** | Story 11 added the golden committed-effect/replay/privacy proof (`test_assignment_set_committed_effect_replay_is_identical_but_not_a_projection`). It is an immutable effect, not current projection truth. |

### C. Evidence-story and audit-record sweep

| Source/item | Recommended disposition |
|---|---|
| Story 07 triage/evidence. | **CLOSE-WITH-EVIDENCE.** No open ledger item; its restart, Stop, boundary, and no-post-marker-Config proofs feed kill rows 1, 2, 5, 8, and 12. |
| Story 08 full-suite failures and Story 09 full-suite failures. | **DOCUMENTED CARRY.** They were baseline-triaged, not Story 08/09 regressions; the final current set is the 11-name list below, not an old raw count. |
| C1 checkpoint findings (ten across rounds 1–5). | **CLOSE-WITH-EVIDENCE.** The checkpoint record says all ten fixed with committed proofs; sleep/resume/takeover scenarios are explicit sitting notes under the owner’s yolo ruling, not reopened closeout work. |
| C3 audit note 1: per-pass handoff/recovery SQLite scans. | **CARRY-TO-BACKLOG IF MEASURED PAIN APPEARS.** Single-user, cadence-bounded, no damage; candidate dirty/unsettled-count gate is recorded (`story-08-c3-counsel.md:51–60`). |
| C3 audit note 2: injected fence-fault → legacy enqueue collision. | **CARRY AS FAULT-ONLY NOTE.** Counsel confirmed it only with an injected handoff failure and ruled it out under the capped fault rule; do not represent it as a normal-action pass. |
| C3 audit notes 3/4: serial Stop cancel loop and missing unsettled-handoff index. | **CLOSE-WITH-EVIDENCE.** Daemonised post-commit cancellation measured `stop_wall_ms=16.31`; additive index and snapshot proof landed. |
| Phase D: remote speech transport. | **CARRY-TO-BACKLOG.** Admission refuses it honestly until an audio transport exists; it is future capability, not a router bypass. |
| Phase D: faster-whisper constructor-inseparable load. | **DOCUMENTED NARROW EXCEPTION.** Local-only exception is honoured and production-shaped warm/cold proofs exist; no ordinary failure. |
| Phase D: continuity proof’s `Transcriber.__new__`/internal subclass. | **CARRY-TO-BACKLOG.** Explicit proof debt, not a product failure; migration/bundle/controller continuity is otherwise proven. |
| Phase E’s four receipt/execution defects and Rails migration sweep catch. | **CLOSE-WITH-EVIDENCE.** All fixed in its one permitted round; Phase E carries no new ledger item. |
| Story 09 byte-length token reservation. | **DOCUMENTED NARROW CARRY.** Conservative over-reservation, never under-reservation; no authority/egress expansion. |
| Story 09 any-effect replay guard under P=1 effect ceiling. | **DOCUMENTED NARROW CARRY.** Equivalent protection under the frozen ceiling; receipts/effect adoption remain tested. |
| Story 09 dispatch-unknown ownership by generic controller. | **CLOSE-WITH-EVIDENCE.** Correct shared controller ownership, exercised by the generic and B4 boundary tests. |
| Story 09 turn-state-transition observation. | **CLOSE-WITH-EVIDENCE.** The B2 multi-step implementation made the model/tool/final/terminal states truthful. |
| Story 10 dead standalone Recipe-entry workbench tier. | **CARRY-TO-BACKLOG.** No production transport passes it; retain as non-routing attribution cleanup, not a false current route. |
| Story 10 seven Swift leaves. | **HELD BY OWNER RULING.** Name and retain the frozen bridge; do not call the census zero. ORCH-CALL 1 decides close wording. |
| Story 10 census xdist and Story 12 refinement xdist flakes. | **DOCUMENTED LOAD FLAKES.** Serial-green evidence exists; do not merge them with the genuine 393 timing race. |
| Story 12 generic `error_500` exception-string concern. | **CLOSE-WITH-EVIDENCE.** S5 proved the post-secret scrub and sentinel absence. |
| Story 12 44px assertion width coverage and reduced-motion spot check. | **CLOSE-WITH-EVIDENCE THROUGH RERUN.** Cosmetic audit notes; repeat their real-hub paths after the final glass run rather than expand the product. |
| Story 11 stale `MCP_SIDECAR` resource-count prose. | **CLOSE-WITH-EVIDENCE.** Fixed in Story 11 close commit. |
| Story 11 `[populated-1440]` and refinement-coordinator xdist/serial-green flakes. | **DOCUMENTED LOAD FLAKES.** Keep separate from the named 393 repair; reclassify only if serial reproduction changes. |

### D. Inherited-failure baseline — current honest carry

`assets/story-08-inherited-failure-baseline.txt` began as 72 pre-phase failed
test names. Later Phase 143 work healed most; Story 11’s close capture reports
**11 inherited failures**, plus two load flakes and the named 393 test-stability
intake. The closeout must record these exact red names and owners as a
**documented carry**, not silently call a raw red suite green:

| Current inherited red family (11 tests) | Owner/disposition |
|---|---|
| `test_ask_grounding_claims.py::{test_flags_an_unsupported_claim_and_not_a_supported_one,test_no_grounding_claims_when_no_context_material}`; `test_ask_runner_migration.py::test_ask_uses_versioned_contract_hash_runner_and_staged_projection` | Pre-143 Ask/grounding contract ownership; carry to its owner, not router closeout. |
| `tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date` | UAT/build-ledger ownership; documentation/build inventory drift, not runtime routing. |
| `test_interior_canon_guard.py::test_no_left_border_rails_in_web_css`; `test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift`; `test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms`; `test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html` | Cross-surface web grammar/copy hygiene ownership; pre-existing unrelated violations. |
| `test_kernel_effect_fence.py::{test_kernel_broker_modules_stay_within_line_budget,test_kernel_broker_has_zero_driver_specific_conditionals}` | Kernel architecture/debt ownership; do not contort routed code to satisfy it. |
| `test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config` | Inference setup legacy-read authority ownership; carry separately unless a final-tree triage identifies an actual new router change. |

The final suite record compares FAILED node IDs against this current set, names
any fluctuation, and classifies nothing as inherited merely because it is
inconvenient. A new failed node is branch-new until reproduced on `main` at the
same baseline or assigned by the orchestrator.

## 5. Slices

### S1 — Stabilise glass evidence and add the thin chaos proof

1. Repair the test readiness barrier described in §4A; execute focused real-hub
   assignments glass proof on 1440/393/200%, keyboard/live-region/reduced
   motion, with the 393 repeat run.
2. Add the one `test_phase143_closeout_chaos.py` production-composition
   scenario described in §3. Reuse the existing router/library/sync machinery;
   no new controller, lifecycle, schema, or browser abstraction.
3. Run focused relevant suites under isolated HOME and capture their output via
   Delivery Workbench evidence. Review output before any status change.

### S2 — Create the write-once closeout ledger

Create `assets/phase-143-closeout-ledger.md` after S1 is green relative to the
baseline. It contains 12 immutable numbered kill rows, the 9 exit-criterion
cross-links, exact evidence command/capture IDs, test paths, commit/tree IDs,
constitutional articles, result, and the narrow Swift/baseline carries. It
must explicitly distinguish **PASS**, **HELD BY OWNER RULING**, and
**DOCUMENTED CARRY**; no “waived” status is allowed.

### S3 — Final phase-exit proof and close mechanics

1. Confirm Story 15 is `done` with its evidence before starting this close
   flip; it is a close gate only, not a start gate.
2. Run final isolated-HOME generated censuses, API/MCP inventory/parity,
   production web build, the stable glass e2es, chaos proof, then the CI-style
   full suite. Capture raw failure output and compare it against §4D.
3. Update the Story 14 file status/progress, `evidence-story-14.md`, the
   Phase 143 `current-phase-status.md` story row, Where-we-are text, and all
   exit boxes only when the ledger is complete. Update
   `pm/roadmap/holdspeak/README.md` Last updated / current-phase pointer as
   the operating cadence requires. The PMO status/evidence/contract action is
   deliberately last and follows the repository’s Delivery Workbench gate.

**All commands use isolated HOME.** The final suite baseline command is:

```bash
HOME_REAL=$HOME; HOME=$(mktemp -d) \
PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright \
npm_config_cache=$HOME_REAL/.npm \
uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py
```

Build and targeted commands receive the same `HOME=$(mktemp -d)` discipline;
the final evidence keeps stdout/stderr and exit status rather than piping away
the failed-node list.

## 6. [ORCH-CALL] items

1. **Swift scope at phase close — recommend ACCEPT.** Record a scoped
   Python/web production PASS for kill criterion 3 and explicitly retain seven
   Swift physical leaves as HELD under the owner’s web-first ruling; do not
   imply a global zero-bypass result. The future Swift recreation owns them.
2. **Cross-product chaos shape — recommend ACCEPT the one-restart composition
   runbook, reject literal-SIGKILL ceremony.** Existing families prove their
   own crash boundaries. One shared durable-state test closes the useful gap
   without multiplying browser/process flakes.
3. **Existing owner-shot disposition — recommend VERIFY, not assume.** Stories
   12/13 record shots sent to the owner and e2e walks, but their progress text
   does not itself record a final owner verdict. Confirm the merge/owner record
   suffices under Constitution IX.4; otherwise obtain the owner’s view before
   checking the glass exit row.
4. **Expected-red full suite close rule — recommend ACCEPT exact-baseline/no-
   branch-new, never a false raw-green claim.** The 11 inherited nodes are
   external, named ownership. Story 14 still refuses any new failure, including
   a reclassified 393 glass failure.

## 7. Risk register

| Risk | Signal | Containment |
|---|---|---|
| Test fix masks a product loading defect. | 393 fails after a true readiness wait, page errors, or screenshots show incorrect glass. | Treat as product bug and return it to the Assignments surface; never hide it with retries/sleeps. |
| Chaos run becomes a second router implementation. | New controller/schema/recovery framework appears. | Limit it to existing production composition and durable rows; test only. |
| Close ledger mistakes old evidence for production-path proof. | Row has no test/capture/tree ID or only prose/component mock evidence. | Refuse row completion; add the narrow proof or label carry honestly. |
| Held Swift leaves become silently erased. | Census says zero without listing seven leaves. | Criterion 3 ledger row must carry hold branch, owner ruling, and future owner. |
| Baseline failures hide a regression. | Final failure set differs from the named 11 or a serial run reproduces a “flake.” | Compare exact node IDs, reproduce against main where needed, and keep Story 14 open for branch-new failures. |
| Close status outruns Story 15 or owner glass review. | Story 15/evidence absent; no owner-shot disposition. | Treat both as hard final-flip gates, while allowing Story 14 implementation/proofs to begin now. |

## Planning summary

- Kill criteria: 10 already evidenced; 2 need closeout proof; the Swift scope is
  an explicit owner-ruled hold, not a fabricated zero.
- The only meaningful chaos gap is a one-restart cross-product composition
  proof; per-family crash/hostile-input coverage is already broad.
- Intake: one genuine 393 hydration race to stabilise; three Story-13 ledger
  items closed by Story 11; audit carries are explicitly classified above.
- Final suite truth is 11 inherited red nodes, documented with owners; no
  branch-new node is acceptable.
- Slices: S1 glass/chaos proof, S2 write-once ledger, S3 final evidence and
  gated status/document updates after Story 15.
- Four ORCH-CALLs: Swift wording, chaos mechanism, owner-shot disposition, and
  expected-red baseline rule.

## 6b. Orchestrator dispositions (2026-08-27)

All four recommendations ACCEPTED, decided by the orchestrator as
tie-breaker:

1. Swift scope: scoped Python/web PASS + seven leaves HELD under the
   owner ruling; no global-zero claim. The frozen bridge branch
   (`hold/hs143-10-slice5-swift-bridge`) is the recreation seed.
2. Chaos: the one-restart cross-product composition runbook ships; a
   literal SIGKILL harness is rejected as ceremony (yolo bar).
3. Owner-shot record: SATISFIED BY THE SESSION RECORD — Story 12's
   shots were explicitly viewed on the owner's request before their
   merge order; Story 13's final set was delivered before the owner's
   merge word. Both merges followed shot delivery; the glass exit row
   may check with those citations. No re-ask needed.
4. Close rule: exact-baseline/zero-branch-new, never a raw-green
   claim; the 11 inherited nodes ship in the ledger with named
   non-router ownership; a recurrence of the 393 glass flake after its
   ready-barrier fix counts as branch-new, not baseline.

Build order (after Story 15 merges): S1 (two kill-criteria proofs +
the flake ready-barrier fix + cross-product runbook), S2 (the
write-once closeout ledger), S3 (phase-exit doc flips + final sweep +
close). The forbidden-vocabulary grep from Story 15 lands as a guard
in S1 if cheap, else ledgered.
