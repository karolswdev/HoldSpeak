# DC-03 The Practice — seam census (2026-08-30)

- **Recipes:** table `recipes` schema.py:1217–1234 (`tools_json`, `system_prompt`, `profile_id`, no `kind`) → additive `kind`; repo `holdspeak/db/primitives.py:88–139`; `holdspeak/services/recipe_service.py`; routes `holdspeak/web/routes/primitives/recipes.py`; seeds `holdspeak/seeds/fresh-desk.yaml` (no `recipes:` section; `seed.py:283–288` upserts recipes).
- **Tool names by class:** `holdspeak/services/thread_tools.py:28–197` — 52 evidence reads, 3 candidate builders, 85 effect proposals, 16 `people.*` sensitive; the palette seam `tool_schemas_for(allowed)` at L220.
- **Threads:** `threads.recipe_id` exists, NO `mode_id` (bind modes through `recipe_id`); assembler `thread_service.py:695–793` (`_assemble_payload`: system prompt from recipe L714–720, leaf path L723, refs L725–748, parts `text|annotation` L759–762, `_sensitive_texts` L790–793); no compaction cut logic.
- **Notes:** `notes(tags_json)` schema.py:847–860; no tag-filter API (json_each WHERE needed); FTS ignores tags.
- **Verbs/composer:** `verbRegistry.ts:44–65` Verb shape; `ThreadComposer.tsx:64–86` `THREAD_SLASH_COMMANDS` (keep/fork/stop/new), `filterSlashCommands`; no argument support yet.
- **Capabilities:** `chat.turn` at `inference_capabilities.py:1069–1072` (group `thought`); backfill family `chat-route-assignments`; fences `test_phase143_inference_capability_census.py` (`EXPECTED_CALL_SITES` L57, `PRODUCT_RUNNER_ENTRANCES` L176), one_path census/spine, placement provenance; pattern test `tests/unit/test_hs151_chat_capability.py`.
- **Annotations:** `annotation` kind exists (schema.py:3452); no draft flag → additive `thread_message_parts.draft`; no selection-popover component in web (only xterm copy); MicButton reusable.
- **Compaction:** `system` row + `stats_json {"compaction": true, "cut_at"}` needs no schema change.
- **Todo → Door:** `action_items(meeting_id NOT NULL FK)` schema.py:98–110; writers `db/meetings.py:409`, `follow_through_service.py:285–290`; no `door.add_item` tool (`families/door.py:17` = `door.get` only); no `DoorService.add_item`; cards carry `source` + `CardProvenance` (`follow_through_service.py:73, 106–116`).
- **Tests to copy:** recipe tests, `test_hs151_chat_capability.py`, `test_thread_tool_gate.py`, the 151/152 rigs.
