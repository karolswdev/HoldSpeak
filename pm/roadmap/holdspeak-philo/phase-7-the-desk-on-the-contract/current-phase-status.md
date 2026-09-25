# Phase 7 - The Desk on the Contract

**Last updated:** 2026-09-25 (DRAFTED r2 — Astra's check paid; unratified; builds only after Phase 6 closes).

## Goal

The bounded desk slice on the one contract: notes, zones (directories), knowledge bases, zone and knowledge membership, and the remaining decision operations. The owner files a note into a zone and finds it again, from an MCP client with NO repository access, with a kernel receipt where he files or decides. Routes, MCP tools and MCP resources for the slice reach ONE declared operation each, bound to the hub's ONE `PrimitiveService`. The duplicated paths retire. The residual set shrinks by the identities enumerated below.

## Authority

The owner, 2026-09-23 (verbatim): "the sidecar design is an absolutely retarded design — things have to flow through services — it has always been my ask but somehow that ask got misinterpreted."

The owner, 2026-09-24 night, by AskUserQuestion (verbatim from `../PHASE-6-7-CHARTER-DRAFTS.md` §"The owner's rulings"):

- **D1** the next slice = file and find desk notes (Phase 7 as bounded above).
- **D2** repairs first: Phase 6 The Honest Morning before Phase 7.
- **D3 (Article XI):** writes that FILE or DECIDE — decision create/update/supersede, filing into a zone — get a kernel operation and a receipt through the existing kernel path; plain edits (a note body, a Thought save) do not. Phase 7 story 02 pays it for the desk slice and Phase 5's carried decision debt with it.
- **D4** Phase 7's closing use: Codex WITHOUT repository access (discovery from the catalogue alone is an acceptance criterion); a reopened Desk read accepted; already-open refresh not claimed.

Carried: Phase 5's settled positions (`../phase-5-the-one-service-layer/current-phase-status.md:129-146`), its compatibility rules (`:109-116`) and its fence law. The method is handover XXVIII §"The method" (`docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:11-20`). The slice and its shape are Astra's counter-proposal, ADOPTED (`../PHASE-6-7-CHECK-ASTRA.md` CONDITIONS; XXVIII §Road B).

Everything below the owner's words is the two brains' proposal for how to honour them.

## The roots

- **Tenet 3 (help and accelerate):** the Phase 5 rehearsal found the review-list decision only after 201 s and 25 repository reads (`pm/roadmap/holdspeak/BACKLOG.md:1216`; `docs/internal/philo/phase-5/his-words/rehearsal.md:43,49-50`). A client without the repository would not find it. The catalogue must name his jobs.
- **Tenet 1 (no over-engineering):** a finite explicit descriptor table per (kind, verb) is a module. A discovery framework, universal CRUD semantics or a new authority policy is not in scope.
- **Tenet 7 (a Senior Architect with reports):** the job is his: put a note where he keeps things, find it again, put a decision on his review list, make his brief.
- **Article XI:** the owner ruled which desk writes are consequential (D3). Filing and deciding get one kernel admission and one terminal receipt each, and so does every write whose effect is a filing, also inside a create, update or delete (XI.1: "Each effect is judged for itself"). Genuinely plain edits do not.

## Status of this charter

DRAFTED 2026-09-25 by Muad'Dib. Astra's check: RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`); r2 pays it. The owner's ratification owed; build starts only after Phase 6 closes (D2).

## Scope

- **In:** the slice inventory below; explicit descriptors per (kind, verb) in `holdspeak/operations.py`, bound at hub composition to the hub's `PrimitiveService`; HTTP routes, MCP tools and the slice's MCP resources over `invoke`; the duplicated paths retired; kernel admission + receipts for every ADMITTED row of the admission table, through the complete kernel path (story 02); tool descriptions that name the jobs, and a discovery fence (story 01); the shelf-enum alignment repair carried from Phase 5 (story 01); new atlas browser cases and their `.op` siblings (story 03); the closing use from Codex without repository access (story 04).
- **Out:**
  - Workflows and chains (`desk.*` `kind=workflows|chains`, 16 identities): parked with their owning slice. They run work (`holdspeak/web/routes/primitives/workflows.py` `SequenceWorkflowService`), which is a different contract from a filing edit.
  - The workbench aliases (`desk.verb` `verb_id=workbench.add_item|workbench.run`): parked with the workbench slice. Workbench execution differs (`holdspeak/mcp/tools.py:1148-1149`).
  - `desk.snapshot` and `desk.needs_you`: parked. They are aggregate reads over many owners (`holdspeak/mcp/tools.py:912-920`); `desk.needs_you` belongs to projects.
  - Projects (42 MCP identities): Phase 8, the owner's second job.
  - People (17): its own store and custody boundary.
  - Any face change. Any change to the spatial Floor.
  - "Attach a note to a meeting": DROPPED from the closing job (Active risks, MISSED 4). No durable note-to-meeting relationship exists in this slice.
  - Owner-only authority for primitive writes: a policy change, not applied by default (Settled between the brains).
  - Already-open Desk refresh (D4).

### The slice inventory

Canonical operation names are the brains' proposal; story 01 fixes them in its first commit, and Astra checks them. Existing public names stay compatible. "Paid" names the residual identities `(transport, entry_point, discriminator)` from `docs/internal/philo/phase-5/residual-set.json`.

| Operation (proposed) | Current HTTP | Current MCP tool / resource | Residual identities paid | Non-uniformity |
|---|---|---|---|---|
| `note.create` | `POST /api/notes` (`primitives/notes.py:53`) | `desk.create kind=notes`; `desk.verb desk.create kind=notes` | 2 MCP | Refuses a Thought-owned note id with `thought_expected_revision_required` (`services/primitive_service.py:75-76`). |
| `note.read` | `GET /api/notes/{note_id}` (`:74`) | `desk.get kind=notes`; resource `holdspeak://primitives/{kind}/{id}` (`mcp/resources.py:234`) | 1 MCP | — |
| `note.update` | `PUT /api/notes/{note_id}` (`:83`) | `desk.update kind=notes`; `desk.verb desk.update kind=notes` | 2 MCP | A Thought-owned note routes to `RefinementThoughtService.update_note` with expected revisions and returns revision cursors (`services/primitive_service.py:91-111,147-152`). NOT uniform. |
| `note.delete` | `DELETE /api/notes/{note_id}` (`:106`) | `desk.delete kind=notes`; `desk.verb desk.delete kind=notes` | 2 MCP | A Thought-owned note is tombstoned, not deleted (`services/primitive_service.py:127-134`), and the tombstone unfiles it (`db/refinement_thoughts.py:236`): ADMITTED. A plain note delete leaves its zone membership row unchanged (`db/primitives.py:185-200`): exempt. |
| `note.list` | `GET /api/notes` (`:43`) | `desk.list kind=notes` | 1 MCP | Takes an optional `tag` (`services/primitive_service.py:54`). |
| (notes route constructor) | `primitives/notes.py::build_notes_router._svc` fallback (`:30-38`) | — | 1 HTTP | Paid only when the fallback construction leaves the route. |
| `zone.create` | `POST /api/directories` (`primitives/directories.py:42`) | `desk.create kind=directories`; `desk.verb desk.create kind=directories` | 2 MCP | Refuses a taken name `zone_name_taken` (`services/primitive_service.py:336-356`). With a caller-supplied `directory_id` it can move an existing zone: ADMITTED; otherwise exempt. |
| `zone.read` | `GET /api/directories/{directory_id}` (`:67`) | `desk.get kind=directories`; resource `holdspeak://primitives/{kind}/{id}` | 1 MCP | Returns `{directory, member_ids, members}` (`services/primitive_service.py:323-334`), not the row alone. |
| `zone.update` | `PUT /api/directories/{directory_id}` (`:76`) | `desk.update kind=directories`; `desk.verb desk.update kind=directories` | 2 MCP | `parent_id` uses a sentinel: absent ≠ null (`services/primitive_service.py:358-382`). With `parent_id` present it moves the zone and its contents: ADMITTED; a rename alone is exempt (Article XI as ruled). |
| `zone.delete` | `DELETE /api/directories/{directory_id}` (`:101`) | `desk.delete kind=directories`; `desk.verb desk.delete kind=directories` | 2 MCP | Unfiles every member and moves child zones to the root (`db/primitives.py:1182-1204`). ADMITTED (Article XI as ruled). |
| `zone.list` | `GET /api/directories` (`:35`) | `desk.list kind=directories` | 1 MCP | Each row carries `member_ids` (`services/primitive_service.py:313-321`). |
| (directories route constructor) | `primitives/directories.py::build_directories_router._svc` fallback (`:22-30`) | — | 1 HTTP | As notes. |
| `kb.create` | `POST /api/kbs` (`primitives/kbs.py:42`) | `desk.create kind=kbs`; `desk.verb desk.create kind=kbs` | 2 MCP | Refuses an empty name (`services/primitive_service.py:243-259`). With `member_ids`, or over a caller-supplied `kb_id`, it writes knowledge memberships (`db/primitives.py:401-432`): ADMITTED; otherwise exempt. |
| `kb.read` | `GET /api/kbs/{kb_id}` (`:62`) | `desk.get kind=kbs`; resource `holdspeak://primitives/{kind}/{id}` | 1 MCP | — |
| `kb.update` | `PUT /api/kbs/{kb_id}` (`:71`) | `desk.update kind=kbs`; `desk.verb desk.update kind=kbs` | 2 MCP | With `member_ids` it adds and removes knowledge memberships (`db/primitives.py:401-432`): ADMITTED; a rename alone is exempt. |
| `kb.delete` | `DELETE /api/kbs/{kb_id}` (`:89`) | `desk.delete kind=kbs`; `desk.verb desk.delete kind=kbs` | 2 MCP | — |
| `kb.list` | `GET /api/kbs` (`:35`) | `desk.list kind=kbs` | 1 MCP | — |
| (kbs route constructor) | `primitives/kbs.py::build_kbs_router._svc` fallback (`:22-30`) | — | 1 HTTP | As notes. |
| `zone.file` | `PUT /api/directories/{directory_id}/members/{primitive_id}` (`primitives/directories.py:121`) | `zone.file` (`mcp/tools.py:233,864`) | 1 MCP | ONE zone per primitive: a re-file MOVES it (`db/schema.py:1605-1611`, `db/primitives.py:1224-1235`). A tombstoned Thought's note is refused (`services/refinement_thought_service.py:1369-1372`). D3: ADMITTED. |
| `zone.unfile` | `DELETE /api/directories/{directory_id}/members/{primitive_id}` (`:133`) | `zone.unfile` (`mcp/tools.py:234,866`) | 1 MCP | Unfile is a tombstone row (`db/primitives.py:1232-1234`). ADMITTED (Astra's reading; the owner confirms). |
| `zone.members` | `GET /api/directories/{directory_id}/members` (`:111`) | `zone.list_members` (`mcp/tools.py:235,870`); resource `holdspeak://zones/{id}/members` (`mcp/resources.py:258`) | 1 MCP | — |
| `kb.member.add` | `PUT /api/kbs/{kb_id}/members/{resource_ref}` (`primitives/kbs.py:109`) | `kb.add_member` (`mcp/tools.py:236,872`) | 1 MCP | A reference, not a primitive filing: many per KB. ADMITTED (Astra's reading; the owner confirms). |
| `kb.member.remove` | `DELETE /api/kbs/{kb_id}/members/{resource_ref}` (`:119`) | `kb.remove_member` (`mcp/tools.py:237,874`) | 1 MCP | ADMITTED (Astra's reading; the owner confirms). |
| `kb.members` | `GET /api/kbs/{kb_id}/members` (`:99`) | `kb.list_members` (`mcp/tools.py:238,878`) | 1 MCP | — |
| `decision.delete` | `DELETE /api/decisions/{decision_id}` (`primitives/decisions.py:98`) — calls `_svc()` directly, bypassing the contract | `desk.delete kind=decisions`; `desk.verb desk.delete kind=decisions` | 2 MCP | The HTTP bypass is NOT a census identity (the route's constructor was paid in PHILO-5-01); migrating it is uncounted work (Astra finding 9). A tombstone (`db/primitives.py:318-325`). ADMITTED (Astra's reading; the owner confirms). |
| `decision.status` | `PUT /api/decisions/{decision_id}/status` (`primitives/decisions.py:108`) — direct `_svc()` call | **No separately named MCP tool.** Reached today through `desk.update kind=decisions {status}` (already `decision.update`) | 0 | Same effect as an update of `status` (`services/primitive_service.py:211-218`). ADMITTED (Astra's reading; the owner confirms). |
| `decision.supersede` | `POST /api/decisions/{decision_id}/supersede` (`primitives/decisions.py:125`) — direct `_svc()` call | `decision.supersede` (`mcp/tools.py:395,1043`) | 1 MCP | Writes two rows: the old decision updated, a successor created (`services/primitive_service.py:220-232`). D3: ADMITTED. |
| `decision.create` / `decision.update` | `POST /api/decisions`; `PUT /api/decisions/{decision_id}` | `desk.create/update kind=decisions` (already on the contract, `holdspeak/operations.py:175-219`) | 0 (paid in PHILO-5-01) | Gain KERNEL ADMISSION + RECEIPTS per D3: Phase 5's carried debt (`../phase-5-the-one-service-layer/current-phase-status.md:329,332-335`). |

Totals: **33 MCP + 3 HTTP residual identities.** The MCP rows: notes 8, directories 8, kbs 8, zone membership 3, knowledge membership 3, `desk.delete`/`desk.verb desk.delete` `kind=decisions` 2, `decision.supersede` 1.

Arithmetic: the **12 update/delete identities** (`desk.update`, `desk.delete`, `desk.verb desk.update`, `desk.verb desk.delete`, each for notes, directories and kbs) cover the three kinds together; directories and kbs alone contribute 8. The admission correction (Article XI as ruled) changes how some of these writes execute, not the residual inventory.

### The enumerated identities

Exactly these 36 entries of `docs/internal/philo/phase-5/residual-set.json` (at main `f93e76fa`):

| # | Transport | Entry point | Discriminator |
|---|---|---|---|
| 1 | mcp | `decision.supersede` | — |
| 2 | mcp | `desk.create` | `kind=notes` |
| 3 | mcp | `desk.create` | `kind=kbs` |
| 4 | mcp | `desk.create` | `kind=directories` |
| 5 | mcp | `desk.delete` | `kind=notes` |
| 6 | mcp | `desk.delete` | `kind=decisions` |
| 7 | mcp | `desk.delete` | `kind=kbs` |
| 8 | mcp | `desk.delete` | `kind=directories` |
| 9 | mcp | `desk.get` | `kind=notes` |
| 10 | mcp | `desk.get` | `kind=kbs` |
| 11 | mcp | `desk.get` | `kind=directories` |
| 12 | mcp | `desk.list` | `kind=notes` |
| 13 | mcp | `desk.list` | `kind=kbs` |
| 14 | mcp | `desk.list` | `kind=directories` |
| 15 | mcp | `desk.update` | `kind=notes` |
| 16 | mcp | `desk.update` | `kind=kbs` |
| 17 | mcp | `desk.update` | `kind=directories` |
| 18 | mcp | `desk.verb` | `verb_id=desk.create,kind=notes` |
| 19 | mcp | `desk.verb` | `verb_id=desk.create,kind=kbs` |
| 20 | mcp | `desk.verb` | `verb_id=desk.create,kind=directories` |
| 21 | mcp | `desk.verb` | `verb_id=desk.update,kind=notes` |
| 22 | mcp | `desk.verb` | `verb_id=desk.update,kind=kbs` |
| 23 | mcp | `desk.verb` | `verb_id=desk.update,kind=directories` |
| 24 | mcp | `desk.verb` | `verb_id=desk.delete,kind=notes` |
| 25 | mcp | `desk.verb` | `verb_id=desk.delete,kind=decisions` |
| 26 | mcp | `desk.verb` | `verb_id=desk.delete,kind=kbs` |
| 27 | mcp | `desk.verb` | `verb_id=desk.delete,kind=directories` |
| 28 | mcp | `kb.add_member` | — |
| 29 | mcp | `kb.list_members` | — |
| 30 | mcp | `kb.remove_member` | — |
| 31 | mcp | `zone.file` | — |
| 32 | mcp | `zone.list_members` | — |
| 33 | mcp | `zone.unfile` | — |
| 34 | http | `holdspeak/web/routes/primitives/directories.py::build_directories_router._svc` | `PrimitiveService` |
| 35 | http | `holdspeak/web/routes/primitives/kbs.py::build_kbs_router._svc` | `PrimitiveService` |
| 36 | http | `holdspeak/web/routes/primitives/notes.py::build_notes_router._svc` | `PrimitiveService` |

## The revision and counting basis

Pinned to main `f93e76fa` (the commit this charter branches from). At that commit the residual fence is green: `RESIDUAL FENCE GREEN: 320 identities match` (`scripts/residual_census.py --check`, run under an isolated HOME for this draft). The ledger's own measurements: 320 residual identities = **256 MCP + 64 HTTP** (`docs/internal/philo/phase-5/residual-set.json` `measurements`).

The counting rule, verbatim from the ledger's `counting` field: "mcp: every assembled tool dispatched by hand, desk.* split by kind and desk.verb by verb and kind, minus the identities an operation descriptor exposes; http: every syntactic *Service(...) construction in holdspeak/web/routes, keyed by module::function".

Consequences, stated so no one reads them as promises:

- **33 + 3 is not a guaranteed reduction while fallbacks remain.** The three HTTP identities are `_svc()` fallback constructions for a partially wired context (`primitives/notes.py:30-38`). A syntactic census cannot tell a fallback from a hub construction. If a fallback stays for the route tests, the identity MOVES and is not paid — the Phase 5 precedent is `monday_brief.py::build_monday_brief_router.ops` (`residual-set.json` `moved`). The honest range at close: 284 (all 36 paid) to 287 (the 33 MCP only).
- The census counts constructors and declared exposure, not traversal (Astra finding 9, `../PHASE-6-7-CHECK-ASTRA.md`). The HTTP decision delete/status/supersede bypasses (`primitives/decisions.py:98,108,125`) are not identities; their migration is real work that no count shows.
- New public tools may raise the public tool count (228 today) while the residual set shrinks. Different measurements, reported separately (Phase 5 rule).
- The atlas today: `atlas.json` has 85 cases at `f93e76fa` (81 when Astra checked the drafts); `atlas-phase3.json` has 36.

## Article XI as ruled

D3, verbatim: "writes that FILE or DECIDE — decision create/update/supersede, filing into a zone — get a kernel operation and a receipt through the existing kernel path; plain edits (a note body, a Thought save) do not. Phase 7 story 02 pays it for the desk slice and Phase 5's carried decision debt with it."

The effect decides, not the verb name (XI.1: "Each effect is judged for itself"). Astra's check (`checks/charter-astra-r1.md` finding 1) reproduced two filing effects inside writes that r1 called plain edits; both left zero kernel operations. r2 audits every create, update and delete of notes, directories and kbs for a placement field (a parent, a zone, member ids) and classifies each below.

### The admission table

| Operation | Admission | The effect that decides it | Source |
|---|---|---|---|
| `decision.create` | ADMITTED (D3) | A decision made. | `services/primitive_service.py:166-194` |
| `decision.update` | ADMITTED (D3) | A decision changed. | `:196-203` |
| `decision.supersede` | ADMITTED (D3) | A decision replaced: two rows, ONE admission. | `:220-232`; `db/primitives.py:327-339` |
| `zone.file` | ADMITTED (D3) | A primitive filed; a re-file moves it. | `services/primitive_service.py:398-413`; `db/primitives.py:1224-1235` |
| `decision.status` | ADMITTED (Astra's reading) | The same status mutation as the admitted `decision.update`; another route cannot exempt it. | `services/primitive_service.py:211-218` |
| `zone.unfile` | ADMITTED (Astra's reading) | The filing relationship removed. That it can be undone does not remove Article V's filing trigger. | `:415-427` |
| `decision.delete` | ADMITTED (Astra's reading) | A decision withdrawn: a lifecycle change. The row is a tombstone, so "irreversible" is not the reason. | `db/primitives.py:318-325` |
| `kb.member.add` / `kb.member.remove` | ADMITTED (Astra's reading) | A durable reference filed into or removed from a knowledge base. Many-to-many does not change the effect. | `services/primitive_service.py:294-310` |
| `zone.delete` | ADMITTED (this audit) | Every member unfiled and every child zone moved to the root, in the same transaction. | `db/primitives.py:1182-1204` |
| `kb.create` with `member_ids`, or with a caller-supplied `kb_id` | ADMITTED (this audit) | Knowledge memberships written. Over an existing `kb_id` the create is an upsert that REPLACES the membership set: probed in an isolated database, `kb.create` with an existing `kb_id` and no `member_ids` removed a membership added through `kb.add_member` (the service passes `member_ids or []`). The same admission as `kb.member.add`/`remove`. | `services/primitive_service.py:252-256`; `db/primitives.py:401-432` |
| `kb.update` with `member_ids` | ADMITTED (this audit) | Knowledge memberships added and removed to match the list. The same admission as `kb.member.add`/`remove`. | `db/primitives.py:401-432` |
| `zone.update` with `parent_id` present | ADMITTED (this audit) | The zone moved under another parent (or to the root), with its contents. | `services/primitive_service.py:358-382` (sentinel: absent ≠ null) |
| `note.delete` of a Thought-owned note | ADMITTED (this audit) | The tombstone unfiles the note from its zone. | `db/refinement_thoughts.py:236` via `services/refinement_thought_service.py:1295-1309` |
| `zone.create` with a caller-supplied `directory_id` | ADMITTED (this audit) | Over an existing id the create is an upsert that sets `parent_id` (to the given value or NULL): it can move an existing zone. Memberships are kept (probed). | `services/primitive_service.py:336-356`; `db/primitives.py:1109-1130` |
| `zone.create` without `directory_id` (with or without `parent_id`) | exempt (this audit) | A new zone made where it is made. Nothing already filed moves. | `services/primitive_service.py:336-356` |
| `zone.update` without `parent_id` (a rename) | exempt | Name only; memberships and parent unchanged. | `:358-382` |
| `kb.create` without `member_ids` and without `kb_id`; `kb.update` without `member_ids` (a name) | exempt | Name only. Probed in an isolated database: a KB rename kept a membership added through `kb.add_member` (the legacy list is kept in step, `db/relationships.py:85-110`). | `services/primitive_service.py:243-278` |
| `kb.delete` | exempt (this audit) | The KB row tombstoned; its membership rows are not touched. | `db/primitives.py:459-468` |
| `note.create`, `note.update` (title, body, tags) | exempt (D3) | A plain edit; no placement field. | `services/primitive_service.py:65-125` |
| `note.update` of a Thought-owned note (a Thought save) | exempt (D3) | A Thought save. | `:101-107` |
| `note.delete` of a plain note | exempt (this audit) | The note tombstoned; its zone membership row is not touched. | `db/primitives.py:185-200` |
| every read (`*.read`, `*.list`, `zone.members`, `kb.members`) | no admission (XI.5) | Computation without effect; still an authenticated principal and read authority. | — |

An operation whose admission depends on an argument (`kb.create` with `member_ids` or `kb_id`, `kb.update` with `member_ids`, `zone.create` with `directory_id`, `zone.update` with `parent_id`) is decided from the validated arguments BEFORE the service acts; the descriptor declares the condition. One admission per logical operation: a KB update that renames and changes members is one operation, not two.

The four rows marked "Astra's reading" are Astra's rulings (`checks/charter-astra-r1.md` §"THE FOUR ADMISSION RULINGS"), recorded as its readings **for the owner to confirm or overrule at ratification**. The rows marked "this audit" are the brains' readings of the same rule and are ratified with the charter the same way.

### Refusal receipts

Every attempt leaves a receipt (V.2), and XI.2 names refusal as a terminal outcome. So every refusal of an admitted operation ends in a refusal receipt: a kernel refusal at submission (`kernel/broker.py:76-81`, `_refuse_attempt` at `:332-344`), an owner rejection (`:220-225`), and a DOMAIN refusal in the service after approval (the Thought filing guard `services/refinement_thought_service.py:1369-1372`, `NotFound`, `zone_name_taken`). A domain refusal never happens "before admission" for an admitted operation. Story 02 fences the unchanged membership AND the refusal receipt through both transports.

### The complete kernel path

`kernel.submit` alone is not the path: a successful submission stops at `awaiting_decision` (`kernel/broker.py:122-129`), and execution authority has its own owner and delegation checks (`kernel/broker.py:190-204`). Each admitted write runs the whole existing path. The precedent in the tree is the owner-gesture path `type_text_from_owner_gesture` (`holdspeak/desktop_typing.py:63-176`: submit, inline owner approval, claim, execute, receipt).

1. **Submission.** The service submits ONE request per logical operation under the transport's principal (`with _as_principal(principal): kernel.submit(...)`, `services/gate_service.py:34-46`; `kernel/runtime.py:235-248`), with a new operation spec per admitted operation beside the existing ones (`kernel/runtime.py:87-118`). Payload, target and arguments are fixed at admission (XI.3); supersede mints the successor id before submission so the two-row write is one immutable payload.
2. **Approval.**
   - **OWNER principal** (the Desk's HTTP session; the loopback MCP sidecar, which forwards the hub's owner token, `mcp/server.py:144-190`, and is accepted only on loopback, `web/routes/mcp_http.py:127-131`): the call IS the owner's gesture, so the service approves inline with the same principal (XI.4: "The owner's own gesture is approval"; `desktop_typing.py:117-119`). No second confirmation.
   - **AGENT principal** (a remote MCP credential): the kernel refuses a non-owner decision without delegation (`kernel/broker.py:190-204`). The operation stays HELD in `awaiting_decision`; the call returns the held handle, not the write; the owner approves or rejects it through the existing decide route (`web/routes/system/kernel_routes.py:44-66`). A live owner-approved parent run lets its child proceed (`kernel/broker.py:329-330`; `kernel/causation.py:46`). The agent's palette is NOT read as a standing approval: that would manufacture owner authority. Where main accepts an agent's desk write today, it writes it directly (the service performs no principal check, `operations.py:151-154`; palette membership decides reach, `mcp/tools.py:1164-1175`); holding it is a named behaviour change for the owner's ratification (Decisions deferred), and the compat tables state it.
3. **Execution.** After approval the operation is claimed (`kernel/executor.py:26`) and the service's real callable writes once, under the warrant. Nothing is written before approval.
4. **Terminal receipt.** `succeeded`, `refused` (with the rule by name, V.3), `failed`, or `indeterminate` (`kernel/executor.py:89`; restart recovery at `kernel/broker.py:30-33`).

**Readback.** The write's result carries `operation_id` and the terminal `receipt` (as `desktop_typing.py:163-170` does). A later read: `GET /api/kernel/read?refs=operation:<id>&view=receipt` (`web/routes/system/kernel_routes.py:24-33`; `kernel/broker.py:37-62`); an agent reads only its own operations (`:51-52`). MCP has no kernel read today, so story 02 declares ONE read operation over the same `kernel.read` for MCP (a read: no admission, XI.5). It raises the public tool count by one, reported separately from the residual set.

**The principal reaches the kernel unchanged.** It comes from the transport (`operations.py` `_TRANSPORT_PRINCIPAL` at `:151`); arguments never carry authority. "No owner-only by default" means only that no NEW owner-only refusal is added; it never lets a service decide as the owner on an agent's behalf. Whether a loopback agent that holds the owner token should BE the owner is not this phase's ruling.

**No double admission.** One kernel operation and one terminal receipt per admitted logical operation, whichever transport or alias (`desk.verb`, `desk.update`, the HTTP route) called it; supersede's two rows are one operation. A write inside an admitted operation is judged for itself (XI.1), and never admitted twice.

**Phase 5's characterization becomes a fence.** `tests/unit/test_philo5_the_loop.py:618` pins the zero today ("CHARACTERIZATION ONLY"). Story 02 replaces it with an admission fence: red on a copy of main through the real producer, green on the branch.

Authority is not admission. Owner-only authorization neither admits nor writes a receipt (`../PHASE-6-7-CHECK-ASTRA.md` finding 5).

## Discovery without repository access

D4: the closing use runs from Codex WITHOUT repository access; discovery from the catalogue alone is an acceptance criterion. The Phase 5 rehearsal did not prove it: "This proves ordinary prompts with client discovery in this repo; it does not prove discovery without repository access" (`docs/internal/philo/phase-5/his-words/rehearsal.md:49-50`). It needed 25 repository reads and 201 s to find the review-list decision (`pm/roadmap/holdspeak/BACKLOG.md:1216`). The rehearsal's root audit counted 28 completed shell commands, all repository/config reads (`rehearsal.md:61-62`). These are DIFFERENT SCOPES, not conflicting counts: 25 completed shell commands in the `decision_thought` turn plus 3 in the `import` turn = 28 over the whole run (Astra recounted the retained event logs, `checks/charter-astra-r1.md` finding 5; `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/codex/{decision_thought,import}/events.jsonl`). In the Phase 6 driver run Codex chose `door.add_item` where the job was a desk decision (`pm/roadmap/holdspeak/BACKLOG.md:1225`).

- The tool descriptions name the jobs in his words: "file a note into a zone", "find a note", "put a decision on my review list", "make my brief". Argument descriptions name where each id comes from (for example, `directory_id` from the zone list).
- Today they do not: `zone.file` reads "File a primitive in a Zone." (`holdspeak/mcp/tools.py:233`); `desk.create` reads "Create a desk primitive." (`:67-68`).
- **Acceptance (story 01):** a fence that reads ONLY the real `tools/list` answer (no source, no repository files) and maps each job phrase to its tool and argument path. This fence proves the words are present; it does not prove a model finds them.
- **Acceptance (story 04):** a launch setup that actually withholds repository access AND inherited repository instructions (story 04 names it: `codex exec` started outside the repository with `-C` an empty scratch directory, a scratch `CODEX_HOME` so no `~/.codex` project trust or config reaches the repository, no `AGENTS.md`/`CLAUDE.md` in any parent of the working directory, the MCP server pointed at the isolated hub only). The complete initial context and events are retained. The Codex event log shows zero repository, source or roadmap reads (a fence that must FAIL on the Phase 5 log); every tool choice comes from `tools/list`.

## Named atlas pairs

Existing note cases in `docs/internal/philo/graph/atlas.json` (retained; `.op` siblings minted in story 03 where the outcome is durable):

- `case.j1.first_words_keep_as_note.kept`
- `case.j11.write_a_thought.window_open`, `case.j11.thought_keep.kept`, `case.j11.write_a_thought.create_refused` (Thought-owned notes)
- `case.j11.thought_keep.receipt_time` and its `.op` in `atlas-phase3.json` (the `.op` seeds `POST /api/directories` in setup only; that is not a directory case)

NEW browser cases story 03 must mint (none exist today — `atlas.json` and `atlas-phase3.json` have no directory, KB, zone-membership, supersede or decision-status case; Astra finding 7):

- `case.p7.zone_create.visible` — a zone made; it shows on the Desk.
- `case.p7.zone_file.note_in_zone` — a note filed into a zone; it shows in the zone.
- `case.p7.zone_file.refile_moves` — a re-file moves the note (one zone per primitive).
- `case.p7.zone_unfile.note_leaves` — an unfiled note leaves the zone.
- `case.p7.kb_create.visible` — a knowledge base made; it shows on the Desk.
- `case.p7.kb_member.add_and_remove` — a reference added to a knowledge base and removed.
- `case.p7.decision_status.review_list` — a decision set to the status that puts it on his review list; it shows in the brief's visible rows on a fresh Desk read.
- `case.p7.decision_supersede.successor_visible` — a superseded decision and its successor, both readable.
- `case.p7.decision_delete.gone` — a deleted decision leaves the Desk.

Each at 1440 and 393, with an `.op` sibling for its durable outcome. The case ids are proposals; story 03 fixes them against the atlas schema. A case is minted only where the Desk shows the object today; where it does not, the case records "not on the face" and is an `op`-only pair — never a face change (Out).

## Compatibility and the residual set

The Phase 5 rules (`../phase-5-the-one-service-layer/current-phase-status.md:109-116`), verbatim:

- Residual identities are `(transport, entry point, discriminator)` where necessary — tool names are too coarse. `desk.create/get/update/list` serve several primitive kinds (`holdspeak/mcp/tools.py:554,689`).
- Retire the duplicated **decision path**, not the generic `desk.*` tools; the generic compatibility entry stays for its remaining kinds. Generated aliases reach the same declaration; paid application branches disappear in the same commit.
- Preserve names, arguments, defaults, envelopes, refusal behaviour and palette membership. Test palette refusal through dispatch (`holdspeak/mcp/tools.py:1045`) as well as catalogue filtering.
- Newly exposed import/shelf operations may raise the public tool count while the residual implementation set shrinks. These are different measurements, reported separately.

For Phase 7: the `desk.*` generic tools STAY for their other kinds (workflows, chains) with unchanged schemas. What retires is the duplicated PATH for notes, directories, kbs and the decision operations: the `getattr` branches in `_primitive_list/get/create/update/delete` (`holdspeak/mcp/tools.py:590-615`), the direct membership calls (`:864-879`), the direct `supersede_decision` call (`:1043-1044`), and the direct `_svc()` calls in the slice's routes. Each kind ships a three-state compatibility table (base main, round one, built).

## Settled between the brains

Phase 5's seven positions, carried (`../phase-5-the-one-service-layer/current-phase-status.md:133-146`): Declaration, Composition, Effects, Transport, Proof, Closing proof, Fences. Muad'Dib accepted all seven there; they bind here unchanged.

Added for this phase (Astra's check of the drafts, finding 5):

- **A finite explicit descriptor TABLE per (kind, verb) is a module, not a framework.** Each row names its real callable, schema, result, refusals, exposure and completion. No discovery framework; no universal CRUD semantics; Thought-owned notes keep their revision behaviour.
- **Owner-only is a policy change and is NOT applied by default.** Existing authority behaviour is preserved unless ratified. Today's primitive writes do not require the owner; a change needs its own named ruling.

## Exit criteria (evidence required)

- [ ] 1. Every slice operation is reachable by route, by MCP (tool and, where one exists, resource) and by the rig's `op` step, resolving to the same declared contract and the same live `PrimitiveService` within one hub (object identity in-hub; durable state across restart).
- [ ] 2. The duplicated paths are retired and the residual set shrank by the enumerated identities (33 MCP; the 3 HTTP only where the fallback left), recorded by `(transport, entry point, discriminator)`; the fence fails on a new residual identity (red on a copy of main).
- [ ] 3. The complete tool roster and `docs/generated/operations.json` are regenerated and drift-guarded.
- [ ] 4. The named pairs agree on durable outcome and refusals between the `api`/`op` path and the browser path; the new browser cases are retained at 1440 and 393; real and replayed runs retained separately.
- [ ] 5. The closing use: Astra drives "file this note into <zone> and find it" and "put this decision on my review list" from Codex WITHOUT repository access; a reopened Desk read at 1440 and 393; the filed and decided writes read back with their receipts; rehearsed, owner-reviewed shots. Never recorded as a sitting.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-7-01 | Notes and directories on the contract (and discovery) | backlog | [story-01-notes-and-directories-on-the-contract](./story-01-notes-and-directories-on-the-contract.md) | - |
| PHILO-7-02 | Membership and decisions under Article XI | backlog | [story-02-membership-and-decisions-under-article-xi](./story-02-membership-and-decisions-under-article-xi.md) | - |
| PHILO-7-03 | The atlas for the desk | backlog | [story-03-the-atlas-for-the-desk](./story-03-the-atlas-for-the-desk.md) | - |
| PHILO-7-04 | File it and find it without the repo | backlog | [story-04-file-it-and-find-it-without-the-repo](./story-04-file-it-and-find-it-without-the-repo.md) | - |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The primitive contracts and discovery | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-7-01 | feat/philo-7-01-notes-and-directories |
| Membership and decisions | 02 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-7-02 | feat/philo-7-02-membership-and-decisions |
| The atlas | 03 | Astra (Luna) | Muad'Dib | ../wt-philo-7-03 | feat/philo-7-03-the-atlas |
| The closing use | 04 | Astra (Luna) | Muad'Dib | ../wt-philo-7-04 | feat/philo-7-04-file-it-and-find-it |

Sequential: 01 → 02 → 03 → 04. `holdspeak/operations.py`, `holdspeak/mcp/tools.py` and the generated files have one shipping owner per commit.

## Where we are

2026-09-25: DRAFTED by Muad'Dib from handover XXVIII r2 (§Road B, Astra's counter-proposal adopted), Astra's check of the drafts, and the owner's D1–D4. Astra's check of this charter: RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`). r2 pays it: the hidden filing effects admitted (zone delete, KB member ids, zone moves, the Thought tombstone, create over an existing id); refusal receipts required; the complete kernel path named; D4's launch setup concrete; the 25/28 scopes stated; the estimate placed before build. Nothing is built. The owner's ratification is owed (with Astra's four readings and this audit's readings). Build starts only after Phase 6 closes (D2).

**Estimate (PROVISIONAL, placed before build authorization):** **11–15 engineering days, sequential.** Per story: 01 3–4 d; 02 4–5 d (includes the complete kernel path and the hidden filing effects); 03 3–4 d (includes the new browser cases); 04 1–2 d. Grounded on Phase 5's provisional 11–14 d (itself an estimate, not measured delivery) and its story shapes. CALIBRATED after story 01's first kind (notes) lands; the calibration is recorded here before story 02 starts.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| MISSED 3 — false uniformity: one generic row for every kind hides Thought-owned revisions, zone moves, two-row supersede | high | an explicit row per (kind, verb) naming its real callable and refusals; compat tables per kind | a descriptor whose callable is `getattr` over a kind string |
| MISSED 4 — unassigned debt: the shelf-enum drift and "attach to a meeting" | medium | shelf-enum alignment is story 01 acceptance; attach is DROPPED from the closing job (the job is file + find + review-list decision) | a story or rehearsal step that claims an attachment |
| A lexical discovery fence taken as proof that a model discovers | medium | story 01's fence proves words only; story 04's transcript (zero repository reads) is the proof | any record that cites the catalogue fence as discovery proof |
| The census does not shrink as reported | medium | report MCP and HTTP separately; a fallback that stays is MOVED, not paid | a count that includes a moved HTTP identity as paid |
| Double admission or a bypass of an admitted write | medium | one admission per logical operation in the service, whichever transport; the admission table classifies every create/update/delete by its effect | two kernel operations for one write, or a filing effect (membership or parent changed) with none |
| An admitted write stops at `awaiting_decision` and never lands | medium | the complete path (submission, approval, execution, terminal receipt) is named and fenced end to end | a write whose operation has no terminal receipt |
| Manufactured owner authority | medium | the principal reaches the kernel unchanged; an AGENT write is held, never approved as the owner | an agent-principal write approved by a principal other than the owner or a live delegation |
| An authority change slips in with the migration | medium | owner-only NOT applied; compat tables include the principal cases | a non-owner write that main accepted is refused |
| A face change creeps in through story 03's new cases | medium | cases record what the Desk shows today; "not on the face" is lawful | a web source edit in story 03 |
| Migration appetite: workflows, chains, workbench or aggregates pulled in | high | the 36 enumerated identities are the whole scope | a story touches an identity outside the table |

## Decisions made (this phase)

- 2026-09-25 — DRAFTED by Muad'Dib; the slice is Astra's counter-proposal as adopted in XXVIII r2; "attach to a meeting" dropped from the closing job — Muad'Dib.
- 2026-09-25 — r2: Astra's check (RATIFY-WITH-CONDITIONS) paid; the admission table rewritten by effect; the kernel path, readback and principal cases named; D4's launch setup concrete; the provisional estimate 11–15 d placed before build — Muad'Dib.
- 2026-09-24 night — the owner ruled D1 (desk notes next), D2 (repairs first), D3 (file or decide = admission + receipt; plain edits do not), D4 (Codex without repository access; a reopened Desk read).

## Decisions deferred

- Astra's four readings (`decision.status`, `zone.unfile`, `decision.delete`, `kb.member.add/remove`: all ADMIT) and this audit's readings (the rows marked "this audit" in the admission table): the owner confirms or overrules each at ratification.
- The AGENT-principal behaviour change: an agent's admitted desk write is HELD for the owner's decision instead of written directly (main writes it). The owner rules at ratification; if he overrules, the alternative must be a bounded delegation he grants, never an approval a service makes as the owner.
- Whether a contract refusal before submission (`unknown_operation`, `invalid_arguments`, `authority_in_arguments`, `operations.py:150`) owes a kernel refusal receipt. Unknown; Astra checks before story 02 builds.
- Whether `decision.status` gets a separately named MCP tool or stays reached through `desk.update kind=decisions`. Story 02 decides; either way the descriptor names both paths and the discovery words name the job.
- The canonical operation names (proposed above). Story 01's first commit; Astra checks.
- The owner's ratification of this charter.
