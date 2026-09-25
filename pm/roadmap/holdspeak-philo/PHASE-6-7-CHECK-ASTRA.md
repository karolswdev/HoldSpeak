# Check — Astra, 2026-09-24 night, on the Phase 6/7 drafts (handover XXVIII @ 189a6b52)

VERDICT: RATIFY-WITH-CONDITIONS — present both directions after correcting the scope, counting, and completion claims below.

FINDINGS:

1. **The 320 baseline reproduces; the family summary and forecast need correction.** At main `189a6b52`, I ran the census under an isolated HOME: `RESIDUAL FENCE GREEN: 320 identities match`. The ledger is unchanged from the draft’s `06a5bf97`. Counting MCP by tool prefix and HTTP by route-module basename gives:

   | Transport | Reproduced families |
   |---|---|
   | MCP, 256 identities | desk 46; project 42; people 17; thought 16; provider 13; cadence 11; workbench 10; model_library 7 |
   | MCP, continued | concierge, decision_record, inference_assignment, meeting, reaction, scheduled_recording, watch: **5 each** |
   | MCP, continued | ask, heartbeat, interview, plugin_job, recipe: **4 each** |
   | MCP, continued | coder, follow_through, kb, practice_recipe, settings, zone: **3 each** |
   | MCP, remainder | seven families at 2; seven at 1 |
   | HTTP, 64 identities | settings 5; projects 4; automations and monday_brief 3 each; eight families at 2; 33 at 1 |

   Therefore the pointer’s “five families at 5” and “six at 3” should both be **eight**, counting both transports. The handover omits the two HTTP families at 3. Also, **320 − 46 − 42 = 232**, not below approximately 180; additional payments must be enumerated. **Tenet 3 / Article VI:** the owner needs a trustworthy scope. Evidence: `docs/internal/philo/phase-5/residual-set.json:125`, `pm/roadmap/holdspeak-philo/PHASE-6-7-CHARTER-DRAFTS.md:10`, `docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:37`.

2. **Road A identifies real defects, but “all canvas-free” and two diagnoses are too broad.**

   | Repair | Evidence and ruling |
   |---|---|
   | **1. Failed import → SAVED** | Anchors identify the wrong badge path: `web/src/desk/chair/intelBadge.ts:26`, `web/src/desk/chair/ChairHome.tsx:265`. **Canvas-free**, using FAILED. However, the real wire adapter also drops transcription status: `web/src/desk/api.ts:463`. Adding `import_failed` to the helper alone cannot repair the face. Fence producer → wire adaptation → rendered badge. **Tenets 3/4.** |
   | **2. Count/time conflict** | Both cited paths are right: `web/src/desk/chair/briefEgress.tsx:43`, `web/src/desk/chair/ChairHome.tsx:875`, `holdspeak/web/routes/monday_brief.py:47`. **“One count” is not a sufficient design.** Generated items and currently unhandled items legitimately differ after Ack/Defer; THIS WEEK is also excluded from Arrival. Preserve those meanings and the historical snapshot. Time-format alignment can reuse an existing idiom; changing the meaning or labels of the counts needs a small canvas amendment. **Tenet 3.** |
   | **3. Zero toast / overlap** | `web/src/components/AmbientLayer.tsx:175` renders the zero; `intelligenceAttention:95–96` correctly stores numeric facts. Omit zero tokens at rendering. **That part is canvas-free. Placement is not settled:** the toast is fixed, with a hard-coded bottom offset, and covers summary/capture content in the retained `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real/shots/summary/393-after.png`. Show the proposed unobstructed placement at both widths before building it. **Tenets 3/5/6.** |
   | **4. Raw pipeline wording** | `holdspeak/services/monday_brief_service.py:500` is correct. **Canvas-free** as a producer-wording repair within existing rows. Also cover the same defect in breakage titles at `holdspeak/services/monday_brief_service.py:597`; otherwise repair 5 leaves one failure that Arrival still hides. Name the recorded action accurately—requesting a summary does not itself prove completion. **Tenet 4.** |
   | **5. Two failures for one missing decision** | `holdspeak/web/routes/decisions.py:58` is correct. Retained evidence names HTTP observer rows **67 and 68**, versus op row **6**, for the same absent ID. **Canvas-free.** Preserve legacy decision reads; do not obtain parity by suppressing failures globally. `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/carried/verification/missing-browser-missing-id-rows.txt`. **Tenet 3.** |
   | **6. Empty decision after Done** | **Citation drift:** the save/exit seam is now `web/src/desk/pullouts/DecisionPullout.tsx:66`; lines 69–71 concern status cycling. **Canvas-free** if repairing the existing transition. Cause remains unconfirmed: `web/src/desk/store/dataSlice.ts:297` already patches decision text optimistically. “Await the refresh” is therefore not yet a diagnosis. The retained observation proves empty at 0.950 s, readable at 1.363 s. Fence the initial transition and failed-save behavior, not eventual text alone. **Tenet 3.** |

3. **Road A’s estimate is plausible only as provisional effort.** The proposed **3–4 engineering days** needs explicit allowance for the toast design, S4 diagnosis, counsel, and closing runs. Do not imply that two lanes automatically halve it. The split is workable if Muad’Dib exclusively owns `ChairHome.tsx`; Astra’s toast repair may need its capture-clearance seam at `web/src/desk/chair/ChairHome.tsx:685`. Allocate shared atlas/generated files to one shipping owner. **Tenets 1/3:** keep the work bounded without concealing integration cost. `docs/internal/TWO-BRAINS.md:106`.

4. **Desk first is defensible; “46 uniform primitive operations” is inaccurate.** The 46 comprise **42 primitive identities**, including compatibility aliases, plus `desk.snapshot`, `desk.needs_you`, and two workbench verbs. The actual kinds are notes, decisions, kbs, directories, workflows, chains—**not artifacts**. Zone membership is another three identities; knowledge membership another three; `decision.supersede` another one. Decision status has an HTTP path but no separately named MCP tool. Evidence: `holdspeak/mcp/tools.py:33`, `holdspeak/mcp/tools.py:912`, `holdspeak/mcp/tools.py:1139`, `holdspeak/web/routes/primitives/decisions.py:108`.

   Prefer desk work because it completes a concrete filing/retrieval job, then projects for Room work. “90%” describes the Desk’s intended role, not measured usage of this MCP prefix. People is a credible alternative for report preparation, but its custody boundary warrants separate scope. Provider/settings should move first only if setup blocks the chosen job. The **HTTP settings 5** mostly count heartbeat constructions; they are not five unmigrated settings capabilities. `holdspeak/web/routes/system/settings.py:24`, `holdspeak/web/routes/system/settings.py:294`. **Tenets 2/3/7:** order by useful jobs, not family size.

5. **A finite descriptor table is lawful; automatic uniform policy is not settled.** Expanding explicit rows into `OperationDescriptor` objects remains a module, provided each row names its real callable, schema, result, refusals, exposure, and completion. No discovery framework or universal CRUD semantics is needed. Notes already have Thought-owned revision behavior that differs from other primitives: `holdspeak/services/primitive_service.py:91`. This fits the `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:133`.

   **“Owner-only where a verb writes” is a policy change**, not a consequence of that settlement. Current primitive writes do not universally impose it. Preserve existing authority behavior or name and ratify the compatibility change. Owner-only authorization also does not provide kernel admission or receipts. **Tenets 1/3; Article XI.**

6. **The Article XI decision need not block a migration-only story 01.** Phase 5 explicitly permitted migration while naming inherited admission debt; it did not establish an exemption. Story 01 may follow that boundary if it preserves behavior and carries the debt honestly. It cannot change write authority or certify lawful admission while postponing the relevant ruling to 02. Filing into zones makes Article V’s “files” trigger particularly relevant. Reads and composition work can proceed independently. Evidence: `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/checks/story-02-built-astra.md:13`, `docs/internal/CONSTITUTION.md:169`. **Tenet 1 supports bounded deferral, not an invented exemption.**

7. **The four-stage shape is sound; its proof scope and 10–13 days are not yet grounded.** The current `atlas.json` has **81 cases**; it has note cases but no directory, KB, workflow, chain, supersede, or zone-membership cases. Story 03 therefore needs new browser cases as well as `.op` siblings. `docs/internal/philo/graph/atlas.json:6031`.

   “Attach it to a meeting” also lacks a named operation in the proposed inventory. Define a durable relationship and its readback, or change the closing job. A Markdown link must not silently satisfy “attachment.” Finally, make discovery without repository access an acceptance criterion: the previous rehearsal explicitly did **not** prove it. `docs/internal/philo/phase-5/his-words/rehearsal.md:49`. Re-estimate before build authorization, once these obligations and the admission scope are known. **Tenets 2/3/7.**

8. **The method mostly carries the right lessons, with omissions and one authority error.** Calling Astra→Muad’Dib counsel a “self-check,” then saying only the orchestrating session’s counsel counts, misstates the equal-brain protocol. The other brain checks; the lane owner merges after counsel on built. `docs/internal/project-rooms/HANDOVER-MUADDIB-XXVIII.md:12`, `docs/internal/TWO-BRAINS.md:114`.

   Carry explicitly: words **and active atlas fences** change together; receipts survive every rendered branch; same-hub object identity differs from restart durability; palette refusals are exercised through dispatch; generated references stay current; real/replayed provenance stays separate. The fast-CI merge exception is recorded in `pm/roadmap/holdspeak-philo/phase-4-the-morning/final-summary.md:58`. Keep it, but assign later heavy-job triage and compare failure names against the relevant base—**44 is historical evidence, not a permanent allowance**. **Tenets 1/3.**

9. **An empty residual set is neither necessary nor sufficient for “fully via MCP.”** HTTP census counts constructors, not all operation bypasses. For example, decision delete/status/supersede call the composed service directly although that route’s constructor identity was already paid. MCP census trusts declared exposure; it does not itself prove traversal. Resources and unexposed capabilities are not comprehensively counted. Conversely, the brief’s partial-context fallback remains counted despite correct production composition. `scripts/residual_census.py:61`, `scripts/residual_census.py:110`, `docs/internal/philo/phase-5/residual-set.json:115`.

   Define done as **every in-scope server capability discoverable and executable through MCP, reaching the declared operation and bound service, with demonstrated authority, outcomes, refusals, and readback**. Retain a reasoned exceptions inventory. Hand-written transport work remains: multipart parsing, file custody and cleanup, response/envelope mapping, authentication, and URI handling. Rig setup, restart, clock advancement, and observation remain rig actions. Window/layout verbs currently remain UI-only. `holdspeak/web/routes/meeting_import.py:97`, `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/current-phase-status.md:63`, `holdspeak/mcp/tools.py:519`. **Tenets 1/3.**

CONDITIONS:

- Correct the census summary, forecast, S4 anchor, method wording, and definition of done before presenting the drafts.
- Settle Road A’s count meanings and toast placement; explicitly cover raw breakage wording. Keep the red-before-fix and actual-atlas proof requirements.
- **Counter-proposal:** Road A first. Then a bounded desk slice: notes, zones/directories, knowledge membership, and remaining decision operations. This selects **33 existing MCP residual identities**, plus three relevant HTTP constructor identities—not a guaranteed 36-entry reduction if fallbacks remain. Park workflows/chains, workbench aliases, and aggregate reads with their owning slices. Projects follows.
- Keep four stories: **01** explicit primitive contracts and discovery; **02** memberships and decision completion under the named authority settlement; **03** new actual-atlas cases plus operation equivalence; **04** ordinary-word filing/retrieval from a client without repository access, with durable readback and both-width shots. Assign the shelf-enum repair explicitly; “Road B” currently gives it no story.
- Retain four owner decisions, expressed as jobs and consequences:
  - **D1:** “Which job next: file and find desk notes, work in a project room, or prepare work for your reports?”
  - **D2:** “Complete the morning repairs first, or run the MCP work alongside them?” Recommend repairs first.
  - **D3:** “Which named local edits require kernel admission and receipts?” State that the owner’s gesture already approves the act; any exemption needs an explicit constitutional basis or amendment.
  - **D4:** Keep Codex as the default rehearsal client; ask about another client only if desired. State the discovery and already-open Desk freshness promise explicitly, because those affect scope.

MISSED:

1. **First-use cost:** another successful rehearsal with repository-assisted discovery would repeat the prior 201-second decision search.
2. **Hidden failures:** repairing duplicate observer rows without repairing raw breakage wording still leaves failures invisible and difficult to handle.
3. **False uniformity:** Thought-owned notes, workbench execution, aggregate reads, and simple primitive edits have different contracts and effects.
4. **Unassigned debt:** shelf-enum alignment is promised to Road B without ownership; “attach to meeting” promises a relationship without an identified implementation.

TUESDAY: Road A addresses obstacles visible in the retained morning shots; Road B becomes credible when the owner can file and find the result from an ordinary request without source-code research.

UNKNOWN: No new hub, atlas walk, suites, or owner sitting was run. I reproduced the census, inspected code, retained observations, two shots, and the retained brief DB. S4’s runtime cause, a supported note-to-meeting attachment, current heavy-CI failures, and delivery estimates remain unverified. The tree is unchanged, including its three pre-existing untracked files.

Conditions paid by Muad'Dib in this commit (handover XXVIII r2); the counter-proposal ADOPTED.
