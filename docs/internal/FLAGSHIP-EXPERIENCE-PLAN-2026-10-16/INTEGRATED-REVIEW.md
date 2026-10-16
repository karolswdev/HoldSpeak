# Integrated review — independent Sol counsel

2026-10-16. Independent finished-implementation review requested under
KICKOFF.md. This is Sol counsel, not the formal Muad'Dib/Astra postmerge check.
Completed focused counsel. All four product findings below are fixed and
rechecked. The remaining condition is the root's release quick check.
No product edits, staging, commits, builds or browser runs by this reviewer.
At root's explicit request, this reviewer repaired two stale external-link
expectations in `web/src/desk/components/__tests__/agentWordsFence.test.tsx`.
Both now assert the retained label, exact HTTP destination, `_blank`,
`noreferrer noopener` and inert HTML; compact assertions remain. The one-file,
machine-locked run with isolated HOME passed all 8 listed tests (1.33 s):
`.tmp/flagship/agent-words-fence-list.log` and
`.tmp/flagship/agent-words-fence-run.log`. This test-only integration work is
disclosed separately from the independent product-source review.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Fixed: Brief's resumed read replaced its retained reading body.**
   Tenet 3 (help and accelerate). `web/src/desk/pullouts/IntelligencePullout.tsx:91` uses Activity,
   which stops and restarts effects when a view hides and returns. Brief's
   mount effect (`pullouts/views/BriefView.tsx:216`) calls nonquiet `load()`;
   `BriefView.tsx:193` sets loading, and `BriefView.tsx:377` substitutes
   SurfaceState for the whole body. The Send fold's local open state
   (`BriefView.tsx:635`) is therefore discarded on return. The shortened
   loading body can also clamp the scrolling element after the shell restores
   its position (`IntelligencePullout.tsx:112`). The retained-view test uses
   a substitute BriefView (`IntelligencePullout.test.tsx:12`) and cannot prove
   this real body survives. Keep existing material mounted during a resumed
   read and verify an actual unfolded Send/scroll round trip.
   **Fixed in root's bounded integration pass:**
   `web/src/desk/pullouts/views/BriefView.tsx:177` retains the material-presence
   ref; its effect at line 219 uses a quiet resumed read. New real BriefView
   Activity tests exercise a deferred successful and failed resumed read while
   retaining the same Send node and selected subject. Phone tour
   `.tmp/flagship/after-393-complete/observation.json` records the Send fold
   and edited task draft retained, with a nonzero Brief position of 419→419.

2. **Fixed: a closed missing artifact kept unrelated refreshes in failure.**
   Tenet 3. Exact reads traverse the session's held refs (`web/src/desk/api.ts:938`),
   including refs whose windows closed; `store/compositorSlice.ts:337` removes
   only the pullout. A failed exact read calls the global failure path
   (`api.ts:963`), and `store/dataSlice.ts:263` creates a Desk READ receipt.
   Thus the local source error becomes a repeated global error after the
   user closes its window. **Fixed in root's bounded integration pass:**
   `web/src/desk/api.ts:961` retains source-local error metadata and no longer
   calls the global failure path. The usable public artifact bucket remains
   live. Focused recheck passed: `.tmp/flagship/composition-resume-run.log`
   reports 4 files, 46 tests passed, including the real Brief resume checks.

3. **Fixed: the missing-artifact face printed `not_found`.** Tenet 4 (simple product
   English), UX-CANON A.10 (plain reasons).
   `.tmp/flagship/graph-missing-393/20261016T182151Z-case.brief_reading.source.artifact_missing-astra-393/after.png`
   shows the raw code next to Source unavailable. The new exact route returns
   a service-error envelope; `web/src/desk/pullouts/ArtifactPullout.tsx:37`
   prints its transport-selected message. Prefer its plain detail or omit
   the redundant code while keeping the source state and read Retry.
   **Fixed in root's integration pass:** the unavailable face now withholds
   the duplicate machine token; failed-read detail uses product humanization
   (`web/src/desk/pullouts/ArtifactPullout.tsx:37`). Final build
   `c15a5e7c1ef79062` was observed in the official graph walk; its shot
   `.tmp/flagship/graph-missing-ship/20261016T183744Z-case.brief_reading.source.artifact_missing-astra-393/after.png`
   shows Source unavailable and Retry read, with no raw token. Its observation
   verdict is pass; this reviewer read both the shot and observation.

4. **Fixed: a delayed write replaced the currently inspected held task's board.**
   Tenet 3. `web/src/desk/pullouts/views/FollowThroughView.tsx:155` closes
   `reload` over the render's focus ID, and `FollowThroughView.tsx:245` calls
   that closure after awaiting the write. Assign held A; while its POST waits,
   open held B; let B's focused read finish; then resolve A's POST. A's
   continuation issues a newer read for A and replaces B's board. Because
   `boardFocusId` is A while the requested focus remains B, neither target
   expansion nor the missing-target notice repairs the mismatch. Reopening
   the same B request changes no prop and starts no new read. A later
   `desk_changed` read may heal it, but that depends on response/debounce
   timing and does not guard the stale writer continuation. The post-write
   refresh must use the current focus or avoid superseding a later source
   request. A deterministic delayed-write/focus-change test can prove it.
   **Fixed in root's integration pass:**
   `web/src/desk/pullouts/views/FollowThroughView.tsx:151` retains the current
   focus ID; the post-write refresh at line 249 passes that current ID.
   `web/src/desk/pullouts/views/FollowThroughView.test.tsx:466` covers delayed
   A write, B focus, then A completion: reads are A→B→B, only A is written,
   B stays expanded, and the success receipt still names A.
   `.tmp/flagship/sources-focus-list.log` lists the case; its focused run
   (`.tmp/flagship/sources-focus-run.log`) passed all 21 tests in 2.28 s.

CONDITIONS:

- Restore the required release quick check to green. The latest
  `.tmp/flagship/quick-ship.log` reports one failing Python case:
  `tests/unit/test_monday_brief_service.py::test_a_desk_upload_with_no_start_lands_in_a_fresh_brief`.
  Root is investigating it; this counsel does not attribute its cause.
  That run reports 4185 web tests, 1507 Python tests, 109 sweep tests and
  17 canon checks passed. An earlier full quick run passed all 1508 Python
  tests (`.tmp/flagship/quick-final.log`); it is not the final quick result.
  No product-source review condition remains.

MISSED:

- A stale writer continuation needs current source identity as well as
  ordered reads; a live bus refresh can mask the defect.
- The mocked retained-view test proves the shell mechanism, not Brief's
  interaction with its real loading path. This is the larger owner cost.
- Session-long source holds made the new global artifact failure receipt
  outlive its window.

TUESDAY: Yes within the declared fixture boundary: the exact held task opens,
its draft survives return, explicit Assign persists without removing the hold,
and pending output states its missing PR context before a readable document.

UNKNOWN:

- Final-build completed actual tours and representative paired shots were
  read from `.tmp/flagship/after-phone-ship/` and
  `.tmp/flagship/after-narrow-ship/` (10 states each), including Material,
  captured Codex AskWell, read failure/retry and Memory. The latter records
  Intelligence at an actual 600 px width. Both list no page errors and
  preserve source lifecycle. Phone proves nonzero return at 419→419;
  the desktop fixture fits without a nonzero Brief scroll. Earlier 1440
  evidence was read from `.tmp/flagship/after-1440-complete/` (10 states).
- The latest quick-check failure remains root's investigation, separate
  from this completed focused review. No final-quick-green claim is made.
- Reviewer executed only the 8-test external-link fence file above. Root's
  other test totals are judged from logs, not independently rerun.
- Real provider/agent completion and owner visual acceptance are outside
  the declared isolated fixture boundary.
- Captured Codex asks renders and exposes its Answer input; its isolated
  session has no attached terminal and correctly disables Answer. Delivery
  to a real agent was not verified. Historic flattened text was not repaired.

## Root release resolution — 2026-10-16

The sole remaining condition is closed. Root traced the intermittent failure
to two separate import commits, reviewed the minimal atomic-publication fix,
and read its deterministic failing-before/passing-after regression. The unchanged
Monday upload assertion and all147 scoped tests pass. The final ordinary quick
check is GREEN:4185 web,1599 affected Python,109 sweeps,17 canon checks
(`.tmp/flagship/quick-release.log`). This is root's release resolution of the
condition, not a rewritten Sol report or a claimed Muad'Dib check.
