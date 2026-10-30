# Extended documentation accuracy audit

Owner request, 2026-10-29: make the extended documentation accurate. The preceding rewrite and README panel did not prove every instruction. Check actual current behavior, not only navigation or terminology.

Worktree: `/Users/karol/.codex/worktrees/readme-panel/HoldSpeak`. Branch: `docs/core-docs-accuracy`. Source base: `4dce2796d`. It has the same product implementation as `c161be0e8`; the intervening PRs changed documentation. The clean existing worktree was reused because its complete tree matched current main before branching. Never move or clean a working tree.

Tuesday question: can the architect follow a guide without searching for an absent control, relying on an unsupported promise, or confusing a stored plan with a completed action?

## Settled audit and correction method

Read each owned guide in full. Audit procedures, commands, UI labels, configuration defaults, scope/authority statements, persistence, availability, and claimed outcomes against active source and relevant tests. Follow the active import/registration path: a matching name in a parked component does not establish current UI availability. Distinguish callable API, registered tool, active UI, fixture-tested behavior, live observation, and incomplete feature. Correct unsupported claims rather than inventing product changes.

Do not polish or rewrite an accurate paragraph merely to show activity. Preserve useful anchors and valid technical detail. Use current product names (Mode is reusable instructions; Agent is a coding session) while preserving exact wire/config identifiers in code. Read `docs/internal/DOCS_STYLE.md`. Model key, permission, fallback and egress claims require their actual policy path. Public docs must state material limits where users need them.

For every document, file a JSON row: `path`, `disposition` (`corrected`, `source_checked_unchanged`, `generated_checked`, or `unverified`), `claims` (document line/claim, source path:line, result), `changes`, `unknowns`. Include concrete source anchors for all corrected claims and substantive source checks for unchanged guides. A guide-level source review does not certify every statement or a live deployment. Say what you could not establish. No unsupported whole-product accuracy verdict.

## Ownership and coordination

Exact paths are in `lanes.json`. Each worker owns only its lane's public Markdown plus `<lane>-audit.json` and `<lane>-report.md` in this folder. Root owns the remaining guides, README/CONTRIBUTING, generated files, integration, tests, review, status, staging, commits and PRs. Anchors can drift: re-read before editing; never alter sibling files. Report cross-lane findings to root with evidence.

Generated configuration/API/MCP regions are read-only for workers. Report source/generator inconsistencies; root regenerates as needed. Do not edit canon, historical plans or evidence to make a current claim true. Do not change product code, defaults, tests or packages. Do not delegate further.

## Verification and ship

Workers run only `python3 scripts/check_docs.py <owned paths>` and `git diff --check`. No pytest, vitest, browser suite, package install, live hub/Desk call, microphone, provider request, launch, send, device change or owner data access. This is an owner-started repository task, not a HoldSpeak-launched task: no launch credential is required. No staging or commits. Return exact changed paths, principal corrections and source anchors, navigation output, unknowns, then hold for SHIP.

Root checks the source claims that matter, chooses targeted tests with isolated HOME under `scripts/test_lock.py`, performs the required quick check, and uses synthetic fixture flows where available. No metal/full-suite run or private Desk state. Tests and source review have separate evidence labels. The user has authorized documentation corrections and continuing the PR workflow; no product behavior change is included.
