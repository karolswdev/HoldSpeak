# PHILO-4-01 - Generate is always reachable

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** done
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

- [x] Scope: the Arrival's BRIEF section ONLY (`ChairHome.tsx:1260,1283`). The brief view's own limitation (`BriefView.tsx:297`, Generate only when there is no brief) is retained and ledgered, not repaired here. — built in `web/src/desk/chair/ChairHome.tsx` only; `BriefView.tsx` changed only its empty label to `No changes` (ask 5), its Generate limitation untouched.
- [x] The Generate verb is the existing library Button, present on the BRIEF section whether or not day-one rows are untriaged; placed on the canvas at 1440 and 393 with its loading / failed-read / generating states (reachable never means concurrently enabled: disabled while a read or a generation is open) and RATIFIED by the owner before build. — `briefVerbs` (ChairHome.tsx, `<BriefEgress/>` + library `Button`, `disabled={generating || briefLoading}`) passed as `actions` in all five branches; ratified 2026-09-23; fence `generateAlwaysReachable.philo401.test.tsx` (every button in the section has `.btn`).
- [x] The egress badge, the period/generated date caption and the receipt survive the rendered transition unchanged (A3's caption law). — vitest "keeps the badge, the caption and the receipt through every transition" (success → open → failure).
- [x] Generating with untriaged rows keeps those rows' triage state on the old brief's durable shelf (nothing is silently acknowledged or deferred); read back after generation. — `tests/unit/test_philo_4_01_generate.py::test_next_day_generate_keeps_the_old_brief_triage` (real service, read back); vitest "never touches the old rows' triage" (no `/shelf` call); rig observations at both widths hold zero `/shelf` requests.
- [x] Fence: a rendered BRIEF section with one untriaged day-one row HAS the Generate Button (the fence asserts presence; today it is absent, and that absence is the recorded pre-fix red). — "draws Generate in the head while a day-one row is untriaged"; red on origin/main 1c39294c (`Unable to find an element by: [data-testid="arrival-brief-generate"]`, `docs/internal/philo/phase-4/generate/prefix-red-vitest.txt`).
- [x] Rig: closure chain step 5 as written reaches Generate without the acknowledgement detour, both widths. — runs `20260924T053019Z` (1440) and `20260924T053350Z` (393): one click on the head `Generate`, no Ack, POST 200, a new brief id with the decision in `sections.decisions`. The case predicate (the decision text inside the visible ledger) is FAIL at both widths: the decision is folded behind `1 more` (story 02).

## Effort (council-style estimate, not a promise)

1–2 days incl. the canvas (Astra's check: the right minimal action)

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-24 — Astra's check on built: BOUNCE — paid in round two (atlas contracts, graph, canvas status). `checks/story-01-built-astra.md`. The active atlas: `case.j10.arrival_generate_brief.generated_empty` and `case.j10.arrival_reload.reload_persisted` expect `No changes`; `case.j10.route_brief_generate.load_failure` performs an `http_fault` (POST /api/brief/generate → 500) and observes `BRIEF DID NOT GENERATE · HTTP 500` at `[data-testid=arrival-brief-generate-failed]`; the empty-brief claim names `No changes` (plus the producer source); the reload claim points at the quiet branch (ChairHome.tsx:1333). Fence `tests/unit/test_philo4_01_atlas_contracts.py`: 6 failed / 2 passed on the HEAD atlas, 8 passed after (`docs/internal/philo/phase-4/generate/round2-*`). `docs/generated/graph.json` regenerated; `--check` exits 0. The three cases pass on the rig at 1440 and 393.

- 2026-09-24 — BUILT (Muad'Dib lane, Opus 5.5 worker): the head verbs in every branch, `GENERATING…`, `BRIEF DID NOT GENERATE · <cause>` with no Retry, `No changes`. Superseded fences moved in the same commit: `briefReceiptRendered202.test.tsx:79` (`Generate again` → `Generate`), `briefLoadAndDate.philo303.test.tsx` (Generate absent while reading / after a failed read → present, disabled / enabled), `ChairHome.test.tsx` write recovery (the write-failure receipt and its Retry → the status line and Generate). Atlas `state.briefs.*` source lines re-pointed. Rig step 5: Generate reached at both widths; the face predicate fails on the fold (story 02).

- 2026-09-23 — RATIFIED by the owner on the round-six canvas ("so... my walk says: yes!"): all six asks. Build what was ratified: the boards in `assets/story-01-canvas/` are the spec; `No changes` (ask 5) is in this story's scope with its wording fences.

- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
- 2026-09-23 — canvas round two after Astra's bounce: `assets/story-01-canvas/` (README, 11 boards × 1440/393 in `shots/`, `morning-brief.html`); artifact https://claude.ai/artifact/LHjuHKL1pVZuh4aK5J9qRU. The 12 px floor paid in the library (section head label, chip). UNRATIFIED.
- 2026-09-23 — canvas round three after Astra's r2 RATIFY-WITH-CONDITIONS: board 7 split into 7a (empty brief, `No changes` proposed) and 7b (fully triaged); new boards 6b, 8a, 8b, 9 (16 boards × 1440/393); `0 items` ruled a counter of zero (the receipt already drops it); library containment for dynamic section-head labels and chips, proved by two Playwright probes (`shots/lib-directory-393.png`, `shots/lib-jira-chip-393.png`); 24 healed allowances removed from the HS-202-05 floor ledger. UNRATIFIED.
