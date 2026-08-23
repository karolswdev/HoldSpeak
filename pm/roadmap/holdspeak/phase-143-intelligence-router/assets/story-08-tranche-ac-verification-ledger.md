# Story 08 tranche A–C — orchestrator verification ledger (2026-08-22)

All commands run by the orchestrator from a quiet tree; outputs read from
files. Worktree `.tmp/worktrees/hs143-08` at the tranche head (uncommitted);
baseline = root repo, `main` @ `89d232f3`.

## Focused proof

- `tests/unit/test_phase143_meeting_route_primitives.py`: **29 passed** —
  includes the full spec-v2 (a)–(j) adversarial matrix, the P1
  non-default-policy admission + race refusal, and the reversed
  unknown-dispatch posture (stays reserved after delayed egress).
- Adjacent §13 authority matrix (12 suites): **224 passed, 0 failed** after
  guard regeneration.
- Static: compileall clean; `ruff --select F` clean (one F401 fixed:
  unused `Mapping` import in `inference_service_route_policy.py` — note:
  the implementation worker's report claimed ruff green on that same file
  list; flagged as report-inflation, caught by orchestrator rerun);
  `git diff --check` clean.

## Guard regeneration (design stabilized first, per HANDOVER §8 P1)

- `tests/fixtures/db_schema_canonical.txt`: regenerated with the test's own
  logic; diff = exactly the six new inference tables + their immutable
  UPDATE/DELETE triggers + the `inference_route_plans.principal_policy_sha256`
  column. Green.
- Routing-authority census: two `profile_id` anchors in `sync_service.py`
  shifted 652→658 / 667→673 by the six inserted hostile-sync lines; explicit
  census review confirmed identical references and classification
  ("V1 profile and workbench sync payload", 143-11). Green.

## Full CI-style suite triage (isolated HOME, xdist, no metal)

- Tranche worktree: 99 failed / 6326 passed → after building the gitignored
  web bundle in the worktree (CI builds it too): **71 failed / 579 passed**
  across the 44 previously-failing files.
- Baseline (`main` @ 89d232f3), same files, same env, same contention:
  **71 failed / 579 passed** — failure NAME SETS BYTE-IDENTICAL
  (scratchpad `wt-fails.txt` vs `bl-fails.txt`, `diff` empty).
- Verdict: **zero Story 08 regressions.** The 71 are local-environment
  failures reproducing on clean main: seeded profile points at
  `~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf` which an isolated HOME
  hides (409 readiness cascades), LLM-vs-deterministic expectations without
  a reachable endpoint, and playwright/pytest-timeout contention. Main CI
  is green (ninth straight), so these are local-env-only, ledgered here —
  not silently matched, not the tranche's debt.

## Counsel trail

- Round 1 (Terra, design): DO-NOT-RATIFY → six findings adopted → spec v2.
- Round 1b (Sol, sounding board): CONCUR-WITH-NOTES; forward obligations
  banked; later amended by the owner's yolo direction (see counsel file).
- Cold audit (Sol, §16): in flight at the time of this ledger entry;
  verdict to be appended by the orchestrator.

## Cold audit round 1 (Sol) — DO-NOT-RATIFY, 2026-08-22

Sol reran the primitive file (29 passed), the hostile subset (22 passed),
the adjacent matrix (224 passed), guards + censuses (8 + 42 passed), and
statics — then wrote 9 original adversarial probes. Six passed
(activate-crash rollback, concurrent reconcile, policy-flip refusal,
committed-replay pinning, settled-replay idempotence + mutated-reference
refusal). Three exposed gaps:

1. **P0 bundle seal (probe 4):** late `admit_on_frozen_route` on an old
   bundled route physically dispatched while the parent was CANCELLING —
   the Stop fence stopped existing executions but did not seal the routes.
   → spec amendment A1; fix round briefed.
2. **P1 equal-total policy swap (probe 8):** per-route policy substitution
   accepted when the aggregate budget stayed equal. → A2; fix round.
3. **P1 historical projection (probe 9):** exact v1 adapter output rejected
   by the coordinator's current-registry validation. → A3; fix round.
4. **Determination (probe 2):** the independent-lifecycle-witness rule is
   provably unverifiable against a hostile in-process provider. → A4:
   ruled a recorded note per the owner's yolo rigor bar (providers =
   composition-owned code, no trust boundary); enforcement = per-adopter
   counsel review + adopter proof tests. NOT a mechanism.

Sol also independently confirmed: census anchor change classification-
preserving; SERVICE inheritance impossible; principal evidence deep-
reconstructed; cross-substitution and provenance tamper refusing; and the
human-compliance answer — no owner exposure today (no production
entrance), real exposure only if an entrance adopted the unfixed
checkpoint.

## Fix round after cold audit (Terra) + orchestrator verification, 2026-08-22

- **A1 bundle seal:** implemented at the SINGLE `inference_route_executions`
  insert point (controller `start_execution_in_transaction`): bundle-member
  join + LEFT JOIN `kernel_parent_runs`, refuses
  `inference_route_execution_parent_sealed` unless every joined parent is
  OPEN; missing parent also refuses (fail-closed); check precedes the
  insert in the same transaction. Orchestrator verified the single-insert
  claim by repo grep and read the seam. Audit probe 4 now dies on the seal.
- **A2 per-route fingerprints:** pre-admission capture of (id, revision,
  sha256, attempts) per declaration; per-route comparison in the bundle
  transaction before the aggregate net. Audit probe 8 now refuses with
  "Parent route policy changed during admission".
- **A3 frozen-definition projection:** shared reconstruction
  (`frozen_capability_definition_in_transaction`) feeds coordinator
  projection and durable winner replay; proven at coordinator level by
  `test_preupgrade_frozen_route_binds_after_registry_upgrade` (extended
  end-to-end) + current-revision pin. (Audit probe 9 bypasses the
  coordinator by design; its output is not evidence either way.)
- Primitive file now 34 tests. Adjacent §13 matrix after fixes:
  **229 passed, 0 failed** (one more census anchor drift 1129→1170,
  review-confirmed classification-preserving: same
  `RoutedInferenceCoordinator.execute` runner.invoke call, displaced by
  the projection changes). Statics green.
- Cold-audit round 2 (same Sol context) dispatched: verify fixes 1–3
  adversarially, judge A4 scoping honestly, update §16 verdicts.

## Cold audit round 2 (Sol) — RATIFY, 2026-08-22

All round-1 findings closed; A4 scoping explicitly judged honest ("explicit
rather than pretending the service can determine which tables arbitrary
Python code read") — no dissent. Round-2 evidence beyond the reruns:

- Seal: repo-wide insertion census confirms ONE executable insert site;
  all four admission entrances funnel through it. New probes: ordinary
  late admission, pre-frozen plan passed directly to the controller,
  missing parent row, command replay after sealing — all refuse
  `inference_route_execution_parent_sealed` with zero partial rows;
  replay reconstructs only the existing stopped execution.
- Fingerprints: original 2+4→4+2 swap refuses per-route; a placement-only
  assignment edit with an identical policy fingerprint is lawfully
  accepted (shell claims policy budget, not placement) — correct
  boundary. No surviving same-total substitution found.
- Frozen projection: coordinator + durable replay succeed with a
  poisoned current registry (raises if consulted) — frozen-definition
  validation proven independent of process registry.
- Reruns: primitives 34/34; hostile/seal/policy subset 28/28; adjacent
  §13 matrix 229/229; census guards 15/15; statics green.
- §16 checklist: ALL SEVENTEEN ITEMS PASS (item 2 scoped under A4).

**Tranche A–C is cold-ratified.** Counsel's sitting paragraph preserved in
the audit transcript and quoted in the orchestrator's close report.


## Phase B checkpoint — RATIFIED (Sol, three rounds, 2026-08-22)

Round 1 (7 probes): DO-NOT-RATIFY — 3 blockers (Stop crash windows losing
aftercare; swallowed fence failure; frozen deployment not controlling the
physical transcriber) + 5 further findings. Hardening round F1–F8
(`13645888`, incl. 28 zombie legacy_ tests ported-or-deleted).
Round 2 (6 fresh probes): F3–F8 closed; two remaining claim-race blockers
(fence-pending row claimable with parent OPEN; recovery upsert resetting a
running claim) + factory-less 'active' seam. Surgical round (`9dc8dde1`) —
claim selectors require route_fence_pending=0; upsert guards running rows;
one caller-sweep catch (transcript-refresh owner release); factory-less ⇒
record_only/transcriber_unavailable.
Round 3: RATIFY. Sol judged its own probe deltas (3 lawful pre-fix-assertion
reversals), ran the four successor tests, added a scheduled-selector
interleaving probe (one claim, only after fence durable + marker cleared),
independently reran the chartered matrix (313/313), and accepted the
implementer's OPEN-parent normal-path argument point by point. Tuesday
judgment: "I would use this on a tired Tuesday now."

## Recorded limitations

- Best-effort physical cancellation after a committed fence: a failed physical
  cancel reports success while provider work may continue; the durable fence +
  late-output discard law bound the harm to wasted provider compute for at most
  the in-flight attempt (no state corruption, no publication). Ruled a recorded
  limitation per the owner minimal-ceremony bar (code-review finding 8,
  2026-08-22).
