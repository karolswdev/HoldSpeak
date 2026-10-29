# Automation

An Automation is one instruction, a source scope, an execution choice, and a
result destination. It can run when you press **Run now**, on a schedule, or
after a supported event. A saved suggestion is not an enabled Automation.

## Choose an execution path

Use the path that owns your trigger and result:

| Path | Starts when | Produces |
| --- | --- | --- |
| **Run now** | You press **Run now** | One run record and one result |
| Schedule | The hub reaches the saved time | One run record for that occurrence |
| Event | A supported source event matches | One run record for that event |
| Agent handoff | The Automation's **Do** is **Hand to agent** | A brief and a coding-agent launch |
| Sequence or Workflow | You start a saved sequence | Parent and child receipts |
| Project Watch and Steward | A configured Project source changes | Observation, review, and permitted follow-up |
| Heartbeat | A supported unattended sweep runs | A Heartbeat evaluation |
| Cadence | **run-now** or the enabled Cadence loop | Open-loop review and prepared next actions |

The local MCP sidecar and Reach are transports. They do not add a scheduler or
authority. An external scheduler is required if you repeat a Reach Runner job.

The same systems can be reached through these supported paths:

| Path | Starts when | Produces |
| --- | --- | --- |
| [Interview](INTERVIEW.md) | You answer or select **Try draft** | Saved context, suggestions, manual drafts, and supported Project setup |
| [Thread tools](USER_GUIDE.md#ask) | A model requests a permitted tool during a turn | Tool execution within the Thread mode and its policy |
| [Agent or Ask](WEB_DESK.md) | You submit an instruction | A model result from selected context |
| [Sequence or Workflow](MCP_SIDECAR.md#sequence) | You start a configured run | Parent and child receipts |
| [Project Watches and Steward](PROJECT_ROOMS.md) | A supported source change matches configured Project behavior | Project-scoped observation, proposals, and supported effects |
| [Heartbeat](USER_GUIDE.md#notices-and-the-heartbeat) | A configured unattended sweep runs | Evaluation of available work under the Heartbeat policy |
| [Scheduled recording](USER_GUIDE.md#schedule-a-recording) | A configured recording time arrives | Meeting capture when the hub can run it |
| [Voice commands](VOICE_COMMANDS.md) | A configured keyword matches | The action mapped to that keyword |
| [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk) | You deliver text or an allowed key | Input to an identified live Coder pane |
| [External MCP client](MCP_SIDECAR.md) | Your client calls a tool | The operation exposed by the sidecar or Reach transport |

Cadence and Heartbeat are distinct systems. An Interview cadence preference is
context until you configure a supported recurring operation. Reach Runner also
needs an external scheduler when you want it to repeat.

## Complete a manual trial first

1. State the result you need.
2. Choose the records in **About**.
3. Choose **Do**: run an instruction, or hand the work to an agent.
4. Choose **With**: an available engine or installed agent profile.
5. Choose **Put it in**.
6. Press **Run now** and inspect the result and Receipt.

For an agent handoff, also choose an optional **Review by** agent. The review
choice is part of the launch terms. It does not make the reviewer a second
builder or grant it owner authority.

## Configure recurring work

The Automation sentence has these words:

| Word | Meaning |
| --- | --- |
| **Do** | `run` executes the instruction. `hand_to_agent` creates a coding-agent handoff. |
| **About** | Explicit records, supported relative sets, People names, or a repository Folder. |
| **When** | Manual, a schedule, or a supported event. |
| **With** | An engine profile for `run`, or an installed agent profile for `hand_to_agent`. |
| **Review by** | An optional installed reviewer for an agent handoff. |
| **Put it in** | **My Inbox**, **Needs you**, **Today**, or a saved destination that prepares a send. |

The builder writes each choice when you press it. It does not show the stored
cron expression. If a schedule has no usable engine or agent, HoldSpeak keeps
the schedule saved but off and names the missing **With** choice.

Before you rely on a recurring task, verify:

- the trigger and its local time zone;
- the Project and source scope;
- the execution host, model or agent profile;
- the output target and any required destination;
- the Control mode and effect authority;
- the pause or disable control;
- one completed manual run with a Receipt.

Relative source sets are expanded when the run starts. Current starter sets
include this week's meetings, notes, and decisions, Jira bugs labelled
`agent-ok`, and GitHub review requests. A source that cannot be read is not
silently treated as current evidence.

## Understand authority

The default Control mode is **YOLO**. Eligible work runs within its configured
scope. **Normal** and **Secure** hold operation classes that need an owner
decision or a scoped grant. See [Control mode](SECURITY.md#control-mode).

An Automation run freezes its route before execution. A later engine or
assignment change affects the next run. It does not move a run already in
progress.

Content review, authorization, and execution are separate states. A prepared
destination result waits for your **Send** press. An accepted proposal does
not prove that an external effect occurred. Read the operation state and
Receipt.

## Results and persistence

An instruction Automation makes one occurrence item per run. The result keeps
the rendered text, sources used, writes, prepared actions, model and boundary,
and any reported CLI cost.

The output target controls where HoldSpeak files the result:

- **My Inbox** creates a Note with a link to the run.
- **Needs you** creates a Door item due today.
- **Today** keeps the newest result in Today's Prepared block.
- A saved destination calls `channel.prepare`. You inspect it and press
  **Send** before it leaves the machine.

Automation memory is optional and separate from Desk memory. It informs later
runs and never authorizes them. A run with no instruction keeps the older
queue-style behavior.

## Use an MCP client

Read [MCP sidecar](MCP_SIDECAR.md) for the generated tool roster, transport,
resources, and deliberate exclusions. An external client should:

1. read the current Automation and source state;
2. select a registered operation;
3. submit an idempotency key when the operation supports one;
4. handle a refusal, question, or approval request;
5. inspect the terminal result and Receipt;
6. read the affected record after a state change.

After an uncertain write, inspect the record before retrying. Do not claim
completion from a model's narrative alone.

## Interview limits

Interview can prepare manual context, suggestions, and supported Project setup.
Its **Delegation** section prepares a brief. Its **Cadences** section records
context. Neither section installs an arbitrary schedule or agent assignment.

Treat model-generated dates, permissions, source coverage, and completion
claims as unverified until the actual configuration and Receipt agree.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A saved idea never runs | Configure a supported **When** choice in its owning feature. **Keep idea** does not create a trigger. |
| A schedule is saved but off | Choose a ready engine or agent in **With**, then enable the schedule. |
| **Run now** fails | Read the named source, assignment, runtime, or authority refusal. |
| An agent handoff is queued | The configured `agents.working_at_once` slots are full. Leave it queued or lower active work. |
| The result is missing | Read the run state and Receipt. A canceled or indeterminate run needs inspection before retry. |
| A destination has no external result | It may be prepared only. Open the result and press **Send**. |
| A remote run fails | Check the hub, credential, palette, and external scheduler. |

## See also

- [Coder integration](CODER_INTEGRATION.md): coding-agent launches and reviews.
- [Models](MODELS.md): engine readiness and assignments.
- [Execution destinations](EXECUTION_DESTINATIONS.md): frozen routes.
- [MCP sidecar](MCP_SIDECAR.md): callable contracts and transport limits.
- [Cadence](CADENCE.md): unresolved work and recurring review.
