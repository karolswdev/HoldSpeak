# PHILO-9-07 - The project delegation grant (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** done
- **Depends on:** PHILO-9-02 (the admission path and the HTTP edge repair, B2); the owner's word on the grant's bound; **the grant lifecycle beat** (`design/project-grant-beat.md`, checked by Codex Astra before build); the grant-face canvas ratified by the owner before the face build
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** the owner's Q2 ruling (2026-09-27, verbatim: "Grant an agent a bounded project delegation, like Phase 7's filing grant. This is a bigger scope, with a new grant face and a canvas."); grounding F19 (an agent with a PROJECT credential and no grant turned unattended runs on and archived a project, zero kernel rows); BACKLOG "PHILO-7-02 canvas follow-ups" (DESK palette = ALL)
- **Canvas:** the grant's verb and chip per project on the credential row (Settings → Remote Access), at 1440 and 393, from the library species, as Phase 7 story 02's grant canvas

## Problem

Today an agent's consequential project writes need no grant (F19). After story 02 they are refused `project_delegation_required`. The owner ruled that an agent may do bounded project work under a grant he gives, as Phase 7's desk filing grant does for the desk (`holdspeak/kernel/desk.py:31-45`; `kernel_desk_delegations`, `holdspeak/db/schema.py:1839-1853`; `PUT`/`DELETE /api/settings/remote/delegations/{identity}`, `holdspeak/web/routes/mcp_http.py:387-400`; `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md`). The desk grant is one per agent with a fixed desk set; it cannot hold a per-project bound.

## Pre-brief and pre-canvas conditions (Codex Astra r4)

- **R4-1 (the beat):** the grant authorizes an agent-started run's children only as the steward beat settles it (`holdspeak/kernel/causation.py:28-40`); each child names the grant and the owner's policy as its authority basis; effects outside the grant run only where the owner's policy makes them eligible; a revoke or expiry cuts further children off, each refused child with its receipt, without manufacturing an owner principal; `project.stop_steward` only on the agent's own run (stored `requested_by`, `holdspeak/services/project_steward_service.py:455-462`), the project resolved from the stored run or update.
- **R4-2:** the refusal of `project.mark_update_delivered` for an agent **holding a real grant** is fenced here (moved from story 01).
- **R4-3 (the canvas):** the grant canvas draws a LIVE project grant with no credential row and with Remote Access OFF, with its stop action (as Phase 7's `orphans`, `holdspeak/services/desk_delegation.py:109-115`); each rendered transition is fenced.
- The sibling table is justified (Codex Astra r4 F1); reuse the terms hashing and `transition_and_receipt`; no second lifecycle engine.

## Scope

- **In:** the charter's "The project delegation grant", built as proposed there:
  - `kernel_project_delegations` (the desk table's columns plus `project_id`; one LIVE per `(agent_identity, project_id)`; the terms, including the operations, stored in the row).
  - `PROJECT_GRANT_OPERATIONS` = the bound the owner ratifies (recommended: `project.run_steward`, `project.stop_steward`, `project.publish_update`); every other admitted row owner-only, and `project.mark_update_delivered`, `project.archive` and `project.configure_steward` writes never grantable.
  - `project.delegation.grant` / `project.delegation.revoke`: owner-only, admitted with receipts, HTTP only (`PUT`/`DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}`), in no MCP palette.
  - The check at admission: an AGENT's admitted project write executes when a LIVE grant for that agent and that project names the operation, its receipt naming the delegation; otherwise `project_delegation_required` → `_expired` → `_revoked` with a refusal receipt, over MCP and HTTP.
  - The lifecycle as Phase 7's: optional `expires_at`, no default; owner revoke; a credential revoke revokes its project grants durably first (handover XXIX law 4); identity-keyed, so a grant survives a restart and a credential reissue; atomic terminal writes (`transition_and_receipt`).
  - The grant face on the credential row, as the ratified canvas draws it; DESK palette = ALL repaired on the same row (store the issued palette name, never reverse the map; BACKLOG "PHILO-7-02 canvas follow-ups").
- **Out:** widening the desk grant; a HELD state for agent writes (Phase 7 R1: none); any grant over owner-only rows.

## Acceptance criteria

- [ ] With a real Settings-issued PROJECT credential, over MCP and HTTP: each operation in the bound is refused `project_delegation_required` with a receipt without a grant (red on main: P3-style success with zero rows), and executes with a LIVE grant on that project, its receipt naming the delegation (new).
- [ ] An agent-started run's children execute only as R4-1 settles, each naming the grant and the policy; a revoke mid-run refuses the next child with a receipt and ends the run terminal; `project.stop_steward` on another actor's run in the same project is refused.
- [ ] A grant on project A does nothing on project B; an operation outside the bound stays refused with the grant; `project.mark_update_delivered`, `project.archive` and `project.configure_steward` writes are refused for an agent in every case.
- [ ] Revoke, expiry and a credential revoke end the grant (refusals change to `_revoked` / `_expired`); a restart and a credential reissue keep a LIVE grant; the lifecycle beat's interleavings fenced; a mutation of each check turns its fence red.
- [ ] `project.delegation.grant` and `revoke` are owner-only, admitted, with receipts; an agent calling them is refused.
- [ ] The grant face matches the owner-ratified canvas at 1440 and 393, including a LIVE grant with no credential row and Remote Access OFF, fenced as rendered after each change; a DESK credential reads back as DESK (red on main: ALL).

## Effort (not a promise)

PROVISIONAL: 2.5–3.5 engineering days (the beat and the canvas included).

## Test plan

- **Fences ship with this story** (story 05 only assembles and reruns).
- **Integration:** grant, refusal, lifecycle and per-project fences through the real hub on an isolated HOME with real credentials (the Phase 7 story 02 pattern; boundary fences with an authenticated principal, handover XXIX law 5).
- **Glass:** the credential row at 1440 and 393.
- **Manual / device:** the owner's review of the canvas and the shots.

## Notes

- 2026-09-28 — BUILT on `feat/philo-9-07` (the Fedaykin lane, on story 02's head `aeae7bd8`). The grant: `kernel_project_delegations` (additive; one LIVE per agent and project), `holdspeak/kernel/project.py` (the one check reuses Phase 7's `desk.check_row` and its imported terms hash; the codes `project_delegation_required` → `_expired` → `_revoked`), `holdspeak/services/project_delegation.py` (grant, revoke, the credential revoke durable first, the wire's projection), the routes `PUT`/`DELETE /api/settings/remote/delegations/{identity}/projects/{project_id}` (owner-only, admitted, HTTP only). The agent: admission by identity AND project (the project from the stored run or update), approval and the claim by the frozen basis (G1, never G2); an agent's run freezes its grant beside the policy (`authority_json.grant`); each child is admitted on the steward's trusted path (`kernel/causation.py`) and re-checked at approval and the claim, so a revoke mid-run refuses the next child with its receipt and ends the run refused; with no next child the run's own boundary or its completion ends it refused. The face as the ratified canvas draws it (set A words, `▸ Projects`, project orphans beside the desk orphans, the credential revoke's receipt); the DESK = ALL repair stores the issued palette name. The Disclosure species gets the 44 px halo at a narrow window (it is the Button's `chrome` variant, which has no `.btn` base). Evidence: [evidence-story-07](evidence-story-07.md).
- 2026-09-28 — board 11's offset (canvas r2 finding 5): in the product the Settings window's top does not move after a credential revoke at 1440 or 393 (fenced: `test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put`). The canvas's 58 px was the canvas harness's own; its cause in the harness was not traced.
- 2026-09-28 — the separate grant lifecycle beat (`design/project-grant-beat.md`, "Depends on") was not written: the build follows the steward beat's A1–A7 and Phase 7's grant beat, which this story's A-row fences carry. Muad'Dib decides whether Codex Astra's check of the built PR stands in for it.

- 2026-09-27 — the grant canvas RATIFIED by the owner ("Ratify as drawn"), after Codex Astra canvases r1 DNR → r2 DNR → r3 RATIFY: set A words `Allow run and publish` / `RUN AND PUBLISH ALLOWED` (Q4); the per-project list behind a visible `▸ Projects` (Q5). Canvas: `assets/story-07-grant-canvas/`.
- 2026-09-27 — canvases round three (Codex Astra canvases r2 finding 5): the build diagnoses one open the canvas accepted: on grant canvas board 11 at 393 the Settings window sits about 58 px lower than on the other boards (cause unknown; nothing is cut off). Find the cause during integration and fence the window's position after a credential revoke.
- 2026-09-27 — round six (Codex Astra r4): R4-1 in the beat, R4-2 the real-grant refusal of mark delivered, R4-3 the orphan and Remote-Access-OFF states on the canvas.
- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib on the owner's Q2 ruling; unratified. A new story rather than growing story 02 (Tenet 1): story 02 already carries 20 descriptors, the admission table, the steward beat and the B1/B2 repairs, and this grant has its own beat, canvas and owner review.
