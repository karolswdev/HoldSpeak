# Final integration verification — 2026-09-05

Base: desktop merge `860ad7d2`. Commands run in an isolated worktree; Python proof drivers redirect home resolution to temporary data without changing HOME. The existing Playwright Node binary supplies Node because the system Homebrew Node cannot load its ICU dependency.

Complete `npm run check`, actual output excerpts:

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (709 source files; zero framework residue).
 Test Files  235 passed (235)
      Tests  2246 passed (2246)
✓ built in 4.27s
bundle gate passed (Desk JS 1263386 B; Desk CSS 298070 B; source maps 0)
```

The final Settings row change was then checked with the Settings/Interview/Thread suites (actual output):

```text
> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2 src/pages/cores/__tests__/settingsFaceRoster.test.tsx src/pages/cores/__tests__/SettingsCore.test.ts src/desk/__tests__/InterviewPanel.test.tsx src/desk/__tests__/ThreadToolRows.test.tsx


 RUN  v4.1.9 /Users/karol/dev/alt/HoldSpeak-integration/web


 Test Files  4 passed (4)
      Tests  64 passed (64)
   Start at  17:03:24
   Duration  1.87s (transform 750ms, setup 303ms, import 1.24s, tests 609ms, environment 1.04s)
```

Backend command: `python docs/internal/architect-assistant/proof/run_tests.py -q --tb=short tests/integration/test_interview_conversation.py tests/unit/test_interview_service.py tests/unit/test_interview_tool_execution.py tests/unit/test_project_mcp_driver.py tests/unit/test_project_mcp_palette.py tests/unit/test_thread_modes.py tests/unit/test_thread_tool_loop.py`. Actual terminal result:

```text
......................                                                   [100%]
238 passed in 75.90s (0:01:15)
```

A broader rerun after the web prerequisites found 251 passes and two new UI canon failures. The Interview controls now use the library Button/Select and shared nonzero-count formatting; the inherited Room receipt caption uses countLabel; the decorative favorite uses SVG. No scanner or ceiling was weakened. The final three canon suites (`test_ux_canon_ratchet.py`, `test_interior_canon_guard.py`, `test_native_surfaces_guard.py`) report:

```text
...............                                                          [100%]
15 passed in 0.78s
```

TypeScript, tokens, architecture guard and bundle gate were checked again on the final candidate; a fresh build preceded the browser walk. Actual `python docs/internal/architect-assistant/proof/browser_walk.py --desktops` result:

```json
{"result": "pass", "model": "scripted fixture; not live model quality", "desktops": "Night Train renders; change places and settle preserve Thread draft; preference and favorite survive reload", "viewports": [1440, 393], "model_passes": 4, "tool_activity": "collapsed before final answer; manual expansion preserved at completion", "revisit": "same thread, section and fact retained", "people": "handoff before composer input", "screenshots": ["tool-activity-before-answer.png", "tool-activity-after-answer.png", "interview-walk-1440.png", "interview-walk-393.png", "interview-walk-people-393.png"]}
```

Screenshots were inspected at both widths. Logs remain under the integration worktree’s ignored `.tmp/delivery-*`; refreshed assertions and screenshots are committed under `assets/`. The earlier failed browser fixture, draft-remount failure, and canon failures were corrected and rerun. Scripted-model success establishes mechanics; live-model recommendation quality and physical audio remain outside this verification. GitHub CI status is available on the delivery PRs and is not inferred from these local results.
