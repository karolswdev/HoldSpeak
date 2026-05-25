# HS-17-12 — Bookmark Count in Recording-Tick Payload

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-17-05 (Recording-tick infrastructure); HS-17-06 (alternation pattern for tick payload)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

During a meeting, bookmarks are fire-and-forget: HoldSpeak adds them on `long_press` event, the device sees a brief `Bookmark @ Xs` flash, the LCD reverts to the next Recording tick. The user has no running count of how many bookmarks they've placed — easy to lose track of in a long meeting.

User feedback 2026-05-10 (paraphrased after the LVGL polish session): "I wish I could see how many bookmarks I've made without stopping the meeting and opening the web UI."

## Scope

### In

- Extend HS-17-05's Recording-tick payload generator: when the meeting has ≥ 1 bookmark, the tick rotates between:
  - `Recording MM:SS` (5s)
  - `<n> bookmarks` (5s) — where `<n>` is the current count.
  - …repeating.
- If 0 bookmarks: skip the alternation; just emit `Recording MM:SS` (HS-17-05 baseline).
- Combines naturally with HS-17-06's title alternation: with all three (title, bookmarks, recording-tick), the rotation is `Recording MM:SS` → `<title>` → `<n> bookmarks` → repeat.
- Truncation at 30 chars (rarely needed since the count strings are short).
- Symbol: `LV_SYMBOL_BELL` (already mapped for Bookmark) when the leading word matches.
- Integration test: bookmark-count alternation appears when bookmarks ≥ 1; doesn't appear when 0.

### Out

- Bookmark *removal* during a meeting (not currently a HoldSpeak feature; would need its own story).
- Last-bookmark text in the tick (HS-17-06 covers title; segment text is HS-17-08; bookmark count is just the count).
- Color-coded counts (LCD is monochrome).
- Per-bookmark navigation from the device — out of scope.

## Acceptance Criteria

- [ ] HS-17-05's Recording-tick payload generator checks `len(meeting.bookmarks)`; if > 0, alternates with `<n> bookmarks` (or `1 bookmark` singular).
- [ ] Combines with HS-17-06's title alternation cleanly (if both are configured): cycle is `Recording` → `<title>` → `<n> bookmarks` → repeat.
- [ ] Bridge-side `_ACTIVITY_SYMBOLS` picker matches "bookmarks" (plural) the same way it matches "Bookmark" (singular).
- [ ] Integration test asserts the alternation behavior with bookmarks ≥ 1 and = 0.
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification: meeting with bookmarks added mid-recording; LCD tick alternates correctly.

## Test Plan

- **Unit:** payload generator with N bookmarks (parametrized over 0/1/2/10).
- **Integration:** simulated meeting with 3 bookmarks added during a 30s window; recording-tick alternation observed.
- **Manual:** real meeting on AIPI-Lite; add bookmarks; watch LCD.

## Notes

- **Singular vs. plural:** `1 bookmark` not `1 bookmarks`. Tiny but visible UX detail. Story should bake this in via a simple `f"{n} bookmark{'s' if n != 1 else ''}"` formatter.
- **Combines cleanly with HS-17-06.** Both stories extend HS-17-05's payload generator; this one + HS-17-06 should land together OR be carefully ordered so the alternation logic stays clean (probably a small `TickPayloadGenerator` class that owns the rotation pattern).
- **Symbol picker note:** HS-17-09 will also extend the picker (for "Action: ..." strings). All three stories add new symbol-map entries; consider consolidating them into a single picker-extension PR if they land close together.
- **Future-proofing:** if MIR-01 starts surfacing action-item count too, the same alternation could include `<n> actions`. Generalize the payload generator to "metrics slot" that can host any per-meeting counter.
