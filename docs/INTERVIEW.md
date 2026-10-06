# Interview

Interview helps you describe your work and find useful ways to use HoldSpeak.
It runs in a normal Thread. You can return to each topic as your goals and Projects change.

The model asks questions and proposes ideas. The controller checks tool access and saves structured context.
The conversation can vary. The state and the tool checks follow fixed rules.

## Before you start

Set up a model in [Models](MODELS.md). Tool use depends on the model, its assignment, and the current permissions.
Existing Projects give Interview context. You can also start with one outcome and no Project.

HoldSpeak has two question-based surfaces:

| Surface | Purpose |
| --- | --- |
| **Interview** mode in a Thread | Build working context and suggestions across sections. This guide covers it. |
| **Interview** pane in the Thought Workbench | Refine one Note with focused questions. See [Develop a thought](USER_GUIDE.md#develop-a-thought). |

## Start a conversation

1. Select **New Thread**.
2. Select **Interview** in the mode tabs above the composer.
3. Describe one outcome that would help your work.
4. Select **Send**.

Example: "I lead an architecture transformation. Help me prepare a decision review from my Projects."

The model can read permitted records, save context, or ask a question.
Routine tool calls stay inside **Actions**. Open **Actions** to see them.
Decision requests, tool questions, and failures stay visible.

## Choose a section

Use **Section** to change the topic. You can return to an earlier section in the same Thread.
A new section changes the available tools. It does not send a model request.

| Section | Topic | What the model can do |
| --- | --- | --- |
| **Goals** | Outcomes and signs of progress | Read Projects. Save context. |
| **Projects** | Scope, outcomes, and source gaps | Read Projects. Use the Project setup tools. |
| **What matters** | Changes that deserve attention | Read Project and decision records. |
| **Cadences** | Repeated preparation and reviews | Read Cadence status and loops. |
| **People** | Confidential relationship work | None. Select **Open People**. This section has no composer. |
| **Decision log** | Rationale and open decisions | Read decision records. |
| **Delegation** | Agent briefs and constraints | Read Workbench records. |
| **Sources & models** | Missing connections and model readiness | Read connections and providers. |

Never enter credentials in an Interview answer. Use the setup control for the connection.

## Review saved context

1. Select **Context**.
2. Open **Known context**.
3. Read the fact. **Your answer** means you stated it. **Inferred** means the model interpreted it.
4. Open **Source** to see the quoted answer.

The source helps you check a fact. It does not prove that an inference is correct.

To correct a fact, state the correction in the conversation. Then check **Known context**.
A statement from the model that it remembered something is not proof. Look for the saved fact.

To remove a fact, select **Remove**. The controller also removes suggestions that depend on that fact.
Removal does not erase earlier Thread messages, kept outputs, or promoted Notes.

## Review a suggestion

**Context** lists the suggestions for the current section.
Open **Reason & prerequisites** to see the basis and the missing requirements.
Select **All suggestions** to see ideas from other sections.

| Label | Meaning |
| --- | --- |
| **Manual draft** | The model can prepare a draft in this conversation. |
| **Needs input** | The idea needs more information. |
| **Needs connection** | The idea needs a source or service connection. |
| **Idea · unavailable** | HoldSpeak cannot do this today. |

A label describes feasibility. It does not mean a task ran or an automation exists.

| Control | Result |
| --- | --- |
| **Try draft** | Records your choice and sends a request for a manual draft. It does not schedule work. |
| **Keep idea** | Records that you want to keep the idea. |
| **Later** | Defers the idea. |
| **Dismiss** | Records that you declined the idea. |
| **Explore** | Returns from drafting to exploring. |

## Keep a useful result

1. Read the draft in the Thread.
2. Check the source claims and assumptions.
3. Correct unsupported details in the conversation.
4. Use the Keep control on the reply to save a Note or Artifact.
5. Open the saved record and check it.

**Keep idea** records a suggestion choice. Keep on a reply creates a separate output record.

## Promote a fact into a Note

A saved fact belongs to one Thread. Promotion copies the fact into a canonical Note that other work can reference.

Promotion has no button. It runs through the browser API, for the owner only. No model tool can promote or revoke.

Only a fact marked **Your answer** can be promoted. The **People** section refuses promotion.

1. `POST` to `/api/threads/{thread_id}/interview` with `command_id`, `expected_revision`, and an `event`.
   The `event` has `kind` set to `promote` and a `fact_id`.
2. Read the promotion identifier and target reference in the response.
3. `GET /api/threads/{thread_id}/interview/promotions` to list the promotions of a Thread.
4. `POST` an `event` with `kind` set to `revoke_promotion` to withdraw one.

The promotion record stores a source locator and a content hash. It does not store a second copy of the words.
Revoking a promotion does not delete the Note.

A promoted record is reachable by reference, not by relevance.
Attach it to a Thought or name it in a Thread, and the model can read it.
An automatic relevance search over your Notes does not return it.

A model in an ordinary Thread can still read the Note through the desk listing tools.
Promote only facts that you accept in a Thread with a model.

## Resume

Reopen the Thread to resume its sections, facts, and suggestion choices.
Start a new Thread for a different purpose. Interview context belongs to its Thread. It is not a global record about you.

An unsent draft survives a reload. It lives in the browser tab and ends when you close the tab.
If a send fails, the composer keeps your text. Read the error before you send again.

## Project setup limits

In **Projects**, Interview can use the Project setup flow to select, test, and finalize the scope you choose.
Finalizing changes Project configuration under the current [control mode](AUTHORITY.md).
Check the Project and its sources afterward. A proposal does not prove that a change succeeded.

Interview does not install arbitrary schedules, agent assignments, or unsupported integrations.
A finished Interview does not authorize recurring work. For scheduled paths, see [Automation](AUTOMATION.md).

Review every model answer. A successful tool call proves that the call ran. It does not prove that the advice is good.

## Troubleshooting

| Problem | Action |
| --- | --- |
| **Interview** is not in the mode tabs | Update HoldSpeak. |
| The model says it saved a fact, but none appears | Check **Actions** for the write result. Ask for the save again. |
| A context update fails | Let the Thread reload. Apply your change again. |
| The model repeats an answered question | Point to your earlier answer. Ask for the next open question. |
| A draft invents a date, owner, or decision ID | Correct it. Ask for a placeholder where the record has no value. |
| The composer is missing in **People** | Select **Open People**, or select another section. |
| The conversation is too long for the model | Use the Thread compaction control, or assign a model with more context. |
| A suggestion needs a missing service | Open **Sources & models**. Set it up in the named control. |

## See also

- [Architecture work](ARCHITECTURE_WORK.md)
- [Threads](USER_GUIDE.md#threads)
- [Automation](AUTOMATION.md)
- [Control modes](AUTHORITY.md)
