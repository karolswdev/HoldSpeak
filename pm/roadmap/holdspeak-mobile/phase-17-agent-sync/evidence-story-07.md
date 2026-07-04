# Evidence — HSM-17-07: docs (the agent-sync loop, the hook install, entry points)

**Date:** 2026-07-04. The dedicated docs story, written against the loop as
actually shipped and proven in 17-02..05.

## What changed

- **`docs/AGENT_HOOK_INSTALL.md`** — the one-command install is now the
  primary path: a new "One-Command Install" section (`holdspeak agent-hook
  install` / `uninstall`, idempotent, exactly reversible, foreign hooks
  preserved, hooks take effect for new sessions, the Codex trust review
  named). The lifecycle the hooks report (working / waiting with the
  question / idle / ended, with decay) and where it surfaces (the iPad desk,
  `GET /api/coders/sessions`) stated. The manual template path kept below.
  The stale hook-event lists corrected to the shipped templates (Claude
  gains `Notification`, bounded `PostToolUse`, `SessionEnd`; Codex gains
  `Notification`, `SessionEnd`, with the no-SessionEnd decay note). The
  safety model reworded honestly: settings change only when you run the
  install command, and uninstall restores them exactly.
- **`README.md`** — the iPad companion section documents the loop as a user
  meets it: coding agents on the desk (calm working / demanding when
  blocked), the four answer modes (type, speak, drop a record as grounding,
  AI draft on device or endpoint with the badge saying which), and the
  never-autonomous guarantee (a draft lands editable; only an explicit send
  delivers). A "Where to go next" row points at the hook install.
- **`docs/ARCHITECTURE.md`** — a new "The agent sync loop" section with a
  Mermaid flowchart in the existing diagram style: hooks → registry → hub →
  the desk object (glare on waiting) → the composer → explicit send →
  the selected session's tmux pane. The prose states the never-autonomous
  and egress guarantees and the failed-delivery posture (the question stays).

## Canon vocabulary held

"Agent" in every touched doc means a live Claude Code / Codex coding session;
the persona builder is not referenced. Egress appears only as the badge
grammar (local + your desktop; on device; endpoint). No privacy prose.

## Guards (the story's own test plan)

- Doc drift + voice guard (`tests/unit/test_doc_drift_guard.py`): **18
  passed** — no roadmap vocabulary, no prose dashes, no AI vocabulary, no
  banned feature names in the touched entry points.
- Mermaid render guard (`tests/e2e/test_mermaid_renders.py`): **2 passed** —
  the new diagram renders through mmdc with the rest of the set.
