# The static pass — lane brief (PHILO-2-02 Muad'Dib · PHILO-2-03 Astra)

Both brains receive this text verbatim. The contract is `docs/internal/philo/briefs/graph-audit-brief.md` §§0–2, 6, 8, 9; this page only fixes the deliverable paths, the bounds and the sealing law. Read the brief first, then `docs/internal/philo/graph/atlas.json` (69 cases, 37 edges, 111 states: the ids you must reuse), `docs/internal/philo/graph/graph.schema.json` (+ `examples/graph.example.json`), `docs/internal/philo/data/README.md` and the four shards (Phase 1 record ids), `docs/generated/openapi.json`, `capabilities.yaml`, `components.yaml`, `domain-model.yaml`, `integrations.yaml`, `trust-boundaries.yaml`.

## Deliverables (this lane's files only)

1. `docs/internal/philo/graph/static-<brain>.json` — validates with `uv run python scripts/philo_graph_validate.py <file>` (schema + referential integrity + Phase 1 references). `observations` is empty (no hub in a static pass). `cases` references the atlas ids it traced (copy the case objects verbatim; do not invent cases). `claim_reviews` carry `pass: static` reasoning in `limits`.
2. `docs/internal/philo/graph/static-<brain>.md` — the §9 report shape (PASS: static; SOURCE revision + dirty; CONTRACT versions; JOBS: for each of J1–J11 the expected result and the STATIC verdict: wired | broken | unverifiable-statically, with evidence; GRAPH; COVERAGE; FINDINGS ranked by owner cost with bin; ORPHANS; UNKNOWN).

## Bounds

- **Deep trace, mandatory:** every edge the atlas names (37) and every control on the faces the eleven jobs touch (the arrival/Chair, the SETUP row and Concierge engine door, the Meetings review row and the summary face, the Desk memory shade and window, the BRIEF section, the Thought/note editor, the first-value gate): edge → interface → connection → action, each link with `path:line` evidence and a `relation`; a chain that breaks (a handler that resolves nothing; an execution owner that never performs the promised operation; a state the face has no branch for) is a `finding` with bin `product-defect`.
- **Enumeration, mandatory, breadth not depth:** every production entry point platform-wide with its exposure (active | conditional | internal | parked | historical): `web/src/desk/verbRegistry.ts`, `web/src/desk/applications.ts`, every library `Button` `onClick`/submit/change site, keyboard maps and the hotkey, `holdspeak/runtime/*` timers, WebSocket frame kinds, the MCP tool list (`holdspeak/mcp/`), the CLI (`holdspeak/main.py`), connector inputs, engine responses. One node per edge; links only where you traced them.
- **Claim reviews:** every Phase 1 capability whose `entry_points` or `surfaces` touch the deep-traced edges: verified | contradicted | unresolved | not_applicable, with the record id, the field, the revision and evidence.
- **Orphans:** derived from typed links and declared exposure (an internal capability needs no button; a parked surface is not an active edge; a local presentation action needs no table).
- **Doc drift:** a Phase 1 or canon sentence the trace contradicts → `finding` bin `doc-drift` (ledger only; correction is story 07).
- Source inspection, executed behaviour and owner observation stay distinct; never claim the second or third from the first.

## Sealing

Work in your own worktree (`../wt-philo-2-02` Muad'Dib, `../wt-philo-2-03` Astra), branch `audit/philo-2-0N-static-<brain>`. Commit only through the gate (`dw contract new --story PHILO-2-0N`), or hold for SHIP if you are a worker. **Do not read the other brain's `static-*.json`/`.md`, its branch, or its worktree until all four pass outputs are sealed.** Shared preparation (schema, atlas, rig) is not a finding.

## Laws

No hub, no product process, no e2e in a static pass. Unit fences in an isolated HOME only (`HOME=$(mktemp -d)`). Never the owner's data dir, keychain or microphone. Never a git verb that moves or cleans a tree; stage by explicit path. Report with the validator's output for your JSON and the §9 report; never inflate; "unverifiable statically" is a good answer.
