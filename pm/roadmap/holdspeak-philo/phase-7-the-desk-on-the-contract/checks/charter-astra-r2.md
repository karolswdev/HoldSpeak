# Check — Astra, 2026-09-25, r2 on the Phase 7 charter draft (PR #650 @ c01d5a7a)

VERDICT: RATIFY-WITH-CONDITIONS

Suitable to present as a conditional proposal. The two new admissions are correct, but r1 is not fully paid: the rename exemptions, held-write continuation and D4 exclusion still need correction.

FINDINGS:

1. **Both new admissions reproduced through the real service.** In a throwaway DB:
   - `kb.create(kb_id="kb", name=...)`, without `member_ids`, changed membership `(kb, note:n).deleted` from `0` to `1`.
   - `zone.create(directory_id="child", name=...)`, without `parent_id`, changed `child.parent_id` from `"parent"` to `NULL`; its note membership survived.

   These match `holdspeak/services/primitive_service.py:253` and `holdspeak/db/primitives.py:1114`. **Ratify both admission readings.** [Probe DB](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p7-r2-xy4d0gmh/probe.db).

2. **The exempt set still hides placement changes during concurrent writes.** Ordinary sequential note edits, Thought saves, plain-note deletion, KB deletion and renames preserved placement in my probes. However, both rename implementations read placement and then write that snapshot back:
   - KB rename reads `existing.member_ids`, then replaces memberships: `holdspeak/services/primitive_service.py:269`.
   - Zone rename reads `existing.parent_id`, then writes it back: `holdspeak/services/primitive_service.py:366`.

   I paused each rename after its real read and made another real service call. KB rename tombstoned newly added `note:b`; zone rename reversed a move from `p1` to `p2`, restoring `p1`. No mocked reads or injected rows. [Interleaving DB](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p7-r2-interleaving-__awfrpk/probe.db).

   **Keep plain renames exempt, but make them update only the requested fields.** Admitting every rename would obscure the defect. The charter must include this narrow repair and its real-producer fences. **Tenets 1/3/7; XI.1.**

3. **The held-agent path still lacks its execution continuation and owner affordance.** The existing decide route only calls `kernel.decide`: `holdspeak/web/routes/system/kernel_routes.py:63`. Approval transitions to `awaiting_execution`: `holdspeak/kernel/broker.py:257`.

   Reproduced through that HTTP route with the real `tool.call` codec: `awaiting_decision → awaiting_execution`, receipt `NULL`. This proves the existing transition, not future desk execution. [Kernel probe DB](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p7-r2-kernel-l6py75vq/probe.db).

   Story 02 must name what resumes execution after the original caller receives HELD, and what terminates abandoned work. The cited restart method only processes supplied native IDs: `holdspeak/kernel/broker.py:24`. Also, the existing approval face reads gate proposals, not arbitrary kernel operations: `web/src/desk/gate.ts:44`. Name the existing face adapter or amend “any face change” out of scope. An HTTP endpoint alone does not complete Tuesday. **Tenets 2/3; XI.2.**

4. **Position for the owner on approval:** inline approval of the owner’s authenticated gesture is lawful and required by `docs/internal/CONSTITUTION.md:184`; another confirmation would contradict it.

   **Holding an undelegated AGENT write is a real behavior change.** I reproduced immediate agent decision creation and filing, with zero kernel operations. Ratify the change explicitly, with the usable completion path from finding 3. Alternatively, grant bounded delegation; palette membership supplies no such approval. A live parent qualifies only when its signed continuation identities include this agent: `holdspeak/kernel/causation.py:65`.

   D4’s sidecar forwards an owner token, so that rehearsal proves OWNER compatibility, not the AGENT hold/delegation path. **Tenets 1/3; XI.3–4.**

5. **Position for the owner on contract refusals:** **yes, a malformed attempt at a known consequential operation owes a kernel refusal receipt.** Moving validation ahead of submission does not erase the attempt. `invalid_arguments` and `authority_in_arguments` currently escape before the service: `holdspeak/operations.py:643`. Both reproduced without receipts; direct malformed kernel submission produced a refused receipt.

   Preserve the named error, authenticated transport principal and zero effects; add the receipt for identifiable consequential attempts. Failed reads remain exempt under XI.5. A genuinely unknown operation with no identifiable consequential effect can remain a protocol refusal—do not invent an effect solely to journal it. Record that boundary explicitly. **Tenets 1/3; V.2 and XI.2/5.**

6. **The single MCP kernel-read operation is lawful supporting scope.** It gives a held caller a way to retrieve its eventual outcome, and reuses the existing authenticated read and agent-identity restriction: `holdspeak/kernel/broker.py:37`. Keep it read-only, declare its palette exposure, fence another agent’s refusal, and count it separately from residual retirement.

   Correct `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-02-membership-and-decisions-under-article-xi.md:25`: a HELD response cannot carry a terminal receipt yet. Specify pending-handle and terminal-result variants. **Tenets 1/3; XI.5.**

7. **D4 is meaningful context isolation, but it is not repository-access exclusion.** Installed Codex `0.155.1` confirms both flags exist. Its help says they suppress user configuration and execpolicy rules. The story itself concedes no filesystem sandbox: `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-04-file-it-and-find-it-without-the-repo.md:30`.

   An empty directory, fresh HOME and zero-read transcript can prove discovery succeeded without reading the repository. They cannot prove access was unavailable. Either run the client where checkouts are absent/unreadable and retain a failed-read probe, or obtain an explicit owner amendment to D4’s narrower observational claim. Keep the negative-control log fence. I independently recounted **25 + 3 = 28** commands; that correction is paid. **Tenet 3; D4; Article IX.**

CONDITIONS:

- Add the two rename repairs and interleaving fences; preserve genuinely plain-edit exemptions.
- Settle held-write resumption, recovery, owner access and pending-result semantics before story 02’s brief.
- Present findings 4 and 5 as explicit positions for the owner’s ruling.
- Enforce repository exclusion, or visibly amend D4 with the owner.
- Replace “r2 pays it” with the actual remaining conditions. The estimate and attachment correction are paid; Phase 6 closure is confirmed on main.

MISSED:

1. Highest owner cost: an exempt rename silently reverses another filing action.
2. Next: HELD or APPROVED can become a permanent waiting state without a reachable owner action and executor continuation.
3. Next: a successful cold-context rehearsal is reported as stronger access-exclusion evidence than it provides.

TUESDAY: The owner-token file/find/review job is useful; the undelegated-agent path does not yet have a chartered route from HELD to a result the tired owner can obtain.

UNKNOWN: Checked `c01d5a7a` through artifact/source inspection, isolated real-service probes, controlled real-call interleavings, the existing kernel HTTP route and retained-log counts. No fresh Codex rehearsal, browser walk, full suite or proposed Phase 7 fence was run. The worktree remains unchanged.