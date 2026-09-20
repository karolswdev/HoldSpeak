# HS-201-08 — story-08-docs-delta-muaddib

Invocation confirmed by CLI result: model `claude-fable-5-1`, session `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. Peer clock estimates below are unverified; capture timestamps are UTC. Read-only check.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on C4 and C2 for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:** `.tmp/hs201-green/philo-boundary-delta.md` in full.
- **What I checked independently:**
  - I read current source at the lines cited for the three added rows.
  - I ran `git grep` against HEAD for the three removed excerpts.
  - I ran `git status` on the four source paths behind the delta.
- **Not re-run:** I did not re-run `collect()`. Root's 898→898 count and the 3/3 delta stand as root's claim. I checked the row content, not the totals.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The three removals are inherited and already true on 321247d2.
   - `git grep` against HEAD finds none of these in holdspeak/ source:
     - "Verify endpoint compatibility with the OpenAI"
     - "an untitled Meeting requests an auto-title"
     - the old line "Custody may understand Anthropic before execution does. It still"
   - The only surviving match is the rewritten comment at model_library_service.py:555
     at HEAD.
   - So the committed census was stale against its own base when #589 merged. The
     regeneration records a change main already contains.
   - `git status` shows no lane diff on these files:
     - holdspeak/commands/doctor.py
     - holdspeak/meeting_session/intel_admission.py
     - holdspeak/services/model_library_service.py
     - web/src/pages/cores/history/CatalogRail.tsx
   - Root's statement that these are "not this lane" is correct.

2. Root's correction of the worker's excerpt is right.
   - The `model_transport` hit in model_library_service.py is line :376,
     "# The existing OpenAI-compatible execution adapter accepts the closed". That line
     carries the lexical token.
   - The worker cited the :377 prose ("Meeting result schema. Carry that adapter
     support…"), and the delta file still says :377 at two places.
   - Current source, as I read it:
     - :376-378 is the adapter comment.
     - :555-556 is the Custody/Readiness comment.
     - CatalogRail.tsx:254 is "`onSelect` and issue ZERO requests. Both run verbs
       dispatch."
   - Record the corrected delta in evidence. Do not record the worker's file verbatim.

3. Only one row in the delta reflects a change in product behaviour.
   - Five of the six rows are comments.
   - The doctor.py `fix=` string is the only one tied to a product change. Its removal
     matches a ratified decision: current-phase-status.md has Phase 201's lane-A
     amendment under "Decisions made", and the Cloud intel check now answers
     "Live analysis is off for Record".
   - A `model_transport` candidate leaving the census because a cloud probe was retired
     means the census is tracking the change correctly.
   - I agree that stale rows must not be restored and that no production comment should
     be altered to keep a row alive. Doing either would turn the census into a fixture.

4. The Firefox row.
   - The false removal is honestly diagnosed: the temp root lacked `extensions/`.
   - Keep that correction in evidence as written. It is the kind of mistake the record
     should show.
   - It also sets a rule for the real run. Regenerate from the worktree root, never from
     a partial copy.

5. C2 as I wrote it was self-referential. Root is right, and the replacement is better.
   - A capture cannot embed the hash of an index that will later contain the capture.
   - The proposed sequence is accepted:
     a. stage all inputs;
     b. capture the eleven docs commands under Python 3.12;
     c. prove nothing moved;
     d. restage evidence and closure records only;
     e. generate the final contract.
   - C2 is withdrawn in its original wording and replaced by condition R2 below.

CONDITIONS:
R1. Evidence carries the corrected 3-removed / 3-added table with the :376 fix. Each
    removal is attributed to the inherited commits the worker named
    (a07d4bb5/d23cfe81, 183f1b5c, 6365b7d3; added row c31a4da0).
    - I did not verify those hashes. Root should confirm each with `git log -S` before
      writing them down.
    - If a hash cannot be confirmed, write "inherited on 321247d2" and leave it out.
R2. Replacement for C2. Make it mechanical.
    - Step 1. After staging the inputs, record `git write-tree` as T1 in the capture
      header.
    - Step 2. Run the eleven docs commands exactly as test.yml:27-37 has them. Use
      /opt/homebrew/opt/python@3.12/bin/python3.12 and record its version string.
    - Step 3. Restage evidence and closure records only.
    - Step 4. Record `git diff --cached --name-only T1`. Every path in that output must
      be under pm/roadmap/ or the story's checks/ folder.
    - If a generator, a generated output, a metadata shard or a product file appears in
      that list, the capture is void. Repeat it from a new tree T1'.
    - This check proves "no input changed after the passing capture". A plain
      `git diff --exit-code` cannot prove it.
R3. Regenerate from the full worktree root, in one pass, LAST. This is after
    roadmaps.py and all label-string edits.
    - The post-regeneration diff of boundary-candidates.json must show exactly the 3/3
      semantic delta plus line-number movement.
    - If any other row is added or lost, stop and come back.
R4. Standing conditions are unchanged.
    - The full quiet-tree pytest must be read to its end.
    - Every failure must be named.
    - Nothing may be relabelled green.
    - Counsel-on-built is owed on the final tree.

MISSED (ranked by cost to the owner):
1. #589 merged a census that was already stale against its own base, as finding 1
   shows.
   - The owner ruled "fully embrace", so this is not a complaint.
   - It is a ledger fact for Philo's first follow-up. The docs job would have been red
     on the merge commit itself.
   - The ledger should say main's docs red did not originate in Phase 201's lanes alone.
2. A lexical census that indexes COMMENTS will change every time a comment is rewritten.
   - Five of these six rows are comments.
   - This is the same fragility as the line anchors.
   - One ledger line is enough. Do not redesign it here.
3. The API roster grows 693→694 with `POST /api/concierge/summary-selection`.
   - That is a Phase 201 route appearing in a reference for the first time.
   - Confirm it carries the expected egress/authority row in the regenerated
     API_REFERENCE.md. It should not be a bare entry.

TUESDAY: Not applicable. No face is touched. The owner gets references that match the
tree he is actually running.

UNKNOWN:
- Root's row totals and the completeness of the 3/3 delta. I checked the content of the
  named rows, not the whole 898-row comparison.
- The four commit hashes the worker attributes (R1).
- Whether 3.12-regenerated bytes match CI's. Only the PR's docs job settles this.
- The full pytest run is still in progress. This ruling covers no part of it.
```
