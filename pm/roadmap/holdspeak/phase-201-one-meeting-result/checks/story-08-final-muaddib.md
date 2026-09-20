# HS-201-08 — Built result before final run

CLI confirms claude-fable-5-1, session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Peer clock estimates are not run timestamps.

Root: the full run later finished with six failures; this is a conditional check, not closure.

**Check — Muad'Dib (claude-fable-5-1), final counsel-on-built for HS-201-08, 2026-09-20.**

- **Artifact:** the staged index on `feat/hs-201-green` in `/Users/karol/dev/tools/wt-201-a` (58 paths, uncommitted).
- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id. Root says the CLI confirms it.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - the staged name list;
  - the index compared with T1 `249b8364…`;
  - the staged diff of `roadmaps.py`, the four generators, both metadata shards and the Philo README;
  - `tests/unit/test_roadmaps_api.py`, in full;
  - `holdspeak/web/routes/concierge.py:269-316`;
  - the summary-selection row in `docs/generated/api-reference.json`, plus a count of rows with empty handler evidence at HEAD and in the staged file;
  - `BACKLOG.md:1172`;
  - the tail of `.tmp/hs201-green/full-worksteal.log`.
- **Not re-read:** I read the source, guardrail, startup and restart work in my earlier built check. I did not read it again here, and T1 shows it has not moved since that check.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The index contains what root says it contains.
   - It holds 50 non-PNG paths plus exactly 8 PNGs, all under story-08-shots. That
     totals 58. No tracked rig artifacts from other phases are staged.
   - There are no unstaged non-PNG modifications.
   - `git diff --cached --name-only 249b8364…` returns ONE path:
     pm/roadmap/…/evidence-story-08.md. R2's invariant holds right now.
   - tests/unit/test_web_server_startup.py and tests/unit/test_roadmaps_api.py are both
     staged. That pays built-check C4.

2. The roadmaps repair is exactly the ratified expression and nothing more.
   - roadmaps.py:147 now reads `(next_data.get("next_story") or {}).get("story_id")`.
     It is a one-line diff.
   - The test file drives the REAL `_project`, and the real router through a
     TestClient, with `_run` replaced by the producer's exact bytes. The null case
     returns `{"next_story": null}` with exit 2, which matches what I saw
     `.githooks/dw next holdspeak-philo --json` print.
   - Five payload variants are pinned: top-level `story_id`, top-level `id`, nested
     `next_story.story_id`, absent `next_story`, and explicit null.
   - The list-route test asserts HTTP 200 with both projects present. The active
     project keeps its id and the completed one is null.
   - It uses `raise_server_exceptions=False`, so the pre-fix state fails honestly as a
     500 and the exception is not swallowed.
   - The double's `raise AssertionError(args)` on any unexpected dw call is good. The
     test cannot pass quietly through a call it did not model.
   - The roadmaps conditions C1 and C2 are paid. Root's capture shows 2 failed and
     4 passed before the fix and 6 green after, which is the expected pattern.

3. The generator edits are string-only, as required. This covers the four generators'
   limits/scope/note strings and the API_REFERENCE header line.
   - Boundary `scope` no longer says "unchanged". It now says "in the snapshot census
     baseline, read from the current working tree at generation".
   - In the OpenAPI generator both `info` keys are retained, so the test's two `.pop`
     calls still succeed (O2).
   - No other staged hunk touches those scripts.
   - The anchors are exactly the four ratified: runtime.json 1267→1049 (twice),
     1454→1236, and integrations.json 1850→1855. No other anchors changed.
   - The README "Maintenance baseline" note is accurate, and it names the isolated
     HOME requirement.
   - The three docs conditions are paid: doctor anchors C1, the string-only label
     edits C3, and review of the regenerated diff C4.

4. RULING on the summary-selection handler_evidence gap. Recording the gap satisfies
   my delta-check MISSED-3. No implementation change is required or wanted.
   - First reason: the gap is a pre-existing limit of the collector. It is not a
     property of this route.
     - At HEAD, 160 of 693 rows have empty `handler_evidence`. In the staged file,
       161 of 694 do.
     - ALL six concierge routes are empty, including five that predate Phase 201:
       apply, detect, download, probe and propose. The new row matches its siblings.
     - Fixing it would mean redesigning the extractor for nested router prefixes. That
       is outside a restoration story (tenet 1).
   - Second reason: the row does not overclaim. It carries source, consumers, four
     test candidates labelled as search leads, and the generic uncertified
     contract_review text.
   - Third reason: I read the handler myself (concierge.py:269-316) and it has the
     properties root reports.
     - `_owner(request)` runs first.
     - The body is refused unless its key set is exactly {commandId,
       expectedAssignmentRevision, profileId, profileRevision}.
     - `assign_summary` receives `request.state.principal`.
     - The handler makes no outbound call. Whether `assign_summary` does, I did not
       trace (see UNKNOWN).
   - My MISSED-3 asked for an "expected egress/authority row". That wording went beyond
     what this reference is built to say. The ledger entry at BACKLOG.md:1172 is the
     correct discharge, and I withdraw the stronger wording.

5. The not-proof labelling, the eleven named failures (ten roadmaps at class (b) and
   one OpenAPI at class (a)), and the single SIGINT with no orphan processes are as
   root reports. I did not re-read that evidence section. K1 and K2 are accepted as
   stated.

6. The final run is in progress.
   - full-worksteal.log is at about 14%, and a count of lines containing `F` returns
     ZERO so far.
   - The earlier diagnostic had shown four failures by 8% and about twelve by 13%. A
     clean first 14% is therefore consistent with the roadmaps/OpenAPI repairs having
     removed those two families.
   - This is an observation of a partial log. It proves nothing about the remaining
     86%, and nothing is green yet.

CONDITIONS (for closing, after the run ends):
F1. full-worksteal.log must reach 100% with zero failed and zero errors.
    - The exact command line goes in evidence: isolated HOME, the absolute
      PLAYWRIGHT_BROWSERS_PATH and npm_config_cache, `-n 4 --dist=worksteal
      --ignore=tests/e2e/test_metal.py`, and nothing else deselected.
    - The final counts line is recorded verbatim together with the capture's exit code.
    - Record the skip count beside the diagnostic's 101. If it rose, explain why.
    - Any red means fix and rerun, and the story stays in-progress. There is no
      partial closure and no "green except".
F2. After the run, restore the tracked rig PNG churn from `git show HEAD:path` and
    re-park untracked artifacts.
    - Root then re-views the eight story-08 shots. If the run rewrote them, restage
      them only after viewing.
    - Staging refreshed shots puts paths under assets/ into the diff from T1, which is
      lawful. However, NO generator, generated output, metadata shard, script, test or
      product path may appear in `git diff --cached --name-only 249b8364…`.
    - If one does, the docs capture is void and T1 must be retaken.
F3. Closure records are staged last.
    - Flip the AC boxes honestly. AC6 cites the worksteal run and the eleven docs
      commands.
    - Set the story header to done, update the status row and "Where we are", and
      update the README "Last updated" line.
    - The lane report says which brain owned the lane, which checked it, and that they
      agreed.
    - Then run `dw contract new --story HS-201-08`. Commit once through the gate, never
      with --no-verify.
    - Push, and open a PR titled exactly "HS-201-08 main is green". No merge.
F4. The PR body lists the repair families separately:
    - the six named reds plus notifications;
    - roadmaps;
    - the four docs generators plus OpenAPI.
    It also names what only CI can prove:
    - the three Ubuntu unit reds;
    - byte-equality of openapi.json and the three references under CI's Python 3.12;
    - the macOS E2E job under CI's non-xdist ordering.
    A red PR run reopens the story. It does not get explained away.
F5. If the final run passes, state what happened to the "twelve inherited failures"
    and the daily-loop pair that current-phase-status.md still ledgers. Either they
    healed or they were never in this command's selection.
    - Correct that ledger text in the same commit, so the status doc does not
      contradict a green run.
F6. Record this check at checks/story-08-final-muaddib.md. The earlier built-check's
    finding-3 correction stays visible (the Allow-primary / Deny-focus correction;
    root says paid).

MISSED (ranked by cost to the owner):
1. The title promises "main is green", and main's badge also depends on jobs this lane
   never ran locally: Linux Smoke, Critical Journeys, Web Quality and screenshots.
   - Those were green on 35478778899, but that run predates #587 and #589.
   - If any of them is red on the PR, the promise is broken even with pytest at 100%.
   - F4 covers reporting. The owner should hear "green on the PR run", never "green
     locally".
2. The observer-fallback writer is still open, as the backlog states.
   - Until it is fixed, any unisolated local run by the owner writes a HoldSpeak
     database into his real HOME.
   - This is the closest item in this ledger to his actual desk. It should be the first
     thing picked up after this PR.
3. 161 of 694 API rows have no handler evidence. That is 23% of the reference.
   - It is fine as a disclosed limit.
   - It is worth one sentence in the Philo follow-up, so nobody reads the reference as
     having been inspected.
4. Story 07, the sitting, is untouched and still the phase's real close. Nothing here
   should be read as first-use proof.

TUESDAY: Yes for what this story touches.
- The Roadmap list opens with both projects.
- A saved Ask reads SAVED HERE after a restart at both widths.
- The guardrail box holds Deny filled and focused through a reload.
- The ledgered caveat stands: after a reload the violation reason is not redrawn.

UNKNOWN:
- The outcome of the final run. It was at about 14% with no `F` when I read it. This
  verdict ratifies nothing beyond what F1 requires.
- Whether `assign_summary` performs any egress. I read the route and did not trace the
  service.
- Regenerated-output content beyond the summary-selection row and the empty-evidence
  counts. I did not re-derive:
  - OpenAPI 568→569;
  - doctor 41 keys;
  - boundary 898→898 with the 3/3 delta;
  - capability/component/trust IDs 77/19/17.
  They stand as root's verified claims.
- The ThreadPullout.test.tsx and transcriber test bodies. I have not read them in any
  round, and I accept the captured green.
- The PR's CI result on Ubuntu and macOS. It does not exist yet.
```
