# HS-108-04 - Reads arrive with a principal

- **Project:** holdspeak
- **Phase:** 108
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-108-06
- **Owner:** unassigned

## The thesis

GitHub, Jira, and Delivery Workbench CLI reads remain receipt-free
computation, but no entry point may invent an owner principal.

## Recipe

1. Remove `LOCAL_OWNER` defaults from C02/C03/C05 and their call graph.
2. Require `principal` in enrichment functions, packs, pipeline runner,
   mission-control bridge functions, grounding, and composing routes.
3. Derive the principal at HTTP/background entry points.
4. Default a missing request principal to `UNAUTHENTICATED`, never owner.
5. Preserve `ReadSubprocessDenied` instead of swallowing it under the
   broader `OSError` hierarchy.
6. Prove refusal happens before the injected subprocess runner.

## Acceptance

- Omitting a principal is a Python call error.
- `UNAUTHENTICATED` and agent principals cannot run owner CLI reads.
- Owner reads retain their exact argv and output behavior.

## Test plan

Activity, pipeline, grounding, meeting-context, and mission-control unit
groups, with negative runner-not-called assertions.
