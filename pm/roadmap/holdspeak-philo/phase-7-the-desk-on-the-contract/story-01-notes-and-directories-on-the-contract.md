# PHILO-7-01 - Notes and directories on the contract

- **Project:** holdspeak-philo
- **Phase:** 7
- **Status:** backlog
- **Depends on:** Phase 6 closed (the owner's D2); the owner's ratification of this charter
- **Unblocks:** PHILO-7-02
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra's check of the drafts, findings 4, 5, 7 and MISSED 3, 4; the owner's D1, D4

## Problem

Notes, directories (zones) and knowledge bases reach HTTP through their own routers (`holdspeak/web/routes/primitives/notes.py:43-106`, `directories.py:35-101`, `kbs.py:35-89`) and MCP through the generic `desk.*` tools, which call `getattr(service, f"create_{kind}")` over a kind string (`holdspeak/mcp/tools.py:590-615`). Two hand-wired paths to one job, 24 MCP residual identities and 3 HTTP fallback constructors (`primitives/notes.py:30-38`, `directories.py:22-30`, `kbs.py:22-30`). The kinds are not uniform: a Thought-owned note updates through `RefinementThoughtService` with expected revisions (`holdspeak/services/primitive_service.py:91-111`) and is tombstoned on delete (`:127-134`); a zone read returns `{directory, member_ids, members}` (`:323-334`); a zone update's `parent_id` uses a sentinel (`:358-382`). The tool descriptions do not name his jobs: `desk.create` reads "Create a desk primitive." (`holdspeak/mcp/tools.py:67-68`); the Phase 5 rehearsal needed 25 repository reads to find a decision job (`pm/roadmap/holdspeak/BACKLOG.md:1216`). The shelf-enum drift from Phase 5 has no owner: the MCP schema refuses an unknown state before the registry (`holdspeak/mcp/tools.py:459`) while the descriptor declares the service's refusal (`holdspeak/operations.py:421-423`; BACKLOG row at `pm/roadmap/holdspeak/BACKLOG.md:1210`).

## Scope

- **In:** explicit descriptors, one row per (kind, verb), for notes, directories (zones) and kbs: create, read, update, delete, list — 15 operations in `holdspeak/operations.py`, each naming its real callable, schema, result, refusals, exposure and completion; bound at hub composition to the hub's `PrimitiveService`; HTTP routes, the `desk.*` tools for these kinds, the `desk.verb` aliases and the `holdspeak://primitives/{kind}/{id}` resource over `invoke`; the duplicated paths retired; compat tables per kind (three-state: base main, round one, built); the residual set paid by identities 2-5, 7-24, 26-27 and, where the fallback leaves, 34-36 of the phase's enumerated table; DISCOVERY: tool and argument descriptions naming the jobs; the shelf-enum alignment repair.
- **Out:** memberships and decisions (story 02); kernel admission (story 02; no D3-set write is in this story); workflows and chains (the `desk.*` tools keep serving them unchanged); any authority change; any face change.

## Acceptance criteria

- [ ] The descriptor table is explicit: one row per (kind, verb), no `getattr` over a kind string in any contract path; Thought-owned note behaviour (expected revisions, cursors, tombstone) preserved and declared as the note rows' result and refusals.
- [ ] HTTP, MCP tools, `desk.verb` aliases and the primitive resource reach the same declaration and the same live instance within one hub (object identity in-hub; durable state across restart).
- [ ] The duplicated paths for notes, directories and kbs are retired; `desk.*` stays for workflows and chains with unchanged names, arguments, defaults, envelopes, refusals and palette membership; palette refusal tested through dispatch and through catalogue filtering.
- [ ] A three-state compat table per kind (notes, directories, kbs), green on main, green on the branch; every changed behaviour stated in full (Phase 5 story 01 form). Existing authority behaviour preserved: no owner-only refusal where main accepted.
- [ ] The residual fence: identities 2-5, 7-24, 26-27 paid (24 MCP); 34-36 paid only if the fallback construction leaves the route, else recorded as MOVED with a reason; a new identity fails (red on a copy of main); public tool count and residual set reported separately.
- [ ] `docs/generated/operations.json` and the complete tool roster regenerated and drift-guarded.
- [ ] DISCOVERY: the descriptions of the tools and arguments for this slice name the jobs in plain words ("file a note into a zone", "find a note", "make a zone", "put a decision on my review list" is named here for the words and paid in story 02); every id argument names where its value comes from. A fence reads ONLY the real `tools/list` answer (no source files) and maps each job phrase to its tool and argument path; red on main.
- [ ] Shelf-enum alignment: the MCP `monday_brief.shelf` transport and `brief.shelf.write` agree on who refuses an unknown state; real-producer red on main, green on the branch; the refused branch counts as registry reach only if it reaches the registry.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

Not yet grounded. Re-estimated after this story's first kind (notes) lands.

## Test plan

- **Unit:** the descriptor table and binding identity; per-kind compat tables; the residual fence (red on a copy of main); palette refusal through dispatch; the catalogue-only discovery fence; the shelf-enum alignment fence.
- **Integration:** the real `MeetingWebServer` hub: HTTP and `/api/mcp` calls for each kind recorded by the one registry's `invoke`; a Thought-owned note update through both transports with its revisions.
- **Manual / device:** none (story 04).

## Notes

- 2026-09-25 — drafted by Muad'Dib from handover XXVIII r2 §Road B and Astra's check of the drafts; unratified.
