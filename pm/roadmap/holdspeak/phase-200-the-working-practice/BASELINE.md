# Phase 200 baseline and earlier work

**Observed:** 2026-09-05, America/Denver.
**Repository baseline:** `519afd4f82d24ad5bd8c5f17df59b6a4fbeed19d`.
**Method:** source and documentation inspection, Git history, and read-only GitHub status queries.
No owner database census, live microphone test, or new full product test run was performed while authoring this roadmap.

## Observed signals

| Signal | Evidence | Consequence |
|---|---|---|
| Interview is merged, with manual drafting and supported Project setup. | [PR 561](https://github.com/karolswdev/HoldSpeak/pull/561), [delivery status](../../../../docs/internal/architect-assistant/DELIVERY_STATUS.md). | Extend its composition and quality. Preserve its existing durable state and tool boundaries. |
| Recommendation quality remains unproved after prompt changes. | [Interview limits](../../../../docs/INTERVIEW.md#project-setup-and-automation-limits). | Evaluate real model behavior separately from fixture mechanics. |
| Concierge, Heartbeat, meeting proposals, Steward drafting, and Reach exist on the selected baseline. | [User guide](../../../../docs/USER_GUIDE.md), [Project Rooms](../../../../docs/PROJECT_ROOMS.md). | Reuse and prove their production paths before adding replacements. |
| Current main CI completed with failed unit and E2E jobs. Web quality, integration, Linux smoke, and documentation jobs passed. | [Run 34002938227](https://github.com/karolswdev/HoldSpeak/actions/runs/34002938227). | Establish a current failure ledger. The result does not classify all failures as product defects or inherited failures. |
| The update parser can set `verified=True` when it finds a valid inventory reference. | [`_parse_model_output`](../../../../holdspeak/services/project_update_service.py). | Valid references need a separate factual-support state. Preserve old provenance without upgrading its meaning. |
| The needs-you builder skips failed Room reads and returns `stale: False`. | [`build_aggregate`](../../../../holdspeak/services/needs_you_aggregate.py). | Add explicit source coverage and partial-result semantics. Verify the complete rendered path. |
| Reach Runner requires a reachable hub and an external scheduler. Credentials are lost when the hub restarts. | [Runner guide](../../../../docs/REACH_RUNNER.md), [credential store](../../../../holdspeak/principals.py). | Design availability, credential lifetime, and restart recovery before relying on unattended work. |
| Calendar work exists in an open PR. | [PR 558](https://github.com/karolswdev/HoldSpeak/pull/558), observed head `2cde6e62d58571da0c76409fff4ead35644b4752`. | Inspect its current diff and proofs before integration. Its title and phase rows are not runtime attestation. |

These are dated observations.
HS-200-01 refreshes the selected integration revision and actual deployment before dependent implementation.
A read of local working files does not establish which revision a running process loaded.

## Capability disposition

| Capability | Existing owner or seam | Phase 200 disposition |
|---|---|---|
| Capture and corrections | Dictation runtime, speech sessions, correction memory | Reuse; prove physical capture, permissions, retry, delivery, and restart in 04–05. |
| Models | Concierge, Model Library, inference assignments, Intelligence Router | Reuse; repair demonstrated readiness and route adoption gaps in 04. |
| Evidence and generated updates | `project_update_service.py`, existing reference resolvers | Correct support semantics in 06; reuse through 10–13, 17, and 27. |
| Project attention | `needs_you_aggregate.py`, Heartbeat, Door, shade | Correct coverage in 07; compose relevance and actions in 15. |
| Project preparation | Project, Memory, Monday brief, updates | Compose three complete recipes in 11, 17, and 21. |
| Meeting outcomes | Meeting completion, proposal bridge, decisions, follow-through | Prove one production chain in 12–14 and 16. |
| Working context | Interview state, Notes, Thoughts, Projects, qualified refs | Add explicit promotion and reference reuse in 10. Avoid a second personal database. |
| Interview setup | InterviewService, Thread tools, ProjectSetupService | Add prepared plans, reconciliation, and supported recipe adapters in 18–20. |
| Scheduling | Heartbeat, Cadence, scheduled recordings, Steward | Keep their owners; expose exact bindings in 21 and 33–35. |
| Workers | Delivery factory, steering, adapter capability ledger | Reuse one supported adapter through 24–30. |
| Assignment outcome and acceptance | Proposed architect-assistant contracts | Implement only the missing domain boundary in 24–29. |
| Remote execution | Reach transport, principals, runner | Prove deployment and credential recovery in 31–36. |
| Native devices and portfolio | Existing and planned separate tracks | Retain supported behavior; expand when pilot evidence demonstrates a requirement. |

## Earlier roadmap accounting

| Earlier work | Treatment | Destination |
|---|---|---|
| 170: Great Pass and Concierge | Adopt integrated implementation and retain outstanding live-proof obligations. | 01, 04, 09, 39 |
| 171: Heartbeat | Adopt scheduler, aggregate, and notification work. Prove quiet hours, coverage, and restart. | 07, 15, 21, 33–36 |
| 172: Loop Closes | Adopt production bridge and People joins. Prove source-supported outcomes across days. | 12–14, 16 |
| 173: Steward | Adopt drafter and observations. Correct claim semantics; retain existing effect policies. | 06, 11, 17, 21 |
| 174: Reach | Adopt transport. Complete operational durability for the selected deployment. | 31–36 |
| 175: Calendar and the Clock | Inspect open PR and integrate only justified calendar dependencies first. Preserve remaining authored work. | 22 |
| 176: Speak Loop | Carry real dictation and correction proof into the core release. | 05 |
| 177: Thread at Work | Carry grounded Project conversations and measured usefulness into the daily loop. | 10–11, 18–20, 23 |
| 178: Portfolio | Defer new portfolio surfaces until cross-Project pain is measured. | Expansion decision in 37 |
| 179: Companion | Preserve supported behavior. Defer new native parity commitments. | Expansion decision in 37 |
| 180: Proof | Move real-use, release, and performance proof into this phase's gates. | 08, 16, 23, 30, 36–40 |
| 155: Crew | Reconcile its child-work design before the Assignment implementation. No second crew runtime. | 24, 26 |
| Architect-assistant DP-00/00A | Runtime and Interview foundation. | 01–08, 10, 17–20 |
| DP-01/02 | Daily preparation, decisions, and follow-through. | 09–16, 21–23 |
| DP-03/04 | Assignment and supervised delivery. | 24–30 |
| DP-05 | Owner pilot. Begin R1 observation when G1 passes. | 16, 23, 30, 37 |
| DP-06 | Bounded automation. | 31–36 |
| DP-07/08 | Portfolio and further reach. | Evidence-based follow-on decision in 37 |

This mapping changes the default sequence for new work.
It does not rewrite old evidence or declare old unfinished stories complete.
HS-200-01 assigns each surviving obligation one active owner and destination.
Correct functionality can satisfy a new story through fresh integrated proof.
It does not require a duplicate implementation.

## Repository debt at planning

Delivery Workbench reports five existing structural issues on the baseline.
They concern orphan evidence in Phase 101 and missing final summaries in Phases 152, 153, 154, and 156.
Historical warnings also identify multiple open phases and older evidence conventions.
The planning change must add zero new structural issues.

Historical reconciliation belongs to HS-200-01 where it affects execution ownership.
No evidence file or old final summary is fabricated to make a checker green.
The selected release's functional checks remain a separate obligation.

## Assumptions

| Assumption | Working default | Resolution point |
|---|---|---|
| Initial operator | Karol, using one real transformation stream | 01 and pilot entry |
| Sources | Existing connected repository and available Project records | 01 and 11 |
| Model | A currently configured, compatible, explicitly selected route | 04 and 08 |
| Calendar | Optional for the first manual preparation result | 22 |
| Worker | One existing adapter with enforceable declared limits | 24 and 26 |
| Availability | One owner-controlled hub; no active-active database | 31 |
| Capacity | One primary delivery lane; no calendar deadline is promised | Re-estimate after G0 |
| Pilot opportunities | Real tasks may require more than ten elapsed workdays | 23 and 37 |

Employer sources, organizational decision rights, and financial savings are not inferred from personal fixtures.
