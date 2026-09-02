# Phase 165 - Project Rooms: The MCP Family (P6)

- **Project:** holdspeak
- **Status:** in-progress
- **Chartered:** 2026-09-02 off main `e7b45a5b` (164 The Unattended Desk MERGED via PR #530 — the NINTH Project Rooms phase merged)
- **Canon:** docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §11 (11.0 current-layer assessment, 11.1 placement, 11.2 resources, 11.3 MCP-001..008), §14 P6 slice, §15 acceptance scenario; CONSTITUTION.md

## The charter

P6's exit, verbatim: **a local MCP client can drive the same
scenario, and the product is ready for Gate B partners.** §11.0's
verdict guides everything: MCP already stands as a programmable
facade (~94 tools, ~20 families, same DB, service-dispatched) — so
REUSE the family registration, discovery, and transport; never a
second tool server. What's missing is exactly what this phase adds:
a `project.*` family (holdspeak/mcp/families/project.py via the
FAMILIES registry, the door.py TOOLS/inputSchema idiom), the §11.2
compact resources, the durable Steward run contract over MCP
(start returns run_id promptly, poll explicitly — MCP-003; the
insert_run seam from 164 is the substrate), the setup interview and
provider discovery over MCP, and the GRADUATION of the reactions
family's watch primitives (watch.list/create/set_enabled/refresh/
preview, reactions.py:21-35) to WatchSpec@1 with durable test/
baseline/evaluation/effect inspection — extend, never replace. Every
tool calls ProjectService or a service-composed command (MCP-001:
identical commands, revision checks, idempotency, events, error
codes as Web); effect tools require-or-generate command_id with safe
retry (MCP-002); results are structured JSON, never prose-parsed
(MCP-004); unsupported citizen mutations refuse typed (MCP-005); a
broken unrelated family never suppresses Project tools (MCP-006);
a focused PROJECT_PALETTE + Project Thread mode make the family
agent-safe (MCP-007). The walk drives §15's whole acceptance
scenario through a local stdio client — Gate B readiness is the bar
the owner verdicts.

OUT: remote transport/identity/Tasks/ecosystem (MCP-008, deferred),
Jira parity (P7), external MCP-client consumption (provider adapter
seam noted, not built).

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-165-01 | The family skeleton (project.py reads + §11.2 resources; MCP-006 isolation) | done | [story-01-the-family-skeleton](./story-01-the-family-skeleton.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-165-02 | The command tools (lifecycle/link/review/updates; MCP-001/002/004/005) | backlog | [story-02-the-command-tools](./story-02-the-command-tools.md) | - |
| HS-165-03 | The driver tools (steward runs, setup interview, provider discovery, watch graduation) | backlog | [story-03-the-driver-tools](./story-03-the-driver-tools.md) | - |
| HS-165-04 | The palette (PROJECT_PALETTE + Project Thread mode; parity hardening) | backlog | [story-04-the-palette](./story-04-the-palette.md) | - |
| HS-165-05 | The walk (a local MCP client drives §15 end to end — OWNER VERDICT) | backlog | [story-05-the-walk](./story-05-the-walk.md) | - |
| HS-165-06 | The docs (the Gate B partner surface; the dedicated docs story) | backlog | [story-06-the-docs](./story-06-the-docs.md) | - |
| HS-165-07 | The close (gates, debts, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

1/7. HS-165-01 the family skeleton DONE (2026-09-02): the project.*
family lands the house way (FAMILIES registry, door.py idiom, three
read tools as thin drivers with EQUALITY parity asserts against the
very service returns Web uses); all five §11.2 resources resolve with
typed refusals; and MCP-006 was BUILT, not found — the families
registry previously crashed whole on one bad import; per-family
importlib + DEGRADED_FAMILIES now isolates, proven through the REAL
assembly path with a poisoned fake family. The delta resource rides
the same private seams the Web's own delta route rides (parity, warts
included — ruling in the story trace). Every pin paid: MCP tool count
142->145, families 31->32, resources 29->34 (docs/README +
MCP_SIDECAR; doc drift guard green). Gates: 54 passed scoped. NEXT:
HS-165-02 the command tools.

## Active risks

- MCP-001 parity is the phase's honesty problem: a tool that
  half-reimplements a service verb instead of calling it is the
  third door reborn. Counsel will hunt exactly this.
- The watch graduation must not orphan the legacy reactions tools:
  the 164 boundary rule (the state column fences schedulers) has an
  MCP twin — name which tool family owns which watch rows.
- MCP-003's polling contract rides run_due/insert_run from 164 —
  the route's daemon-thread lesson applies to the sidecar too:
  never hold a tool call open across phase execution.
- Debts carried in: 164 N-1..N-5 + the scheduled-path trigger wire
  + per-watch cadence editing; 163 S-4/N-1/N-3; 160 N-5/N-1/N-2;
  158 S-1/N-1/N-3; 159 seeding walls; 161 N-1.
