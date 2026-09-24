# Check — Astra, 2026-09-23, on the Phase 4 charter (PR #620 @ e36bc386)

VERDICT: **RATIFY-WITH-CONDITIONS** on presenting the charter to the owner. The three repairs address the right morning job. Correct the scope, repair choices and proof criteria below first.

FINDINGS:

1. **The claimed Phase 175/200 ratification of the three-row Arrival cap is not established.** Phase 175’s `pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/mockups/BriefWeek.dc.html:65` draws three example rows in the detail view; it does not specify an Arrival cap. Phase 200’s `pm/roadmap/holdspeak/phase-200-the-working-practice/assets/settled-design-daily-workflow.md:204` cites `BRIEF_CAP = 3` as existing code. History traces its introduction to Phase 170, commit `328d06fd`.

   Keeping the cap and repairing selection/order is still the smaller change. But remove the unsupported ratification claim and the blanket exemption that changing order needs no design review. Show the resulting order on the already-required canvas. **Tenets 3 and 6; UX-CANON A.2.**

2. **“Newest decision first” needs a real ordering source.** Arrival currently concatenates sections with decisions last (`web/src/desk/chair/ChairHome.tsx:801`). Moving that section first can expose *a* decision, but does not establish newest-first: decision items receive random IDs and equal priority, then reload by priority and ID (`holdspeak/services/monday_brief_service.py:761`, `holdspeak/services/monday_brief_service.py:1168`).

   Settle the ordering rule before briefing a worker. The fence must include several older decisions, not only four older non-decision rows. **Tenets 3 and 7.**

3. **Story 03 should choose brief-scoped IDs; generic “idempotent insert” is not an equivalent repair.** Each item belongs to one brief, and triage references that item (`holdspeak/db/schema.py:2440`). An in-memory probe using those exact table declarations showed:
   
   - Plain INSERT: the reported uniqueness failure.
   - `INSERT OR IGNORE`: no failure row in the new brief.
   - `INSERT OR REPLACE`: the old brief loses its row; with foreign keys enabled, its triage disappears.
   - Separate IDs: both briefs and the old triage survive.

   Scope **both pipeline and connector** item IDs to their brief; retain `source_ref` and cause; no migration. Require read-back of both briefs, preserved old triage, and same-day idempotence. Mint the overlapping failure through its real producer.

   Also reconcile “still names the cause in plain words” with current behavior: breakage titles contain service/method or connector IDs (`holdspeak/services/monday_brief_service.py:546`), while Arrival renders only `item.text` (`web/src/desk/chair/ChairHome.tsx:2000`). An ID fix alone cannot establish that face claim. **Tenets 3, 4 and 7.**

4. **Story 01 has the right minimal action, but its scope and fence are ambiguous.** One existing Generate action on a populated Arrival, without forced triage, is the smallest repair. Its `pm/roadmap/holdspeak-philo/phase-4-the-morning/story-01-generate-always-reachable.md:22` covers only the BRIEF section; it does **not** cover the cited `web/src/desk/pullouts/views/BriefView.tsx:297`.

   Explicitly retain BriefView’s limitation if this is Arrival-only. If both faces are repaired, both need canvas ratification and rendered tests. Define loading, failed-read and generating states without making “always reachable” mean concurrently enabled. Preserve the existing egress, date and receipt through the rendered transition, and define triage preservation against the old brief’s durable shelf.

   Line 24 also reverses the fence: asserting “has no Generate” passes today. Assert the desired presence; record its pre-fix absence as the failure. **Tenets 3 and 5; UX-CANON A.2.**

5. **Step 5 is the right job, but its current PASS is insufficient to close exit 1.** The `docs/internal/philo/graph/atlas-phase3.json:2124` checks text containment. Its `scripts/graph_walk.py:832` accepts the expected text even when the observation marks it invisible and outside the viewport; I confirmed that with the extracted pure function. The retained `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/closure/20260924T014339Z-case.closure.chain.s5_next_day_brief_more_opened-muaddib-393/after.png` demonstrates why containment is inadequate.

   Keep the **interaction** as written: populated untriaged day one → producer-day advance → one Generate → readable decision, without Ack/Defer or expansion. Strengthen proof with the new brief identity/date, unchanged old triage, readable row geometry and inspected shots at both widths. Retain cumulative restart evidence.

   Add the Phase 4 forward link to `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/current-phase-status.md:28` **now**, leaving it unchecked. Close it only against the integrated evidence. Exit 3 remains the owner’s sitting on the full chain. **Tenets 3 and 7; Article IX.**

6. **The estimate and README need one consistent account.** Story estimates total **2.5–4 engineering days**. With 01 → 02 and 03 parallel, the stated critical path is **2–3 working days**, excluding owner availability. That supersedes my earlier 1–2-day A5 estimate; say so explicitly.

   The `pm/roadmap/holdspeak-philo/README.md:27` calls Phase 3 done with open exits, while its second index calls it `pm/roadmap/holdspeak-philo/README.md:41`. Use one index: Phase 3 closed by ruling with exits 1/3 open; Phase 4 unratified; Phase 5 parked, unratified, linked. Update the top status accordingly. **Tenets 2 and 3.**

7. **Phase 5 r2 pays much of r1, but “pays that check” overstates completion.** Attribution, descriptor limits, clock/callback gaps, per-hub identity, residual identities, complete-roster documentation and the owner’s normal job request are addressed.

   Remaining r1 conditions include the revision/counting basis, exact transport mappings—the `pm/roadmap/holdspeak-philo/PHASE-5-CHARTER-DRAFT.md:52`—named atlas pairs, explicit compatibility/palette preservation, and separate real-engine/replayed evidence. Some are expressly deferred to future stories. Record them as carried conditions and retain the draft as parked. This is **not** a new review or ratification of Phase 5’s substance. **Tenets 1 and 3.**

CONDITIONS:

- Settle story 02’s ordering rule and correct its canvas provenance.
- Choose brief-scoped failure IDs and require preservation of both briefs, triage and causes.
- Resolve story 01’s face scope, state behavior and incorrectly worded pre-fix fence.
- Strengthen the actual closure case’s evidence; link Phase 3’s open exit now.
- Reconcile estimates, README rows and Phase 5’s condition-payment claim.

MISSED:

1. **Highest owner cost:** “newest first” can still display old decisions if recency is inferred from random item IDs.
2. **Data cost:** suppressing the collision can silently omit or move the failure and destroy its triage.
3. **Verification cost:** another green containment check can leave the phone decision unreadable.

TUESDAY: **Not yet.** With these conditions, the charter targets the right result: leave yesterday’s work untouched, press Generate once, and read the new decision.

UNKNOWN:

Reviewed clean HEAD `e36bc386`. I changed nothing. I read the artifacts, code, prior r1 report and retained phone shot; ran only in-memory schema/predicate probes. No product suite, hub, new atlas walk or real-producer failure reproduction ran. The claimed cap-ratifying canvas and the owner’s sitting remain unverified.