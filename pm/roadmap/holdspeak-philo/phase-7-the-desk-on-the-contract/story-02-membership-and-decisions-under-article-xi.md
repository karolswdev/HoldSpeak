# PHILO-7-02 - Membership and decisions under Article XI

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** PHILO-7-01; the open D3 readings settled (phase status, Decisions deferred)
- **Unblocks:** PHILO-7-03
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra's check of the drafts, findings 5, 6, 9; the owner's D3

## Problem

Zone and knowledge membership reach MCP through direct service calls (`holdspeak/mcp/tools.py:864-879`) and HTTP through the routers (`holdspeak/web/routes/primitives/directories.py:111-133`, `kbs.py:99-119`). Decision delete, status and supersede bypass the contract on HTTP (`primitives/decisions.py:98,108,125` call `_svc()` directly) and on MCP (`desk.delete kind=decisions` through `_primitive_delete`, `holdspeak/mcp/tools.py:614-615`; `decision.supersede` through `primitives.supersede_decision`, `:1043-1044`). Decision status has an HTTP path but no separately named MCP tool. No desk write admits through the kernel: `holdspeak/services/primitive_service.py` has no kernel call, and Phase 5 left `decision.create/update` as INHERITED Article XI DEBT, pinned by a characterization test (`tests/unit/test_philo5_the_loop.py:618`; `../phase-5-the-one-service-layer/current-phase-status.md:329,332-335`). The owner has now ruled D3. Filing is one zone per primitive: a re-file moves it (`holdspeak/db/schema.py:1605-1611`, `holdspeak/db/primitives.py:1224-1235`). Supersede writes two rows (`primitive_service.py:220-232`).

## Scope

- **In:** descriptors for `zone.file`, `zone.unfile`, `zone.members`, `kb.member.add`, `kb.member.remove`, `kb.members`, `decision.delete`, `decision.status`, `decision.supersede`; HTTP, MCP tools and the `holdspeak://zones/{id}/members` resource over `invoke`; the bypasses retired; identities 1, 6, 25, 28-33 paid (9 MCP); kernel admission + one terminal receipt for the D3 set — `decision.create`, `decision.update`, `decision.supersede`, `zone.file` — plus whichever open readings the ratification settles; the admission through the existing kernel path (`with _as_principal(principal): kernel.submit(...)`, `holdspeak/services/gate_service.py:34-46`), with new operation specs beside the existing ones (`holdspeak/kernel/runtime.py:87-118`); the principal from the transport; the characterization test replaced by a real fence.
- **Out:** admission for plain edits (note body, Thought save, zone/kb create/update/delete) — D3; owner-only authority (a policy change; not applied); the atlas cases (story 03); any face change.

## Acceptance criteria

- [ ] Every membership and decision operation above is one explicit descriptor, reached by HTTP, MCP and (where it exists) the resource, resolving to the same live instance in one hub; the HTTP bypasses at `primitives/decisions.py:98,108,125` call `invoke`.
- [ ] The D3 set is admitted: each write makes exactly ONE kernel operation and ONE terminal receipt, through HTTP and MCP alike (refusal and failure included); the receipt is read back through the contract. Red first: on a `git archive` copy of main the same real-producer call makes zero operations and zero receipts.
- [ ] No double admission: a write through `desk.verb`, `desk.update` or the HTTP route makes one operation, not two; a Thought-owned filing guard (`services/refinement_thought_service.py:1369-1372`) still refuses before admission or ends in a refusal receipt — which one is declared.
- [ ] Plain edits are NOT admitted: a note body edit, a Thought save and zone/kb create/update/delete leave zero kernel operations (a fence, so an accidental admission is caught).
- [ ] `tests/unit/test_philo5_the_loop.py:618` (characterization) is replaced by the admission fence; its docstring history is kept in the story notes.
- [ ] Existing authority preserved: compat tables per operation (three-state) include the principal cases; no refusal where main accepted, unless a ruling names it.
- [ ] The residual fence: identities 1, 6, 25, 28-33 paid; a new identity fails (red on a copy of main); the roster and `operations.json` regenerated and drift-guarded.
- [ ] Discovery words for "put a decision on my review list" and "file a note into a zone" point at the admitted tools; the story 01 catalogue-only fence stays green.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

Not yet grounded. Re-estimated after story 01.

## Test plan

- **Unit:** descriptors and binding identity; compat tables; the admission fence (operation + receipt counts per write, per transport; red on a copy of main); the no-admission fence for plain edits; the no-double-admission fence; the residual fence.
- **Integration:** the real hub: a decision created, set to review, superseded; a note filed, re-filed (moved) and unfiled; each through HTTP and `/api/mcp`; kernel operations and receipts read back.
- **Manual / device:** none (story 04).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B, Astra's check of the drafts, and the owner's D3; unratified. The open readings (`decision.status`, `zone.unfile`, `decision.delete`, `kb.member.add/remove`) are settled before this story builds.
