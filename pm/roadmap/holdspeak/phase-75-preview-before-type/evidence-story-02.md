# Evidence — HS-75-02 — Type it / Discard on the cockpit and the desk

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-75-preview-before-type`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **One shell surface instead of two page-specific ones**:
  `PreviewCard.astro` + `preview-card.js` (the QueueHud idiom — markup in
  the component, behavior in a bus-fed script, `is:global` CSS for the
  JS-toggled DOM) mounts in AppLayout, so an armed preview is visible on
  EVERY route: the desk front door, the dictation cockpit, history, all
  of it. The design reason is recorded in the component: the mode must
  never swallow a dictation silently, and Qlippy's cards are double-gated
  so they cannot be the unconditional home — this also supersedes the
  idea of a separate Qlippy mirror (the shell card already shows wherever
  Qlippy would).
- **The card**: the armed text (scrollable, pre-wrap), the egress badge
  (`⌂ Local · not typed yet` — the P60 wake card's exact label; no
  prose), **Type it** (primary; consumes the server-minted token through
  the real route — the runtime types only its own stored text) and
  **Discard** (burns). Keyboard-first: the primary takes focus on
  arrival; Enter types; Escape discards. A 404 (the token consumed
  elsewhere) settles the card quietly; other failures show an honest
  inline error.

## Verification artifacts (Playwright, real app, real broadcasts)

- **On the desk** (`/`): a real `dictation_preview` broadcast revealed
  the card with focus ON the primary (asserted); Type it consumed the
  token through the real route (the capturing store received exactly the
  armed text) and the card hid (`02-card-on-desk.png`).
- Discard burned without typing; **Escape** burned too (the keyboard
  path asserted separately).
- **On the cockpit** (`/dictation`): the same shell card revealed and
  typed (`02-card-on-cockpit.png`).
- Zero page errors. Web build green. Full suite: **3086 passed with
  exactly ONE failure — the manifest guard catching the card's new call
  sites** (the preview routes gained their web consumer tag);
  regenerated, guard 5/5.

## Acceptance criteria — re-checked

- [x] Type it / Discard on the cockpit AND the desk (one shell surface,
      every route — strictly more than the criterion asked).
- [x] The one bus; no modal; no prose (the badge is the answer).
- [x] Keyboard-first (focus + Enter + Escape asserted).

## Deviations from plan

- The scaffold imagined a desk-island card + possibly a Qlippy mirror;
  the shell-level card supersedes both (one implementation, universal
  coverage) — recorded with reasoning above.
