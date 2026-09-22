# PHILO-2-04 - The live pass, Muad'Dib

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

A graph read from the tree cannot see an Open that answers with nothing. The live pass drives every applicable case (an edge in a reachable state) through its real production entry point and judges it by the outcome law (brief §3): the expected result is recorded before the trigger; an enabled action that promises a change and produces neither it nor an intelligible refusal is a finding; an unexplained zero diff is unresolved, never pass.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `scripts/graph_walk.py` (the one versioned rig, shared by both brains; interface-specific trigger adapters permitted; walk parking is story 07's business under its replacement criteria) runs against a real hub in a fresh isolated HOME and browser profile, states minted through their real production entry points and transitions, with explicitly labelled boundary substitutions where the brief permits them (recorded engine replies at the provider boundary; the fixture WAV at the input boundary), at 1440 and 393 for face cases, with every clock source named and its mechanism verified or the case recorded as unexercised (brief §7).
- [ ] The owner-selected first-use cases (story 01) are walked first with the real LAN engine, its identity and result recorded, technical completion and owner usefulness reported separately; every other applicable case with a labelled recorded engine reply.
- [ ] Per applicable case: preconditions, expected result, initial feedback and terminal outcome observed separately, before/after evidence and a shot; the rig is calibrated first against a dead action, a request with no promised result, a wrong-target result, a valid focus/geometry change, an unchanged-result contract and an operation that never completes (brief §7); a timer, tool or CLI edge is driven through its real entry point, never a substitute click; unexercised cases are recorded with the missing mechanism.
- [ ] The pass never touches the owner's desk (`~/.local/share/holdspeak`), never the microphone (fixture WAV), never his keychain.
- [ ] Output: `docs/internal/philo/graph/live-muaddib.json` + `live-muaddib.md` + shots; Astra's check recorded beside it.

## Test plan

- **Unit:** the rig's six calibration cases (brief §7) each read the verdict the contract names; none is classified by the presence of a diff alone.
- **Integration:** the rig itself, one state, both widths, in CI.
- **Manual / device:** none; the owner's own sitting is HS-202-06.

## Notes / open questions

Sealing law (brief §§6–7, 9): this pass's report is sealed (committed on its own branch) before its author reads any other pass; shared schema, fixture recipes and rig calibration are preparation, not shared findings. Every run records source revision and dirty-tree status, contract versions, runtime provenance and unexercised cases with reasons.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
