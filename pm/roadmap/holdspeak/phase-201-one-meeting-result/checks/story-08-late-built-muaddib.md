# HS-201-08 — Final counsel on the late repairs

CLI confirms claude-fable-5-1, session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. The peer checked the staged code read-only. Its unconfirmed environment variable does not replace the CLI session record. Run times below are the DW capture times, not peer clock estimates.

Astra closure: the final full capture at 2026-09-20T07:18:40Z completed with 11,264 passed, 116 skipped, four existing strict xfails and zero failures/errors. All eleven docs commands passed at 07:17:48Z against T1 6c8c47bdfeeae64d3246cd592aa309a3a0e9f645. Final shots were viewed and rig churn was restored/parked. Evidence carries the artifact-envelope limit. The closure check records the final index invariant and delivery conditions.

Wording correction: the peer's final Tuesday sentence below overstates the creation gap. The narrowed, checked D5 wording in story-08-d5-wording-muaddib.md remains authoritative: **No current owner creation path is proven by this rig.** Hashless legacy paths remain unaudited; no universal absence claim is made. The peer text is retained verbatim.

**Check — Muad'Dib (claude-fable-5-1), final counsel-on-built on the four late families for HS-201-08, 2026-09-20.**

- **Artifact:** the staged index on `feat/hs-201-green` in `/Users/karol/dev/tools/wt-201-a` (82 paths, uncommitted).
- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.

What I read:
- the staged name counts and the list of unstaged paths
- the index delta from T1 `6c8c47bd…`
- the staged diff of `tests/integration/test_process_input_real_hub.py`, in full
- the staged diff of `tests/e2e/test_hs174_remote_settings_glass.py`, in full
- about the first 150 lines of the staged `tests/e2e/test_hs175_rhythm_brief_glass.py` diff
- every changed line of `tests/e2e/test_phase200_daily_loop.py`, plus `:1016-1030` in place
- the added fixture block of `BriefView.test.tsx`
  - I read the fixture only, not the assertions below it.
- the real artifact recorder at `holdspeak/meeting_plugins.py:318-340`
- the bridge's artifact selection at `holdspeak/services/proposal_bridge_service.py:258-285`

What I did not read:
- any evidence capture, canary, log or shot from this round
- `.tmp/hs201-green/full-verified.log`, the final full-suite run log (started 07:18Z)

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The index is as stated.
   - 82 paths are staged and 18 of them are PNGs. All 18 sit under
     phase-201/assets/story-08-shots.
   - No other phase's assets are staged. Nothing is unstaged.
   - `git diff --cached --name-only 6c8c47bd…` returns ONE path, evidence-story-08.md.
     R2's invariant holds against the fresh T1.
   - Root's account of the first T1 is the correct handling. The api-reference
     generator picked up the new test path as a candidate in five settings routes.
     Root regenerated that one output and retook T1.
     - I did not read that +5-line diff.

2. Interrupted send: the edit is exactly the ratified one.
   - `import select` became `import selectors`.
   - The wait is now a 3-line `with DefaultSelector()` block.
   - The assertion `readable and os.read(ready_read, 16) == b"typed"` is untouched.
     An empty selector result therefore still fails the test.
   - The `with` closes the selector before the kill and reconcile steps.
   - S1 is met.

3. Remote settings: built as ratified, and the targeted-credential witness is stronger
   than I asked for.
   - The fresh AgentCredentialStore is patched onto `holdspeak.principals` BEFORE
     `_boot`. The fixture then does `try / yield / finally: server.stop()`. This meets
     R2 and closes the leaked hub.
   - Revoke is scoped to the `.surface-ledger-row` that contains the
     `test-glass-runner` primary, and the wait is for THAT row to detach.
     - "test-glass-runner" is not a substring of "other-glass-runner", so the two rows
       cannot be confused.
   - The second credential is issued through the real
     `/api/settings/remote/credentials`.
   - After the revoke, its row must still be attached.
   - Its token must also complete a real MCP `initialize` on `/api/mcp` as an agent
     principal. That checks that the token is still usable, which is more than checking
     the row text. R3 is met.
   - The producer file is untouched and no conftest change was made (R1).

4. Weekly brief: built as ratified.
   - The `if pullout_visible:` escape is gone.
   - `.intelligence-brief` must become visible within 3 s or the test fails.
   - The `\b00\b` check on the whole face is replaced. For each of the three
     `brief-tw-*` rows that is present, the test requires exactly one primary whose
     text matches `^[1-9]\d* `.
     - A zero-count row is lawful only when it is absent, which is the A.8 law.
   - Checks (1), (3), (4), (5) and (6) are retained as they were. They are de-indented
     and otherwise unchanged. I did not read (7) or the shot code, so they stand as
     root's claim.
   - The unit fixture drives the real BriefView with `this_week` items that include
     "0 armed". It uses BOTH trip cases, 00:33 and 08:00, as timezone-less local ISO,
     which is the correct way to avoid a UTC-offset dependency. B2 is met for the
     fixture. I did not read the assertions that follow it.

5. Daily loop: D2's producer truth is met for the field that matters. One precise
   limit needs recording.
   - Real parts:
     - `DecisionCapturePlugin` and `ActionOwnerEnforcerPlugin` run on the imported
       meeting's actual segments through `admitted_dispatch`.
     - Their outputs are asserted non-empty and passed unmodified as `structured_json`.
     - The real `ProposalBridgeService.bridge_meeting_artifacts` produces the two
       proposals.
     - The bridge selects artifacts by `plugin_id` (proposal_bridge_service.py:269,276)
       and then parses the structured output.
     - So everything the bridge reads comes from the real producers. There is no
       hand-typed shape and no raw INSERT.
   - Limit:
     - In production the artifact ENVELOPE comes from `synthesize_meeting_artifacts`
       over the plugin-run rows (meeting_plugins.py:322-339). That envelope is
       artifact_type, title, status, confidence and sources.
     - The fixture calls `record_artifact` directly. It uses hand-chosen values
       `artifact_type="decisions"` / `"action_items"` and `status="draft"`. It sets
       no `sources`.
     - No plugin-run row is written.
     - The bridge does not select on those fields, so the proof holds.
     - Any day-2 face that reads an artifact's type, status or sources is seeing
       fixture values, not synthesized ones.
     - Evidence should say this in one sentence.
   - Ordering is correct.
     - `plugin_calls == []` and `proposals == []` are asserted on the real route BEFORE
       the fixture runs.
     - The wait-for-succeeded is followed by `review = _review()` at :1026, before its
       first use.
   - The D5 wording appears verbatim in the narrowed form in three places: the module
     docstring, the helper docstring and a `walk.fact`. The "NORMAL CONTROLS" carve-out
     is named. D4 and D5 are met.
   - The Review face is asserted to read exactly "PROPOSALS · NOT RUN", with no
     EXTRACTED and no "Nothing to review". That is an honest face fence.

6. Negative canaries: root reports three.
   - Weekly: the actual test loop is AST-extracted. "0 MEETINGS" and "00 ARMED" fail.
     Both clock strings pass.
   - Daily: the two empty-state asserts are AST-extracted. They pass on the current
     state and reject a forced call or a forced proposal.
   - Interrupted send: the high-fd probe went red and then green.
   - Extracting the ACTUAL assertion AST is the right method. Re-typing the rule would
     prove nothing about the real test.
   - I did not read any of these captures. They stand as root's claims.

CONDITIONS (closing; F1-F6 and X1-X2 stand, restated where they are now specific):
Z1. `.tmp/hs201-green/full-verified.log` must reach 100% with ZERO failed and ZERO
    errors.
    - The command is as stated. It uses an isolated HOME, absolute browser and npm
      caches, `-n 4 --dist=worksteal --ignore=tests/e2e/test_metal.py`, and nothing
      else is deselected.
    - Record the final counts line verbatim.
    - Expected shape: the 4 existing strict xfails remain. The skip count is compared
      with 116, and any change is explained.
    - Any F or E means the story stays in-progress. Fix, take a new T1, run docs,
      run the full suite again. No partial closure.
Z2. After the run, restore tracked rig churn from HEAD and park untracked files.
    - Then prove `git diff --cached --name-only 6c8c47bd…` lists ONLY paths under
      pm/roadmap/.
    - If any test, script, metadata, generated or product path appears, T1 and the
      eleven docs commands are void. Retake them.
Z3. Add to evidence the one-sentence envelope limit from finding 5.
    - This is an evidence-only change and does not disturb T1.
Z4. Flip the AC boxes honestly. AC6 cites THIS run and the 07:17:48Z docs capture.
    - Update the story header, the status row, "Where we are", the README "Last
      updated" line, and the phase ledger. The ledger must lead with the D5 gap.
    - Then run `dw contract new --story HS-201-08`. Make one gated commit, never with
      --no-verify.
    - Push, and open a PR titled exactly "HS-201-08 main is green". No merge.
Z5. The PR body lists the SEVEN repair families.
    - It states that the first complete worksteal run was RED with 6 failed.
    - It carries the D5 sentences.
    - It names what only CI proves:
      - the three Ubuntu unit reds
      - byte-equality of the regenerated references and openapi.json under CI's
        Python 3.12
      - the non-xdist macOS E2E ordering
    - It states that the high-fd repair cannot be confirmed by CI at all.
    - A red PR run reopens the story.
Z6. Record this check beside the story. The original D5 sentence stays visible with its
    correction.

MISSED (ranked by cost to the owner):
1. The remote-settings test now writes a NEW file,
   `build-remote-revoked-{width}.png`, into the phase-174 assets
   (test_hs174_remote_settings_glass.py:34, the SHOTS constant).
   - Every future full run will leave two untracked PNGs in a closed phase's folder.
   - The guardrail test avoided this by pointing at SHOTS_08.
   - This is NOT blocking, and I do not ask for a change now. A change would restart
     T1 and the full run for a cosmetic gain.
   - Ledger it under the evidence-churn scar, with the one-line fix.
2. The fixture bypasses plugin-run rows and artifact synthesis, as finding 5 notes.
   - Nothing in the suite now exercises `synthesize_meeting_artifacts` →
     `record_artifact` → bridge as one chain for a meeting.
   - The exception is the 4 strict xfails.
   - Add this to the ledger item for the parked pipeline. It is a second thing to
     re-prove when that entry returns.
3. `tests/e2e` now imports `tests.unit.plugin_dispatch_rig`.
   - The file already imported from tests.unit, so this is no new kind of coupling.
   - A move of that rig would break an e2e walk. No action.
4. Story 07, the sitting, remains the phase's real close. Nothing in these four
   families is first-use proof.

TUESDAY:
- Yes for what he touches:
  - Roadmaps opens.
  - A saved Ask reads SAVED HERE.
  - Deny holds through a reload.
  - Revoking one remote credential leaves the others working.
- He still cannot create the carried decision himself. The record now says so plainly.

UNKNOWN:
- The outcome of the final run. I read none of it, and this verdict ratifies no green.
- The evidence captures, canary outputs and all 18 shots from this round.
  - I read none of the new 10. Root reports viewing them.
  - One detail stands as root's statement: the 393 prepare shot shows only the top of
    the preparation, and the carried rows are asserted in the DOM.
- The tail of the weekly glass diff, which is check (7) and the shot code. Also the
  BriefView unit assertions below the fixture.
- The +5-line api-reference.json regeneration and the 11-node late collect.
- Whether the fresh-store fixture or the stopped hubs change fd pressure or the
  behaviour of any other test in the run now in progress.
- The PR's CI result.
```
