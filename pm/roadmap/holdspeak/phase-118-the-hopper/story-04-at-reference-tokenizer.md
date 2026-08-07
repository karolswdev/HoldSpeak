# HS-118-04 — @-reference tokenizer

- **Project:** holdspeak
- **Phase:** 118
- **Status:** done
- **Depends on:** HS-118-01, HS-118-02, HS-118-03
- **Unblocks:** HS-118-05
- **Owner:** unassigned

## The thesis (the bar)

There is no way to name a desk object inline in text anywhere in
HoldSpeak. Grounding is attached through a selector panel — a
separate interaction from writing the instruction. The user thinks
"summarize the Monday standup and compare with last week's retro" but
must express it as three separate gestures: type text, open grounding
panel, check two meetings.

The `@`-reference tokenizer lets the user name desk objects inline.
When the user types `@` in the inlet, an autocomplete popover shows
matching zone names (case-insensitive prefix search). Selecting a
match adds the zone's qualified ref to the grounding tray as a chip
and removes the `@query` span from the input. The instruction reads
naturally; the grounding is attached by naming, not by browsing.

Zone names are the only resolution target. Zones are the
organizational primitive — if something matters, it lives in a zone.
Naming the zone is naming the work.

**Articles served:** II (DeskPrimitive contract — zones are
addresses), VI (honest by construction — exact name match, no
guessing), VII (no prose — inline reference, not a panel).

## The resolver function

A pure, shared function used by both the typed (@) and voice paths:

```typescript
// web/src/lib/drawerResolver.ts

interface ResolvedRef {
  name: string;      // matched zone name (display form)
  id: string;        // zone id (dir_...)
  ref: string;       // qualified ref (zone:dir_...)
  kind: string;      // primitive kind ("zone" for now)
}

function resolveDrawerName(
  query: string,
  zones: Directory[]
): ResolvedRef | null;

function resolveDrawerNames(
  text: string,
  zones: Directory[]
): { refs: ResolvedRef[]; cleanText: string };
```

### `resolveDrawerName(query, zones)`

Case-insensitive exact match of `query` against zone
`nameNormalized` values (fetched from the API, computed by Python
— HS-118-01). The resolver never recomputes normalization in
JavaScript; it compares the query's lowercased form against the
stored normalized values. Returns the first match or null. Since
zone names are globally unique (HS-118-01), there is at most one
match.

### `resolveDrawerNames(text, zones)`

Scans `text` for zone names as complete phrases. Matching rules:

1. **Word-boundary matching.** A zone name matches only when
   bounded by: start/end of string, whitespace, or punctuation
   (`.,;:!?'"()-`). The boundary predicate is explicit — do NOT
   use regex `\b`, which has inconsistent Unicode behavior across
   engines. Instead, check the character immediately before and
   after the candidate span against the boundary set.

   Examples:
   - Zone "Plan": "planning session" → NO (letters on both sides).
   - Zone "Plan": "the Plan works" → YES (space before, space after).
   - Zone "Now": "do this now" → YES (space before, end of string).
   - Zone "Now": "do this now!" → YES (space before, `!` after).
   - Zone "Research": "Research-notes" → YES (start of string, `-`
     is a boundary character).

   Zone names containing regex-special characters are matched
   literally (escape them if building a regex, or use indexOf +
   boundary check).

2. **Longest-match-first.** Sort zone names by length DESC before
   scanning. A zone named "Monday standup notes" matches before
   "Monday standup" matches before "Monday." Each match consumes the
   span — subsequent shorter matches cannot overlap consumed spans.

3. **Case-insensitive.** Comparison uses the stored
   `nameNormalized` values from the API (computed by Python
   per HS-118-01). The resolver lowercases the text for comparison
   but never recomputes Python's `casefold()` in JavaScript.

4. **Deduplication.** If the same zone name appears twice in the
   text, it produces one ref (not two).

5. **`cleanText`.** The text with matched zone names removed and
   excess whitespace collapsed. This is a diagnostic/internal value.
   The voice path (HS-118-05) does NOT use `cleanText` for display
   — it preserves the full original transcript. `cleanText` is
   retained in the function signature for potential future use
   (e.g. structured logging) but is not consumed by any UI path.

## Deliverables

1. **The resolver module** (`web/src/lib/drawerResolver.ts`).
   Pure functions, no side effects, no React dependencies. Fully
   unit-testable.

2. **The autocomplete popover.** A new component rendered inside the
   inlet:

   ```
   InletAutocomplete
   ├── popover (anchored to the inlet container, not cursor position)
   │   └── SurfaceRow[]  one per matching zone
   │       ├── glyph: zone icon
   │       ├── title: zone name
   │       └── detail: member count ("3 items")
   ```

   The popover anchors to the bottom edge of the inlet (above it),
   not to the cursor position in the text input. Cursor-relative
   anchoring in a plain `<input>` requires measurement hacks that
   are fragile across browsers. Inlet-relative anchoring is reliable
   and visually consistent.

3. **Autocomplete behavior.**
   - Triggered when the user types `@` in the inlet text field,
     only if `@` is preceded by a boundary character (start of
     input, space, or punctuation). An `@` inside a word (e.g.
     email addresses) does not trigger the popover.
   - The active query is: text between the triggering `@` and the
     cursor.
   - Filters zones by case-insensitive prefix of the query.
   - Shows up to 8 matches, sorted alphabetically.
   - Arrow keys navigate, Enter selects, Escape dismisses.
   - On select: the `@query` span is removed from the input, the
     zone's qualified ref is added to the grounding tray as a chip,
     cursor returns to the position after the removed span.
   - If only one match remains after filtering, Enter selects it.
   - If no matches, the popover shows "No zones match" in
     `--text-faint`.
   - Backspacing past the `@` closes the popover.
   - Space with no matches closes the popover and keeps text as
     literal.

4. **Zone list source.** The autocomplete reads zones from
   `useDesk.getState().items.directory` — already loaded by
   `loadAll()`. No new API needed.

5. **Interaction with grounding tray.** On select:
   - The chip appears in the tray (same `desk-chip` as drops).
   - Duplicate prevention: if the zone is already in the tray, the
     `@query` text is still removed but no second chip is added.
   - Removing a chip from the tray does NOT restore the `@query`
     text in the input — the chip is the reference, the text is the
     instruction. They're separate concerns.

6. **Paste handling.** Pasting text containing `@` does not trigger
   the autocomplete. The autocomplete only activates on keystroke-by-
   keystroke `@` entry. Pasted `@name` text stays as literal text.

7. **CSS treatment.**

   ```css
   .inlet-autocomplete {
     position: absolute;
     bottom: 100%;
     left: 0;
     right: 0;
     z-index: var(--z-popover, 200);
     background: var(--surface-2);
     border: 1px solid var(--border);
     border-radius: 6px;
     box-shadow: var(--desk-window-bevel);
     max-height: 240px;
     overflow-y: auto;
   }
   .inlet-autocomplete [data-selected] {
     background: var(--accent-tint);
   }
   ```

## Keyboard interaction matrix

| State | Key | Action |
|-------|-----|--------|
| Popover closed | `@` | Open popover, start filtering |
| Popover open | Any char | Filter by prefix after `@` |
| Popover open | `↑` / `↓` | Navigate matches |
| Popover open | `Enter` | Select highlighted match |
| Popover open | `Escape` | Close popover, keep `@` text |
| Popover open | `Backspace` past `@` | Close popover |
| Popover open | ` ` with no matches | Close popover, keep text |
| Popover open | `Tab` | Select highlighted match (same as Enter) |

When the popover is open, Enter selects a match and does NOT submit
the inlet. Enter only submits when the popover is closed.

## What NOT to do

- Do NOT resolve anything other than zone names. No meetings, no
  artifacts, no recipes. Zones are the address layer.
- Do NOT add fuzzy matching, Levenshtein distance, or "did you mean?"
  suggestions. Exact prefix match for autocomplete, exact phrase
  match for the resolver.
- Do NOT use contentEditable or render inline chips in the text
  field. The input stays a plain `<input type="text">`. The visual
  confirmation lives in the grounding tray, not in the field.

## Test plan

- `npx tsc --noEmit` — zero type errors.
- `npx vitest run` — new tests for the resolver:
  - `resolveDrawerName("Research", zones)` → exact match.
  - `resolveDrawerName("research", zones)` → case-insensitive match.
  - `resolveDrawerName("nonexistent", zones)` → null.
  - `resolveDrawerNames("summarize Research and Planning", zones)`
    → two refs resolved, cleanText = "summarize and".
  - Longest-match-first: zones "Mon" and "Monday standup" both exist,
    text "Monday standup" → resolves "Monday standup", not "Mon."
  - Word-boundary: zone "Plan", text "planning session" → no match
    (no boundary after "Plan" — next char is "n").
  - Word-boundary: zone "Now", text "do this now" → matches (space
    before, end of string after).
  - Word-boundary: zone "Now", text "I don't know" → no match (no
    boundary-delimited "Now" substring).
  - Dedup: zone "Research" appears twice in text → one ref, both
    occurrences removed from cleanText.
  - Unicode: zone "Café notes", text "café notes" → matches.
- New tests for autocomplete:
  - Type `@Res` → popover shows "Research" zone.
  - Select → chip in tray, `@Res` removed from input.
  - Escape → popover closes, `@Res` stays as literal.
  - Duplicate select → no second chip, text still removed.
  - Paste `@Research` → no popover triggered.
  - Enter with popover open → selects, does not submit inlet.
- Visual at 1440: popover anchored above inlet, surface-2 background,
  bevel shadow, rows highlight on arrow-key navigation.
- Visual at 393: popover fills available width, doesn't overflow
  viewport.
