# HSEGHS001HS104-143-11 - HTTP, MCP, Sync, and Compatibility

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
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
