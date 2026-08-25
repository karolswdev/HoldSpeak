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
