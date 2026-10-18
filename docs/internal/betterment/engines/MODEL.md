# Engines: the model today, and what is missing

The owner, 2026-10-17: "I thought we wanted to have simple integration with
various engines, e.g. OpenRouter, Claude Code CLI (like -p), Codex CLI, and so
on. How come those engines aren't assignable too? The local llama.cpp and the
OpenAI LAN endpoints are a good start, but so are other things."

This file is the map of the code as it is now. The input to `DESIGN.md` and
`RECIPE.md` for this feature. I read code only. I did not run a browser, the
hub or any test. A claim that needs a run to confirm says so.

The short answer to his question: **every engine HoldSpeak can run is one of
two things. It is a model file that it loads itself, or a server that speaks
the OpenAI chat API.** There is no third kind. A command-line agent (Claude
Code, Codex, pi, Gemini CLI) is not an engine kind, so nothing can assign it.
The code already knows how to run `claude -p` and `codex exec` once, safely,
for one narrow job. That code was never joined to the assignment system, and
no face calls it.

---

## 1. Engine kinds and assignment slots today

### The three layers

1. **A destination** (`InferenceTarget`): where the work runs and how the hub
   reaches it.[^target] It has a kind, a transport, a boundary (the egress
   label) and a readiness state.
2. **A model profile**: one model on one destination, with the claims that
   say which jobs it can serve (for example "this engine returns the meeting
   summary schema").[^profilebody] The Model Library writes these.
3. **An assignment**: an ordered list of model profiles (the first one, then
   its fallbacks) stored under one key.[^scope] The run reads the key, plans a
   route, and freezes the chosen deployment before it runs.[^engine-for-rev]

### Destination kinds

| Kind | What it is | Transport | Built as |
|---|---|---|---|
| `this_device` | A GGUF or MLX model file on this Mac (llama.cpp in the process). Also Whisper for speech. | `in_process` | `MeetingIntel(provider="local")`[^local] |
| `private_endpoint` | An OpenAI-compatible server on a private address (LAN llama.cpp, vLLM, Ollama, LM Studio). | `https` (or `http`) | `MeetingIntel(provider="cloud", base_url=…)`[^oai] |
| `external_service` | The same adapter, with a public host (OpenRouter, OpenAI). The host decides the kind, not the owner. | `https` | the same[^oai][^private] |
| `mesh_node` | Another HoldSpeak node that polls the hub for work. | `mesh_relay` | `MeshRelayIntel`[^mesh] |
| `paired_device` | The paired desktop app. The hub can list it but refuses to run work on it. | `paired_https` | refused: `inference_paired_device_execution_unsupported`[^paired] |
| `hub_default_cloud` | The old configured cloud leg, kept as a named destination. | `https` | `MeetingIntel(provider="cloud")`[^hubcloud] |

The boundary vocabulary is four words: `local`, `private_network`, `mesh`,
`cloud`.[^boundaries]

Under every kind except mesh and Whisper there is one class, `MeetingIntel`.
Each job reaches it through one method, `_chat_completion_text(messages, …)`,
which runs either llama.cpp or the OpenAI SDK.[^choke] That one method is the
seam a new engine kind plugs into (section 3).

### Assignment slots

A **job** is a registered capability. There are about 30 that an owner can
assign, in six groups and one default.[^caps]

| Group | Capabilities (the jobs) |
|---|---|
| Thoughts & notes | `thought.interview`, `ask.answer`, `chat.turn` (the Thread) |
| Writing & dictation | `speech.intent_classify`, `speech.rewrite`, `speech.target_classify` |
| Speech recognition | `speech.transcribe` (local only by boundary) |
| Meetings | `meeting.live_analysis`, `meeting.deferred_analysis` (the summary), `meeting.auto_title`, `meeting.bookmark_label`, meeting plugins |
| Agents & tools | `agent.plan`, `agent.tool_turn`, `agent.code`, `workbench.item`, `recipe.run`, `sequence.step`, `workflow.node`, `voice.reference_resolve`, `project.update_draft`, `project.brief_prepare`, `project_doc.suggest_update` |
| Background | `background.rails_summary`, `background.cadence_draft`, `decision.promotion_draft`, `delivery.pr_review_draft`, `calendar.snapshot_extract`, `memory.embed`, `memory.extract`, `memory.consolidate`, `memory.page` |

An assignment key has one of five forms. A run reads them in this order and
takes the first one that is set:[^resolve]

```
invocation:<id>:capability:<cap>       one run only
subject:<kind>:<id>:capability:<cap>   one Thought, Workbench, agent, recipe or project
capability:<cap>                       one job everywhere
group:<group>                          a group of jobs
global                                 the Default for AI work
```

### Diagram

```
   WHAT HOLDSPEAK DOES                      WHAT HE HAS
   (capabilities)                           (model profiles -> destinations)

   meeting.deferred_analysis --+            +-- profile "Qwen 4B"  -> this_device   (llama.cpp, in process)
   ask.answer -----------------+            +-- profile "LAN qwen" -> private_endpoint (OpenAI API over http)
   chat.turn ------------------+-- key -----+-- profile "OR model" -> external_service (OpenAI API, openrouter.ai)
   workbench.item -------------+  (chain:   +-- profile "node-2"   -> mesh_node     (relay queue)
   recipe.run -----------------+   first,   +-- (paired_device: listed, never runs)
   ...                             fallback)
                                    |
   lookup order:                    v
   invocation > subject >     route plan freezes ONE deployment revision
   capability > group >             |
   global                           v
                              build_intel_for_revision()
                                    |
                     +--------------+---------------+
                     v              v               v
               MeetingIntel    MeetingIntel     MeshRelayIntel
               (llama.cpp)     (OpenAI SDK)
                                    ^
                                    |
                     NOT HERE: claude -p / codex exec / pi -p / gemini -p

   SEPARATE, NOT JOINED:
     Coding agents (claude, codex, pi) in tmux panes       factory_launch.py
     pi READS the agent.code assignment (it consumes an engine)  pi_launch.py
     agent_summarizer.py runs claude -p / codex exec once -> no face calls it
```

---

## 2. What he can assign now, versus what he asked for

"Supported" means: he can add it, wire it to a job, and the job runs on it.
"Partly" means it runs, but something on the way breaks or confuses.

| Engine | State | Why |
|---|---|---|
| llama.cpp on this Mac (GGUF file) | **Supported** | `this_device`. Catalog presets download from huggingface.co.[^presetloop] |
| llama.cpp / vLLM on the LAN | **Supported** | `private_endpoint`, OpenAI API. "Find on LAN" or "Add an engine". |
| Ollama | **Supported** | The hub scans 127.0.0.1:11434 and offers it as FOUND, with "Use it".[^ports] |
| LM Studio | **Supported** | The same scan, port 1234.[^ports] |
| Another HoldSpeak node | **Supported** | `mesh_node`. |
| Paired desktop app | **Missing** | Listed, then refused at run time.[^paired] |
| OpenRouter | **Partly** | The adapter works (OpenRouter speaks the OpenAI API). Six signed OpenRouter presets ship in the catalog.[^orpresets] The service has a hosted connect verb.[^hosted] But the live face never shows the presets, and its only add path takes the first model in alphabetical order. See "OpenRouter today" below. |
| OpenAI API | **Partly** | The same path as OpenRouter: paste `https://api.openai.com/v1` and a key. The same first-model problem. On a list that holds non-chat models, the first id may not be a chat model. A run would confirm this. |
| Anthropic API | **Missing** | Blocked by name. The family `anthropic` is refused before anything is stored, and the host `api.anthropic.com` shows NOT SUPPORTED YET.[^anthropic] Anthropic does publish an OpenAI-compatible endpoint. Whether that endpoint passes the hub's `/models` check with a Bearer key is **unknown**. |
| Gemini API | **Unknown** | Not named anywhere in the code. Google publishes an OpenAI-compatible URL. It would go through "Add an engine" like OpenAI, with the same first-model problem. Not verified. |
| Claude Code CLI (`claude -p`) | **Missing** | There is no CLI engine kind. `claude -p` runs in one place only: `agent_summarizer.py`, which summarizes a captured coding-agent session. Its route has no caller on the web face.[^summarizer] |
| Codex CLI (`codex exec`) | **Missing** | The same as Claude Code. A safe argv already exists: `codex exec --sandbox read-only --ephemeral -`.[^summarizer] |
| pi (`pi -p`) | **Missing** (as an engine) | pi is a coding agent that *consumes* an engine: it runs on the `agent.code` assignment, and that engine must be an OpenAI-compatible server.[^pi] It cannot *be* an engine for a job. Its one-shot flags are not in the code. Confirm them before we build. |
| Gemini CLI | **Missing** | Not in the code at all. Its one-shot flag (`-p`) is not verified here. |

### OpenRouter today, press by press (from the code, not from a run)

1. Open Settings (⌃4), then the Engines module. (2 presses)
2. Press **Add an engine**. One row opens: *Server address*, *Key*, *MY
   SERVER*, *Check*, *Add*.[^addrow] (1 press)
3. Type `https://openrouter.ai/api/v1` and paste the key. (He must know the
   URL; nothing on the face says "OpenRouter".)
4. Press **Check**. The hub calls `GET /models` and sorts the ids
   alphabetically.[^sorted] (1 press)
5. The face takes `models[0]`, the alphabetically first of several hundred
   OpenRouter ids, and shows it as READY. There is no model picker.[^first]
6. Press **Add**. (1 press)
7. Drag the engine onto a job. (1 drag)

That is about 6 presses and a drag, and the result is a model he did not
choose. Three more breaks:

- **One engine for each host.** The profile id comes from host and port
  (`engine-openrouter-ai`).[^profileid] A second Add for another OpenRouter
  model reuses that id, so it seems to change the first engine's model and
  not add a second one. A run would confirm this.
- **The presets are invisible.** The detector skips every catalog entry that
  is not a local download.[^presetloop] The face that could connect a hosted
  preset (`ModelLibraryCore`, "Connect") is inside the parked FrontDoor and
  the parked `settingsModels`.[^parkedface]
- **An agent can do it in one call.** The MCP tool
  `model_library.connect_hosted_model` takes `provider_family: "openrouter"`,
  a model id and the key.[^mcphosted] The face cannot.

---

## 3. The smallest honest architecture for a "CLI engine" kind

### The concept

A CLI engine is a destination whose transport is **a process on this Mac**.
HoldSpeak gives it a prompt and reads text back. It is a peer of
`private_endpoint`. It is not a coding agent: it has no pane, no tools, and
no write access.

```
kind       cli_engine
transport  subprocess
engine     cli_v1
boundary   cloud (the CLI calls its vendor), or private_network when the
           owner marks MY SERVER (pi on his LAN model)
egress     the vendor host, from the preset: API.ANTHROPIC.COM, API.OPENAI.COM, ...
```

### The contract

- **Command**: a closed preset table in code. No free shell string in the
  first slices. Each preset holds argv, how the prompt goes in (stdin or an
  argument), how to read the output, the egress host, and a cost flag.
- **Prompt**: the system and user messages, put together as one text, on
  stdin. stdin avoids argv length limits and keeps the prompt out of `ps`.
- **Output**: text on stdout. For `--output-format json`, the existing
  `_extract_summary_text` reads `result` / `text` / `content`.[^extract]
- **Timeout**: one per preset, kept inside the runner's deadline
  (`deadline_at`).[^deadline] Kill the process when time runs out or on
  cancel.
- **Labels**: the boundary and host for the egress chip, plus a COST token
  for presets that bill by token (Claude Code has `--max-budget-usd`; Codex
  has no such flag in the code).

The presets to start with. The first two already exist and are safety
checked:[^summarizer]

| Preset | argv (prompt on stdin) | Egress |
|---|---|---|
| `claude` | `claude -p --tools "" --no-session-persistence --output-format json --max-budget-usd 0.10 [--model M]` | api.anthropic.com |
| `codex` | `codex exec --sandbox read-only --ephemeral - [-m M]` | api.openai.com (or the provider in his Codex config: **unknown**) |
| `pi` | `pi -p …`: **flags to verify** | the provider in pi's own config; the owner marks it |
| `gemini` | `gemini -p …`: **flags to verify** | generativelanguage.googleapis.com |

`validate_summarizer_command` already refuses the dangerous flags
(`--dangerously-skip-permissions`, `--sandbox danger-full-access`,
`bypassPermissions`).[^validate] Use it again; do not write a second one.

### Why it fits with little new code

- **One method to override.** `CliEngine(MeetingIntel)` overrides
  `_ensure_model_loaded` (check that the executable is on PATH) and
  `_chat_completion_text` (run the process). `run_prompt`,
  `run_prompt_messages` and `analyze` (the meeting summary) then work with no
  other change, because each one calls that method.[^choke]
- **Streaming is optional.** The prompt adapter falls back to one text block
  when an engine has no `run_prompt_stream`.[^streamfallback] `MeetingIntel`
  has that method, so `CliEngine` must override it to yield the whole answer
  as one delta.
- **Typed jobs check their own output.** Meeting analysis, Thought interview
  and dictation intent check the result against their schema before a run
  succeeds.[^enforced] A CLI cannot take `response_format`, so `CliEngine`
  adds the schema to the prompt as an instruction ("reply with JSON only,
  matching this schema"). A bad answer becomes `invalid_typed_output`, and
  the chain goes on to its fallback.
- **The profile row needs no schema change.** Store `kind="cliCommand"`, the
  preset in `base_url` as `cli:claude`, and the model name in `model`. Only
  the `openAICompatible` branch parses `base_url` as a URL.
- **Readiness already exists.** First run already reads INSTALLED and SIGNED
  IN for claude and codex.[^signedin] Use the same reads for the engine lamp.

### Files to change

The mapping from profile kind to (kind, engine, boundary) is copied in five
places. Each copy needs the new kind:

1. `holdspeak/intel/cli_engine.py` (new): `CliEngine`, the preset table, the
   subprocess call (timeout, kill, empty temp cwd, closed stdin). Move or
   import `build_summarizer_command`, `validate_summarizer_command` and
   `_extract_summary_text` from `holdspeak/agent_summarizer.py`.
2. `holdspeak/inference_targets.py`: `cliCommand` in
   `SUPPORTED_PROFILE_KINDS` (line 50). A branch in `target_from_profile`
   (lines 405–489), with readiness from PATH and sign-in. An entry in the
   `_engine_for_revision` map (lines 784–801).
3. `holdspeak/intel/providers.py`: a `cliCommand` branch in `_profile_engine`
   (line 812).
4. `holdspeak/services/inference_route_plan_service.py`: the v1 identity
   adapter (lines 1609–1625).
5. `holdspeak/services/model_profile_service.py`: provider family
   `cli_agent`, runtime family `cli_v1` (lines 297–310 and
   `_LEGACY_RUNTIME_FAMILIES`, line 67).
6. `holdspeak/inference_locality.py` (line 136) and
   `holdspeak/services/profile_service.py` (line 170): the lamp and the
   kind map.
7. `holdspeak/services/model_library_service.py`: `cli_agent` in
   `_PROVIDER_FAMILIES` (line 41) and `_provider_runtime_family` (line 619),
   and a `connect_cli_engine(principal, draft)` verb next to
   `connect_hosted_model`.
8. `holdspeak/mcp/families/model_library.py` and
   `holdspeak/web/routes/model_library.py`: the matching MCP tool and route.
9. `holdspeak/services/concierge_service.py`: in `detect`, list each
   installed, signed-in CLI as a FOUND engine (like the loopback scan), so
   the face's existing **Use it** adds it in one press.
10. `web/src/features/runson/model.ts`, `useRunsOn.ts`, `RunsOnCore.tsx`: a
    CLI emblem, the egress chip from the preset host, and Use it for a found
    CLI.

Keep two jobs off this kind. **Dictation** is a hot path with a latency cap,
and its own runtime refuses a revision it cannot bind.[^dictation] **Speech
transcription** is local by boundary. The assignment compatibility check
must refuse `speech.*` for `cli_v1`. Without that refusal, `speech.rewrite`
(which has no structured claim) would accept the wire and then fail at run
time.

### Slice order (for RECIPE.md)

1. Backend kind and engine, plus the MCP tool. An agent can then connect
   `claude` and assign it to `meeting.deferred_analysis`. Proof: a hub test
   with a fake `claude` script on PATH in the scratch HOME.
2. The face: installed CLIs appear as FOUND, and Use it adds one in a press.
3. OpenRouter repair (not a CLI, but he asked): a model picker on Check, the
   hosted presets shown as FOUND, one profile for each model and not for each
   host.

---

## 4. The face today for choosing an engine

**Where it is.** Settings (⌃4) → **Engines** opens `RunsOnCore`.[^settings]
The same face is called "Runs on" (its own title), "Engines" (the Settings
row), `/models` (the path) and "Concierge" (the code and the old
window).[^names] That is four names for one place.

**What he sees.**

- A head: "N engines" or "No engine yet", with READY / LIMITED / BROKEN /
  WAITING counts, "THIS MAC · M-SERIES · 64 GB", and "Checked hh:mm".
- Two verbs: **Find on LAN** and **Add an engine**.
- A FOUND list (loopback and LAN engines not yet in the library) with **Use
  it**.
- The switchboard. On the left, "What HoldSpeak does": six group jobs and
  the Default. On the right, "What you have": engine plates. He drags a wire
  from a job to an engine. "Uses default engine" shows on a job that
  inherits. **Try it** runs a sample on a job.
- A fold, **Download a local model**, with the catalog presets and Meaning
  search.
- A foot: the receipt ("PATCHED …"), the egress chip of the last engine,
  **Undo**.[^addrow]

**Where it confuses him.**

1. **"Add an engine" means "add a server".** The row asks for a *Server
   address* (`http://<host>:<port>/v1`). A service (OpenRouter, OpenAI) is
   only a URL that he must already know. A program (Claude Code, Codex) has
   no way in at all. This is the gap he named.
2. **He cannot pick the model.** Check takes the first model in alphabetical
   order and Add saves it.[^first]
3. **One plate for each host.** A second model from the same host seems to
   replace the first one (section 2).
4. **His agents live in another room.** First run has an Agents card for
   Claude Code, Codex and pi, with INSTALLED and SIGNED IN lamps and the
   host chips API.ANTHROPIC.COM, API.OPENAI.COM and LAN.[^agentscard] None
   of them show under "What you have". The product knows they are installed
   and signed in, but it does not offer them as engines.
5. **Anthropic is a dead end.** It shows NOT SUPPORTED YET, a state with no
   verb.[^anthropic]
6. **Only groups are wired.** The face writes only `global` or
   `group:<id>`.[^scopefor] The service and MCP can set a single job (for
   example "summaries on OpenRouter, everything else on the LAN") or a
   single Workbench. The face lists the jobs under Details only. Meetings has
   one exception for the summary job.
7. **A typed key is not kept unless he presses Add.** The key goes with one
   Check, and Add stores it only if the Key field still holds it.

---

## 5. Risks

**Egress labelling.** A CLI runs on this Mac, but its prompt goes to its
vendor. The plate and the egress chip must never say THIS DEVICE. The label
comes from the preset (`API.ANTHROPIC.COM`). For pi it comes from the owner,
because pi's own config decides the provider. For Codex, the host depends on
his Codex config (**unknown**). Show the preset host, and show "per Codex
config" when we cannot read it. Meeting transcripts and People notes go
where the chip says. That is the same rule as for any cloud endpoint, and
the chip must be there before the first wire.

**Secrets.** Endpoint keys are in a 0600 JSON file,
`~/.holdspeak/profile-custody/profile-keys.json`. They are not in the
Keychain. An environment variable with the slot's name is the
fallback.[^keystore] A CLI engine needs no key from HoldSpeak: each CLI uses
its own sign-in (its config folder, or the Keychain for Claude Code).
HoldSpeak must not read, copy or pass those credentials. It runs the CLI as
the owner, with his HOME. **Defect found while reading (not verified by a
run):** `/api/setup/discover-models` falls back to `OPENAI_API_KEY` from the
hub's environment when no key is typed, and it sends that key as a Bearer
header to *whatever address was typed*.[^openaikey] An address typed by
mistake receives his OpenAI key. That belongs in its own small fix.

**Streaming.** The first slice has none. A Thread answer on a CLI engine
arrives as one block. Claude Code has a streaming JSON output that can come
later. The prompt adapter already accepts an engine without streaming.

**Long runs and cancel.** The existing summarizer uses a 20 s
timeout.[^summarizer] A meeting summary through `claude -p` can take longer,
and a Node CLI takes about one to two seconds to start (an estimate, not
measured). Set the timeout for each preset, inside the runner deadline.
Today both adapters answer `cancel()` with `not_supported`.[^cancel] A
subprocess *can* be killed, so `CliEngine` should kill it when the runner
cancels. The background jobs (memory extraction, rails summaries) can fire
many calls. Each call is a new process, and on a subscription plan each call
counts against his limits. Do not put `memory.*` on a CLI engine by default.

**Tools and side effects.** An agent CLI can edit files and run commands.
The presets turn tools off (`--tools ""`) or use a read-only sandbox, and
`validate_summarizer_command` refuses the bypass flags.[^validate] Run the
process in an empty temp folder, not in a repository. Do not add more guards
than these (Tenet 1: no over-engineering for safety).

**CLI sign-in state.** A CLI that is not signed in may wait for an
interactive login. Close stdin, keep the timeout, and show NOT SIGNED IN on
the plate. When the hub cannot tell, the existing reads answer
SIGN-IN UNKNOWN and not NO.[^signedin] Treat UNKNOWN as "try once".

**Tests never touch the real HOME.** A test must never run the owner's real
`claude` or `codex`: they would use his real sign-in and bill him. Tests put
a fake `claude` script on PATH inside the scratch HOME. Rigs need a switch,
default off, so that a lane machine's installed CLIs do not appear as FOUND
(`HOLDSPEAK_CLI_ENGINES=off`). It works like
`HOLDSPEAK_LOOPBACK_ENGINE_PORTS` set to empty in the graph-walk
rig.[^rigswitch] The CLAUDE.md rule "a new read of machine state needs a
switch" covers this case.

### Which work honours an assignment

| Work | Honours an assignment? | Note |
|---|---|---|
| Meeting summary, live analysis, title, bookmark | Yes | `intel_queue.py:226`, `:256`, `:586` |
| Dictation intent and rewrite | Yes, when assigned | Otherwise the old `dictation.runtime.profile_id` path. Only local, endpoint or mesh engines can bind.[^dictation] |
| Speech transcription | Local only | the boundary is fixed to `local` |
| Ask | Yes, plus a per-call target | `ask_service.py:186` |
| Thought interview | Yes | plus the old `thoughts.inference_target_id` setting (`inference_targets.py:627`) |
| Thread (desk chat) | Yes (`chat.turn`) | `thread_service.py:2099` |
| Draft update | Yes | `project_update_service.py:1831` |
| Preparation brief | Yes | `preparation_brief_service.py:790` |
| Workbench runs | Yes, and for each Workbench | `workbench_runner.py:329`, `schedule_delegation.py:24` |
| Recipes, sequences, workflows | Yes | `recipe_service.py:147`, `sequence_workflow_service.py:451`, `:720` |
| Memory, cadence, decisions, PR review, rails, calendar snapshot | Yes | the call sites name their capability |
| Monday brief | No model call found | `monday_brief_service.py` reads the assignment heads only (`:2343`). Whether a model writes any part of it: **unknown**. |
| Coding-agent session summary | **Hard-wired** to claude or codex | `agent_summarizer.py`. Outside the assignment system, and no face calls it. |
| Coding agents (Claude Code, Codex) | Not assignable | Each one runs on its own CLI model. The launch profile picks the harness.[^harness] |
| pi | Reads `agent.code` | It consumes an engine; it is not one.[^pi] |

---

[^target]: `holdspeak/inference_targets.py:123-160` (`InferenceTarget`); kinds at `:405-489`.
[^profilebody]: `holdspeak/services/model_library_service.py:439-470` (`_profile_body`, claims).
[^scope]: `holdspeak/services/inference_assignment_service.py:1710-1770` (`_scope`).
[^engine-for-rev]: `holdspeak/inference_targets.py:722-805` (`build_intel_for_revision`, `_engine_for_revision`).
[^local]: `holdspeak/intel/providers.py:849-862`; `holdspeak/inference_targets.py:405-426`.
[^oai]: `holdspeak/intel/providers.py:833-848`; `holdspeak/inference_targets.py:462-478`.
[^private]: `holdspeak/inference_targets.py:55-67` (`_private_endpoint`).
[^mesh]: `holdspeak/intel/providers.py:826-832`; `holdspeak/inference_targets.py:440-461`.
[^paired]: `holdspeak/inference_targets.py:32`, `:802-805`.
[^hubcloud]: `holdspeak/inference_targets.py:28`, `:764-770`.
[^boundaries]: `holdspeak/inference_capabilities.py:27`.
[^choke]: `holdspeak/intel/engine.py:184` (`MeetingIntel`), `:390` (`_chat_completion_text`), `:835` (`run_prompt`), `:903-936` (`_analyze_once`).
[^caps]: `holdspeak/inference_capabilities.py:1066-1157` (`builtin_capability_definitions`).
[^resolve]: `holdspeak/services/inference_assignment_service.py:2204-2240` (`_resolve`).
[^presetloop]: `holdspeak/services/concierge_service.py:722-746`; the skip is at `:724`.
[^ports]: `holdspeak/services/inference_default_service.py:69-74`.
[^orpresets]: `holdspeak/inference_setup_catalog.py:114-245`.
[^hosted]: `holdspeak/services/model_library_service.py:213-222`, `:381`.
[^anthropic]: `holdspeak/services/model_library_service.py:235-243`, `:619-637`; `holdspeak/services/concierge_service.py:56`.
[^summarizer]: `holdspeak/agent_summarizer.py:19` (20 s timeout), `:133-161` (the argv), `:221-286` (the run); the route is `holdspeak/web/routes/dictation/agent.py:141-195`; `grep agent-context/summarize web/src` finds nothing.
[^pi]: `holdspeak/delivery/pi_launch.py:1-10`, `:46`.
[^addrow]: `web/src/features/runson/RunsOnCore.tsx:78-160` (the add row), `:408-428` (the two verbs), `:502-534` (the foot).
[^sorted]: `holdspeak/setup_runtime.py:161-168`.
[^first]: `web/src/features/runson/useRunsOn.ts:778-797` (`setAddModel(answer.models[0])` at `:789`).
[^profileid]: `web/src/features/concierge/endpointDraft.ts:56-62`, `:83`; `web/src/features/runson/useRunsOn.ts:804-812`.
[^parkedface]: `web/src/pages/cores/frontDoor.tsx:509`; `web/src/pages/cores/SettingsCore.tsx:58-61` (the import is commented out); `web/src/pages/cores/settingsModels.tsx:4`.
[^mcphosted]: `holdspeak/mcp/families/model_library.py:54-64`.
[^extract]: `holdspeak/agent_summarizer.py:289-310`.
[^deadline]: `holdspeak/kernel/inference_invoke.py:14-19`, `:75-77`.
[^validate]: `holdspeak/agent_summarizer.py:164-190`.
[^streamfallback]: `holdspeak/kernel/prompt_adapter.py:103-134`.
[^enforced]: `holdspeak/services/model_library_service.py:72-90`.
[^signedin]: `holdspeak/services/onboarding_service.py:696-773`; `web/src/desk/firstrun/AgentsCard.tsx:32-40`.
[^dictation]: `holdspeak/plugins/dictation/assembly.py:257-305`; `holdspeak/speech_session/session.py:297-327`; `holdspeak/speech_session/revision_target.py:36-42`.
[^settings]: `web/src/pages/cores/SettingsCore.tsx:253`, `:2452-2454`.
[^names]: `web/src/desk/applications.ts:189-191`, `:356-368`; `web/src/features/runson/RunsOnCore.tsx:170`.
[^agentscard]: `web/src/desk/firstrun/agentsStep.ts:18`, `:45-50`.
[^scopefor]: `web/src/features/runson/useRunsOn.ts:152-154`.
[^keystore]: `holdspeak/profile_key_store.py:30`, `:178-186`.
[^openaikey]: `holdspeak/web/routes/setup.py:247-266`.
[^cancel]: `holdspeak/kernel/prompt_adapter.py:36-40`; `holdspeak/services/inference_semantic_adapters.py:124-125`.
[^rigswitch]: `holdspeak/services/inference_default_service.py:77-80`.
[^harness]: `holdspeak/delivery/factory_launch.py:67-80`.
