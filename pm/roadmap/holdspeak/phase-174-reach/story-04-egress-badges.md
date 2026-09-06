# HS-174-04 — Egress badges on remote reads

- **Project:** holdspeak
- **Phase:** 174
- **Status:** done
- **Depends on:** HS-174-02, HS-174-03
- **Unblocks:** HS-174-05, HS-174-08
- **Owner:** unassigned

## Problem

Article III:2 requires egress disclosed by the badge at the point of
decision. Today the pipeline observer shows egress badges for cloud
model calls, but remote MCP reads — which cross the network to the
hub — carry no badge. A remote read is not a local read; the user must
see that a call came from outside the machine.

## Scope

- In:
  - Every remote MCP call is kernel-admitted with a terminal receipt
    (Article XI:2) naming the remote principal and the operation.
  - The pipeline observer shows an EGRESS badge on every remote call
    (the "remote" badge state from story 01's design).
  - Local stdio calls remain badgeless (they do not cross the network;
    Article III does not apply to same-machine reads).
  - The receipt distinguishes remote reads from remote writes (writes
    already have receipts through Article V; reads are new).
- Out:
  - Badge changes for non-remote calls (the existing local/cloud
    badges are unchanged).
  - Remote-specific audit views (the pipeline observer is sufficient).

## Acceptance criteria

- [x] Every remote MCP call produces a kernel receipt with the remote
      principal's identity and the operation (Article XI:2).
- [x] The pipeline observer shows a "remote" EGRESS badge on every
      remote call.
- [x] Local stdio calls produce no egress badge.
- [x] The receipt for a remote read names the caller, the tool, and
      the outcome (Article V:2).

## Test plan

- Unit: a remote call through the HTTP transport produces a kernel
  receipt; a local stdio call does not.
- Unit: the pipeline observer event for a remote call carries the
  "remote" egress badge; the same tool over stdio does not.
- Integration: drive a tool over HTTP and over stdio; verify the
  receipt and badge presence differ correctly.

## Notes / open questions

- Should remote reads be kernel-admitted as a new operation kind or
  tagged on the existing tool dispatch? Propose a tag on dispatch
  (the transport knows it is remote; the kernel sees the tag).
