Everything is verified from the tree and the four observations. Check follows.

# Check — Muad'Dib, 2026-09-24 (r2, the .op sibling setup)

Read-only check of the bounded case amendment. No edits, no agents, no hub, no walk.

**VERDICT: RATIFY-WITH-CONDITIONS**

**FINDINGS**

1. **Astra's root cause is correct and the earlier ordering theory is disproved.** The route at `holdspeak/web/routes/decisions.py:58-61` calls the contract's decision.read, catches NotFound, then calls the legacy lifecycle service. The MCP path reaches only the primitive service. Both browser runs at 22:26:49Z and 22:27:45Z carry two broke rows, lifecycle then primitive, with distinct pipeline-event source refs. Both .op runs at 22:28:57Z and 22:30:16Z carry one row, primitive only, and blocked at the capture step with the message "capture_match at sections.broke matched 0 rows". One cause, two events on HTTP, one on MCP. This is a compatibility fallback, not a duplicate decorator.

2. **The proposed setup normalization is lawful and inside the charter.** The .op sibling already runs three real HTTP setup steps against the same hub for engine selection. Adding a fourth, the same GET on the deliberately absent id that the browser case runs, exercises a production entry point headlessly and seeds the identical failure domain. No SQL, no fixture injection. The pair's target is scoped breakage retention across brief generation, and that target is unchanged.

3. **The browser evidence already proves the retention half.** Old Ack retained on the day-one brief, new scoped ids in the next-day brief, same two source refs. Both runs have producer clock reads at 20:27 and 20:28, inside the window, so the earlier clock condition is paid. The .op sibling reached the day-one brief with a correct clock too. The block is entirely the capture text.

4. **The capture text is consistent once the setup changes.** With the HTTP read in the .op setup, the lifecycle row exists on both transports and the existing capture_match on that text is correct. Keep it.

5. **The claim "this pair does not establish missing-decision refusal parity" is true and must be written.** On MCP a missing decision is one NotFound with one observer event; on HTTP it is NotFound plus a legacy read that fails again. That is transport drift in the compatibility layer. It belongs to PHILO-5-04 as inherited debt, not to this story.

**CONDITIONS**

1. Add the GET on the absent id to the .op setup with the same expect_status 404 and a "why" that names it as the legacy fallback seed, placed before the day-one brief.generate exactly as in the browser case. Do not remove the canonical decision.read op step. Keep both, in that order, so the record shows MCP was read and the HTTP fallback was exercised.
2. Comparator: add an explicit cross-transport breakage check that compares the ordered set of broke texts on the final brief across op and browser, and per run asserts each broke row's source ref maps to an old item and its id is new. Do not silently drop or de-duplicate the lifecycle row. Name the check so a future diff of the two sets reads as a product change.
3. Fence law: the new comparator check must read "fail" or "blocked" against the retained 22:28:57Z or 22:30:16Z observation paired with 22:26:49Z before it reads "pass" on the new run. Those two blocked runs stay in the tree, unselected, with a note.
4. Record in the evidence and in the atlas precondition for the .op sibling: setup uses HTTP to exercise the legacy missing-decision fallback; missing-decision refusal parity across transports is not established by this pair and differs today.
5. Record the fallback drift in the PHILO-5-04 intake as inherited Article XI compatibility debt with the route line cited. No product change under this story.

**MISSED**

1. The atlas precondition text for the .op sibling still says "the real DecisionLifecycleService observer records this failed read" on the MCP decision.read step. That "why" is false on MCP and must be corrected when the HTTP step is added.
2. The .op sibling has no browser, so the 393 viewport claim rests on the browser run alone. Fine for the pair, but the pair index must select 1440 browser against the .op run, not 393.

**TUESDAY:** No face or product change. The owner's brief still lists two broke rows for one missing decision read through the Room. That is the drift condition 5 records, not this story's fix.

**UNKNOWN**

1. Whether the hub, when the same absent id is read twice in a row by HTTP then MCP, emits a third primitive event that the comparator's source-ref mapping would then see as an unmatched pair. Astra's proposed order is HTTP only after the MCP op, so the run will show it. If a third row appears, condition 2's per-run mapping still holds because each row maps to an old item.
2. Whether the LAN engine is still up for the rerun. Not probed.

**Answer to the question:** the bounded setup normalization is the right move and inside the charter. The pair must not be reported unequal on the extra lifecycle row, because the row is a known compatibility fallback on one transport, but it must not be hidden either. Compare the sets explicitly, record the drift, and let 5-04 rule on the fallback.


---

# Check — Muad'Dib, 2026-09-24 (follow-up on the breakage-window amendment)

Read-only. No edits, no runs. Whoever acts files this under `checks/`.

**VERDICT: RATIFY-WITH-CONDITIONS** (the replacement is lawful; condition 1 of my earlier follow-up is corrected to REPLACE, not add)

**FINDINGS**

1. **Astra's cause diagnosis holds.** `holdspeak/web/routes/decisions.py:58-61` invokes contract `decision.read`, and on `NotFound` falls through to legacy `DecisionLifecycleService.get_decision`. The MCP canonical `decision.read` (`holdspeak/operations.py:222`) binds only to the PrimitiveService. So one HTTP read of a missing id lands two `pipeline_events` rows and one MCP read lands one. The brief collector keys on `(service, method)` (`monday_brief_service.py:577-593`), so it faithfully reports two broke rows from HTTP and one from MCP. This is a real compatibility fallback, not a duplicate decorator.
2. **The S5 pair's claim is scoped breakage retention across brief generation**, not transport parity on missing-decision refusal. A fair comparator needs equal failure-domain inputs. Today the inputs differ by construction (2 vs 1). Adding a third event fixes nothing and makes them unequal the other way (3 vs 2).
3. **An `api` step inside the `.op` sibling is already precedent-lawful.** Its setup opens with three `http-route` steps (discover-models, define-endpoint, summary-selection). `expect_status` is honored on `api` steps headlessly (`scripts/graph_walk.py:3336-3338`), so a 404 setup step blocks correctly if the route answers anything else.
4. **Requiring the browser case to add an MCP read purely for normalization is Tenet 1 waste.** One matching HTTP setup step on both sides is the smaller, honest fix.
5. **The `.op` `capture_match` on lifecycle text becomes truthful** once the lifecycle row actually exists on that side. Browser `broke.0` pinning stays deterministic: the lifecycle event is inserted after the primitive one, and the collector orders `timestamp DESC, id DESC`.

**CONDITIONS**

1. **Corrected condition 1:** in the `.op` sibling setup, REPLACE the `op decision.read philo402-deliberately-absent` step with the same step text the browser case uses: `{"kind":"api","method":"GET","path":"/api/decisions/philo402-deliberately-absent","expect_status":404,"adapter":"http-route","body":null}`. Its `why` must say: setup only; exercises the HTTP legacy fallback at `decisions.py:58-61` so both transports seed the identical two `pipeline_events`; not a missing-decision parity claim. Do not keep the MCP read alongside it.
2. **Every other `.op` step stays an op:** day-one `brief.generate`, `brief.latest` with `capture_match` text `DecisionLifecycleService.get_decision failed`, `brief.shelf.write` acknowledged, `decision.create`, `decision.update`, same-day `brief.generate`, the clock advance, the trigger `brief.generate`, and the durable reads. No SQL seeding anywhere.
3. **Comparator:** add one cross-transport check, `next_day.breakage_causes`, comparing the full set of `(text, detail)` of the final brief's broke items across op and browser by exact equality, plus the existing per-run `source_ref → new id` relationships. No dedupe, no dropping of lifecycle rows. Keep `breakage_scoped_ids` per label as it is.
4. **Fence law:** show `next_day.breakage_causes` FAILING on the retained pair (browser 222649Z or 222745Z against headless 222857Z or 223016Z, where the headless side lacks the lifecycle row) before it passes on new runs.
5. **Record in the case `why`, in `evidence-story-03.md`, and in the 5-04 handoff:** this pair does not establish missing-decision refusal parity; HTTP GET on a missing id falls through to the legacy lifecycle service, MCP `decision.read` does not; inherited compatibility projection drift, owed to PHILO-5-04; no product change in 5-03.
6. **The earlier six conditions stand unchanged** (wrapper, hour window, overlap check, unselected-run note, capture path, fence).

**Cross-set semantics, final:** both transports seed two failures from one HTTP read. Both final briefs must carry exactly the two causes `PrimitiveService.get_decision failed` and `DecisionLifecycleService.get_decision failed`, with brief-scoped ids that differ from the day-one ids and map back to the same two `source_ref`s. Any difference in the cause set is a FAIL, never tolerated.

**MISSED**

1. The owner's brief still says "2 things broke" for one missing read over HTTP. That is the 5-04 debt, and the wording of condition 5 should say it plainly.
2. The browser cases pin `sections/broke/0/text` by row order; the `.op` side selects by text. Harmless now, but a future third failure in the window would break the browser pin first. Note it, do not fix it here.

**TUESDAY:** No face or product change. The owner's real Tuesday brief is untouched.

**UNKNOWN**

1. I did not re-run anything. Whether the LAN engine is up for the three reruns is unprobed.
2. I read the `api` step handler, not a headless run with `expect_status: 404` on that path. The first rerun proves it.


## Astra response

Accepted the corrected replacement, not addition. The comparator compares every retained cause without dropping duplicates. Actual old blocked runs remain unselected; the new run must prove the two-source mapping and old shelf retention.
