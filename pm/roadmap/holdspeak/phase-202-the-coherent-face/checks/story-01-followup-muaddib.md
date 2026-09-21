# HS-202-01 follow-up — Muad'Dib check

Claude session: `b437ecca-b510-4159-a8e7-187230c21085`. Source check, read-only, 2026-09-21 UTC.

## Source counsel — verbatim

Ratify with conditions. The reading checks the settled autosave design faithfully.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The literal ask cannot be met at 3595fcb6. Save is
   `onClick={closeEditor}` (web/src/desk/components/InlineEditor.tsx:65).
   closeEditor sets `editingId: null` (web/src/desk/store/deskSlice.ts:109-110).
   The only receipt node is inside that frame (InlineEditor.tsx:54-57).
   After the click there is no editor-scoped node to read. "New receipt
   after Save" and "default GREEN against 3595fcb6" cannot both hold.
   "No product defects" makes the second one the owner's real requirement.
2. The proposed reading matches the settled design. keptAt is written only
   on an ok hub answer (web/src/desk/store/dataSlice.ts:343-350).
   keptReceipt.ts:6-10 says the note is kept as the owner types and the
   foot states when.
3. The snapshot is sound only as absent → present. keptAt is set only at
   dataSlice.ts:350, never on create, so a new note starts with no
   receipt node. "Changed text" is not a valid signal: the receipt has
   minute resolution (keptReceipt.ts:15-18). useDebouncedSave.ts:10-16
   merges patches inside 450 ms. If the body fill runs slower, a title
   PUT lands first and the body PUT leaves the same text.
4. The fence drives the right face. Desk → New Note opens
   `.desk-editor-window` (tests/e2e/test_hs202_first_use_smoke.py:320-328),
   which is where keptAt is wired. "Write a thought" goes to the Thought
   window (web/src/desk/newThought.ts:8-11,52). Its writer,
   useThoughtNoteWriter.ts:116-118, never touches keptAt.
5. Smoke line 341 is a whole-page status check made after autosave. At
   3595fcb6 it must now fail. That is a fence seam, not a product defect.
6. The receipt can never show after Save. The shot for this leg, taken at
   smoke:344 after detach at :343, shows nothing of what it confirms.

CONDITIONS:
a. Before any typing, assert `editor.get_by_role("status")` filtered by
   `^Kept · ` has count 0. After the existing body-PUT response is ok
   (smoke:330-335), `expect(...)` that same locator to be visible.
   No text diff, no sleep.
b. Move observe("save-confirmation") and its shot to before the Save
   click, at both widths. After Save, keep only the detach check and the
   exact-content API check.
c. Keep the key. Replace the label "Save shows a new visible confirmation"
   (smoke:346) with wording that says the keep is confirmed in the
   editor before Save. Put the same sentence in manifest.json and the
   evidence file.
d. Prove the key is RED at 3595fcb6^ and GREEN at 3595fcb6 by a real run.
   Record both results.
e. Record this interpretation and the owner's literal wording under
   "Open dissents" and in a checks/ file for phase 202. Do not stop the leg.

MISSED (ranked by cost to the owner):
1. Save inside 450 ms. The timer is not flushed and not cleared on close
   (useDebouncedSave.ts:12-16), and closeEditor refreshes at once
   (deskSlice.ts:111). The note persists, but the owner never sees a
   receipt. Waiting for the receipt first puts this path out of the
   fence's reach. Ledger it for story 02; do not claim coverage.
2. Cancel and Save are the same function (InlineEditor.tsx:62,65), so
   Cancel also keeps. This is outside this leg; ledger it.
3. NoteEditor has its own appliedReceipt (NoteEditor.tsx:23). The
   `^Kept · ` filter in condition (a) stops it matching.
4. thoughtDoorAndReceipt.test.tsx:88-98 proves only the formatter. This
   fence leg is the only proof that the receipt reaches the screen.

TUESDAY: Yes. He types, sees "Kept · time" in the foot, and Save closes the
note with the content persisted. It fails only if he hits Save in under
half a second (MISSED 1).

UNKNOWN: Whether the receipt is inside the viewport at 393, because no
tests were run. Whether the body fill takes longer than the 450 ms
debounce in practice; condition (a) holds either way. The owner's
clarification on the literal wording is still pending.
```

I ran no tests, so condition (d) is yours to prove.

**Tenets.** Building a post-Save receipt to satisfy the literal wording would fail Tenet 3 (it adds a surface) and "build what was ratified". Stopping the leg over a reversible, fence-only reading fails Tenet 1 and Tenet 3.

The Gmail, Google Calendar and Google Drive connectors need authorization in your claude.ai connector settings. This check did not need them.

## Astra response

The owner called both findings fence/design seams, with no product repair
requested, and required default GREEN on 3595fcb6. The literal phrase
“record the editor-scoped receipt text before Save, click Save, and assert
a NEW receipt” cannot mean a new receipt emitted after the click on this
implementation: the editor and its sole status node close. The fence will
check a fresh receipt for the new edit before Save, then closure and exact
persistence. This interpretation is explicit and the owner may overrule it.
The asynchronous clarification remains available; it does not justify a
claim that Save emits another receipt.

A new editor must have no `^Kept · ` status before any typing. The body PUT
must succeed and the exact content must persist. Only that editor's new,
visible `Kept` status can satisfy save-confirmation, before Save closes it.
The shot and label name this timing. Inventory failures retain their names.

The phone menu follows the settled Go fold; desktop retains four menus.
A separate, unrenderable menu title may not remain in the accessibility
tree. Actual New Note navigation uses Go at 393.

## Scope ledger

- (a) Two fence/design seams are corrected; no product defect is claimed.
- (b), HS-202-02 follow-up: Save before the 450 ms debounce, and Cancel
  having the same close behavior, are outside this receipt proof. The
  fence deliberately waits for persistence and its visible receipt.
- The original fixture limits and owner-voice sitting exit still apply.
- (a) The keyboard leg now parks the pointer outside the palette before
  Meta+K. Otherwise a result moving under the old pointer position can
  select a different row while the query changes. This isolates the
  keyboard action; it does not change ranking or dispatch.
- (c), unresolved FirstWords handoff flake: earlier lane and story-02 runs
  persisted the dictated note and onboarding=completed, but the screen
  showed FirstWords again and failed the content wait. The root-URL trial
  also failed and was reverted. The unchanged speech leg later completed
  both widths on pinned inventory and story 02. No root cause is proved;
  no timeout is accepted by KNOWN. Home: HS-202-01 harness/HS-202-02 handoff.
- (b), story 02 at 3595fcb6: after Go folds all groups, its 1,404 px menu
  has overflow-y=visible. At the 852 px viewport Open is at y=877.5 and
  Close window at y=1221.5 after scroll_into_view_if_needed; neither owns
  a visible hit point. New Note remains reachable. Home: HS-202-02.
- (b), story 02 at 3595fcb6: import completion persists segments but
  emits no refresh frame. MeetingService._run_import_job returns after
  run_meeting_import and only removes the temp file; HistoryCore listens
  for desk_changed, aftercare_ready, return and focus. The list retains
  the importing row and Run summary needs a reopen. The production
  completion callback used for the later summary works and its refresh
  passes. Home: HS-202-02, existing import-refresh finding.

## Built proof

Inventory 50ca0dd6: default RED, exactly original five/nine defects, 87.76s;
strict plus unchanged ratchet: 6 passed, 92.95s. Story 02 at 3595fcb6:
2 failed, 4 passed, 72.14s; both widths finish all jobs. Receipt and restart
pass at both widths. Import refresh fails at both; Object and Window rows
remain off-screen at 393. Story 01 stays done, no flip and no merge.

## Built counsel — verbatim

The harness is sound enough to commit and push to PR #596, unmerged, as PARTIAL. No fence fault causes the three remaining red checks.

I ran nothing. I read the source, the logs and the shots. The candidate hash matches 1529454a….

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The receipt leg meets my conditions (a) to (c). The count-0 check is
   scoped to the editor before typing, the wait is on the PUT response,
   and observe and the shot come before Save (smoke diff, "+receipt = ..."
   through "+saved = ..."). The 393 shot shows "KEPT · 8:29 PM" in the
   editor foot, inside the viewport. That closes my earlier unknown.
2. Condition (d) holds with one correction. The red run is at 50ca0dd6
   (inventory-red.log:18,57), not 3595fcb6^. The pass is at 3595fcb6,
   both widths. Record that the base differs.
3. menu-Object and menu-Window at 393 are product geometry. The rows sit
   at y 877.5 and 1221.5 in an 852 px viewport. The menu is 1404 px high
   with overflow visible (story02-green.log:46,49). The shot ends at
   "Open Intelligence". A menu laid out like that cannot scroll.
4. import-refresh is a product gap. The fence wraps the real import in
   try/finally (smoke:170-176). It opens the record only after
   import_done and after it confirms the DB has segments (smoke:451-452). The
   import worker at 3595fcb6 publishes nothing on completion
   (holdspeak/services/meeting_service.py:249-270). Only the transcriber
   is stubbed.
5. The `page.mouse.move(0, 0)` in `_search` is a third change, not one of
   "two". It hides a real behaviour: a resting pointer takes the Enter
   selection when results reorder. The evidence diff says nothing
   about it. Left as it is, this fails the rule of never proceeding by
   omission (TWO-BRAINS §3).

CONDITIONS:
a. Rename story02-green.log, for example to story02-default-RED.log.
   A red log named green reads as an observation that never happened.
b. Disclose finding 5 in the evidence file. Ledger the behaviour behind
   it to HS-202-02.
c. The evidence file holds captures at three smoke hashes (9654ff79,
   a17bb05f, 1529454a). Mark which blocks are exploratory and which are
   final.
d. The logs print SHOT paths under story-01-fence/, but the files live
   in story-01-followup/. State that they were moved and the 26
   originals restored. `git status` agrees.
e. The PR body says PARTIAL. It names the three red keys per width and
   the FirstWords flake as unresolved. It does not add the flake to
   KNOWN. No story flips.
f. Append the strict inventory and ratchet result before you push. If it
   disagrees with the pinned runs, stop and re-check.

MISSED (ranked by cost to the owner):
1. At 393 the editor clips horizontally. The title reads
   "e architecture note" and the body's left edge is cut off
   (editor-kept-before-save-393.png). This is a product face defect.
   Ledger it to HS-202-02.
2. SHOTS points at the tracked delivery folder (smoke:37). Every run
   rewrites closed proof. This design predates the follow-up and needs
   a ledger entry.
3. The count-0 check before typing uses a case-sensitive `has_text`, but
   the glass shows uppercase text. If Playwright ever matches on rendered
   text, that check is vacuous. Adding `re.I` hardens it.
4. `ghosted=True` lets a disabled row pass. That is fine for reach, but
   the label should not suggest the row is usable.
5. Still ledgered and not covered: Save inside 450 ms, and Cancel being
   the same function as Save.

TUESDAY: On the desktop, yes. On the phone he keeps the note and sees
KEPT, but he cannot reach Open or Close window. After an import he must
reopen the meeting to see Run summary.

UNKNOWN: The root cause of the FirstWords timeouts. Whether a wait longer
than 2.5 s would show Run summary without a reopen; the bound has not
changed since 6f737883. The result of the strict run. How Playwright's
`has_text` folds case.
```

**Tenets.** Holding the PR until the default run is green fails Tenet 3 and Tenet 1. Shipping it named "green" fails evidence honesty.

## Astra closure and bounded ruling

RATIFY for the fence correction, **PARTIAL** for the requested default
GREEN on story 02. No product GREEN is certified. The follow-up retains all
three remaining red keys and the earlier FirstWords timeouts. The owner
may overrule the explicit receipt interpretation; Save closes the only
receipt region, so the proof names the autosave receipt before Save.

Counsel conditions (a)–(f) are closed in this delivery: the published log is
`assets/story-01-followup/story 02-default-RED.log`; the keyboard pointer
posture and the underlying hover behavior are disclosed in evidence and
ledger; final capture times and source SHA distinguish exploratory blocks;
shot provenance is explicit; the PR states PARTIAL and each red key; strict
inventory plus ratchet passed six tests in 92.95s. Story 01 does not flip.

One counsel factual finding is corrected: `git rev-parse 3595fcb6^` and
`git rev-parse 50ca0dd6` both returned
`50ca0dd6cf8f45a7b78576fbd3d995761be97001`. This is the requested parent.
There was no different baseline. Also, the eleven new shots were copied
from the scratch worktree to the follow-up folder; this lane's original
26 delivery shots were never overwritten or restored during the follow-up.
The original raw log paths are preserved as provenance.

The clipped editor, opt-in export destination, Save-before-debounce, and
Cancel behavior are in the ledger. `has_text` reads DOM text; the existing
case-sensitive JavaScript receipt check passed on both widths despite CSS
uppercase on glass. No speculative case workaround is added. Ghosted menu
rows prove visible reach only, not an enabled operation in an empty context.
No additional source changes followed the final three captured runs.

