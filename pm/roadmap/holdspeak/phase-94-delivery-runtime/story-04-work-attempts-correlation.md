# HS-94-04 — Work attempts and exact Story/session/worktree correlation

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-02, HS-94-03
- **Unblocks:** HS-94-06, HS-94-07, HS-94-08

## Problem

Delivery Workbench currently joins a session to every in-progress Story in its
repo and calls it exact only when there is one. On the real HoldSpeak tree the
observed result was 29 ambiguous sessions and zero exact ones. Browser-only
manual pins do not travel, audit, or bind a worktree/terminal.

## Scope

- In:
  - durable Work attempt repository and projection;
  - exact compound Story refs;
  - binding to node, source, worktree, agent session, and terminal target;
  - association provenance: launch, rider claim, manual, contract, heuristic;
  - attempt lifecycle and replayable events;
  - agent hook/rider integration for explicit claim where available;
  - manual attach/reassociate/clear through hub API and Receipt;
  - migration of browser manual pins;
  - legacy `dw sessions` correlation as a labeled fallback;
  - attention projection for waiting, detached, stale, and ambiguous attempts.
- Out:
  - autonomous Story selection;
  - changing Story status when an attempt starts/ends;
  - inferring completion from agent output;
  - terminal streaming or launch.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the cross-client native parity capture moves to
[BACKLOG candidate Y](../BACKLOG.md); the hub record, wire, and correlation
fixture carry the contract.


- [x] One attempt has one primary Story and exact node/source/worktree/session/
      target identity.
- [x] Launch, rider claim, and manual association render their provenance and
      never masquerade as Delivery Workbench state.
- [x] An existing local/remote session can be attached to a Story, survives
      client/restart, and appears identically on Web and native.
- [x] Repo-wide heuristic output remains available but is labeled ambiguous and
      never pins one session to several Story cards as exact.
- [x] Multiple concurrent attempts on one Story and one agent touching
      sequential Stories are represented without identity reuse.
- [x] Worktree removal/session end/node offline moves attempts to honest states
      without deleting history.
- [x] The real HoldSpeak fixture produces exact attempts for explicitly claimed
      sessions; the baseline “zero exact” regression is closed.
- [x] Attempts expose one durable read projection with explicit provenance
      and honest states; surfacing attention/Receipt rows for attempts
      through the shared Desk projection spine is HS-94-08's Desk-expression
      scope (recorded there), not silently claimed here.

## Test plan

- model/repository lifecycle and idempotent event projection;
- association precedence and provenance;
- multiple project slugs and duplicate-looking Story IDs across sources;
- browser pin migration;
- node offline/reconnect, worktree removed, session restarted;
- two agents/two worktrees/two Stories live;
- Python/TypeScript/Swift fixture parity.

## Implementation direction

- Do not add Story fields to `agent_sessions.json` as the only truth; sessions
  are node presence and attempts are hub runtime records.
- A rider may report a claim, but the hub resolves it against the source snapshot
  before marking exact.
- Use qualified Story refs everywhere; never lookup by bare Story ID across
  sources.
- Keep manual association reversible and auditable.
- Attempt end does not imply Story done. Delivery completion remains a rail
  mutation with evidence/gate rules.

## Evidence required

- before/after correlation counts on the flagship fixture;
- live two-agent/two-worktree attempt view;
- manual attach and rider-claim Receipts;
- node/worktree/session failure transitions;
- cross-client contract captures.
