# HS-120-04 — Browser mic means toggle

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Phase 119 shipped click-to-toggle mic. Five or more components still
label the mic button "Hold to speak" / "Hold to fill" / "Hold to
answer." The labels teach users the wrong interaction model. This is a
repository-wide sweep — every MicButton label in every component.

When this ships, no surface in the codebase says "Hold to..." for a
browser mic. Labels reflect the actual interaction: "Speak" / "Voice
input" / "Speak to fill" or similar.

## Known locations

- `SessionPullout.tsx` line ~458: `label="Hold to speak"`
- `CoderPullout.tsx` lines ~97, ~141: `label="Hold to answer"`,
  `label="Hold to fill"`
- `NotePullout.tsx` line ~91: `label="Hold to fill"`
- `CapabilitySection.tsx` line ~134: `label="Hold to fill"`
- `DeliveryTerminalWindow.tsx`: (Terra-discovered) similar stale label

A `grep -rn "Hold to" web/src/` sweep must run to catch any others.

## Acceptance criteria

- [ ] `grep -rn "Hold to" web/src/` returns zero hits on mic labels.
- [ ] Every MicButton label reflects click-to-toggle semantics.
- [ ] No functional changes to the mic — only labels and aria-labels.

## Test plan

- Grep: `"Hold to"` across `web/src/` returns zero matches.
- Visual: open each listed component, verify mic label is updated.

## Files in scope

- `web/src/desk/components/SessionPullout.tsx`
- `web/src/desk/pullouts/CoderPullout.tsx`
- `web/src/desk/pullouts/NotePullout.tsx`
- `web/src/desk/pullouts/shared/CapabilitySection.tsx`
- `web/src/desk/components/DeliveryTerminalWindow.tsx`
- Any other files discovered by grep.
