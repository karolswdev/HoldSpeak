# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — CHECK on built, PR #669 @ 26c2d4bc

Subject: PHILO-8-04 (a), the empty decision headings. Worktree `/Users/karol/dev/tools/wt-philo-8-04`, read-only; `git status --short` = 0 lines before and after, HEAD 26c2d4bc.
Method: two `git archive` copies (origin/main 267f692a with the new glass copied in; the branch 26c2d4bc), real `npm ci --ignore-scripts && npm run build` in each (both exit 0), isolated HOME, PLAYWRIGHT_BROWSERS_PATH set, scoped runs only.

## VERDICT: RATIFY-WITH-CONDITIONS (one small test condition; merge after it, or merge now and pay it as the first line of 8-03)

Tenets: pass. Library `SurfaceSection` composed (Tenet 5); an empty label removed (UX-CANON "no empty labels"); nothing added for safety (Tenet 1); no new words.

## VERIFY, point by point

1. **Red on main, green on branch — REPRODUCED.** Main copy: `2 failed` — "title-only at 1440: headings ['Decision context', 'Decision', 'Consequences'], want []" and the same at 393 (first main attempt: 1440 timed out on `.chair` during a cold boot, an infra wait, re-run clean red). Branch copy: `2 passed in 26.35s`. Vitest: the 3 new cases on main = `2 failed | 5 passed (7)` (title-only and only-with-text red; all-three green as expected); branch = `3 passed (3) / 15 passed (15)`.
2. **Scoped CSS touches nothing else — CONFIRMED.** Static: `.desk-decision-card > .surface-section > .surface-section-head` (`web/src/desk/surface/surface.css:62`); `desk-decision-card` is used only at `web/src/desk/pullouts/DecisionPullout.tsx:84` (ThreadPullout.tsx:416 names it in a comment only). Live: Intelligence Follow-through with 3 seeded action items, both builds, 393 and 1440: computed styles per lane (Now/Waiting/Unassigned/Overdue) identical, and the screenshots are byte-identical (`cmp` equal at both widths).
3. **Atlas anchors — CORRECT.** Branch `DecisionPullout.tsx:70` = `const cycleDecisionStatus` (range 70-79 ends at the `};`), `:138` = `Supersedes {`, block 136-140. Live on the branch copy, `graph_walk.py run --viewport 393 --engine none`: `case.p7.decision_status.review_list` VERDICT pass terminal=settled; `case.p7.decision_supersede.successor_visible` VERDICT pass ("'Supersedes Atlas old decision' is readable"). `test_philo_graph_atlas.py` green in the scoped run.
4. **philo605 negative control — WEAKENED (finding F1).**
5. **Empty = blank after trim — CONFIRMED.** Code `DecisionPullout.tsx:121` `String(text || "").trim()`. Live on the branch: a decision with context "   \n\t ", decision "\n\n", consequences " " shows no heading (main shows all three). The vitest case covers `consequencesMarkdown: "  "`.
6. **Edit offers all three — CONFIRMED.** The editor `DecisionPullout.tsx:94-111` has no diff; live title-only Edit: Context 1, Decision 1, Consequences 1 at 393 and 1440; vitest asserts the three textboxes.
7. **Evidence honesty — ACCEPTABLE, gap closed here.** The recorded red stops at title-only. My probe ran all five cases on main: context-only (3 heads, want 1), context+decision (3 heads, want 2), whitespace (3, want 0) are all red on main; all-three is green on main, as it must be. So every non-trivial glass case is red on main. The branch shows exactly the wanted heads in all five. Note: the vitest and web-baseline captures (index tree 7855181) come before the CSS narrowing (e09599c6); only the glass and CSS guards were re-run after. A CSS-only change does not move jsdom results; acceptable.

## FINDINGS

- **F1 (minor, test) — the held-prop negative control can now pass without the read view.** `web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx:238-245`: the old `expect(decisionSection?.textContent).toBe("Decision")` proved the read view drew the OLD record (a Decision section with no new text). The new `expect(held).toBeUndefined()` also passes when the read view never renders. Proof by mutation: removing `setEditingDecision(false)` (`DecisionPullout.tsx:68`, Done never leaves the editor) → branch control `1 passed`; the same mutant against main's control (`:67`) → `1 failed`. The production-host test on the branch still kills that mutant (it expects "Keep the local ledger"), so suite coverage holds; only the control's own proof lost its read-mode anchor.
- **F2 (report, not the tree) — "heads now 12 px (were 10 px)" is false.** Computed `font-size` of the three headings is `10px` on BOTH builds at 393 and 1440. `.desk-next .desk-pullout-body h3` (`window-chrome.css:207-210`, specificity 0,2,1) beats `.surface-section-head h3` (`surface.css:79-84`, 0,1,1). There is no size change; the tree never claims 12 px (grep of story/evidence/status: none). Correct the lane's report only.
- **F3 (nit) — `const sections = [undefined, decisionSection()]`** repeated at `philo605…:238, 259, 280, 288, 319, 363` keeps `sections[1]` alive through a placeholder. Readable enough; cleaning is optional.
- **F4 (nit) — the comment at `surface.css:59-61`** cites `.desk-pullout-body section:not(:first-child)`; the real selector is `.desk-next .desk-pullout-body section:not(:first-child)` (`window-chrome.css:202`).
- Pixel parity: the branch all-three card at 393 matches main's within about 1 px of vertical offset (single hairline, same spacing).

## CONDITIONS

- **C1** — give the negative control a read-mode anchor, for example after Done: `expect(document.querySelector(".desk-decision-editor")).toBeNull();` plus `expect(document.querySelector(".desk-decision-card")?.textContent).not.toContain("Keep the local ledger");`. Proof = the setEditingDecision mutant turns it red.

## MISSED

- The Follow-through lanes compute a doubled hairline on main and the branch alike (section `border-top: 1px solid` + head `border-top: 1px solid`, e.g. Waiting/Unassigned/Overdue), the same pattern this story removed from the decision window. Out of scope; a backlog line for the Floor lane if the owner sees it.
- `tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence` fails on main AND the branch on `tests/unit/test_philo7_file_and_find.py:26` — the evidence's "known, not mine" is true (reproduced on both copies). Main is red on that guard; someone owes a fix.

## UNKNOWN

- Whether the follow-through doubled hairline is visible to the eye (the head's colour `var(--wash-1)` may be near-transparent); computed styles only.
- The branch at other widths than 393/1440: not run.
