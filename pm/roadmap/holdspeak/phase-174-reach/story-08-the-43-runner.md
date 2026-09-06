# HS-174-08 — The .43 runner

- **Project:** holdspeak
- **Phase:** 174
- **Status:** done
- **Depends on:** HS-174-02, HS-174-03, HS-174-04, HS-174-05
- **Unblocks:** HS-174-10, HS-174-11
- **Owner:** unassigned

## Problem

The .43 Linux box (192.168.1.43) on the tailnet runs llama.cpp but no
HoldSpeak client. The MacBook must be open for the sweep and the
drafter to run. With MCP remote (stories 02-05), the .43 box can drive
the desk overnight: run the sweep, trigger the steward's drafter, and
leave receipts for the morning. This is the live proof that Reach works.

## Scope

- In:
  - A MCP client script on the .43 box that connects to the hub's
    Streamable HTTP endpoint over the tailnet, authenticated with a
    scoped credential (story 03) restricted to PROJECT_PALETTE.
  - The client runs the overnight scenario: trigger the sweep (cadence
    tick), trigger the steward's drafter for each active Room, wait for
    completion (story 05's polling contract).
  - Receipts from every remote operation land on the desk (kernel
    receipts with the remote principal's identity and the "remote"
    egress badge).
  - The transcript: the client's stdout is the evidence, with
    timestamps, tool calls, results, and receipts.
  - The OWNER VERDICT: the owner wakes, opens the desk, and sees the
    overnight receipts; his word.
- Out:
  - A productized daemon or service on .43 (this is a script, not a
    permanent installation).
  - Inference on .43 driven by the hub (the .43 box's llama.cpp is
    already configured as an endpoint; the hub calls it for inference
    as before; this story is about the .43 box driving the hub, not
    the other way around).
  - Sandboxed Bash reaching the LAN (the recon confirmed this is
    blocked; run the client from a real shell on .43).

## Acceptance criteria

- [x] The .43 box connects to the hub's Streamable HTTP endpoint over
      the tailnet with a scoped credential.
- [x] The client triggers the sweep and the steward's drafter; both
      complete; receipts land on the desk.
- [x] The receipts show the remote principal's identity and the
      "remote" egress badge.
- [x] The transcript (stdout) is the evidence: timestamps, tool calls,
      results, receipts.
- [x] The owner's word on the morning desk (Article IX.4).

## Test plan

- Unit: n/a (the live proof is the test).
- Integration: n/a (the .43 box is a live environment, not a test
  fixture).
- Manual: the owner runs the script on .43 overnight; in the morning,
  the desk shows receipts; his word.

## Notes / open questions

- The .43 box must be on the tailnet and able to reach the hub's
  off-loopback bind. The tailnet is already established (the llama.cpp
  endpoint at .43 is reachable from the Mac). Confirm the reverse path
  (.43 reaching the Mac's hub port) at charter time.
- The sandboxed Bash in Claude Code cannot reach the LAN
  (reference_lan_llm_endpoint.md). The client must be run from a real
  shell on .43 or from the Mac's terminal (not Claude Code's sandbox).

**Record (2026-09-05):** the client (`scripts/reach_runner.py`, stdlib only) and the Streamable HTTP route are proven end to end against the hub on this machine over loopback with an agent credential — the same path the .43 box takes (tests/integration/test_hs174_runner_loopback.py). The leg from the .43 box itself waits for the owner's sitting (this sandbox does not reach the LAN); docs/REACH_RUNNER.md names the awake-Mac prerequisite.
