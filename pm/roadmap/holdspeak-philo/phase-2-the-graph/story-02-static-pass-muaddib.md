# PHILO-2-02 - The static pass, Muad'Dib

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

The Philo package already holds the connections and actions layers (openapi.json, capabilities.yaml, components.yaml, domain-model.yaml, integrations.yaml, trust-boundaries.yaml, schema-inventory.json). It has no edges layer and no consequences layer, and it says what exists, never whether it is wired through. One brain reads the tree and builds the graph.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] From the tree alone (no hub), every edge is enumerated: browser verbs (verbRegistry, applications.ts, every library Button `onClick`), keyboard and the hotkey, timers (heartbeat, intel drainer, schedules), WebSocket frames, the 82 MCP tools, CLI verbs, connector webhooks, engine replies.
- [ ] Every edge is linked to its interface, connection and action with evidence path:line; an edge whose chain breaks statically (a handler that resolves nothing, a route with no service, a service with no table) is a finding.
- [ ] Orphans both ways are listed: verbs with no effect, effects with no verb (capabilities.yaml entries with no interface), faces with no state, states with no face.
- [ ] The pass reads the existing inventories and marks each Philo claim it can verify or contradict (doc drift bin).
- [ ] Output: `docs/internal/philo/graph/static-muaddib.json` + `static-muaddib.md` in the four-bin, ranked report shape; Astra's check recorded beside it.

## Test plan

- **Unit:** the output validates against the schema of story 01.
- **Integration:** n/a.
- **Manual / device:** none; this pass never starts the product.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
