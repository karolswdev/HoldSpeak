# Evidence - HS-145-02

- **Story:** HS-145-02 - The connect-calendar affordance
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T19:35:10Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_door_read_model.py tests/unit/test_door_routes.py tests/unit/test_door_mcp.py tests/unit/test_door_transport_parity.py 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 48b0ab7af92634637fcae30d135c49043ab12260

```text
..................                                                       [100%]
18 passed in 25.19s
```

## Orchestrator triage note

The captured run (18 passed) covers the four Python door suites:
read model (`calendar_configured` False on empty subscription / True
on valid HTTPS / False with no loader), routes + MCP key-set
assertions, and transport parity with both sides on the same
`config_loader`. The rest of the proof chain, verified by the
orchestrator directly:

- **The glass proof** lives in
  `tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state`
  (real hub): empty rail + no calendar → "No calendar connected." +
  the Connect calendar ghost button; the click opens the Settings
  surface scoped to the Meetings module (asserted inside the owning
  container); a configured subscription whose ICS holds only past
  events → "No future time scheduled." with NO connect button — the
  no-nag law on real glass.
- **Shots** (`assets/story-03-shots/rail-*.png`, eyeballed): the
  affordance at 1440 and 393, the Settings landing (CALENDAR
  Subscription field + its mic visible), the quiet state.
- Composition truth: the production seat is `web_server.py` (not the
  route module the plan guessed) — both it and the MCP `_service()`
  factory pass `config_loader=Config.load`; live-read ruling [B2a]
  honored. `scripts/mcp_walk.py` door aggregate key set updated in
  the same story; the 135 tool count untouched.
- The full close sweep is story 03's captured record.
