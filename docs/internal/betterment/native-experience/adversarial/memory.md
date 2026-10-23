# memory — Search memory and inspect a sourced result

Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd`  
Reviewer task: `review_memory`  
Evidence class: source and representative assertions, plus historical captures; no tests, walks, or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The real job is: open Memory from Go, ⌘K, or a `q:` deep link; type or speak a question; distinguish a hit, miss, or unavailable read; inspect the source; return to the query; then repeat. A senior architect also needs “What I owe” without an Ask. The manifest sends `open-project-memory` to `MemoryCore` (`web/src/desk/applications.ts:359-374`). That core sends project scopes to Room, `q:` scopes to `RecallFace`, and an unscoped open to pages plus Ask (`web/src/pages/cores/MemoryCore.tsx:113-177,197-201`). ⌘K is a third path calling `/api/memory/search` and filtering hits by opener (`web/src/desk/components/DeskToolShelf.tsx:492-504,876-925`). The audit must name the canonical split, durable result identity, source display, stale-source recovery, and return behavior; “collection/detail contract” is too vague.

FINDINGS:

1. **High — the same Memory job has three unjoined entry/result contracts.** Go Memory is answer-first, RAW contains recall, and ⌘K opens Ask or an object; `ProjectMemoryCore` is only a re-export (`web/src/pages/cores/ProjectMemoryCore.tsx:1-9`). Owner cost: Tuesday search becomes “which Memory?” and return behavior is unspecified. This fails Tenets 2 and 3. Correction: retain one Memory app/window identity and specify the shared query/result/source/return contract; keep Room and Ask as scoped consumers, with `q:` a deep link, not another surface.

2. **High — broad search capability silently drops or strands result kinds.** The backend searches `decision_record`, `project_item`, and `workbench_item` among other ecosystem kinds (`holdspeak/db/memory.py:1054-1069`), while ⌘K drops any hit without `refOpener` (`web/src/desk/components/DeskToolShelf.tsx:883-895`). Recall rows can render kinds with no opener (`web/src/features/project-room/recall/RecallFace.tsx:281-310`), and the citation contract deliberately has no window for several source kinds (`web/src/desk/surface/citations.tsx:24-36`). Owner cost: a relevant result is absent or looks inspectable but cannot be opened. This fails Tenets 3 and 5. Correction: either bound the audit to openable kinds and label display-only evidence, or route each named kind through an existing primitive/Room; do not add dead verbs.

3. **Medium — failure and retry are inconsistent.** Recall names `CANT SEARCH` and offers Retry (`web/src/features/project-room/recall/RecallFace.tsx:409-417`), but ⌘K converts a failed search to an empty hit list (`web/src/desk/components/DeskToolShelf.tsx:497-502`), and pages intentionally swallow a failed read as absence (`web/src/desk/standingPages.tsx:7-10,121-126`). Owner cost: “nothing found” and “memory is unavailable” are indistinguishable, with no fast recovery. This fails Tenets 3 and 6. Correction: share a named read state, preserve the query/result, offer Retry, and return to the same Memory context after source inspection.

## Convergence

Within `memory`, use the existing catalogue capability `knowledge.memory_search` for one source-ref/result contract; first consumers are Memory and ⌘K, with catalogue capability `knowledge.grounding` remaining the model-facing reader. These are capability IDs, not extra workflow families. Converge `source_context` and `navigation_commands` through existing `openRef`/`openSourceRef` and the manifest, not a new router. `ask_whole_desk` consumes the same question text but must remain the Ask/thread result path. Keep `speech_learning` separate: DictationCore’s SPEAK/JOURNAL/LEARNED wings (`web/src/pages/cores/DictationCore.tsx:38-48,122-132`) and `voice.learning_digest` describe correction routing and replay, not long-horizon source retrieval. Do not merge these into a generic explorer; that would erase useful boundaries and violate Tenet 3.

## User experience

Source suggests a pleasing “what do I owe?” path: Memory opens on pages, sources are explicit, and Ask is available. Historical 1440/393 captures (`docs/internal/betterment/asking/shots/25-memory-app-1440.png`, `34-memory-393.png`) show a legible recall face, but do not prove this baseline or owner delight. Ad hoc search is less pleasing: RAW, ⌘K, and Ask compete, and failed ⌘K reads are silent. Fix the query/source grammar and failure path before adding interfaces.

CONDITIONS: Name the canonical Memory entry and return flow; define openable versus display-only result kinds and source identity; add honest failure/retry behavior to ⌘K and pages; preserve the Dictation learning boundary.

MISSED: (1) parked/deleted source after a hit, highest return risk; (2) a workbench or decision-record hit that search finds but UI cannot inspect; (3) repeated query after reopening, including filter and scroll; (4) learning correction/replay versus memory search, ranked by owner confusion.

TUESDAY: Pages can answer a known obligation in one press, but source search is not yet one dependable, recoverable job.

## Acceptance challenges

1. On a populated desk, Go ▸ Memory shows the standing answer; open its source, then return, and the same page/query remains visible.
2. Run the same question through ⌘K and `q:`; both preserve the query, identify the source, and open the same existing source surface.
3. Search for text that exists only in a `workbench_item` or `decision_record`; the result is either inspectable through an existing opener or explicitly display-only, never silently omitted.
4. Make `/api/memory/search` or `/api/memory/pages` fail once; the face names the failure, preserves input, offers Retry, and recovers without a second window.
5. Reopen after a successful search and separately correct/replay a phrase in Dictation; Memory restores its query while Dictation keeps its learning receipt.

UNKNOWN: No test, live provider/native boundary, current production shot, or owner acceptance. Meaning quality, owner labels, post-hit source existence, and full findability remain unproved.
