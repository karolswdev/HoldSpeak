# Project Rooms SRS suite

Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30
Vision epic: [GitHub issue #514](https://github.com/karolswdev/HoldSpeak/issues/514)

This directory is the implementation requirements suite for graduating HoldSpeak's existing Project subsystem and Project Memory surface into Project Rooms: a living operating model for consequential work.

## Documents

1. [Integrated system SRS](./SRS_SYSTEM.md) — normative scope, system requirements, release boundaries, and traceability.
2. [Product and validation SRS](./SRS_PRODUCT_VALIDATION.md) — wedge, users, jobs, hypotheses, validation measures, and market-facing acceptance.
3. [Web experience SRS](./SRS_WEB_EXPERIENCE.md) — information architecture, interactions, states, responsiveness, accessibility, and Web acceptance.
4. [Domain, driver, and Stewardship SRS](./SRS_DOMAIN_DRIVER.md) — domain model, persistence, services, API/MCP contracts, Delta, and the local YOLO Steward.
5. [Interview and universal Watches SRS](./SRS_PROJECT_INTERVIEW_WATCHES.md) — outcome-led creation, provider discovery, tested Watches, cadence, YOLO actions, and setup acceptance.

## Normative language and precedence

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative. Requirement IDs remain stable after implementation begins; superseded requirements are retained with a disposition rather than silently renumbered.

When documents conflict, precedence is:

1. accepted product decisions in `SRS_SYSTEM.md`;
2. the more specific requirement in a council SRS;
3. issue #514 for vision and rationale;
4. existing behavior where no new requirement speaks.

An implementation discovery that invalidates a requirement updates this suite before or with the code change.

## Priority and verification

- **MUST / V0** — required for the owner dogfood and market-validation vertical slice.
- **SHOULD / V1** — required for a credible design-partner release after V0 proves value.
- **LATER / V2+** — expansion work; not a V0 launch blocker.

Verification codes:

- **T** — automated unit, integration, contract, or end-to-end test.
- **D** — deterministic product demonstration.
- **U** — owner/design-partner usability or outcome validation.
- **I** — inspection of schema, trace, receipt, accessibility tree, or generated contract.

## Slice naming

The suite uses two slice schemes: domain slices P0--P7 (`SRS_DOMAIN_DRIVER.md` section 14) and setup slices V0-A through V0-E (`SRS_PROJECT_INTERVIEW_WATCHES.md` section 15). V0-A, V0-B, and V0-C land within P1--P4 before Gate A.

## Baseline truth

This is a graduation, not a greenfield replacement. At baseline `60a4ee99`, HoldSpeak already has:

- `ProjectRepository` and a synchronized `projects` identity;
- `ProjectService` and `/api/projects` routes;
- independent Project resource relationships;
- meeting association and automatic Project detection;
- Project-scoped actions, artifacts, decisions, Ask, and memory search;
- a Project Memory Desk application with Timeline, Decisions, Search, and Ask;
- a narrow “since last meeting” Delta;
- Workbench, Agent/Recipe, Cadence, RuntimeBus, Follow-Through, and YOLO control-mode seams;
- durable typed connector Watches, semantic service events, scheduled refresh, Workbench Reactions, and a live GitHub PR snapshot adapter;
- a broad MCP semantic catalogue, but no `project.*` family.

The implementation MUST extend these authorities or deliberately migrate them. It MUST NOT introduce a second Project identity, a second task board, or a second agent runtime.
