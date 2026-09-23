# PHILO-2-02 - The static pass, Muad'Dib

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

The Philo package already holds the connections and actions layers (openapi.json, capabilities.yaml, components.yaml, domain-model.yaml, integrations.yaml, trust-boundaries.yaml, schema-inventory.json). It has no edges layer and no consequences layer, and it says what exists, never whether it is wired through. One brain reads the tree and builds the graph.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] From the tree alone (no hub), every edge is enumerated: browser verbs (verbRegistry, applications.ts, every library Button `onClick`), keyboard and the hotkey, timers (heartbeat, intel drainer, schedules), WebSocket frames, the 82 MCP tools, CLI verbs, connector webhooks, engine replies.
- [x] Every edge is linked to its interface, connection and action with evidence path:line; an edge whose ACTUAL wiring breaks (a handler that resolves nothing, an execution owner that never performs the promised operation) is a finding; a route, table or receipt is not required merely to complete the shape (brief §§1–2, 6).
- [x] Orphans both ways are listed: verbs with no effect, effects with no verb (capabilities.yaml entries with no interface), faces with no state, states with no face.
- [x] The pass reads the existing inventories and marks each Philo claim it can verify or contradict (doc drift bin).
- [x] Output: `docs/internal/philo/graph/static-muaddib.json` + `static-muaddib.md` in the three-bin, ranked report shape (brief §9); Astra's check recorded beside it.

## Test plan

- **Unit:** the output validates against the schema of story 01.
- **Integration:** n/a.
- **Manual / device:** none; this pass never starts the product.

## Notes / open questions

**Sealed 2026-09-22 (Opus worker, 205 tool calls; the sealing law held — no read of ../wt-philo-2-03 or static-astra.*).** `static-muaddib.json` 1.39 MB, deterministic (two builds, one md5), validator OK: nodes 1,780 (edge 1,658 · state 58 · interface 28 · action 28 · connection 8), links 138, cases 69 copied verbatim, claim reviews 13 (9 verified · 2 contradicted · 2 unresolved), findings 15 (11 product-defect · 2 tooling-debt · 2 doc-drift), 2,153 source refs re-anchored with 0 mismatches. Census: 23 applications, 52 verbs, 1 hotkey, 44 WS frame kinds, 7 timers, 29 CLI commands, 225 MCP tools, 5 connector inputs, 3 engine boundaries, 1,223 control sites (951 library · 243 raw · 29 unclassified), 569 HTTP paths. JOBS: wired J1 J2 J4 J5 J7 J9 J10 J11 · broken J3 (the Download path never finishes) and J6 (the arrival never learns the summary landed) · unverifiable-statically J8. Top findings in `static-muaddib.md`. Tooling: `uv run python scripts/philo_graph_validate.py` needs `--extra dev` (jsonschema lives in the extras); five atlas cases trigger by clicking `main.chair` (a placeholder, for story 01's atlas to fix before the live pass). Lane-brief path drift recorded: ConciergeCore lives under `web/src/features/concierge/`.

Sealing law (brief §§6–7, 9): this pass's report is sealed (committed on its own branch) before its author reads any other pass; shared schema, fixture recipes and rig calibration are preparation, not shared findings. Every run records source revision and dirty-tree status, contract versions, runtime provenance and unexercised cases with reasons.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
