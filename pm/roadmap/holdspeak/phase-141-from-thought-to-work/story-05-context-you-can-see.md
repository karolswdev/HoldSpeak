# HS-141-05 — Context you can see

- **Status:** done
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
attachment and its expanded leaves in receipt detail. Add one **AI context** row
and Attach interaction with pinned/recent and search. Do not expose unsupported
kinds. The HS-141-05A extension lets the owner promote the complete current set
as a hub-local default for future local create/adopt. It remains empty until
explicitly configured, never mutates existing Thoughts, never syncs, and uses
the same resolver, manifests, application service, receipts, and HTTP/MCP
authority.

## Acceptance

- [x] The shipped default attachment policy is empty; no context attaches until
  the owner explicitly attaches it or configures a future set.
- [x] Default Attach view is compact pinned/recent context plus search; the full
  catalog stays behind explicit Browse/search rather than rendering as a wall.
- [x] Everyday context is reachable in one Attach interaction at both widths,
  including 393px, without scanning the full catalog.
- [x] Browser never sends copied material as authoritative context.
- [x] Deleted/stale refs refuse by name before inference/proposal acceptance.
- [x] Receipts name the visible attached container and the exact versioned leaf
  refs hydrated and used; collection membership cannot drift an in-flight turn.
- [x] Detach/new revision cannot mutate an in-flight frozen turn.
- [x] The picker shows complete **On this Thought** and **For new Thoughts**
  sets; **Remove from this Thought** and **Stop using by default** have distinct
  scopes and receipts.
- [x] A configured set applies atomically only to later local create/adopt. It
  performs no retroactive mutation, sync, model invocation, or partial attach.
- [x] Invalid birth-time context fails open to an empty Thought with durable
  named whole-set attribution; stale existing attachments retain the ordinary
  explicit **Update context** repair.
- [x] HTTP GET/PUT default policy and MCP create/adopt/get/replace use the same
  transport-neutral owner service with qualified refs and closed schemas.

## Tests

Focused grounding/ref-hydration/privacy suites, adversarial Ask/sync checks, and
the both-width picker walk are recorded in
[`evidence-story-05.md`](./evidence-story-05.md).

Ruled designs: [`HS-141-05`](./assets/hs-141-05-design.md) and the integrated
[`HS-141-05A default extension`](./assets/hs-141-05a-default-ai-context-design.md).

## Bundling note

HS-141-05 and HS-141-06 ship together in the Phase 141 Workbench bundle because
context repair, completion, and the one-primary reducer share one authoritative
Thought projection. Splitting them would publish incompatible backend and Desk
halves; neither story's status is inflated by the bundle.
