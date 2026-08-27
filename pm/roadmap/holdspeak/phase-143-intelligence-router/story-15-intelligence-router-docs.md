# HSEGHS001HS104-143-15 - Intelligence Router Repo-Wide Documentation

- **Project:** holdspeak
- **Phase:** 143
- **Status:** done
- **Depends on:** 143-10, 143-11, 143-12, 143-13
- **Unblocks:** 143-14
- **Owner:** unassigned

## Problem

The router's mechanics — capability registry, sparse assignment authority and
precedence, frozen route plans, the fallback controller and its receipts, the
InferenceRunner waist, the ToolTurn foundation and qualification law, the
one-way legacy-pointer migration law, and the census guards that keep it all
converged — exist today only in PMO artifacts
(`assets/architecture-contract.md`, story files, proposals). Repo-wide
documentation does not teach them. An engineer or agent landing cold cannot
learn how HoldSpeak routes intelligence without roadmap archaeology. Owner
ruling 2026-08-25: this is critical; the plumbing must be documented in
repo-wide documentation.

## Scope

- **In:** One durable internal architecture doc
  (`docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md`) covering the full
  mechanic chain (assignment → resolution → frozen route plan → controller →
  runner → receipt; ToolTurn parent/lease/model-step; migration + census law)
  with pointers to the owning modules. Update the existing entry points that
  already gesture at this territory so they defer to it:
  `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`, `docs/MODELS.md`,
  `docs/API_SURFACE.md`, `README.md` where it names model behavior, and
  `docs/PLUGIN_AUTHORING.md` where plugins touch inference. Follow
  `docs/internal/DOCS_STYLE.md`.
- **Out:** New behavior, new UI, restating PMO evidence verbatim, and
  duplicating owner-facing setup steps already owned by `docs/MODELS.md`.

## Acceptance criteria

- [ ] The internal doc explains every mechanic named in the Problem section,
  each grounded with the owning module path (no dead pointers).
- [ ] Every touched entry-point doc defers to the new doc instead of carrying
  a stale or partial parallel account.
- [ ] A reader can trace one real call (e.g. a Recipe run) end to end —
  assignment lookup, freeze, execution, fallback, receipt — from the doc alone.
- [ ] Doc claims are checked against the shipped code of Stories 01–13, not
  against plan files (plans drifted from shipped reality is the failure mode).
- [ ] `docs/internal/DOCS_STYLE.md` conventions hold; positioning voice per
  `docs/internal/POSITIONING.md` for anything user-facing.

## Test plan

- **Unit:** none (docs story); doc-link/anchor checks if the repo's doc lint
  covers them.
- **Manual:** trace-one-call read-through against the live code; grep sweep
  proving no entry-point doc still teaches the pre-router account.

## Notes / open questions

Chartered 2026-08-25 by owner ruling during Story 10, per the standing
dedicated-docs-story law (after features, before closeout). Runs after the
owner-facing glass (12/13) lands so screenshots and flows are documented once,
not twice.

## Progress

- 2026-08-27 — Plan ratified (`assets/story-15-router-docs-plan.md`; four
  ORCH-CALLs accepted: 1,800–2,500-word budget, MODELS.md substantial
  rewrite, in-doc trace with stable anchor, generator-owned API_SURFACE
  deferral). One build round, all three slices:
  `docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md` (1,816 words,
  eleven sections, the Recipe-run trace verified step-by-step against
  shipped code with file:line per step, stable anchor
  `#recipe-run-from-assignment-to-receipt` added by the orchestrator);
  entry-point deferrals in Backend Runtime, MODELS (owner-guide rewrite
  around Library→Assignments, retired mental models killed), README
  (incl. live MCP census 134 tools), Plugin Authoring (host-issued
  PluginDispatch, direct-provider guidance gone), MCP Sidecar
  (defers mechanics), API_SURFACE via the generator under isolated HOME
  (one deferral sentence; json unchanged, 536 routes). Verification:
  stale-vocabulary sweep clean incl. inference_target_id; doc-drift +
  api-surface 24 passed (orchestrator-verified); router adoption/census/
  ToolTurn 61; product-copy 13 + 2 inherited-only. Eight deferral links
  across the six entry points.
