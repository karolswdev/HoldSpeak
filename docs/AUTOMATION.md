# Automation

HoldSpeak provides several ways to prepare and execute work.
Choose the path that matches the trigger, required tools, and authority of your task.

An MCP tool exposes an operation to a client.
It does not by itself provide a scheduler, a running worker, or permission to execute an effect.
The client, runtime, model assignment, and operation policy still matter.

## Choose an execution path

| Path and guide | Trigger | Result |
| --- | --- | --- |
| [Interview](INTERVIEW.md) | You send an answer or select **Try draft** | Saved context, suggestions, manual drafts, and supported Project setup |
| [Thread tools](USER_GUIDE.md#threads) | A model requests a permitted tool during a turn | Tool execution within the Thread mode and its policy |
| [Agent or Ask](WEB_DESK.md) | You submit an instruction | A model result from selected context |
| [Sequence or Workflow](MCP_SIDECAR.md#sequence) | You start a configured run | Existing multi-step processing with run results |
| [Project Watches and Steward](PROJECT_ROOMS.md) | A supported source change and configured Project behavior | Project-scoped observation, proposals, and supported effects |
| [Heartbeat](USER_GUIDE.md#rhythm) | A configured unattended sweep | Evaluation of available work under the Heartbeat policy |
| [Cadence](CADENCE.md) | **run-now** or an enabled runtime loop | Review of unresolved work and preparation of next actions |
| [Scheduled recording](USER_GUIDE.md#schedule-a-recording) | A configured recording time | Meeting capture when the hub can run it |
| [Voice commands](VOICE_COMMANDS.md) | A keyword that you configured | The specific action mapped to that keyword |
| [Coder steering](USER_GUIDE.md#steer-a-session-from-the-desk) | You deliver text or an allowed key | Input to an identified live Coder pane |
| [External MCP client](MCP_SIDECAR.md) | Your client calls a tool | The operation exposed by the sidecar or Reach transport |

Cadence and Heartbeat are distinct systems.
An Interview cadence preference is context until you configure a supported recurring operation.
The remote [Reach Runner](REACH_RUNNER.md) also depends on an external scheduler when you want it to repeat.

## Complete a manual trial first

1. Identify one output and its intended use.
2. Select the source records for that output.
3. Configure the required model assignment.
4. Run the task once through the applicable surface.
5. Inspect the result and its Receipt.
6. Correct the source selection or instruction if necessary.

For architecture work, start with a [decision or agent brief](ARCHITECTURE_WORK.md).
Manual results help you determine the required scope before you configure unattended work.

## Configure recurring work

Use the owning feature's setup controls.
Each recurring task needs a supported trigger and an available runtime.

Before you rely on the task, verify:

- The event or time that starts it, including the time zone when applicable.
- The Project and source scope.
- The model assignment and its execution host.
- The output location or fixed external destination.
- The authority for each effect.
- The control that pauses or disables the task.
- A completed trial with a result and an execution record.

A saved instruction or suggestion is insufficient proof that recurring work exists.
Read the actual configuration and the relevant run history.
If the feature exposes a next trigger, check that value too.

## Understand authority

The default Control mode is **YOLO**.
Eligible operations can execute directly within configured scope.
**Normal** and **Secure** hold different classes of work for a decision or a scoped grant.
See [Control modes](AUTHORITY.md) for the exact operation families.

A Thread also has mode-specific tools and per-tool policies.
**Allow always** records a Thread tool policy. It does not remove the called service's own checks.
A tool can still refuse because its destination, credential, source scope, or runtime is invalid.

Content review, authorization, and execution are separate states.
An accepted proposal can remain unexecuted.
Use the execution result and Receipt to determine whether an effect occurred.

## Use an MCP client

The [MCP reference](MCP_SIDECAR.md) lists the tools, transports, resources, and deliberate exclusions.
Use its generated roster to verify that the required operation exists.
The Thread mode can expose a smaller selection than the server's full catalog.

The local sidecar opens the hub database through the product services.
It does not provide the Web runtime's live event connection or every live delivery path.
Reach provides a separate remote transport with scoped credentials.

For an external orchestrator, implement the control loop in that client:

1. Read the relevant state.
2. Select a supported operation.
3. Submit its required arguments.
4. Handle a refusal, question, or approval request.
5. Inspect the terminal result.
6. Read the affected record when the operation changes state.

Use documented operation identities when a service supports safe retries.
After an uncertain write result, inspect the affected record before you repeat the write.
An external client must not claim completion from a model's narrative alone.

## Current Interview boundary

Interview can prepare manual results and use its supported Project setup operations.
Its **Delegation** section prepares briefs. Its **Cadences** section explores recurring work.
Neither section installs a general agent assignment or an arbitrary schedule in the current increment.

A model can suggest combinations beyond the available adapters.
Treat such a suggestion as an idea until the required tools and execution path exist.
Model-generated dates, permissions, source coverage, and completion claims need verification.

## Troubleshooting

| Problem | Action |
| --- | --- |
| A saved idea never runs | Configure a supported trigger in its owning feature. **Keep idea** does not create one. |
| A configured task does not start | Check the enable state, Control mode, trigger, and runtime availability. |
| A tool is absent from a Thread | Check the selected mode and its permitted tool set. |
| A tool returns success but no external result appears | Distinguish proposal creation from execution. Inspect the execution state and destination record. |
| A remote run fails | Check the hub connection and the scoped credential. Use the runner's exit code. |
| A worker cannot continue | Resolve the named source, model, permission, or runtime prerequisite. |

## See also

- [Interview](INTERVIEW.md): manual discovery and supported setup.
- [Control modes](AUTHORITY.md): operation policy and grants.
- [MCP sidecar](MCP_SIDECAR.md): callable contracts and transport limits.
- [Cadence](CADENCE.md): unresolved work and recurring review.
