# HS-104-01 - The capability ledger — what each adapter actually knows

- **Project:** holdspeak
- **Phase:** 104
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-104-02, HS-104-05
- **Owner:** unassigned

## The council finding (the bar)

The council's strongest structural demand: before any gate holds a
call or any card prints a number, the system must state, **per agent
adapter**, whether each capability is *authoritative*, *inferred*, or
*unavailable*. AgentGlass silently blends hook events (authoritative
for Claude Code), transcript scans (inferred), and OTel spans (varies
by exporter) into one radar — which is exactly how a dashboard learns
to lie. HoldSpeak's Article VI posture demands the opposite: the
ledger first, the surfaces second.

## Problem

HoldSpeak already speaks to agents through several adapters with very
different epistemic standing — a tmux pane via `coder_steering.py`
(pane content: authoritative; what model runs inside it: unavailable),
a delivery node via `holdspeak/delivery/node_link.py` (attempt
identity: authoritative), the mesh relay (`holdspeak/intel/`), and
soon Claude Code hooks (HS-104-02). Nothing records what each adapter
can actually vouch for, so every downstream surface is one refactor
away from printing an inferred number as a fact.

## Recipe

1. **The ledger is data, not prose.** New module
   `holdspeak/agent_capabilities.py`: a frozen declaration table —
   adapter id → capability → standing. Capabilities (fixed enum):
   `tool_hooks`, `session_identity`, `usage_tokens`, `repo_head`,
   `blocking` (can the adapter *stop* a call, or only observe it).
   Standings (fixed enum): `authoritative`, `inferred`,
   `unavailable`. Declare the adapters that exist today: `tmux-pane`,
   `delivery-node`, `mesh-node`, and a `claude-code-hooks` row that
   HS-104-02 will make true (declare it `unavailable` in this story;
   HS-104-02 flips the two entries it implements — the ledger never
   promises ahead of the code).
2. **One read API.** `GET /api/agents/capabilities` returns the whole
   table. Add a JSON schema to the contracts area as a SPEC artifact
   (standing direction: the web desk is the reference
   implementation; a future Swift recreation builds from these
   schemas — no HSM work rides this story).
3. **The doctor names it.** Extend `collect_doctor_checks()` with an
   "Agent capabilities" check: it fails if any code path registered
   in the ledger's *consumers* list requests a capability the ledger
   marks `unavailable` — a census in the HS-87 chokepoint-census
   style, greppable and mechanical.
4. **The enforcement hook for later stories.** Export
   `require_capability(adapter, capability)` → raises a typed error
   naming the adapter and standing. HS-104-02 and HS-104-05 MUST go
   through it; the census pins their call sites.

## Out of scope

- Any UI beyond the doctor line (the ledger is plumbing; HS-104-05
  is the first surface that renders standings).
- Auto-detection of capabilities. Declarations are hand-written and
  reviewed — that is the point.

## Acceptance

- The ledger module exists with the four adapters declared and unit
  tests pinning every (adapter, capability) cell.
- `GET /api/agents/capabilities` serves the table; the contract
  schema validates the live response.
- The doctor check and `require_capability` exist with tests for the
  refusal path (typed error, names the standing).

## Test plan

- **Unit:** the full matrix; `require_capability` allow + refuse;
  schema validation of the route payload.
- **Integration:** the doctor check green on the current tree; a
  deliberate bad consumer registration turns it red in-test.

## Chef's notes

- Resist making standings dynamic. A standing changes when code
  changes, in the same commit, with the census watching. The moment
  the table is computed at runtime it becomes another inference.
- The `blocking` capability is the load-bearing one for HS-104-02:
  tmux is `unavailable` for blocking (you can interrupt, not
  intercept), Claude Code hooks are `authoritative`. Getting this
  cell right is what keeps the gate from ever being offered on a
  session that cannot honor it.
