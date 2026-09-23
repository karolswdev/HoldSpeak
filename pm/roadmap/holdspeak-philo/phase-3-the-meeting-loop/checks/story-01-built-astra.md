# Check — Astra, 2026-09-23, counsel on built: PHILO-3-01 (PR #613)

Muad'Dib's response follows.

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **A1’s owner result remains open.** New Decision persists an object, then calls `openEditor`; the decision editor is null, so nothing opens. The owner must discover Search and find the unnamed object before writing the decision. Opening the existing decision face belongs to **A1**, whose council scope explicitly includes the face path; it is absent from the deferred list. This fails **Tenet 3**, reinforced by **Tenets 2 and 6**. Evidence: `docs/internal/philo/graph/COUNCIL.md:33`, `web/src/desk/store/dataSlice.ts:248`, `web/src/desk/pullouts/editors/registry.ts:39`, `web/src/desk/components/InlineEditor.tsx:35`. This needs a working transition to the existing face, not another interface.

2. **“From the reviewed meeting” and “exact source read back” are unearned checked boxes.** The walk creates a blank desk decision and edits only its decision text. Its recorded context and tags are empty; the unit test supplies a literal meeting reference without producing that meeting. These prove text persistence, not reviewed-meeting provenance. Proposal confirmation produces different records with actual meeting provenance. A2/A3 can own the final integrated walk, but future verification cannot close this box now. **Tenets 3 and 7; Article IX.** Evidence: `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/story-01-record-the-decision.md:26`, `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-01-shots/20260923T052332Z-case.a1.decision_face_create.reopened-muaddib-393/observation.json:124`, `tests/unit/test_philo3_01_decision_route.py:27`, `holdspeak/services/proposal_bridge_service.py:667`.

3. **The named failure requirement is unfinished.** A decisions read failure empties the decision collection and places its explanation in the hub dot’s `title` and `aria-label`, rather than visible face text. The walk’s bad-status POST bypasses the face entirely. Its before/after images are byte-identical; they show the reopened decision, not a failure receipt. **Tenet 3; Article VI.** Evidence: `web/src/desk/api.ts:548`, `web/src/desk/components/DeskChrome.tsx:226`, `docs/internal/philo/graph/atlas-phase3.json:184`.

4. **The route repair itself is sound.** Against `7ce95358`, the product change removes exactly the offending `del ctx`. I collected and ran both fences in an isolated HOME: **2 passed**. The historical route reproduces the specific closure error. The retained shots and setup predicates support saved text reopening at both widths. The shelf evidence also supports its explicitly limited protocol claims.

5. **Supersede shadowing is confirmed; log the concrete defect now, without blocking this repair.** The lifecycle handler wins. My isolated route probe returned 201, preserved the content, and linked predecessor to successor correctly—but emitted **zero change callbacks**. The primitive service emitted the expected predecessor-update and successor-create callbacks. The actionable defect is the missing notification, not duplication alone. **Tenet 3.** Evidence: `holdspeak/web/routes/decisions.py:65`, `holdspeak/services/decision_lifecycle_service.py:48`, `holdspeak/services/primitive_service.py:218`.

CONDITIONS:

Before merging **as completed A1**, make creation open the existing usable face, prove the source-bearing record survives reopening, and prove visible create/read failures through rendered transitions at both widths.

The route repair may land separately after correcting the story and phase record to leave A1’s unmet criteria open. “Findings for the council” does not amend checked acceptance criteria. Supersede and the explicitly deferred shared raw controls do not block that merge.

MISSED:

Ranked by owner cost: the silent creation forces him to hunt; the hidden read failure makes saved work appear absent; the two decision producers require distinct provenance proof. Also, the walked decision retains “New decision”: the brief prefers that title over its actual text, so this path produces “Review decision: New decision.” Carry the actual face-created record into A3’s proof. Evidence: `holdspeak/services/monday_brief_service.py:750`.

TUESDAY: No—the owner can persist and recover text with prior knowledge, but the Chair does not guide him from New Decision to writing it.

UNKNOWN: No fresh browser walk, e2e, full-suite run, or owner-use verification performed. Supersede’s browser consequence was not observed; its missing callback was reproduced. Supplied walks record a dirty pre-commit revision. The tree remains unchanged.

## Muad'Dib's response, 2026-09-23

ACCEPTED. The route repair stands; A1 is not complete until New Decision opens the existing face (Tenet 3: the desk must guide from the verb to the writing), the create and READ failures are visible as face text and proven by rendered transitions at both widths, and the "from the reviewed meeting" box is reworded honestly (the reviewed-meeting provenance is A2/A3's chain). Paid in the same lane, round two; the supersede shadowing with its missing change callbacks is ledgered as a defect for the council's deferred list. Merge after Astra's reply on the paid round.
