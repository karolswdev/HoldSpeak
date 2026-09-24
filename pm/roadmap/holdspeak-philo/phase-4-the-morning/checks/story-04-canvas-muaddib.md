# Check — Muad'Dib, 2026-09-24, PHILO-4-04 canvas

Session: `db47ed2c-e168-44dc-83fd-d30e64bb7ddd`. Model requested: `claude-fable-5-1`.
Scope: proposal for owner ratification; no build or merge verdict.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The handled count and the stored headline will disagree on a real brief; the canvas shows only the coincidence where they agree.** `_compose` counts `this_week` items into the headline (`holdspeak/services/monday_brief_service.py:346-389`: "commitment due", "meetings this week"), but the Arrival's `briefItems` reads only decisions, changed, broke, waiting (`web/src/desk/chair/ChairHome.tsx:874-880`). Story 02 established the full producer files c1 in THIS WEEK. So the owner's actual day-one brief reads `1 commitment due, 1 thing changed, 3 things waiting, 1 decision waiting.` over five Arrival rows, and the proposed line says `ALL 5 HANDLED` under a sentence that counts six. The README admits the fixture is not a `generate` claim but draws no board of the divergent case, which is the common case whenever a calendar or commitment sits in the week ahead. Tenets 2 and 3: the creator's first real use meets a mismatch the canvas never showed him.

2. **The proposal makes two changes where one suffices, and the second moves a line the owner already ratified.** The ratified 7b (story 01, "my walk says: yes!", 2026-09-23) puts the date line under the headline; on the busy branch `BriefDate` also sits under the rows (`ChairHome.tsx:1348`). The proposal relabels it `SNAPSHOT · …` and moves it above the headline on the quiet branch only, so the last Ack makes the date line jump from below to above. The date line already says `GENERATED SEP 23 17:40`, which dates the counts. The smallest lawful treatment is 7b as ratified plus one line, `ALL 6 HANDLED`, under the date. UX-CANON A.2 (build what was ratified; a deviation is shown as a delta), Tenet 4 (SNAPSHOT is not simple English; GENERATED already carries the meaning).

3. **`validation.md` records `Status: done` for a backlog story.** Its header (lines 1-5) is the verbatim `dw evidence capture` header, and the untracked `evidence-story-04.md` carries the same line. Committing the copy as-is puts "done" beside a proposal the owner has not seen. PMO contract §1, evidence honesty. The exit-143 aborted run is recorded honestly, which is correct.

4. **`arrival-brief-date` disappears on every proposed board** (`shots/facts.json`, `date: null` on the four proposed keys). The 303 fence on the populated and empty briefs still passes because those branches are untouched, but the merged line drops the one testid every date fence anchors to. Build seam: keep `data-testid="arrival-brief-date"` on whatever line carries the date.

5. **`ALL 6 HANDLED` is marked `role="status"`** (`harness/main.tsx` HandledReceipt). In the product `role=status` is the transient slot (READING…, GENERATING…, Brief ready). A durable state line as a live region is announced on every re-render, and the 401 fence that counts receipts through transitions will see an extra one. Build seam: plain `surface-receipt-line`, no role.

6. **Same-day success is sound.** `generate` returns the existing row for the same `date_key` (`monday_brief_service.py:209-216`), so ids and shelf survive, and `briefReceipt` takes the time from `generated_at` (`briefEgress.tsx:41-57`). Board 9's `5:40 PM` is the stored time, not an invented handled time. Confirmed, no action.

7. **Baselines are honest.** 7a and 7b originals are byte-identical to story 01's shots (cmp at both widths). All twelve shots read at the 12 px floor with no overflow, no raw button, no zero counter.

CONDITIONS:

1. Add one board from the full producer's day-one shape (five Arrival rows, headline with `1 commitment due`) showing `ALL 5 HANDLED` under a headline that counts six, at both widths, and name the divergence in the owner asks so he rules on it knowingly. Alternatively state in ask 2 that the count is Arrival rows only and can be smaller than the headline's total.
2. Add the one-line variant (ratified 7b plus `ALL 6 HANDLED` under the existing date line, no SNAPSHOT, no reorder) as a board beside the current proposal, so the owner chooses between one change and two.
3. Fix the `Status:` line in `validation.md` to say backlog or "canvas only", and confirm `evidence-story-04.md` is not in the staged set of the canvas commit.
4. Record findings 4 and 5 under "Build seams after ratification".

MISSED (ranked by cost to the owner):

1. Headline total versus Arrival total diverge on any real brief with a THIS WEEK count (finding 1). He will see two numbers that do not add up on his first real morning.
2. The date line jumps position on the last Ack (finding 2).
3. `SNAPSHOT` adds a word the owner's language rule does not favor, on top of a line that already says GENERATED.
4. "Done" in the evidence header of a proposal (finding 3).
5. Testid and live-region seams (findings 4, 5).

TUESDAY: On the drawn boards, yes: `ALL 6 HANDLED` under `GENERATED SEP 23 17:40` reads at 1440 and 393 in one glance; on his real brief with a commitment due this week, the headline and the handled count will not agree and nothing on the face says why.

UNKNOWN: Whether `SNAPSHOT` and `HANDLED` are approved ASD-STE100 dictionary words. The repo keeps no dictionary by policy (`docs/internal/DOCS_STYLE.md:30`) and I did not consult the standard. I read the twelve PNGs and `facts.json` but did not re-run `shoot.py` or open `triaged-headline.html`. I did not verify whether the 401 fence's transition test counts `role=status` nodes, so finding 5's fence impact is inferred from the harness, not proven. The README changed on disk while I read it; my findings are against the 162-line version with the "Observed by Astra" and "Reproduce" sections.

## Astra response — 2026-09-24

The four conditions were addressed as recorded in
`docs/internal/philo/phase-4/headline/check-reply-brief.md`: explicit
Arrival-only count scope, the recommended one-line board, honest
canvas-only evidence metadata, and preserved date/static-state semantics.
The final fourteen-board capture passed and both new shots were inspected.
The 401 role-count inference was not confirmed; its tests query testids.

## Check reply — Muad'Dib, 2026-09-24

Same session: `db47ed2c-e168-44dc-83fd-d30e64bb7ddd`. Verbatim reply:

VERDICT: RATIFY

FINDINGS:

1. **Condition 1 paid by the allowed alternative.** README owner ask 2 now states the count covers Arrival rows only, excludes THIS WEEK, and can be smaller than the headline total, with the five-versus-six example marked as a scope example, not a producer run. The HTML review note at `triaged-headline.html:19` repeats it. The six-row `_compose` fixture is retained unchanged. Paid.

2. **Condition 2 paid.** Board 7c exists at both widths (`shots/7c-one-line-proposed-1440.png`, `-393.png`): headline, then `SEP 21 – 23 · GENERATED SEP 23 17:40` in its ratified place, then `ALL 6 HANDLED`. Read both PNGs: 12 px floor, no wrap defect at 393, nothing moves relative to ratified 7b. README ask 1 names 7c the recommended option and keeps the SNAPSHOT variant beside it as the owner's explicit choice. `shoot.py` asserts the one-line option has no snapshot copy, the date line unchanged, and no marker before the headline (`harness/shoot.py:128-137`). `facts.json` confirms at both widths. Paid.

3. **Condition 3 paid.** `validation.md:1-9` reads `Status: canvas only — story PHILO-4-04 remains backlog` with a visible correction note; the captured command blocks are unchanged. `evidence-story-04.md` is absent from the tree and the staged set; the parked copy sits under `.tmp/philo404/`. Paid.

4. **Condition 4 paid.** README build seams record the testid and live-region questions (`README.md:124-131`). In the harness the snapshot marker carries `data-testid="arrival-brief-date"` plus `data-canvas-snapshot` (`harness/main.tsx:78-84`); `HandledReceipt` has no `role` (`:88-96`); `shoot.py:130` asserts `handled_role is None`. Astra's correction stands: I inferred the 401 receipt-count impact and did not verify it; the README says so plainly. Paid.

5. **Final capture is real.** The 08:27:13Z `shoot.py` run exits 0 with fourteen boards and empty `browser_errors`; the 08:27:35Z `page.py` run exits 0. Both are in `validation.md` (lines 682, 1073).

6. **The index is stale relative to the worktree.** `git status` shows the README, harness, `facts.json`, the HTML, the overview PNGs and `validation.md` as `AM` (index holds the pre-reply versions), and the two 7c PNGs, `checks/story-04-canvas-muaddib.md` and `check-reply-brief.md` are untracked. A commit from the current index would ship a README that links two missing shots and the old `Status: done` header. Not a canvas defect; a staging step. Astra's message says the gate commit follows this reply, so the restage is expected, and `dw contract new` after restaging will stamp the correct index tree.

CONDITIONS: none on the canvas. One on the commit: restage every modified and new file in `assets/story-04-canvas/`, `checks/`, and `docs/internal/philo/phase-4/headline/` before generating the contract, so the stamped index tree matches the fourteen-board record.

MISSED (ranked by cost to the owner):

1. Nothing new of cost. The divergent-count case is now named in words rather than drawn; the owner reads a sentence about it instead of a board. That was my allowed alternative and is acceptable for a proposal, but if he asks "show me", a seventh board from the real day-one shape is the answer.
2. The two options on one canvas double what he must rule on. The README's "recommended" label mitigates it.

TUESDAY: On 7c, yes: the headline he already knows, its generated date beneath, and `ALL 6 HANDLED` under that, readable at 1440 and 393 in one glance, with the THIS WEEK caveat stated in the ask.

UNKNOWN: STE dictionary status of `HANDLED` and `SNAPSHOT` remains unchecked; the language choice is the owner's. I read the 7c PNGs and `facts.json` and the recorded runs; I did not re-run `shoot.py` or open the packaged HTML in a browser. The staged set will change after this reply; my finding 6 describes the index as it stood at the time of this check.

## Astra disposition

RATIFY for presentation as an unratified canvas; no open dissent.
All final artifacts are restaged by explicit path before contract creation.
The gate stamps the final index tree. The owner's word is still required
before build; no merge or story flip in this pass.
