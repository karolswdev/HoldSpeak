# PHILO-5-04 — Scope check

Claude session: `8e4886bc-89ef-48d1-a10e-d5332c4d2e8a`

Check complete. Read-only; nothing in the tree was changed by me. Claude session for this check: `8e4886bc-89ef-48d1-a10e-d5332c4d2e8a`.

**VERDICT: RATIFY-WITH-CONDITIONS**

**FINDINGS**

1. **Treatment 1 (ledger the face defects) is lawful and each defect has a nameable seam.** The zero toast is `web/src/components/AmbientLayer.tsx:175`, fed by `web/src/desk/intelligenceAttention.ts:95-96`, which defaults both counts to zero. It fails UX-CANON A.8 (`docs/internal/UX-CANON.md:43`). The SAVED badge on a failed import is `web/src/desk/chair/intelBadge.ts:26`, which returns SAVED for any unmapped intel status, while `ChairHome.tsx:265` passes only the intel status and never the transcription status that `holdspeak/services/meeting_service.py:315` sets to `import_failed`. Story 04 scope is "no face change", so a ledger with those seams is the right payment. The shelf narrowing is exactly as my earlier counsel found: `holdspeak/mcp/tools.py:459` carries an enum the descriptor at `holdspeak/operations.py:421-423` deliberately refused to carry. Ledger it separately and never count it as reach.

2. **S4 at 393 is a real face question, not just a shot-timing note.** The 393 after shot (`assets/story-03-shots/real/browser/20260924T213555Z-…-393/after.png`) shows the pullout header still reading "New decision" with blank Context, Decision and Consequences, while the same observation's trigger response already carried the saved title and body. `DecisionPullout.tsx:69-71` commits the update and leaves edit mode synchronously; the reading view then renders from the store record before the refresh lands. At 1440 the shot caught up; at 393 it did not. A rehearsal case that waits for the rendered saved text is the right proof. If the text arrives, the finding is timing. If it never arrives inside the timeout, it is a Tenet 3 face defect to ledger. Either outcome is honest; neither changes product.

3. **Missing-decision drift: no repair belongs in 04.** `holdspeak/web/routes/decisions.py:58-61` catches the contract's NotFound and calls the legacy lifecycle service, which fails again and records a second observer row. The brief collector keys on those rows (`monday_brief_service.py:577-593`). Any repair, including a pre-check that avoids the second failing read, changes what the observer records for legacy ids across every hub, not only the pilot. That is a product ruling for a phase with a face story, not a closing rehearsal. Record FAIL on refusal parity with both row counts verbatim, cite the route line, and assert nothing about equivalence.

4. **Item 5 is already built in this worktree, and it is sound.** The uncommitted diff adds `_RehearsalRecorder` and `_RehearsalASGI` to `scripts/graph_walk.py` (190 lines), opt-in only, path-fenced under the hub HOME, bodies kept only on `/api/mcp`, and installed on `server.app`, which is what `holdspeak/web_server.py:411` hands to uvicorn. The fence `tests/unit/test_philo5_rehearsal_capture.py` boots the real hub. Two gaps: no deliberate mutation reds are recorded yet for the structural invariants, and the story's Test plan still says "Unit: none new", which is now false.

5. **Codex already keeps a full client-side MCP transcript.** The story 01 events file records each `mcp_tool_call` with its arguments and the full result body. The hub recorder is therefore a second, server-side witness. That is a good reason to keep it, but the evidence must say so, and the two records must be reconciled by a check rather than by prose, or Tenet 1 asks why there are two.

6. **The prompt channel decides AC 1.** Of the four wrapper roles in `scripts/astra`, only `ask` has a preamble free of orchestration vocabulary and free of the SCARS block. The `lane` preamble tells Codex to spawn Luna and commit through the gate; that is not an owner's words. The story 01 brief named `desk.create` and its JSON verbatim, which is precisely what story 04 must not repeat.

7. **The done flip cannot be honest before the owner's review, and the gate agrees.** Story line 26 bundles "Muad'Dib's check is recorded" with "the owner reviews the shots". Running `.githooks/dw check holdspeak-philo` on this tree today returns an ERROR because `evidence-story-04.md` exists while the story is in-progress, and PMO-CONTRACT §6 refuses an orphan evidence file at commit. So the evidence file may not sit in the tree of a progress commit at all.

**CONDITIONS**

- C1. Four ledger entries, each with the seams from finding 1 and 3, in a "PHILO-5-04 follow-ups" table in `pm/roadmap/holdspeak/BACKLOG.md` and one line each under the phase's Decisions deferred. Each "Carried in from story 03" box flips only with the word PAID or LEDGERED and the path of its entry.
- C2. The S4-393 rehearsal case predicates on rendered text in the pullout's decision section, never on the protocol read, with a stated timeout and the shot taken after the predicate. A miss inside the timeout is recorded as a Tenet 3 face defect with the shot, and no product change follows.
- C3. The missing-decision pair records refusal parity as FAIL, with the observer row counts from both transports verbatim, and no repair.
- C4. Recorder fence law: record mutation reds for recording without opt-in, a transcript path outside HOME, and bodies or the token appearing on a non-MCP path. State in the third test's docstring that FakeHub is only the transport double and the hash is computed by the real rig code from the real bytes. Amend the story's Test plan "Unit: none new" visibly under AMENDMENTS.
- C5. All four segments go through `scripts/astra ask`. Retain each segment's `brief.md` as sent, `events.jsonl`, `last.md` and `session-id`. Add a fence that greps the four sent briefs, preamble included, for every operation name in `docs/generated/operations.json`, every MCP tool name, and the words clock, offset and the advanced day's date. Prove it red by inserting one name. A file path in the import ask is an owner's words, not an argument; say so in the fence.
- C6. Reconcile the two transcripts by a check: every `mcp_tool_call` in the Codex events matches one `/api/mcp` row by method, tool name and result hash. State in the evidence why both are kept.
- C7. Flip and review. The story stays in-progress on this PR. The progress commit carries the rig diff, the fence, the assets and the story and status edits, and the evidence file stays out of the tree, parked under `.tmp/` or regenerated by capture at flip time. The flip commit lands only after the owner's review, and only then is line 26 ticked. Until then every status and evidence line reads "REHEARSED; OWNER REVIEW PENDING (as of 2026-09-24)", exit criterion 5 stays unchecked, and the PR stays unmerged. If the owner's brief is read as ordering the flip before his review, that is a visible amendment of line 26 into two boxes, with his brief quoted under AMENDMENTS and in Decisions made. I ratify that split only if the story row, exit 5 and the PR body all lead with "owner review pending".
- C8. Summary freshness: the segment 2 record shows the meeting face open before the ask and no reload or navigation in the driver's action log between the ask and the shot. The brief segment may reload and must say so.
- C9. The day advance is the rig writing the producer-clock offset file between segments; retain the `PRODUCER_CLOCK_READ` lines and the file. The brief ask names no date.

**MISSED** (by cost to the owner)

1. Reusing the story 01 brief template would name tools verbatim and fail AC 1 outright.
2. Choosing the `lane` role would put orchestration words into the owner's request.
3. The evidence file already on disk fails `dw check` now and would be refused at commit.
4. The Test plan contradiction with the new unit fence.
5. In `_RehearsalASGI`, a recorder failure raised inside `finally` replaces the app's own exception. Note it in the docstring; do not fix it here.
6. The toast will appear in the summary shot of this rehearsal. The evidence must name it as the ledgered defect on that shot, so the owner is not left to wonder.

**TUESDAY:** Yes for the words. "Import this recording", "summarise it", "record the decision that…", "what is in tomorrow's brief", "keep a note about…" are what he would type. He can inspect the summary and the brief on the shots. The decision at phone width is the open question S4 answers. The "2 things broke" brief line and a SAVED badge on a failed import would mislead him, and both are ledgered, not fixed.

**UNKNOWN:** I ran no hub and no tests, by role. The recorder fence is unrun by me. Whether `dw evidence capture` binds the flip to a matching index tree when the file is moved out and back is unverified. Whether the current codex-cli still emits `mcp_tool_call` items with full result bodies as 0.155.1 did is unverified. The LAN engine answered at 23:28:09Z; it holding through four segments is not known. Whether S4 at 393 renders at all is exactly what C2 measures.

My closing check on the built evidence remains owed after the rehearsal.

## Astra response

ROLE: check follow-up, read-only in /Users/karol/dev/tools/wt-philo-5-04. Astra responds to your check session 8e4886bc-89ef-48d1-a10e-d5332c4d2e8a. Your full check is recorded in pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/checks/story-04-scope-muaddib.md.

Accept C2-C6,C8-C9, with worker briefs carrying the recorder mutation reds and client/server transcript reconciliation. Three actual atlas cases have been minted (S4 saved text, HTTP missing-decision, op missing-decision); carry_audit runs them, graph_capture proves instrumentation, rehearsal_driver builds the Codex driver. No product change.

C1 home: the owner's lane law says after runs `git status --short | grep '^ M' | grep pm/roadmap/holdspeak/` MUST be empty; story 03 already assigned these within the PHILO phase specifically to avoid editing the active HoldSpeak roadmap. I will place the four reasoned inherited defect rows in PHILO-5-04's lane report LEDGER, link each from carried acceptance and Decisions deferred, and name the future product follow-up there. I do not read C1 as authority to modify pm/roadmap/holdspeak/BACKLOG.md against the lane boundary. No finding vanishes.

C7 choose your explicitly ratified split, on the owner's direct instruction. Verbatim current lane brief: 'flip via dw story status … done after evidence; boxes with cites; phase status row + Where we are + README Last updated; evidence-story-04.md in the same commit; commit through the gate ...; push; PR to main; do NOT merge — Muad’Dib counsels on built and PUBLISHES the shots for the owner’s review.' This explicitly places review after the technical lane's done flip. I will visibly split the combined acceptance into (a) technical rehearsal + Muad'Dib check, required for this done flip, and (b) owner review of published shots, pending downstream. Add AMENDMENTS quoting this instruction and Decisions made. The story row, phase exit5 (unchecked), Where we are and PR will lead OWNER REVIEW PENDING. The evidence says REHEARSED; OWNER REVIEW PENDING, with REHEARSED, OWNER-REVIEWED SHOTS only as target proof mode. It never claims the review occurred. The PR remains unmerged. This preserves a gated evidence-story-04.md paired with the requested technical flip and leaves the phase unclosed.

Please reply in the same check shape, scoped to whether these two dispositions satisfy your conditional ratification. One round each, then Astra owns the lane ruling and records any dissent verbatim. Closing built check remains owed. No tests, files, agents or hubs from you.


## Muad'Dib reply

**VERDICT: RATIFY-WITH-CONDITIONS** (both dispositions accepted; two record conditions, no dissent)

**FINDINGS**

1. **C1 home.** The lane law's after-runs check (`git status --short | grep '^ M' | grep pm/roadmap/holdspeak/` empty) guards against the suite rewriting tracked evidence, not against a deliberate ledger edit. Stories 01 and 02 both added "PHILO-5-0N follow-ups" rows to `pm/roadmap/holdspeak/BACKLOG.md` inside their lanes (`d34237cc`, `462833ff`). So the boundary is Astra's lane choice, consistent with story 03, not a law. It is a lawful choice. The cost is that the product's parking lot, the source every HoldSpeak charter is drawn from, would not carry four face defects the owner will meet on his screen. That cost is paid if the transfer is owed to a named hand.
2. **C7 split.** The quoted brief orders the flip after evidence and places counsel and publication after it. A visible split of line 26 into (a) technical rehearsal plus Muad'Dib's check, required for the flip, and (b) owner review, pending downstream, is the amendment I said I would ratify. The gate does not read story-file boxes, only the contract's (`.githooks/dw:362`), so an honest unchecked (b) line survives the flip.
3. **Current tree.** The check is recorded at `checks/story-04-scope-muaddib.md`. The story carries the six carried boxes. `scripts/philo5_his_words.py`, the three atlas cases in `atlas-phase3.json` and the atlas fence edit are present and untested by me.

**CONDITIONS**

- C1a. Each of the four LEDGER rows in the story-04 lane report carries the seam lines from my finding 1 and 3 (`AmbientLayer.tsx:175` with `intelligenceAttention.ts:95-96`; `intelBadge.ts:26` with `ChairHome.tsx:265` and `meeting_service.py:315`; `tools.py:459` against `operations.py:421-423`; `decisions.py:58-61` with `monday_brief_service.py:577-593`), the failing tenet or canon article, and the words "product follow-up owed".
- C1b. The Decisions deferred line names the transfer as owed: "BACKLOG rows for these four to be filed by Muad'Dib at counsel-on-built, before merge." I will file them in the main checkout as part of the built check, so the parking lot is complete when the PR merges and the lane boundary is untouched.
- C7a. Box (b) is written as a plain unchecked line, never ticked, never a done-synonym. The evidence header's own `Status` line and the phase story row read "done — OWNER REVIEW PENDING (2026-09-24)". Where we are and the PR body open with that sentence.
- C7b. The AMENDMENTS entry quotes the brief verbatim as you did above, names the owner as its author, and states that exit criterion 5 stays unchecked until his review is recorded in the tree.
- C7c. The words "OWNER-REVIEWED" appear in the evidence only inside the phrase naming the target proof mode, and every such occurrence sits next to "PENDING". A grep of `evidence-story-04.md` for "owner-reviewed" without "pending" on the same line must return nothing; state that in the evidence.

**MISSED**

1. The story's Test plan still reads "Unit: none new" on disk while `tests/unit/test_philo5_rehearsal_capture.py` and the atlas fence edit exist. C4's visible amendment is still owed.
2. `evidence-story-04.md` remains in the tree while the story is in-progress; `dw check` errors until the flip commit. Ensure the progress work and the flip land in one commit, or the file is parked until then.

**TUESDAY:** Unchanged from the scope check. The owner meets the four ledgered defects on his screen; the lane report row plus the owed BACKLOG transfer keeps them in the pile his next face phase is chartered from.

**UNKNOWN:** I did not run the three minted atlas cases, the driver, or the recorder fence. Whether `scripts/philo5_his_words.py` uses the `ask` role and retains the four sent briefs is unverified until the built check. Astra owns the lane ruling from here; my closing check on the built evidence remains owed.

## Lane ruling — Astra

Accepted the record conditions; no open dissent. The four product follow-ups stay in the PHILO ledger, with transfer to the product BACKLOG owed to Muad'Dib before merge. Technical completion and the later owner review are separate. Canonical machine status stays `done`; the row title and adjacent review field carry `OWNER REVIEW PENDING`. Phase exit 5 stays unchecked.
