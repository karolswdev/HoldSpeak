# Project Rooms — product and market-validation SRS

Document ID: `SRS-PRJ-PRODUCT`
Status: Draft for implementation planning
Version: 0.1
Date: 2026-08-30

## 1. Council verdict

Project Room is the correct universal surface, but it is not a defensible market wedge by itself.

The wedge is:

> HoldSpeak is the personal project chief of staff that continuously reconstructs the truth of one consequential project from meetings, decisions, commitments, notes, and delivery systems; shows only what materially changed; performs configured follow-through in local YOLO mode; and leaves an evidence-backed update ready for the owner.

The product components have distinct jobs:

- **Project Interview** — compiles the outcome and watch intent into a working system.
- **Watches** — continuously observe the exact native/provider conditions that matter.
- **Project Room** — the place the user opens.
- **Delta** — the repeat-use loop.
- **Steward** — the leverage and differentiation.
- **Update Factory** — the immediately legible proof of value.
- **MCP driver** — the reusable programmatic interface, not the proposition.

A manually maintained risk/milestone dashboard fails the thesis. An update writer alone is also insufficient.

The near-term activation promise is:

> Describe the outcome; within five minutes HoldSpeak leaves you with a real tested Watch, an understandable cadence, and an agent prepared to act.

## 2. Market baseline

| Adjacent product | Current capability | HoldSpeak implication |
|---|---|---|
| Linear | Structured updates, update staleness, Pulse summaries, and update drafting from project changes and linked Slack. [Updates](https://linear.app/docs/initiative-and-project-updates), [Pulse](https://linear.app/docs/pulse) | “AI writes my update” is commodity. HoldSpeak must cover cross-system evidence, decision lineage, and follow-through. |
| Notion | Custom Agents perform scheduled/triggered work across Notion and connected tools/MCP. [Custom Agents](https://www.notion.com/en-gb/blog/introducing-custom-agents) | Recurring reports are commodity. HoldSpeak must require far less workspace construction and maintenance. |
| Asana | AI Teammates, Dash, AI Studio, connectors/MCP, and a Work Graph coordinate projects and agents. [Asana AI](https://asana.com/product/ai), [human-agent direction](https://investors.asana.com/news-releases/news-release-details/asana-unveils-operating-system-human-agent-teams) | Do not compete on enterprise work-management breadth. Win with the individual leader's cross-system fluency and local YOLO leverage. |
| Atlassian Rovo | Agents monitor Jira progress and delivery risk. [Rovo Agents](https://support.atlassian.com/rovo/docs/agents/) | Delivery-risk detection inside Jira is insufficient differentiation. Connect delivery facts to meetings, decisions, promises, and communication. |

Directional market evidence, not quantitative proof, repeatedly describes duplicated status entry, manual leadership packs, and flexible workspace maintenance burden. See [project status duplication](https://www.reddit.com/r/projectmanagement/comments/1i17xud), [Notion maintenance](https://www.reddit.com/r/Notion/comments/1t8c39c/i_think_the_hardest_part_about_using_notion_long/), [manual PMO reporting](https://www.reddit.com/r/projectmanagement/comments/1swc15p/project_reporting_how_much_is_still_manual/), and [G2 PPM analysis](https://learn.g2.com/best-project-and-portfolio-management-software).

Resulting product laws:

1. The user MUST NOT re-key source-system state to maintain the Room.
2. Weekly maintenance MUST remain materially below time saved.
3. Important update claims MUST resolve to evidence.
4. Steward MUST execute follow-through, not merely summarize.

## 3. Primary user and jobs

### PV-PER-001 — Transformation/architecture lead

A senior architect, transformation lead, engineering leader, technical program owner, founder, or staff-level power user who:

- owns outcomes spanning multiple teams and systems;
- receives truth through meetings, tickets, PRs, notes, decisions, and informal conversations;
- must brief leadership and support teams;
- is not a dedicated project administrator;
- is comfortable granting a local agent broad authority;
- values speed, keyboard fluency, inspectability, and extensibility.

Primary jobs:

- “Tell me what materially changed since I last understood this Project.”
- “Show me which decision, dependency, risk, or promise now requires judgment.”
- “Perform the obvious maintenance and follow-through without supervision.”
- “Prepare the update I owe, with evidence I can inspect.”
- “Let me correct your interpretation once and move on.”

### PV-PER-002 — Multi-project technical power user

An independent builder, consultant, product lead, or technical leader personally managing several consequential workstreams.

### Unsupported initial personas

- organization-wide PMO seeking capacity, budget, or earned-value management;
- collaboration-first teams requiring concurrent multi-user planning;
- users primarily seeking a Jira/Asana task-board replacement;
- HR/performance-management buyers;
- users unwilling to connect or capture source evidence.

## 4. Validation hypotheses

| ID | Hypothesis | Required evidence | Falsification threshold |
|---|---|---|---|
| PV-H01 | First value requires no ontology setup. | Useful evidence-linked Delta within 10 minutes of creation/import. | Most Projects require more than 20 minutes of schema/view/source maintenance. |
| PV-H02 | Delta creates repeat use. | At least 3 of 5 design partners voluntarily review Delta in 3 of 4 test weeks. | Users open only when reminded or writing a report. |
| PV-H03 | HoldSpeak surfaces missed material. | At least 3 of 5 users report one consequential item they had not reconciled. | Delta merely repeats obvious ticket activity. |
| PV-H04 | Update Factory removes real work. | Median edit-to-copy under five minutes and at least 70% generated content retained. | Drafts are routinely rewritten or require source reconstruction. |
| PV-H05 | YOLO Steward creates return value. | At least 70% of completed runs leave useful state, action, draft, or judgment. | Cleanup time equals or exceeds time saved. |
| PV-H06 | Cross-citizen understanding differentiates. | Users value Meeting/Decision/Door/delivery composition over issue-tracker summary. | Connected Linear/Jira/Notion agent solves the job equally well. |
| PV-H07 | The product has economic value. | At least 3 of 5 external partners agree to pay or continue a paid pilot. | Praise does not convert to continued use or payment intent. |
| PV-H08 | Interview-installed Watches eliminate blank-dashboard setup. | At least 80% install a tested first Watch; median time with existing auth is at most five minutes. | Users require manual provider queries, ontology construction, or repeated setup repair. |

## 5. Strict scope

### MUST / V0

- Specialized Web Project Room.
- Project name, purpose, outcome, lifecycle, review cadence, and revision.
- Typed relationships to existing HoldSpeak citizens.
- Project-owned milestones, risks, dependencies, source bindings, review cursor, proposals, updates, and Steward runs.
- Sources: Meetings, Decisions, Door/Follow-Through, Notes/Artifacts/Threads, and one real delivery connector.
- Interview-led outcome/Watch setup, live provider capability discovery, real test, baseline, and activation.
- Now plus keyboard-operable Delta review.
- Evidence-linked update editing, save, and Copy as Markdown.
- Manual and scheduled local YOLO Steward.
- One action recipe that produces real follow-through.
- Minimal `project.*` MCP family over the same application service.
- Local validation instrumentation and redacted experiment export.
- Transformation and Blank configurations using one domain model.

### SHOULD / V1 validation

- Jira when required by the selected EverDriven proving Project.
- Leadership and technical update presets.
- Project-scoped Thread and Ask.
- narrow browser-window layout;
- correction rules learned from repeated dismissals;
- saved Project views;
- source refresh scheduling and retry controls.

### LATER / V2+

- graphical Map;
- portfolio/cross-Project rollups;
- deep Project hierarchies;
- arbitrary schemas/custom fields;
- automatic Slack/email publication;
- broad Microsoft 365 connector suite;
- multi-user collaboration, remote MCP, enterprise governance;
- generalized plan generation;
- cost/resource/budget management;
- Swift/native mobile.

## 6. Product requirements

### 6.1 Onboarding and first value

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-001 | MUST | Primary creation MUST begin with intended outcome and what HoldSpeak should notice, not metadata or ontology; name may be inferred and edited. | T,U |
| PV-002 | MUST | Transformation and Blank MUST store the same Project semantics and differ only in defaults/modules. | T,I |
| PV-003 | MUST | Within two questions, setup MUST offer two to five concrete Watch recommendations grounded in intent and usable provider/native capability. | T,D |
| PV-004 | MUST | A prepared proving Project MUST activate one live-tested Watch within five minutes with existing auth and reach useful evidence-linked state within 10 minutes. | D,U |
| PV-005 | MUST | Linking source material MUST not require copying its content into Project-owned fields. | T,I |
| PV-006 | MUST | A Watch recommendation MUST show exact scope, condition, cadence, response, readiness, and why it was proposed. | T,D |
| PV-007 | MUST | Setup MUST show current matching entities before activation; first value MUST NOT depend on waiting for a future transition. | T,D,U |
| PV-008 | MUST | Blank/manual-only creation and deterministic setup MUST remain available when providers or inference are unavailable. | T,D |

### 6.2 Thirty-second truth

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-010 | MUST | Within 30 seconds of opening, the owner MUST be able to state outcome, material changes, top risks/blockers, pending decisions, stale evidence, next checkpoint, and Steward state. | U |
| PV-011 | MUST | No change, stale source, unavailable source, and stable Project MUST remain different product states. | T,D |
| PV-012 | MUST | The initial attention set MUST be material and capped; raw activity is not the opening experience. | T,U |
| PV-013 | MUST | Every derived claim MUST open an evidence source or state that evidence is missing. | T,D |

### 6.3 Review and correction

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-020 | MUST | Candidate changes MUST be grouped by meaning rather than connector/source. | T,D |
| PV-021 | MUST | The owner MUST be able to Accept, Edit & accept, Defer, or Dismiss each candidate. | T,D |
| PV-022 | MUST | An unchanged dismissed candidate MUST NOT recur; materially new evidence may produce a linked successor. | T |
| PV-023 | MUST | Conflicting evidence MUST remain a conflict for judgment rather than an automatic winner. | T,D |
| PV-024 | MUST | Review completion MUST leave a durable checkpoint and advance the source cursor. | T,I |
| PV-025 | SHOULD | Repeated corrections SHOULD be convertible into a visible Project-local rule. | T,D |

### 6.4 Update value

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-030 | MUST | Update MUST be an editable document, not a chat response. | T,D |
| PV-031 | MUST | It MUST separate status, changes, risks/dependencies, decisions required, completed follow-through, and next moves while omitting empty sections. | T,D |
| PV-032 | MUST | It MUST show source coverage, stale/unavailable sources, and unresolved conflicts. | T,D |
| PV-033 | MUST | Editing prose MUST NOT mutate Project truth. | T |
| PV-034 | MUST | The owner MUST be able to save a version and copy Markdown; external publication is later. | T,D |
| PV-035 | SHOULD | Personal, Leadership, and Technical presets SHOULD alter emphasis, not facts. | T,D |

### 6.5 YOLO value

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-040 | MUST | YOLO MUST run configured available tools without per-action prompts. | T,D |
| PV-041 | MUST | V0 MUST ship one real action recipe selected from the proving Project, not a simulated/demo-only action. | D,U |
| PV-042 | MUST | A run MUST produce typed changed state, a real action result, an update, an explicit judgment request, or honest no-change. Prose alone is not an action. | T,I |
| PV-043 | MUST | The return experience MUST show actual successes and failures, not synthetic completion. | T,D |
| PV-044 | MUST | Pause/Resume/Stop are operational controls and MUST NOT introduce approval ceremony. | T,D |
| PV-045 | MUST | After inspecting a run, the product MAY ask one lightweight usefulness question and optional correction; it MUST NOT interrupt each action. | T,U |

### 6.6 Validation instrumentation

| ID | Pri | Requirement | Verify |
|---|---|---|---|
| PV-050 | MUST | Local events MUST cover Project creation, first evidence, refresh, candidate decisions, review completion, draft/save/copy, Steward run/action result, update edit, and Room return. | T,I |
| PV-051 | MUST | The system MUST derive time-to-first-Delta, review time, accept/edit/defer/dismiss rates, source coverage, update retention/edit distance, time-to-copy, run usefulness, and weekly active reviews. | T,I |
| PV-052 | MUST | The owner MUST be able to export a redacted validation report without Project contents. | T,D |
| PV-053 | MUST | Product telemetry MUST measure maintenance time as well as time saved. | U,I |

## 7. Core validation journeys

### PV-J01 — First real Project

Describe “Technology Transformation,” state the material signals to watch, accept and clarify one native/delivery Watch, live-test and baseline it, then open on current useful state.

Acceptance: one tested active Watch in under five minutes with existing auth and one material source-linked state/Delta in under 10 minutes, with no custom fields, JSON, JQL, or view construction.

### PV-J02 — Monday truth recovery

Open after several source changes, review semantic candidates by keyboard, write one accepted commitment through to Door, and finish review.

Acceptance: unchanged reopening produces no duplicate candidates.

### PV-J03 — Leadership update

Draft from accepted Project state, inspect a source, edit as a document, save, and copy Markdown.

Acceptance: saved content and evidence manifest reproduce the update; edits do not alter Project facts.

### PV-J04 — Unattended YOLO value

Enable schedule/action recipe, let source evidence change while away, and return after the Steward runs.

Acceptance: the run performs one real useful action, drafts an update, and reports actual outcomes/failures without prompts.

### PV-J05 — Wrong interpretation

Edit/dismiss an ambiguous risk; unchanged evidence stays suppressed; later contradictory evidence becomes a linked new candidate.

Acceptance: correction persists without rewriting the source.

## 8. Launch gates

### Gate A — internal dogfood

Use two real EverDriven Projects for three consecutive weeks. Pass only if:

- both reach first useful Delta in one session;
- both install at least one live-tested Watch during the interview;
- at least one missed/late item is surfaced;
- at least three real updates are created and used;
- at least two unattended runs produce useful return value;
- weekly maintenance is below estimated reconciliation time saved;
- no important claim lacks inspectable evidence.

### Gate B — five external design partners

Run a four-week assisted alpha. Pass only if:

- 4/5 reach first value during onboarding;
- 3/5 voluntarily return in three different weeks;
- 3/5 produce/use at least two updates;
- median open-to-copy time is under five minutes after onboarding;
- at least 60% of material candidates are accepted or edited-and-accepted;
- 3/5 agree to pay or continue a paid pilot.

### Gate C — wedge decision

- **Proceed as Project Steward** if Delta, actions, and updates all repeatably create value.
- **Narrow to evidence-backed Update Factory** if updates retain value but follow-through does not.
- **Narrow to personal project intelligence** if Delta is valuable but actions/updates are not.
- **Stop/reframe** if Room maintenance is high, accepted candidate precision remains below 40% after tuning, or native connected-tool agents solve the job equally well.

## 9. Primary risks and tests

| Risk | Falsification test |
|---|---|
| Commodity update generator | Blind-rate HoldSpeak versus the native connected tool on usefulness, missed material, evidence, and prep time. |
| Ontology maintenance burden | Measure setup/weekly maintenance; remove fields/modules if maintenance exceeds 20% of reported time saved. |
| Delta becomes another inbox | Cap initial attention, measure defer/dismiss rate and queue age. |
| Connector ambition blocks proof | Prove native sources plus one production connector; do not claim fixture-only universality. |
| Steward is automation theater | Require typed changed state or real action result; prose does not count. |
| Polished prose hides weak truth | Measure evidence coverage and edit distance separately. |
| Universal model weakens onboarding | Dogfood Transformation defaults while keeping universal domain nouns. |
| Interview becomes chat theater | Require a visible compiled contract, real provider test, current entities, and deterministic fallback. |
| MCP/provider breadth delays proof | Use one provider adapter contract; ship live GitHub first and add Jira only when the proving Project requires its real adapter. |
| YOLO creates cleanup | Track corrections/reversals and direct usefulness; pause expansion if cleanup exceeds value. |

## 10. Required discovery inputs

Before freezing V0 implementation order, the owner shall select:

1. one active EverDriven proving Project;
2. the first required external source—Jira, GitHub, or Microsoft 365;
3. the first unattended action that would feel genuinely valuable;
4. the actual update artifact sent today;
5. five potential external design partners and a price at which intent is meaningful.

The proving Project and first useful unattended action—not Map layout—determine V0 sequencing.
