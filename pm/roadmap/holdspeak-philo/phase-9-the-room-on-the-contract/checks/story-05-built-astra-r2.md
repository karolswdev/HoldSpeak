VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **One verification failure is still masked.** In `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/fences.sh:15`, `mrc=$?` captures `cut`’s status. I reproduced: primary suite succeeds, mutation runner exits 1, wrapper exits **0**. Substituting `mrc=${pipestatus[1]}` in memory correctly handles all four success/failure combinations. **Tenet 3; Article IX.**

2. **Retention is repaired; export provenance needs an annotation.** I verified **28/28 Phase 9**, **69/69 Phase 7+8**, and **194 observations per base comparison**, with matching case IDs, widths, atlas hashes and verdicts. The retained face images match the rig’s viewport and pixel scale. However, old-export observations identify revision `b2fd7e8b`, because Git discovers the enclosing worktree: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots/base-294632c0/case.j1.first_words_continue_later.idle--1440/20260928T192713Z-case.j1.first_words_continue_later.idle-muaddib-1440/observation.json:15`. I reconciled this independently: **1,554 product source files in each export match its claimed commit**, and both built-index hashes match their observations. The comparisons are supported; the revision field alone is misleading. **Tenet 3; Article IX.**

3. **Census and equivalence conditions are paid.** The `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/evidence-story-05.md:29` names the previously omitted backend/glass coverage; its 131 named test functions exist. Delivery’s retained observations at both widths contain the click’s 200 response, Priya delivery, matching operation/receipt and stored readback. I inspected both delivery shots and the grant/Connections shots. Both Connections predicates are now compared in `tests/unit/test_philo9_atlas.py:137`. Independently applying all ten mutations in memory produced **10 failures**, including the wrong-state mutation.

4. **s5’s classification is paid.** `pm/roadmap/holdspeak/BACKLOG.md:1369` separates the missing input precondition from the unexplained summary timeout and corrects the counts to **2/6 each**. The original exit-1 capture remains. Recomputing the retained comparison gives **zero pass→not-pass transitions**.

5. **Generated-artifact verification is paid.** I collected and ran the named suite: **435 passed**. All **13 documentation/OpenAPI command invocations** passed. The `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-proof/docs_nav.sh:8` correctly exits 1 after an injected failure. Finding 1 is the remaining wrapper gap.

CONDITIONS:

- Fix mutation-status propagation and retain the failing-before/passing-after wrapper proof.
- Record the export-provenance reconciliation without editing historical observations. Refresh PR #688’s stale counts and “timing flake” description.

These are narrow corrections; another atlas rerun is unnecessary.

MISSED: Ranked by owner cost: a mutation failure can still appear green; exported runs inherit misleading revision metadata; the PR description still presents round-one claims.

TUESDAY: The reviewed screens let the owner mark delivery, see Priya’s row, allow a project grant and read NEVER CHECKED at both widths.

UNKNOWN: Lost originals, omitted base screenshots and the historical summary timeout remain unverifiable. I did not rerun the full suite or live atlas walks. Reviewed `11a89a12..67ce9256` in a fresh worktree; no files changed.