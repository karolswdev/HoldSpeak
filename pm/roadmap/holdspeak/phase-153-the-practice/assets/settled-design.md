# Phase 153 settled design — The Practice (DC-03)

Ruled by the orchestrator 2026-08-30 from the DC-03 seam census
([audit-census.md](./audit-census.md)) and the holistic counsel
design-beat (Phase 152 `assets/counsel-design-beat.md`: RATIFY-W-C;
M7, M8, S4, S5, R3). RFC §6.5–6.6. Builders implement.

## The one sentence

The Thread learns a practice: a mode (what it may touch and how it
speaks), saved prompts, a cheaper second model watching the hands, the
owner's annotations by voice, a compaction cut that keeps the fence, and
todos that land on the Door — never a parallel list.

## D1 — modes as recipes (story 01)

- Recipes gain additive `kind TEXT NOT NULL DEFAULT '' CHECK(kind IN
  ('', 'mode'))`; a mode = a recipe row {name, colour in `avatar`,
  system_prompt, tools_json = allow-list}. `threads.recipe_id` binds a
  thread to its mode (no `mode_id`; one binding).
- Seeds (`holdspeak/seeds/fresh-desk.yaml`, ids `hs-seed-mode-*`), the
  allow-lists (S4), sourced from `thread_tools` classes:
  **Desk** = every evidence_read + candidate_builder (no effects);
  **Chase** = Desk + the People and follow-through effects
  (`people.commitment.transition`, `people.agenda.add`,
  `people.note.create`, `follow_through.complete`,
  `follow_through.commit_decision`, `door.add_item`);
  **Draft** = no tools; **Plan** = `thought.*` reads + `door.get` +
  `memory.search` + `decision_record.*` reads.
- The executor's palette = the mode's allow-list ∩ the classification
  map; the truth table still gates effects. Mode tabs on the composer
  head (Desk · Chase · Draft · Plan · custom); switching writes
  `threads.recipe_id` and applies from the NEXT turn.

## D2 — prompts + slash verbs (story 02)

- A prompt = a Note tagged `prompt`; `GET /api/notes?tag=prompt` (json_each).
- `ThreadComposer` slash commands gain arguments: `/mode <name>`,
  `/prompt <name>` (inserts the note body), `/compact`, `/todo <text>`,
  `/tools` (lists the mode's palette), `/guardrail on|off <name>`; `/`
  only at line start (R3). Still the registry: each slash command maps
  to a registered verb id.

## D3 — guardrails (story 03) — M8

- Capabilities `chat.guardrail` (output `{violations[], warnings[]}`)
  and `chat.compact` (output `{summary}`), sealed, `structured_output`,
  assignment chains backfilled from `chat.turn` (the owner points them
  at a cheaper model in Assignments).
- A guardrail = a Note tagged `guardrail` {instruction, trigger tools,
  N messages}; seeds `effect-guard` (any effect touching a person's
  ledger without a named source) and `egress-guard` (cloud egress of a
  `people.*` read); enabled per mode (`tools_json` sibling key
  `guardrails`).
- Timing: tool_calls extracted → guardrail assignment runs ONCE with
  (last N + pending calls) → `thread_guardrail` frame + row
  (violations/warnings) → THEN the per-call admission. Advisory only:
  yolo proceeds; safe/neutral flips the decision box default to Deny.
  Never auto-denies. Guardrail failure = warning row `guardrail_failed`,
  never a block.

## D4 — annotations (story 04) — S5

- Select text in an assistant part → in-flow popover (comment field
  WITH mic; no modal) → `annotation` part on a DRAFT user message
  (`thread_message_parts.draft INTEGER NOT NULL DEFAULT 0`, additive);
  chips above the composer; Send promotes the draft (draft=0) and the
  assembler prefixes "The owner annotated: …" per part; survive reload.

## D5 — compaction + todo (story 05) — M7

- `/compact` → `chat.compact` over the leaf path → a `system` row whose
  `stats_json` = `{"compaction": true, "cut_at": <message_id>}` and a
  text part = the summary; the assembler includes only that row and
  what follows; the summary part inherits `sensitive=1` when any
  summarized part was sensitive and its text joins `_sensitive_texts`.
- Todo: `action_items.meeting_id` becomes nullable + additive
  `source_type`, `source_ref`; `DoorService.add_item`; MCP
  `door.add_item` (effect_proposal) with `source_type='thread'`; the
  Door card gets a `thread` provenance case ("from a thread" chip
  opening the pullout). `/todo <text>` and the model's `todo_write`
  both go through it.

## D6 — the walk (story 06)

Counsel legs: real `.43` — mode switch Desk→Chase, `effect-guard` fires
on a `people.commitment.transition`, annotation round-trip by voice,
`/compact` (visible cut; post-cut turn's payload contains only the
summary + after), `/todo` lands on the Door; People boundary through
`egress-guard` (violation row; safe-mode default flips to Deny); glass
1440 + 393 (mode tabs, guardrail row, annotation chips, cut marker, the
Door card with thread provenance). Docs; close counsel.

Recorded: R3 (`/` at line start only).
