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
| **LLM** | dictation block-classification + KB enrichment, and meeting intel | `dictation.runtime.*`, `meeting.intel_*` |

This document is about the **LLM** role. (Transcription uses Whisper sizes,
`tiny` / `base` / `small` and up, via MLX-Whisper or faster-whisper; see the
[README](../README.md).)

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
- **Configure:** author the endpoint once as a **Runs on destination**. The
  compatibility route remains `/profiles`; give it a name, base URL, and
  model, then choose it where work runs:
  - **Meeting intelligence:** Settings → **Runs on**.
  - **Dictation:** Dictation → Runtime → **Runs on**.
  - **Personas:** use the Persona editor's **Runs on** picker.
- **Configure by hand:** the compatibility shape lives in `config.json` and
  still works when no destination is selected:
  `dictation.runtime.openai_compatible_base_url` + `_model` + `_api_key_env`
  for dictation; `meeting.intel_provider: "cloud"` (or `"auto"` for
  local-first with endpoint fallback) + `meeting.intel_cloud_base_url` +
  `intel_cloud_model` for meeting intel.

> **On the name `cloud`.** The intel provider called `cloud` just means
> "the endpoint provider"; it is **not** necessarily a hosted/paid API. Point
> `intel_cloud_base_url` at a self-hosted LAN server and it stays entirely local.
> The API key (`intel_cloud_api_key_env`) is **optional** for keyless
> self-hosted endpoints.

---

## Runs on destinations

The three backends above answer *how* an LLM runs. A **Runs on destination**
answers *where*: a named, reusable target for model-backed work. API and
persistence contracts retain the `profile` compatibility name.

- **Basic.** Pick one active destination. This is the single-target experience:
  one model, app wide. Most users never need more.
- **Advanced.** Keep a list of named destinations (this device, or any
  OpenAI-compatible endpoint such as OpenRouter or Claude) and assign one
  **per Persona**. Scout can run on this device while Editor runs on an endpoint
  and Critic runs on a third. Every place that touches a model shows a small
  "Runs on" control with the resolved default already selected and changeable
  at the point of use.

A destination carries only its definition: name, kind, endpoint, model, and
usable context window. It never carries the API key. The definition syncs across
your surfaces (desktop hub, iPad, iPhone, web) so the same named destination is
available everywhere; a surface that cannot host a kind (a this-device GGUF in
a browser) shows it as unavailable rather than pretending. The key stays with
each surface and is joined only at request time. See
[Security & privacy](SECURITY.md#5-secrets-handling).

Runs on destinations also drive the desktop hub's pipelines: meeting intelligence and
the dictation rewrite each carry a "Runs on" picker (Settings → Cloud &
advanced, and Dictation → Runtime), so one destination can serve
Personas, Meetings, and dictation. `holdspeak doctor` reports
which destination each pipeline resolves to, warns when an assigned destination is
missing, and names the exact `HOLDSPEAK_PROFILE_<ID>_KEY` variable to export
when a destination needs a key on this machine.

### The mesh edge: run on another node

A Runs on destination can name a node instead of an endpoint: pick the **Mesh
node** kind and type the node's name. A run against that destination relays through
the hub to the node's worker, which executes it on the node's own provider
and keys. The model and the key never move; the request does. Any machine
becomes an edge with one command:

```bash
HOLDSPEAK_HUB_TOKEN=<the hub token> holdspeak mesh serve --hub http://<hub>:8765
```

Running the command is the consent; Ctrl-C stops it and the node reads
offline within seconds. On iPhone and iPad the same consent is one switch,
Settings → "Serve my models to the mesh": while the app is open, runs
against a destination naming that device execute on its own model.
Availability is honest: a node is live only while
its worker polls, so pickers and the models list show its state, a run
against an offline node refuses immediately and names the node, and
`holdspeak doctor` lists every edge with its age under "Mesh edges". The
serving machine needs a real provider of its own (a local model or an
endpoint) in its config; the hub-side destination only names where the run
goes. Relay runs are chat, Persona, meeting-intelligence, and dictation
rewrites; the prompt travels only between the hub and the executing node.

Manage Runs on destinations on the Web compatibility route `/profiles`, or in
native Settings; assign a Persona in the Persona editor.

## Current suggestions (a moving target)

These are reasonable defaults at the time of writing, **not** mandates. Newer
or smaller models that fit your hardware are fine; HoldSpeak only cares that the
model can follow an instruction and return JSON when asked.

| Consumer | Backend | Suggested default | Where set |
|----------|---------|-------------------|-----------|
| Dictation | `llama_cpp` (GGUF) | a current small instruct GGUF (e.g. `Qwen3.5-4B-Instruct-Q4_K_M`) | `dictation.runtime.llama_cpp_model_path` |
| Dictation | `mlx` (Apple) | a current Qwen3.5 MLX build (e.g. `Qwen3.5-8B-MLX-4bit`) | `dictation.runtime.mlx_model` |
| Meeting intel | `local` (GGUF) | a current small/mid instruct GGUF (e.g. `Qwen3.5-9B-Instruct-Q6_K`) | `meeting.intel_realtime_model` |
| Meeting intel | `cloud` (endpoint) | whatever your endpoint serves | `meeting.intel_cloud_model` + `meeting.intel_cloud_base_url` |

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
