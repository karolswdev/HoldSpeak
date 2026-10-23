# knowledge_drawers — Keep reference material in a named drawer and use it as context

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_knowledge_drawers`  
Evidence class: active React/TypeScript and backend source, representative assertions, and prior shell captures; no execution or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts with an existing knowledge collection, or with a note/object filed into one. The user finds the named collection, opens it, sees authoritative members (including empty, unavailable, and stale states), opens a member, and returns. The second path is About: find the collection, attach it to Ask, submit an immutable context snapshot, then reopen the saved thread with that reference. Q10 removes New Knowledge, keeps KB tools, and does not migrate KB rows into directory rows (`docs/internal/betterment/asking/RECIPE.md:307-320`).

The active KB host is `KbPullout`, selected by the registry (`web/src/desk/pullouts/registry.ts:26-40`), and member presses call `openScreenRef` (`web/src/desk/pullouts/KbPullout.tsx:42-59`). `DrawerWindow` is a retained project/restoration host with singular selection; current project doors open Room (`web/src/desk/drawer/DrawerWindows.tsx:10-13`; `web/src/desk/screen/open.ts:22-27`) (`web/src/desk/drawer/DrawerWindow.tsx:134-149`).

FINDINGS:

1. **P0 — The audit points at the wrong recipe and omits the authoritative read contract.** Its `docs/internal/betterment/asking/RECIPE.md:129-133` anchor is Q3, not Q10. Q10 names `primitive_service.py` and `tests/unit/test_desk_drawers.py`, but the inventory and brief omit them. The backend merges stored `member_ids`, live edges, and tombstones (`holdspeak/services/primitive_service.py:293-323`); the assertion covers add/remove through that edge store (`tests/unit/test_desk_drawers.py:26-42`). Owner cost: stale or duplicate membership; this fails Tenets 3 and 5. Correction: state this merge, ordering, and removal contract.

2. **P1 — The boundary between KB and project/explorer drawers is ambiguous.** `KbPullout` has rows but no selection, while retained `DrawerWindow` has `selectedId`, modes, and Room actions (`web/src/desk/pullouts/KbPullout.tsx:42-83`; `web/src/desk/drawer/DrawerWindow.tsx:241-307`). Owner cost: a project-host rewrite, failing Tenets 1, 3, and 5. Correction: bind this audit to KB membership, open identity, and Ask context; decide whether KB needs scoped selection. Do not require range selection or cross-window drag unless Q10 expands.

3. **P1 — Filing, Ask context, and return/recovery are not connected.** `DeskFilingStrip` has retry/failure states (`web/src/desk/components/DeskFilingStrip.tsx:46-66,102-105`) and toggles KB membership (`:160-174`); About offers KB by name (`web/src/desk/components/about/AboutPicker.tsx:68-72`). But `KbPullout.test.tsx:45-88` covers only rows, unavailable members, copy, and empty state. Owner cost: a Tuesday trust gap, failing Tenets 3 and 7. Correction: add the add/remove → refresh/reopen → Ask snapshot → saved-thread return path while preserving those guards.

## Convergence

Converge with `drawers` for collection view identity, persistence, and any future scoped selection; its active first consumers are `DirectoryPullout` and `KbPullout`; retained `DrawerWindow` is not a production-adoption target, not a reason to replace the KB provider. Converge with `objects_pullouts` for `openScreenRef` and object verbs, `source_context` for the KB ref/chip, and `ask_whole_desk` for Ask's immutable request and thread reopen. `notes_editor` remains the member editor and owns text recovery. Keep KB membership/edge semantics separate from directory membership and repository transfer: Q10's explicit counterargument is that KB rows do not become directory rows.

## User experience

Source suggests a fast path: a named collection exposes Contents, members open through the Desk grammar, and About finds the same name. Assertions preserve empty versus unavailable (`web/src/desk/pullouts/KbPullout.test.tsx:48-88`). Optional captures show the project shell at 1440 and 393 (`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/surface-projects-1440.png`, `surface-projects-393.png`), but no KB capture was inspected, so craft and owner delight are unknown. The KB sprite aliases `artifact` (`web/src/desk/sprites.ts:29-34`); verify that a named drawer reads as one live. Improve one-press use and operation receipt; do not add a wizard.

CONDITIONS:

1. Correct the Q10 source anchor and include the backend merge/tombstone contract.
2. Bound KB versus project/explorer behavior and name the first selected/context consumer.
3. Add the filing, Ask, refresh, failure, and return scenarios below at both sizes.

MISSED:

1. **High:** Existing-only versus creation boundary after New Knowledge was parked.
2. **High:** Edge-store add/remove, tombstoned members, refresh, and repeated opens.
3. **Medium:** KB picked in About, Ask answer kept, and thread reopen/return.
4. **Medium:** Large list, unavailable member, empty collection, and filing retry.

TUESDAY: Existing KB use could be quick, but this audit is not yet sufficient until membership authority, Ask context, and return behavior are one clear path.

## Acceptance challenges

1. Open an existing KB containing a stored member, an edge-only member, a tombstoned member, and an unresolved ref: show each honest state, hide the removed member, and open/return from a real member at 1440 and 393.
2. From a note, add and remove KB membership through the existing filing strip; a refusal is named with Retry, and a refresh/reopen reflects the authoritative edge without duplicates.
3. Search the KB name in About, add it, submit Ask, then reopen the kept thread: the payload and follow-up retain `kb:<id>` rather than silently reverting to whole-Desk context.
4. Open the same KB repeatedly while switching to its member and back; one collection identity remains, and an empty or unavailable read never claims success.

UNKNOWN: No tests, builds, live Desk/API/provider/native actions, performance/accessibility checks, or owner walk were run. The captures are prior project-shell evidence, not KB acceptance.
