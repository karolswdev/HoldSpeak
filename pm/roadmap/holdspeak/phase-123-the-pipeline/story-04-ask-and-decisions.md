# HS-123-04 — Ask and decisions

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

Ask is orchestration: it resolves grounding, admits inference, invokes a
model, preserves the turn, and emits citations/receipts. Decision lifecycle
operations read two sources, transition or supersede a decision, promote it,
and can produce a model-backed draft. These are application operations, not
FastAPI implementation details; MCP must be able to invoke the same paths
without a shadow implementation.

When this ships, `AskService` owns all ask operations and a named
`DecisionLifecycleService` owns decision list/get/moment/lifecycle/promotion
behavior. Both route modules are narrow transport adapters.

## Phase 122 pattern to follow

Follow the completed HS-122 service extraction pattern and the HS-123-01 error
boundary:

- Construct services with the database plus only the existing domain
  collaborators (grounding, kernel/admission, inference, artifact/decision
  persistence). Never inject `WebContext`, a router, or FastAPI request types.
- Each public method receives `Principal` first. Services return domain DTOs
  that preserve current response payloads, or raise shared domain errors; the
  route maps errors to the current HTTP status/body.
- Keep HTTP JSON parsing and streaming/response serialization at the edge.
  Move all source lookup, authorization, persistence, inference admission,
  receipt, and provenance logic behind the service call.
- Preserve the external API exactly. Do not replace citations with text-only
  answers or turn model admission/receipt failures into generic 500s.

## Required service contracts

### `AskService`

Create `holdspeak/services/ask_service.py` with:

- `list_models(principal)`;
- `resolve_grounding(principal, refs)`;
- `ask(principal, question, grounding, ...)`;
- `keep(principal, output, sources)`.

`ask` is the complex extraction. Define a typed request/result boundary which
contains the current optional model, grounding, and ask settings, but no
FastAPI type. Move the whole orchestration into the service: validate inputs,
resolve/normalize grounding, apply current authorization and inference
admission, invoke the selected model, preserve the turn/output, attach sources
and citations, and produce the existing receipt/error semantics. Do not split
this into a route-owned preflight followed by a service call; that reintroduces
a second ask implementation.

### `DecisionLifecycleService`

Create `holdspeak/services/decision_lifecycle_service.py`, or extend
`PrimitiveService` only if it can remain a coherent named boundary. It must
provide:

- `list_decisions(principal, ...)` and `get_decision(principal, decision_id)`
  with the existing desk/meeting dual-source ordering and fallback;
- `get_moment(principal, decision_id)`;
- `transition(principal, decision_id, action, payload)` for accept/reject and
  the common lifecycle response behavior;
- `supersede(principal, decision_id, payload)`;
- `promote(principal, decision_id, artifact_type, payload)`;
- `draft_promoted_with_model(principal, decision_id, artifact_type, payload)`.

The last operation is complex: it must retain authorization, decision lookup,
promotion constraints, kernel admission, inference execution, durable artifact
creation, provenance, and receipt/failure behavior as one application
operation. The route must not coordinate kernel and inference itself.

## Audited handler map

### `holdspeak/web/routes/primitives/ask.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 200 | `api_list_models` — `GET /api/models` | `AskService.list_models(principal)` | Medium — preserve model visibility and target/status projection. |
| 213 | `api_resolve_grounding` — `POST /api/grounding/resolve` | `AskService.resolve_grounding(principal, refs)` | Medium — retain ordering, missing-reference behavior, sources, and citations. |
| 243 | `api_ask` — `POST /api/ask` | `AskService.ask(principal, question, grounding, ...)` | **Complex** — extraction includes grounding, admission, inference, turn persistence, citations, and receipt/error behavior. |
| 461 | `api_ask_keep` — `POST /api/ask/keep` | `AskService.keep(principal, output, sources)` | Medium — preserve source canonicalization and durable kept-output semantics. |

### `holdspeak/web/routes/decisions.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 56 | `list_decisions` — `GET /api/decisions` | `DecisionLifecycleService.list_decisions(principal, filters)` | High — retain dual-source list ordering, deduplication, and fallback. |
| 108 | `get_decision` — `GET /api/decisions/{decision_id}` | `DecisionLifecycleService.get_decision(principal, decision_id)` | High — retain desk-first/meeting fallback and not-found behavior. |
| 124 | `get_decision_moment` — `GET /api/decisions/{decision_id}/moment` | `DecisionLifecycleService.get_moment(principal, decision_id)` | Medium — preserve source-moment provenance/access rules. |
| 201 | `accept_decision` — `POST /api/decisions/{decision_id}/accept` | `DecisionLifecycleService.transition(principal, decision_id, "accept", payload)` | Medium — retain lifecycle guards and common response. |
| 205 | `reject_decision` — `POST /api/decisions/{decision_id}/reject` | `DecisionLifecycleService.transition(principal, decision_id, "reject", payload)` | Medium — retain lifecycle guards and common response. |
| 209 | `supersede_decision` — `POST /api/decisions/{decision_id}/supersede` | `DecisionLifecycleService.supersede(principal, decision_id, payload)` | High — preserve desk-decision supersession and provenance links. |
| 242 | `promote_decision` — `POST /api/decisions/{decision_id}/promote/{artifact_type}` | `DecisionLifecycleService.promote(principal, decision_id, artifact_type, payload)` | High — retain artifact type validation, promotion constraints, and provenance. |
| 270 | `draft_promoted_decision_with_model` — `POST /api/decisions/{decision_id}/promote/{artifact_type}/draft-with-model` | `DecisionLifecycleService.draft_promoted_with_model(principal, decision_id, artifact_type, payload)` | **Complex** — kernel admission plus inference and durable promoted-draft receipt. |

The accept/reject handlers deliberately share the existing
`_transition_response` behavior. Move that behavior into `transition` (or a
private service helper); do not leave one route-specific lifecycle path behind.

## Implementation steps

1. Read both full route modules and list each current dependency before moving
   code: model registry, grounding/source helpers, kernel, inference runtime,
   persistence, and error mappers.
2. Define transport-neutral request/result DTOs only where raw dictionaries
   obscure the contract. Reuse existing domain values where available.
3. Move `api_ask` as a complete vertical operation. Test success, denied
   admission, model failure, invalid/missing grounding, citation preservation,
   and kept-output source preservation.
4. Implement a single dual-source lookup helper inside the decision service so
   list/get/moment/transition/promotion cannot drift on fallback rules.
5. Move lifecycle validation and promoted-artifact provenance into the decision
   service. Keep kernel/inference collaborators injected and retain their
   existing receipt and failure semantics.
6. Replace handlers with parsing, one service call, shared service-error-to-HTTP
   mapping, and response serialization. Add service and route regression tests.

## Acceptance criteria

- [ ] `AskService` owns all four ask operations in the table and every public
      method accepts an explicit `Principal` without importing routes.
- [ ] `AskService.ask` preserves grounding resolution, source/citation shape,
      inference admission, model execution, durable turn/output behavior, and
      existing receipt/failure semantics.
- [ ] The named decision service owns every decision handler in the table,
      including dual-source list/get fallback, moment retrieval, lifecycle,
      supersession, promotion, and model-backed drafting.
- [ ] Model-backed promotion performs authorization, kernel admission,
      inference, provenance, persistence, and receipt generation in the
      service boundary rather than in a route.
- [ ] Ask and decision handlers make no direct database/domain-helper calls;
      services remain free of FastAPI, `WebContext`, and route imports.
- [ ] Existing ask, grounding, decision, inference, kernel, and route contract
      tests remain green, as does `uv run pytest -q`.

## Builder verification

```bash
rg -n "class (AskService|DecisionLifecycleService)|def (list_models|resolve_grounding|ask|keep|list_decisions|get_decision|get_moment|transition|supersede|promote|draft_promoted_with_model)" holdspeak/services
! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/primitives/ask.py holdspeak/web/routes/decisions.py
! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/ask_service.py holdspeak/services/decision_lifecycle_service.py
uv run pytest -q
```

## Files in scope

- New: `holdspeak/services/ask_service.py`
- New or extended: `holdspeak/services/decision_lifecycle_service.py`
- `holdspeak/services/primitive_service.py` only if it is the selected decision
  boundary
- `holdspeak/web/routes/primitives/ask.py`
- `holdspeak/web/routes/decisions.py`
- Composition wiring for grounding, kernel, inference, and persistence
  collaborators
- Related ask, grounding, decision, meeting, kernel, inference, route, and
  service tests
