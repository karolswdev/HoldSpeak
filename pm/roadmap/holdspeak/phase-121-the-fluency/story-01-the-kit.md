# HS-121-01 — The kit

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-121-02 (one footer), all subsequent stories
- **Owner:** unassigned

## The thesis (the bar)

The usability audit found five patterns reinvented per-surface across
the entire desk. This story builds them once in the kit so every
subsequent story — and every future surface — composes from primitives.

When this ships, five new kit primitives exist with tests, no consumers
yet (adoption is stories 02-11):

### 1. SurfaceState action slot

`SurfaceState` gains optional `onAction: () => void` and
`actionLabel: string` props. When both are provided, a `desk-chip`
button renders below the empty label. This is the structural fix for
12+ dead-end empty states.

```tsx
<SurfaceState empty emptyLabel="No items yet" emptyGlyph="○"
  actionLabel="Add an item" onAction={() => addItem()} />
```

File: `web/src/desk/surface/Surface.tsx`

### 2. SurfaceFooter

A shared footer component with three fixed slots: `egress | receipt |
verbs`. Replaces 8 footer species with one. Renders as
`<footer className="desk-surface-footer">` with CSS grid or flex
layout.

```tsx
<SurfaceFooter
  egress={<EgressChip ... />}
  receipt={undoReceipt}    // from useUndoReceipt
  verbs={<>
    <button className="desk-chip" onClick={copy}>Copy</button>
    <button className="desk-chip" onClick={edit}>Edit</button>
  </>}
/>
```

The receipt slot renders transient tokens (undo countdowns, "Copied"
confirmations, "Saved" lamps) that appear and fade. The verbs slot
renders persistent action buttons.

File: new `web/src/desk/surface/SurfaceFooter.tsx` + CSS

### 3. LedgerFilter

A composable filter bar: `StringGadget` + `MicButton` + live-apply +
Enter-opens-top-hit + filter persistence via localStorage keyed by
surface name.

```tsx
const { query, setQuery, filtered } = useLedgerFilter(items, {
  key: "meetings",        // localStorage persistence key
  match: (item, q) => item.name.includes(q),
});
```

When `query` is non-empty, a removable filter token renders. Closing
and reopening the surface restores the last query.

File: new `web/src/desk/surface/LedgerFilter.tsx` (or hook)

### 4. useCopyReceipt

A hook that copies text to clipboard and returns a transient receipt
element for the nearest `SurfaceFooter` receipt slot.

```tsx
const { copy, receipt } = useCopyReceipt();
// In a verb: onClick={() => copy(text)}
// In footer: <SurfaceFooter receipt={receipt} ... />
// receipt is null normally, "Copied" LampGadget for 2s after copy
```

File: new `web/src/desk/hooks/useCopyReceipt.ts`

### 5. useUndoReceipt

A hook that defers a destructive action for a window (default 8s)
and returns a receipt element with an UNDO button and countdown.

```tsx
const { remove, receipt } = useUndoReceipt();
// In a verb: onClick={() => remove("Removed item", () => deleteItem(id), () => restoreItem(id))}
// In footer: <SurfaceFooter receipt={receipt} ... />
// receipt shows "Removed item · UNDO · 7s" with countdown
```

On UNDO click: calls the revert function, clears the receipt.
On expiry: calls the fire function, clears the receipt.

File: new `web/src/desk/hooks/useUndoReceipt.ts`

## Acceptance criteria

- [ ] `SurfaceState` renders an action button when `onAction` +
      `actionLabel` are provided. Does not render when absent
      (backward compatible).
- [ ] `SurfaceFooter` renders three slots with correct layout.
      Empty slots collapse gracefully.
- [ ] `LedgerFilter` persists query to localStorage. Restores on
      mount. Clears on explicit clear.
- [ ] `useCopyReceipt` writes to clipboard and returns a transient
      receipt that auto-clears after 2 seconds.
- [ ] `useUndoReceipt` defers the action, shows countdown, fires
      on expiry, reverts on UNDO click.
- [ ] All five primitives have unit tests.
- [ ] All five use desk token CSS — no inline styles, no hardcoded
      colors.
- [ ] Typecheck passes.

## Test plan

- Unit: SurfaceState renders action button, doesn't render without
  props.
- Unit: SurfaceFooter renders each slot, collapses empty slots.
- Unit: LedgerFilter persists/restores from localStorage mock.
- Unit: useCopyReceipt calls navigator.clipboard.writeText and
  returns receipt.
- Unit: useUndoReceipt fires after timeout, reverts on click,
  clears receipt.

## Files in scope

- `web/src/desk/surface/Surface.tsx` (SurfaceState modification)
- New: `web/src/desk/surface/SurfaceFooter.tsx`
- New: `web/src/desk/surface/SurfaceFooter.css`
- New: `web/src/desk/surface/LedgerFilter.tsx`
- New: `web/src/desk/hooks/useCopyReceipt.ts`
- New: `web/src/desk/hooks/useUndoReceipt.ts`
- Test files for each
