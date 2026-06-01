# HS-29-03 — Comms plugins (real run)

- **Project:** holdspeak
- **Phase:** 29
- **Status:** done
- **Depends on:** HS-28-01 (renderer registry)
- **Unblocks:** HS-29-05
- **Owner:** unassigned

## Problem

The last two registered stubs are the comms drafters:
`stakeholder_update_drafter` (`stakeholder_update`) and
`decision_announcement_drafter` (`decision_announcement`). They turn a meeting into
shareable comms. Flipping both makes **zero stubs remain**.

## Scope

### In

- Two real plugins (deferred, `required_capabilities=["llm"]`), registered in
  `_REAL_PLUGINS`:
  - `stakeholder_update_drafter` → `{"headline", "highlights": [str], "risks":
    [str], "next_steps": [str]}` (a structured stakeholder update).
  - `decision_announcement_drafter` → `{"announcements": [{"title", "audience"|
    null, "message"}]}`.
- A renderer + structured `/history` render for each (`stakeholder_update`,
  `decision_announcement`).
- Unit + synthesis tests per plugin.
- A direct live `.43` Q6 check per plugin, recorded in evidence.

### Out

- Actually sending the comms (email/Slack) — RFC-disabled actuators.
- Tone/length presets (later).

## Acceptance criteria

- [x] Two real `run()`s return validated payloads; failure + capability-blocked
      covered. `stakeholder_update` succeeds when it has a headline or any non-empty
      section; `decision_announcement` when ≥1 announcement.
- [x] `register_builtin_plugins` returns the real classes; **no
      `DeterministicPlugin` remains** for any of the fourteen IDs
      (`test_no_deterministic_stub_remains`).
- [x] Both artifact types render structured in `/history`.
- [x] Tests green; full sweep green (2062 passed); each verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_stakeholder_update_drafter_plugin.py`,
  `test_decision_announcement_drafter_plugin.py`.
- Synthesis: a body case per type in `test_artifact_synthesis_diagram.py`.
- A registrar assertion that **no stub** is returned for any built-in ID.
- Full sweep + direct live checks.

## Notes / open questions

- `stakeholder_update` is the one "document-shaped" output; still render it
  structured (headline + sections), not as a raw markdown blob.
