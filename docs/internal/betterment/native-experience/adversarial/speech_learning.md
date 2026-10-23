# speech_learning — Correct a phrase and replay or learn it later

Baseline: `main555728021`  
Reviewer task: `review_speech_learning`  
Evidence class: source and active test inspection; existing empty-state captures; no test execution or owner walk.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

Job starts with a dictation, identifies its journal entry, marks the result
wrong, teaches a text/intent/target correction, replays the stored transcript,
sees before/after routing, and returns to the next dictation. It must survive a
provider refusal, lost request, restart, retention, and a return from another
Desk surface without confusing “stored”, “fired”, “reached”, and “delivered”.
The brief names the application-model contract but not these states.

FINDINGS:

1. **High — the audit’s evidence ledger is materially incomplete.** It says
only `docs/CAPABILITIES.md:24-29` was inspected and names no tests
(`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:1855-1869`).
Active consumers and assertions exist in `web/src/pages/cores/dictation/SpeakFace.tsx:608-708`,
`web/src/pages/cores/dictation/Journal.tsx:187-313`,
`tests/integration/test_dictation_journal_replay.py:95-154`,
`tests/integration/test_web_dictation_correction_ritual.py:50-70`, and
`web/src/pages/cores/dictation/__tests__/speakFaceTeach.test.tsx:272-340`.
This costs the owner duplicate design work and risks inventing a second “task
view” (Tenets 2 and 3). Correction: inventory these seams and state which
claims remain unexecuted; the catalogue is not behavior proof.

2. **High — replay recovery is not a closed task contract.** The backend returns
named failures and preserves the original row
(`holdspeak/web/routes/dictation/pipeline.py:1457-1538`), but the Journal handler
has no pending, error, retry, or return state (`web/src/pages/cores/dictation/Journal.tsx:504-510`).
A provider failure can leave the architect with no visible outcome despite a
durable identity (Tenets 3 and 6). Correction: specify and test
`entry_id + pending|succeeded|failed`, named failure, retry, and unchanged
row/no new journal row; include leaving and returning to the open row.

3. **High — learning refresh is not a proven cross-face contract.** `Learned` listens
for `learning_event` (`web/src/pages/cores/dictation/Learned.tsx:160-166`), but
`Memory` reads its digest once and has no bus subscription
(`web/src/pages/cores/dictation/Memory.tsx:52-63`). The server emits that event
only when a correction has positive reach (`holdspeak/web/routes/dictation/pipeline.py:1422-1437`),
and the fallback teach route has no corresponding broadcast
(`holdspeak/web/routes/dictation/pipeline.py:1146-1195`). A zero-reach teach has
no event; unmount/remount may mask it, but a concurrent window can show stale
learning (Tenets 3 and 6). Correction: define one
store-change invalidation; refresh Learned and digest from it, while keeping
`APPLIED`, `REACHED`, and `TAUGHT` distinct.

## Convergence

Converge with `speech_dictation` (same run/result and journal seam),
`capture_thought` (first consumer of the preserved transcript/draft), and
`native_input` (text editing, voice, IME and return-to-focus). The shared
contract is the existing journal id, raw/final text, correction and operation
outcomes, and feedback—not a new registry or runtime. Keep `capture_thought`
separate: saving a Note is a different durable effect; keep `native_input`
separate: caret/IME semantics are not routing learning; and keep
`voice_commands` separate: it executes a configured Desk verb. The inventory
groups these families under speech capture (`USE-CASE-INVENTORY.json:1676-1685`)
but does not bind first consumers or state ownership.

## User experience

The source suggests a loop: Wrong opens an in-world teach row, the journal
route links the correction to its entry, and replay previews without typing
(`SpeakFace.tsx:610-622`; `pipeline.py:1457-1465`). The
1440 Journal and 393 Learned captures show only quiet empty states
(`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-dictation-1440-Journal.png`,
`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-dictation-393-Learned.png`); they do not prove the loop,
failure clarity, accessibility, or owner delight. A senior architect needs one
stable result identity and an honest next action, not stale digest or a
vanished replay failure.

CONDITIONS: Correct the evidence inventory, define the shared identity/state
contract, and add the four acceptance challenges below before treating this
audit as an implementation brief. No new surface is required if existing
Speak, Journal, Learned, and Memory consumers can close the loop.

MISSED:

1. Cross-face refresh after a correction with zero reach (highest cost: false
   learning state).
2. Replay provider refusal/cancellation and retry without mutation.
3. Restart and retention boundaries: correction survives; applied counts may
   decrease only when retained journal rows age out.
4. Return from Journal/Settings to the pending Speak result without losing the
   raw transcript or journal id.

TUESDAY: The path can be fast when it works, but stale learning and silent
replay failure prevent a dependable Tuesday correction loop.

## Acceptance challenges

1. Given a delivered result with a journal id, choose TEXT, edit “What you
   said”, Teach, and assert one linked correction, a `TAUGHT` receipt, and a
   refreshed Learned row without remounting.
2. Teach a TARGET correction, replay the same journal id, and assert a
   before/after target change, no typing, no new journal row, and a visible
   `REPLAY` result; repeat with a provider refusal and assert named failure plus
   retry.
3. Teach a valid correction whose reach is zero, switch to Learned and the
   digest, and assert both surfaces show the new stored rule while `APPLIED`
   remains absent.
4. Leave Speak with an unsubmitted result, open Journal or Settings, return,
   and assert the raw transcript and journal id are unchanged; restart and
   assert the correction remains available and retained-count semantics stay
   honest.

UNKNOWN: No tests were run, no live Desk/provider/native walk was performed,
and no owner appearance or performance acceptance is claimed. The captures are
baseline empty states only; learned routing quality under real speech remains
unverified.
