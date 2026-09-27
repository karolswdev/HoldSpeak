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
