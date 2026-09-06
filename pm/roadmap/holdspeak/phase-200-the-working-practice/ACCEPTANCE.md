# Phase 200 acceptance and owner pilot

**Status:** required future evidence. No result below is an achieved result.
**Protocol version:** 1.
The [story files](current-phase-status.md#story-status) own implementation acceptance.
This document defines the integrated product and release evidence.

## Evidence levels

| Level | Establishes | Cannot establish alone |
|---|---|---|
| Source inspection | A contract and its apparent implementation | The running path, model quality, or user value |
| Deterministic tests | State, command, failure, and interface behavior | Physical capture or useful generated content |
| Real model trials | Measured content and tool behavior for one route | Unobserved models or daily adoption |
| Physical/runtime proof | Actual device, deployment, and restart behavior | General platform parity |
| Owner work | Useful results, correction effort, and continuity | Market-wide adoption or organizational authority |

Keep the levels separate in each gate report.
A scripted model is appropriate for failure injection.
It is insufficient evidence for recommendation usefulness.

## Required behavioral scenarios

| ID | Scenario and passing condition | Owning stories | Level |
|---|---|---|---|
| P200-A01 | Identify the loaded backend, bundle, and database. Detect a stale bundle and a second runtime. | 01–02 | Tests, actual runtime |
| P200-A02 | Back up, upgrade, restore a copy, and reopen the same permitted records and attachments. | 02, 38 | Tests, actual runtime |
| P200-A03 | Cold install reaches an edited, copied or kept sentence without an LLM. | 03–05, 39 | Browser, physical |
| P200-A04 | Select a compatible model, execute a real probe, fail one prerequisite, repair it, and return to the unfinished task. | 04 | Tests, model, browser |
| P200-A05 | Capture, correct, replay, and reopen physical dictation. Permission failure and uncertain delivery do not silently lose or duplicate the work. | 05 | Tests, physical |
| P200-A06 | Attach a valid irrelevant citation to invented prose. The claim stays unsupported. Edits invalidate prior support. | 06, 08 | Tests, model |
| P200-A07 | Fail one or every Room read. Arrival and brief show incomplete coverage rather than an all-clear. | 07, 15 | Tests, browser |
| P200-A08 | Promote a stated constraint, reuse it in another Thread, correct it, and revoke a source. Derived plans and disclosure respond correctly. | 10, 20 | Tests, browser |
| P200-A09 | Prepare a brief from a Project and manual purpose, open its sources, keep it, and resume after restart. | 11, 16 | Model, owner |
| P200-A10 | Complete a linked meeting through the actual trigger. Review source-backed proposals and retry completion without duplicates. | 12, 16 | Tests, model, physical |
| P200-A11 | Accept then supersede a decision. Next-day recall identifies the current decision and its rationale. | 13, 16 | Tests, owner |
| P200-A12 | Prepare permitted People context with an ambiguous identity, locked store, and missing source. No protected material leaks into ordinary context. | 14 | Tests, owner |
| P200-A13 | Act on a priority through its domain verb. Test a changed item set with unchanged total, quiet hours, and restart. | 15 | Tests, browser, device |
| P200-A14 | Run each of the three recipes manually with a useful kept result and declared coverage. | 11, 17, 23 | Model, owner |
| P200-A15 | Express exploratory interest and then an exact setup request. Only the supported, authorized setup becomes actual configuration. | 18–19 | Tests, model, owner |
| P200-A16 | Interrupt before and after each setup effect. Reopen, reconcile partial work, and avoid duplicate configuration. | 19–20 | Failure injection |
| P200-A17 | Revisit an existing recipe, change a material field, pause it, and inspect the actual next trigger. | 20–21 | Tests, owner |
| P200-A18 | Run one actual scheduled brief. Its result, scheduler identity, route, and receipt appear in the Project. | 21 | Actual runtime |
| P200-A19 | Use an associated calendar event and a manual purpose. Ambiguous matching cannot create new recording authority. | 22 | Tests, browser |
| P200-A20 | Start an immutable assignment through Web and supported tools. Unsupported adapter capabilities refuse before dispatch. | 24–26 | Tests, real worker |
| P200-A21 | Return a result against the wrong revision or with a fabricated test claim. Mandatory verification prevents passing acceptance. | 27 | Tests, real worker |
| P200-A22 | Answer a blocker, reconnect, request changes, and inspect result evidence through existing Desk surfaces. | 28, 30 | Browser, real worker, owner |
| P200-A23 | Crash after claim, change scope, cancel during completion, revoke a source, and deliver a duplicate callback. One lawful result wins. | 29 | Failure injection |
| P200-A24 | Reboot the selected hub and recover scoped machine access. Rotate and revoke credentials without exposing token material. | 31–32 | Tests, actual deployment |
| P200-A25 | Fire duplicate occurrences, expire leases, cross DST, and miss a schedule. Apply the declared overlap and catch-up policy. | 33–34 | Failure injection |
| P200-A26 | Execute both unattended recipes through three actual scheduled occurrences each, including a controlled outage or restart. | 35–36 | Actual deployment |
| P200-A27 | Install the packaged candidate cold and complete the daily path using normal controls and public instructions. | 38–39 | Cold rehearsal |
| P200-A28 | Calculate net effort from all attempts and record the owner's keep/repair/stop judgment for each recipe. | 23, 30, 37 | Owner work |

Every implementation story also runs the tests appropriate to its changed seam.
The scenario matrix supplements those tests.

## Critical defects

Any unresolved critical defect blocks its gate regardless of averages:

- Silent loss of accepted input or kept work.
- Unexplained duplicate consequential effects.
- Invented decision acceptance, source-backed owner, deadline, or verification result.
- Unsupported prose presented as checked fact.
- Unauthorized disclosure or execution outside the applicable scope.
- Incomplete observation presented as an all-clear.
- A worker or scheduler represented as stopped or completed without supporting evidence.
- Acceptance despite a failed mandatory check.
- Restore that loses required records without an explicit supported recovery outcome.

Use severity based on consequence and the actual path.
Do not classify every minor wording issue as critical.
An unresolved critical factual defect in the selected workflow blocks unattended enablement.

## Quality corpus

HS-200-08 creates at least thirty versioned episodes.
Use ten Interview episodes, ten meeting episodes, and ten grounded brief/update episodes.
Keep at least one-third as held-out acceptance cases before tuning prompts.
Add real failures as regression cases while preserving an independent held-out set.

Include these variations:

- No source, partial source, stale source, revoked source, and contradictory source.
- A relevant document containing no support for the proposed sentence.
- Stated facts, model inferences, and explicit user corrections.
- Missing or ambiguous owner, date, identity, and acceptance.
- Long context, omitted evidence, unavailable tools, and model failure.
- Repeated suggestions under changed wording and dismissed suggestions.
- Successful tools followed by a misleading narrative.

Record prompt and recipe versions, model identity, route, sampling settings, and context coverage.
Score factual support against source material.
Score suggestion relevance with the owner or a designated reviewer.
A model judge may assist triage but cannot supply the only acceptance evidence.

## Performance targets

These targets apply to the attested pilot hardware and supported model.
Record cold and warm results separately.

| Measure | Initial target | Method |
|---|---|---|
| Local action acknowledgement | At most 500 ms p95 | Twenty representative interactions, including a running or failed request |
| Useful cached Project content | At most 2 seconds p95 | Twenty visits to a Project fixture with 500 linked records |
| First capture to visible text | At most 3 active minutes with capture prerequisites available | Cold product task; report permission and download waits separately and in total elapsed time |
| Thirty-minute meeting processing | Terminal result or truthful continuing progress within 60 seconds of dispatch | Identify the actual admitted job and stage; record total completion latency |
| Reopened accepted work | Same authoritative record after restart | Compare IDs, revisions, content, and applicable source availability |

The progress requirement cannot pass with a decorative spinner.
Model completion time and active human effort are separate measurements.
Record the time spent fixing failures.

## Owner pilot entry

Start R1 observation after HS-200-16 passes.
Use one real transformation stream and existing permitted sources.
Select useful tasks before the assistant produces their results.
Record the actual operator, model destinations, baseline effort, and decision authority where relevant.

Keep observations locally unless the owner selects another destination.
Publish only synthetic or redacted evidence.
Do not introduce passive telemetry.

The pilot can continue while recipe setup and supervised delivery improve.
Record every build and configuration change.
Separate comparisons where a change materially affects behavior.

## Daily-practice sample

Observe at least ten workdays with:

- Five relevant meetings with independently reviewed decision/action ground truth.
- Ten decision-recall tasks.
- Two weekly Project updates.
- Five useful Interview sessions, including three revisits.
- Actual use of all three starter recipes.

Ground truth identifies decisions and actions before scoring the generated extraction.
It records ambiguous or absent fields explicitly.
Do not select only the easiest or most successful tasks.
Record aborts and failures in the denominator.

If the work does not provide enough opportunities, extend the sample period.
The result remains inconclusive until sufficient relevant observations exist.
Do not manufacture meetings or assignments to fill the quota.

## Usefulness targets

| Measure | Definition | Initial target |
|---|---|---|
| Preparation effort | Active time through an owner-usable reviewed brief, including correction and task-specific setup | Under five minutes per sampled brief |
| Extraction precision | Correct source-supported proposals divided by all proposals | At least 90% across the meeting sample |
| Extraction recall | Correct extracted decisions/actions divided by independently marked source decisions/actions | At least 90% across the meeting sample |
| Decision recall | Correct current decision, rationale, and source recovered within one minute | At least eight of ten tasks |
| Interview first value | Active time through a useful first result with required prerequisites available | Under ten minutes |
| Interview revisit | Active time to change the intended existing configuration and verify it | Under three minutes in at least three revisits, with no duplicates |
| Suggestion usefulness | Sessions with a relevant actionable suggestion selected for real work | At least three of five sessions |
| Intentional daily use | Workdays with a real recipe use | At least eight of ten observed workdays |
| Attention relevance | Relevant/actionable initial priorities divided by all initial priorities shown | Establish the baseline at midpoint; report missed material needs separately |
| Net time recovered | Comparable baseline effort minus all assisted effort | Initial target of 120 minutes per five-workday week |
| Outcome quality | A source-supported example of improved decision work or preserved follow-through | At least two concrete examples |

Targets are planning assumptions, not achieved facts.
HS-200-01 can recalibrate a target to the actual workload before scored sampling, with a recorded reason.
Once sampling starts, a missed target is a result.
Do not lower the threshold retrospectively to declare success.

Subtract capture, setup, source selection, review, correction, supervision, repair, and maintenance from the baseline.
Allocate shared setup costs once.
Report wall-clock time separately from active effort.
An avoided hypothetical incident is not converted into invented savings.

## Review cadence

At day five, identify the three largest causes of lost effort or incorrect output.
Prioritize repairs through the owning stories.
Preserve the failed observations.

At day ten, classify every target as pass, fail, or inconclusive.
Record whether the owner wants to continue each recipe and why.
Spontaneous return is useful additional evidence.
Required daily use must not be manufactured as a compliance exercise.

HS-200-23 closes the daily-practice review.
HS-200-30 adds five bounded supervised assignments.
Each assignment records acceptance, correction, failure, or an inconclusive outcome and the actual supervision effort.
The five assignments need not occur inside the original ten-workday period.

HS-200-36 adds three actual scheduled occurrences for each enabled unattended recipe.
Immediate run-now calls do not count as scheduled occurrences.
Failure injection supplements these observations.

HS-200-37 combines the evidence without adding overlapping test or task counts.
The final report distinguishes daily value, supervised value, and unattended reliability.

## Evidence record

Each observation records:

| Field | Content |
|---|---|
| Identity | Scenario, story, build, model, hardware, configuration version |
| Task | Actual purpose, scope, source refs, expected result, baseline method |
| Execution | Start/end, operation identities, output refs, terminal or indeterminate state |
| Review | Support judgments, corrections, failed checks, reviewer outcome |
| Effort | Active minutes, elapsed minutes, setup allocation, maintenance |
| Coverage | Available, stale, failed, excluded, and missing sources |
| Result | Pass, fail, or inconclusive with reason and follow-up owner |

Use the existing evidence capture and UAT conventions.
Create a paired evidence file only when its story ships.
The final phase summary must distinguish the product release decision from any later market or portfolio claims.
