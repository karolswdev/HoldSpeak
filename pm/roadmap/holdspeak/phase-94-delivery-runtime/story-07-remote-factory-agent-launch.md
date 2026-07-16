# HS-94-07 — Remote factory and Story-bound agent launch

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-04, HS-94-06
- **Unblocks:** HS-94-08, HS-94-09

## Problem

Remote nodes can only receive peek/arm/steer/keys for a key the owner already
knows. Pane discovery and factory remain local. Spawn creates a shell, not an
agent bound to a selected source/worktree/Story. The owner cannot start the work
they intend to steer from the remote Desk.

## Scope

- In:
  - remote terminal/session discovery through node capabilities;
  - remote spawn, rename, kill through the command envelope;
  - configured Agent Profiles for Claude/Codex executables and fixed options;
  - configured-root source/worktree selection;
  - create/select worktree and branch with preview and conflict refusal;
  - Story-bound agent launch;
  - atomic logical creation of Work attempt, terminal target, launch Receipt,
    and eventual rider session binding;
  - partial-launch, failed-to-register, process-exited, reconnect, and cleanup
    states;
  - exact consequence and destination copy from Phase 93;
  - local factory parity.
- Out:
  - arbitrary browser-supplied command or executable;
  - autonomous agent scheduling;
  - cloning arbitrary URLs from the browser;
  - bypassing OS permissions, node root allow-lists, or Delivery Workbench gate;
  - assuming process launch means Story completion.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the true cross-machine launch over a second physical node moves to
[BACKLOG candidate Y](../BACKLOG.md); the launch atomicity, guards, rollback,
and remote-verb behavior are machine-verified here with real git worktrees
and a stubbed launcher exec (a real Claude/Codex binary is a candidate-Y
rider, not a contract requirement).


- [x] The Desk lists remote panes/sessions with node, source/worktree, command
      profile, and immutable target; no pre-known `pane:%N` is needed.
- [x] A person selects a Story and online capable node, chooses/creates an
      allowed worktree, previews exact launch facts, and launches Claude or
      Codex without supplying shell syntax.
- [x] Launch creates one Work attempt and one target; rider registration binds
      the real session without duplication.
- [x] Process launched but rider absent is a retained partial state with terminal
      access and cleanup, not a fake success.
- [x] Rename/kill on a remote node target the discovered generation, are
      idempotent, and produce node+hub Receipts.
- [x] Name/branch/path/argv injection, source outside configured roots, duplicate
      worktree, dirty-worktree policy, and node capability mismatch refuse before
      execution.
- [x] Node disconnect during launch/kill reconciles by command ID.
- [x] Local factory behavior and safety census remain intact.

## Test plan

- Agent Profile validation and secret/argv redaction;
- worktree create/select/conflict/dirty/root containment;
- partial launch and rider binding timeout;
- duplicate command and reconnect;
- remote spawn/rename/kill;
- actual Claude and Codex sessions on two worktrees;
- destructive policy-mode behavior and audit completeness.

## Implementation direction

- Agent Profiles are node-owned registered capabilities. The client selects an
  ID; it never supplies executable or free-form shell.
- Prefer git argv plumbing and explicit fields over `sh -c`.
- Worktree creation is a distinct typed operation with its own Receipt and
  rollback/cleanup status.
- Keep process/session discovery independent: a terminal can exist without an
  agent rider and must say so.
- End attempt and kill process are separate consequences; UI must name which one
  it performs.

## Evidence required

- remote Story → worktree → launch → session → terminal capture for Claude and
  Codex;
- partial-launch recovery;
- worktree and injection refusal matrix;
- remote lifecycle Receipts;
- node-loss reconciliation.
