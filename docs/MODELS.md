# Models: bring your own

HoldSpeak does **not** ship model weights, and it does not require one specific
model. The LLM layer is deliberately model-agnostic: pick whatever runs well on
your hardware and point HoldSpeak at it.

> **Model names are a moving target.** The specific models suggested below are
> *current picks*, refreshed periodically; they are **suggestions, not
> requirements**. If a name here looks dated, that's expected: swap in whatever
> the current good small/mid instruct model is. The contract is the *interface*
> (GGUF / MLX / OpenAI-compatible), not any single checkpoint.

There are two model roles, configured independently:

| Role | What it does | Config keys |
|------|--------------|-------------|
| **Transcription** (Whisper) | speech → text | `model.name`, `model.backend` |
| **LLM** | dictation block-classification + KB enrichment, meeting intel, Ask, and explicit Thought refinement | destinations under Settings, Models |

Most setup below is about the **LLM** role. Transcription uses Whisper sizes,
`tiny` / `base` / `small` and up, via MLX-Whisper or faster-whisper; its model
calls still follow the same admitted execution contract described below.

---

## The three ways to bring an LLM

You can run the LLM **in-process** (HoldSpeak loads the weights) or **over an
endpoint** (a server you run loads them). Pick one per consumer.

### 1. GGUF, in-process (`llama_cpp` / intel `local`)

The cross-platform default. HoldSpeak loads a `.gguf` file directly via
`llama-cpp-python` (Metal on Apple Silicon, CUDA/CPU elsewhere).

- **Install:** `uv pip install -e '.[dictation-llama]'`
  (on macOS arm64, build with Metal: `CMAKE_ARGS="-DGGML_METAL=on" …`)
- **Get a model:** any GGUF chat model from HuggingFace. Example (swap freely):
  ```bash
  mkdir -p ~/Models/gguf
  huggingface-cli download bartowski/Qwen3.5-4B-Instruct-GGUF \
    Qwen3.5-4B-Instruct-Q4_K_M.gguf \
    --local-dir ~/Models/gguf --local-dir-use-symlinks False
  ```
- **Point HoldSpeak at it:**
  - dictation → `dictation.runtime.llama_cpp_model_path`
  - meeting intel → `meeting.intel_realtime_model`

### 2. MLX, in-process (Apple Silicon, `mlx`)

The recommended in-process path on M-series Macs: faster and more
memory-efficient than GGUF there.

- **Install:** `uv pip install -e '.[dictation-mlx]'`
- **Get a model:** any MLX chat build (a local snapshot dir **or** an HF repo id).
  Example (swap freely):
  ```bash
  huggingface-cli download mlx-community/Qwen3.5-8B-MLX-4bit \
    --local-dir ~/Models/mlx/Qwen3.5-8B-MLX-4bit
  ```
- **Point HoldSpeak at it:** `dictation.runtime.mlx_model`
  (a path, or a bare `mlx-community/…` repo id).

> MLX is currently wired for the **dictation** runtime. Meeting intel runs on
> GGUF (`local`) or any endpoint (`cloud`).

### 3. Any OpenAI-compatible endpoint (`openai_compatible` / intel `cloud`)

The escape hatch: point HoldSpeak at **any** server that implements
`/v1/chat/completions`. This covers a self-hosted LAN box, Ollama's OpenAI
bridge, vLLM, llama.cpp-server, LM Studio, LiteLLM, or an actual cloud API. The
endpoint owns model loading; HoldSpeak needs no local weights.

- **Install:** `uv pip install -e '.[dictation-openai]'` (dictation side)
- **Configure:** add the endpoint once under **Settings, Models → AI
  connections** (the API resource is `/api/inference-targets`; `/api/profiles`
  is a read-only alias). Give it a name, base URL, model, and context window,
  then choose it for a job:
  - **Writing & dictation, meetings, background assistance:** **Choose AI for
    each job** in the same module.
  - **Agents:** the **Runs on** picker where you author the Agent.
- **Keys:** set, replace, or remove a destination key inline in **Settings,
  Models**. The hub keeps that value in owner-only local custody and joins it
  only at run time; Settings reads show only whether it is set.
  `HOLDSPEAK_PROFILE_<ID>_KEY` remains a headless fallback. Removing an inline
  key suppresses that fallback for the destination. A keyless self-hosted
  endpoint needs no key at all.

There is no hand-edited alternative. `dictation.runtime.openai_compatible_*`
and `meeting.intel_cloud_*` are dead fields: an upgrade reads a configured
legacy endpoint once, converts it into a `legacy-dictation` or `legacy-intel`
destination, and points the feature at it. After that the destination is the
only truth.

> **On the name `cloud`.** `meeting.intel_provider` still chooses whether the
> meeting-intel leg runs `local` (in-process GGUF), `cloud`, or `auto`.
> `cloud` means "the endpoint leg", not necessarily a hosted or paid API:
> point its destination at a self-hosted LAN server and it stays entirely
> local.

---

## What a destination means at execution

A **Runs on** choice is mutable configuration only until work is admitted. Before
an actual model attempt, HoldSpeak captures the resolved destination as an
immutable `DeploymentRevision`: engine kind, endpoint/model identity, boundary,
secret slot reference, and mesh node where applicable. The `InferenceRunner` at
the executing boundary admits one `inference.invoke@1` child against that exact
revision. The reviewed adapter constructs and dispatches only after the child is
claimed. Editing a destination or picker after admission cannot retarget that
attempt.

Every physical attempt gets its own immutable terminal receipt. An `auto` local
to endpoint fallback is two frozen revisions and, when both are attempted, two
children and two receipts; it is never an invisible provider switch inside one
receipt. Cancellation suppresses late output, and uncertain execution remains
`indeterminate`. Destination keys are joined only inside the selected adapter;
credentials, prompts, completions, and token streams are absent from deployment
revisions and kernel rows.

Thought refinement follows the same admission path with a stricter context
boundary. A new Thought has no attached context. The owner explicitly attaches
a qualified Note or the seeded Everyday-context collection; HTTP and MCP carry
refs and expected revisions only. Immediately before dispatch, the hub verifies
the immutable attachment ledger, resolves the exact versioned leaves into a
bounded canonical JSON block, labels it as untrusted data, and binds its hash to
the invocation. Changed or deleted sources refuse by human name. Once the
dispatch hook commits, later edits or detach cannot alter the provider bytes,
and no attachment/review action silently launches a second model attempt.

No backend is exempt. In-process GGUF/MLX work, endpoint calls, mesh workers,
and shared Whisper transcription/preload all enter an `InferenceRunner` at their
executing boundary. Meeting, dictation, and configured wake sessions are finite
parents, while each
actual LLM or Whisper call is a causally linked child with a live authority and
revision check. See the canonical
[one-path inference contract](ARCHITECTURE.md#inference-admission-one-path-one-receipt-per-attempt).

## Runs on destinations

The three backends above answer *how* an LLM runs. A **Runs on destination**
answers *where*: a named, reusable target for model-backed work. API and
persistence contracts retain the `profile` compatibility name.

- **Basic.** Pick one active destination. This is the single-target experience:
  one model, app wide. Most users never need more.
- **Advanced.** Keep a list of named destinations (this device, or any
  OpenAI-compatible endpoint such as OpenRouter or Claude) and assign one
  **per Agent**. Scout can run on this device while Editor runs on an endpoint
  and Critic runs on a third. Every place that touches a model shows a small
  "Runs on" control with the resolved default already selected and changeable
  at the point of use.

A destination carries only its definition: name, kind, endpoint, model, and
usable context window. It never carries the API key. The Python/web sync contract
is derived from `SYNC_REGISTRY` in `holdspeak/services/sync_service.py`; its
`profile` and `deployment_revision` kinds, pull buckets, and JSON schemas are the
authority. Web fields are checked against those schemas. No Swift enum or native
fixture defines this contract, and the inference-admission change adds no Swift
compatibility work.
A future native client may consume the finished Python/web shape. The key stays
local and is joined only at dispatch time. See
[Security & privacy](SECURITY.md#5-secrets-handling).

Destinations also drive the desktop hub's pipelines. **Settings, Models** leads
with **Choose your AI**, discovers models already stored under `~/Models`, and
keeps reusable endpoints under **AI connections**. **Choose AI for each job**
can route writing and dictation, meetings, and background assistance to one of
those connections. `holdspeak doctor` reports
which destination each pipeline resolves to and warns when an assigned
destination is missing or has no key. Set the key inline in **Settings,
Models**, or use `HOLDSPEAK_PROFILE_<ID>_KEY` for headless fallback.

### The mesh edge: run on another node

A Runs on destination can name a node instead of an endpoint: pick the **Mesh
node** kind and type the node's name. A run against that destination relays
through the hub to the node's worker, which executes it on the node's own
provider and keys. The model and provider key never move; the request does.

Pair the node deliberately. On the hub:

```bash
holdspeak node token create --name edge >/dev/null
holdspeak node token export --name edge --out ./holdspeak-pairing-edge.json
```

Move that owner-only pairing file to the serving machine through a channel you
trust, then on that machine:

```bash
holdspeak node pair --from ./holdspeak-pairing-edge.json
holdspeak mesh serve --hub http://<hub>:8765
```

The transfer contains this node's bearer credential plus the hub's public
Ed25519 offer pin; the hub's private signing key never leaves the hub. The worker
authenticates as a node, not with `HOLDSPEAK_HUB_TOKEN`. For every claimed job it
verifies and reserves the signed, node/revision/operation/attempt/deadline-bound
offer
before its local `InferenceRunner` constructs or calls a provider. The worker's
physical attempt gets its own immutable local receipt; the hub independently
settles the content-free report. Retrying report delivery never reruns the model.

Running `mesh serve` is the consent; Ctrl-C stops it and the node reads offline
within seconds. A node is live only while its worker polls, so pickers and the
models list show its state, a run against an offline node refuses immediately and
names the node, and `holdspeak doctor` lists every edge with its age under "Mesh
edges". The serving machine needs a real provider of its own (a local model or an
endpoint) in its config; the hub-side destination only names where the run goes.
Relay runs are chat, Agent, meeting intelligence, and dictation rewrites; the
prompt travels only between the hub and the paired executing node.

Manage Runs on destinations in **Settings, Models** or on the Web compatibility
route `/profiles`; assign an Agent in the Agent editor.

## Current suggestions (a moving target)

These are reasonable defaults at the time of writing, **not** mandates. Newer
or smaller models that fit your hardware are fine; HoldSpeak only cares that the
model can follow an instruction and return JSON when asked.

| Consumer | Backend | Suggested default | Where set |
|----------|---------|-------------------|-----------|
| Dictation | `llama_cpp` (GGUF) | a current small instruct GGUF (e.g. `Qwen3.5-4B-Instruct-Q4_K_M`) | `dictation.runtime.llama_cpp_model_path` |
| Dictation | `mlx` (Apple) | a current Qwen3.5 MLX build (e.g. `Qwen3.5-8B-MLX-4bit`) | `dictation.runtime.mlx_model` |
| Meeting intel | `local` (GGUF) | a current small/mid instruct GGUF (e.g. `Qwen3.5-9B-Instruct-Q6_K`) | `meeting.intel_realtime_model` |
| Meeting intel | `cloud` (endpoint) | whatever your endpoint serves | a destination under Settings, Models, chosen as the meetings **Runs on** |

**Sizing intuition:** a small instruct model (~4-9B, Q4-Q6) is fast and good
enough for routing/enrichment and most meeting intel; a mid model (~14-32B) gives
sharper intel at the cost of latency. GPU offload (Metal/CUDA, `n_gpu_layers=-1`)
makes the larger tiers practical.

---

## Notes

- **GGUF is current**, not legacy: it's the standard local-inference format and
  HoldSpeak keeps it as the default in-process format. Only specific *model
  names* get refreshed over time.
- HoldSpeak never downloads weights for you. `holdspeak doctor` and the web
  readiness panel only *show* the install/download commands; you run them.
- If a model path is missing or an endpoint times out, HoldSpeak degrades
  gracefully (preserves the original transcript; queues meeting intel for retry)
  rather than failing the capture.

## See also

- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): where the dictation model
  is used.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): where the meeting-intel model is used.
- [Security & Privacy](SECURITY.md): what a cloud endpoint changes about egress.
