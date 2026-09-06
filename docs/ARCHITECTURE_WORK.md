# Architecture work recipes

Use these recipes to prepare decisions and direct work during an architecture transformation.
They produce manual drafts from the records and context available to HoldSpeak.

Each example is a suggested working method.
It is not a claim that HoldSpeak can discover your organization or execute every part of its transformation.

## Prepare the working context

1. Open an [Interview](INTERVIEW.md) Thread.
2. Describe one outcome in **Goals**.
3. Identify the relevant Project in **Projects**.
4. Explain your constraints in **What matters**.
5. Check the facts saved under **Context**.

Example outcome: “Make architecture decisions easier to review and revisit.”

Useful constraints include a decision deadline, required evidence, and the types of work you can delegate.
Label uncertain information as an assumption.

## Recipe: prepare a decision review

**Input:** a named Project, available decision records, and the question under review.
**Output:** a draft review brief with sources and unresolved questions.

1. Select **Decision log** in Interview.
2. Request a review of the relevant recorded decisions.

   > Prepare a decision review for the selected Project.
   > Separate recorded facts from assumptions.
   > Include the rationale, unresolved questions, and conditions for review.
   > Identify missing evidence without inventing records.

3. Inspect the returned sources.
4. Request corrections for unsupported claims.
5. Keep the final reply as a Note or Artifact.

Use this outline to review the draft:

| Field | Required content |
| --- | --- |
| Question | The decision to make, in one sentence |
| Context | Relevant facts and their source references |
| Options | Recorded options, plus clearly labeled new proposals |
| Constraints | Stated requirements and unresolved assumptions |
| Rationale | The reasons for the recorded or proposed choice |
| Authority | The decision owner, if known |
| Review condition | The change that would require another review |
| Gaps | Evidence or input still required |

A saved brief does not approve a decision.
Use your organization's decision process to establish acceptance and decision rights.
HoldSpeak must not infer those rights from a job title or a Project name.

## Recipe: prepare for a transformation meeting

**Input:** a meeting purpose and selected Notes, decisions, or previous Meeting records.
**Output:** an agenda and a list of questions supported by those records.

1. Open a Thread.
2. Attach the relevant records with `@`.
3. Request an agenda from the attached records.

   > Prepare an agenda for this review.
   > Identify open decisions, changed assumptions, and questions that need an owner.
   > Cite the attached records.
   > Leave unprovided dates and owners as placeholders.

4. Check each question against its source.
5. Keep the agenda as a Note.

After the meeting, use [meeting intelligence](MEETING_MODE_GUIDE.md) to review the transcript and extracted results.
Compare those results with the agenda before you update a decision or send a follow-up.
Use the protected [People](PEOPLE_INTEGRATION.md) surface for confidential relationship context.

## Recipe: prepare a manual agent brief

**Input:** a specific task, an existing Project, and explicit execution constraints.
**Output:** a brief that you can review before you give it to a Coder session or another agent.

1. Select **Delegation** in Interview.
2. Describe the task and its allowed scope.
3. Request a manual agent brief.

   > Prepare a brief to investigate the stated architecture question.
   > Include the available sources, expected output, and validation method.
   > List assumptions and missing prerequisites.
   > Keep execution and configuration changes as proposals.

4. Add the repository, branch, and paths if the task requires code access.
5. Specify the actions that require your decision.
6. Keep the reviewed brief.

Before you deliver the brief, verify these fields:

| Field | Question |
| --- | --- |
| Objective | What result must the worker produce? |
| Scope | Which systems, repositories, and files are included? |
| Sources | Which records can the worker use? |
| Authority | Which actions can the worker perform? |
| Checkpoint | When must the worker return for a decision? |
| Validation | What evidence will show that the result works? |
| Completion | What must be present before you accept the result? |

Interview prepares the brief. It does not start a worker for this recipe.
For actual delivery, use an existing [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk) path or your external agent client.
Check the applicable [authority rules](AUTHORITY.md) before delivery.

## Recipe: test a recurring review manually

**Input:** an output that already helped once, a review frequency, and its source requirements.
**Output:** a repeatable recipe and a decision about whether automation is useful.

1. Select **Cadences** in Interview.
2. Describe the result you want to repeat.
3. Specify the intended day, time, and time zone.
4. Request a manual trial with the available sources.
5. Review the draft and record corrections.
6. Keep the recipe if the trial is useful.

For example: “Every Friday, prepare unresolved decisions for my Monday architecture review.”
That sentence describes a desired cadence. It does not install one.
Use [Automation](AUTOMATION.md) to determine whether an existing execution path supports it.

For an automated version, verify the configured trigger, source scope, destination, authority, and stop control.
If a required capability is absent, retain the manual recipe and name the missing capability.

## Assess daily usefulness

Keep a short review Note after each trial.
Record the task, source coverage, corrections, and whether the result helped the decision.
Compare preparation time only when you have measured it.

Use these observations to change the same Interview context.
Retain useful suggestions with **Keep idea**.
Defer or dismiss suggestions that do not help.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The Project contains few records | Add or attach the required sources. Request a template with explicit gaps until the evidence exists. |
| The draft sounds plausible but lacks evidence | Request source references for factual claims. Remove unsupported claims. |
| The suggested workflow needs an unsupported tool | Keep it as a manual recipe or an unavailable idea. |
| A recurring result creates too much work | Revisit **What matters** and **Cadences**. Reduce the scope before you automate it. |

## See also

- [Interview](INTERVIEW.md): context, suggestions, and repeat visits.
- [Project Rooms](PROJECT_ROOMS.md): project records and source connections.
- [Automation](AUTOMATION.md): execution paths and current limits.
- [Meeting mode](MEETING_MODE_GUIDE.md): capture and review after a meeting.
