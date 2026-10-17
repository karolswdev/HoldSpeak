# Formal Astra postmerge review — #1243

VERDICT: RATIFY

FINDINGS:
1. Tenets 3, 5, 6 and 7: the merged Decision face puts writing first using existing paper/gadget components, with retained supporting drafts and reachable Done. Evidence: `web/src/desk/pullouts/DecisionPullout.tsx:163`; real creation/save shots at `.tmp/daily/decision-paper-1440/20261017T181918Z-case.daily.decision.save-astra-1440/` and `.tmp/daily/decision-paper-393/20261017T181943Z-case.daily.decision.save-astra-393/`.
2. Tenets 3 and 7: Ask preserves the canonical Note handoff, separates sent sources from the next question, and protects a newer handoff from an earlier successful reply. Keep uses the submitted snapshot. Evidence: `web/src/desk/components/AskPanel.tsx:176`, `:301`, `:341`; 95 scoped Ask/Note checks pass.
3. Tenets 3, 5 and 7: the previously broken loaded phone state now owns all nine pointer probe points for Back, Remove, Ask and Keep. Quote and Add notes are expanded; composer377px has no overflow and leaves reader214px. Evidence: `.tmp/daily/ask-scrollhint-393/20261017T184302Z-case.daily.ask.passage-astra-393/after.png` and `.tmp/tonight/ask-scrollhint-393.log`. Final same-build1440 also passes at `.tmp/daily/ask-scrollhint-1440/20261017T184456Z-case.daily.ask.passage-astra-1440/`.
4. Tenets 3 and 7: Thread resolves named sources, bounds expanded header scrolling and retains drafts/focus through Commands. Evidence: `web/src/desk/pullouts/ThreadPullout.tsx:96`, `web/src/desk/components/ThreadComposer.tsx:399`; `.tmp/daily/thread-final-sources-393/20261017T182939Z-case.daily.thread.sources-astra-393/after.png`. The stale Listen test now opens More and still proves speech and Stop; all11 file tests pass.
5. Merged product `018a1358f` is delivered from `wt-daily-experience-20261017`, PID14353, port8765. Source and served build both equal `e95ae448a3f033e6`; health, Desk, Conductor and Models return200. The actual Desk address printed by `holdspeak web` was opened. Final ordinary quick is GREEN after the one test-only correction; the broad run's4,188 other related tests,109 sweep cases and17 canon checks passed.

CONDITIONS: None for this merged change. Full-main verification runs separately after delivery under the current fast cycle; any finding is fixed forward.

MISSED: The first selected-passage presence predicate passed while the loaded phone layout hid Ask and overlapped quote controls. Actual expanded-state screenshots and pointer ownership exposed it. The canonical source handoff and bounded context fix are included in this merge. Independent integrated advisory review also found command focus and a late reply hiding a newer handoff; both are fixed.

TUESDAY: Yes: write a decision, ask about a saved passage and continue a readable thread with the main actions reachable.

UNKNOWN: Owner aesthetic acceptance, live model quality and physical microphone/browser speech output. Walk provider text was explicitly replayed; Thread content used the real import API. Test totals do not establish owner acceptance. The postmerge full-main result is pending.


## Full-run follow-up

The original review above preceded full-main completion. The run then found five failures: two product copy findings, two stale Thread-details navigation tests and one memory-index database lock. See RELEASE.md for exact identities, preserved evidence and fix-forward disposition. Owner aesthetic acceptance remains open.


## Formal follow-up review — #1244

VERDICT: RATIFY

FINDINGS:
1. Tenet4: Decision's supporting field now says Background consistently in editing, reading and copied text; stored `context_markdown` is unchanged. Evidence: `web/src/desk/pullouts/DecisionPullout.tsx:44`, `:172`, `:193`;46 focused Decision and21 product-copy/language checks pass.
2. Tenets3 and4: Thread's argument action names its consequence using the existing command label. Evidence: `web/src/desk/components/ThreadComposer.tsx:986`;93 composer checks pass. Root inspected actual Toggle guardrail shots at1440 and393 in `.tmp/daily-main/thread-argument-{1440,393}/`. Both own all nine real-pointer target points, retain the draft on Close and return focus to the writer. The phone target is44px tall; the full label fits.
3. Tenets3 and7: the receipt test now navigates the real Thread details fold before Rename, without dropping any refusal/receipt/pointer assertion. Evidence: `tests/e2e/test_desk_glass.py:656`; both focused widths and all12 affected browser checks pass. Ordinary quick is GREEN:304 related web,12 affected browser,109 sweep and17 canon checks.
4. Merged product `ac55cd318` is delivered from `wt-daily-delivery-20261017`, PID38565, port8765. Verified source and served build both equal `22aa76d6327046a1`; four HTTP checks return200. The actual root Desk address printed by `holdspeak web` was opened. Verification remains in a separate worktree.

CONDITIONS: None for these bounded copy/navigation corrections. The full-main run is in progress; any new finding is fixed forward.

MISSED: #1243's scoped checks missed two language-contract failures and two stale receipt-navigation cases. All four are corrected here. Its fifth full-run failure, a memory-index database lock, remains explicitly open in STATUS and the release record: one original parameter and52 scoped cases pass, but no cause was established. No speculative transaction patch or blanket retry was added.

TUESDAY: Yes: Decision names supporting background clearly, and Thread commands state what the press does without losing the draft or writer focus.

UNKNOWN: The original database-lock cause; owner aesthetic acceptance; live provider quality and physical native input/output. The full-main result is pending and cannot close the unknown lock cause merely by passing.


## Subsequent full result and source-anchor correction

Merged `ac55cd318`: `1 failed, 16697 passed, 26 skipped, 1 xfailed, 12 warnings in 674.18s (0:11:14)`; mandatory live bus `3 passed in 23.82s`. The sole stale atlas source anchor is now corrected, with all26 source-anchor checks passing. The original recall-lock case passed, but its earlier cause remains unknown and open. The [final merged verification record](https://github.com/karolswdev/HoldSpeak/pull/1244#issuecomment-6239495252) holds the exact final head and outcome; the earlier one-failure run is not relabelled green.
