# PHILO-7-02 - Membership and decisions under Article XI

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** PHILO-7-01; the owner's ratification of the admission table, Astra's four readings and the AGENT-principal hold (phase status, Article XI as ruled and Decisions deferred)
- **Unblocks:** PHILO-7-03
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra's check of the drafts, findings 5, 6, 9; the owner's D3

## Problem

Zone and knowledge membership reach MCP through direct service calls (`holdspeak/mcp/tools.py:864-879`) and HTTP through the routers (`holdspeak/web/routes/primitives/directories.py:111-133`, `kbs.py:99-119`). Decision delete, status and supersede bypass the contract on HTTP (`primitives/decisions.py:98,108,125` call `_svc()` directly) and on MCP (`desk.delete kind=decisions` through `_primitive_delete`, `holdspeak/mcp/tools.py:614-615`; `decision.supersede` through `primitives.supersede_decision`, `:1043-1044`). Decision status has an HTTP path but no separately named MCP tool. No desk write admits through the kernel: `holdspeak/services/primitive_service.py` has no kernel call, and Phase 5 left `decision.create/update` as INHERITED Article XI DEBT, pinned by a characterization test (`tests/unit/test_philo5_the_loop.py:618`; `../phase-5-the-one-service-layer/current-phase-status.md:329,332-335`). The owner has now ruled D3. Filing is one zone per primitive: a re-file moves it (`holdspeak/db/schema.py:1605-1611`, `holdspeak/db/primitives.py:1224-1235`). Supersede writes two rows (`primitive_service.py:220-232`).

## Scope

- **In:** descriptors for `zone.file`, `zone.unfile`, `zone.members`, `kb.member.add`, `kb.member.remove`, `kb.members`, `decision.delete`, `decision.status`, `decision.supersede`; HTTP, MCP tools and the `holdspeak://zones/{id}/members` resource over `invoke`; the bypasses retired; identities 1, 6, 25, 28-33 paid (9 MCP); kernel admission + one terminal receipt per logical operation for EVERY row the phase status's admission table marks ADMITTED — the D3 set (`decision.create`, `decision.update`, `decision.supersede`, `zone.file`), Astra's four readings as ratified (`decision.status`, `zone.unfile`, `decision.delete`, `kb.member.add/remove`), and the hidden filing effects (`zone.delete`; `kb.create` with `member_ids` or `kb_id`; `kb.update` with `member_ids`; `zone.create` with `directory_id`; `zone.update` with `parent_id`; the Thought-owned `note.delete`); these writes in story 01's rows gain their admission HERE (story 01 moves them onto the contract without changing how they execute); the COMPLETE kernel path as the phase status names it — submission (`with _as_principal(principal): kernel.submit(...)`, `holdspeak/services/gate_service.py:34-46`, new operation specs beside `holdspeak/kernel/runtime.py:87-118`), approval (the owner's gesture inline for an OWNER principal; HELD for an AGENT principal without a live delegation), execution, terminal receipt; the receipt readback (in the write's result, `GET /api/kernel/read`, and one MCP read operation over `kernel.read`); the principal from the transport, unchanged; the characterization test replaced by a real fence.
- **Out:** admission for the rows the admission table marks exempt (a note create or edit, a plain note delete, a Thought save, a zone or KB rename, `zone.create` without `directory_id`, `kb.create` without `member_ids` and `kb_id`, `kb.delete`) — D3; owner-only authority (a policy change; not applied); the atlas cases (story 03); any face change.

## Acceptance criteria

- [ ] Every membership and decision operation above is one explicit descriptor, reached by HTTP, MCP and (where it exists) the resource, resolving to the same live instance in one hub; the HTTP bypasses at `primitives/decisions.py:98,108,125` call `invoke`.
- [ ] Every ADMITTED row of the admission table makes exactly ONE kernel operation and ONE terminal receipt per logical operation, through HTTP and MCP alike (refusal and failure included); supersede's two rows are one operation; a KB update that renames and changes members is one operation. Red first: on a `git archive` copy of main the same real-producer call makes zero operations and zero receipts. The hidden effects are fenced by their EFFECT: a zone delete that unfiles, a `member_ids` write that adds and removes, a `kb.create` over an existing `kb_id` that clears memberships, a zone move by `parent_id` or by `zone.create` over an existing id, a Thought tombstone that unfiles.
- [ ] The complete path runs end to end: an OWNER-principal write is submitted, approved inline by the same principal, executed once after approval and ends in a terminal receipt; an AGENT-principal write without a live delegation stays HELD in `awaiting_decision` and writes nothing until the owner decides through the existing decide route, then ends in a terminal receipt; no write is approved by a principal other than the owner or a live delegation (no manufactured owner authority).
- [ ] Readback: the write's result carries `operation_id` and the terminal receipt; `GET /api/kernel/read?refs=operation:<id>&view=receipt` and the MCP read operation return the same receipt; an agent reads only its own operations.
- [ ] No double admission: a write through `desk.verb`, `desk.update` or the HTTP route makes one operation, not two.
- [ ] Refusal receipts (V.2, XI.2): every domain refusal of an admitted operation ends in a refusal receipt naming the rule (V.3) — the Thought filing guard (`services/refinement_thought_service.py:1369-1372`), `NotFound`, `zone_name_taken`. Fenced through BOTH transports: the membership is unchanged AND the refusal receipt exists.
- [ ] The exempt rows are NOT admitted: a note create or edit, a plain note delete, a Thought save, a zone or KB rename, `zone.create` without `directory_id`, `kb.create` without `member_ids` and `kb_id`, and `kb.delete` leave zero kernel operations (a fence, so an accidental admission is caught).
- [ ] `tests/unit/test_philo5_the_loop.py:618` (characterization) is replaced by the admission fence; its docstring history is kept in the story notes.
- [ ] Existing authority preserved: compat tables per operation (three-state) include the principal cases; no refusal where main accepted, unless a ruling names it. The AGENT-principal hold is stated in full in the compat tables as the one named change, and ships only as the owner ratifies it.
- [ ] The residual fence: identities 1, 6, 25, 28-33 paid; a new identity fails (red on a copy of main); the roster and `operations.json` regenerated and drift-guarded.
- [ ] Discovery words for "put a decision on my review list" and "file a note into a zone" point at the admitted tools; the story 01 catalogue-only fence stays green.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

PROVISIONAL: 4–5 engineering days (includes the complete kernel path and the hidden filing effects). Calibrated after story 01's first kind.

## Test plan

- **Unit:** descriptors and binding identity; compat tables; the admission fence (operation + receipt counts per logical operation, per transport; red on a copy of main), including each hidden filing effect; the complete-path fence (OWNER inline approval; AGENT held); the refusal-receipt fence through both transports; the readback fence; the no-admission fence for the exempt rows; the no-double-admission fence; the residual fence.
- **Integration:** the real hub: a decision created, set to review, superseded, deleted; a note filed, re-filed (moved) and unfiled; a filed note's zone deleted; a KB's members changed by `member_ids`; a refused filing of a tombstoned Thought's note; each through HTTP and `/api/mcp`; kernel operations and receipts read back.
- **Manual / device:** none (story 04).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B, Astra's check of the drafts, and the owner's D3; unratified. The open readings (`decision.status`, `zone.unfile`, `decision.delete`, `kb.member.add/remove`) are settled before this story builds.
- 2026-09-25 — r2 (Astra's charter check, findings 1-3): the admission table rewritten by effect; the refusal alternative removed (every domain refusal of an admitted operation leaves a refusal receipt); the complete kernel path, readback and principal cases named.
