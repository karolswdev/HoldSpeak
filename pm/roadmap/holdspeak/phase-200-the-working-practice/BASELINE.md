# Phase 200 baseline and earlier work

**Attested:** 2026-09-06, America/Denver, by HS-200-01.
**Repository baseline:** `bea4176c2f7e5a5709e3404e517bd0790d2fe7b2`.
**Planning baseline it supersedes:** `519afd4f82d24ad5bd8c5f17df59b6a4fbeed19d`, inspected 2026-09-05.
**Method:** read-only. Git and GitHub queries, `sqlite3 file:…?mode=ro` against the owner's live database, authenticated GET against the running hub, local toolchain probes, and source inspection. No write of any kind. No product suite was run against the owner database. No secret value was read, copied, or recorded.

The planning revision of this document was a source and documentation
inspection with no database census, no live probe, and no runtime
observation. Those are now performed. The row-level record — the full
observation set, the CI failure ledger, the obligation map, and the
pilot census — is
[assets/baseline-2026-09-06.md](assets/baseline-2026-09-06.md). This
document holds the summary and the disposition; that file holds the
evidence the summary points at.

The identity observation was reproduced twice, as the story's test plan
requires. **Both runs are byte-identical.**

## Observed signals

Rows marked **attested** were observed on the running installation on
2026-09-06. Rows marked *planning* are carried from the 2026-09-05
inspection and have not been re-observed.

| Signal | Evidence | Consequence |
|---|---|---|
| **Two `holdspeak web` processes are running against the same database**, one started 2026-09-05 17:55 on :54644 and one started 2026-09-06 10:36 on :49353. Neither reports the other. **attested** | [detail §1.3](assets/baseline-2026-09-06.md) | This is the condition C1 forbids and P200-A01 requires detecting. It is the highest-value G0 repair and it is live on the owner's desk today. |
| **The running product is not the repository HEAD, and nothing in the product says so.** The hub loaded code at 10:36; main moved to `bea4176c` at 11:29. The served bundle was built at 10:36:01. **attested** | [detail §1.3–§1.4](assets/baseline-2026-09-06.md) | A checkout attests nothing about a running process. Confirms the story's premise and sets HS-200-02's scope. |
| Backend build identity, frontend bundle identity, database identity and config revision are all **unexposed**; schema version is readable in code but appears nowhere under `holdspeak/web/`. **attested** | [`holdspeak/__init__.py:52`](../../../../holdspeak/__init__.py), [`holdspeak/db/core.py:48`](../../../../holdspeak/db/core.py) | Five of C1's eight identity obligations are missing. HS-200-02 is new work, not a repair. |
| **The owner's model route does not work: the default profile requires a key that is unset.** Two LAN destinations are ready and need no key. **attested** | [detail §1.6](assets/baseline-2026-09-06.md) | HS-200-04 can repair this through the existing Settings surface. It is also beat 0 of the owed 176 walk. |
| **The owner has no calendar source and zero calendar events**, after Phase 175 shipped the calendar wire. **attested** | [detail §1.7](assets/baseline-2026-09-06.md) | HS-200-22 cannot assume an event stream. Calendar stays optional for first value. |
| **The owner's desk holds one active Project and nine archived ones**, all created 2026-09-03/04, with zero decisions, zero commitments and zero interview sessions. **attested** | [detail §4](assets/baseline-2026-09-06.md) | No pilot Project is selected. The question is written for the owner; see "Open decisions" below. |
| Interview is merged, with manual drafting and supported Project setup. *planning* | [PR 561](https://github.com/karolswdev/HoldSpeak/pull/561), [delivery status](../../../../docs/internal/architect-assistant/DELIVERY_STATUS.md) | Extend its composition and quality. Preserve its existing durable state and tool boundaries. Its own status document states it does not enable Assignments or bounded scheduling. |
| Recommendation quality remains unproved after prompt changes. *planning* | [Interview limits](../../../../docs/INTERVIEW.md#project-setup-and-automation-limits) | Evaluate real model behavior separately from fixture mechanics. |
| Concierge, Heartbeat, meeting proposals, Steward drafting, and Reach exist on the selected baseline. **attested by source, not by execution** | [obligation map §5](assets/baseline-2026-09-06.md) | Reuse and prove their production paths before adding replacements. |
| **Four CI jobs are red on main**: Unit (30 failures), Integration macOS (3), E2E macOS (2), DeskOS Web Quality (3 TypeScript errors). Documentation Navigation and Linux Smoke pass. **attested** | [Run 34007939416](https://github.com/karolswdev/HoldSpeak/actions/runs/34007939416), [ledger §3](assets/baseline-2026-09-06.md) | The failure ledger now exists with identities, reasons and repair stories. Most failures are runner-environment, not product defects — but not all, and the exceptions are named. |
| The update parser sets `verified=True` whenever a cited ref exists in the inventory. **attested at source** | [`project_update_service.py:583,590`](../../../../holdspeak/services/project_update_service.py) | Valid references need a separate factual-support state. Preserve old provenance without upgrading its meaning. |
| The needs-you builder skips failed Room reads and returns `stale: False`. **attested at source** | [`needs_you_aggregate.py:54-58,105`](../../../../holdspeak/services/needs_you_aggregate.py) | Add explicit source coverage and partial-result semantics. The Room's own `ok / degraded / absent` tag already exists and is discarded — the signal is there to carry. |
| **Reach credentials are wiped on process restart, by design and by docstring.** **attested at source** | [`holdspeak/principals.py:103-110`](../../../../holdspeak/principals.py), [Runner guide](../../../../docs/REACH_RUNNER.md) | Design availability, credential lifetime, and restart recovery before relying on unattended work. Three credential stores exist that share no code path. |
| **Calendar work is merged, not open.** PR 558 merged at `aa278604`; its R1 matcher ruling merged at `7d897302`. **attested** | [PR 558](https://github.com/karolswdev/HoldSpeak/pull/558) | The planning row for this signal is superseded. HS-200-22 integrates a merged wire and completes unbuilt faces, rather than inspecting an open diff. |
| **One PR remains open: #526**, relationship-aware memory plus a designed-only "Continuity" program. **attested** | [PR 526](https://github.com/karolswdev/HoldSpeak/pull/526) | Its retrieval half is an input to HS-200-10 and HS-200-11. Its Continuity half is a competing program specification Phase 200 has not adopted. No Phase 200 row assumes either. |

These are dated observations. A later story re-checks the running
installation before a live action; a read of local working files still
does not establish which revision a running process loaded.

## Capability disposition

Dispositions use EXECUTION.md's vocabulary: reuse and prove ·
integrate · repair a demonstrated gap · new work · defer. The
row-level map, with `file:line` for every EXISTS and an explicit
MISSING for every gap, is
[assets/baseline-2026-09-06.md §5](assets/baseline-2026-09-06.md).

Counted from that map: **69 contract obligations** — 36 EXIST, 22 are
MISSING, 9 are PARTIAL, 2 are a confirmed defect or an observed
undecided condition. Across the 40 stories, **48 disposition tags**:
18 new work, 14 reuse and prove, 13 repair, 3 integrate.

| Capability | Existing owner or seam | Phase 200 disposition |
|---|---|---|
| Runtime identity and custody | `web_runtime.py`, `setup_status.py`, `db/core.py` backup/restore | **New work.** Only process start exists. Build identity, bundle identity, database identity, config revision and two-runtime detection are all missing; backup covers the main database only, not attachments or the People sidecar. 02, 38. |
| Capture and corrections | Dictation runtime, speech sessions, correction memory, journal — including 176's `text` correction kind | Reuse; prove physical capture, permissions, retry, delivery, and restart in 04–05. Eleven parked 176 defects land in 05. |
| Models | Concierge, Model Library, inference assignments, Intelligence Router | Reuse; repair the demonstrated readiness gap in 04 — the default route has no key while two LAN routes are ready — and add return-to-task, which is missing. |
| Evidence and generated updates | `project_update_service.py`, existing reference resolvers | Repair support semantics in 06; the three C2 axes are missing and `claims_json` is an opaque blob, so the migration is a blob rewrite. Reuse through 10–13, 17, and 27. |
| Project attention | `needs_you_aggregate.py`, Heartbeat, Door, shade | Repair coverage in 07 and relevance in 15: no per-source coverage record, no item cap, no dedup key, and a count-only notification edge that cannot see a changed set of the same size. |
| Project preparation | Project, Memory, Monday brief, updates | Reuse; compose three complete recipes in 11, 17, and 21. The missing piece is the evidence manifest (C3), for which the Thought refinement frozen attachment is the pattern to copy. |
| Meeting outcomes | Meeting completion, proposal bridge, decisions, follow-through | Reuse; prove one production chain in 12–14 and 16. Decision supersession exists; an accept/reject verb does not. |
| Working context | Interview state, Notes, Thoughts, Projects, qualified refs | **New work over existing seams.** InterviewService has no promotion path, and two ref vocabularies (`qualified_ref` and `thread_refs`) need reconciling. Avoid a second personal database; PR #526's retrieval half is an input, not an assumption. 10. |
| Interview setup | InterviewService, Thread tools, ProjectSetupService | Repair and extend in 18–20: no configuration-plan record exists, `project_commands` has no unique index on its request hash, three writers skip the replay check, and the setup controller mints no command envelope. The Steward's `steward_steps` expected-vs-observed pattern is the model. |
| Scheduling | Heartbeat, Cadence, scheduled recordings, Steward — **and a fifth owner**, the kernel delegated-schedule path | Keep their owners; expose exact bindings in 21 and 33–35. No binding record and no per-firing occurrence identity exists at any of the four named owners. `kernel_schedule_ticks` is the one durable dedupe row in the tree and is the pattern to generalise. |
| Workers | Delivery factory, steering, adapter capability ledger | Reuse one supported adapter through 24–30. The ledger already decides the adapter on evidence: only `claude-code-hooks` declares authoritative BLOCKING and usage tokens. One demonstrated defect: the factory launch persists its record *after* spawning the process. |
| Assignment outcome and acceptance | Proposed architect-assistant contracts | **New work.** No AssignmentService, no definition table, no `assignment.run` kernel kind, no `assignment:` ref type, no acceptance-check record. 24's task is reconciling two specifications, not discovering one. 24–29. |
| Remote execution | Reach transport, principals, runner | Repair and extend in 31–36. Credentials are confirmed in-memory; three credential stores share no code path; no machine enrollment exists; no launchd or systemd install is documented anywhere. |
| Shared experience | `web/src/desk/surface/`, the canon scanner and ratchet | Reuse. The voice law holds at ceiling `mic: 0` after 176. One gap: MCP steering is read-only while HTTP steering is not, which C11 forbids. |
| Release and observation | Packaging, release gate, API surface (668 routes), MCP sidecar (222 tools, 40 families), web baseline (5 entries) | Reuse and prove in 38–39. The isolated proof driver leaks `$HOME` for subprocesses and import-time paths and is not invoked by CI — 03 owns that. |
| Native devices and portfolio | Existing and planned separate tracks | Retain supported behavior; expand when pilot evidence demonstrates a requirement. |

## Earlier roadmap accounting

Every surviving obligation now has one destination story and a delivery
owner. **Delivery owner is `unassigned` for every row**, matching the
phase status file, until the phase names one. Historical records are
pointed at, never rewritten: no earlier story is flipped, closed, or
re-stated as complete by this story.

The specific inherited proof obligations — the seven owed attended
walks, the eleven unanswered 172–174 owner questions, Phase 176's open
story 06, the sixteen BACKLOG "AG" remainders, and the CI runner
entry — are enumerated one row at a time in
[assets/baseline-2026-09-06.md §2](assets/baseline-2026-09-06.md).

| Earlier work | Treatment | Destination |
|---|---|---|
| 170: Great Pass and Concierge | Adopt integrated implementation; the attended walk is still owed. | 01, 04, 09, 39 |
| 171: Heartbeat | Adopt scheduler, aggregate, and notification work. Prove quiet hours, coverage, and restart. Walk owed. | 07, 15, 21, 33–36 |
| 172: Loop Closes | Adopt production bridge and People joins. Three owner questions unanswered; walk owed. | 12–14, 16 |
| 173: Steward | Adopt drafter and observations. Correct claim semantics. Three counsel questions unanswered; walk owed. | 06, 11, 17, 21 |
| 174: Reach | Adopt transport; complete operational durability. Five owner questions unanswered; walk owed. | 31–36 |
| 175: Calendar and the Clock | **Merged, not open.** Integrate the landed wire; complete the unbuilt faces; three unit failures to diagnose. Walk owed, and his desk has no calendar connected. | 22 |
| 176: Speak Loop | Carry real dictation and correction proof into the core release. **Story 06 remains open in Phase 176**; sixteen remainders parked in BACKLOG "AG". | 05, and 03 for the fence hygiene |
| 177: Thread at Work | Parked behind Phase 200, never deleted. Carry grounded Project conversations and measured usefulness into the daily loop. | 10–11, 18–20, 23 |
| 178: Portfolio | Defer new portfolio surfaces until cross-Project pain is measured. | Expansion decision in 37 |
| 179: Companion | Preserve supported behavior. Defer new native parity commitments. | Expansion decision in 37 |
| 180: Proof | Move real-use, release, and performance proof into this phase's gates. | 08, 16, 23, 30, 36–40 |
| 155: Crew | **Chartered 0/5, nothing shipped.** Its three ratified decisions — receipted subthread calls, depth cap 1, no auto-approve — are reusable inputs and do not conflict with C7. Integrate the decisions; defer the surface. | 24, 26 |
| PR #526: relationship-aware memory + Continuity | Retrieval half is an input; Continuity is a designed-only competing program Phase 200 has not adopted. | 10, 11; adoption decision in 37 |
| Architect-assistant DP-00/00A | Runtime and Interview foundation. Its delivery record states it does not enable DP-03/04/06. | 01–08, 10, 17–20 |
| DP-01/02 | Daily preparation, decisions, and follow-through. | 09–16, 21–23 |
| DP-03/04 | Assignment and supervised delivery. | 24–30 |
| DP-05 | Owner pilot. Begin R1 observation when G1 passes. | 16, 23, 30, 37 |
| DP-06 | Bounded automation. | 31–36 |
| DP-07/08 | Portfolio and further reach. | Evidence-based follow-on decision in 37 |

This mapping changes the default sequence for new work. It does not
rewrite old evidence or declare old unfinished stories complete.
Correct functionality can satisfy a new story through fresh integrated
proof; it does not require a duplicate implementation.

## Repository debt at planning

`.githooks/dw check holdspeak` reports **six** structural issues in the
working tree and **five** on committed main. The five on main are the
ones the planning revision named: orphan evidence in Phase 101 and
missing final summaries in Phases 152, 153, 154 and 156. The sixth is
`phase-170-the-great-pass/evidence-story-03.md`, an **untracked**
file left in the shared tree by another lane; it has never been
committed and is not this story's to move.

The planning change must add zero new structural issues, and this one
adds none: it writes only inside
`pm/roadmap/holdspeak/phase-200-the-working-practice/`.

No evidence file or old final summary is fabricated to make a checker
green. Whether the four missing summaries are written by their own
phases or explicitly retired is a decision for HS-200-40.

The selected release's functional checks remain a separate obligation,
now enumerated as a failure ledger in
[assets/baseline-2026-09-06.md §3](assets/baseline-2026-09-06.md) and
owned by HS-200-03.

## Assumptions

| Assumption | Working default | Status at 2026-09-06 | Resolution point |
|---|---|---|---|
| Initial operator | Karol, using one real transformation stream | **Unresolved and blocking the owner-facing legs.** The desk holds one active Project of unknown provenance and nine archived ones. The question is written below. | 01 (asked), pilot entry |
| Sources | Existing connected repository and available Project records | **Partly resolved.** GitHub and Jira are connected and authenticated; 32 watches and 32 project sources exist across the ten Projects. Which of them belong to the pilot stream is part of the open question. | 01 and 11 |
| Model | A currently configured, compatible, explicitly selected route | **Contradicted.** The configured route is unavailable for want of a key; two LAN routes are ready and unselected. Repairable in an existing surface, but which route the pilot uses is the owner's call because it decides egress. | 04 and 08 |
| Calendar | Optional for the first manual preparation result | **Confirmed necessary.** Zero calendar sources, zero events. | 22 |
| Worker | One existing adapter with enforceable declared limits | **Confirmed available and already decided by evidence:** of four ledger adapters, only `claude-code-hooks` declares authoritative BLOCKING and usage tokens. | 24 and 26 |
| Availability | One owner-controlled hub; no active-active database | **Contradicted in fact.** Two hub processes are running against one database right now. No active-active *database* was introduced, but the assumption of one hub is not currently true on the owner's machine. | 31, with 02 supplying the detection |
| Capacity | One primary delivery lane; no calendar deadline is promised | Unchanged. | Re-estimate after G0 |
| Pilot opportunities | Real tasks may require more than ten elapsed workdays | Unchanged, and now quantified: 6 meetings, 0 decisions, 1 action item, 9 journal rows and 0 corrections on the desk today. | 23 and 37 |

Employer sources, organizational decision rights, and financial savings
are not inferred from personal fixtures.

## Open decisions for the owner

One question blocks the owner-facing legs of G1 and G2. It is written in
full, with the census behind it, in
[assets/baseline-2026-09-06.md §4](assets/baseline-2026-09-06.md).

> **Which real transformation stream is the Phase 200 pilot, and which
> sources belong to it?**
>
> The desk holds one active Project (`proj-10b35905777c`, created
> 2026-09-04: 4 sources, 7 observations, 6 proposals, 1 review) and nine
> archived ones from the same two days. Nothing read-only distinguishes
> a real stream from a Room left standing after the Phase 169 build, and
> no Project content was read to guess. Needed: (1) the stream — that
> Project, a re-scoped version of it, or a new one; (2) the sources —
> which repositories, boards or issue scopes; (3) the employer boundary
> — if the real stream cannot enter this database, the pilot uses a
> personal stream with the limitation recorded rather than a silent
> substitute.

A second, smaller decision rides with it: which model route the pilot's
briefs run on. HS-200-04 can repair the unset-key condition without an
owner decision, but choosing between the ready LAN routes and a cloud
route decides whether transcripts leave the machine, and that is the
owner's call.

HS-200-11, HS-200-16 and HS-200-23 cannot start their owner-facing legs
until the first question is answered. Every G0 story and most of G1
proceeds without it.
