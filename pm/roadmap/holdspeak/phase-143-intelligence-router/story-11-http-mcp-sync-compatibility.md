# HSEGHS001HS104-143-11 - HTTP, MCP, Sync, and Compatibility

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-03, 143-04, 143-05, 143-06
- **Unblocks:** 143-12 through 143-14
- **Owner:** unassigned

## Problem

The new authority needs exact transport parity and a safe compatibility
boundary. Current profile MCP access and sync can bypass OWNER or expose local
binding material.

## Scope

- **In:** Closed HTTP/MCP twins for library, profiles/bindings, registry,
  assignments, previews, and route receipts; shared OWNER service methods;
  idempotency, narrow CAS, safe DTOs, hub-local sync classification.
- **Out:** Model-facing owner resources and events as authority.

## Acceptance criteria

- [ ] Reciprocal golden fixtures match inside transport envelopes.
- [ ] Nested unknown fields refuse; replay succeeds; changed payload refuses.
- [ ] None/AGENT/MODEL_TURN fail before DB/config discovery.
- [ ] Hostile sync cannot bind, assign, download, probe, resume, or invoke.
- [ ] No secret, path, prompt, owner material, or private endpoint leaks.

## Test plan

- **Unit:** auth matrix, recursive schemas, mapping, request receipts.
- **Integration:** restart, lost response, sync forgery/inertness, v1 exception.
- **Manual / device:** regenerate HTTP/MCP inventories and inspect safe Details.

## Notes / open questions

GET reconstructs authority; advisory events can always be lost.

## Progress

- 2026-08-26 — Plan ratified (`assets/story-11-transport-parity-plan.md`;
  six ORCH-CALLs accepted: declarative parity vectors, bounded base64
  file intake, retired-shapes-disappear, receipt golden proof, aliases
  retire together, raw model_profile.*/destination.* families retire —
  closing the MCP-vs-HTTP private-provider bypass). Round 1 (S1+S2):
  twelve owner-only MCP twins (7 model_library.* + 5
  inference_assignment.*) in two new family modules, each calling the
  same application service as its HTTP route — owner guard before body,
  closed versioned DTOs, 16MiB base64 file intake staged-and-deleted,
  write-only secret, assignment-head invariance byte-checked per twin;
  the reciprocal parity harness runs 12 declarative vectors + the
  committed_effect receipt proof against fresh production HTTP and MCP
  compositions (GET/summary invalid-body variants honestly N/A).
  MCP_SIDECAR inventory truthfully 137→149. Orchestrator-verified: twin
  + parity suites 21 passed; worker: full focused 48, MCP/one-path
  guards 25, no schema changes, S4 retirement untouched.
