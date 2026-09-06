# Models

Choose the engines that HoldSpeak uses for each capability.
The **Concierge** combines engine discovery and model assignments in one window.

## Configure an assignment set

1. Open **Settings > Models**.
2. Review the engines under **FOUND**.
3. Add an engine or download a supported preset if necessary.
4. Review the proposed engine for each group under **THE SET**.
5. Select **Use these** when the set is ready.

Each engine row identifies its host and current state.
A file on disk or a saved credential does not prove that the engine can run.
The set can include different engines for different kinds of work.

## Add or check an engine

Use **Add an engine...** for a keyless compatible endpoint.
Enter its base URL in the endpoint field.
Select **Check** to inspect it.

A catalog preset shows **Download** and its file size when the model is absent.
Selecting **Download** starts acquisition through the Model Library service.
Dependent assignments remain **WAITING** until the model is ready.

Cloud rows indicate whether a key is set.
Their **Check** control shows `1 TOKEN · $` before a paid probe.
The Concierge requires that explicit action for a paid cloud check.
Normal model work can also incur provider charges.

The current Concierge URL field does not collect a provider key.
For a keyed provider, use the owner Model Library API with its separate write-only secret field.
The [Model Library contract](MCP_SIDECAR.md#model-library) describes the underlying owner operations.
The [API surface](API_SURFACE.md) lists their HTTP routes.

For headless provisioning, `HOLDSPEAK_PROFILE_<ID>_KEY` remains an environment fallback for the identified model profile.
Do not place credentials in a Thread, Note, or shared model record.
A cloud row showing **KEY NOT SET** requires credential setup before a paid check can succeed.

## Understand readiness

| State | Meaning |
| --- | --- |
| **READY** | The engine passed the applicable readiness check. |
| **CHECKING** | A check is in progress. |
| **WAITING** | A download or prerequisite has not completed. |
| **KEY NOT SET** | The cloud engine needs a configured key. |
| **UNREACHABLE** | The engine did not respond as required. |
| **OFF** | You explicitly disabled a capability group. |

**Use these** requires every group to be ready or explicitly off.
A successful check establishes current availability. It does not guarantee future availability or model quality.

## Adjust individual capabilities

Select **Adjust** below the proposed set to open the capability table.
Each row shows its group, assignment, and engine host.
Use an individual assignment when the group choice does not suit that capability.

The service resolves the applicable assignment when work starts.
Changes to the model catalog or assignments affect later work.
They do not move a run that has already started.

## Model Library and assignments

**Model Library** names the underlying availability service.
It records models, deployment information, and readiness observations.
An **assignment** selects the compatible model list for a capability or eligible saved item.
These are separate service contracts beneath the Concierge.

The current **Settings > Models** and assignment entry points open the Concierge.
Older instructions that begin with separate Library and Assignments screens describe an earlier interface.
Use the [MCP reference](MCP_SIDECAR.md) or [API surface](API_SURFACE.md) for programmatic access to those services.

The assignment service supports complete ordered lists of one to four compatible models.
More specific assignment scope takes precedence over a group default.
A missing or incompatible assignment produces a named failure when work starts.

## Local runtimes and endpoints

Install the optional runtime that your chosen capability needs.
From an active source environment:

| Runtime | Command |
| --- | --- |
| GGUF through llama.cpp | `uv pip install -e '.[dictation-llama]'` |
| MLX text models on Apple Silicon | `uv pip install -e '.[dictation-mlx]'` |
| OpenAI-compatible dictation endpoint | `uv pip install -e '.[dictation-openai]'` |
| Optional meeting analysis dependencies | `uv pip install -e '.[meeting]'` |

For a package installation, use the equivalent `holdspeak[extra]` package.
See [Getting Started](GETTING_STARTED.md) for environment setup.

Capability requirements include supported input types, tool use, structured output, and context size.
A model that works for writing can still be unsuitable for Interview or meeting analysis.
An available MLX artifact also requires a capability path that supports its runtime.

The Concierge proposes local speech recognition.
Other groups can use a local engine, LAN endpoint, or selected cloud service.
Check each host before you apply the set.
Model requests can send source context to that host.

## Meeting output compatibility

Meeting intelligence expects structured fields for topics, action items, and a summary.
An endpoint must support the applicable request and response format.
A server-wide schema setting can conflict with the requested meeting schema.

For field definitions and compatibility behavior, see the [meeting output schema](internal/MEETING_OUTPUT_SCHEMA.md).
Use the returned error and Receipt when you diagnose a failed request.

## Troubleshooting

| Problem | Action |
| --- | --- |
| No engine is available | Add a compatible endpoint or download a supported preset. |
| A local model remains unavailable | Check the model file, optional runtime, and capability requirements. |
| An endpoint is unreachable | Check its address, required credential, and network path. Repeat **Check**. |
| An assignment cannot run | Use **Adjust** to select a compatible engine for that capability. |
| **Use these** remains disabled | Resolve each waiting group or explicitly set an unneeded group to off. |
| Tool results are unreliable | Review the sources and model output. A readiness check does not evaluate recommendation quality. |

## See also

- [Getting Started](GETTING_STARTED.md): install the required environment.
- [Interview](INTERVIEW.md): tool-based conversation and current quality limits.
- [Security & Privacy](SECURITY.md): model data and credential boundaries.
- [Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md): service routing and admission.
