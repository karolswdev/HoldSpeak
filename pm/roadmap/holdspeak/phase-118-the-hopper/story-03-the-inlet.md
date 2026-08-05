# HS-118-03 — The inlet

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** --
- **Unblocks:** HS-118-04, HS-118-05
- **Owner:** unassigned

## The thesis (the bar)

The current workbench composer is a form: title input, optional body
fold, priority cycle chip, grounding selector panel. Four separate
controls for what should be one gesture. The user's instruction IS
the item — there is no meaningful distinction between "title" and
"body" when the instruction is "summarize @Monday standup for the
team."

The inlet replaces the composer with a single unified input surface.
One text field. One mic (inherited — every text input can be spoken
into, Article IV). One grounding tray that fills from drops,
@-references, or voice. One submit gesture. The inlet is the
hopper's mouth — always visible, always inviting, zero ceremony.

When this ships, the old composer is gone. The inlet is pinned to the
bottom of the items wing. Dropping a desk object onto the inlet
(or anywhere on the workbench body) adds grounding chips to the tray.
The user types or speaks intent into the field. Enter or the GO
transport key submits. One gesture: intent + grounding → item.

**Articles served:** IV (every text input can be spoken into — the
inlet inherits the mic; visible single-mic authority), V (consent —
item creation is a filing action; the user's explicit Enter/GO
gesture is the approval), VII (no prose, no chrome — the inlet is
minimal furniture), VIII (native-grade craft — the inlet must feel
immediate and physical).

**UI/UX direction:** Study the existing AskPanel composer and the
WorkbenchWindow composer. The inlet takes the AskPanel's single-field
simplicity and the WorkbenchWindow's drop-to-work contract. The
grounding tray borrows the `desk-chip` vocabulary already used
everywhere on the desk.

## Deliverables

1. **The inlet component.** Replaces the existing `wb-composer` div
   in `WorkbenchWindow.tsx`. Structure:

   ```
   wb-inlet                        pinned to bottom, border-top
   ├── wb-inlet-tray               grounding chips, horizontal scroll
   │   └── desk-chip[]             one per grounding ref, × to remove
   ├── wb-inlet-row                flex row
   │   ├── MicButton               system primitive, scoped voice
   │   ├── input[type=text]        mono, "What needs doing?", flex:1
   │   └── TransportKey "GO"       disabled when field empty
   ```

   No title/body split. The text field content becomes
   `WorkbenchItem.body` — the full instruction. The `title` field on
   the item is derived: first 64 characters of the body, truncated at
   a word boundary.

2. **Drop-to-inlet.** The existing `onDrop` handler on `.wb-body`
   changes behavior. Instead of creating items directly from dropped
   objects, drops now populate the grounding tray with chips. Each
   dropped desk object (`application/x-desk-item` transfer data)
   becomes:
   - A `desk-chip` in the tray showing the object's title (truncated
     to 24 chars) with an `×` to remove.
   - A qualified ref in the pending grounding state:
     `meeting:id` for meetings, `zone:id` for directories,
     `artifact:id` for artifacts/notes.
   - Multiple drops accumulate — each adds to the tray.

   After the drop, the text input auto-focuses. The user sees their
   grounding chips and can immediately type or speak intent.

3. **Explicit priority.** Priority defaults to P3. A compact chip
   next to the GO button shows the current priority. Clicking cycles
   through P1 → P2 → P3 → P1. No inference, no keyword detection.
   The user sets it if they care; most items stay P3.

   Priority colors: P1 = `--danger-signal`, P2 = `--warn-signal`,
   P3 = `--text-faint` (visually quiet, doesn't compete for
   attention).

4. **Submit flow.** Enter or GO transport key:
   - Trim the text field. If empty, no-op.
   - Extract `title` (first 64 chars at word boundary) and `body`
     (full text).
   - Build grounding from the tray: `{ refs: ["zone:dir_x", ...],
     meeting_ids: [...], artifact_ids: [...] }`. Meeting and artifact
     IDs are extracted from their qualified refs for backward
     compatibility with the existing conductor hydration path.
   - Read priority from the cycle state.
   - Call `addWorkbenchItem(workbenchId, payload)`.
   - Clear the text field, grounding tray, and reset priority to P3
     on success.

5. **Grounding tray state.** The tray is the source of truth for
   pending grounding. It's a local React state: `ResolvedRef[]`.
   The `ResolvedRef` interface (defined in HS-118-04's
   `drawerResolver.ts`) is: `{name, id, ref, kind}` — where `kind`
   is the primitive kind (always `"zone"` for now). Deduplication:
   refs with the same qualified ref string are rejected (no duplicate
   chips). Removing a chip removes the ref. The tray collapses
   (display:none) when empty.

6. **CSS treatment.**

   ```css
   .wb-inlet {
     border-top: 1px solid var(--border-subtle);
     background: var(--surface-2);
     padding: var(--desk-window-pad-x);
     flex-shrink: 0;
   }
   .wb-inlet-tray {
     display: flex;
     gap: 4px;
     overflow-x: auto;
     padding-bottom: 6px;
   }
   .wb-inlet-tray:empty { display: none; }
   .wb-inlet-row {
     display: flex;
     gap: 6px;
     align-items: center;
   }
   .wb-inlet input {
     flex: 1;
     font: var(--desk-surface-body-size) var(--font-mono);
     background: transparent;
     border: none;
     color: var(--text);
     outline: none;
   }
   ```

   Drop hover: the inlet gets `var(--accent-tint)` background and
   `var(--accent)` border, matching the existing drop-zone pattern.

## What NOT to do

- Do NOT keep the old composer alongside the inlet. The inlet
  replaces it completely. No toggle, no "classic mode."
- Do NOT add a separate body field or fold. The instruction is one
  continuous text.
- Do NOT add an explicit grounding selector panel (the old
  GroundingSection with checkboxes). Grounding arrives through drops,
  @-references (HS-118-04), or voice (HS-118-05). No panel.
- Do NOT infer priority from instruction text. That would be a
  hidden classification — a guess by another name. (Article VI.)

## Test plan

- `npx tsc --noEmit` — zero type errors.
- `npx vitest run` — new tests:
  - Inlet renders with input, mic, and GO transport.
  - Drop on inlet adds grounding chip; chip × removes it.
  - Duplicate drop (same ref) is rejected — no second chip.
  - Submit creates item with body as instruction, derived title,
    grounding refs, and explicit priority.
  - Empty submit is no-op.
  - Priority cycle: click cycles P3 → P1 → P2 → P3.
  - After submit: field, tray, and priority all reset.
- `uv run pytest -q` — backend tests unaffected (no backend changes).
- Visual at 1440: inlet pinned to bottom, grounding chips scroll
  horizontally, drop hover shows accent treatment, GO disabled when
  empty, priority chip visible.
- Visual at 393: inlet fills width, chips scroll, mic and GO
  remain accessible.
