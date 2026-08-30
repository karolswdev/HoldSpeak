# HS-153-02 - Prompts and slash verbs (notes tagged prompt, arguments)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-153-01
- **Unblocks:** HS-153-05, HS-153-06
- **Owner:** unassigned

## Problem

A saved prompt is desk material, not a chat-only list: a Note tagged
`prompt` (settled design D2). The composer's slash commands (keep /
fork / stop / new) gain arguments and become the practice's verbs —
still registry verbs, `/` only at line start (R3).

## Scope

- **In (data layer — LANDED `9cb769a9`, verify):** `GET /api/notes?tag=`
  (json_each over `tags_json`), seed prompt notes.
- **In (this story):** `ThreadComposer` slash grammar with arguments:
  `/mode <name>` (binds via 01), `/prompt <name>` (inserts the note body
  at the caret, mic-fill still works), `/tools` (lists the current
  palette as a system-style row, in-flow), `/todo <text>` and
  `/compact` (wired in 05; here they register and show "not yet" until
  05 lands — no dead menu items after 05), `/guardrail on|off <name>`
  (03). Completion popover for the argument (mode names, prompt titles)
  reusing the existing slash filter; every command maps to a registered
  verb id in `verbRegistry.ts`.
- **Out:** prompt editing (that is the Note editor), prompt sharing.

## Acceptance criteria

- [ ] `filterSlashCommands` returns argument completions for `/mode d` → Desk/Draft and `/prompt <partial>` → matching note titles; `/` mid-line does nothing.
- [ ] `/prompt <name>` inserts the note body verbatim; `/mode chase` PATCHes `recipe_id` and the tab moves.
- [ ] Glass 393: the completion popover fits (no overflow), Esc closes it, Enter picks.

## Test plan

- **Unit:** vitest `ThreadComposer` slash grammar + `verbRegistry` mapping; `tests/unit/test_notes_tag_query.py` (or the existing notes route test extended).
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `slash`.
- **Manual / device:** story 06.

## Notes / open questions

- Argument completion is a second stage of the same popover, not a second popover.
