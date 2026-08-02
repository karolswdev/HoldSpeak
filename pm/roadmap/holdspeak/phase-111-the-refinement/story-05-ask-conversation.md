# HS-111-05 - Ask and conversation

- **Project:** holdspeak
- **Phase:** 111
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

The Ask composer, grounding picker, conversation thread, and
kept-card receipts are where the operator talks to the machine. Chat
UIs are the most SaaS-shaped surface in the industry; this one must
not read as a chat app. The bar: **Ask reads as a command console —
a beveled input deck, an etched grounding picker, a thread that reads
as a session transcript, receipts as filed records** — Workbench 2.0
grammar, dark 2004 render.

## Method (phase canon)

1. **Audit.** An agent walks composer, picker, thread, and kept
   cards; files every chat-app-ism and SaaS-ism.
2. **Rethink.** Propose the native interior against the phase
   question — layout, density, controls, typography.
3. **Implement** in `web/src`.
4. **Prove** with live screenshots on the real desk, 1440 and 393.

## Test plan

- The composer is a beveled input deck with the speak-to-fill mic,
  not a rounded chat bar.
- Thread messages read as transcript entries, not chat bubbles.
- The grounding picker and kept-card receipts use the shared etched
  treatment.
- Screenshot walk at both viewports, no overflow.
