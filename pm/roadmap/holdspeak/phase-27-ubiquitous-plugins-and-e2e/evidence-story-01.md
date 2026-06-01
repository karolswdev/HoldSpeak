# HS-27-01 Evidence — `action_owner_enforcer` real run

**Date:** 2026-06-01.
**Story:** [story-01-action-owner-enforcer.md](./story-01-action-owner-enforcer.md).

## Implementation Evidence

**Plugin** (`holdspeak/plugins/builtin/action_owner_enforcer.py`) — real
`ActionOwnerEnforcerPlugin` (`kind="validator"`, deferred,
`required_capabilities=["llm"]`), mirroring the `mermaid_architecture` pattern:
strict prompt → `MeetingIntel._chat_completion_text` → `_extract_action_items`
(parse a fenced or bare `{"action_items": [...]}`, normalize, compute a per-item
`gap` of `missing_owner` / `missing_due` / `missing_both` / `null`). Placeholder
owners (`unassigned`, `TBD`, `null`, …) are treated as missing. Success returns
`{summary, action_items, gap_count, confidence_hint=1.0, active_intents}`; an
unparseable response, empty list, or missing transcript returns the clean
failure shape (no `action_items` key), exactly like mermaid's parse-failure path.

**Registration** (`holdspeak/plugins/builtin/__init__.py`) — replaced the
one-off `if plugin_id == "mermaid_architecture"` with a `_REAL_PLUGINS` map; both
`mermaid_architecture` and `action_owner_enforcer` now register their real class,
the other eleven stay `DeterministicPlugin`.

**Synthesis** (`holdspeak/plugins/synthesis.py`) — added an `action_items`
checklist body branch beside the diagram branch: a `- [ ] task — owner: … · due:
… ⚠️ gap` list, plus `structured_json["action_items"]`. Non-diagram,
non-action_items bodies remain **byte-for-byte** unchanged (regression-locked).

## Tests

- `tests/unit/test_action_owner_enforcer_plugin.py` (10 cases): attributes,
  success-with-gaps, bare-JSON parse, unparseable → failure, empty-list →
  failure, no-transcript → failure, provider-exception caught, placeholder-owner
  normalization, non-object → None, host-blocked-without-capability, registrar
  returns the real class.
- `tests/unit/test_artifact_synthesis_diagram.py` (+1): action_items checklist
  body + `structured_json` key; the existing byte-for-byte non-diagram guard
  still passes (now also implicitly covering the action_items branch is gated).

```bash
uv run pytest -q tests/unit/test_action_owner_enforcer_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_plugin_host_llm_capability.py   # 23 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                              # 1914 passed, 13 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live runtime check (real `.43` Q6 endpoint, no API key)

Ran the plugin against a realistic 4-speaker transcript, then through
`synthesize_meeting_artifacts`:

```text
confidence: 1.0 | gap_count: 3
summary: 4 action item(s); 3 missing an owner or due date.
  Draft the OAuth flow   — owner Karol, due Friday   (gap: none)
  Book the offsite venue — owner —,     due —         (gap: missing_both)
  Review the migration plan — owner Maria, due —      (gap: missing_due)
  Update the docs        — owner —,     due —         (gap: missing_both)

### Action Owner Enforcer
4 action item(s); 3 missing an owner or due date.
- [ ] Draft the OAuth flow — owner: Karol · due: Friday
- [ ] Book the offsite venue — owner: — · due: —  ⚠️ missing both
- [ ] Review the migration plan — owner: Maria · due: —  ⚠️ missing due
- [ ] Update the docs — owner: — · due: —  ⚠️ missing both
```

It correctly extracted every action item, assigned owners/dues where stated, and
flagged each gap — on the most universal meeting output.

## Result

The second real plugin is live (Phase 27, 1/5). The Phase-16 pattern generalized
cleanly to a non-diagram, text/checklist artifact. **Next: HS-27-02** — the
spoken-meeting e2e harness, which will demonstrate this plugin + the mermaid
diagram together on real endpoints with screenshots.
