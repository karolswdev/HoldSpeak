# Models

Open **Settings > Engines** to make an engine available and assign it to an AI
job. An engine is an inference destination. A launched Claude Code, Codex, or
pi coding session is a different path with its own repository, worktree, and
brief. See [Coder integration](CODER_INTEGRATION.md).

## Choose an engine

1. Open **Settings > Engines**.
2. Select **Find on LAN**, **Add an engine**, or **Download a local model**.
3. Select the job and choose an engine.
4. Use **Default engine** when the job has no more specific assignment.

**Custom tasks** routes saved Agents and Workflow steps. **Background work**
routes automatic drafts, summaries, and memory work. These are capability
groups, not separate provider accounts.

The current **Engines** window names the job rows for the work they serve:

| Row | Capability group |
| --- | --- |
| **Speech to text** | `speech_recognition` |
| **Dictation clean-up** | `writing_dictation` |
| **Answers and notes** | `thoughts_notes` |
| **Meeting summaries** | `meetings` |
| **Custom tasks** | `agents_tools` |
| **Background work** | `background` |
| **Default engine** | `default` |

## Add or check an engine

Use **Add an engine** for an OpenAI-compatible endpoint and enter its **Server
address**. Use **Check** to inspect current readiness. A catalog model can
show **Download** when its local artifact is missing. An assignment that
depends on that artifact stays **WAITING** until the acquisition is ready.

Cloud rows show **KEY SET** or **NOT SET**. A paid probe requires the explicit
check control. A key belongs to the owner-only secret field and is not copied
into Notes, Threads, Receipts, or model payloads.

The environment fallback `HOLDSPEAK_PROFILE_<ID>_KEY` is for headless setup of a
known profile. It does not replace the owner secret boundary.

## Agent CLI engines

The supported CLI presets are Claude Code, Codex, pi, and Gemini CLI. A CLI
engine is an inference destination that starts one process for a prompt. It is
not a coding handoff and does not receive a repository task unless that is the
separate Coder flow.

The profile stores `base_url=cli:<preset>` and a `model` value. `default`
means the CLI's own default. The CLI uses its own sign-in; HoldSpeak does not
read or copy that sign-in. `HOLDSPEAK_CLI_ENGINES=off` disables all CLI-engine
discovery and runs.

Each preset has different controls:

| Preset | Process behavior | Tool boundary |
| --- | --- | --- |
| Claude Code | JSON output. HoldSpeak uses strict MCP configuration and no permission prompts. | Built-in tools are off for a plain run. A run with Desk tools receives HoldSpeak's scoped MCP server. Folder mode enables only `Read`, `Glob`, and `Grep`. |
| Codex | JSON event output. HoldSpeak disables unrelated configured MCP servers and feature paths. | The default is a read-only sandbox. With Desk tools, the run receives HoldSpeak's scoped MCP server. Folder mode keeps read-only shell access for that folder. |
| pi | `--print` one-shot text output, no session, extensions, skills, templates, context files, MCP, approval, and offline startup. | No Desk tools are wired into this CLI engine path yet. Its own provider config decides the endpoint. |
| Gemini CLI | JSON output with default approval mode, no extensions, and an allow-list naming no MCP server. | Shell, edit, and write tools that need approval stay out. Gemini's read-only tools can remain available; do not describe this preset as all tools off. |

The CLI subprocess runs with a bounded timeout and a temporary run context.
For Claude and Codex Desk-tool runs, HoldSpeak issues a run credential and
revokes it after the process exits. It never exposes the credential in argv or
the generated config file. A provider or CLI can still send the prompt to its
own cloud or LAN destination. Inspect the egress host in the engine row and
Receipt.

An Automation **spend_limit** applies per run where the chosen preset
enforces a provider limit. A preset that does not enforce one cannot be made
to report a provider cost by this setting.

## Understand readiness

| State | Meaning |
| --- | --- |
| **READY** | The engine passed its current readiness check. |
| **CHECKING** | A check is in progress. |
| **WAITING** | A download or prerequisite is incomplete. |
| **NOT SET** | A required cloud key is absent. |
| **UNREACHABLE** | The endpoint or runtime did not answer. |
| **OFF** | The capability group is explicitly disabled. |

Readiness is a point-in-time fact. It does not promise future availability,
provider success, or model quality.

## Try a job

Select **Try it** beside a job. A text trial uses a fixed sample. **Speech to
text** uses the microphone and **Stop**. The destination appears before the
trial. A successful call with no text reads **Completed · No text returned**.

A trial checks one capability. It does not test every Agent, Workflow, memory,
or tool operation, and a provider can charge for it.

## Assignments and frozen routes

An assignment selects one to four compatible models in order. More specific
scope wins over a group default. At run start, HoldSpeak freezes the ordered
route and deployment revisions. A later Settings change affects the next run
only. No hidden provider is substituted when all selected legs fail.

The Receipt records the frozen primary model, attempted legs, fallback reason,
host, boundary, and result. [Inference targets](INFERENCE_TARGETS.md) explains
the destination identity and readiness model.

## Repair states
The current **Engines** window resolves the applicable assignment when work
starts. A later catalog or assignment change affects later work only. It does
not move a run that has already started. The advanced setup surface exposes
**Model Library** and **Assignments** when you select **Set up my own** and
open **Table**.

| State | Meaning | Action |
| --- | --- | --- |
| **MODEL FILE MISSING** | A local assigned model is absent. | Select **Download**. |
| **ENDPOINT UNREACHABLE** | The assigned endpoint did not answer. | Check **Server address** and select **Check**. |
| **TOOL INCOMPATIBLE** | The engine cannot serve the capability. | Select **Choose** for that group. |
| **CREDENTIAL EXPIRED** | A required key or provider connection is missing. | Open **Connections** or the engine secret field. |

## Local runtimes and endpoints

Use the optional runtime required by the assigned capability:

| Runtime | Install |
| --- | --- |
| GGUF through llama.cpp | `uv pip install -e .` |
| MLX text models on Apple Silicon | `uv pip install -e '.[dictation-mlx]'` |
| OpenAI-compatible endpoint | `uv pip install -e .` |
| Meeting analysis extras | `uv pip install -e '.[meeting]'` |

The model must also satisfy the capability's input, tool, structured-output,
and context requirements. A model suitable for writing can be unsuitable for
Interview or meeting analysis.

## Meeting output compatibility

Meeting intelligence needs the applicable structured topic, action, and
summary fields. An endpoint can be reachable and still reject the requested
format. Read the returned error and Receipt.

## Troubleshooting

| Problem | Action |
| --- | --- |
| No engine is available | Add a compatible endpoint or download a supported local artifact. |
| CLI engine is missing | Check its executable on PATH and `HOLDSPEAK_CLI_ENGINES`. |
| CLI run has no Desk tools | Confirm the preset. pi and Gemini do not receive the M1 Desk-tool path. |
| Local model is unavailable | Check the file, runtime extra, and capability requirements. |
| Endpoint is unreachable | Check the address, key, and network route. |
| Assignment cannot run | Open **Settings > Engines**, read the named refusal, and choose a compatible engine or repair the named prerequisite. |
| Trial says **UNREACHABLE** | Read the Receipt for the attempted route and refusal. |
| Tool results are weak | Review sources and model output. Readiness does not measure quality. |

## See also

- [Inference targets](INFERENCE_TARGETS.md): destination identity and routing.
- [Execution destinations](EXECUTION_DESTINATIONS.md): frozen execution routes.
- [Coder integration](CODER_INTEGRATION.md): coding-agent launches.
- [Security and privacy](SECURITY.md): provider data boundaries.
