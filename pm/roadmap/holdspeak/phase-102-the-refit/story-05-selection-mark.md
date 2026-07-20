# HS-102-05 — The selection mark yields to open

- **Project:** holdspeak
- **Phase:** 102
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "Single click 'marking' things, good, but upon double-click, the
> 'mark' should go away."

## Problem

Round 9's click grammar (single = select, double = open) was
approved in substance, with one exact correction: opening an object
currently leaves its selection ring and the "1 selected · Ask AI"
bar standing behind the opened card. The owner's grammar: the open
CONSUMES the mark — double-click opens the card and the mark (ring +
selection bar) clears.

## Scope

- In: the engine tap arm (`web/src/desk/gl/engine.ts`, the
  double-tap open branch) and the touch tap-open branch: opening an
  object clears the selection (without disturbing an open Ask
  composer's held rope — the HSM-16-04 rule stays). The context
  menu's Open and the a11y layer's activation follow the same
  grammar. The smoke walk leg's grammar assertions grow to pin it:
  after double-click, card open AND no ask bar.
- Out: modifier-click toggle, lasso, background-tap clear (all
  shipped and correct); multi-select semantics.

## Acceptance criteria

- [ ] Double-click (mouse) opens the card AND clears the mark: no
      selection ring, no selection bar, while the ask composer's
      held selection (askOpen) is never stripped mid-compose.
- [ ] Touch tap-open and menu-Open follow the same rule.
- [ ] The smoke leg pins it (select → bar present; open → card
      present, bar gone).
- [ ] Driven headed on the staged hub, both viewports; screenshots
      read.

## Test plan

- The smoke walk leg (grown assertions); web vitest for any store
  change; the headed hand-drive.

## Evidence required

- The before/after drive record; the grown smoke-leg output.
