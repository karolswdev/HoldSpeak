# PHILO-2-01 - The rulebook and the state atlas

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** see the phase status doc
- **Owner:** both brains (co-authored; the other checks)

## Problem

Three audits measured properties and callers; the owner's sitting found two dead basics in two clicks: an edge with no effect (a receipt's Open) and a state with no face (an empty brief). Nothing in the tree defines the chain a verb must close, or the states a face must render. Without one rulebook, two passes cannot be compared and a council cannot rule.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `docs/internal/philo/briefs/graph-audit-brief.md` is the ONE brief both brains run, verbatim (this story ratifies it; it is drafted at charter).
- [ ] The four definitions (edge, interface, connection, action) and the four questions are pinned with examples from the sitting.
- [ ] The zero-diff law is stated: a verb that leaves no visible consequence where the click left the user is a finding, by Article III; no allowlist.
- [ ] The state atlas names the states to mint, derived from the data model: every projection kind x attention_state; brief none/empty/full/shelved; meeting recorded/imported/no-summary/summary/failed; engine assignment none/missing-profile/ready; first-value no_speech/no_microphone/microphone_unavailable; the clock t0, +1 sweep, +1 day, +1 week boundary.
- [ ] The first-use twenty are listed: the edges the owner touches in a demo, in order (arrival, SETUP row, Choose an engine, Add an engine, Check, Use this for summaries, Record, Stop, Import, open meeting, Run summary, Desk memory, a receipt's Open, Generate brief, Generate again, Write a thought, Kept, restart, find the summary, voice typing).
- [ ] The graph file schema is fixed (`docs/generated/graph.json`: nodes typed edge|interface|connection|action|state, links with evidence path:line or a shot or a DB row, and per-link `consequence` from the live pass).
- [ ] Findings have three bins (product defect; doc drift; tooling debt) and one ranking: cost to the owner on a Tuesday.

## Test plan

- **Unit:** `tests/unit/test_philo_graph_brief.py` — the brief exists, names the twenty, the four definitions, the zero-diff law, the atlas states, and the schema; the schema validates an example graph.
- **Integration:** n/a.
- **Manual / device:** the owner reads the brief once and says whether the twenty are his twenty.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
