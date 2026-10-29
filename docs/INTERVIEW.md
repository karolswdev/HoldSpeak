# Interview

Use questions to develop working context and prepare a useful next step.
The current Desk supports this through ordinary Ask follow-ups and the Note-refinement Interview pane.
The separate structured Interview mode remains a retained Thread service with sectioned facts and suggestions.

The older Thread window's mode tabs, Section picker, and Context controls are parked.
The active Ask does not expose those controls.
This guide distinguishes the current user path from the retained programmatic contract.

## Before you start

Assign an engine for the job in [Models](MODELS.md).
Tool use depends on the engine and the allowed palette.
You can begin with a Note or a blank Project.
A Project with connected evidence gives the model more context.

| Path | Purpose | Current access |
| --- | --- | --- |
| Ask follow-ups | Explore a goal, reason over sources, and prepare work | Active Ask window |
| Note-refinement Interview pane | Refine one editable Note while preserving its original text | **Develop this thought** on the Note |
| Interview Thread mode | Retain sectioned facts, suggestions, choices, and promotions | Thread HTTP and Interview MCP services |

The Note-refinement pane and Interview Thread mode use different state contracts.
A question-based conversation does not automatically create structured Interview facts.

## Start a conversation

For the current Desk:

1. Open Ask, or use **Ask about this** on a Note or Project.
2. Select starting records through the toolbar scope menu when needed.
3. Describe one outcome and ask for one useful question at a time.
4. Send your answer as a follow-up.
5. Use **Save as note** when you want a separate working brief.

Example: “Help me prepare an architecture decision review from this Project. Identify the evidence gaps before drafting.”
Ask saves its exchanges as a Thread.
Its tools can retrieve additional permitted records beyond the starting About selection.
This flow does not activate the structured Interview mode.

A programmatic client can create that mode through `POST /api/threads`:

```json
{
  "title": "Architecture review context",
  "recipe_id": "hs-seed-mode-interview"
}
```

Send turns through `POST /api/threads/{thread_id}/turns` with a `text` field.
Read the returned Thread and Interview state before issuing revision-sensitive commands.
Use the authenticated hub API described in [API reference](API_REFERENCE.md).
The examples name API payloads and do not bypass authentication or model setup.

## Choose a section

The Interview service declares these sections in `holdspeak/services/interview_contracts.py`.
A section determines its purpose and tool palette.
Changing the section is a state command and does not itself run a model.

| Section | Purpose | Supported service work |
| --- | --- | --- |
| Goals | Define useful outcomes | Read Projects and save context |
| Projects | Inspect scope and source gaps | Read Projects and prepare supported Project setup |
| What matters | Identify meaningful changes | Read Project and decision evidence |
| Cadences | Explore repeated work | Read Cadence state and record a desired frequency |
| People | Continue confidential relationship work | Handoff to the protected People surface |
| Decision log | Recover rationale and review conditions | Read decision evidence |
| Delegation | Develop manual agent briefs | Read Project and Workbench context |
| Sources & models | Identify missing prerequisites | Read connection and provider state |

The service exposes section changes through `interview.change_section` and owner HTTP commands.
The active Ask window does not supply a Section picker.
Never put credentials in conversation text.

## Review saved context

`interview.get` returns the structured state for an Interview Thread.
A fact retains its source message, quote, classification, and current revision.
A user-stated fact differs from an inferred fact.
An inference is a model interpretation and needs review against its evidence.

Read the source before accepting the fact as working context.
Fact removal invalidates dependent suggestions.
A stale expected revision is refused rather than overwriting newer state.

## Review a suggestion

A suggestion records its basis, scope, prerequisites, feasibility, and uncertainty.
A model can suggest work beyond the currently installed adapters.
Such a suggestion remains an idea or manual recipe until a supported execution path exists.

Owner HTTP commands record dispositions such as keeping, deferring, or dismissing an idea.
They require a command id, expected revision, and supported event.
MCP model tools do not receive the owner's promotion or disposition authority.

A kept idea does not create an Automation, start an agent, or grant a permission.
Use the owning feature's configured operation for those actions.

## Keep a useful result

In ordinary Ask, the exchange is retained automatically.
Use **Save as note** for an editable output or **Add to note** when Ask originated from that Note.
Use **Make it a task** for a supported task result.
These writes are separate from structured Interview facts and suggestions.

The Thread API also offers its own keep operation.
Read [Agents and Threads](AGENTS_AND_THREADS.md) for the retained conversation contract.

## Promote a fact into a Note

The Interview service supports owner-controlled promotion through its HTTP command endpoint.
Promotion creates a linked canonical record from the source fact.
A client must supply the current revision and a new command identity.
Read promotion results through `GET /api/threads/{thread_id}/interview/promotions`.

The command endpoint accepts section, fact-removal, disposition, status, promotion, and promotion-revocation events.
The active Ask does not expose the older promotion panel.
The Interview MCP family does not add owner promotion tools.

Revoking a promotion link is distinct from deleting its source message or independently editing a kept Note.
Read the service's returned state before retrying a failed command.

## Resume

Use Ask's **Recent** list to resume an ordinary retained conversation.
A programmatic Interview client reads the existing Thread and `interview.get` state.
It should continue that Thread rather than create a duplicate for every turn.
A saved section, fact, or suggestion is not evidence that background work ran while the client was closed.

## Project setup limits

Interview's Projects section can prepare supported setup and inspect proposals.
Final configuration remains subject to the owner's configuration authority.
A tested proposal is distinct from a finalized Project.
Read [Project Rooms](PROJECT_ROOMS.md) for the current Desk setup path.

Cadences describes wanted recurring work.
Delegation develops a brief.
Neither section installs an arbitrary schedule or starts a coding agent by itself.

## Troubleshooting

| Problem | Action |
| --- | --- |
| There is no Interview tab | Use ordinary Ask or Note refinement. The older Thread mode UI is parked. |
| No structured facts appear after an Ask | Ordinary Ask is not automatically an Interview-mode turn. |
| A command is stale | Read the current Thread revision and review the intended change. |
| A suggestion never runs | Configure the supported Automation or handoff separately. |
| Project setup is incomplete | Continue through the current Project setup controls and inspect the resulting Project. |
| People is unavailable | Repair its key and access state in the protected People surface. |

## See also

- [Ask on the Desk](WEB_DESK.md#ask-about-your-work): current conversation controls.
- [Develop a thought](USER_GUIDE.md#develop-a-thought): the Note-refinement pane.
- [Architecture work](ARCHITECTURE_WORK.md): useful requests and completion checks.
- [Agents and Threads](AGENTS_AND_THREADS.md): retained service operations.
