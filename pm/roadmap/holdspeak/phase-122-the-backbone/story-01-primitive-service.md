# HS-122-01 — Primitive service

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-122-06 (thin routes audit)
- **Owner:** unassigned

## The thesis (the bar)

Notes, decisions, knowledge entries, zones, workflows, and chains
share a common CRUD shape: list, get, create, update, delete, plus
membership operations for zones and knowledge. Today each route
handler calls `get_database()` and repositories directly. A second
adapter (MCP) cannot reach these operations without HTTP.

When this ships, a `PrimitiveService` class exists that owns all
generic primitive CRUD. It takes a `Principal`, enforces authorization,
validates invariants, calls repositories, and returns typed results.
The FastAPI routes for notes, decisions, knowledge, zones, workflows,
and chains become thin adapters that call this service.

## Scope

- `PrimitiveService.list(principal, kind, query?, limit?, cursor?)`
- `PrimitiveService.get(principal, kind, id)`
- `PrimitiveService.create(principal, kind, fields)`
- `PrimitiveService.update(principal, kind, id, patch)`
- `PrimitiveService.delete(principal, kind, id)`
- `PrimitiveService.file(principal, dir_id, member_ref)` — add to zone
- `PrimitiveService.unfile(principal, dir_id, member_ref)` — remove
- `PrimitiveService.add_member(principal, kb_id, ref)` — KB membership
- `PrimitiveService.remove_member(principal, kb_id, ref)`

Each method uses the existing repository layer unchanged. The service
is the new boundary; repositories remain the persistence adapter.

## Acceptance criteria

- [ ] `PrimitiveService` class exists with all listed methods.
- [ ] Each method takes an explicit `Principal` parameter.
- [ ] Notes, decisions, KB, zone, workflow, chain route handlers
      delegate to `PrimitiveService` — no direct `get_database()`.
- [ ] Existing API behavior unchanged (same responses, same errors).
- [ ] Service is importable without FastAPI — no request/response
      types in its interface.
- [ ] Tests pass: `uv run pytest -q`

## Files in scope

- New: `holdspeak/services/primitive_service.py`
- `holdspeak/web/routes/primitives/notes.py`
- `holdspeak/web/routes/primitives/decisions.py`
- `holdspeak/web/routes/primitives/kbs.py`
- `holdspeak/web/routes/primitives/directories.py`
- `holdspeak/web/routes/primitives/workflows.py`
- `holdspeak/web/routes/primitives/chains.py`
