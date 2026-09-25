# PHILO-7-01 - Notes and directories on the contract

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** Phase 6 closed (the owner's D2); the owner's ratification of this charter
- **Unblocks:** PHILO-7-02
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra's check of the drafts, findings 4, 5, 7 and MISSED 3, 4; Astra's charter check r2, finding 2 and MISSED 1; the owner's D1, D4, R4

## Problem

Notes, directories (zones) and knowledge bases reach HTTP through their own routers (`holdspeak/web/routes/primitives/notes.py:43-106`, `directories.py:35-101`, `kbs.py:35-89`) and MCP through the generic `desk.*` tools, which call `getattr(service, f"create_{kind}")` over a kind string (`holdspeak/mcp/tools.py:590-615`). Two hand-wired paths to one job, 24 MCP residual identities and 3 HTTP fallback constructors (`primitives/notes.py:30-38`, `directories.py:22-30`, `kbs.py:22-30`). The kinds are not uniform: a Thought-owned note updates through `RefinementThoughtService` with expected revisions (`holdspeak/services/primitive_service.py:91-111`) and is tombstoned on delete (`:127-134`); a zone read returns `{directory, member_ids, members}` (`:323-334`); a zone update's `parent_id` uses a sentinel (`:358-382`). The tool descriptions do not name his jobs: `desk.create` reads "Create a desk primitive." (`holdspeak/mcp/tools.py:67-68`); the Phase 5 rehearsal needed 25 repository reads to find a decision job (`pm/roadmap/holdspeak/BACKLOG.md:1216`). The shelf-enum drift from Phase 5 has no owner: the MCP schema refuses an unknown state before the registry (`holdspeak/mcp/tools.py:459`) while the descriptor declares the service's refusal (`holdspeak/operations.py:421-423`; BACKLOG row at `pm/roadmap/holdspeak/BACKLOG.md:1210`).

The renames are exempt (D3; R4), but both rename implementations read placement and write that snapshot back. A KB rename reads `existing.member_ids` and replaces the membership set with it (`holdspeak/services/primitive_service.py:269-276`); a zone rename reads `existing.parent_id` and writes it back (`:366-375`). A rename that races another filing action silently reverses it. Astra reproduced both through the real service, pausing each rename after its real read and making another real call: the KB rename tombstoned a newly added `note:b`; the zone rename reversed a move from `p1` to `p2` (`checks/charter-astra-r2.md` finding 2). This is the highest owner cost Astra named (MISSED 1).

## Scope

- **In:** explicit descriptors, one row per (kind, verb), for notes, directories (zones) and kbs: create, read, update, delete, list — 15 operations in `holdspeak/operations.py`, each naming its real callable, schema, result, refusals, exposure and completion; bound at hub composition to the hub's `PrimitiveService`; HTTP routes, the `desk.*` tools for these kinds, the `desk.verb` aliases and the `holdspeak://primitives/{kind}/{id}` resource over `invoke`; the duplicated paths retired; compat tables per kind (three-state: base main, round one, built); the residual set paid by identities 2-5, 7-24, 26-27 and, where the fallback leaves, 34-36 of the phase's enumerated table; DISCOVERY: tool and argument descriptions naming the jobs; the shelf-enum alignment repair; THE RENAME REPAIR: a KB rename and a zone rename update ONLY the fields the caller named (the name), never write back a placement snapshot; renames stay exempt from admission.
- **Out:** memberships and decisions (story 02); kernel admission (story 02). Some rows here carry a filing effect the phase status's admission table marks ADMITTED (`zone.delete`; `kb.create` with `member_ids` or `kb_id`; `kb.update` with `member_ids`; `zone.create` with `directory_id`; `zone.update` with `parent_id`; the Thought-owned `note.delete`). This story moves them onto the contract with their execution UNCHANGED (the compat tables show it) and each descriptor names its admission condition; story 02 adds the admission; workflows and chains (the `desk.*` tools keep serving them unchanged); any authority change; any face change.

## Acceptance criteria

- [ ] The descriptor table is explicit: one row per (kind, verb), no `getattr` over a kind string in any contract path; Thought-owned note behaviour (expected revisions, cursors, tombstone) preserved and declared as the note rows' result and refusals; each row declares its admission condition from the admission table (exempt, or ADMITTED when a named argument is present), for story 02 to enforce.
- [ ] HTTP, MCP tools, `desk.verb` aliases and the primitive resource reach the same declaration and the same live instance within one hub (object identity in-hub; durable state across restart).
- [ ] The duplicated paths for notes, directories and kbs are retired; `desk.*` stays for workflows and chains with unchanged names, arguments, defaults, envelopes, refusals and palette membership; palette refusal tested through dispatch and through catalogue filtering.
- [ ] A three-state compat table per kind (notes, directories, kbs), green on main, green on the branch; every changed behaviour stated in full (Phase 5 story 01 form). Existing authority behaviour preserved: no owner-only refusal where main accepted.
- [ ] The residual fence: identities 2-5, 7-24, 26-27 paid (24 MCP); 34-36 paid only if the fallback construction leaves the route, else recorded as MOVED with a reason; a new identity fails (red on a copy of main); public tool count and residual set reported separately.
- [ ] `docs/generated/operations.json` and the complete tool roster regenerated and drift-guarded.
- [ ] DISCOVERY: the descriptions of the tools and arguments for this slice name the jobs in plain words ("file a note into a zone", "find a note", "make a zone", "put a decision on my review list" is named here for the words and paid in story 02); every id argument names where its value comes from. A fence reads ONLY the real `tools/list` answer (no source files) and maps each job phrase to its tool and argument path; red on main.
- [ ] Shelf-enum alignment: the MCP `monday_brief.shelf` transport and `brief.shelf.write` agree on who refuses an unknown state; real-producer red on main, green on the branch; the refused branch counts as registry reach only if it reaches the registry.
- [ ] THE RENAME REPAIR: `kb.update` with a name and no `member_ids` writes the name only and leaves every knowledge membership as the database holds it at write time; `zone.update` with a name and no `parent_id` writes the name only and leaves `parent_id` as the database holds it at write time. Real-producer INTERLEAVING fences, one per rename: pause the rename after its real read, make another real service call (`kb.member.add` of a new reference; a zone move by `parent_id` from `p1` to `p2`), let the rename finish, and assert the other action SURVIVES (the new membership live; the zone under `p2`). Both fences RED on a `git archive` copy of main (Astra's reproduction), green on the branch. No mocked reads, no injected rows. The rename stays exempt (the story 02 no-admission fence covers it); a rename that also carries `member_ids` or `parent_id` is the ADMITTED row, unchanged by this repair.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

PROVISIONAL: 3–4 engineering days (r3: the rename repair and its two interleaving fences fold in, about half a day). Calibrated after this story's first kind (notes) lands; the calibration is recorded in the phase status before story 02 starts.

## Test plan

- **Unit:** the descriptor table and binding identity; per-kind compat tables; the residual fence (red on a copy of main); palette refusal through dispatch; the catalogue-only discovery fence; the shelf-enum alignment fence; the two rename interleaving fences (red on a copy of main).
- **Integration:** the real `MeetingWebServer` hub: HTTP and `/api/mcp` calls for each kind recorded by the one registry's `invoke`; a Thought-owned note update through both transports with its revisions.
- **Manual / device:** none (story 04).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B and Astra's check of the drafts; unratified.
- 2026-09-25 — r3 (Astra's charter check r2, finding 2): the rename repair added — renames update only the requested fields; two real-producer interleaving fences, red on main.
- 2026-09-25 — r4 (Astra's charter check r3, finding 6): the rename repair and its two survival fences confirmed by Astra's independent real-service interleavings (a KB rename tombstoned a newly added `note:b`; a zone rename restored `parent_id="p1"` after a move to `p2`); genuinely plain renames stay exempt. No change to this story's scope.
