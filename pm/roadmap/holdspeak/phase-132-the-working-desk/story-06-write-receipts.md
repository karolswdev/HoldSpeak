# HS-132-06 — Desk writes report their failures

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-132-07
- **Owner:** unassigned

## Problem

The dominant defect class on the web desk is the silent write. Verified bare
catch blocks or unchecked responses: WorkbenchWindow `addItem`
(`WorkbenchWindow.tsx:1153-1155`), `handleDrop` (:1294-1296),
`updateItem`/rerun/dismiss (:536-540), `handleKeep` (:546-555),
`handleRetryMint` (:561-568), voice add-item/dismiss (:1189-1192,
:1256-1263); `dataSlice.createPrimitive` never checks `res.ok`
(`web/src/desk/store/dataSlice.ts:174-183`); `seedDesk`'s failure return is
discarded (`EmptyDesk.tsx:44-54`). `lib/api.ts` has no global receipt
channel. When the hub is unreachable or rejects a payload, Create, Hopper GO,
drop-to-work, Keep, Retry mint, Dismiss, Re-run, and Seed all appear to do
nothing — indistinguishable from a no-op, no retry affordance. This violates
the standing refusals-name-why rule and Article V.2 at the UI layer.

## Scope

### In

- One shared write-receipt channel (extend the existing
  `useUndoReceipt`/`useCopyReceipt` pattern) that any desk write verb reports
  into: named failure, in-flow placement (receipt bar/turn — never
  overlapping UI, per standing rule), retry affordance where re-issuable.
- Wire the ~13 verified silent sites through it; `createPrimitive` and
  `seedDesk` surface their failures.
- A lint-style guard (test or eslint rule) against bare `catch {}` around
  `apiFetch`/`apiRequest` writes in `web/src/desk`.

### Out

- Optimistic-update/undo redesign; backend error-shape changes.

## Acceptance criteria

- [ ] With the hub down, every listed verb shows a named failure receipt with
  retry where applicable; nothing silently no-ops.
- [ ] Successful writes are unchanged (no new chrome on success beyond
  existing patterns).
- [ ] The guard fails on a newly added swallowed write.

## Test plan

- vitest: per-verb failure surfacing with a mocked failing fetch; the guard
  test.
- `cd web && npx vitest run --reporter=dot` (full web suite stays green).
