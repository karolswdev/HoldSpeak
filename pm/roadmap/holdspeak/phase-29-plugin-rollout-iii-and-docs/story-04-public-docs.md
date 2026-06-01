# HS-29-04 — Public README + plugin docs

- **Project:** holdspeak
- **Phase:** 29
- **Status:** done
- **Depends on:** HS-29-01, HS-29-02, HS-29-03 (so the docs describe what shipped)
- **Unblocks:** HS-29-05
- **Owner:** unassigned

## Problem

The public `README.md` (source canon: "public install + usage surface") does not
mention the meeting-intelligence plugin system at all, even though the product now
ships **fourteen** real LLM-backed plugins. Before we publish, the README must
tell users what HoldSpeak actually produces from a meeting.

## Scope

### In

- A **"Meeting intelligence plugins"** section in `README.md`:
  - One paragraph on how it works: saved/recorded meeting → transcript → MIR
    routing → plugin chain (against a configured OpenAI-compatible LLM) →
    artifacts rendered read-only in `/history`. Note the `"llm"` capability gate
    and that it runs on saved meetings (not live).
  - A table of the fourteen plugins: ID, what it produces (artifact type), and the
    meeting profile it fits.
  - A pointer to `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` (the RFC) for internals.
- Keep it accurate to the code: fourteen real plugins, artifact types per
  `synthesis._ARTIFACT_TYPE_BY_PLUGIN`, profiles per `router.py`.

### Out

- Rewriting unrelated README sections.
- A how-to-author-a-plugin guide (internal RFC + the trodden pattern cover that;
  a public authoring guide can be a later doc).
- `docs/USER_GUIDE.md` deep-dive (optional; only if quick).

## Acceptance criteria

- [x] `README.md` has a plugin section: how-it-works paragraph + the fourteen-row
      table (ID / artifact / profile) + RFC pointer.
- [x] The list matches the code (fourteen real plugins; names/artifact types
      verified against `builtin/__init__.py` + `synthesis.py`).
- [x] No stale claims (no "coming soon" for already-shipped plugins).

## Test plan

- No code. Cross-check the table against `_REAL_PLUGINS`,
  `_ARTIFACT_TYPE_BY_PLUGIN`, and `router.py` chains by eye. Full sweep still green
  (docs-only change).

## Notes / open questions

- Memory `feedback_holdspeak_not_really_released`: the README's "v0.2.0 released"
  is forward-looking; this section is product-accurate but doesn't need release
  ceremony.
