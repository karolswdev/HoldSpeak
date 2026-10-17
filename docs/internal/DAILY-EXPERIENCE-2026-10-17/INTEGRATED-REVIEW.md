# Integrated advisory review — 2026-10-17

Independent Sol HIGH worker, read-only. Root inspected the cited screenshots and run tails separately. This is advisory review, not Muad'Dib's check or the formal postmerge Astra review.

VERDICT: RATIFY

FINDINGS:
1. **Closed — loaded Ask phone overlap (Tenets 3 and 7).** Expanded quote and Add notes keep Back, Remove, Ask and Keep reachable with distinct 44px targets. Composer: 377px without overflow; reader: 214px. Evidence: `.tmp/daily/ask-scrollhint-393/20261017T184302Z-case.daily.ask.passage-astra-393/after.png`, `.tmp/tonight/ask-scrollhint-393.log`.
2. **Closed — source custody and newer handoffs (Tenets 3 and 7).** Saved Note context survives floor selection pruning; answer sources and Keep retain the sent snapshot. A newer handoff opens the composer and survives an earlier successful reply. Evidence: `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:553`, `web/src/desk/components/AskPanel.tsx:183`, `web/src/desk/__tests__/askPanelRunsOn.test.tsx:448`.
3. **Closed — Thread source overflow and picker focus (Tenets 3, 5 and 7).** Twelve named sources remain inside bounded header scrolling; reader and composer stay visible. Commands receives focus and returns it to writing. Evidence: `.tmp/daily/thread-final-sources-393/20261017T182939Z-case.daily.thread.sources-astra-393/after.png`, `web/src/desk/components/ThreadComposer.tsx:398`.

CONDITIONS: None remaining within this advisory review.

MISSED: The initial Ask presence predicate passed while the textarea covered controls and Ask disappeared below the body. Expanded-state screenshots and pointer ownership exposed the failure; the final build resolves it.

TUESDAY: Yes. Decision puts writing first; Ask preserves source identity and reading; Thread keeps Send and Keep clear while retaining advanced actions.

UNKNOWN: Owner acceptance, live model quality and native voice behavior. Provider text in these walks was declared replay.
