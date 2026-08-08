# Phase 128 — Desk Intelligence

**Status:** done (10/10).

**Last updated:** 2026-08-07.

## What we're building

One Desk Intelligence pullout brings the completed backend intelligence services
onto the Desk as three time-horizon views: **Brief**, **Follow-Through**, and
**Receipts**. One dock icon, palette verbs, attention state, and in-place
cross-links make the operating picture openable without creating another world.

## The architecture

```text
Dock / palette / WHY controls
            │
            ▼
  IntelligencePullout (PULLOUT_CONTENT)
            │
   ┌────────┼────────────────┐
   ▼        ▼                ▼
Brief   Follow-Through    Receipts
Monday  FollowThrough     DecisionReceipt
Brief   Service.board()   Service search/detail
   │        │                │
   └────────┴──── cross-links┴──► primitive windows
            │
     AttentionDrawer projections
```

## Constitutional grounding

- **Article I:** Intelligence is a Desk pullout, dock object, and primitive
  affordance, never a feature-owned screen.
- **Article VII:** The pullout uses concise labels and in-place detail; it
  introduces no modal or explanatory UI prose.
- **Article VIII:** Signal Workbench chrome, responsive sheet behavior, and
  keyboard-ready controls make each viewport a first-class surface.
- **Article IX:** The phase ends only with a real Playwright walk and screenshots
  at 1440px and 393px.

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-128-01 | Intelligence pullout shell | done | [story-01](story-01-pullout-shell.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-128-02 | Brief view | done | [story-02](story-02-brief-view.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-128-03 | Follow-Through view | done | [story-03](story-03-follow-through-view.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-128-04 | Receipts view | done | [story-04](story-04-receipts-view.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-128-05 | Dock icon and palette commands | done | [story-05](story-05-dock-and-palette.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-128-06 | WHY affordance on primitives | done | [story-06](story-06-why-affordance.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-128-07 | Cross-link drill paths | done | [story-07](story-07-cross-links.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-128-08 | Attention badges and notifications | done | [story-08](story-08-attention-badges.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-128-09 | Responsive and mobile behavior | done | [story-09](story-09-responsive.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-128-10 | The walk | done | [story-10](story-10-the-walk.md) | [evidence-story-10](./evidence-story-10.md) |

## Where we are

Phase 128 is complete (10/10). One Desk Intelligence pullout now joins Brief,
Follow-Through, and Receipts with dock and palette entry, WHY affordances,
cross-links, attention badges, and responsive sheet behavior. The walk proves
the segmented surface, its three views, search, type safety, and intelligence
service regression coverage.
