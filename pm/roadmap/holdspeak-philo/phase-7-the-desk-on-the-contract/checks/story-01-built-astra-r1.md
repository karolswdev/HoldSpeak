VERDICT: RATIFY-WITH-CONDITIONS — merge after findings 1 and 2 are resolved.

FINDINGS:

1. **The rig silently changes canonical calls.** `scripts/graph_walk.py:816` drops every argument except the ID for the six new read/delete projections. Reproduced through the real hub:
   - `note.delete` with valid Thought revisions loses those revisions and returns `thought_expected_revision_required`; direct invocation succeeds.
   - `note.delete {note_id:"n", owner:"forged"}` is refused by the registry with `authority_in_arguments`. The projected call deletes the note: the resulting DB row is `id=n, deleted=1`.
   
   This fails Tenet 3 and Article IX: the verifier exercises a different request. [Retained reproductions](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-philo7-check-dmx7a34e/probe-built.jsonl:8).

2. **The KB admission condition misses an accepted filing effect.** `holdspeak/operations.py:908` requires a nonempty **list** or supplied `kb_id`. On both main and built, MCP accepts `{"name":"K","member_ids":{"note:n":true}}` without `kb_id`. The repository iterates the dictionary’s keys at `holdspeak/db/primitives.py:406`, creating a live membership. My built DB contains `knowledge_id=kb_f6f0c2b3b01e, resource_ref=note:n, deleted=0`. The declaration therefore labels a real filing effect exempt. This fails Tenet 3 and Article XI.1. The admission fence checks the rule and argument names, but only checks that the condition text is nonempty (`tests/unit/test_philo7_contract.py:115`).

3. **The rename repairs are real and ratified.** The interleaving wrapper returns the actual read unchanged, then performs another real service call (`tests/unit/test_philo7_rename_repair.py:48`). Both fences independently failed on archived `02a862f2` with the reported lost membership/restored `p1`, and passed on built. I also reproduced deletion during each rename: main resurrects; built returns `NotFound`. That change and the empty-KB-update change are lawful and explicitly recorded in `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/evidence-story-01.md:48`.

4. **Compatibility and the zone alias repair hold in the checked scope.** Main’s real `/api/mcp` reproduces `create_directorie`; built creates the zone. The alias at `holdspeak/mcp/tools.py:38` is minimal; I found no dependency requiring the misspelling. I found no input narrowing in the fifteen descriptors against the existing adapters and service signatures. The named refusal changes are declared. The four Phase 5 edits expand name sets, strengthen the shelf assertion, or add a real producer; they do not weaken their existing fences.

5. **Keep the shelf enum removal.** The states remain discoverable, and unknown strings now reach the declared service refusal through both transports. The real-producer fence checks registry reach and unchanged storage (`tests/unit/test_philo7_shelf_alignment.py:81`). I reproduced its main red and built green. No additional validation layer is needed.

6. **Accounting and records check out.** Independently: 293 residual identities on built; exactly 27 reappear against archived main—24 MCP and 3 HTTP. Both hubs publish 228 tools. The HTTP fallback constructors left the routes, so PAID matches the stated census. Generated operations, API reference and roster checks pass. Story status, phase row and README stamp agree. My scoped runs passed **290 + 4 tests**; the retained 1,293-test run remains the author’s separate evidence.

CONDITIONS:

- Guard all six read/delete projections against discarded arguments. Explicitly block unsupported revision-bearing calls, or provide a faithful transport path. Add real-hub regression fences showing refusal cannot become execution and valid revisions cannot disappear.
- Correct `kb.create`’s admission condition to cover accepted membership-producing inputs, including dictionaries. Preserve existing acceptance; regenerate the export and add the compatibility/effect fence.
- Record these corrections and their red/green evidence before merging.

MISSED:

1. Highest cost: the rig can invalidate the forthcoming refusal and receipt proofs while still producing successful calls.
2. Next: type-permissive compatibility must also inform admission conditions.
3. During merge, preserve main `dcf3eaeb`’s R5: `decision.delete` belongs in the grant. This branch’s older phase text still excludes it.
4. Minor discovery debt: “including optional id” at `holdspeak/mcp/tools.py:84` remains misleading where literal `data.id` is refused.

TUESDAY: The checked hub supports making, filing and finding these objects; a tired owner’s cold-client and Desk experience remains unproved until stories 03–04.

UNKNOWN: No browser/atlas walk or full suite run by me, as instructed. PR #657 reported no status checks when inspected. Exact m1–m9 mutation patches were not independently replayed. The reviewed worktree remains unchanged at `2ad17ee8`.