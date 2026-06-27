# HSM-17-07 — Docs: the agent-sync loop, the hook install, entry points

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** todo — the dedicated docs story ([[feedback_dedicated_docs_story]]); after the features,
  before closeout.
- **Depends on:** HSM-17-01..06 (document the loop as actually shipped + proven).
- **Owner:** unassigned

## Problem

Agent sync introduces a new first-class concept (a live coding session as a synced primitive) and a new
setup step (installing our hooks into Claude/Codex). Per the dedicated-docs-story rule, the **entry
points** must learn it, not just an internal note.

## Scope

- **In:**
  - **The hook install** documented as a first-class setup step (the one command, idempotent, reversible)
    — where a user turns on "inject ourselves into my Claude/Codex."
  - **The loop** documented: a coder asks → it surfaces on the desk → you answer (typed / spoken /
    dropped-context / AI-drafted) → it injects back. With the egress + never-autonomous guarantees stated.
  - **Entry points touched** (the lesson from [[project_phase64_docs_catch_up]] — feature docs must touch
    the entry points): the companion / AIPI-Lite section, the README "two modes / companion" surface, and
    an `ARCHITECTURE.md` diagram of the agent-sync loop (capture → primitive → answer → inject) consistent
    with the existing Mermaid set.
  - **Canon vocabulary** honored: a coding "agent" (Claude/Codex session) is distinct from Qlippy and
    from the (renamed/removed) persona builder; egress is a badge.
- **Out:** end-user marketing copy; the launch narrative.

## Acceptance criteria

- [ ] The hook install is documented as a clear, reversible setup step.
- [ ] The agent-sync loop is documented end-to-end with the never-autonomous + egress guarantees.
- [ ] At least one entry point (README and/or the companion docs page) reflects agent sync; an
      `ARCHITECTURE.md` diagram of the loop is added and renders.
- [ ] No naming regression: "agent" = coding session; the persona layer (if kept) reads as its renamed
      self everywhere in docs.
- [ ] Voice guard passes on any `docs/*.md` touched (HS-IDs / dashes / AI-vocab rules —
      [[project_phase58_front_door]]).

## Test plan

- The Mermaid render guard passes for the new diagram (`tests/e2e/test_mermaid_renders.py`).
- Voice guard passes on touched `docs/*.md`.
- A fresh read-through: a new user can find and run the hook install and understand the loop from the
  entry points alone.
