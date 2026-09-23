# PHILO-3-04 canvas: the thought's receipt

`thought-receipt.html` is one self-contained page. It has no external fetches. It inlines the token `:root` from `web/src/styles/tokens.css` (generated from `web/design-tokens.json`), the @fontsource woff2 files that `global.css` imports, and the library rules it reuses, and it names the source of each rule. Shots: `canvas-1440.png` and `canvas-393.png` (Playwright headless, full page).

## The four states (the foot's receipt slot, two lines)

| # | Line 1 (the write) | Line 2 (filing) | Verbs |
|---|---|---|---|
| 1 | `KEPT · 14:32` (`--text-muted`) | `IN <drawer>` or `NOT IN A DRAWER` (`--text-faint`); ` · FINISHED` joins it | Change · Finish |
| 2 | `SAVING…` (after an edit, during the 450 ms wait and the PATCH) | same | Change · Finish |
| 3 | `DID NOT SAVE · <cause>` (`data-tone="danger"`) | same | Retry · Change · Finish |
| 4 | `CHANGED ELSEWHERE` (`data-tone="danger"`) | same | Reload · Change · Finish |

Finish becomes Resume on a finished thought, as it does today. Retry replaces today's "Try again". At 393 the receipt takes the whole second row of the foot (the SurfaceFooter narrow default). The Thought face's `"receipt verbs"` override does not apply to it.

Proposed causes for line 1 of state 3 (ASD-STE100): a fetch that throws (no response) → `THE HUB DID NOT ANSWER`; an `ApiError` with a status → `THE HUB DID NOT ACCEPT THE CHANGE`.

## Seams to bind (the writer → the foot)

- **Kept time.** Success path `web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:131-137`. Keep `result.thought.working_note.last_modified` (the server stamps it: `holdspeak/services/refinement_thought_service.py:1892`) as `keptAt` state. Format it with the existing species `web/src/desk/keptReceipt.ts:12` (`Kept · <time>`, the viewer's locale). Before the first edit, show the loaded note's `last_modified`.
- **Pending.** `edit()` at `useThoughtNoteWriter.ts:211` sets `dirty` (a ref) and `schedule()` at :205 waits 450 ms. `saving` (:107) is true only while the request is in flight. The foot needs one `pending` state: true from `edit()` until success or failure.
- **Failure.** Catch path `useThoughtNoteWriter.ts:195-198`. Keep the cause token for line 1. The prose message there ("Could not save this thought…") and the conflict prose at :94 leave the face. The foot states the fault.
- **Foot.** `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:484-491` (receipt and verbs). The message line at :468-471 stops showing writer save prose.
- **Filing line.** Today the projection has only `filing_status` (`refinement_thought_service.py:1716`, :1885). The drawer name for `IN <drawer>` needs `directory_memberships.directory_id` (`holdspeak/db/schema.py:1605`) resolved to its name and added to the thought projection.
- **CSS.** One face rule on the existing hook: `.thought-note-foot .surface-footer-receipt { flex-direction: column }` + filing line `--text-faint`. No new species, colour or font.

## Library debt the canvas shows (build must pay in the library)

`web/src/desk/surface/surface-footer.css` still sets `.surface-footer-receipt-line` and `.surface-footer-egress` at **10 px**, which is below the 12 px floor (type-scale ruling 2026-09-21). The canvas draws them at 12 px. `.surface-receipt-line` (`surface.css:2743`) is 11 px. Both are library fixes, not face fixes.

## Ratification question

Do you ratify this foot: `KEPT · <time>` from the last successful write, separate `SAVING…`, `DID NOT SAVE · <cause>` with Retry, and `CHANGED ELSEWHERE` with Reload, with the filing state on its own line below?
