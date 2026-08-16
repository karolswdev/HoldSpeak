# HS-120-11 — The walk

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** HS-120-01 through HS-120-10
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every surface touched by stories 01-10 must be visually verified
against the real hub at two viewports (1440px desk, 393px mobile).
The walk proves that the entire desk feels like one OS — no surface
looks like it belongs to a different app, no emoji leaks, no blank
voids, no stale labels.

When this ships, Playwright screenshots at both viewports cover:

1. Workbench dashboard (with needs-attention and idle cards).
2. Open workbench window (config strip collapsed, expanded; item cards
   in all statuses; inlet with grounding tray; template picker).
3. Directory pullout (populated and empty).
4. Chain pullout (with steps and empty).
5. Decision pullout (view and edit mode).
6. Constitutional context core.
7. Session pullout.
8. Empty desk.
9. Presence page.
10. Settings footer (no DEFAULTS button).
11. Repo window Issues tab.
12. Knowledge entry empty state.
13. Coder pullout footer.
14. Workbench canvas (if accessible without a running workflow).

## Acceptance criteria

- [ ] Screenshots at 1440px and 393px for each listed surface.
- [ ] No raw emoji visible in any screenshot.
- [ ] No blank/void pullouts.
- [ ] No "Hold to..." labels visible.
- [ ] No hardcoded hex colors visible in the canvas.
- [ ] Every surface matches the Signal Workbench material language.

## Test plan

- Playwright screenshot walk at 1440px and 393px against the real hub.
- Manual review of every screenshot for visual coherence.

## Files in scope

- Evidence file: screenshots land in `assets/` next to the evidence.
