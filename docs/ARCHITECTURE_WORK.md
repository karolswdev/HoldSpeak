# Architecture work recipes

Use these recipes to prepare decisions and direct work during an architecture
change. Each recipe produces a manual draft from the records that HoldSpeak
holds. A recipe is a working method. HoldSpeak does not discover your
organization and does not run your transformation.

## Prepare the working context

1. Open an [Interview](INTERVIEW.md) Thread.
2. Describe one outcome in **Goals**.
3. Select the Project in **Projects**.
4. Write your constraints in **What matters**.
5. Check the facts saved under **Context**.

Example outcome: "Make architecture decisions easier to review and revisit."

Useful constraints are a decision deadline, the evidence you require, and the
work you can delegate. Mark uncertain information as an assumption.

## Recipe: prepare a decision review

**Input:** a Project, its decision records and the question under review.
**Output:** a draft review brief with sources and open questions.

1. Select **Decision log** in Interview.
2. Send this request:

   > Prepare a decision review for the selected Project.
   > Separate recorded facts from assumptions.
   > Include the rationale, open questions and conditions for review.
   > Identify missing evidence. Do not invent records.

3. Inspect the returned sources.
4. Ask for corrections to each unsupported claim.
5. Keep the final reply as a Note or an Artifact.

Check the draft against this outline.

| Field | Required content |
| --- | --- |
| Question | The decision, in one sentence |
| Context | Facts and their source references |
| Options | Recorded options and labeled new proposals |
| Constraints | Stated requirements and open assumptions |
| Rationale | The reasons for the choice |
| Authority | The decision owner, if known |
| Review condition | The change that needs another review |
| Gaps | Evidence or input you still need |

A saved brief does not approve a decision. Use your organization's process for
acceptance and decision rights. HoldSpeak does not infer those rights from a
job title or a Project name.

## Recipe: prepare a transformation meeting

**Input:** a meeting purpose and chosen Notes, decisions or earlier Meetings.
**Output:** an agenda and questions that the records support.

1. Open a Thread.
2. Attach the records with `@`.
3. Send this request:

   > Prepare an agenda for this review.
   > Identify open decisions, changed assumptions and questions that need an owner.
   > Cite the attached records.
   > Leave unknown dates and owners as placeholders.

4. Check each question against its source.
5. Keep the agenda as a Note.

After the meeting, review the transcript and results in
[Meeting mode](MEETING_MODE_GUIDE.md). Compare them with the agenda before you
change a decision or send a follow-up. Use [People](PEOPLE_INTEGRATION.md) for
confidential relationship context.

## Recipe: prepare an agent brief

**Input:** a task, a Project and the limits of the work.
**Output:** a brief that you review before you give it to a Coder session or
another agent.

1. Select **Delegation** in Interview.
2. Describe the task and its allowed scope.
3. Send this request:

   > Prepare a brief to investigate the stated architecture question.
   > Include the sources, the expected output and the validation method.
   > List assumptions and missing prerequisites.
   > Keep execution and configuration changes as proposals.

4. Add the repository, branch and paths if the task needs code access.
5. Name the actions that need your decision.
6. Keep the reviewed brief.

Check these fields before you deliver the brief.

| Field | Question |
| --- | --- |
| Objective | What result must the worker produce? |
| Scope | Which systems, repositories and files are in scope? |
| Sources | Which records can the worker use? |
| Authority | Which actions can the worker do? |
| Checkpoint | When must the worker return for a decision? |
| Validation | What evidence shows that the result works? |
| Completion | What must exist before you accept the result? |

Interview prepares the brief. It does not start a worker. To deliver the brief,
use [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk) or your own
agent client. Check the [authority rules](AUTHORITY.md) first.

## Recipe: test a recurring review by hand

**Input:** an output that helped once, a frequency and its sources.
**Output:** a repeatable recipe and a decision on whether to automate it.

1. Select **Cadences** in Interview.
2. Describe the result you want to repeat.
3. State the day, time and time zone.
4. Request a manual trial with the available sources.
5. Review the draft and record corrections.
6. Keep the recipe if the trial helps.

Example: "Every Friday, prepare open decisions for my Monday architecture
review." This sentence describes a wanted cadence. It does not install one.
Read [Automation](AUTOMATION.md) to find an execution path that supports it.

Before you automate, check the trigger, the source scope, the destination, the
authority and the stop control. If a capability is missing, keep the manual
recipe and name the gap.

## Assess usefulness

After each trial, write a short Note. Record the task, the source coverage,
your corrections and whether the result helped. Compare preparation time only
if you measured it. Use **Keep idea** on suggestions that help. Defer or
dismiss the others.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The Project has few records | Add or attach sources. Ask for a template with explicit gaps. |
| The draft sounds right but has no evidence | Ask for source references. Remove unsupported claims. |
| The workflow needs a tool HoldSpeak lacks | Keep it as a manual recipe. |
| A recurring result creates too much work | Narrow **What matters** and **Cadences** before you automate. |

## See also

- [Interview](INTERVIEW.md)
- [Project Rooms](PROJECT_ROOMS.md)
- [Automation](AUTOMATION.md)
- [Meeting mode](MEETING_MODE_GUIDE.md)
