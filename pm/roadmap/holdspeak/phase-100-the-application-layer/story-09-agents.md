# HS-100-09 — B5: Agents

- **Project:** holdspeak
- **Phase:** 100
- **Status:** backlog
- **Depends on:** HS-100-08
- **Unblocks:** HS-100-10

## Problem

Job 3's front door is a roster named with a banned word, and its glass
never live-passed (UIUX_JUDGMENT §5.7). Thesis §1.3: blocked first.

## Scope

- In: CompanionCore rebuilt as Agents — blocked sessions lead with the
  asked question and the answer composer (mic + input + Answer +
  Draft-with-AI) one verb from the pane; then running, then idle;
  wings = Delivery (board + dossiers), Chat (today's PersonaChat moved
  in); "Personas" leaves the glass everywhere (allowlist shrinks).
- Out: steering chokepoint changes (audited seam stays byte-identical).

## Acceptance criteria

- [ ] Blocked-first ordering pinned by test.
- [ ] The vocabulary allowlist entries for persona-words are gone.
- [ ] Live screenshots at 1440 and 393.

## Test plan

- vitest; vocabulary guard; integration pins.

## Evidence required

- Suite output; the screenshots.
