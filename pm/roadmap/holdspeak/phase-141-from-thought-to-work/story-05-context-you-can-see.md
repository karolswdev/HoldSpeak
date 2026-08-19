# HS-141-05 — Context you can see

- **Status:** backlog
- **Depends on:** 141-02, 141-04
- **Unblocks:** 141-07, 141-08

## Problem

HoldSpeak has overlapping lasso, grounding, contextual-action, Rails, and
workbench context paths. The owner needs one visible attachment model, not
hidden enrichment or a 14-item catalog.

## Scope

Use qualified `GroundingSelection.resources` refs as the Phase 141 attachment
contract. Begin with Notes and the seeded Everyday-context Knowledge collection.
Hydrate server-side. Each attachment revision freezes both the owner-visible
container ref and the exact server-resolved leaf refs plus their versions; a
Knowledge collection name alone is not executable provenance. Show the visible
attachment and its expanded leaves in receipt detail. Add one Attach interaction
with pinned/recent and search. Do not expose unsupported kinds.

## Acceptance

- [ ] Default attachment set is empty; nothing attaches automatically.
- [ ] Default Attach view is compact pinned/recent context plus search; the full
  catalog stays behind explicit Browse/search rather than rendering as a wall.
- [ ] Everyday context is reachable in one Attach interaction at both widths,
  including 393px, without scanning the full catalog.
- [ ] Browser never sends copied material as authoritative context.
- [ ] Deleted/stale refs refuse by name before inference/proposal acceptance.
- [ ] Receipts name the visible attached container and the exact versioned leaf
  refs hydrated and used; collection membership cannot drift an in-flight turn.
- [ ] Detach/new revision cannot mutate an in-flight frozen turn.

## Tests

Focused grounding/ref-hydration/privacy tests and both-width picker glass.
