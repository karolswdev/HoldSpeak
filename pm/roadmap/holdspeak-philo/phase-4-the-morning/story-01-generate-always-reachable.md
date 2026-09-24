# PHILO-4-01 - Generate is always reachable

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** the morning in one move
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Closure finding:** Phase 3 final-summary "What he still cannot do" #1

## Problem

`BriefSection` (`web/src/desk/chair/ChairHome.tsx:1260`, `:1980`) offers Ack and Defer but no Generate while a day-one row is untriaged; `Generate again` appears only when nothing is untriaged (`:1283`); the brief view offers Generate only when there is no brief (`BriefView.tsx:297`). A3's next-day case passed only because its day-one brief was empty. The morning needs a detour.

## Scope

- **In:** the result below, its fence(s) red pre-fix, the rig case at 1440 and 393.
- **Out:** everything the phase status lists as out.

## Acceptance criteria

- [ ] Scope: the Arrival's BRIEF section ONLY (`ChairHome.tsx:1260,1283`). The brief view's own limitation (`BriefView.tsx:297`, Generate only when there is no brief) is retained and ledgered, not repaired here.
- [ ] The Generate verb is the existing library Button, present on the BRIEF section whether or not day-one rows are untriaged; placed on the canvas at 1440 and 393 with its loading / failed-read / generating states (reachable never means concurrently enabled: disabled while a read or a generation is open) and RATIFIED by the owner before build.
- [ ] The egress badge, the period/generated date caption and the receipt survive the rendered transition unchanged (A3's caption law).
- [ ] Generating with untriaged rows keeps those rows' triage state on the old brief's durable shelf (nothing is silently acknowledged or deferred); read back after generation.
- [ ] Fence: a rendered BRIEF section with one untriaged day-one row HAS the Generate Button (the fence asserts presence; today it is absent, and that absence is the recorded pre-fix red).
- [ ] Rig: closure chain step 5 as written reaches Generate without the acknowledgement detour, both widths.

## Effort (council-style estimate, not a promise)

1–2 days incl. the canvas (Astra's check: the right minimal action)

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
