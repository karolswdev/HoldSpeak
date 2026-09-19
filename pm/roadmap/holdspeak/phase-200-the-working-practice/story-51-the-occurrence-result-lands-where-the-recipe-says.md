# HS-200-51: The occurrence's result lands in the Project as the record the recipe declares

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-50
- **Unblocks:** HS-200-53
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); C5's output column; AC P200-A18

## Problem

**A scheduled run's only place to put an answer is a text column on a
Workbench item.**

`workbench_items` ends a run by writing `result`, `result_egress_json` and
`result_artifact_id` (`holdspeak/db/schema.py:1732-1734`), and the run itself is
receipted in `workbench_runs` (`:1742`). That is the right shape for an
inference answer. It is the wrong shape for every output C5's table promises:

| Recipe | C5's declared output | Where it actually lives |
|---|---|---|
| Meeting preparation | "Kept brief with sources and open questions" | `project_briefs` (`holdspeak/db/schema.py:4378`), kept by `PreparationBriefService.keep` (`holdspeak/services/preparation_brief_service.py:1134`) |
| Decision and commitment review | "Current decisions, unresolved obligations, evidence gaps" | `decision_records` (`:1127`) and the follow-through records |
| Weekly Project update | "Editable update with claim support and coverage" | `project_updates` (`:4109`), drafted by `ProjectUpdateService.draft_update` (`holdspeak/services/project_update_service.py:1501`) |

So even after HS-200-50 dispatches to the right service, the occurrence has no
declared answer to the question *what did Monday morning leave on the owner's
desk?* A brief that is not kept is a draft the owner must find; a result string
on an item is not a brief at all. AC P200-A18 asks for exactly this: "Run one
actual scheduled brief. Its result, scheduler identity, route, and receipt
appear in the Project."

## Scope

Map a scheduled occurrence's outcome onto the owning service's own record, link
the record back to the occurrence, and make the Project show it with the
receipt that produced it.

Implementation seams: `holdspeak/services/workbench_runner.py` (the terminal
record of a domain occurrence); `holdspeak/services/recipe_catalog.py` (the
descriptor's declared output becomes the mapping, not a switch in the runner);
the three owning services' existing create/keep/draft entry points;
`holdspeak/db/schema.py` for the occurrence link, additive only.

Out: a new Project surface. The records above already have faces from
HS-200-11, 13 and the Phase 162 Update Factory, and the occurrence's result
must appear on those.

Out: auto-publishing anything. A scheduled weekly update produces an
**editable draft**; publication stays an owner act (C5, and the Constitution's
egress rules).

## Acceptance criteria

- [ ] Each of the three recipes' scheduled occurrences produces the record its
      descriptor declares, through that service's own entry point — not a
      second writer.
- [ ] The record carries a durable link to the occurrence, and the occurrence's
      receipt carries a link to the record; either can be reached from the
      other.
- [ ] The Project's existing surface shows the record with its scheduler
      identity, route and receipt — no new face, and no raw ids on screen.
- [ ] A scheduled weekly update lands as an editable draft; nothing is published
      without the owner's act.
- [ ] A partial or refused occurrence produces a record that says so in the
      shipped coverage vocabulary, and never an all-clear (C4; the
      HS-200-07 rule).
- [ ] Re-running the same due minute cannot produce a second record — the
      occurrence identity is the idempotency boundary, proven with two real
      ticks.
- [ ] An agent-persona Workbench's `result` behaviour is unchanged, fenced.
- [ ] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_recipe_outcome`. Drive a real occurrence through the
real `WorkbenchRunner` into the real owning service against a real temporary
database, then read the record back through the real Project read path — the
proof is the record the product's own reader returns, not a row the test wrote
and re-read (`reference_lying_test_doubles`). Never touch
`~/.local/share/holdspeak/holdspeak.db`.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidate (HS-200-46).** One sentence must stay true: a scheduled
occurrence's outcome is written by the owning service's own entry point, never
by the runner writing the domain table directly. A cheap AST predicate over
`holdspeak/services/workbench_runner.py` expresses it, in the shape HS-200-45's
composition fence already uses. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**Open, for the implementer to settle and record:** whether a scheduled
preparation brief is `kept` automatically or left as a draft the arrival
surfaces. HS-200-11 made keeping the owner's act for a manual brief; a Monday
brief nobody kept may be a Monday brief nobody sees. Argue it in the evidence
with the rejected option, the way HS-200-45 argued its fork.
