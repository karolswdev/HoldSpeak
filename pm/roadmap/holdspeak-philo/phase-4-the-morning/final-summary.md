# Phase 4 — The Morning — final summary

**Closed:** 2026-09-24. Chartered 2026-09-23 from the Phase 3 closure on the owner's word ("yes close and open"); ratified by the owner on the story 01 canvas ("so... my walk says: yes!") and the story 04 canvas ("good to go, no sitting reqd..."). Four stories, four PRs, both brains on every one.

## What he can do now that he could not on 2026-09-23

- Press Generate on the Arrival while yesterday's brief still has untriaged rows. Before, the verb was absent until every row was acknowledged or deferred.
- See the new decision first. The BRIEF section leads with decisions, newest first by the decision record's own timestamp; the three-row cap stays. Before, decisions came last and the new one sat behind the fold.
- Generate the next brief after a failure in the lookback. Before, a failure selected into two briefs reused its id and the next brief answered 500.
- Tell that yesterday's brief is done. After every row is handled, one line reads `ALL n HANDLED` under the date; the stored headline and counts are kept as history.
- Read a failure in plain words: `BRIEF DID NOT GENERATE · HTTP n` with Generate as the recovery; `GENERATING…` while it runs; `No changes` for an empty brief.

## The morning, on the rig

One Generate on a populated, untriaged day-one brief, after the producer day advances, puts the new decision in row 1, readable and unobscured (nine of nine hit samples owned), at 1440 and 393, with and without a breakage item in the lookback; the old brief's rows and triage are unchanged; the real LAN engine summarised (`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`). Runs: `assets/story-02-shots/20260924T072614Z…1440`, `072514Z…393`, `072814Z…breakage-1440`, `072722Z…breakage-393`. Phase 3's exit 1 closed against these.

## Both brains, per story

| Story | Built by | Checked by | Verdicts | Merged |
|---|---|---|---|---|
| 01 Generate is always reachable | Muad'Dib (Opus 5.5) | Astra | canvas: BOUNCE, conditions, library BOUNCE, library RATIFY + conditions, paid (six rounds); built: BOUNCE (active atlas pinned retired strings), BOUNCE (stale generated refs), paid | `566495b0` #625 |
| 02 The decision in the visible rows | Astra (Luna) | Muad'Dib | RATIFY-WITH-CONDITIONS (schema snapshot; the authorization-order ruling; canvas item 7 corrected), paid | `280ee7ce` #626 |
| 03 Breakage ids never collide | Muad'Dib (Opus 5.5) | Astra | RATIFY-WITH-CONDITIONS (scope amendment; the original producer identified; collector order), paid | `6e9d6161` #624 |
| 04 The triaged headline | Astra (Luna) | Muad'Dib | canvas: RATIFY for presentation; built: RATIFY-WITH-CONDITIONS (the headline sentence ledgered as Tenet 4 debt), paid | `20ee2672` #627 |

## Fences that failed pre-fix (exit 3)

- 01: rendered 13 failed / 7 passed on `1c39294c` (the presence fence: `Unable to find … arrival-brief-generate`), pytest 2 failed / 17; atlas contracts fence 6 failed / 2 on the archived atlas (`docs/internal/philo/phase-4/generate/`).
- 02: producer 3 failed; rendered 2 failed; readable predicate 3 failed / 5 passed; covered-row transition 1 failed (`docs/internal/philo/phase-4/rows/`).
- 03: `IntegrityError: UNIQUE constraint failed: monday_brief_items.id`, 2 failed on `1c39294c` (`docs/internal/philo/phase-4/ids/red-pre-fix.txt`).
- 04: rendered 5 failed / 3 passed (`docs/internal/philo/phase-4/headline/`).

## The library, changed under the canon

The section head label and the egress chip were 10 px, under the 12 px floor; both are 12 px now, on every section head and chip on the desk. Head verbs no longer shrink; long dynamic headings wrap inside their head; the Jira and Confluence host chips truncate with an ellipsis (their rows show the full host); route disclosures keep their full text and carry their destination as the tooltip; 24 healed floor allowances removed from the floor guard. Ratified by Astra at the canvas' round four.

## The owner's sitting

Waived by the owner 2026-09-24 ("no sitting reqd..."): accepted, not observed. No walk is claimed. The retained rig evidence above is the phase's proof; usefulness of the summaries stays PARTIAL as measured in Phase 3.

## What he still cannot do (ledgered, not lost)

- A pending actuator authorization can sit behind `N more` when older decisions exist (the ratified newest-first order; Phase 4 decision log).
- On first paint at 393, row 3 sits under the capture bar until Generate (story 02 repaired the transition only).
- The breakage row's text is filtered off the Arrival (raw-id filter); the head and the receipt can disagree by the hidden rows — the Tenet 4 wording debt.
- The producer's headline is a sentence ("1 thing changed, …"); breakage titles carry service/method ids; 71 more under-12 px lines in the library (canvas README ledger); the pullout section label override at 10 px.
- Focus lands on `body` after Generate.
- The brief view's own Generate limitation (`BriefView.tsx`).
- Everything Phase 3 carried: the aftercare panel covering the fold at 393; ASR instability; exception-path queue wording; `1 WORDS`; the council's deferred list; the four Constitution amendments unruled.

## Laws learned

- The rig's contract book is a fence: an active atlas case that pins a retired string recurs the wording scar one layer up. Fence the atlas.
- Canvas fixtures come from the real producer (`_compose`), never hand-ordered rows; a canvas board that contradicts the producer is corrected on the record, not silently.
- A global library truncation hides disclosures; truncate only where the full value is visibly elsewhere.
- Never symlink `node_modules` into a worktree or an archive and then run `uv sync`: the build hook's `npm ci` follows the link (three incidents).
- Measure every visible text node, not only the species you changed.
- The heavy CI jobs run over an hour; merge on the other brain's lifted verdict, green scoped fences and the fast jobs, per the owner's ruling; keep the inherited-failure baseline on file.

Astra's build summary from the story 04 lane is retained at `assets/build-summary-astra.md`.
