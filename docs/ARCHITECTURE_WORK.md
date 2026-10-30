# Architecture work recipes

Use these recipes to turn existing context into a decision brief, meeting agenda, implementation task, or recurring review.
Each recipe names its inputs, current Desk path, and result to inspect.
Models can help prepare work. Your organization's decision rights remain yours to establish.

## Prepare the working context

1. Keep the goal and constraints as a Note.
2. Open the relevant Project or source records.
3. Select **Ask about this**, or open Ask and choose records through the toolbar scope menu.
4. Describe the output and identify unknown facts.
5. Inspect the returned sources before using the draft.

Example: “Make architecture decisions easier to review and revisit.”
Add the evidence you require, a deadline when known, and the work that can be delegated.
Ask one follow-up at a time when the constraints are unclear.
Use **Save as note** for the working brief.

About supplies a starting point for retrieval.
A tool-capable engine can inspect additional permitted Desk records.
A Project-specific service can enforce a narrower scope.

## Recipe: prepare a decision review

**Input:** A Project, relevant decision records, and the question under review.
**Output:** A review brief with evidence, open questions, and review conditions.

1. Open Ask from the Project or selected decision.
2. Enter this request:

   > Prepare a decision review from these records.
   > Separate facts from assumptions and new options.
   > Include rationale, open questions, and review conditions.
   > Cite evidence and name missing information.

3. Open the sources returned with the answer.
4. Correct unsupported claims through a follow-up.
5. Select **Save as note** for the reviewed draft.

| Field | Content to check |
| --- | --- |
| Question | The decision in one sentence |
| Context | Facts with source references |
| Options | Recorded alternatives and labeled new proposals |
| Constraints | Requirements and explicit assumptions |
| Rationale | Reasons supported by the available evidence |
| Decision owner | Named authority, or an explicit unknown |
| Review condition | A change that should trigger another review |
| Gaps | Evidence or input still needed |

A saved brief does not establish organizational acceptance.
Confirm the decision through the applicable decision process and record its outcome.

## Recipe: prepare a transformation meeting

**Input:** A meeting purpose and relevant Notes, decisions, or Meetings.
**Output:** An agenda and questions linked to that evidence.

1. Open Ask and choose the starting records through the toolbar scope menu.
2. Describe the meeting's purpose and participants when known.
3. Ask for an agenda with open decisions, changed assumptions, and owner questions.
4. Inspect its sources and replace guessed dates or owners with explicit unknowns.
5. Select **Save as note** for the agenda.

Record or import the meeting through [Meeting mode](MEETING_MODE_GUIDE.md).
Review its transcript and intelligence before confirming a decision or commitment.
Use the prior agenda as context for an Ask about what changed.

Confidential relationship editing belongs in [People](PEOPLE_INTEGRATION.md).
Its protected store and access rules differ from an ordinary Note.

## Recipe: prepare an agent brief

**Input:** A task, its Project, repository, constraints, and acceptance evidence.
**Output:** A reviewed brief and a launched coding session when the prerequisites are ready.

1. Create a task from a Note or an Ask answer using its supported task control.
2. Associate the work with the Project and repository.
3. Select **Hand to agent** on the supported source item.
4. Inspect the brief, source context, repository, branch, and worktree.
5. Choose the installed agent and optional reviewer.
6. Launch the work, or queue it when the concurrency limit is full.

| Brief element | Question to answer |
| --- | --- |
| Outcome | What must be true when the task is done? |
| Scope | Which systems, files, and changes are allowed? |
| Constraints | What must the implementation preserve? |
| Sources | Which records support the task? |
| Validation | Which result or check shows that the change works? |
| Completion | What artifact and review result must return? |

The launch creates an execution attempt, not a completed implementation.
Review the agent's result and repository changes before accepting the task.
A CLI engine used to answer an Ask is a separate path from that repository session.
Read [Coder integration](CODER_INTEGRATION.md) for dependencies, queueing, and session replies.

## Recipe: test a recurring review by hand

**Input:** A useful output, the records it needs, and a desired frequency.
**Output:** A tested instruction that can become an Automation.

1. Use Ask to prepare the output once from known records.
2. Check its evidence and correct the instruction.
3. Create an Automation with that instruction in **Do**.
4. Choose **About**, **With**, and **Put it in**.
5. Run a manual trial and inspect its retained result.
6. Enable a supported **When** trigger only after the trial is useful.

Example: draft open architecture decisions each Friday and put the result in My Inbox.
This becomes recurring work only when the saved trigger, executor, and authority are configured.
The hub must be running when the job is due.
Read [Automation](AUTOMATION.md) for source sets, agent handoffs, and result placement.

The separate prepared-procedure catalogue has its own current trigger limits.
Do not infer scheduling support from a recipe descriptor or a model's suggested cadence.

## Assess usefulness

Record the trial's source coverage, corrections, and practical value as a Note.
Compare preparation time only when you measured it.
Check whether the next action is clear and whether the output reduces work for its intended reader.
A plausible answer without evidence is a draft that still needs correction.

The retained [Interview mode](INTERVIEW.md) can also store structured facts and suggestions through its services.
Its parked browser controls are not required for these current Desk recipes.

## Troubleshooting

| Problem | Action |
| --- | --- |
| The Project has few sources | Add relevant records or ask for a template with explicit gaps. |
| The draft has no evidence | Ask for references, then inspect and correct the claims. |
| About omits related work | Check retrieval tools and the actual service scope. |
| A workflow needs an unavailable adapter | Keep a manual instruction and name the missing execution path. |
| Recurring output creates noise | Narrow the instruction, source set, and trigger. |
| The coding agent cannot start | Repair the named repository, CLI, tmux, hook, or engine prerequisite. |
| A launch finished without a useful change | Inspect the agent result and review the repository state before accepting it. |

## See also

- [Project Rooms](PROJECT_ROOMS.md): connected project work.
- [Automation](AUTOMATION.md): recurring execution and results.
- [Coder integration](CODER_INTEGRATION.md): handoffs and session controls.
- [Meeting mode](MEETING_MODE_GUIDE.md): capture and intelligence.
