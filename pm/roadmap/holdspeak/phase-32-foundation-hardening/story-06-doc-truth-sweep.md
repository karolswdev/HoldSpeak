# HS-32-06 — Stale non-PMO doc sweep + drift guard

**Status:** not-started.

## Goal

Make the **non-PMO** project docs tell the truth. The PMO roadmap corpus is the
historical record and stays verbatim by design — this story touches only docs
that claim *current* state and are wrong:

- `pm/roadmap/holdspeak/HANDOVER.md` — the "Three real plugins ship; the other 11
  are `DeterministicPlugin` stubs" section is dead (Phase 29 took it to **14 real,
  zero stubs**, locked by `test_no_deterministic_stub_remains`). HANDOVER is the
  "read me first" doc, so this is the most actively misleading line in the repo.
  *(HANDOVER sits in `pm/` but is a live-state pointer, not write-once evidence —
  in scope.)*
- `docs/PLAN_*.md` — "branch feature/intel-streaming" / "branch feature/menu-bar"
  headers reference branches that **do not exist** (menubar in fact shipped:
  `holdspeak/menubar.py`, a `menubar` extra, README ✅). Correct the status claims.
- `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — reconcile any remaining "⚠️ stub"
  per-plugin lines against the zero-stubs reality.
- `README.md` positioning — the lede still pitches "voice typing"; reconcile with
  what shipped (a local-first transcription-and-intelligence runtime) without
  overclaiming.
- **Vestigial `config.meeting.web_enabled` (added by HS-32-02).** Dropping the
  embedded per-meeting web server left this config field + its Settings checkbox
  (`tui/screens/settings.py`) controlling nothing. Remove the dead field, the
  toggle, and reconcile `test_config.py`'s `web_enabled` assertions — or document
  why it stays. *(Code drift, not just docs, but the same truth-in-state concern.)*

## Scope

- **Greenfield/aggressive — delete, don't archive.** These are non-PMO project
  docs, not the historical PMO record. If a `PLAN_*.md` describes a branch/feature
  that no longer exists or shipped differently, **delete the dead doc** (or the
  dead section) outright rather than marking it "superseded." Stale docs that lie
  are worse than absent ones.
- Fix the still-relevant docs to state only true current status (HANDOVER's
  pickup pointer, README positioning).
- Add a lightweight guard against the worst drift returning: e.g. a test asserting
  no doc claims a stub count that contradicts `test_no_deterministic_stub_remains`,
  and/or a check that any remaining PLAN "branch …" header names a branch that exists.

## Test plan

- The drift guard runs in the suite and is green.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- Manual: re-read HANDOVER + the PLAN headers; every status claim is verifiable
  against the code/branches as of this commit.

## Done when

- [ ] Dead PLAN docs/sections (non-existent branches, shipped-differently features)
      are **deleted**; surviving docs (HANDOVER pointer, README positioning) state
      only true things.
- [ ] A drift guard is committed and green.
- [ ] Full suite green.
