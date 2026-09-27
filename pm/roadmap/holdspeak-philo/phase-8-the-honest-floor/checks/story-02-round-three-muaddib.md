# PHILO-8-02 — Muad'Dib's lane record, rounds three and four

Fedaykin lane (Opus 5.5) for Muad'Dib. Branch `feat/philo-8-02-one-delete`, PR #672.

## Round three (Codex Astra r1 on `b65107f5`, BOUNCE — `story-02-built-astra-r1.md`)

Paid at `d3eab7e8`. The record is `docs/internal/philo/phase-8/one-delete/README.md` §"Round three". Codex Astra r2 (`story-02-built-astra-r2.md`) confirmed these fixes: repeat plus Undo, the host above DeskApp's early return (including recovery and Undo at 1440), the foot, and the resize rule.

## Round four (Codex Astra r2 on `d3eab7e8`, BOUNCE — `story-02-built-astra-r2.md`)

| Item | Cause | Repair (file:line at the round-four commit) |
|---|---|---|
| 1. A successful delete cleared an unrelated failed rename ("RENAME ZONE FAILED · NAME TAKEN" and its Retry disappeared) | `clearWriteFailure()` ran with no condition after every landed delete | A write failure now carries its `subject` (`web/src/desk/hooks/useWriteReceipt.ts`, `WriteFailure.subject`, `reportWriteFailure(…, subject)`). A refused delete reports `qualifiedRef(kind, id)` (`web/src/desk/store/dataSlice.ts:581`). A landed delete clears only a standing `DELETE` failure for the same subject (`dataSlice.ts:589`) |
| 2. After a refusal, Workbench Remove stopped working (the next Remove sent zero requests) | the Workbench commit dropped `write()`'s promise, so the hook never saw the refusal and never freed the key. `write()` also answers `{ok:false}`, not `false` | One result contract: a commit answers nothing or `Promise<boolean>` (`web/src/desk/hooks/useUndoReceipt.ts`, `type Fire`). The Workbench returns `write(…).then((result) => result.ok)` for Remove and Clear done (`web/src/desk/components/WorkbenchWindow.tsx:1209`, `:1310`). The listener returns `deletePrimitive`'s boolean |
| 3. A re-created reference could not be deleted again | committed keys lived as long as the host | A key is held only for its window and its commit, and is freed when the commit settles, on success or refusal (`useUndoReceipt.ts:59`, `:62`, `:71`) |
| 4. "Removal committed" showed before the write settled (briefly beside a delayed 403 failure) | the hook set `committed` before it called `fire` | A new `committing` phase: while the commit is in flight the receipt keeps "Removed …" with no Undo and no countdown (`useUndoReceipt.ts:68`). "Removal committed" shows only after success. A refusal clears the undo receipt, so only the failure receipt speaks. No new words |
| MISSED 3. The error named only "HTTP 403" | `writeFailureReason` keeps only the status | The hub's own words go into the label's title, the existing idiom (`useWriteReceipt.ts:70` `writeFailureDetail`, `:103`). The visible label does not change. Example: title `DELETE FAILED · HTTP 403 · Delete refused by the glass` |

The fences go through the real hub, and the rendered transition is recorded with a MutationObserver from the press:
- `test_a_refused_delete_says_so_with_retry` (list and Floor, 1440 and 393, a 403 that answers 1 s late): "Removal committed" never appears between the press and the failure. The failure says `DELETE`, has Retry, and its title carries the hub's words. The object stays (200). Retry deletes it (404).
- `test_a_workbench_remove_works_again_after_a_refusal` (1440 and 393): after the refusal, the next Remove sends one DELETE and the item is gone. "Removal committed" never appears before the failure.
- `test_a_delete_keeps_an_unrelated_rename_failure` (1440 and 393): the rename failure and its Retry still stand after the delete lands (404).
- `test_a_recreated_object_can_be_deleted_again`: delete, re-create with the same id, refresh, then Delete. One DELETE is sent and the object 404s.

Red on `d3eab7e8`: all 9 cases failed, at a load average of 2.75 → 13.04 (`docs/internal/philo/phase-8/one-delete/red-round-four-d3eab7e8.log`):
- the refusal transition: `AssertionError: [… 'Removed Refuse me …', … 'Removal committed' …]` (`assert not True`), at all four face and width pairs;
- Workbench: `AssertionError: (0, [<the item>])`, zero DELETE requests after the refusal;
- the rename: `AssertionError: []`, no rename failure left standing;
- re-created: `AssertionError: (200, 0)`.

The transition on the fix (list 1440): `'Removed Refuse me Undo 08s' … '01s'`, then `'Removed Refuse me'` (in flight), then `'DELETE FAILED · HTTP 403 Retry OK | Removed Refuse me'` (one render while the hook clears), then `'DELETE FAILED · HTTP 403 Retry OK'`.

Unit fences (vitest):
- the hook: a key stays blocked while its commit is in flight and is free after it settles; "Removal committed" shows only after the commit lands; a refused commit goes pending → committing → idle;
- the listener: the mock `deletePrimitive` answers `true`.

## Round five (Codex Astra r3 on `a84d1a37`, BOUNCE, narrowing — `story-02-built-astra-r3.md`)

Astra r3 confirmed round four: all 13 of its r2 probes pass, every commit callback returns the boolean, B's success keeps A's failure, a double press sends one DELETE, and a re-created ref deletes again. It ruled the refusal overlap acceptable (135–430 ms, and it never says "Removal committed"). My round-four text said "one render"; it lasts 135–430 ms.

| Item | Cause | Repair (file:line) |
|---|---|---|
| P1. After a refusal, the Workbench's renewed Remove hid its Undo; the item was deleted when the window ended | the footer ranked `writeReceipt` over the pending undo receipt | A live Undo is never hidden: the footer shows the undo receipt first while it is pending or committing (`web/src/desk/components/WorkbenchWindow.tsx:1911`). A new Remove of the same item clears that item's old refusal (`:1205`). The refusal carries the item as its subject (`:1217`; `web/src/desk/hooks/useWriteReceipt.ts:157`, `attempt(…, { subject })`). A failure for another item stays |
| P2. The phone list's refusal was off-screen (y −1196…−1138); Retry could not be reached | the desk failure fallback renders above the scrolling work (`DeskReceiptRow`) | On the list, the desk write failure sits in the fixed foot, above the undo receipt, in the #665 seat (`web/src/desk/components/DeskListView.tsx:107`, `:395`). Mounting it there makes the bar's copy yield, so the failure shows once. It uses the foot's ground (`list-view.css`). No new element |
| MISSED 1. The Workbench fence waited out the renewed window without checking the receipt | — | The fence now requires the renewed Undo to be readable in the viewport before it waits |
| MISSED 2. A click proves nothing about the viewport (Playwright scrolls to the target) | — | `_readable_in_view` checks the viewport bounds and that the element's centre point lands on the element, BEFORE any click |
| MISSED 3. The resize fence had no time bound | — | The fence now records when the DELETE starts, relative to the resize, and requires less than 1 s |

Red on `a84d1a37` (serial, load 2.70 → 11.64; `docs/internal/philo/phase-8/one-delete/red-round-five-a84d1a37.log`):
- the phone list refusal: `.write-receipt is not readable in the viewport: [{'top': -1196, 'bottom': -1138, … 'inViewport': False, 'own': False}]`;
- Workbench, both fences at both widths: the renewed Undo never shows (`Page.wait_for_function: Timeout 5000ms exceeded.`);
- the resize time bound: it passes on `a84d1a37`, which already had the fix (69 ms on this branch). On `b65107f5` it fails: `AssertionError: (4146.1, '05s')`, the DELETE 4146 ms after the resize, which is the timer ending, not the face change.

Green: the refusal fence passes at list and Floor, 1440 and 393. The Workbench undo-after-refusal fence passes (Undo readable, the item kept, zero DELETE). Both story 01 glass files still pass (42 of 42 in the scoped run).

## Round six (Codex Astra r4 on `daedfc99`, BOUNCE on one defect — `story-02-built-astra-r4.md`)

Astra r4 confirmed round five: all nine r3 probes pass. It ruled the wider use of the list foot lawful and the Undo precedence acceptable.

| Item | Cause | Repair (file:line) |
|---|---|---|
| P2. In the Workbench, a successful removal of B erased A's unresolved failure and its Retry | the Workbench's local channel cleared its failure on any landed write; the `subject` was recorded but not used there | One rule in both channels: a failure about a subject is cleared only by a landed write about the same subject (`web/src/desk/hooks/useWriteReceipt.ts`, `attempt`'s success path). A failure with no subject still clears on any landed write, as before |
| MISSED 1. The unrelated-failure fence covered only the desk channel | — | New fence `test_a_workbench_success_keeps_another_items_refusal` (1440, 393): A refused; B removed and committed (the hub keeps A); after B's linger, A's failure and Retry still show, and Retry is readable in the viewport; Retry removes A. Vitest: `hooks/__tests__/useWriteReceiptSubject.test.ts` |
| The resize console error `Cannot read properties of null (reading 'x')` | CLASSIFIED, see below | `web/src/desk/gl/engine.ts:423`, `:571`, `:678`: a late sprite texture is not set on a destroyed sprite |
| MISSED 2. The inherited rename duplicate (chip and old receipt together after F2) | inherited from story 01's rename path | LEDGERED, not fixed: BACKLOG "PHILO-8-02 follow-ups", home the Floor lane |

**The console error, classified.** I captured the stack on Astra's own `daedfc99` build: 2 page errors in 40 runs of the resize fence at `-n 4`.
```
TypeError: Cannot read properties of null (reading 'x')
    at Tt._setWidth (…/WorldStage-BDUnZ0VN.js:5:41608)     (pixi Sprite)
    at set texture (…/WorldStage-BDUnZ0VN.js:5:61118)      (pixi Sprite)
    at …/WorldStage-BDUnZ0VN.js:295:6775                    (engine: loadSprite's onReady, `t.spriteUrl===o&&(t.sprite.texture=d)`)
    at …/WorldStage-BDUnZ0VN.js:295:1263                    (textures.ts loadSprite: Assets.load(...).then(... onReady))
```
- **Cause:** a world sprite loads late, on the first paint. When it arrives, its node may already be gone and pixi throws on the destroyed sprite. In this fence the resize commits the pending delete during the spatial world's first paint, and the refresh then removes that object's node before its PNG has loaded.
- **Inherited code:** `engine.ts` and `textures.ts` have not changed since `aa35cdb3`, on main and on this branch. So the defect is inherited.
- **Trigger:** this story's face-change commit is what fires it.
- **Main:** not reproduced. A resize-only probe on main `ce772ef9` (393 list to 1440, no delete, because main has no list delete) gave 0 errors in 30 runs.
- **Fix:** it sits on this story's path, so it is fixed here. The guard `!node.sprite.destroyed` covers all three late-texture callbacks.
- **Verification:** the same guards, patched into Astra's reproducing bundle, gave 0 errors in 80 runs (load about 30, with 41 timing failures, so fewer than 80 reached the face change) and 0 in a further 40 runs (1 timing failure). Unpatched, it was 2 in 40.
- **Caveat:** my own build never reproduced it (0 in 70), so the fix can only be shown against Astra's build. The record is `docs/internal/philo/phase-8/one-delete/resize-console-error.txt`.

Red on `daedfc99` (Astra's build; its only change is the engine guard, which does not touch this path; `red-round-six-daedfc99.log`): `workbench two items 1440: standing []` / `AssertionError: []` at both widths.

## Round seven (Codex Astra r5 on `ba55892e`, BOUNCE: the same class of defect, one more caller — `story-02-built-astra-r5.md`)

Astra r5 confirmed round six: the Workbench repair holds at both widths, a zone rename keeps the delete failure, and the sprite guards are sound (0 page errors in 40 runs). The new finding: New Zone (POST 201) erased an unrelated Delete failure and its Retry, with A still 200 on the hub, at both widths. The cause: `createPrimitive` called the desk channel's unconditional `clearWriteFailure()`, and so did `updatePrimitive`.

**Correction of my round-six claim.** Round six said "one rule in both channels". That was stronger than the code: only the delete path followed the rule in the desk channel. As of round seven it is true by construction, as follows.

**The repair closes the class.** The desk channel's `clearWriteFailure(subject?)` now follows the subject rule itself (`web/src/desk/hooks/useWriteReceipt.ts`):
- a standing failure about a subject is removed only by a clear with that same subject;
- a standing failure with no subject is removed by any clear.

The owner's explicit dismissal (OK) is the new `dismissWriteFailure()`, used by the receipt's OK button and the hook's `clear`. The Workbench's local channel has had the same rule since round six (`useWriteReceipt.ts`, `attempt`'s success path).

Subjects are passed where the caller has one:
- `updatePrimitive`: its refusal and its clear both carry `kind:id`;
- `deletePrimitive`: `kind:id`;
- `renameZone`: its refusal and a new success-path clear both carry `directory:id`.

**Every call site of `clearWriteFailure` / `dismissWriteFailure`**, all now covered by construction:

| Call site | What it answers |
|---|---|
| `web/src/desk/callLoopWiring.ts:40` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/newThought.ts:32` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:718` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:936` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:974` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:982` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:1591` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:1871` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:1926` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/ChairHome.tsx:1981` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/chair/_parked/lanes/BriefLane.tsx:112` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/store/dataSlice.ts:251` | a READ failure healed by a clean refresh (READ failures carry no subject) |
| `web/src/desk/store/dataSlice.ts:382` | `createPrimitive` landed (New Zone, New Note…): a new object has no earlier failure, so no subject; it clears only a subject-less failure (a CREATE refusal) |
| `web/src/desk/store/dataSlice.ts:550` | `updatePrimitive` landed: subject `kind:id`; its refusal now carries the same subject |
| `web/src/desk/store/dataSlice.ts:591` | `deletePrimitive` landed: subject `kind:id` (replaces the round-four inline check) |
| `web/src/desk/store/dataSlice.ts:658` | `renameZone` landed: subject `directory:id`; its refusal now carries it (the success path cleared nothing before) |
| `web/src/desk/store/dataSlice.ts:860` | SEED DESK landed (subject-less) |
| `web/src/desk/store/recordingSlice.ts:55` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/store/recordingSlice.ts:68` | a subject-less write landed (Chair capture/meeting posts, the call loop, a new thought, a recording); it clears only a subject-less failure |
| `web/src/desk/hooks/useWriteReceipt.ts` (`useDeskWriteReceipt`: `clear`, the receipt's OK) | `dismissWriteFailure()`: the owner's own dismissal, which removes any failure |

**Fences** (glass, 1440 and 393; the same parameterised fence covers both writes):
- `test_a_create_keeps_an_unrelated_delete_failure`: A's delete is refused, then New Zone lands (POST 201). A's failure stays, its Retry is readable in the viewport, and Retry deletes A (404).
- `test_an_update_keeps_an_unrelated_delete_failure`: the same, with an update in place of New Zone. The update edits a note's body in its editor, which goes through the debounced save to `updatePrimitive`.

All the earlier fences still pass. Channel-level vitest (`hooks/__tests__/useWriteReceiptSubject.test.ts`):
- a clear with no subject does not remove a failure about a subject;
- a clear with another subject does not remove it either;
- a clear with the matching subject does;
- a failure with no subject is removed by any clear;
- the owner's dismissal removes any failure.

Red on `ba55892e` (serial, load average 2.17 → 11.04; `docs/internal/philo/phase-8/one-delete/red-round-seven-ba55892e.log`):
- create: `create 1440: A 200; standing []` / `AssertionError: A's failure was erased`, at both widths;
- update: `update 1440: A 200; standing []` / `AssertionError: A's failure was erased`, at both widths. The first attempt at this fence used Get Info, which the list does not mount; the fence now uses the note's editor.
