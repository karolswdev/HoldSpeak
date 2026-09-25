# Check — Astra, 2026-09-24 night, on the Phase 6 charter (PR #644 @ 88b58912)

VERDICT: RATIFY-WITH-CONDITIONS — present the charter for owner ratification after the corrections below.

FINDINGS:

1. **Story 01 faithfully carries my earlier ruling, but that ruling was wrong. I retract its adapter diagnosis.** `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-01-the-honest-import-badge.md:14` says the producer writes `transcription_status=import_failed`. At `cfa3b4fa`, `meeting_service.py:335` writes **`intel_status`**; `api.ts:498` already adapts both its string and nested `.state` forms; `ChairHome.tsx:266` passes it to `intelBadge`, whose fallback at `intelBadge.ts:26` returns SAVED. The `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-03-shots/none/browser/20260924T222258Z-case.j6.route_intelligence_run.refusal-astra-1440/observation.json:126` confirms `intel_status.state=import_failed` while `transcription_status=active`. Keep the producer → adapter → rendered-badge fence, but remove the mandated transcription-field repair. **Tenets 1/3:** the current diagnosis sends workers toward an unnecessary change that does not fix this failure.

2. **Story 02 leaves contradictory instructions about count meanings.** `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-02-the-briefs-truth.md:28` first preserves the generated snapshot and current Arrival count, then permits “Either the receipt counts what the Arrival shows.” Those quantities legitimately diverge after Ack/Defer and through THIS WEEK exclusion. Remove that alternative; retain distinct, accurately labelled counts and the conditional canvas amendment. The time-format ruling, both producer-wording seams (`monday_brief_service.py:500` and `:597`), request-versus-completion distinction, active-atlas requirement, and `2 more` walk are otherwise carried correctly. **Tenets 3/4.**

3. **The detailed estimates exceed the stated provisional total.** Story estimates are 0.5 + 1–1.5 + 1–1.5 + 0.5 + 0.5–1 = **3.5–5 engineering days**, with the optional count canvas additional. Evidence: story 01:36, 02:37, 03:35, 04:31, 05:30. Yet `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/current-phase-status.md:85` says 3–4 days including counsel and closing runs. “Provisional” is appropriate, but the arithmetic still needs reconciliation. **Tenets 1/3:** distinguish effort from elapsed time and name the closing allowance.

4. **The README’s Phase 5 row is stale, as disclosed.** `pm/roadmap/holdspeak-philo/README.md:29` says OWNER REVIEW PENDING; `pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/final-summary.md:3` records CLOSED and the owner-reviewed rehearsal. Update the row and link the close, preserving “rehearsed, owner-reviewed shots, not a sitting.” **Tenet 3 / Article VI.**

5. **The remaining repair rulings and code anchors check out against `cfa3b4fa`.**
   - **03:** render-only zero omission preserves the numeric facts; placement requires both-width ratification; `ChairHome.tsx:685` goes through Muad’Dib by patch. `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-03-the-toast-that-does-not-cover.md:26`.
   - **04:** legacy reads and observer failures remain protected; the exact parity pair is named. The previously unchecked `monday_brief_service.py:577–593` does deduplicate by **service/method**, so the retained PrimitiveService and DecisionLifecycleService failures survive as two entries. `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-04-one-cause-one-row.md:23`.
   - **05:** `DecisionPullout.tsx:66` is the save seam; `dataSlice.ts:297` begins the optimistic field mapping. Cause-first diagnosis, initial-transition proof, and failed-save behavior are correctly required. `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/story-05-the-decision-body-at-once.md:23`.

6. **The phase boundary and lane split are workable for me.** `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/current-phase-status.md:53` correctly requires the toast canvas, the conditional count canvas, the Phase 4 exit-1 case as written, and the Phase 5 rehearsal at both widths. Owner-reviewed rehearsal is not called a sitting. Exclusive `ChairHome.tsx` ownership and one shipping owner for shared generated files are sound (`pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/current-phase-status.md:77`). The Out list is appropriately bounded. `.githooks/dw check holdspeak-philo` returned **`dw check: ok`**, exit 0.

CONDITIONS:

- Correct story 01’s diagnosis and acceptance criteria; append a correction to my earlier finding and its active handover/ledger claims.
- Remove story 02’s count-conflation alternative.
- Reconcile the total estimate with story effort and closing work.
- Correct the README’s Phase 5 status.
- Make story 05’s proof plan explicitly require observation armed before Done; the existing delayed rig observation cannot certify the first frame.

MISSED:

1. **False first-frame proof:** `graph_walk.py:4393` waits 900 ms before its initial observation; the current S4 atlas case allows 60 seconds (`atlas-phase3.json:6449`). A passing rerun can still hide the defect. Preserve the actual-atlas run and add the transition probe.
2. **Clock agreement needs a timezone decision:** `monday_brief.py:52` formats the timestamp’s own offset, while `briefEgress.tsx:47` converts through browser-local time. Matching 12/24-hour formatting alone does not ensure matching times. Exercise different producer/browser offsets within story 02.
3. **“2 more” opens another face:** `ChairHome.tsx:2127` opens the Brief view. Its before/after walk must inspect that destination, not merely the Arrival overflow label.

TUESDAY: This is the right repair set for his morning; trustworthy failure badges, distinct counts, unobstructed text, and an immediate saved decision are still promises awaiting built proof.

UNKNOWN: S4’s runtime cause, final canvas choices, and delivery duration remain unverified. I inspected the pinned code, retained observations and failure-row extracts, and two retained shots; ran roadmap lint; ran no new hub, suites, atlas cases, or owner sitting. HEAD remained `88b58912`; the tree remained clean and unchanged.

Conditions and MISSED paid by Muad'Dib in this commit.
