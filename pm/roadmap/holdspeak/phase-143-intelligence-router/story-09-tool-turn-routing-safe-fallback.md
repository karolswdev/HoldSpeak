# HSEGHS001HS104-143-09 - Tool Capability Foundation and Safe Routing

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
- **Depends on:** 143-06, 143-07
- **Unblocks:** 143-13, 143-14
- **Owner:** unassigned

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
