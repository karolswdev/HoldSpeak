# HS-121-05 — Keyboard is a complete path

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Mouse-only press rows, missing ARIA combobox patterns, global key
captures that steal from text inputs. Unchanged from the original
story — see Phase 121 charter for full scope.

Covers: F22 (press rows), F23 (palette ARIA), N-A1 (inlet ARIA),
N-A2/A3 (typing guards), N-A4 (event.repeat), N-A6 (template roving).

## Acceptance criteria

- [ ] GroundingSection/RailsPicker press rows: focusable + keyboard.
- [ ] Palette: role="combobox" with aria-activedescendant.
- [ ] InletAutocomplete: role="combobox" with aria-activedescendant.
- [ ] MicButton/ProposalStrip global listeners check e.target.
- [ ] event.repeat guard on held-key handlers.
- [ ] Template picker: roving focus if >4 cards.

## Files in scope

- `web/src/desk/components/GroundingSection.tsx`
- `web/src/desk/components/RailsPicker.tsx`
- `web/src/desk/components/DeskToolShelf.tsx`
- `web/src/desk/components/InletAutocomplete.tsx`
- `web/src/desk/components/MicButton.tsx`
- `web/src/desk/voice/ProposalStrip.tsx`
- `web/src/desk/components/WorkbenchTemplatePicker.tsx`
