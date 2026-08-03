# HS-115-03 - Object windows

- **Project:** holdspeak
- **Phase:** 115
- **Status:** backlog
- **Depends on:** HS-115-01
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

Pullout, ZoneWindow, InfoWindow, and InlineEditor all pass the audit
checklist — layout fills the container, material uses the shared
tokens, bespoke controls are replaced with shared chips, and overflow
is scrollable, not clipped. When this ships, opening any object on
the desk feels like opening a file in a real OS — not a web page in
a window.

**Articles served:** I (the Desk is the front door), VII (quiet
chrome, in-world editing), VIII (native-grade craft).

## Ground (from the audit)

| Rule | File | Violation |
|------|------|-----------|
| L3 | desk.css:730 | InlineEditor lacks viewport-bounded height/scrolling |
| L2 | desk.css:5030 | Zone icon labels forcibly ellipsized |
| M3 | InlineEditor.tsx:498 | More control is bespoke, not shared chip |
| C2 | Pullout.tsx:250 | Unavailable-capability fallback is prose, not state label |
| C3 | desk.css:5246 | InfoWindow identity labels use wrong typography |

## Deliverables

1. **InlineEditor height bound.** Add `max-height: calc(100dvh - 120px)`
   and `overflow-y: auto` to the inline editor wrapper so expanded
   editors don't escape the viewport.

2. **Zone icon labels.** Replace forced ellipsis with `word-break:
   break-word` or allow two lines with line-clamp.

3. **InlineEditor More → chip.** Replace `desk-inline-editor-more` with
   `desk-chip quiet`.

4. **Pullout capability fallback.** Replace the three-sentence
   explanation with a terse state label: "No model configured" or
   "Needs a running LLM".

5. **InfoWindow typography.** Identity field labels use
   `--font-mono` and `--desk-surface-label-size`.

## Test plan

- `npx vitest run` — all frontend tests pass.
- Open a note in world view → expand the editor body to 20+ lines →
  editor must stay within viewport and scroll.
- Open a zone window → long object names must wrap or show two lines.
- Open an agent with no model → fallback must be a single state label.
