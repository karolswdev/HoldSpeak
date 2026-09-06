# Interview

Use Interview to describe your work and develop useful ways to use HoldSpeak.
You can revisit each topic as your goals, Projects, and working habits change.

Interview runs inside a normal Thread.
The model asks questions and proposes ideas. The controller checks tool access and saves structured context.
The conversation can vary. The state and tool checks follow defined rules.

## Before you start

Configure a suitable model through [Settings > Models](MODELS.md).
Tool use depends on the model, its assignment, and the current permissions.
Existing Project records can provide context. You can also start by describing one outcome without a Project.

There are two question-based surfaces in HoldSpeak:

| Surface | Purpose |
| --- | --- |
| **Interview** mode in a Thread | Develop working context and suggestions across repeatable sections. |
| **Interview** pane in the Thought Workbench | Refine one Note through focused questions. |

This guide describes the Thread mode.
See [Develop a thought](USER_GUIDE.md#develop-a-thought) for the Note workflow.

## Start a conversation

1. Select **Desk > New Thread**.
2. Select **Interview** above the composer.
3. Describe one outcome that would help your work.
4. Select **Send**.

Example: “I lead an architecture transformation. Help me prepare a decision review from the Projects already recorded here.”

Your prompt appears in the conversation while the request starts.
The model can inspect permitted records, save context, or ask a question.
Routine calls remain inside **Actions**. Open that control to inspect them.
Requests for a decision, tool questions, and failures remain visible.

## Choose a section

Use **Section** to change the topic. You can return to an earlier section in the same Thread.
Selecting a section changes its available tools. It does not itself send a model request.

| Section | What to discuss | Current capability |
| --- | --- | --- |
| **Goals** | Desired outcomes and signs of progress | Read existing Projects and save stated or inferred context. |
| **Projects** | Project scope, outcomes, and source gaps | Read Projects and use the existing Project setup tools. |
| **What matters** | Changes that deserve attention | Read Project and decision records to support suggestions. |
| **Cadences** | Repeated preparation, reviews, and outputs | Read Cadence status and loops. Develop a manual recipe. |
| **People** | Confidential relationship work | Open the protected People surface. The Thread composer is absent in this section. |
| **Decision log** | Rationale, open decisions, and review conditions | Read decision records and prepare a manual brief. |
| **Delegation** | Agent briefs, constraints, and expected results | Read Workbench records and prepare a manual brief. |
| **Sources & models** | Missing connections or model readiness | Inspect connection and provider records. Continue setup in the existing controls. |

The People handoff does not collect private relationship details in this Thread.
Enter credentials through the relevant setup control, not in an Interview answer.

## Review saved context

1. Open **Context**.
2. Expand **Known context**.
3. Read the fact and its basis.
4. Expand **Source** to inspect the quoted answer.

**Your answer** identifies context based on a stated answer.
**Inferred** identifies a model interpretation.
The source reference helps you check what supports the fact. It does not prove that an inference is correct.

To correct context, state the correction in the conversation.
Then check **Known context** for the updated record.
The model's statement that it remembered something is insufficient without a saved fact.

To remove a fact, select its **Remove** control.
The controller also removes suggestions that depend on that fact.
A changed fact invalidates dependent ideas so they need reconsideration.
Removing context does not erase earlier Thread messages, kept outputs, or backups.

## Review a suggestion

Open **Context** to see suggestions for the current section.
Use **Reason & prerequisites** to inspect the basis and missing requirements.
Use **All suggestions** to review ideas from other sections and earlier choices.

| Label | Meaning |
| --- | --- |
| **Manual draft** | You can request a draft through this conversation. |
| **Needs input** | The idea needs more information. |
| **Needs connection** | The idea needs a source or service connection. |
| **Idea · unavailable** | The proposed behavior is unavailable in the current capability set. |

These labels describe feasibility. They do not establish that a task ran or an automation exists.

| Control | Result |
| --- | --- |
| **Try draft** | Records the choice and immediately sends a model request to prepare a manual draft. |
| **Keep idea** | Records that you want to retain the idea. |
| **Later** | Defers the idea. |
| **Dismiss** | Records that you declined the idea. |
| **Explore** | Returns from draft preparation to exploration. |

**Try draft** appears for a proposed manual suggestion.
Its request asks the model to identify gaps and keep configuration changes as proposals.
It does not schedule work or start a general-purpose worker.

## Keep a useful result

1. Read the completed draft in the Thread.
2. Check source claims and assumptions.
3. Correct unsupported details through the conversation.
4. Use the reply's Keep control to save a Note or Artifact.
5. Open the saved record to verify its contents.

**Keep idea** and Keep on a reply have different purposes.
The first records a suggestion choice. The second creates a separate output record.
The Thread also retains the conversation itself.

## Repeat or resume

Reopen the same Thread to resume its saved sections, facts, and suggestion choices.
Start a new Thread when you want separate context for a different purpose.
Interview context belongs to its Thread. It is not a global personal profile.

Switching between Chair and Floor preserves the open Thread and its current draft.
An unsent composer draft has no durable-save guarantee across a reload.
If sending fails, the composer retains the text for correction or retry.
Review the visible failure before you submit again.

## Project setup and automation limits

In **Projects**, Interview can use the existing setup flow to select, test, and finalize the Project scope you choose.
These operations can change Project configuration under the applicable authority rules.
Check the resulting Project and its sources after setup.
A proposal is not proof of a successful configuration change.

The current Interview does not install arbitrary schedules, general agent assignments, or unsupported integrations.
For available event and scheduled paths, see [Automation](AUTOMATION.md).
Completing an Interview does not authorize recurring work.

Model responses still need review.
Observed limitations include repeated questions, overly broad missing-source claims, and unprovided details that need placeholder labels.
Successful tool calls establish execution results. They do not establish recommendation quality.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Interview is absent from the mode tabs | Check that your installation includes the repeatable Interview feature. |
| The model says it saved a fact, but no fact appears | Inspect **Actions** for the write result. Request the missing save after any reported failure is resolved. |
| A context update fails | Let the Thread reload its current state. Reapply your intended change against the displayed context. |
| The model asks an answered question again | Refer to the existing answer and request the next unresolved question. |
| A draft invents a date, owner, or decision ID | Correct the draft. Require an explicit placeholder where the record provides no value. |
| The composer disappears in People | Select **Open People**, or select another Interview section. |
| A long conversation cannot fit the model | Use the Thread's compaction control or configure a suitable model and context allowance. |
| A suggestion needs a missing service | Use **Sources & models** to identify the prerequisite. Configure it through the named setup surface. |

## See also

- [Architecture work recipes](ARCHITECTURE_WORK.md): decision reviews and manual agent briefs.
- [Threads](USER_GUIDE.md#threads): references, saved replies, tools, and conversation controls.
- [Automation](AUTOMATION.md): supported triggers and execution paths.
- [Control modes](AUTHORITY.md): approval rules and operation boundaries.
