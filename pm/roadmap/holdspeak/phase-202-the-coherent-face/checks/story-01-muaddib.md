# HS-202-01 — Muad'Dib counsel on built

Date: 2026-09-20 (America/Denver). Claude session: `3a12b6ea-c573-49ab-8a48-a24cc6e3ace4`.
Read-only counsel; no product or test run by the checker.

## First check — verbatim

VERDICT: RATIFY-WITH-CONDITIONS

The fence is honest on the main points. Gestures are real clicks and keys. The strict mode compares the exact failure set, and every setup, HTTP, persistence or route assertion aborts the run outright. `record-refresh` is a real defect: `record-refresh-1440.png` shows the MEETING READY toast on screen while the open record still reads SUMMARY OFF, Run summary and QUEUED. The conditions below are harness-only. I ran nothing. I read source, evidence, six shots, the CI workflow and the two rig helpers.

FINDINGS:

1. **The composite `dock` predicate masks Speak and Meetings at 393 (Tenets 2, 3).** `test_hs202_first_use_smoke.py:266-268` folds the three doors into one `all()` under one name.
   - `dock-393.png` shows Speak and Meetings fitting; only Desk memory is off-screen.
   - The 393 log carries no "RECOVERY: open Meetings" line, so `meetings_ok` was true.
   - `dock` is expected at 393 (`:41`), so a later loss of Speak or Meetings at 393 yields the identical failure set and a GREEN verification.
   - `meetings_ok` (`:269`) is never a named check. An unreachable Meetings door takes the staged-surface recovery (`:80-84`) and records nothing new.
   - Desk memory is in the narrow check, as you asked, but it is the only door actually failing and the name does not say so.

2. **The pass branches accept an unloaded surface (Tenets 2, 3; story AC3 "must load their own content markers").**
   - `notes-query` (`:403-411`): when `note_match` is true the check passes on highlight identity plus shelf detach. No notes content marker is required. The `"Notes" in selected_text` clause also lets any program with "Notes" in its name pass.
   - `thought-door` (`:290-292`): a pass is `count() > 0` on `.cm-content`, with no `_loaded` call.
   - `thought-door` also accepts `.thought-workspace`, which is the window the owner bounced on 2026-09-20 ("completely unusable"). Story 02 says "opens a note".
   - Today both checks are RED, so nothing is masked now. They define the green that lane B repairs toward, and that green would certify a loading shell.

3. **The shots in the tree come from mixed runs and are rewritten on every run.** `SHOTS` (`:37`) points into the tracked assets directory in both modes.
   - Git status shows `AM` on every PNG, so the staged bytes differ from the worktree bytes.
   - The clocks on glass disagree within one width set: `dock-393` reads 06:38, `meeting-after-restart-393` 06:39, `planned-host-393` 06:41, and the 1440 shots 06:40.
   - The RED capture is pinned to index-tree `dbb87607`; the PNGs I read are not that run's.
   - The full suite under `-n auto` will rewrite them again. This is the known tracked-evidence-PNG scar, now with 26 more files.

4. **Planned-route provenance is not tied to the Job 5 gesture.** `host = planned["legs"][0]["host"]` (`:350`) is compared only with the chip label and the receipt.
   - It is never compared with `stub.server_address`. The chip shows a bare `127.0.0.1` (`planned-host-393.png`), so the port is invisible on glass.
   - Only speech is assigned by the fixture (`:179`), so the summary route very likely does come from the UI gesture. That is inferred, not asserted.
   - Plan, admitted hash and receipt are otherwise well chained (`:371`, `:378-379`).
   - The receipt's "actual host" is derived from the route under `FakeIntel`. No connection reaches the stub during the run. That limit is honest but should be stated.

5. **Two rig facts are undisclosed (Tenet 3).**
   - The hub's own drainer is OFF in this rig. The evidence log says "drainer is OFF: this process does not own the database" twice per test, from `intel_queue_conductor.py:129-133`. `_boot` never claims the owner lock, and the test drains by hand at `:372`.
   - The glass shows that rig state: `record-refresh-1440.png` reads "NOT DRAINING" on the row. The production callback is real and the toast proves the broadcast arrived. The fence cannot see whether Run summary ever drains on his desk, and the appendix (`05-first-use-fence.md`) says neither of these.
   - The "restart" is a second `MeetingWebServer` in the same Python process. `reset_database()` runs (`glass_infra.py:217`) and the tab gets a fresh context, so reads are file-backed and a new singleton serves the hub. Module state survives, so it is an honest restart for a rig but not a process restart. The appendix at `:16` should say "in-process".

6. **`record-refresh` is one predicate over summary text and the attempts host (`:380-386`).**
   - A no-reload screen with the right summary and the wrong host is counted as the expected failure.
   - The file header says route truth "always fails normally". That holds only after the recovery reopen (`:392-393`). This is low cost, because the repair turns green only when both are right.

7. **Several `_loaded` markers are container shells.** `arrival-display`, `.meetings-head-verbs` and `.meetings-detail-head` pass on any non-ellipsis text, and the blocklist is four literals (`:51`).
   - The job-critical markers are specific: the dictated sentence, the note body, the summary text and the option ids.
   - I judge this adequate. The docstring's "never a window shell" overstates it.
   - `_hit(door, fit=False)` for Search (`:115`) tolerates a clipped door at 393 and gives no reason.

8. **The MeetingPullout distinction is honest.** The print at `:436` and appendix `:19` claim the summary on glass and the receipt through the API, never a receipt badge on the pullout.
   - The activedescendant assertion before Enter (`:134`, `:430`) is strict.
   - The refind is two real moves only if typing is excluded, and it works only with the full exact title.

9. **CI will collect the fence and fail.** `test.yml:274` runs `tests/e2e/ -m "e2e and not metal"` with no `HS202` variable.
   - The PR's E2E job will be red, and main will be red once it merges. That matches the owner's order for the local default.
   - It also puts two failures into every other lane's full-suite run and the merge-on-conclusion rule. Story, status and evidence name no ruling on this.

CONDITIONS:

1. **Dock.** Split `dock` into per-door checks (`dock-Speak`, `dock-Meetings`, `dock-Desk memory`). `KNOWN[393]` then carries only the door or doors that fail today. If Meetings stays a soft check, make it a named check.
2. **Pass branches.** Require a `_loaded` notes content marker on the `notes-query` match branch and drop the loose `"Notes" in text` clause. Use `_loaded` on the `thought-door` pass branch. With lane B, either drop `.thought-workspace` or record why it counts as "a note".
3. **Shots.**
   - Write them to `tmp_path` unless an explicit variable asks for the tree.
   - Stage one set from one named run and state that run in the evidence.
   - Restore the tree after the full suite.
4. **Provenance.** Assert that the planned host equals the stub's host and port.
5. **Disclosure.** In the appendix and evidence, state:
   - the drainer is OFF in the rig and the test drains by hand;
   - "NOT DRAINING" on the shots is rig state;
   - the restart is in-process;
   - the actual host is route-derived under a fake engine.
6. **CI.** Record how `test.yml:274` treats the fence, in the PR body and under Active risks. My recommendation: the job sets `HS202_EXPECTED_FAILURES=1` and the default run stays RED locally.
7. **Pending, as you stated.** The GREEN capture is appended; the unchanged ratchet is captured; the full isolated suite is read; the gate passes; this check is recorded under `phase-202-the-coherent-face/checks/`.

MISSED (ranked by cost to the owner):

1. **Whether Run summary drains on his own desk is outside this fence.** The 2026-09-13 audit found that nothing drains the queue. A green fence says nothing about it. The sitting must carry it.
2. **Desk memory content has no red fence.** Story 02's job 4 says "Desk memory shows the desk's memory", but the Desk memory door is only hit-tested and never opened. Story 02's exit wants "each item with a fence red first".
3. **Refind passes only on the exact full title.** A tired owner types "architecture" or "Notes". The fence names the generic defect but does not test partial recall.
4. **The MEETING READY toast covers the capture bar and the window footer** in `record-refresh-1440.png`. This is a finding for lane B under the no-overlap rule.
5. **After restart the host is not on glass within two moves.** That is not claimed, but the owner cannot re-read the route truth without going deeper.

TUESDAY: No — the owner cannot do the jobs today. At 393 he loses the Desk memory door and three of the four menus; at both widths Write a thought opens Speak, Save confirms nothing and the record never refreshes. The fence detects that and repairs none of it.

UNKNOWN:

- I did not run the GREEN run, the ratchet or the full suite (I was read-only). They are pending and not proved.
- I viewed 6 of the 26 shots. The three `menu-*-393` shots are probably the same frame.
- I could not check whether the 2.5-second `observe` bound can race a product poll, so expected-mode flake is untested.
- I did not inspect `_chip_label`, the `FakeIntel` result shape or `_StubHandler`.
- The owner's voice, microphone permission and the tokenless URL are correctly outside this fence.

## Astra response

1. Dock checks are now independent: `dock-speak`, `dock-meetings`, and `dock-memory`. Only `dock-memory` is expected at 393. A new loss of either working door fails strict verification.
2. The thought pass requires a visible, editable note-specific CodeMirror field: either the primitive note editor ID or the Phase 201-12 ThoughtDocumentPane labelled Note body. That pane is the clean note proved by HS-201-12; it is not the whole old Thought window. Empty initial note content is valid, so its live contenteditable field is the loaded marker. Generic Notes accepts only a note identity or the exact Notes/Desk memory label, and requires the selected note body or saved note in that named destination after Enter.
3. Shots now default to tmp_path. Only `HS202_EXPORT_SHOTS=1` exports to the tree. Final exported GREEN will supply one complete set; full-suite runs cannot overwrite it. Earlier captures are retained as iteration history, not the final shot provenance.
4. The planned host must equal 127.0.0.1. The define-endpoint POST must carry the exact stub URL including port, and the planned profile ID/revision must equal that response. The route contract stores host without port, so comparing its host string with host:port would be false. The profile binding proves the UI gesture selected that endpoint.
5. Appendix now discloses manual queue drain, NOT DRAINING rig state, in-process restart, and route-derived FakeIntel receipt hosts. Real localhost HTTP is used for engine Check only.
6. Kept CI unchanged. The user explicitly orders a normal RED fence and an open, unmerged PR before repair. Active risks and the PR body name the expected E2E failures and HS-202-02 repair home. Setting CI to strict mode is a recommendation, not needed to honor this delivery; normal GREEN remains the phase exit.
7. Any visible but wrong summary or attempt host now fails a hard assertion even when the composite refresh observation is expected to fail. The `_loaded` docstring no longer claims every heading is a content marker. Search requires an owned visible click point; only the shortcut suffix may be clipped.

The revised scoped walk passed 2 tests in 86.37s. Final RED/GREEN captures, exported shot provenance, full suite, and gate remain pending at this response. No product files changed.

## Ledger from counsel

- **(b), HS-202-02:** Desk memory content is not exercised by this fence (only its dock door); partial-title recall, the aftercare toast overlap, and a receipt badge on MeetingPullout need their own repair evidence if taken in that lane.
- **(b), sitting / HS-202-06:** real owner-lock acquisition and background drain, process-level restart, physical egress and the owner's voice remain unproved by this fixture rig.

## Second reply — verbatim

Claude session: `3a12b6ea-c573-49ab-8a48-a24cc6e3ace4`.

VERDICT: RATIFY-WITH-CONDITIONS

The only conditions left are the pending proofs you named. Every harness condition from my first check is met in the current source. I ran nothing; I read the check record, the current test file, the appendix and the status risk row. I hold no dissent on CI or the Note pane.

FINDINGS:

1. **Dock: met.** `test_hs202_first_use_smoke.py:283-287` runs three named checks. `KNOWN[393]` carries only `dock-memory` (`:41`). `meetings_ok` now comes from the named `dock-meetings` check. Losing Speak or Meetings at 393 now fails strict mode as an unexpected defect.

2. **Pass branches: met.**
   - `thought-door` (`:306-315`) needs exactly one visible note field with `contenteditable="true"`. The old `.thought-workspace` shell is gone from the selector. If none of the three destinations appears, the wait times out and the run fails outright.
   - `notes-query` (`:438-456`) takes a note identity or an exact `.desk-deck-label` match. It then requires the content to load in the named region, on both branches, before the check records a pass. The substring match is gone.
   - One harmless residue: if two note editors ever appear, the check reads as the expected `thought-door` failure and not as a new one. I do not require a change.

3. **Shots: met in source; provenance pending.** Shots go to `tmp_path/shots` unless `HS202_EXPORT_SHOTS=1` (`:185`). A full-suite run can no longer write into the tree. Appendix `:51` names the export variable. The exported set itself does not exist yet.

4. **Provenance: met, and stronger than I asked.** The chain:
   - The define-endpoint POST carries the exact endpoint with its port (`:271`).
   - Its response gives a profile id and revision (`:272-273`).
   - The single planned leg must match both, and its host must equal `127.0.0.1` (`:374-376`).
   - The admitted hash and the receipt chain as before (`:398`, `:405-406`).
   I accept Astra's correction that the route contract stores the host without a port. The profile binding is the right proof.

5. **Disclosure: met.** Appendix `:16` says the restart is in-process. `:55-57` state:
   - the rig holds no owner lock;
   - the drainer is OFF, shown as NOT DRAINING on glass;
   - the test drains the real queue by hand;
   - the FakeIntel receipt hosts are route-derived.
   The ledger in the check record sends owner-lock drain, process restart and the owner's voice to the sitting.

6. **Record truth: met.** `:415-421` fail outright on any visible wrong summary or wrong host, even when `record-refresh` is an expected failure. The header's "route truth always fails normally" now holds before the reload as well. Missing or stale content stays the expected defect, which is right.

7. **CI: recorded; I accept the lane owner's ruling.** `current-phase-status.md:46` names the intentional RED E2E job, the unmerged PR, and HS-202-02 as the repair home. It tells the reader not to read strict GREEN as product GREEN. My earlier point was a recommendation.
   - One consequence, stated once and not a dissent: whoever merges this PR before HS-202-02 lands turns main's E2E job RED. The risk row already gives that stop signal.

8. **Clean Note pane: I accept it.** ThoughtDocumentPane's "Note body" is the HS-201-12 note surface. A live contenteditable field is a valid loaded marker for an empty new note. The fixture cannot tell whether that pane satisfies the owner's 2026-09-20 bounce; that is for the sitting.

CONDITIONS (all pending proofs, none needing a source change):

1. Append the final RED capture, `red-reviewed`, to the evidence. Its failure sets must be the five desktop names and the nine narrow names, with `dock-memory` in place of the old `dock`.
2. Append the exported GREEN, `green-exported`, together with the unchanged ratchet. Both widths must print "VERIFIED exact expected failures". The staged PNGs must be that run's bytes, with no `AM` drift at contract time. The evidence must name that run as the only source of the shots, with the earlier captures labelled as iteration history.
3. Read the full isolated suite output, `full`. The two fence failures must be the only new failures. Show that the tree shots were not touched afterwards.
4. `dw gate` passes. The story flip and the evidence ship in one commit. The PR body carries both verdicts and the RED-CI notice. The PR is opened and not merged.
5. Append this second reply to `checks/story-01-muaddib.md`.

MISSED: I have nothing new. The earlier items stand as ledgered:

- (b) For HS-202-02: Desk memory content, partial-title recall, the aftercare toast overlap and the host on the pullout.
- (b) For the sitting: real drain on his desk, process restart and his voice.

TUESDAY: Still no for the owner today. The fence now names each closed door singly and cannot turn green on a shell or on a wrong host. The repairs are HS-202-02's.

UNKNOWN:

- The `red-reviewed`, `green-exported` and `full` logs did not exist when I read, so none of those runs is proved.
- The focused result of 2 passed in 86.37s is Astra's claim. I have not seen the output.
- The PR body is not written yet.
- I did not test whether the 2.5-second `observe` bound can race a product poll in strict mode. If it flakes, split the timing out; do not widen `KNOWN`.
- I did not inspect `_chip_label`, the `.desk-deck-label` markup, or the accessible name of the Notes/Desk memory region. Today the wrong-program branch runs, so the match branch has never been executed.

## Astra's proof closure and lane ruling — 2026-09-21 UTC

**Astra: RATIFY for the authorized RED-fence delivery, not product repair
or merge. Muad'Dib: RATIFY-WITH-CONDITIONS**, with his two replies preserved
above. Source conditions were met at his second reply. The evidence now
contains final RED (00:50:32Z), strict GREEN plus the unchanged ratchet
(00:52:00Z), full suite, web baseline, metadata fixes and baseline comparison.

1. RED prints the exact five desktop and nine narrow failures, including
   `dock-memory`. Strict GREEN runs the same predicates and passes six
   tests in 86.83s.
2. All 26 PNGs come from that one exported GREEN run. Their hashes and
   dimensions are in `assets/story-01-fence/manifest.json`. Astra verified
   them after the full suite and reruns, and inspected final shots at both
   widths. Unrelated generated evidence was put back or parked.
3. Full-suite output was read: 8 failed / 11,299 passed / 116 skipped /
   4 xfailed. Both fence cases passed in strict mode. Two metadata failures
   were repaired and checked. Two runtime failures reproduce on pinned
   base `50ca0dd6`. Four full-run-only failures pass on base and twice
   serially on the lane, once immediately after both fence cases.
   [The ledger](../verification-ledger-story-01.md) keeps exact failures,
   evidence and follow-ups. No branch-new failure was reproduced. The
   parallel causes are unknown; this is not a full-suite GREEN claim.
4. The story and evidence are prepared for the same gated commit. Actual
   gate/commit completion is certified by the contract archive and commit
   trailers; the PR body records both verdicts and intentional RED CI.
   The owner's instruction is to open it against main and not merge.
5. The second reply is retained verbatim above. The metadata repairs only
   make carried inventory citations portable and regenerate its phase
   index; they change no verdict, product behavior, or test assertion.

The lane owner rules that these results satisfy the fixture-fence delivery.
Condition 3 is supported to the limits of the baseline comparison and the
method's two serial GREEN runs, not by a claim that an intermittent failure
can be disproved. Known failures remain named in the commit and ledger.
No open design dissent remains. Tuesday remains **no** until the repair
lane and the owner's sitting supply their own proof.
