# PHILO-9-02 - The steward and the connectors under Article XI

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** done
- **Depends on:** PHILO-9-01; the owner's Q1 ruling (by effect); **[the steward lifecycle beat](../../../../docs/internal/philo/phase-9/steward-beat/README.md)** (the charter's five points, B2 and R4-1), authored by Astra and checked by Muad'Dib before build; B1 remains a separate brief condition
- **Unblocks:** PHILO-9-07, PHILO-9-05, PHILO-9-06
- **Owner:** implementation: Muad'Dib's lane (Fedaykin, Opus 5.5), Codex Astra checks; prerequisite design beat: Astra, Muad'Dib checks (owner's lane assignment, 2026-09-27)
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F5, F8, F9, F16, F17, F18, F19 (round-two probes P1–P3); Codex Astra r1 F2, F3, F4, F7 (`checks/charter-astra-r1.md`)
- **Canvas:** none for this story's kernel work; the Connections face under B1 needs one only if it changes beyond words and chips. The project grant's face is story 07's canvas.

## Problem

- No project write is admitted through the kernel or leaves a kernel receipt (F8). The steward can post a GitHub comment and a nudge is one (egress; Article XI.1, `docs/internal/CONSTITUTION.md:169-175`).
- The steward is asynchronous: the route and the tool insert a run, return its id, and execute the phases on a daemon thread (`holdspeak/web/routes/steward.py:94`; `holdspeak/mcp/families/project.py:1554-1633`).
- `steward.nudges`, `nudge.send` and `nudge.dismiss` build the steward service with `unittest.mock.MagicMock` collaborators in product code (`holdspeak/mcp/tools.py:1177-1191`, F9).
- **No suggestion can become a watched source.** The three MCP tools fail on every call (`svc` unbound, `project.py:2044`, `:2053`, `:2058`, `:2072`, F5). A GitHub `owner/repo` reference never reaches the single-segment `{ref}` route: 404 (`holdspeak/web/routes/projects.py:608`, F16). A Jira suggestion is marked accepted before the add (`projects.py:628`); the add fails because `qualified_ref` refuses `jira:` and `github:` (`holdspeak/db/relationships.py:25`); the failure is swallowed into `accepted_no_watch` (`projects.py:633-639`); zero resources and zero watches after (F17). A successful `add_resource` writes no watch anyway (`holdspeak/services/project_service.py:3169-3284`). The routes read the table with raw SQL (`projects.py:620`, `:657`).
- The steward's run records `compare.review_id: ""` although COMPARE opened a review: `_phase_compare` reads `review.get("id")` (`holdspeak/services/project_steward_service.py:869`); the producer returns `review_id` (`holdspeak/services/project_delta_service.py:1848`). Found by Codex Astra r2 on a real hub (F20).
- `connection.list` probes GitHub authentication and persists its state through `_github_entry` (`holdspeak/services/connections_service.py:113`, `:154-177`), and the Door's count fetches GitHub/Jira snapshots (`holdspeak/services/project_door_service.py:146`); neither is admitted (F21).
- Proposal Defer and Dismiss are decisions: Dismiss records `decided_by_ref`, sets `dismissed` and stops recurrence; Defer records the decision and when it returns (`project_delta_service.py:988`, `:1012`, `:1292`).
- Archive turns unattended runs off and pauses watches in one transaction (`project_service.py:3023-3035`, F18). An agent with a PROJECT credential and no grant turned unattended runs on and archived a project, with zero kernel rows (F19).

## Pre-brief conditions (Codex Astra r3; settled in the charter's "Pre-brief conditions")

- **B1 — the connection read contract.** GitHub, Jira and Confluence rows cached, each with its own checked-at time and age, and a truthful "never checked" state (not "Off" / "Not set up", `web/src/pages/cores/connections/api.ts:65`); Calendar and Models stay live local reads (`holdspeak/services/connections_service.py:392`, `:431`); Confluence Recheck gets a real probe that stores its state and time — a repair: today it makes no subprocess call (Astra) — or its Recheck is withheld; the affected callers are the Connections face, the Door's source rows and the setup interview's annotations (`holdspeak/services/project_setup_service.py:1431`). This story owns the Connections face (`web/src/pages/cores/connections/ConnectionsPane.tsx`: the one-newest-time footer at `:502`, `:509`) and its fences; a canvas first if the face changes beyond words and chips (UX-CANON §A.2).
- **B2 — the HTTP edge refusal.** Today the central HTTP gate answers 403 `principal_right_required` before any operation runs (`holdspeak/principals.py:354`, `holdspeak/web_server.py:655`; Astra: Door count, Door create with sources and GitHub Recheck with a real PROJECT credential, zero kernel rows). Repair the boundary so an identifiable consequential request from an authenticated agent reaches its declared operation's refusal (`project_delegation_required` with a receipt) — or, once story 07 lands, executes under a LIVE project grant; reads, exempt edits, unknown routes and unauthenticated requests stay protocol refusals with no receipt (Phase 7's line).

## Pre-brief conditions (Codex Astra r4)

- **R4-1:** the steward beat settles agent-started children (`holdspeak/kernel/causation.py:28-40` refuses an agent's child without a live owner continuation): how the agent's grant (story 07) and the owner's policy authorize each child, including effects outside the grant (`holdspeak/services/project_steward_service.py:1313` passes the initiator into `decide_proposal`); the revoke/expiry cutoff without manufacturing an owner principal; `project.stop_steward` bound to the stored `requested_by` (`:455-462`), the project resolved from the stored run.
- **R4-2:** `project.mark_update_delivered` and `POST /api/updates/{id}/delivered` land here with their admission (story 01 supplies the `project_update_deliveries` table and the read-backs).

## The routes and tools this story admits or refuses (Codex required it; the implementation brief, 2026-09-28)

Grounded on main `d05e0eb5` (route declarations by file:line). "Admitted" = one kernel operation and one terminal receipt; an AGENT (PROJECT credential) is refused `project_delegation_required` with a receipt until story 07's grant names the operation. "Conditional" = admitted for the form the admission table names, exempt for the other form. The B2 edge gives exactly the admitted and conditional rows below `AGENT_SUBMIT` in `required_right` (`holdspeak/principals.py:296`), by exact method and pattern; no prefix. A conditional route's adapter re-applies the OWNER right to its exempt form before any service call (a protocol refusal, no receipt). Every other row keeps today's edge right.

**HTTP, admitted (edge `AGENT_SUBMIT`):**

| Method and pattern | Declaration | Operation | Admission |
|---|---|---|---|
| `DELETE /api/projects/{project_id}` | `holdspeak/web/routes/projects.py:281` | `project.archive` | admitted (story 01 row, enforced here) |
| `POST /api/projects/{project_id}/meetings/{meeting_id}` | `projects.py:390` | `project.link` | admitted; `watch.create` stays its child |
| `DELETE /api/projects/{project_id}/meetings/{meeting_id}` | `projects.py:404` | `project.unlink` | admitted |
| `PUT /api/projects/{project_id}/resources/{resource_ref:path}` | `projects.py:335` | `project.resource.add` | admitted |
| `DELETE /api/projects/{project_id}/resources/{resource_ref:path}` | `projects.py:357` | `project.resource.remove` | admitted |
| `POST /api/projects/{project_id}/reviews/{review_id}/proposals/{proposal_id}/decide` | `holdspeak/web/routes/project_reviews.py:109` | `project.decide_proposal` | admitted, all four verbs |
| `POST /api/projects/{project_id}/reviews/{review_id}/accept` | `project_reviews.py:151` | `project.accept_review` | admitted |
| `POST /api/updates/{update_id}/publish` | `holdspeak/web/routes/project_updates.py:175` | `project.publish_update` | admitted (grant set, story 07) |
| `POST /api/updates/{update_id}/delivered` | new, `project_updates.py` | `project.mark_update_delivered` | admitted; owner-only (never granted) |
| `POST /api/projects/door/count` | `holdspeak/web/routes/project_door.py:40` | `project.door.count` (new row, HTTP only) | admitted (egress) |
| `PUT /api/projects/{project_id}/steward/policy` | `holdspeak/web/routes/steward.py:224` | `project.configure_steward` (write form) | admitted |
| `POST /api/projects/{project_id}/steward/runs` | `steward.py:62` | `project.run_steward` | admitted (grant set, story 07) |
| `POST /api/steward/runs/{run_id}/stop` | `steward.py:190` | `project.stop_steward` | admitted (grant set, story 07) |
| `POST /api/steward/trigger` | `steward.py:403` | `project.steward.trigger` | admitted |
| `POST /api/nudges/{step_id}/send` | `steward.py:454` | `nudge.send` | admitted (egress) |
| `POST /api/watches/{watch_id}/test` | `holdspeak/web/routes/watches.py:119` | `project.watch.test` | admitted (egress) |
| `POST /api/watches/{watch_id}/evaluate` | `holdspeak/web/routes/providers.py:572` | `project.watch.evaluate` | admitted (egress) |
| `PUT /api/watches/{watch_id}/rules` | `watches.py:229` | `project.watch.set_rules` | admitted |
| `POST /api/watches/{watch_id}/pause` | `watches.py:163` | `project.watch.pause` | admitted |
| `POST /api/watches/{watch_id}/resume` | `watches.py:185` | `project.watch.resume` | admitted |
| `POST /api/watches/{watch_id}/retire` | `watches.py:207` | `project.watch.retire` | admitted |
| `PATCH /api/watches/{watch_id}` | `watches.py:89` | `project.watch.update` (new row, HTTP only; the charter's "HTTP capability exceptions") | admitted (changes what may act) |
| `POST /api/watches/{watch_id}/baseline` | `watches.py:141` | `project.watch.baseline` (new row, HTTP only; same table) | admitted (egress) |
| `POST /api/projects/{project_id}/suggested-sources/{ref:path}/add` | `projects.py:629` (today `{ref}`, one segment: F16) | `project.add_suggested_source` | admitted (filing; arms egress) |

**HTTP, conditional (edge `AGENT_SUBMIT`; the adapter re-applies OWNER to the exempt form):**

| Method and pattern | Declaration | Operation | Admitted form / exempt form |
|---|---|---|---|
| `POST /api/projects/door` | `project_door.py:71` | `project.door.create` | a non-empty `sources` / a bare create |
| `POST /api/connections/{provider}/recheck` | `holdspeak/web/routes/connections.py:50` | `connection.recheck` | `provider` in {`github`, `jira`, `confluence`} / {`calendar`, `models`} |

**HTTP, reads and exempt edits through the registry (edge right unchanged: OWNER; no operation of their own):** `GET /api/projects/{project_id}/steward/policy` (`steward.py:207`, `project.configure_steward` read form); `GET /api/steward/runs/{run_id}` (`steward.py:169`, `project.get_steward_run`); `GET /api/projects/{project_id}/nudges` (`steward.py:441`, `steward.nudges`); `POST /api/nudges/{step_id}/dismiss` (`steward.py:480`, `nudge.dismiss`, exempt); `GET /api/watches/{watch_id}` (`watches.py:73`, `project.watch.inspect`); `GET /api/projects/{project_id}/suggested-sources` (`projects.py:615`, `project.suggested_sources`); `POST /api/projects/{project_id}/suggested-sources/{ref:path}/dismiss` (`projects.py:668`, `project.dismiss_suggested_source`, exempt); `GET /api/connections` (`connections.py:32`, `connection.list`, a cached read under B1). Story 01's exempt rows keep their routes and rights (`project.create`, `project.update`, `project.restore`, `project.open_review`, `project.draft_update`, `project.update_draft`, the item routes) and gain no operation.

**Unchanged and out (named so no edge map guesses them):** `GET /api/projects/{project_id}/steward/runs` (`steward.py:151`, history read); `GET /api/watches`, `GET /api/projects/{project_id}/watches` (`watches.py:40`, `:56`); `POST /api/updates/{update_id}/regenerate` (`project_updates.py:142`: exempt, its model call keeps `inference.invoke`); `GET /api/updates/{update_id}/markdown` (`project_updates.py:205`, copy for delivery: a read); the provider routes `providers.py:100-536` (the `provider.*` migration is deferred; their GitHub/Jira/Confluence recheck routes stay OWNER at the edge and are BACKLOG debt, "PHILO-9 charter follow-ups"); the setup interview routes.

**MCP tools (dispatch through the one registry; palette unchanged; each admitted row's refusal carries its receipt):**

- Admitted: `project.archive`, `project.link`, `project.unlink`, `project.decide_proposal`, `project.accept_review`, `project.publish_update`, `project.resource.add`, `project.resource.remove` (story 01's rows, enforced here); `project.run_steward`, `project.stop_steward`, `project.steward.trigger`, `nudge.send`, `project.watch.test`, `project.watch.evaluate`, `project.watch.set_rules`, `project.watch.pause`, `project.watch.resume`, `project.watch.retire`, `project.add_suggested_source`, `project.mark_update_delivered` (new public tool).
- Conditional: `project.configure_steward` (admitted when any write field is present; a read otherwise); `connection.recheck` (admitted for `github`, `jira`, `confluence`; exempt for `calendar`, `models`).
- Reads and exempt edits (no operation of their own): `project.get_steward_run`, `steward.nudges`, `nudge.dismiss`, `project.watch.inspect`, `project.suggested_sources`, `project.dismiss_suggested_source`, `connection.list`; story 01's exempt and read rows.
- Out, unchanged: `provider.*` (13) and `project.setup.*` (10), still callable, migration deferred.

**Internal (no transport, never grantable):** `project.steward.effect` (the beat §5: one child per executed policy slot that has no admitted operation of its own), whose children are the existing `project.decide_proposal` and `inference.invoke` where the slot uses them.

## B1 settled: the connection read contract (2026-09-28)

- **GitHub, Jira, Confluence rows in `connection.list` are cached reads.** Each row returns the state stored by the last real probe, with that row's own `last_checked_at` (the stored `watch_provider_connections.last_checked_at`, `holdspeak/services/github_provider.py:256-284`, the Jira and Confluence `_persist_connection`) and `checked_age_seconds` computed from it. A provider or connection with no stored check returns the state `never_checked` and `last_checked_at: null`, not `not_configured` ("Off" / "Not set up"). `connection.list` makes no `gh`, `acli` or network call (today `_github_entry` runs `connection_status`, `holdspeak/services/connections_service.py:154-177`, and each read stamps `datetime.now()` as its check time, `:172`, `:216`, `:227`, `:294`).
- **Calendar and Models stay live local reads** (`connections_service.py:392`, `:431`): configuration and assignment are read now; no egress; `last_checked_at` stays null for them because nothing is checked remotely, and the face shows no age for them.
- **The probe lives only in `connection.recheck`**, admitted for `github`, `jira`, `confluence` (egress), exempt for `calendar`, `models`.
- **Confluence Recheck gets a real probe** (not withheld): the adapter already has `connection_status(principal, ref)`, which runs `acli` under its lock and persists the state and time (`holdspeak/services/confluence_provider.py:228`, `:271`, `:453`); `ConnectionsService.recheck("confluence")` calls it for the named connection or for every stored one, as Jira does (`connections_service.py:249-275`). Today it only re-reads rows (`:135`).
- **Every consumer of the List, named:** (1) the Connections face, `web/src/pages/cores/connections/ConnectionsPane.tsx` and its decoder `web/src/pages/cores/connections/api.ts` (`decodeState` at `:65` learns `never_checked`; each card shows its own row's age or "Never checked" as words in its existing chip line; the one-newest-time footer at `ConnectionsPane.tsx:502-509` stops being the only time); (2) the Door's source rows, `web/src/features/project-room/door/useDoorController.ts:9`, `:98-111`, `:194-209` (reads `state` and `connections[]`; `never_checked` reads as not yet connected, and the Door's own count stays admitted separately); (3) the setup interview's annotations, `holdspeak/services/project_setup_service.py:1431` (reads `state` and `account` only; it gets the cached state, which is the point: the interview's migration is deferred and it must not probe); (4) the parked setup face `web/src/features/project-room/_parked/setup/` (parked, not routed; it decodes through the same `api.ts`). No other caller of `list_tools` or `GET /api/connections` exists (`grep` over `holdspeak/` and `web/src/`).
- **The face change is words and chips on the existing cards only** (the age string, "Never checked", the Confluence Recheck now real). If the build needs a new element or layout, the lane stops and reports: a canvas is owed first (UX-CANON §A.2).

## Scope

- **In:** descriptors for the 20 MCP identities of the charter's enumeration (steward 5, nudges 3, watches 7, suggested sources 3, connections 2) and the 3 `SuggestedSourceService` HTTP constructors, bound to the hub's `ProjectStewardService`, `WatchService`, `SuggestedSourceService` and `ConnectionsService`; the nudges on the hub's service with its real collaborators; **source addition with a durable, truthful outcome** — an accept leaves a resource AND a watch on the Room, read back, or is refused with a named reason and the suggestion stays pending; `owner/repo` references reach the route; the route and the MCP twin reach one operation; the policy write through the service; **the steward's review-id repair** (F20: the run's COMPARE records the review it opened); **`connection.list` as a cached read** (each provider's last stored state and check time, no probe; the probe only in `connection.recheck`, admitted for github/jira/confluence, exempt for calendar/models); the Door's count admitted on its route (egress); all four `decide_proposal` verbs admitted (story 01 declared the rows; this story lands the kernel path); kernel admission, one terminal receipt and refusal receipts (Phase 7 R2) for each row the charter's admission table admits, on both transports and for the rows story 01 declared, with no duplicate admission where a lower-level one exists (`watch.create` from a link, `inference.invoke` for a model draft); the steward per the lifecycle beat, each executed effect a child of its run (Article XI.2); agent writes per the owner's Q2 ruling: an admitted row called by an AGENT is refused `project_delegation_required` with a receipt (story 07 adds the grant that lets the bounded rows execute; this story lands the refusal path and the check point the grant plugs into); existing OWNER checks in `WatchService` and the setup service kept; **`project.mark_update_delivered`** (tool and route, one declared operation, each mark admitted with its own receipt, owner-only; `update_not_published`).
- **Out:** the provider discovery tools and the setup interview (migration deferred, still callable); the non-desk two-step terminal writes (BACKLOG "PHILO-7-02 lifecycle beat follow-ups").

## Acceptance criteria

- [x] The 20 MCP and 3 HTTP identities leave the residual set (or MOVE with a named reason).
- [x] Accepting the GitHub suggestion `example/payments` and the Jira suggestion `PAY-123` (minted through the real scanner) leaves a resource and a watch, read back from the database — or a named refusal with the suggestion still `pending`; never `accepted` with nothing added. The same through the MCP twin. (Red on main: 404; 200 `accepted_no_watch` with zero resources and watches — grounding P1.) Fixing `svc` alone does not meet this box.
- [x] No `unittest.mock` import in product code under `holdspeak/`: an AST fence, red on main, with a mutation.
- [x] A steward run's recorded COMPARE `review_id` equals the review `ProjectDeltaService.open_review` returned in the same run, through the real producer on a real hub (red on main: `""`, Codex Astra r2 run `pstrun_aee671c2319c4d00ad51d15dae12024a`).
- [x] `connection.list` makes no provider call for GitHub, Jira or Confluence (a fence counts provider calls; red on main), returns each remote row's own checked-at time and "never checked" when there is none, and still reads Calendar and Models live; the Connections face shows each row's age and "never checked" at 1440 and 393 (red on main: one newest time; "Off"); Confluence Recheck makes a real probe and stores its time (red on main: zero calls, `last_checked_at` null) or its control is withheld; `connection.recheck` for github/jira/confluence is admitted with its receipt, for calendar/models is not; the Door's count is admitted.
- [x] Each of `accept`, `edit_accept`, `defer`, `dismiss` is one admitted operation with its receipt; an agent without a grant naming it is refused `project_delegation_required` for each (red on main: accepted without a row).
- [x] The lifecycle beat's five points are fenced, recovery with a real hub restart during a run; an agent's `project.stop_steward` on another actor's run in the same project is refused (R4-1).
- [x] Each mark of a published update is one admitted operation with its own receipt on MCP and HTTP and appends one `project_update_deliveries` row whose `operation_id` is that operation; `delivered_at` equals the confirmation time; two marks give two rows and two receipts; a draft is refused `update_not_published`; an agent without a grant is refused `project_delegation_required` with a receipt (a new capability: no red claimed; readbacks and a mutation).
- [x] Delivery idempotency (Codex Astra r5): a repeat with the same principal, `command_id` and payload returns the original row, `delivered_at`, operation and receipt (no second row); the same key with a changed payload is refused `idempotency_conflict`; a new key to the same recipient makes a second row; an MCP call without `command_id` makes a new delivery. Fenced for two concurrent requests with one key (one row), and for a replay after a real hub restart.
- [x] The delivery row's `operation_id` is `NOT NULL UNIQUE` and references `kernel_operations(operation_id)`, set from the execution context; `project_id` comes from the stored update (a call naming another project cannot change it); no cascade delete. The insert, the terminal state and the receipt commit in one transaction through `holdspeak/kernel/journal_atomic.py` (`transition_and_receipt`): a failure injected after the insert leaves no row, no terminal state and no receipt (rollback fence), and a replay after that failure succeeds once.
- [x] The discovery fence (`tests/unit/test_philo9_discovery.py`) maps "mark it delivered" to `project.mark_update_delivered`: its strict expected failure turns green and its mark is removed (moved here from story 01 by Muad'Dib's ruling on PR #680, 2026-09-27, R4-2).
- [x] Archive as the owner is one admitted operation with its receipt; the watch pause and unattended-off are inside it (red on main: P2, zero rows).
- [x] Each admitted row is one kernel operation with one terminal receipt on HTTP and MCP; each refusal class leaves its receipt; an exempt row or a read adds no operation of its own (a lower-level effect it carries keeps its own admission); no act is admitted twice. Fences run with an authenticated principal (handover XXIX law 5); a mutation of each turns its fence red.
- [x] Over HTTP, a real Settings-issued PROJECT credential calling Door count, Door create with sources and GitHub Recheck is refused `project_delegation_required` with a receipt (red on main: 403 `principal_right_required`, zero kernel rows); a read, an exempt edit and an unknown route still answer as protocol refusals with no receipt.
- [x] Without a grant, an agent's admitted writes are refused, fenced through dispatch with a real PROJECT credential (red on main: P3 — `configure_steward(unattended_enabled=True)` and `archive` succeed with zero rows).

## Effort (not a promise)

PROVISIONAL: 3.5–4.5 engineering days, plus about 0.5 for the lifecycle beat.

## Test plan

- **Fences ship with this story** (story 05 only assembles and reruns).
- **Integration:** source-addition, admission, lifecycle and agent fences through the real hub on an isolated HOME (the Phase 7 story 02 pattern; the grounding's `probes/r2_probes.py.txt` is the diagnostic record, not a fence); the AST fence.
- **Rig:** `op` steps that read the kernel receipt for each admitted write.

## Notes

- 2026-09-28 — BUILT by the Fedaykin lane (Opus 5.5): every criterion proved in `evidence-story-02.md` (the criteria table maps each to its fences, red on an export of main `d05e0eb5`, and 28 mutations, all caught). Residual 263 -> 240; public tools 236 -> 237. The carried same-key race is paid as a class (law 9). Not built, on the BACKLOG ("PHILO-9 charter follow-ups"): a model draft's `inference.invoke` as the `draft_update` child, the child deadline clamp, `run_once` admission. Codex Astra checks the built PR.
- 2026-09-28 — carried from PHILO-9-01 (Codex Astra r3, MISSED): the same-key concurrency race in the Room's command replay: `ProjectService._check_idempotency` reads the command before the write's transaction and `_record_command` writes `ON CONFLICT(id) DO UPDATE`, so two callers that both find a key absent both write (two revisions and change rows; for DELETE the first answers true, the second false, and the replay then answers false) (`holdspeak/services/project_service.py` `add_resource`, `remove_resource`, `_record_command`). Inherited: it reproduces on main `ffbeb04b` (Codex Astra r3 on PR #680, MISSED; `checks/story-01-built-astra-r3.md` finding 3). **Carry before claiming thread-safe retries**: story 02's execution work (the kernel path, the delivery idempotency fenced for two concurrent requests with one key) must make command ownership exclusive before any retry is called thread-safe. BACKLOG row: "PHILO-9 charter follow-ups".
- 2026-09-27 — steward design beat linked at its assigned `docs/internal/philo/phase-9/steward-beat/README.md` home; Astra authors and Muad'Dib checks the design. Implementation ownership and story status unchanged. B1 remains separately required before the implementation brief.

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. `nudge.send` was not run in the grounding (no GitHub account on the isolated HOME).
- 2026-09-27 — round eight (Codex Astra r5): delivery idempotency, the omitted-key rule, the enforced operation link and one-transaction persistence, with their fences.
- 2026-09-27 — round seven (the owner's "Several per update"): each mark its own row and receipt; `already_delivered` dropped.
- 2026-09-27 — round six (Codex Astra r4): R4-1 in the beat; mark delivered lands here with its admission (R4-2).
- 2026-09-27 — round five (the owner's rulings): the refusal code is `project_delegation_required`; the grant itself moves to story 07.
- 2026-09-27 — round four (Codex Astra r3): pre-brief conditions B1 (the connection read contract, Confluence probe, the Connections face) and B2 (the HTTP edge refusal).
- 2026-09-27 — round three (Codex Astra r2 paid): the review-id repair (F20) with a real-producer fence; `connection.list` cached; the Door count and all four proposal decisions admitted.
- 2026-09-27 — round two (Codex Astra r1 paid): P1–P3 reproduced; source addition as a durable outcome; the admission table; the lifecycle beat as precondition; Q2 restated.
