# HS-153-06 - The walk and the close

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
- **Depends on:** HS-153-01, HS-153-02, HS-153-03, HS-153-04, HS-153-05
- **Unblocks:** HS-154-01
- **Owner:** unassigned

## Problem

The Practice is claimed only when it has been walked on real metal and
real glass, its docs touched, and close counsel heard (settled design
D6; the arc rhythm).

## Scope

- **In:** the metal script `assets/story-06-metal.py` on `.43`
  (tool-qualified deployment): Desk→Chase switch; `effect-guard` fires
  on a `people.commitment.transition`; annotation round-trip by voice
  (mic pipeline through the real hub); `/compact` with a visible cut and
  the post-cut payload captured; `/todo` on the Door; `egress-guard`
  violation on a `people.*` read under a cloud override (safe-mode default
  flips to Deny). Glass `tests/e2e/test_hs153_practice_glass.py` 1440 +
  393: mode tabs, guardrail row, annotation chips, cut marker, Door card
  with thread provenance; shots to `assets/story-06-shots/`; one shot
  exhibit artifact for the owner. Docs: README / USER_GUIDE /
  MCP_SIDECAR entry points (tool count arithmetic = `len(TOOLS)`),
  the Desk Chat plan §6.5–6.6 marked shipped. Close counsel
  (opus, RATIFY / RATIFY-W-C / REJECT; must-fixes in-round). Honest
  sweep: name-diff against main's latest run; web baseline zero
  branch-new; `git checkout -- pm/roadmap/holdspeak/phase-14*` after rigs.
- **Out:** 154 The Call.

## Acceptance criteria

- [ ] Metal script: every leg PASS on `.43`, payloads kept under `assets/story-06-metal-payloads/`.
- [ ] Glass: both widths, all five rooms, zero horizontal overflow; exhibit link in the evidence.
- [ ] Close counsel recorded in `assets/counsel-close.md` with zero open must-fix.
- [ ] Docs entry points touched; `git grep -i warpdrv` hits only the plan + phase records.

## Test plan

- **Unit:** the full scoped set of 153 tests + the 152 set (regression).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py`; the metal script.
- **Manual / device:** the owner's attended leg holds the merge word.

## Notes / open questions

- The `.43` tool qualification seeded in HS-152-06 is reused; do not re-qualify.

## Glass

`tests/e2e/test_hs153_practice_glass.py` -- 6 legs, both widths (1440 + 393).
All 6 passed in 238.81 s. Zero horizontal overflow assertions exist in every leg
(body.scrollWidth <= window.innerWidth + 1).

| Leg | Test | Rooms |
|---|---|---|
| 1 | `test_modes_tabs_render_and_switch` | Mode tabs initial, Chase active, Draft active, unbound |
| 2 | `test_slash_completion_and_prompt_insert` | Slash palette, /mode args, /mode chase picked, /prompt args, /prompt inserted, Esc closes |
| 3 | `test_guardrail_row_renders_and_deny_focused` | Guardrail row, decision box (Deny primary + focused) |
| 4 | `test_annotation_popover_and_chips` | Annotation popover (MicButton present, bounding box inside viewport), chip, reload persists, Send promotes |
| 5 | `test_compact_cut_marker_and_fold` | Cut marker visible, RAW fold shows summary, earlier-messages fold |
| 6 | `test_todo_receipt_and_door_card_chip` | Todo receipt (tool_call part), Door card thread chip |

12 shots selected to `assets/story-06-shots/` (best per room, both widths):

- `mode-tabs-1440.png`, `mode-tabs-393.png`
- `slash-popover-1440.png`, `slash-popover-393.png`
- `guardrail-row-1440.png`, `guardrail-row-393.png`
- `annotation-chip-1440.png`, `annotation-chip-393.png`
- `cut-marker-1440.png`, `cut-marker-393.png`
- `door-thread-chip-1440.png`, `door-thread-chip-393.png`

Build step: `npm --prefix web run build` before the glass run.
Cleanup: `git checkout -- pm/roadmap/holdspeak/phase-141-* ... phase-147-*`
confirmed no leftover modifications outside phase-153.

## Docs

### Files touched

| File | Change |
|---|---|
| `README.md` | Threads paragraph gains modes, saved prompts, guardrails, annotations, `/compact`, `/todo` to the Door (six lines, canonical names, no prohibited nouns) |
| `docs/USER_GUIDE.md` | Six new subsections under "The Thread has hands": Modes (palette table), Saved prompts, Guardrails, Annotations, Compaction, Todo, Slash commands (grammar table: 10 verbs, `/` at line start) |
| `docs/MCP_SIDECAR.md` | `door.add_item` description added to the door (2 tools) section (effect tool, source_type='thread', provenance chip) |
| `docs/internal/PLAN_PHASE_DESK_CHAT.md` | Status line: DC-03 shipped as Phase 153; section 6.5 and 6.6 marked SHIPPED |

### Tool count arithmetic

`len(TOOLS)` = 142, 31 families. Unchanged from Phase 152 -- `door.add_item`
was already registered. All stated counts in `docs/MCP_SIDECAR.md` and
`docs/README.md` remain 142 and pass `test_mcp_tool_count_claims_match_registry`.

### Constitution check

`docs/internal/CONSTITUTION.md` mentions neither "chat" nor "thread" outside
its amendment history. No update needed.

### Test results

- `test_doc_drift_guard.py`: 26/26 passed (0.89 s), including `test_mcp_tool_count_claims_match_registry`.
- `test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift`: pre-existing failures only (25 violations in MEETING_MODE_GUIDE, SECURITY, USER_GUIDE lines 332-342/694/1411, AssignmentEditor, DoorBoardLane, Pullout, ThoughtWorkspaceWindow -- all "model profile" legacy-product-nouns or failure-missing-facts). Zero new violations from these edits.

### warpdrv grep

`git grep -i warpdrv` hits 27 files, all in:
- `docs/internal/PLAN_PHASE_DESK_CHAT.md` (the plan itself)
- `pm/roadmap/holdspeak/` (BACKLOG, HANDOVER, README, phase-151/152/153 records)

Zero hits in source code, user-facing docs, or test files.

## Metal walk

Script: `assets/story-06-metal.py`
Model: Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf on `.43`

### DRY results (fake engines, sandboxed)

Command: `uv run python pm/roadmap/holdspeak/phase-153-the-practice/assets/story-06-metal.py`
Total: 9.7 s, 6/6 PASS, 0 failures.

| Leg | Description | DRY |
|-----|-------------|-----|
| 1 | Mode switch Desk->Chase->Draft; palette checks | PASS (Desk 55 tools excludes 6 effects; Chase 61 tools includes people.commitment.transition; Draft 0 tools) |
| 2 | effect-guard fires; safe=deny, yolo=proceeds | PASS (guardrail part + violations; pending frame default_decision=deny; yolo tool not denied) |
| 3 | Annotation round-trip: POST, draft, Send promotes | PASS (annotation kind=annotation, draft=True, prefix "The owner annotated:", promoted after send) |
| 4 | /compact after 3 turns; post-cut payload | PASS (compaction system row, cut_at present, post-cut payload excludes pre-cut text, contains summary) |
| 5 | /todo -> action_items row source_type='thread' | PASS (receipt_id, DB row, action-items API shows thread-sourced item) |
| 6 | egress-guard cloud override; safe=deny; redaction | PASS (guardrail part + violations; pending default_decision=deny; cloud payload has [people content withheld]) |

Payloads: `assets/story-06-metal-payloads/`

### LIVE results (.43 Qwen3.6, unsandboxed)

Command: `HS153_LIVE=1 uv run python pm/roadmap/holdspeak/phase-153-the-practice/assets/story-06-metal.py`
Total: 154.0 s, 6/6 PASS, 0 failures.

| Leg | Description | LIVE | Note |
|-----|-------------|------|------|
| 1 | Mode switch Desk->Chase->Draft | PASS | recipe_id set; Desk tool=desk.snapshot (evidence_read); Draft no tool_call parts |
| 2 | effect-guard fires; safe=deny, yolo=proceeds | PASS | Guardrail part + violations ("people.commitment.transition written without source"); pending default_decision=deny; yolo proceeds with receipt |
| 3 | Annotation round-trip | PASS | POST 201, annotation prefix, draft, promoted after send |
| 4 | /compact after 3 turns; post-cut payload | PASS | compact status=ok, cut_at present, compaction system row, summary captured |
| 5 | /todo -> action_items row source_type='thread' | PASS | receipt tr-0e8c0c251a91, DB row source_type='thread', action-items API 1 thread-sourced item |
| 6 | egress-guard cloud override; safe=deny; redaction | PASS | Guardrail part + violations ("people.readiness to cloud egress boundary"); pending default_decision=deny; cloud payload carries [people content withheld] |

Payloads: `assets/story-06-metal-payloads-live/`

Leg timing: leg1=25.1s, leg2=33.4s, leg3=18.5s, leg4=58.1s, leg5=9.8s, leg6=7.0s.

**HS-153-06 guardrail JSON fix:**

1. **Default grammar override** (`grammar: ""` in request body): the `.43`
   llama.cpp server runs with a default grammar (the dictation `{"line": ...}`
   schema) that forces every free-text completion through it; `grammar: ""`
   clears it.  Applied in `MeetingIntel._extra_body(has_tools=False)` for
   custom endpoints, and in the metal script's `_LiveEngine`. NOT sent alongside
   tool calls (tools carry their own constrained-decoding grammar).
   **Environment finding for the owner:** plain no-tools turns on `.43` were
   being forced into the dictation grammar; the `grammar: ""` override now
   shields the product.
2. **json_schema response_format** for `chat.guardrail` and `chat.compact`:
   sealed schemas (`{violations: [str], warnings: [str]}` and `{summary: str}`)
   in the payloads, forwarded through `CanonicalPromptAdapter` ->
   `MeetingIntel.run_prompt` -> `_chat_completion_text` -> OpenAI client / local
   llama-cpp-python. Constrains output to exact keys.
3. **Robust parser** (`_extract_structured_json` in `thread_practice.py`):
   strips `<think>...</think>` blocks, tries markdown-fenced JSON, then scans
   for the first balanced `{...}` substring. Belt-and-suspenders behind the
   schema. 12/12 unit tests (`test_thread_practice_parser.py`).

### Defect found

**action_items LEFT JOIN (HS-153-06 fix):** `list_action_items` and
`get_action_item` in `holdspeak/db/meetings.py` used INNER JOIN on the
`meetings` table, which excluded thread-sourced action items whose
`meeting_id` is NULL. Fixed to LEFT JOIN. `_row_to_action_item_summary`
now handles NULL `meeting_date` (`datetime.min` sentinel). `ActionItemSummary`
model (`holdspeak/db/models/__init__.py` and `holdspeak/db/models/actions.py`)
gained `source_type` and `source_ref` fields. `_action_item_payload` in
`holdspeak/services/meeting_service.py` handles `datetime.min` and exposes
`source_type`/`source_ref` in the API response.

Scoped tests: `tests/unit/test_thread_todo.py::TestActionItemsListingDefect`
(2 tests: `test_list_action_items_includes_thread_sourced`,
`test_get_action_item_finds_thread_sourced`). 8/8 passed (7.91 s).

### Voice annotation

The voice part of LEG 3 (mic pipeline through the real hub) is the
owner's attended leg, not tested in this script.


## Exhibit

Shot exhibit for the owner (12 shots, six rooms, both widths, the metal
table): https://claude.ai/code/artifact/33bb0b5b-1c78-4f8f-977d-258f7cb81d64


## The honest sweep

Full isolated suite (`-n 6`, metal excluded), final run after all close
fixes: **11 failed / 7313 passed / 53 skipped**. Name-diff against
main's latest run (`33283941973`, 41 names): **one** name survived —
`test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config`.
Investigated: passes 3/3 alone; the differing key is
`hardware.capability` (the probe includes `available_memory_bytes`, a
live value that drifts under parallel load); `git diff 816a73cb..HEAD`
touches nothing in that module. Verdict: load-induced flake of the
snapshot-equality fence, not branch behaviour. Web baseline: zero
branch-new. Earlier sweep's 13 branch-new fences all resolved
(API-surface manifest, schema snapshot, seed manifest counts, the 143
censuses, `_resolve_deployment_revision` classification).
