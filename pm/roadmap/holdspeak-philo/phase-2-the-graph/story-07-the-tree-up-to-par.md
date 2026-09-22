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
- [ ] `tests/unit/doc_claims/registry.py` gains rows for the claims the council marked drift; false ones are corrected in the same commit or flipped to known_false with a story; the known-false ratchet moves only down.
- [ ] The phase walk scripts listed by the council are moved to `scripts/_parked/` with a one-line reason each (never deleted); `scripts/graph_walk.py` is the walk.
- [ ] `.claude/skills/graph-walk/SKILL.md` (and the AGENTS.md mirror) teaches a worker or Astra to mint a state, run the rig, read a consequence record, and restore only tracked (` M`) shots; `.claude/agents/opus-worker.md` and `scripts/astra` preambles carry the scars: fences naming old words, lying doubles, receipts under one branch, the restore loop.
- [ ] `docs/internal/philo/README.md`, the Philo project README and the HoldSpeak README index point at the graph.

## Test plan

- **Unit:** `test_phase200_doc_claims` green with the new rows; `philo_graph_reference.py --check` green; the skill validates like the Phase 1 skills.
- **Integration:** the Philo drift job in CI.
- **Manual / device:** none.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
