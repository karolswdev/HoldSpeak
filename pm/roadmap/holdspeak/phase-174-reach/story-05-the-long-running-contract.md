# HS-174-05 — The long-running contract

- **Project:** holdspeak
- **Phase:** 174
- **Status:** in-progress
- **Depends on:** HS-174-02, HS-174-04
- **Unblocks:** HS-174-08
- **Owner:** unassigned

## Problem

MCP-003 requires long-running steward invocations to return a `run_id`
promptly and use explicit polling rather than holding a tool call open.
This works over stdio (the sidecar returns run_id, the client polls).
Over HTTP the same contract must hold, and if the MCP Streamable HTTP
spec ratifies a notification channel (SSE), the run state may push
through it — but only if that mechanism is ratified and fits.

## Scope

- In:
  - MCP-003's run_id + polling verified over the Streamable HTTP
    transport: the remote client receives run_id, polls for state, and
    gets the terminal result.
  - If the Streamable HTTP notification channel is ratified in the MCP
    spec at charter time: SSE push for run state (start, progress,
    terminal) over the same connection.
  - Documented contract: the polling interval, the terminal states, the
    timeout behavior (credential TTL bounds the run).
  - Tested: a steward run triggered remotely completes and the client
    receives the terminal result.
- Out:
  - MCP Tasks integration (the recon could not confirm a ratified
    feature; verify against the current spec; never build to a draft).
  - Custom long-running operations beyond the steward.
  - WebSocket-based push (the hub's /api/ws is the web UI's channel,
    not the MCP remote's).

## Acceptance criteria

- [ ] A steward run triggered over HTTP returns run_id promptly; the
      client polls and receives the terminal result (MCP-003).
- [ ] If SSE push ships: the client receives run state events (start,
      progress, terminal) over the Streamable HTTP connection.
- [ ] The polling contract is documented (interval, terminal states,
      timeout behavior tied to credential TTL).
- [ ] The credential's TTL bounds the run: an expired credential
      cannot poll for results.

## Test plan

- Unit: trigger a steward run over HTTP; assert run_id returned
  promptly; poll; assert terminal result.
- Unit: if SSE ships, assert the notification channel delivers state
  events.
- Integration: a remote client on the same machine drives a steward
  run to completion over HTTP.

## Notes / open questions

- The SSE channel decision depends on the MCP spec's state at charter
  time. If not ratified, polling-only ships and SSE is deferred to a
  future phase.
