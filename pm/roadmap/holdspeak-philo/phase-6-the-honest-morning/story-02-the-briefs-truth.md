# PHILO-6-02 - The brief's truth (one time, honest counts, human words)

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** exit 3 (one time format, counts that agree with their labels, no raw ids)
- **Owner:** Muad'Dib (Opus 5.5); Astra checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", ledger rows 5 and 6; Astra's check of the drafts, finding 2 rows 2 and 4, MISSED 2
- **Canvas:** (a) and (c) none; (b) a SMALL CANVAS AMENDMENT only if a count label or a count meaning changes

## Problem

On every fresh Arrival read the brief tells two stories (the PHILO-5-04 receipt seam made it visible; `final/20260925T001407Z-his-words-real/shots/brief/1440.png`):

- **(a) Two time formats.** The head says `GENERATED SEP 25 18:19` (`holdspeak/web/routes/monday_brief.py:47-58`, a 24-hour label built on the server). The receipt says `6:19 PM` (`web/src/desk/chair/briefEgress.tsx:47-50`, `toLocaleTimeString`). One brief, two times.
- **(b) Two counts.** The head says `5 THINGS WAITING`; the receipt says `Brief ready · 6 items`. The receipt counts every row in every section (`briefEgress.tsx:43-46`). The Arrival counts decisions, changed, broke and waiting rows that are not on the shelf and are not raw ids (`web/src/desk/chair/ChairHome.tsx:875-886`); THIS WEEK is excluded. The two counts have DIFFERENT lawful meanings (Astra, finding 2): the generated snapshot vs what is unhandled now. They differ after Ack/Defer. The fix is not "one count".
- **(c) Raw words.** The producer stores a pipeline item with the text `MeetingIntelService.run_intelligence` (`holdspeak/services/monday_brief_service.py:500`). The receipt counts it; the Arrival filters it as a raw id (`ChairHome.tsx:886`). The same raw wording is in breakage titles, `{service}.{method} failed` (`monday_brief_service.py:597`). If only the item is fixed, a failure stays hidden (Astra, MISSED 2). Whether `2 more` renders the raw name is unwalked.

## Scope

- **In:** (a) one time format on the brief through an existing idiom (canvas-free); (b) both counts keep their meanings and the historical snapshot, and the labels say what each counts; (c) human producer wording for the pipeline item and the breakage titles, naming the recorded action accurately (a summary REQUEST is not a completion); the fences; the rig case at 1440 and 393.
- **Out:** a redesign of the BRIEF section; a new row kind; the headline sentence (`MondayBriefService._compose`, a Phase 4 ledgered debt); everything the phase status lists as out.

## Acceptance criteria

- [ ] (a) One time format for the brief's generated time across the head and the receipt, through an existing idiom (no new format invented). The stored `generated_at` is unchanged. Fence: the rendered head and receipt of one brief carry the same time string; red pre-fix (`18:19` vs `6:19 PM`).
- [ ] (b) The head count and the receipt count each keep their lawful meaning: the receipt counts the generated snapshot, the head counts the Arrival rows with an Ack/Defer (THIS WEEK excluded, the Phase 4 ask-2 ruling). The historical snapshot is not rewritten. Either the receipt counts what the Arrival shows, or the labels say what each counts. IF a label or a meaning changes: a SMALL CANVAS AMENDMENT (both widths, exact ASD-STE100 strings) is ratified by the owner BEFORE build; if nothing changes, the story records "no canvas needed" with the reason.
- [ ] (b) Consistent-count fence: one brief from the REAL producer (`_compose`) with a raw pipeline item, a THIS WEEK item and one shelved row; each rendered count equals what its label claims. Red pre-fix (5 vs 6 unexplained).
- [ ] (c) The pipeline brief item (`monday_brief_service.py:500`) and the breakage titles (`:597`) carry human wording that names the recorded action accurately; no `Service.method` text reaches a stored brief item. A summary request is worded as a request, not a completion.
- [ ] (c) Fence: an item minted through the real producer (the real `@observe_service` failure and the real intel run) has no raw `Service.method` text; red pre-fix. Words and the ACTIVE atlas fences change together.
- [ ] Walked: whether `2 more` (the fold) renders a raw name, before and after, at 1440 and 393.
- [ ] Rig: the Phase 5 rehearsal brief (`scripts/philo5_his_words.py`) at 1440 and 393; the shots show one time format and counts that agree with their labels.

## Effort (council-style estimate, not a promise)

1–1.5 days, plus the small canvas if (b) needs one

## Test plan

- **Unit:** pytest on the producer wording (real producer, `@observe_service`); vitest on the rendered head and receipt (time and counts), red pre-fix.
- **Integration:** the rehearsal brief and `case.closure.chain.s5_next_day_brief_has_it` at 1440 and 393 (exit 3), `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 rows 2 and 4: count meanings differ, a label or meaning change needs a small canvas; raw breakage wording at `:597` covered, MISSED 2).
