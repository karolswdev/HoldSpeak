# HSEGHS001HS104-143-09 - Tool Capability Foundation and Safe Routing

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-06, 143-07
- **Unblocks:** 143-13, 143-14
- **Owner:** unassigned

## Progress (2026-08-25)

Work rides `feat/hs143-09-tool-routing` from main `51989047`. The
implementation plan (`assets/story-09-tool-foundation-plan.md`) is
authored from the ruled catalog/context proposal — 42 obligations, no
design-counsel round (the contract is already ruled; ten bounded
implementation choices decided by the orchestrator as tie-breaker,
dispositions in-file). **Part A slices A1+A2 are SHIPPED**: the closed
MODEL_TURN capability projection (provider projection structurally
excludes lease/owner/policy/MCP/transport/credential fields), the
versioned qualified manifest with `tool_qualification` (legacy
manifests project palette 0 — never backfilled as qualified),
server-side foundation-readiness preflight (required tool work refuses
pre-dispatch as `tool_required_unavailable`), the durable
`TurnCapabilityLease@1` + `ToolTurnController` transaction authority
(atomic parent/bundle/route/lease start on the `tool.turn` parent
kind, replay-safe reservations under aggregate + per-capability
budgets, Stop fence, restart reconstruction from persisted terms,
lease expiry/revocation terminalizes without model fallback), and the
five-table private ledger family (effect-child rows carry only
references/hashes/receipt state). Schema landed additively with the
`kernel_parent_runs` CHECK rebuild and an old-shape-DB preservation
proof. Sweep: **6496 passed / zero branch-new**. Next: A3+A4 (model
steps + tool-call admission/effect adoption), then the A5 gate with an
opus verification leg before Part B.

**A3+A4 SHIPPED (2026-08-25).** A3: each reserved model step freezes
its own private operation request plan under the turn's frozen
assignment and runs as exactly one `InferenceFallbackController`
execution — separately admitted and receipted, replay-idempotent, with
lifecycle guards preserving frozen step identity. A4: tool calls are
separately admitted as real kernel `tool.call@1` children under the
`model-turn-tool-service` principal with schema-drift and
confusable-capability refusal; results enter only as the closed typed
envelope (a typed `unavailable` is never a model failure and carries
no material); effect receipts adopt exactly once on replay/restart
while an absent post-dispatch receipt terminalizes
`effect_indeterminate`; restart reconstruction reconciles effect truth
before returning a usable turn (real-DB boundary proofs). One
DECLARED proof gap, ruled by the orchestrator: the 1/N physical-child
cardinality and parallel-result-ordering proofs require the
provider-neutral `ToolModelAdapter` (ORCH-CALL 9) — it is Part-A seam
material and lands in the A5 gate round with those proofs, alongside
the opus verification leg. Sweep: **6503 passed / zero branch-new**.

**A5 SHIPPED — THE PART A GATE IS CLOSED (2026-08-25).** The
provider-neutral `ToolModelAdapter` contract landed
(`services/tool_model_adapter.py`: render once → transport once →
parse exactly one closed answer-or-tool-call candidate; no loop, no
retry — the coordinator/controller stay attempt authority), wired
into the model-step seam with a deterministic internal reference
adapter that fakes only the wire format. The outstanding proofs
closed: 0/1/N physical-child cardinality (pre-dispatch refusal = 0
children; ordinary step = exactly 1 admitted child + receipt; frozen
retry policy = N distinct admitted children, one winner) and parallel
read-result ordering (reversed completion keeps provider-call ordinal
order in durable state and in the next step's material; forward and
reverse completion produce identical canonical next-request hashes).
The gate run itself caught and fixed four things, including
random receipt IDs leaking into provider material (request identity
now stable) and a missing durable result table in the snapshot. The
paired **opus verification leg audited all of Part A: "PART A SOUND —
gate may close"** — all five acceptance criteria verified in the
tree, proofs production-honest, service principals minimally
authorized, ledger triggers enforcing lawful transitions, restart
reconstruction truthful, schema additive with proven CHECK-rebuild
preservation, and the Part B boundary clean (zero production surfaces
import the tool machinery). Two ledger notes: byte-length token
approximation (conservatively over-reserves) and the turn-state
transition to refine when B adds multi-step loops. Sweep: **6511
passed / 48 failed / ZERO branch-new — not one non-baseline name.**
Part B (tool-qualified routing and safe fallback, B1–B4) may begin.

**B1+B2 SHIPPED (2026-08-25).** B1: required-tool routes include ONLY
deployments with exact executable tool qualification (qualified
structured tools, positive palette, native dialect, matching frozen
manifest + deployment capability hashes, composed foundation);
unqualified deployments stay lawful for ordinary work but are
invisible to tool routes; no qualified candidate refuses
`tool_required_unavailable` before ANY dispatch; frozen qualified
routes reconstruct their captured revision — a later manifest edit
cannot retarget (acceptance criterion 4 at routing depth). The
fallback controller proves a model route is bound to a live exact
ToolTurn lease before nonzero tool policy is permitted. B2: the
internal service-owned `ToolTurnFoundationService` (ORCH-CALL 6 —
no production surface imports it, grep-proven as a test) composes a
complete real multi-step turn — model step → tool call → continuation
model step → final answer — with two separately admitted
`inference.invoke` children, a separately admitted `tool.call` child,
individual receipts, and a safe `ToolTurnReceipt@1` projection
(acceptance criterion 5 end-to-end). The opus ledger note is
resolved: the turn state machine is now truthful across the loop
(model_running → tool_requested on a tool candidate, → result_ready
on a final answer; budget exhaustion durably terminalizes
`model_step_budget_exhausted` BEFORE raising; Stop fences the parent
bundle first, then the turn, at both model and tool boundaries).
Sweep: **6518 passed / zero branch-new.** Next: B3 (the ruled
tool-qualified correction/fallback table), then B4.

**B3+B4 SHIPPED — PART B CONSTRUCTION COMPLETE (2026-08-25).** B3
implements the ruled tool-bearing fallback table exactly: a closed
disposition bridge (unknown events raise, never launder); malformed
native calls consume ONE bounded corrective model step with zero tool
dispatch, then advance only to TOOL-QUALIFIED legs (every fallback leg
re-checked for qualification, palette sufficiency, and permissible
egress); a read-only typed `unavailable` feeds forward only within the
frozen lease/budgets and only when the frozen operation schema permits
naming the limitation; tool outage is never auto-mapped to model
failure; a receipted effect is adopted and a repeat attempt refuses
`receipted_effect_adopted`; the terminal set (unknown effect
completion, permission denial, approval refusal, Stop, lease expiry)
never advances; parallel results keep provider-call ordinal identity
under replanning. `ToolTurnReceipt@1` discloses exact tools used,
proposed vs executed effects, and every model-fallback leg — with
nonce/terms/private material proven absent. B4 proves all five
acceptance criteria end-to-end on the real broker path across two
qualified legs (correction + effect adoption + outage + fallback in
one turn; required-tool refusal with zero children; crash-at-boundary
restarts truthful at the model, tool, and effect boundaries; Stop
races fenced at both boundaries). The paired **opus audit verified the
fallback table clause by clause: "PART B SOUND — story may close"** (3
safe ledger notes: byte-length over-reservation; any-effect replay
guard equivalent under the P=1 effect ceiling; dispatch-unknown
correctly owned by the generic controller). Sweep: **6533 passed /
zero branch-new** — third consecutive pure-baseline sweep.

## Problem

The ruled Tool Capability Foundation is design-only. This story makes its
controller, durable private lease, ledgers, and child laws executable before
adding tool-capable model fallback.

## Scope

- **In:** Implement the bounded server-owned ToolTurn controller, canonical
  private capability-lease ledger, model/tool/effect child ledgers and budgets;
  then route each model step through a frozen assignment with tool-qualified
  correction/fallback, receipt adoption, and separate owner truth.
- **Out:** Owner MCP tokens/catalogs and route-controller ownership of tool calls.

## Acceptance criteria

- [ ] Fallback cannot expand palette, scope, budgets, policy, or egress.
- [ ] Receipted effects are adopted; unknown effect completion never falls back.
- [ ] Tool service outage is a typed result, not automatically a model failure.
- [ ] Required tools refuse before dispatch when no qualified profile exists.
- [ ] Every model step and tool call is separately admitted and receipted.

## Test plan

- **Unit:** confusable calls, schema drift, lease expiry/revocation, palette escalation.
- **Integration:** crash at model/tool/effect boundaries, Stop races, receipt adoption.
- **Manual / device:** exact tools-used, proposed/executed effect, and model-fallback disclosures.

## Notes / open questions

Part A is the concrete Tool Capability Foundation gate; Part B cannot advertise
or execute tool use until Part A's service/controller/ledger tests pass.
