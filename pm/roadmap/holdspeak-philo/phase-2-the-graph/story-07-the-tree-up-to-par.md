# PHILO-2-07 - The tree up to par

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-06
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

The sweep informs us or it was theatre. The Philo inventories gain the two missing layers as generated files; every load-bearing sentence about an edge or an action becomes a doc-claims row with a predicate over the graph; the forty walk scripts are parked behind the one rig; a walk skill and refreshed briefs carry this week's scars.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `scripts/philo_graph_reference.py` (+ `--check`) regenerates `docs/generated/graph.json` edges and consequences from the rig outputs; CI drift-checks it like the other Philo inventories.
- [ ] `tests/unit/doc_claims/registry.py` gains `holds` rows for the claims the council marked drift AFTER the prose is corrected to the current truth in the same commit; missing product behaviour stays in the findings and its Phase 3 story, never in the prose; the known-false ceiling is ZERO and this story does not raise it.
- [ ] A phase walk script is moved to `scripts/_parked/` (never deleted) ONLY after its callers and assertions are mapped to verified replacements in `scripts/graph_walk.py` or to an explicit council disposition, recorded per script; the rest stay.
- [ ] The portable Phase 1 skills and maintenance index (`agent/skills/`, `docs/internal/philo/data/README.md`) are EXTENDED with the walk procedure (mint a case, run the rig, read an observation, run-specific output directories, never a blanket restore loop); `.claude/skills/graph-walk/SKILL.md` and the AGENTS.md mirror LINK to that shared procedure; `.claude/agents/opus-worker.md` and `scripts/astra` preambles carry the scars: fences naming old words, lying doubles, receipts under one branch, the restore loop.
- [ ] `docs/internal/philo/README.md`, the Philo project README and the HoldSpeak README index point at the graph.

## Test plan

- **Unit:** `test_phase200_doc_claims` green with the new rows; `philo_graph_reference.py --check` green; the skill validates like the Phase 1 skills.
- **Integration:** the Philo drift job in CI.
- **Manual / device:** none.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
