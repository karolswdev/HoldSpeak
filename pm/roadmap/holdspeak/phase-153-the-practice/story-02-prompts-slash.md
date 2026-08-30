# HS-153-02 - Prompts and slash verbs (notes tagged prompt, arguments)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
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

## What shipped

### Files changed

- **`web/src/desk/components/ThreadComposer.tsx`** -- expanded from 4 to 10 slash commands (keep, fork, stop, new, mode, prompt, tools, todo, compact, guardrail). Each entry now carries a `verbId` field mapping to the verb registry. Added `completeSlash(text, cursor, ctx)` pure function implementing two-stage completion: stage 1 = command filtering, stage 2 = argument completion (mode names from the modes API, prompt titles from `GET /api/notes?tag=prompt`, guardrail titles from `?tag=guardrail`). R3 rule enforced: `/` triggers only at column 0 of a line (start-of-text or after `\n`); mid-line `/` types a literal slash. Added `isSlashAtLineStart` helper. Added `loadPromptNotes()` and `loadGuardrailNotes()` lazy loaders (cached, same pattern as people). Added `SystemRow` component for in-flow feedback from slash commands (/tools, /todo, /compact, /guardrail show system-style rows). Added `onModeSelect` and `currentMode` props for `/mode` and `/tools` commands. `/prompt <name>` inserts the note body verbatim at the caret; mic-fill still works after (the textarea is focused with cursor at end). `/todo`, `/compact` show "not yet available" rows with `TODO(HS-153-05)` hooks. `/guardrail` shows "not yet" with `TODO(HS-153-03)` hook.
- **`web/src/desk/pullouts/ThreadPullout.tsx`** -- wired `onModeSelect` and `currentMode` props to ThreadComposer, delegating to the existing `setMode(threadId, recipeId)` store action.
- **`web/src/desk/pullouts/thread-pullout.css`** -- added `.thread-system-row` and `.thread-system-row-text` styles for in-flow slash command feedback (mono, muted, bordered).
- **`web/src/desk/verbRegistry.ts`** -- added `"thread"` to `VerbScope` union. Added 10 verb entries (`thread.keep`, `thread.fork`, `thread.stop`, `thread.new`, `thread.mode`, `thread.prompt`, `thread.tools`, `thread.todo`, `thread.compact`, `thread.guardrail`) in scope `"thread"`, palette `false`. Every `THREAD_SLASH_COMMANDS` entry maps to one of these.
- **`holdspeak/seeds/fresh-desk.yaml`** -- added second seed prompt `hs-seed-prompt-one-on-one-prep` ("1:1 prep", tags: [prompt]) so the completion list has 2+ items.
- **`tests/unit/test_notes_tag_query.py`** -- new, 9 tests: `TestListByTag` (6: single tag, multi-tag, no match, deleted excluded, deleted included, empty tag, multiple prompts), `TestPrimitiveServiceListNotes` (1: service layer with tag), `TestSeedPromptNotes` (1: seed creates >= 2 prompt notes).
- **`web/src/desk/__tests__/ThreadComposer.test.tsx`** -- extended from 20 to 46 tests. Added: `completeSlash` pure function tests (10: command completions, /mode d -> Desk/Draft, /mode empty -> 4, /prompt w -> Weekly, /prompt empty -> 2, mid-line / -> null, second line /, non-arg command + space -> null, guardrail args), `isSlashAtLineStart` tests (3), verb id well-formedness tests (2: all start with `thread.`, unique), mid-line / component test, Esc closes test, /tools system row test, /compact not-yet test.
- **`web/src/desk/__tests__/verbRegistry.test.ts`** -- added 1 test: every `THREAD_SLASH_COMMANDS` entry has a registered verb with scope `"thread"`.
- **`tests/e2e/test_hs153_practice_glass.py`** -- added `test_slash_completion_and_prompt_insert` leg at 1440 + 393: `/mo` popover shows /mode entry; argument stage shows Desk/Chase/Draft/Plan; Enter picks Chase, GET confirms `recipe_id = hs-seed-mode-chase`; `/prompt` argument stage shows seed titles; pick Weekly update, composer contains the body; Esc closes the palette; zero horizontal overflow. Shots to `assets/story-02-shots/`.

### The seam

`completeSlash(text, cursor, ctx)` is a pure, unit-testable function that owns all slash popover logic. The component's `updateAutocomplete` delegates to it. Argument data is lazy-loaded from the same API endpoints the rest of the desk uses (`/api/recipes?kind=mode`, `/api/notes?tag=prompt`, `/api/notes?tag=guardrail`). The verb registry is the single source of truth: every slash command has a `verbId` that maps to a registered verb, and the `verbRegistry.test.ts` asserts this mapping holds.

### Real-path defects found and fixed

1. **Glass test: React controlled input vs Playwright `fill()`/`press_sequentially()`.** Playwright's `fill()` and `press_sequentially()` set the textarea value but do not reliably fire React's synthetic `onChange` on controlled inputs in the Vite-built bundle. Fixed by using a JS helper that sets the value via `nativeInputValueSetter` and dispatches `input`+`change`+`select` events, which React's delegated event system picks up. Keyboard events (Enter, Escape) work with `page.keyboard.press()` / `page.keyboard.type()`.
2. **Glass test: Escape after JS-driven value change.** After setting the value via the native setter, the textarea may lose focus; a subsequent `composer.press("Escape")` then targets nothing. Fixed by typing "/" via `page.keyboard.type("/")` (after `composer.click()`) for the Esc test, ensuring focus is maintained throughout.
3. **Web bundle staleness.** The glass test runs against the Vite-built bundle in `holdspeak/static/_built/`. Changes to `.tsx` files require `npm run build` before glass tests reflect them. The old bundle still served the previous slash code. Rebuilt before running the glass leg.

## Notes / open questions

- Argument completion is a second stage of the same popover, not a second popover.
- The `TODO(HS-153-05)` hooks in `/todo` and `/compact` handlers are clearly marked and ready for story 05 to wire to the backend.
- The `TODO(HS-153-03)` hook in `/guardrail` is ready for story 03.
- The web bundle (`holdspeak/static/_built/`) is gitignored; the orchestrator's build step must run before glass tests after any `.tsx` change.
