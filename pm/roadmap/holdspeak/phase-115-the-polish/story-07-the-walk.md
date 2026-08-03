# HS-115-07 - The walk

- **Project:** holdspeak
- **Phase:** 115
- **Status:** backlog
- **Depends on:** HS-115-01, HS-115-02, HS-115-03, HS-115-04, HS-115-05, HS-115-06
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every surface on the Desk is screenshot-walked at 1440px desktop
and 393px mobile against the real hub. Every finding from the
2026-08-03 audit is verified fixed. No new violations introduced.
When this ships, the audit artifact can be marked RESOLVED.

**Articles served:** VIII (native-grade craft — proven, not
claimed).

## Shot list

### Desktop (1440px)

1. Empty desk with arrival
2. Note pullout (editing body — editor fills window)
3. Note pullout (reading mode — material rendering)
4. Agent pullout (recipe detail)
5. Zone window (drawer contents)
6. Info window (object inspector — no raw IDs)
7. InlineEditor (in-world, expanded — bounded height)
8. PersonaChat (agent conversation)
9. AskPanel (Ask AI)
10. Session pullout (tmux steering)
11. Desk memory (AttentionDrawer — no raw data)
12. Trust window (terse state labels, not prose)
13. Notification shade (SystemShade — chip controls)
14. Command palette (DeskToolShelf — bevel/keyline)
15. Tool inspector (no raw references)
16. Rails / DeliveryBoard (wings, fixed header, no raw IDs)
17. Roadmap window (bounded scroll, material, no clipped titles)
18. Dossier window (no raw enums/SHAs)
19. Workbench core (resized smaller — canvas fits)
20. Settings / Models (working controls)
21. Speak core (RAW trace behind fold)

### Mobile (393px)

22. Desk arrival
23. Note pullout (sheet mode)
24. InlineEditor (bottom sheet)
25. Command palette (full width)
26. Notification shade

## Deliverables

1. Run the hub at localhost.
2. Capture every shot using Playwright.
3. Verify each shot against the audit checklist.
4. Evidence file with shot paths and pass/fail per rule.

## Test plan

- All shots captured and verified.
- Zero audit violations in any shot.
- Evidence file committed with the story flip.
