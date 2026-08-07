# HS-121-09 — Live desk truth

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-02 (SurfaceFooter receipt slot)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

WebSocket disconnect invisible, workbench run flickers, bell badge
omits held proposals. Unchanged from the original story.

Covers: N-C1 (WebSocket invisible), N-C3 (run flicker), N-C11
(bell badge mismatch).

## Acceptance criteria

- [ ] Connection indicator in DeskChrome during reconnecting/offline.
- [ ] Workbench run indicator does not flicker.
- [ ] Bell badge includes gate-held proposals.

## Files in scope

- `web/src/desk/components/DeskChrome.tsx`
- `web/src/runtime/RuntimeBus.ts`
- `web/src/desk/components/WorkbenchWindow.tsx`
- `web/src/desk/components/SystemShade.tsx`
