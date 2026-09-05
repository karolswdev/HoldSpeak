# Interview and desktop integration

Verified 2026-09-05. Delivery uses isolated worktrees so the original Interview preview, its database, the existing desktop checkout, and the independently active development checkout stay available.

## Delivery sequence

1. [PR #560](https://github.com/karolswdev/HoldSpeak/pull/560), merged at `855b34cb`, repaired main’s existing web quality failures. Actual evidence: [web prerequisites](../web-integration-checks.md).
2. [PR #528](https://github.com/karolswdev/HoldSpeak/pull/528), merged at `860ad7d2`, delivers eight environments, Places/favorites, and Settle. Its history is retained through a merge from current main. Settings keeps the newer Concierge behavior and now exposes Wallpaper in its current hub. The production browser fixtures were refreshed and both Settings and Settle walks pass. See [environment evidence](../../ENVIRONMENTS.md).
3. The accompanying Interview PR, on `feat/repeatable-interview-delivery`, carries the initial manual Interview, prompt/reply visibility, collapsed tool activity, and Thread draft persistence across Chair/Floor remounts. Its base is `860ad7d2`; newer Heartbeat, suggested-source, and Confluence MCP registrations remain present. The combined Project palette has 57 tools.

Every local delivery commit uses the generated, checked repository contract and normal hooks. No force push or hook bypass was used. The desktop branch advances from its original head. Main’s API reported no branch protection or rulesets; ordinary PR merges require no admin override. GitHub’s broader Python/macOS jobs are separate from the local checks and must not be represented as passed while still pending.

## Final behavior and proof

The full web contract passes: 2,246 tests, TypeScript, token generation/validation, architecture guard, production build, and bundle gate. The final Settings/Interview/Thread focused check passes 64 tests; the final UI canon checks pass 15 tests without increasing ceilings. Interview/Project/Thread backend regression passes 238 tests. See [actual outputs](VALIDATION.md).

The final browser walk uses the production build with a real isolated hub and a scripted model. At 1440 and 393 it verifies Night Train, Places, Settle, draft retention, actual MCP writes, folded tool calls before the answer, manual Try draft → Keep, section revisit/reload, saved preferences/favorites, and People handoff. No page errors were observed. See [screenshot](assets/integration-desktop-interview.png) and [assertions](assets/integration-combined-browser.json). The separate Settings browser walk verifies Wallpaper reachability and live scene changes.

A real LAN model previously completed the manual path, with documented quality gaps. This delivery is the repeatable manual Interview increment; it does not claim autonomous orchestration, physical microphone verification, or reliable recommendations across real organizational work.

## Runtime continuity

The original preview server was not restarted, and its checkout was not switched. A consistent, integrity-checked SQLite backup of its active conversation is retained privately under the original checkout’s ignored `.tmp/recovery/`, identified by `.tmp/interview-preview-backup.json`. User conversation data is not published in this PR.

Git integration does not activate a new backend. The combined production build is prepared in the isolated integration checkout. The existing preview remains on its original running backend until a separate activation; there is no claim of a seamless backend handover. To activate in a later runtime session, retain the prior build, back up the actual runtime data, let recording and active turns finish, then start the prepared release and verify existing Threads, Interview, Places, and recording readiness. Preserve writes made after any backup when considering rollback.
