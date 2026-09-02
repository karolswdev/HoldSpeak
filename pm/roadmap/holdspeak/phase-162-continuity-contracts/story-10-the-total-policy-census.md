# HS-162-10 — The total policy census: every capability and source

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-162-01, HS-162-04, HS-162-05, HS-162-09
- **Unblocks:** HS-162-11, HS-162-12, HS-162-13
- **Owner:** unassigned

## Problem

An integration described as “all HoldSpeak” is only credible when omissions
are machine-detectable. Built-ins, internal operations, plugins, and Coder can
otherwise bypass memory policy simply because nobody remembered to list them.

## Scope

- **In:** repository capability-consumer census; source-owner census; generated
  Continuity policy registry; a separate runtime-adapter state registry;
  operation, purpose, destination, scope, cap, disclosure, assignment, and
  owner-decision references; plugin/future-ID registration contract; Coder
  enumeration; CI drift fences and sanitized generated reports.
- **Out:** universal runtime adaptation (CF-2), turning any capability on,
  installing plugins, and semantic-quality policy.

## Acceptance criteria

- [ ] Every model-capable built-in/internal operation and Coder consumer found
  by the repository census has one stable capability/operation row.
- [ ] Every source owner/adapter from HS-162-04 is represented and reconciles
  one-to-one with registry identity and privacy/scope law.
- [ ] Every row explicitly records policy state, allowed purposes/destinations,
  scope rule, hard caps, disclosure, assignment/route binding, and governing
  owner-decision IDs; defaults never silently enable memory.
- [ ] Installed plugin and future capability IDs must register before use;
  unknown IDs fail closed at plan construction and admission.
- [ ] Generated artifacts are deterministic; CI fails when a semantic model
  caller, capability ID, plugin hook, Coder door, or source owner changes
  without a corresponding registry decision.
- [ ] Policy and rollout are independent axes: every ID carries its exact
  ratified `ContinuityCapabilityPolicy@1`, while runtime-adapter state is
  `planned_shadow` for HS-162-11's Ask/Thread/Recipe/Coder representatives and
  `not_integrated|disabled` elsewhere. HS-162-11 alone may atomically change
  those four to `shadow` when adapters and differential fences ship. CF-0 does
  not erase a future bounded policy to `none` because CF-2 owns adoption.

## Test plan

- **Census:** AST/registration/service-owner scans with reviewed exceptions and
  stable generated golden ledgers.
- **Drift:** fixtures add an uncatalogued caller/source/plugin and must fail CI.
- **Policy:** unknown IDs, missing owner references, invalid destination/scope,
  and accidental non-none defaults fail validation.
- **Privacy:** reports contain repo-relative module identifiers, capability IDs,
  and classifications only—never owner filesystem paths or owner data.

## Notes / open questions

- CF-0 §11 and acceptance gate 5 are normative.
- The census is the foundation for complete ecosystem integration; HS-162-11
  proves four seams, while CF-2 later makes runtime plan construction universal.
