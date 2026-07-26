# HS-103-07 - The AI chat surfaces feel like a cool part of the system

- **Project:** holdspeak
- **Phase:** 103
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The owner's verdict (Article IX.4)

Sitting with the Phase 103 chain (2026-07-22), the owner's verdict on
the five build stories was implicitly positive, but the sitting
surfaced a real, standing gap the phase's five stories never touched:
the AI chat interfaces — Ask AI, persona/model chat, the steering
composer — read as competent forms, not as "a real cool part of the
system." Verbatim: "the parts of talking with the AI, the chat
interface, and so on - still need a bettered quality pass and a much
more streamlined and 'oh, I'm talking to a real cool part of the
system' kind of vibe... all the AI Chat interfaces... need 2 notches
better." The owner explicitly chose to hold Phase 103 open until this
lands, rather than spin it into a separate later phase.

## Problem

Surveyed live (staged `seeded-desk`, 1440×900) before scoping this
story. Three surfaces carry the same plain shape: an avatar/glyph, a
plain single-line text input, a pill "Send"/"Ask" button, and a quiet
egress/data-scope caption underneath. None of them:

- distinguish a user turn from an assistant turn visually (no message
  bubbles, no alignment/color difference) once a real conversation has
  turns (`PersonaChat.tsx`'s empty state is just a centered avatar +
  name floating in space; `AskPanel.tsx`'s printed result is a plain
  markdown block with a receipt line underneath).
- show any life while the model is thinking (no typing/pulse
  indicator distinguishing the desk's usual generation-theater
  treatment from any other loading spinner).
- give the send action any weight (no motion, sound, or visual
  confirmation beyond the browser's stock button press).
- carry any of the personality the rest of the desk has (the record
  orb, the NEW beat, the window-open flight animation) — the chat
  surfaces are the one place on the desk that still feels like a
  settings form.

## Scope

- In: `web/src/desk/components/PersonaChat.tsx` (persona + model chat),
  `web/src/desk/components/AskPanel.tsx` (Ask AI composer + printed
  card), `web/src/desk/components/SessionPullout.tsx`'s `SteerComposer`
  (the steering composer) — a shared craft pass: real message-turn
  styling (distinct user/assistant treatment, not a single markdown
  blob), a thinking/generation-theater state matching the desk's
  existing generation-theater vocabulary (see the record orb / NEW
  beat conventions already established elsewhere on the desk), a
  send-motion beat, and a warmer empty state than a lone centered
  emoji. Extract any genuinely shared piece (e.g. a turn-bubble
  component) if three call sites would otherwise duplicate it — but
  don't force one if the three composers' real constraints differ
  (Ask AI is single-shot request/response; persona chat is a
  multi-turn thread; steering is fire-and-forget keys/text into a
  live pane).
- Out: changing the underlying data model, wire shape, or routes for
  any of the three surfaces (`ask.ts`, `chat.ts`, `coder_steering.py`
  and friends) — this is visual/interaction craft over the existing,
  working data flow, not a rewrite; adding new AI capabilities.

## Acceptance criteria

- [ ] A live screenshot walk (before/after, staged hub, 1440 + 393) of
      all three surfaces, judged by the owner in the HS-103-06 sitting
      as meeting the "2 notches better" bar — this is the one story in
      this phase whose closing verdict is explicitly aesthetic/felt,
      not purely mechanical.
- [ ] Message turns in `PersonaChat.tsx` are visually distinct
      (user vs. assistant), not a single undifferentiated thread.
- [ ] A thinking/generation state is visible on all three composers
      while awaiting a response, consistent with the desk's existing
      generation-theater vocabulary (not a new, unrelated spinner).
- [ ] `web` vitest + tsc + build + tokens:gate stay green; the
      interior-canon guard's existing regressions for these three
      files (`test_ask_panel_never_regresses_to_a_pre_box_or_section_stack`
      etc.) still pass or are deliberately, narrowly updated if the
      craft pass changes the specific DOM shape they pin.

## Test plan

- Unit: extend `web/src/desk/components/__tests__/` coverage for the
  changed composers if new behavior (a thinking state, turn styling
  hooks) is added — pin the new DOM shape, not just re-approve it.
- Integration: n/a.
- Manual / device: the before/after screenshot walk named above IS the
  acceptance evidence.

## Notes / open questions

This story's acceptance bar is unusually subjective for this repo's
otherwise mechanical PMO gate — that's deliberate, matching the
owner's own framing of the verdict. Lean on the `ui-ux-pro-max` skill
for concrete pattern references (chat bubble conventions, typing
indicators) rather than inventing a bespoke visual language; stay
inside the existing Signal design system's tokens (Phase 96) rather
than introducing new colors/materials.
