# PHILO-9-01 - The Room's operations on the contract (and discovery)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter (his Q0, Q1 and Q3 rulings shape this story)
- **Unblocks:** PHILO-9-02, PHILO-9-03's backend, PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F4, F6, F12, F13, F14, and the backend halves of F2 and F7; the census table there; BACKLOG "Projects on the contract"; Codex Astra r1 F1, F3, F7, MISSED 4 (`checks/charter-astra-r1.md`)
- **Canvas:** none (no face file)

## Problem

A client that knows only the catalogue cannot put a thing in a project: the only "add" verb is `project.add_suggested_source` (F4); items and resources are HTTP only (`holdspeak/web/routes/projects.py:294-325`, `:411-515`). The face makes a project through the Door (`holdspeak/web/routes/project_door.py:69`), which arms and baselines watches; MCP makes a bare project (`project.create`). The Room read says the updates and the steward are `absent · not_yet_built` after both ran (`holdspeak/services/project_service.py:510-511`, F6). `desk.needs_you` counts muted projects on MCP and not on HTTP (`holdspeak/mcp/tools.py:1077-1090` vs `projects.py:546-573`, F13). The descriptions name mechanisms, not his jobs (F12). Nothing records that he delivered an update: the face copies it (`web/src/features/project-room/update/useUpdateController.ts:163-179`), and `project_updates` has no delivery column (`holdspeak/db/schema.py:4129-4145`) (the owner's Q0 ruling: copy and confirm). A base install cannot import the catalogue (`holdspeak/operations.py:38`; `jsonschema` only in the `test` and `dev` extras, `pyproject.toml:85`, `:139`; F14). Health ignores a past-due milestone and RECEIPTS lists the Room's reads (`project_service.py:1457-1461`, `:1933`; F2, F7 backend).

## Pre-brief conditions (Codex Astra r3; settled in the charter's "Pre-brief conditions")

- **A1:** the HTTP resource routes forward `expected_revision` and `command_id` to the service (`holdspeak/web/routes/projects.py:303`, `:316`; today both are dropped — Astra: two PUTs, `expected_revision=-1`, one command id, both 200, revision 1 → 3). Fence red on main: stale revision → 409 `stale_revision`; reused command id with a different body → 409 `idempotency_conflict`; same-body replay → the recorded result.
- **A2:** the refusal codes per tool (transition includes `idempotency_conflict`) and the per-route HTTP envelopes as the charter's compatibility mapping states them; the equivalence fence uses that mapping, never message text.

## Scope

- **Prerequisite (first commit):** F14 — `jsonschema` in the base dependencies; a fence that imports `holdspeak.mcp.tools` in a clean venv built from the base dependencies only.
- **In:** descriptors in `holdspeak/operations.py` for the 18 MCP identities of the charter's enumeration (Room lifecycle 9, review 4, updates 4, `desk.needs_you` 1), bound at hub composition to the hub's `ProjectService`, `ProjectDeltaService` and `ProjectUpdateService`; the 3 HTTP constructors reach the hub's services; seven of the eight new public tools exactly as the charter's table (`project.mark_update_delivered` lands in story 02 with its admission, R4-2) "The new public tools" (names, schemas, palettes, refusals, authority; `kernel.receipt` added to `PROJECT` and `SWEEP`); the Door's create declared beside `project.create`, each admitted or exempt by its own effect (the charter's admission table; admission itself lands with story 02's kernel path, this story declares the rows); **every `ProjectService` edit of the phase**: F6, F13, and for story 03 the health and NEEDS YOU count of a past-due milestone (F2, the Q3 ruling) and RECEIPTS from the Room's writes (F7); descriptions and argument descriptions in his words (where each id comes from), the delivery words "copy for delivery" and "mark delivered", and **no description says or implies that the product sends the update**; **the delivery table** (the charter's "Delivery by copy and confirm"; the owner's "Several per update"): `project_update_deliveries` (`id`, `update_id`, `project_id`, `delivered_at` = the owner's confirmation time, `delivered_to` nullable, `operation_id`) by the additive reconcile, a repository insert (never an update or delete of a row, never a write to `project_updates`), and each update's `deliveries` list in `list_updates` and the Room read; a three-state compatibility table (base, round one, built) per operation; `docs/generated/operations.json` and the tool roster regenerated.
- **Out:** the steward, the nudges, the watches, the suggested sources and the connections (story 02); every face file (story 03); the setup interview and the provider discovery tools (migration deferred, still callable); automated send (BACKLOG); the project grant (story 07).

## Acceptance criteria

Per the charter's red-first law: behavioural red through the real hub where the defect lives; new exposure proved by equivalence; missing-symbol or unknown-tool failures are never counted.

- [ ] A clean base install imports `holdspeak.mcp.tools` (red on main: `ModuleNotFoundError: jsonschema`).
- [ ] The 18 MCP and 3 HTTP identities leave the residual set (or MOVE with a named reason); the fence fails on a new residual identity on a copy of main.
- [ ] The seven new tools this story exposes match the charter's table, which follows the service (`project.item.list` → `{items, limit, offset}`, limit clamped 1–1000; refusal codes `validation`, `not_found`, `stale_revision`, `idempotency_conflict`; the closed patch fields and vocabularies); each one's durable outcome, result body and code↔status mapping equal the HTTP route's in one hub and across a restart — the charter's compatibility mapping is the only difference, and message text is never compared.
- [ ] `kernel.receipt` is in the `PROJECT` and `SWEEP` palettes; an agent on each reads its own operation's receipt and is refused another principal's (fenced through dispatch).
- [ ] NEEDS YOU's review row says "1 proposal waiting" for one (F22; red on main: "1 proposals waiting").
- [ ] The discovery fence reads only the real `tools/list` answer and maps "make a project", "add a milestone / risk to a project", "what needs me", "draft my update", "publish my update in the Room", "copy my update for delivery" and "mark it delivered" to a tool and an argument path; no project tool's description says the product sends, emails or posts the update.
- [ ] `project.get_room` and `GET /api/projects/{id}/room` report a published update and a completed steward run (red on main: `not_yet_built`).
- [ ] With a muted project, `desk.needs_you` and `GET /api/desk/needs-you` give the same count (red on main).
- [ ] The reconcile creates `project_update_deliveries` on an existing database; the repository inserts delivery rows and has no update or delete path for them; `project_updates` is not written by a delivery (the published-update guard untouched, fenced by a mutation that writes it); two rows for one update read back in order through `list_updates` and the Room read.
- [ ] A past-due milestone turns the Room's health and appears in its NEEDS YOU read (red on main). RECEIPTS in the Room read are the Room's writes (red on main: reads).
- [ ] Existing names, arguments, envelopes and refusals are kept (the compatibility tables); palette refusal tested through dispatch.

## Effort (not a promise)

PROVISIONAL: 3–4 engineering days (the delivery record included).

## Test plan

- **Fences ship with this story** (story 05 only assembles and reruns).
- **Unit/integration:** descriptor fences; the clean-install import fence; the discovery fence over `tools/list`; Room-read, needs-you, health and receipts fences through the real hub on an isolated HOME; `scripts/residual_census.py --check` on the branch and on a copy of main.
- **Rig:** `op` steps for each new operation via `/api/mcp`, with their equivalence against the route.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
- 2026-09-27 — round seven (the owner's "Several per update"): the two columns replaced by the `project_update_deliveries` table.
- 2026-09-27 — round six (Codex Astra r4, R4-2): the delivery tool and its admission moved to story 02; this story keeps the storage, the metadata-only write and the read-backs.
- 2026-09-27 — round five (the owner's rulings): the delivery record and `project.mark_update_delivered`; the delivery words; Q3 branches removed.
- 2026-09-27 — round four (Codex Astra r3): pre-brief conditions A1 (route repair) and A2 (mapping).
- 2026-09-27 — round three (Codex Astra r2 F3 paid): the tools' contracts follow the service; own/foreign receipt fences; F22.
- 2026-09-27 — round two (Codex Astra r1 paid): F14 as prerequisite; the new tools tabled in the charter; this story owns every `ProjectService` edit; Q0 words; fences ship here.
