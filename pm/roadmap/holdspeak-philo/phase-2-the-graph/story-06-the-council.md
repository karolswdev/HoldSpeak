# PHILO-2-06 - The council

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** PHILO-2-02, 03, 04, 05
- **Unblocks:** see the phase status doc
- **Owner:** both brains; the owner rules dissents

## Problem

Four passes, two static and two live, on one brief. The council reconciles them into one graph and one ranked finding list, and answers the roots question: does the product, as wired today, let the owner spend ninety percent of his day on the desk with interfaces that guide him, in the manner of Workbench 2.0+ on steroids (Tenet 6)? Where the answer is no, the outcome is codified as Philo Phase 3, the engineering phase.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] `docs/internal/philo/graph/COUNCIL.md` opens with ONE DECISION PAGE in plain English (brief §9): which selected owner jobs work, fail or remain unverified; the recommended next useful result and the smallest Phase 3 scope that enables it, with effort and dependencies; each decision for the owner as exact question, recommendation, alternative, cost, decisive evidence and dissent; what is deferred and what he still cannot do. Then: agreements, single-brain findings with the other's reply (one round each), open dissents verbatim, the merged `docs/generated/graph.json`.
- [x] Findings in three bins, ranked by cost to the owner on a Tuesday; the owner-selected first-use cases ranked first; counts are diagnostics, never exits.
- [x] The roots verdict: one page, plain words, judging the OBSERVED faces against the Seven Tenets, UX-CANON and DESIGN_SYSTEM, naming where the desk stopped guiding and became plumbing; it does not infer ninety-percent daily usability from first-use coverage — that stays a design aim, reported against selected jobs and observed limits.
- [x] The Phase 3 charter draft (`pm/roadmap/holdspeak-philo/phase-3-*`): at most TEN stories (more requires the scope stop in this phase's risks), each naming the owner result, the edges and states it closes, and the outcome evidence that will close it; the owner ratifies the charter and rules the dissents.
- [x] Doc drift is ledgered here, corrected in story 07; product defects are ledgered here, built in Phase 3; nothing is fixed during the council.

## Test plan

- **Unit:** `docs/generated/graph.json` validates; every finding carries evidence.
- **Integration:** n/a.
- **Manual / device:** the owner reads COUNCIL.md and the Phase 3 charter and rules the dissents.

## Notes / open questions

**Sat 2026-09-23.** COUNCIL.md (decision page first; §§2–5; Astra's check + counter-draft; Muad'Dib's reply and rulings); council-resolutions.json (20 resolutions over all 47 sealed finding ids, final dispositions; one open dissent §4.3); Phase 3 The Meeting Loop drafted (4 stories, A4 pending D3). The merged `docs/generated/graph.json` is story 07's generator output, seeded by the resolutions file (the council's explicit resolutions are its input, per brief §8).

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
