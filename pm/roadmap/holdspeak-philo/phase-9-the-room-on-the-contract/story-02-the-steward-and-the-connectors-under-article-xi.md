# PHILO-9-02 - The steward and the connectors under Article XI

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-01; the owner's answers to Q1 and Q2; **the steward lifecycle beat** (the charter's five points: pending handle, run/effect parentage, terminal receipt, stop, recovery), written as `design/steward-lifecycle-beat.md` and checked by Codex Astra before build
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F5, F8, F9, F16, F17, F18, F19 (round-two probes P1–P3); Codex Astra r1 F2, F3, F4, F7 (`checks/charter-astra-r1.md`)
- **Canvas:** none, unless Q2 (b) puts a project grant on the credential row (then a small canvas first, as Phase 7 story 02)

## Problem

- No project write is admitted through the kernel or leaves a kernel receipt (F8). The steward can post a GitHub comment and a nudge is one (egress; Article XI.1, `docs/internal/CONSTITUTION.md:169-175`).
- The steward is asynchronous: the route and the tool insert a run, return its id, and execute the phases on a daemon thread (`holdspeak/web/routes/steward.py:94`; `holdspeak/mcp/families/project.py:1554-1633`).
- `steward.nudges`, `nudge.send` and `nudge.dismiss` build the steward service with `unittest.mock.MagicMock` collaborators in product code (`holdspeak/mcp/tools.py:1177-1191`, F9).
- **No suggestion can become a watched source.** The three MCP tools fail on every call (`svc` unbound, `project.py:2044`, `:2053`, `:2058`, `:2072`, F5). A GitHub `owner/repo` reference never reaches the single-segment `{ref}` route: 404 (`holdspeak/web/routes/projects.py:608`, F16). A Jira suggestion is marked accepted before the add (`projects.py:628`); the add fails because `qualified_ref` refuses `jira:` and `github:` (`holdspeak/db/relationships.py:25`); the failure is swallowed into `accepted_no_watch` (`projects.py:633-639`); zero resources and zero watches after (F17). A successful `add_resource` writes no watch anyway (`holdspeak/services/project_service.py:3169-3284`). The routes read the table with raw SQL (`projects.py:620`, `:657`).
- Archive turns unattended runs off and pauses watches in one transaction (`project_service.py:3023-3035`, F18). An agent with a PROJECT credential and no grant turned unattended runs on and archived a project, with zero kernel rows (F19).

## Scope

- **In:** descriptors for the 20 MCP identities of the charter's enumeration (steward 5, nudges 3, watches 7, suggested sources 3, connections 2) and the 3 `SuggestedSourceService` HTTP constructors, bound to the hub's `ProjectStewardService`, `WatchService`, `SuggestedSourceService` and `ConnectionsService`; the nudges on the hub's service with its real collaborators; **source addition with a durable, truthful outcome** — an accept leaves a resource AND a watch on the Room, read back, or is refused with a named reason and the suggestion stays pending; `owner/repo` references reach the route; the route and the MCP twin reach one operation; the policy write through the service; kernel admission, one terminal receipt and refusal receipts (Phase 7 R2) for each row the charter's admission table admits, on both transports and for the rows story 01 declared, with no duplicate admission where a lower-level one exists (`watch.create` from a link, `inference.invoke` for a model draft); the steward per the lifecycle beat, each executed effect a child of its run (Article XI.2); agent writes as Q2 rules (Q2 (a): an admitted row called by an AGENT is refused `delegation_required` with a receipt); existing OWNER checks in `WatchService` and the setup service kept.
- **Out:** the provider discovery tools and the setup interview (migration deferred, still callable); the non-desk two-step terminal writes (BACKLOG "PHILO-7-02 lifecycle beat follow-ups").

## Acceptance criteria

- [ ] The 20 MCP and 3 HTTP identities leave the residual set (or MOVE with a named reason).
- [ ] Accepting the GitHub suggestion `example/payments` and the Jira suggestion `PAY-123` (minted through the real scanner) leaves a resource and a watch, read back from the database — or a named refusal with the suggestion still `pending`; never `accepted` with nothing added. The same through the MCP twin. (Red on main: 404; 200 `accepted_no_watch` with zero resources and watches — grounding P1.) Fixing `svc` alone does not meet this box.
- [ ] No `unittest.mock` import in product code under `holdspeak/`: an AST fence, red on main, with a mutation.
- [ ] The lifecycle beat's five points are fenced, recovery with a real hub restart during a run.
- [ ] Archive as the owner is one admitted operation with its receipt; the watch pause and unattended-off are inside it (red on main: P2, zero rows).
- [ ] Each admitted row is one kernel operation with one terminal receipt on HTTP and MCP; each refusal class leaves its receipt; exempt rows and reads leave none; no act is admitted twice. Fences run with an authenticated principal (handover XXIX law 5); a mutation of each turns its fence red.
- [ ] Agent behaviour as Q2 rules, fenced through dispatch with a real PROJECT credential (red on main under Q2 (a): P3 — `configure_steward(unattended_enabled=True)` and `archive` succeed with zero rows).

## Effort (not a promise)

PROVISIONAL: 3.5–4.5 engineering days, plus about 0.5 for the lifecycle beat.

## Test plan

- **Fences ship with this story** (story 05 only assembles and reruns).
- **Integration:** source-addition, admission, lifecycle and agent fences through the real hub on an isolated HOME (the Phase 7 story 02 pattern; the grounding's `probes/r2_probes.py.txt` is the diagnostic record, not a fence); the AST fence.
- **Rig:** `op` steps that read the kernel receipt for each admitted write.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. `nudge.send` was not run in the grounding (no GitHub account on the isolated HOME).
- 2026-09-27 — round two (Codex Astra r1 paid): P1–P3 reproduced; source addition as a durable outcome; the admission table; the lifecycle beat as precondition; Q2 restated.
