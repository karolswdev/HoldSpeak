# HS-27-01 — `action_owner_enforcer` real run (ubiquity champion)

- **Project:** holdspeak
- **Phase:** 27
- **Status:** backlog
- **Depends on:** HS-16-01..05 (the proven plugin pattern + capability gate)
- **Unblocks:** HS-27-02 (gives the e2e a second real plugin to show), HS-27-05
- **Owner:** unassigned

## Problem

`action_owner_enforcer` is registered in `_BUILTIN_PLUGIN_DEFS`
(`holdspeak/plugins/builtin/__init__.py`) as a `kind="validator"` but is still a
`DeterministicPlugin` stub. It's the **most ubiquitous** of the stubs: almost
every working meeting produces action items, and the most common failure mode is
items with **no clear owner or due date**. A real `run()` here helps on standups,
planning, retros, incident reviews — nearly everything — which is why it leads
this phase over niche plugins like `customer_signal_extractor`.

The substrate is already proven by `mermaid_architecture` (Phase 16): LLM call →
parse/validate → structured output → synthesis body → web render. This story
applies that pattern to a **text/checklist** artifact instead of a diagram.

## Scope

### In

- Replace the `DeterministicPlugin` stub for `action_owner_enforcer` with a real
  `ActionOwnerEnforcerPlugin` in `holdspeak/plugins/builtin/`, registered by
  `register_builtin_plugins` (mirror the `mermaid_architecture` switch).
  - `kind="validator"`, `execution_mode="deferred"`,
    `required_capabilities=["llm"]`.
  - `run(context)`: prompt the LLM (via `MeetingIntel._chat_completion_text`,
    same call path as mermaid) to extract action items and flag, per item,
    whether **owner** and **due date** are present; return a structured payload.
- Output shape (structured, validated): `{"summary": str, "confidence_hint":
  float, "active_intents": [...], "action_items": [{"task", "owner"|null,
  "due"|null, "gap": "missing_owner"|"missing_due"|"missing_both"|null}]}`.
  Reject / low-confidence if the model returns no parseable items.
- Synthesis: `action_owner_enforcer` already maps to `artifact_type="action_items"`
  in `_ARTIFACT_TYPE_BY_PLUGIN`. The generic body is fine for v1; **optionally**
  add a small checklist body branch in `synthesize_meeting_artifacts` (a
  `- [ ] task — owner / due  ⚠️ gap` list) — keep non-`action_items` bodies
  byte-for-byte unchanged, exactly as HS-16-03 did for diagrams.
- Tests (unit + integration), mirroring `test_mermaid_architecture_plugin.py`:
  success (items + gaps), parse-failure (garbage → low-confidence failure),
  provider-raises, capability-blocked, output-shape, and a synthesis test if a
  checklist body branch is added (incl. the byte-for-byte guard for other types).

### Out

- Mutating the **existing** action-item system (the `action_items` DB table /
  review states / `/api/all-action-items`). This plugin emits an *artifact*
  (an ownership-gap report), it does not write into that system. If we later want
  the two unified, that's a separate, explicit decision (see status doc risk).
- Owner/identity resolution against the speaker registry. v1 reports the owner
  string as spoken; linking to known speakers is a later enhancement.
- The other stub plugins (separate stories).

## Acceptance criteria

- [ ] `register_builtin_plugins` returns a real `ActionOwnerEnforcerPlugin` for
      `action_owner_enforcer`; the other eleven stay `DeterministicPlugin`.
- [ ] Real `run()` calls the LLM and returns the structured `action_items`
      payload; malformed model output yields a clean low-confidence failure (no
      crash), exactly like mermaid's parse-failure path.
- [ ] Capability-blocked: with no `"llm"` capability the host returns
      `status="blocked"` (already enforced; covered by a test).
- [ ] If a checklist synthesis body is added, non-`action_items` artifact bodies
      are byte-for-byte unchanged (regression-locked).
- [ ] Unit + integration tests green; full sweep green.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_action_owner_enforcer_plugin.py`
  (new; mirror `test_mermaid_architecture_plugin.py`, mock the intel call).
- Integration: extend the synthesis-diagram-style coverage — a fake
  `action_owner_enforcer` run → artifact with the expected body/structured shape.
- Full sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Live (optional, real `.43`): run the plugin against a hand-authored
  action-heavy transcript; confirm it flags missing owners/dues. Feeds HS-27-02.

## Notes / open questions

- Keep the prompt strict and the parser defensive (mermaid showed the LLM will
  occasionally wrap output in prose) — extract the JSON block, validate types.
- The `.43` Q6 endpoint returns answers in `content` (no reasoning-leak); do not
  build `reasoning_content` fallback (project decision — see memory).
- Decide v1 body: generic synthesis body (zero synthesis change, ships faster) vs
  a checklist branch (nicer UX, small synthesis change). Default: ship generic
  first, add the checklist branch only if it's cheap.
