# PHILO-9-02 - The steward and the connectors under Article XI

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-01; the owner's Q1 ruling (by effect); **the steward lifecycle beat** (the charter's five points: pending handle, run/effect parentage, terminal receipt, stop, recovery), written as `design/steward-lifecycle-beat.md` and checked by Codex Astra before build
- **Unblocks:** PHILO-9-07, PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
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

## Scope

- **In:** descriptors for the 20 MCP identities of the charter's enumeration (steward 5, nudges 3, watches 7, suggested sources 3, connections 2) and the 3 `SuggestedSourceService` HTTP constructors, bound to the hub's `ProjectStewardService`, `WatchService`, `SuggestedSourceService` and `ConnectionsService`; the nudges on the hub's service with its real collaborators; **source addition with a durable, truthful outcome** — an accept leaves a resource AND a watch on the Room, read back, or is refused with a named reason and the suggestion stays pending; `owner/repo` references reach the route; the route and the MCP twin reach one operation; the policy write through the service; **the steward's review-id repair** (F20: the run's COMPARE records the review it opened); **`connection.list` as a cached read** (each provider's last stored state and check time, no probe; the probe only in `connection.recheck`, admitted for github/jira/confluence, exempt for calendar/models); the Door's count admitted on its route (egress); all four `decide_proposal` verbs admitted (story 01 declared the rows; this story lands the kernel path); kernel admission, one terminal receipt and refusal receipts (Phase 7 R2) for each row the charter's admission table admits, on both transports and for the rows story 01 declared, with no duplicate admission where a lower-level one exists (`watch.create` from a link, `inference.invoke` for a model draft); the steward per the lifecycle beat, each executed effect a child of its run (Article XI.2); agent writes per the owner's Q2 ruling: an admitted row called by an AGENT is refused `project_delegation_required` with a receipt (story 07 adds the grant that lets the bounded rows execute; this story lands the refusal path and the check point the grant plugs into); existing OWNER checks in `WatchService` and the setup service kept.
- **Out:** the provider discovery tools and the setup interview (migration deferred, still callable); the non-desk two-step terminal writes (BACKLOG "PHILO-7-02 lifecycle beat follow-ups").

## Acceptance criteria

- [ ] The 20 MCP and 3 HTTP identities leave the residual set (or MOVE with a named reason).
- [ ] Accepting the GitHub suggestion `example/payments` and the Jira suggestion `PAY-123` (minted through the real scanner) leaves a resource and a watch, read back from the database — or a named refusal with the suggestion still `pending`; never `accepted` with nothing added. The same through the MCP twin. (Red on main: 404; 200 `accepted_no_watch` with zero resources and watches — grounding P1.) Fixing `svc` alone does not meet this box.
- [ ] No `unittest.mock` import in product code under `holdspeak/`: an AST fence, red on main, with a mutation.
- [ ] A steward run's recorded COMPARE `review_id` equals the review `ProjectDeltaService.open_review` returned in the same run, through the real producer on a real hub (red on main: `""`, Codex Astra r2 run `pstrun_aee671c2319c4d00ad51d15dae12024a`).
- [ ] `connection.list` makes no provider call for GitHub, Jira or Confluence (a fence counts provider calls; red on main), returns each remote row's own checked-at time and "never checked" when there is none, and still reads Calendar and Models live; the Connections face shows each row's age and "never checked" at 1440 and 393 (red on main: one newest time; "Off"); Confluence Recheck makes a real probe and stores its time (red on main: zero calls, `last_checked_at` null) or its control is withheld; `connection.recheck` for github/jira/confluence is admitted with its receipt, for calendar/models is not; the Door's count is admitted.
- [ ] Each of `accept`, `edit_accept`, `defer`, `dismiss` is one admitted operation with its receipt; an agent without a grant naming it is refused `project_delegation_required` for each (red on main: accepted without a row).
- [ ] The lifecycle beat's five points are fenced, recovery with a real hub restart during a run.
- [ ] Archive as the owner is one admitted operation with its receipt; the watch pause and unattended-off are inside it (red on main: P2, zero rows).
- [ ] Each admitted row is one kernel operation with one terminal receipt on HTTP and MCP; each refusal class leaves its receipt; an exempt row or a read adds no operation of its own (a lower-level effect it carries keeps its own admission); no act is admitted twice. Fences run with an authenticated principal (handover XXIX law 5); a mutation of each turns its fence red.
- [ ] Over HTTP, a real Settings-issued PROJECT credential calling Door count, Door create with sources and GitHub Recheck is refused `project_delegation_required` with a receipt (red on main: 403 `principal_right_required`, zero kernel rows); a read, an exempt edit and an unknown route still answer as protocol refusals with no receipt.
- [ ] Without a grant, an agent's admitted writes are refused, fenced through dispatch with a real PROJECT credential (red on main: P3 — `configure_steward(unattended_enabled=True)` and `archive` succeed with zero rows).

## Effort (not a promise)

PROVISIONAL: 3.5–4.5 engineering days, plus about 0.5 for the lifecycle beat.

## Test plan

- **Fences ship with this story** (story 05 only assembles and reruns).
- **Integration:** source-addition, admission, lifecycle and agent fences through the real hub on an isolated HOME (the Phase 7 story 02 pattern; the grounding's `probes/r2_probes.py.txt` is the diagnostic record, not a fence); the AST fence.
- **Rig:** `op` steps that read the kernel receipt for each admitted write.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. `nudge.send` was not run in the grounding (no GitHub account on the isolated HOME).
- 2026-09-27 — round five (the owner's rulings): the refusal code is `project_delegation_required`; the grant itself moves to story 07.
- 2026-09-27 — round four (Codex Astra r3): pre-brief conditions B1 (the connection read contract, Confluence probe, the Connections face) and B2 (the HTTP edge refusal).
- 2026-09-27 — round three (Codex Astra r2 paid): the review-id repair (F20) with a real-producer fence; `connection.list` cached; the Door count and all four proposal decisions admitted.
- 2026-09-27 — round two (Codex Astra r1 paid): P1–P3 reproduced; source addition as a durable outcome; the admission table; the lifecycle beat as precondition; Q2 restated.
