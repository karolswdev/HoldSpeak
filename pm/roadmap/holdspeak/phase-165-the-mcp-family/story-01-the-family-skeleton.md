# HS-165-01 - The family skeleton: reads, resources, isolation

- **Project:** holdspeak
- **Phase:** 165
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-165-02
- **Owner:** unassigned

## Problem

§11.1: no `project.*` family exists. The foundation must land the
house way (the FAMILIES registry, the door.py TOOLS/inputSchema/
dispatch idiom) with MCP-006 isolation proven from birth.

## Scope

- **In:** holdspeak/mcp/families/project.py registered via FAMILIES
  (holdspeak/mcp/families/__init__.py; tools.py:13 consumes it).
  Read tools: project.list / project.get / project.get_room — thin
  drivers over ProjectService and the room projection (the same
  service reads Web uses; MCP-001). §11.2 resources:
  holdspeak://projects/{id}, /room, /delta, /updates/{update_id},
  /steward/runs/{run_id} via the resources.py pattern. MCP-004:
  structured JSON results with stable shapes. MCP-006 under test: a
  family whose import/init fails must not suppress project tools
  (study how server.py/tools.py assemble families; if no isolation
  seam exists, build the minimal one and prove it with a poisoned
  fake family).
- **Out:** commands (02), steward/setup/provider/watch (03).

## Acceptance criteria

- [ ] project.list/get/get_room return the same shapes the Web reads produce (parity assertions against the service, not copies).
- [ ] All five §11.2 resources resolve; unknown ids refuse typed.
- [ ] MCP-006: a poisoned unrelated family leaves project reads working, under test.

## Test plan

- **Unit:** tests/unit/test_project_mcp.py (the test_door_mcp.py idiom: reset_database + family import + server).

## Trace record (orchestrator ruling, 2026-09-02)

The delta resource calls ProjectDeltaService._find_open_review /
_load_frozen_window (private). RULING: lawful — the Web's own delta
route rides the SAME private seams (project_reviews.py:82 calls
_load_frozen_window; :68 reaches _db directly), so the resource is
in MCP-001 parity with Web, warts included. The wart itself (no
public delta-read method) is pre-existing house debt, not this
story's to pay. MCP-006 was BUILT here: the families registry
previously crashed whole on one bad import; per-family importlib +
DEGRADED_FAMILIES now isolates, proven through the real assembly
path with a poisoned fake family.
