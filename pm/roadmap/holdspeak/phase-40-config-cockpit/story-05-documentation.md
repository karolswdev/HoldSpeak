# HS-40-05 — Documentation

- **Project:** holdspeak
- **Phase:** 40
- **Status:** backlog
- **Depends on:** HS-40-01, HS-40-02, HS-40-03, HS-40-04
- **Unblocks:** HS-40-06
- **Owner:** unassigned

## Problem

The current guides teach setup by editing `config.json` / `blocks.yaml`. After
this phase, the web cockpit is the easy path — the docs must lead with it, or
users will still reach for the files.

## Scope

- In:
  - Update `docs/INTELLIGENT_TYPING_GUIDE.md` and `docs/DICTATION_COPILOT.md` to
    **lead with the web-UI setup** ("set this up in `/dictation` — no file
    editing"), keeping the JSON reference as the advanced/headless fallback.
  - Document the persistent correction memory (what's stored, where, that it
    survives restarts, how to curate/clear it in the UI) and the depth-telemetry
    panel.
  - Screenshots of the cockpit + the memory/telemetry panels.
  - Doc drift-guard + live-doc link-check green.
- Out:
  - New marketing copy (README hero is the closeout's job if needed).
  - Re-documenting blocks/KB editing (already covered).

## Acceptance criteria

- [ ] The guides present the web cockpit as the primary setup path; the JSON
      config is framed as the advanced/headless alternative, not the default.
- [ ] Persistent correction memory + the memory/telemetry UI are documented
      (storage, durability, curate/clear).
- [ ] Screenshots embedded; doc drift-guard + link-check green.
- [ ] Every documented control/field matches what actually shipped in 01–04.

## Test plan

- `uv run pytest -q -k "doc_drift or dangling or no_live_doc or link"` → green.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (docs-only).
- Manual: re-read against the shipped UI + config fields.

## Notes / open questions

- Honor the project memory `feedback_dedicated_docs_story`: documentation is its
  own story (here), not a closeout footnote.
- The DICTATION_COPILOT showcase (Phase 39) is a good place to add a "set it up
  in the UI" pointer near the "Turn it on" section.
