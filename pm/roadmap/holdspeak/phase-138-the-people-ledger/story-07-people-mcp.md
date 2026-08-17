# HS-138-07 — People through the MCP service boundary

- **Project:** holdspeak
- **Phase:** 138
- **Status:** done
- **Depends on:** 138-01, 138-02, 138-03
- **Unblocks:** a trusted programmable People workflow
- **Owner:** primary adjudicator

## Problem

The People ledger is service-oriented but absent from HoldSpeak's programmable MCP
surface. Naively injecting `PeopleService` into generic MCP would turn local
encryption into an undeclared disclosure channel and could expose leader-private
prep to a parent client that retains tool results.

## Scope

- **In:** default-off process-start read/write capability; People readiness; active
  relationship list/detail; shared-intent-only 1:1, agenda, durable grounding note,
  source-preserving grounding bundle, request, explicit acceptance, and commitment
  transitions; static/template resources; closed schemas;
  private-record redaction and guessed-ID refusal; MCP Desk schema parity.
- **Out:** MCP store setup/recovery, archive/delete, leader-private creation/read,
  capture/transcripts, model invocation or inferred assessments, scoring/ranking, search, sync,
  export/connectors, participant access, generic primitive CRUD.

## Acceptance criteria

- [ ] Without `HOLDSPEAK_MCP_PEOPLE_ACCESS`, readiness is content-free and no People
  store is composed; every content tool/resource named-refuses.
- [ ] `read` exposes active relationship metadata and only `shared_intent` children;
  no private prep or leader-private record survives serialization.
- [ ] `write` routes creation, explicit request acceptance, and done/dismiss/reopen
  through `PeopleService` and the encrypted authority; no parallel lifecycle store
  or main-database observer is introduced.
- [ ] Grounding notes remain manual encrypted records. The MCP grounding bundle
  includes only shared-intent evidence, names its policy, and performs no inference.
- [ ] Guessed private request/commitment IDs refuse without echoing content. Tool
  schemas and docs state the disclosure boundary at point of use.
- [ ] The default repo MCP configuration remains off and the People catalogue offers
  no setup, archive/delete, capture, inference, search, sync, or export verb.

## Test plan

- **Focused protocol:** default deny, read/write separation, closed catalogue,
  shared-intent CRUD/transition, resource parity.
- **Privacy:** hostile leader-private sentinels across session prep, agenda, request,
  and guessed IDs; inspect serialized tool/resource text for absence.
- **Regression:** People service/store, MCP catalogue, and Follow-through MCP tests
  under an isolated HOME.
- **Handoff:** static flow decomposition remains the primary acceptance method under
  the owner's best-attempt verification ruling; maintainer repeats the real native
  sidecar walk before production enablement.
