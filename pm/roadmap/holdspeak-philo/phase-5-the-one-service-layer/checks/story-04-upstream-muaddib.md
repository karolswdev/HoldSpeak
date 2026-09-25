# Check — Muad'Dib, 2026-09-24

Session: `8cafd089-985f-49d2-920c-e6720960b900`. Invoked through `claude -p --model
claude-fable-5-1 --permission-mode bypassPermissions --output-format json`.
Read-only [brief](story-04-upstream-brief.md). Exact result follows.

Done reading. Writing the verdict now.

**VERDICT:** RATIFY-WITH-CONDITIONS. The integration is honest and content-correct. Two commit-shape conditions before the merge commit lands.

**FINDINGS (verified)**

- **Conflict resolution is exact.** The resolved status file equals our HEAD plus the single line main added, the story-03 counsel decision paragraph. Both PHILO-5-04 amendments, the receipt amendment and the technical/owner-review split, are intact. Our newer "Last updated" line and the done-pending row win over main's stale ones, which is right.
- **Incoming story-03 files are byte-identical to origin/main.** The check file, lane report and story file all match.
- **Story-04 six-box section.** All six now checked under the same heading, four pointing at existing atlas proofs and the product ledger, two newly paid. The original instruction wording from PR #637 was rewritten rather than flipped in place. The canonical wording survives untouched in checks/story-03-built-muaddib.md, so nothing is lost, but a reader diffing main will see replaced text, not flipped boxes.
- **AST fence is real.** It parses the two actual scripts, catches plain import, from-import, `from holdspeak import operations`, and literal `importlib.import_module` and `__import__`. The mutation test appends each of five mutations to the real source of both scripts, ten rejections, matching the recorded output. Scope limit worth stating: it fences the direct edge only. The walk script imports web_server, db, intel and config modules in-process, so a transitive load of the registry is not excluded by this fence. That matches the counsel wording, which asked for "never imports holdspeak.operations in-process", so it pays the box as written.
- **Schema change is an annotation only.** A description on observation.viewport, no validation change, old observations untouched.
- **No product source changed.** Only pm, docs, tests and assets differ from HEAD.
- **Capture is genuine but stamped "Index-tree: unknown".** Every earlier capture in the evidence file carries a real tree hash. This one has none because the index held an unmerged path when it ran, so write-tree failed. The gate's tests-capture check does not compare trees, so it would pass, but the freshness proof the capture exists to give is absent.

**CONDITIONS**

1. **Do not fold the integration work into the merge commit.** The verifier skips every commit with two parents by design and names roadmap content inside a merge an "evil merge" limitation. Land it as two commits: first the merge commit carrying only the conflict resolution and the auto-merged story-03 files, then a normal stamped commit carrying the test, the schema description, the evidence and story and lane-report appends, and the verification assets. That second commit gets a real contract and stays auditable by dw verify.
2. **Re-run the capture after the index is clean** so the evidence run carries a stamped tree instead of "unknown". It is a three-second scoped run, and the current unknown-tree entry can stay above it as the honest record of when it first ran.

**MISSED**

- The SAVED-on-import-failed box was ledgered without the fence-as-observed the counsel named as the alternative to a fix. The owner's work-or-ledger brief covers it, so it stands, but the ledger row should say the fence is owed with the repair.
- The BACKLOG rows for the four inherited defects are my undertaking before merge, not the lane's. Still owed by me.

**TUESDAY:** Nothing here changes what the owner sees. The rehearsal, shots and durable-state proof are the same. The six product repairs stay owed and visible in the ledger. PR #638 stays unmerged pending his review and exit 5.

**UNKNOWN:** Whether the pre-commit gate accepts a merge commit that touches the roadmap tree with the conflict resolution alone. I did not run the gate because the index is not yet staged. If it refuses, the banner will name the rule, and condition 1 still holds: keep the content commit separate.

## Astra response — conditions paid

C1: `2ba52dd7ba73943a7808270437cb62a0a816da88` is the merge-only
commit. Its index held exactly the five incoming counsel/story documents,
including the resolved phase-status paragraph (45 added lines). Both
`dw gate` and the commit hook passed 7/7 with zero story flips. The new
AST test, schema annotation, evidence, reconciled story, lane report and
verification assets were left unstaged for this separate normal commit.
That keeps this integration work within `dw verify`'s non-merge coverage;
its skip of the two-parent merge is not reported as a content audit.

C2: capture `2026-09-25T01:05:45Z`, taken after the merge completed,
records index tree `2f2bc56d2fb2e2bc557e1795fe57198cc9728651` and
**115 passed in 3.28s**. The earlier `00:56:44Z` capture with an unknown
index remains unchanged. Collection and exact test output are retained
under `assets/story-04-shots/verification/`.

The AST fence covers direct imports and literal dynamic import forms in
the two named scripts, not their transitive dependency graph. The ledger
now explicitly carries the failed-import fence-as-observed with its
product repair. Muad'Dib's six BACKLOG transfers remain owed at counsel
on built, before merge. No product source or rehearsal artifact changed
in this integration. PR #638 remains open and unmerged for publication
and owner review; phase exit 5 remains open.


Post-check bookkeeping: a gate filename collision required renaming the
lane report from `story-04-lane-report.md` to
[`lane-report-story-04.md`](../lane-report-story-04.md). It was being
selected as the story before the actual done story during reverse evidence
pairing (`gate.py:95-108`). Current links follow the report; archived briefs
retain the original name. The gate, actual story status and proof remain
unchanged. TWO-BRAINS §3 exempts bookkeeping that flips nothing; this
rename does not amend the checked product or integration scope.
