# PHILO-9-02 - The steward and the connectors under Article XI

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-01; the owner's answers to Q1 and Q2
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F5, F8, F9; the census table there
- **Canvas:** none, unless Q2 (b) puts a project grant on the credential row (then a small canvas first, as Phase 7 story 02)

## Problem

No project write is admitted through the kernel or leaves a kernel receipt (F8: read back from the isolated database after creates, publishes, steward runs, a review and a link). The steward can post a GitHub comment and a nudge is a GitHub comment (egress; Article XI.1, `docs/internal/CONSTITUTION.md:169-175`). `steward.nudges`, `nudge.send` and `nudge.dismiss` build the steward service with `unittest.mock.MagicMock` collaborators in product code (`holdspeak/mcp/tools.py:1177-1191`, F9). The three suggested-source tools fail on every call (`svc` unbound, `holdspeak/mcp/families/project.py:2044`, `:2053`, `:2058`, `:2072`, F5), and the routes read the table with raw SQL (`holdspeak/web/routes/projects.py:620`, `:657`). `project.configure_steward` writes the policy table directly from the MCP branch (`project.py:1419-1552`).

## Scope

- **In:** descriptors for the 20 MCP identities of the charter's table (steward 5, nudges 3, watches 7, suggested sources 3, connections 2) and the 3 `SuggestedSourceService` HTTP constructors, bound to the hub's `ProjectStewardService`, `WatchService`, `SuggestedSourceService` and `ConnectionsService`; the nudges on the hub's service with its real collaborators; the suggested-source repair; the policy write through the service; kernel admission and one terminal receipt for each write Q1 admits, on both transports, and each effect the steward executes admitted as a child of its run (Article XI.2); refusal receipts for the Phase 7 R2 classes; agent writes as Q2 rules (under (b), the DESK palette label is repaired first, BACKLOG "PHILO-7-02 canvas follow-ups"); existing OWNER checks in `WatchService` kept.
- **Out:** the provider discovery tools and the setup interview (charter Out); the non-desk two-step terminal writes (BACKLOG "PHILO-7-02 lifecycle beat follow-ups").

## Acceptance criteria

- [ ] The 20 MCP and 3 HTTP identities leave the residual set (or MOVE with a named reason).
- [ ] The three suggested-source tools answer through the real hub (red on main: the `svc` error).
- [ ] No `MagicMock` (or other `unittest.mock` name) is imported in product code under `holdspeak/`: an AST fence, red on main.
- [ ] Each write Q1 admits is one kernel operation with one terminal receipt on HTTP and MCP; the steward's executed effects are children of its run; each refusal class leaves its receipt; reads and plain edits leave none. Fences run with an authenticated principal (handover XXIX law 5); a deliberate mutation of each turns its fence red.
- [ ] Agent behaviour as Q2 rules, fenced through dispatch.

## Effort (not a promise)

PROVISIONAL: 3–4 engineering days.

## Test plan

- **Integration:** admission fences through the real hub on an isolated HOME (the Phase 7 story 02 pattern); the nudge and suggested-source fences; the AST fence.
- **Rig:** `op` steps that read the kernel receipt for each admitted write.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. `nudge.send` was not run in the grounding (no GitHub account on the isolated HOME).
