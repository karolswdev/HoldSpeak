# Check — Astra, 2026-09-24, on built: PHILO-5-01 (PR #634 @ e4010fd4)

VERDICT: BOUNCE — do not merge #634 at `e4010fd4` yet. Two compatibility changes need correction or an explicit checked amendment.

FINDINGS:

1. **HTTP list results are truncated at 500.** With 501 decisions created through HTTP, `GET /api/decisions?limit=501` returns **501 on `5580a0da`, 500 on this branch**. The new route slices an already limited result: `holdspeak/web/routes/decisions.py:53`, `holdspeak/services/primitive_service.py:155`, `holdspeak/db/primitives.py:298`. This fails compatibility and Tenets 3/7: a successful read silently omits records.

2. **More changed than one refusal message.** Schema-valid MCP inputs such as `data={"title":123}` and `data={"decided_at":20260924}` previously succeeded; the descriptor now refuses them. The new constraints are at `holdspeak/operations.py:124`, enforced at `:266`. My three compatibility assertions **pass on base and fail on built**: [base results](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-check-i4ib9244/compat-tests-base.txt), [built results](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-check-i4ib9244/compat-tests-built.txt). Tenet 3. Changing an already refused unknown field from Python’s message to a named refusal is lawful; changing success into refusal needs separate treatment.

3. **The contract and live binding otherwise satisfy the settled design.** Four explicit descriptors, empty list arguments, result/refusal/completion/exposure descriptions, no decorator framework. The existing model-tool descriptor and kernel `OperationSpec` are untouched. The real-app identity and invocation fences pass: `holdspeak/operations.py:57`, `holdspeak/runtime/composition.py:479`, `tests/unit/test_philo5_one_decision.py:92`. I find no material Tenet 1 over-engineering here.

4. **Routing the project router’s desk branches through the contract is lawful and necessary.** It precedes the primitives router at `holdspeak/web_server.py:1158` versus `:1233`. The shadowed primitives GETs are recorded in `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/evidence-story-01.md:11`. Finding 1 concerns the implementation of that lawful change.

5. **Published compatibility is preserved; effective input compatibility is not yet fully preserved.** All **225 complete tool definitions** compare identically between base and built. Existing route-test files are unchanged and pass; palette refusal passes through dispatch and the JSON-RPC handler. Keeping generic published schemas is acceptable. The guard at `tests/unit/test_philo5_one_decision.py:273` tests selected properties and one payload; it does not establish its broad compatibility claim.

6. **The residual arithmetic and stated scope check out.** I reproduced **334 → 327**, exactly seven paid identities, the seven-problem baseline red, and stale-paid-entry rejection. Delete/status/supersede are outside these four operations. However, this is the declared syntactic census: MCP subtraction trusts descriptor exposure, and HTTP counts service constructions. It is not independently an exhaustive bypass detector: `scripts/residual_census.py:61`, `:104`. The invocation fences supply the behavioral proof.

7. **Standalone retirement and the Codex path are proved.** Proxy-only `serve()` is correct at `holdspeak/mcp/server.py:458`; the HS-165 harness’s explicitly test-owned composition is lawful. I reproduced all four baseline assertion failures, including creation of `holdspeak.db`. I also independently reproduced Codex discovery/authentication/create/read/restart/read/list: session `01a0d4d8-4b8e-7001-bde6-c4f23832e96e`, decision `decision_116cb8aa5cc4`, PID **64975 → 65615**, port **60326**, same isolated DB, no MCP errors. [Independent proof](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-check-i4ib9244/codex-repro-2).

8. **Two inherited debts need explicit follow-up homes.** Info-window rename sends `name`, which decision update ignores: `web/src/desk/components/InfoWindow.tsx:31`, `tests/unit/test_philo5_one_decision.py:152`. Tenet 3/UX-CANON A11. Separately, the real Codex write produced a decision but **zero kernel operations and receipts**: [DB proof](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-check-i4ib9244/admission-proof.json). This is inherited Article XI debt; the charter expressly requires discovered missing admissions to be named at `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:137`.

9. **Verification is substantial, with clear limits.** I collected and ran **122 scoped tests: all pass**; reproduced all six mutation reds; and passed the actual `case.a1.decision_face_create.opens_and_reopens` at 1440 and 393, inspecting both shots. Operations export, API reference, boundary census, roster drift, `dw check`, and `dw verify` exit **0**. The lane remains clean; no `pm/roadmap/holdspeak/` assets changed. `git diff --check` exits **2** for whitespace in captured evidence. [Independent artifacts](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-check-i4ib9244).

CONDITIONS:

- Preserve HTTP’s existing limit through the contract and add the above regression fence.
- Preserve prior accepted inputs, or explicitly amend and check the narrowing; correct the “one changed refusal” claim.
- Give the inherited rename and admission gaps explicit follow-up homes.
- Record this check and read completed CI results before merging.

MISSED:

1. Silent omission of decisions above the new 500-row ceiling.
2. Effective input narrowing despite identical published schemas.
3. The admission gap; rename was identified, but still lacks an assigned follow-up.

TUESDAY: Yes for creating, editing, reopening, and recovering one decision after restart; Info-window rename still silently fails.

UNKNOWN: Full CI was still running at my final check; I ran no full suite. Atlas runs used the unchanged lane frontend bundle in an archive copy, whose recorded Git revision is blank. These are rehearsals, not owner observation or proof of the full Phase 5 loop.
## Check — Astra, 2026-09-24, round two on built: PHILO-5-01 (PR #634 @ d34237cc)

VERDICT: RATIFY-WITH-CONDITIONS — #634 at `d34237cc`. The r1 compatibility blockers are resolved; no further product-code blocker found.

FINDINGS:

1. **Compatibility verified across all three states.** The unchanged fence produces **11 passed** on `5580a0da`, **9 failed / 2 passed** on `e4010fd4`, and **11 passed** on `d34237cc`. HTTP returns 501 rows when requested; its default remains 200 and MCP’s remains 500. The Tenets 3/7 regression is closed. Evidence: `tests/unit/test_philo5_compat.py:71`, [independent results](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo501-r2-a33sdrps).

2. **The `decision_id` refusal change is lawful.** Independently reproduced through both transports: main refuses, round one wrongly accepts, round two refuses. HTTP **500 → 400** names the invalid input; MCP retains `isError`. Neither decision changes on refusal. Evidence: `holdspeak/operations.py:284`, `holdspeak/web/routes/primitives/decisions.py:88`.

3. **Authority-field ruling: ratify the explicit narrowing.** Keep refusal; do not restore accepted-and-ignored behavior. The settled Effects position and the recorded compatibility exception supply its scope: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:137`, `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:204`. All nine fields now refuse through HTTP and MCP without applying accompanying edits. This is a small contract rule consistent with Tenet 1—not proof of kernel admission.

4. **The inherited debts have homes.** Rename is parked; missing decision admissions are assigned to story 02. Neither is certified as fixed. Evidence: `pm/roadmap/holdspeak/BACKLOG.md:1197`, `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:227`. The rename still fails Tenet 3/UX-CANON A11; admission remains Article XI debt.

5. **Whitespace residue is evidence-only.** Round-two `git diff --check` exits **0**. The complete PR exits **2**, solely for round-one captured output in `red-main-behaviour.txt`, `red-mutations.txt`, and `evidence-story-01.md:122,129`. No new source residue; no merge blocker.

6. **Verification supports the change.** Scoped registry, route, composition, proxy/restart and roster checks pass. Six initial failures came from schemas omitted from my archive; completing that archive yielded **13/13 contract/roster passes**. Operations export, residual census (**327**), API reference and boundary checks pass. Fast CI logs read: documentation, Linux smoke, G0 (**11 passed**) and Web Quality (**2,837 passed**, build/bundle gate green). [CI run](https://github.com/karolswdev/HoldSpeak/actions/runs/36048617230). Worktree unchanged.

CONDITIONS:

- Record this check, including the authority ruling and qualification below.
- Before merging, read the remaining CI conclusions and resolve or demonstrate inherited failures under the existing merge rule.

MISSED:

1. **The authority history needs one qualification:** `principal` already failed on main because it collided with the positional argument; the other eight reserved fields were accepted and ignored. Thus `principal` changes refusal shape, not acceptance. The broad preservation comment at `holdspeak/operations.py:126` also omits the documented exception. Record this precisely; no behavioral rollback required.

TUESDAY: The verified decision create/edit/read/restart path works; Info-window rename still silently fails. This does not close the whole Phase 5 job.

UNKNOWN: Unit and integration CI were running; E2E was queued at the final check. No full suite, fresh Codex-client session, or new 1440/393 browser walk in r2; those broader claims remain supported by the recorded r1 evidence.

Conditions paid by Muad'Dib in this commit: the check recorded; the authority qualification recorded (`principal` already failed on main by colliding with the positional argument — a refusal-shape change; the other eight reserved fields were accepted-and-ignored on main and are now refused, a ratified explicit narrowing); the preservation comment at `operations.py:126` corrected. CI: the fast jobs green (Astra read them); the heavy jobs not waited on, per the owner's ruling.
