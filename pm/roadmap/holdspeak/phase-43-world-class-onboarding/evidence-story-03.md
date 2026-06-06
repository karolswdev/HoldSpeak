# Evidence — HS-43-03 — First-dictation reward + Done

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`
- **Owner:** unassigned

## What shipped

The emotional peak of the wizard — the first-dictation step is now a **live,
celebratory reward moment** instead of a placeholder.

### Waiting / live — `welcome.astro` + `welcome-app.js`

- A circular **mic target** with three concentric rings. Idle → faint; **live →
  the rings ripple outward in the accent and the core glows orange** (keyed off the
  `runtime_activity` WS state: listening/recording/transcribing/processing/typing).
- The prompt shows the **actual configured hotkey** in a `<kbd>` chip — read
  dynamically from `/api/settings` (`hotkey.key` → a friendly label, e.g.
  "Right ⌥ / Alt"), never hardcoded.
- A live status line — "● Listening…" — while a dictation is in flight, plus an
  honest "Troubleshoot in setup / skip for now" hint when nothing's happening yet.

### The win

On a real `dictation_typed` / `dictation_delivered` (the runtime's own broadcast),
the step flips to the celebration: a **green check-burst** (pop + spark particles),
**"It worked."** in display type, "Your words landed in the app — typed for you, on
this machine," and the **transcript revealed** in an accent-bordered quote.

### Accessibility / motion

`prefers-reduced-motion` collapses the ripple, the pop, and the sparks; **focus
moves to the "It worked" heading** when it replaces the prompt (`heading_dictation_win`).

## Verification

- **Live (Playwright):** the hotkey rendered "Right ⌥ / Alt" (from `hotkey.key`
  `alt_r`); broadcasting `listening` lit the ripple; broadcasting `dictation_typed`
  flipped to **"It worked."** with the transcript *"ship the world-class onboarding
  wizard by friday."* Screenshots:
  [`wizard_dictation_live.png`](./evidence/wizard_dictation_live.png) (the live
  mic ripple) + [`wizard_dictation_win.png`](./evidence/wizard_dictation_win.png)
  (the celebration).

## Tests run

```
uv run pytest -q tests/integration/test_web_welcome_wizard.py   → passed
```

- `test_first_dictation_is_a_reward_moment` — the live target + the celebration +
  the transcript reveal + the **dynamic hotkey** (mapped, from `/api/settings`) +
  reduced-motion + focus-to-"It worked".

Full suite: see the HS-43-03 commit message.

## Acceptance criteria

- [x] The step shows live dictation state (mic ripple + the actual hotkey) + a
      celebratory success with the transcript; reduced-motion safe; covered by a
      live WS Playwright capture + a markup/source test.
