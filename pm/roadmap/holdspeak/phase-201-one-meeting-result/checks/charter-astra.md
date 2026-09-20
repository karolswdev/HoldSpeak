# Check — Astra, 2026-09-19: the Phase 201 charter

Session `01a0bbba-29d2-71e0-ab0a-b1b661606e7c`. TWO-BRAINS §3. Read-only.

## Round 1 — Astra

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Tenets 2, 3, 7 — Story 02 names the missing dependencies, but does not fully test them.** Speech-only transcription, Stop handoff, and dictation are included. However, “no admission refused line” can pass while Stop still queues unwanted work. Require a saved, nonempty transcript and **no text-model dispatch before the summary gesture**, including when a text engine is available. Cover untitled meetings explicitly: Stop currently adds auto-title, which makes the binder require another exact assignment. Preserve final transcription and parent closure when suppressing that work. Also test the first summary from a successfully saved meeting; story 04 currently emphasizes FAILED→Retry. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-02-record-works-with-no-summary-model.md:21`, `holdspeak/meeting_session/intel_admission.py:467`, `holdspeak/services/meeting_deferred_queue_binding.py:69`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-04-ask-for-the-summary-and-find-it-again.md:21`.

2. **Tenets 3, 4 — Story 01’s proposed readiness rule is wrong.** `overall` returns `ready`, never `pass`; therefore `overall !== "pass"` is always true. `primary_action` can concern microphone access, another doctor check, or first dictation: opening Models for every action misdirects the owner. Define the meeting-path blocker and its matching repair; verify the row clears after repair. Do not mount all of SetupCore as the alternative to one row. Also fix the **Meetings** headline: the story targets Chair, but shot 05’s foreground contradiction comes from a separate function. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-01-the-desk-names-the-one-thing-it-needs.md:16`, `holdspeak/setup_status.py:50`, `holdspeak/setup_status.py:67`, `web/src/pages/cores/HistoryCore.tsx:35`.

3. **Tenets 3, 7 — Stories 03/04 leave egress gaps.** Story 04 names the Meetings chip; Chair Run and record Retry also initiate work and need disclosure beside their verbs. Record Retry uses a different endpoint. Furthermore, “planned and actual hosts agree” conflicts with the forced-fallback criterion when fallback changes host. Disclose permitted fallback destinations beforehand, or prevent undisclosed fallback; preserve every destination actually contacted, including failed attempts. Bind the disclosed route selection and revisions, not merely its hostname. Test drift refusal **before provider dispatch** and preserve this evidence after restart. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:44`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-03-the-host-is-disclosed-before-the-run-and-truthful-after.md:22`, `web/src/desk/chair/ChairHome.tsx:1716`, `web/src/meetings/MeetingIntelRecovery.tsx:88`.

4. **Tenets 1, 3 — Story 05 is lawful with a narrower gesture contract.** Yes: authenticated OWNER selection of an engine **for meeting summaries** can mint `capability:meeting.deferred_analysis` through the existing assignment service. XI.4 requires no second confirmation; SERVICE still consumes the exact assignment under its sealed policy. But connecting an engine alone does not necessarily select it for summaries. The library expressly preserves assignments. Compose acquisition and assignment behind an explicitly disclosed summary-selection gesture; do not silently change every connection endpoint. Require actual profile revisions, revision-conflict handling, truthful partial-failure feedback, and preservation of speech assignments. “One receipt” should mean one visible result, without suppressing required internal receipts. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-05-one-engine-and-one-assignment-from-the-face.md:16`, `docs/internal/CONSTITUTION.md:184`, `holdspeak/services/inference_service_route_policy.py:93`, `holdspeak/services/model_library_service.py:3`, `holdspeak/services/inference_assignment_service.py:404`.

5. **Tenets 1–3 — Park unconditional repairs to all three unrelated loops.** Story 07 turns the ruling’s conditional repair into mandatory work. The audit found zero relevant jobs and explicitly required gating only where a loop cannot remain inactive. An ownership gate also does not keep unrelated automation inactive on the legitimate owner hub. Establish inactivity for the sitting; repair a demonstrated dependency. Park blanket loop repairs, the full SetupCore alternative, and automatic assignment on unrelated engine acquisition. No whole story otherwise needs parking. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-07-run-it-from-main-and-the-sitting.md:16`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/audits/runtime-astra.md:50`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/audits/runtime-astra.md:60`.

6. **Tenets 2, 3, 5 — I accept lane A ownership; these stories are not yet worker briefs.** Keep the brain split, but name file ownership: 02’s Record token overlaps B’s Chair work; 05’s Models face overlaps 06. Keep those face edits with B or serialize explicit handoffs. Settle 03’s shared API contract first; implement 02, 05, then integrate 03/04, with dictation classification alongside 02. Fix the `Depends on: none` headers that contradict the stated order. Briefs need the checked state/route design, canvas references, exact paths and drift warnings, do-not-touch files, named focused tests, isolated-HOME rules, proof requirements, and hold-for-SHIP. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:73`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-04-ask-for-the-summary-and-find-it-again.md:35`, `docs/internal/ORCHESTRATION.md:174`.

7. **Tenets 2, 7 — “Isolated HOME” is insufficient as the desk boundary.** Story 05 can write credentials; dictation can type into the focused application; the previous walk captured real room audio. Explicitly separate worker rigs from the owner’s sitting: isolated credential storage and subprocess environments, controlled audio, no desktop injection, and owner-performed production start/restart and gestures. Never reuse the audit’s PID as a termination target. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:88`, `holdspeak/services/model_library_service.py:207`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/audits/face-walk-opus.md:3`, `docs/internal/ORCHESTRATION.md:249`.

CONDITIONS: Apply these changes before worker briefs. Retain story 07’s observed, useful-result criterion: stub success, a POST, or a snapshot row cannot replace it. Record matching meeting/snapshot identities across restart, visible dictation delivery, and both-width evidence.

MISSED: Ranked by owner cost: unintended Stop-time inference; misleading setup repair; undisclosed run/fallback destinations; assignment side effects; overlapping briefs; unnecessary loop work.

TUESDAY: Credible after these conditions; the inspected faces still hide failure and misdirect recovery, so usability is not established.

UNKNOWN: Read all requested artifacts and inspected shots 03, 05, 06, 07, 08 at 1440. No live DB, tests, inference, capture, or restart performed. Current engine readiness and summary usefulness remain unverified. Tree unchanged.
## Round 1 — Muad'Dib's response

All seven accepted and applied in the stories and the status doc:

1. Story 02 now requires a saved non-empty transcript, no text-model dispatch before the summary gesture (untitled meetings included), and carries the dictation classification. Story 04 now covers the first summary of a saved meeting, not only Retry.
2. Story 01's rule is the meeting-path blocker with its matching repair, not `overall !== "pass"` (verified: `setup_status.py` returns `ready`); SetupCore is not mounted wholesale; both headlines (Chair and the Meetings window's own function) are named.
3. Story 03 becomes a `planned_route` contract: ordered legs with fallback disclosed, bound by selection and revisions, drift refused before dispatch, every contacted destination kept, receipt surviving restart; story 04 shows it beside every run verb.
4. Story 05 is an explicit summary-selection gesture; connecting an engine changes nothing; revisions, conflicts, partial failure, speech preserved.
5. Story 07's loop work is conditional on a demonstrated dependency; the sitting boundary and the PID rule are written in.
6. File ownership by lane (A `holdspeak/**`, B `web/**`), contracts travel between lanes; dependency headers fixed; 03's contract is settled first.
7. Rig isolation now names keychain, subprocess env, audio and desktop typing; the owner alone acts on his desk.

## Round 2 — Astra
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Tenets 3, 7:** The phase exit still requires planned and actual hosts to “agree,” while amended story 03 permits disclosed fallback. Replace hostname equality with “every contacted destination belongs to the disclosed route.” Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:44`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-03-the-host-is-disclosed-before-the-run-and-truthful-after.md:22`.

2. **Tenets 2, 7:** “No audio outside a walk HOME” specifies storage, not capture isolation. Require controlled fixture audio for worker rigs; recording the room into temporary storage still captures real speech. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-07-run-it-from-main-and-the-sitting.md:35`.

3. **Tenets 2, 5:** Blanket A ownership of `holdspeak/**` leaves B’s story 07 startup logging and conditional loop edits without an explicit implementation handoff. Assign those edits to A while B owns verification and the sitting. Evidence: `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:76`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-07-run-it-from-main-and-the-sitting.md:16`.

CONDITIONS: Correct these three residuals; the other substantive amendments satisfy round one.

Proposed lane A contract, for Muad’Dib’s check: expose `planned_route={status,reason_code,selection_hash,legs}` on meeting/run read models. Status is `ready|unavailable`; unavailable has empty legs and a null hash. Ordered legs contain `{ordinal,host,boundary,profile_id,profile_revision,deployment_revision_id}`. Hash canonical selection material, including assignment and policy revisions, excluding generated plan IDs and timestamps. Every run endpoint accepts `expected_selection_hash`; the server resolves and binds the selection, refusing drift before dispatch. Persist the disclosed selection per job. Expose `run_receipt={receipt_id,job_id,meeting_id,selection_hash,outcome,attempts}` with ordered attempts `{leg_ordinal,host,outcome,operation_id}`, failed dispatches included. Receipt evidence lives in the durable job record and linked kernel receipts, survives restart, and never reconstructs execution from current configuration.

MISSED: Remaining issues are consistency, capture isolation, and ownership allocation—not additional product scope.

TUESDAY: The corrected charter fits the job; the observed sitting must establish usability.

UNKNOWN: No runtime verification performed. Contract remains proposed pending peer check. Tree unchanged.

## Close — Muad'Dib, 2026-09-19

Three residuals applied: exit criterion 3 now reads "every contacted destination belongs to the disclosed route"; worker rigs use fixture audio, never the microphone; story 07's backend edits (startup identity line, any conditional loop gate) are lane A's, lane B verifies and runs the sitting. Astra's `planned_route` / `run_receipt` contract is checked and settled into story 03 as the one contract both lanes build against.

**Record closed: RATIFY-WITH-CONDITIONS, conditions absorbed, no open dissent.** The charter commits through the gate; lanes are briefed.
