# HoldSpeak Intelligent Typing Setup

Intelligent typing turns rough speech into useful text for the active app. It
can route an utterance through local rules, project context, agent context, and
an optional LLM rewrite stage before inserting text.

Use this after basic voice typing works. If you are starting from zero, read
[Getting Started](GETTING_STARTED.md) first.

## What You Are Setting Up

The intelligent-typing loop is:

```text
speech -> Whisper transcript -> punctuation cleanup -> dictation pipeline -> typed text
```

The pipeline can:

- classify an utterance against dictation blocks;
- inject project knowledge;
- rewrite rough speech into a cleaner prompt;
- adapt output for Codex, Claude, terminal, browser, editor, or chat;
- suggest narrow `.hs/.../*.md` project documentation updates for review.

## 1. Open The Dictation Cockpit

Start HoldSpeak:

```bash
holdspeak
```

Open:

```text
/dictation
```

Start with the **Readiness** tab. It tells you what is configured, what is
missing, and what to fix next.

## 2. Choose A Runtime Backend

Open:

```text
/dictation -> Runtime
```

Enable:

- `Enable dictation pipeline`
- Optional: `Enable project-aware rewrite stage (.hs/)`

Choose one backend:

| Backend | Use when |
| --- | --- |
| `auto` | You want HoldSpeak to prefer MLX on Apple Silicon and otherwise use llama.cpp |
| `mlx` | You are on Apple Silicon and have an MLX model installed |
| `llama_cpp` | You have a local GGUF model |
| `openai_compatible` | You have a local, LAN, or hosted `/v1/chat/completions` endpoint |

Install extras as needed:

```bash
uv pip install -e '.[dictation-mlx]'
uv pip install -e '.[dictation-llama]'
uv pip install -e '.[dictation-openai]'
```

## 3. Configure An OpenAI-Compatible Endpoint

Use this path for llama.cpp server, LM Studio, Ollama OpenAI bridge, vLLM,
LiteLLM, or a hosted OpenAI-compatible API.

In `/dictation -> Runtime`, set:

| Field | Example |
| --- | --- |
| Backend | `openai_compatible` |
| Base URL | `http://127.0.0.1:8000/v1` |
| Model | `qwen2.5-7b-instruct` |
| API key env | `OPENAI_API_KEY` |
| Timeout seconds | `8` |

Config file shape:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "project-rewriter", "kb-enricher"],
      "target_profile_override": "auto"
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
      "openai_compatible_model": "qwen2.5-7b-instruct",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 8
    }
  }
}
```

HoldSpeak reads the API key from the named environment variable. Do not put API
keys in `.hs/` files.

Known-good local dogfood profile from HS-19 closeout:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["project-rewriter"],
      "target_profile_override": "codex_cli"
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8080/v1",
      "openai_compatible_model": "Qwen3.5-9B-UD-Q6_K_XL.gguf",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 20
    }
  }
}
```

Validation used a local `/v1/chat/completions` server at `127.0.0.1:8080`
and `holdspeak dictation dry-run`. If HoldSpeak reports that the OpenAI
client package is missing, install:

```bash
uv pip install -e '.[dictation-openai]'
```

## 4. Set The Target Profile

HoldSpeak tries to detect the active app automatically. If detection is wrong,
set a manual target override in:

```text
/dictation -> Runtime -> Target profile override
```

Options:

| Option | Meaning |
| --- | --- |
| `Auto-detect target` | Use active-window hints |
| `Codex CLI` | Shape dictation as an implementation prompt for Codex |
| `Claude Code` | Shape dictation as a prompt/reply for Claude Code |
| `Terminal shell` | Preserve command syntax more aggressively |
| `Browser` | Write prose suitable for browser text boxes |
| `Editor` | Write code/editor-friendly prose |
| `Chat` | Write conversational chat text |

Use **Reset target to auto** when active-window detection is working again.

## 5. Create Project Context

Open:

```text
/dictation -> Project Context
```

Create a small `.hs/` directory in your repo:

```text
.hs/
  instructions.md
  context.md
  workflows.md
  targets.md
  ignore
```

Start with this minimal set:

```md
# .hs/instructions.md
When dictating into Codex or Claude, rewrite rough speech into a concise
engineering request. Preserve explicit filenames, commands, and test names.

# .hs/context.md
This project is a local-first Python app with a FastAPI web runtime and Astro
frontend.

# .hs/workflows.md
Run focused Python tests with `.venv/bin/pytest <path>`.
Rebuild the web bundle with `cd web && npm run build`.

# .hs/targets.md
Codex: concise implementation request.
Claude: product/design discussion is acceptable, but include concrete repo context.
Terminal: preserve command syntax exactly.
Browser: keep output plain and paste-friendly.

# .hs/ignore
.env
secrets
private keys
```

Write policy:

- HoldSpeak reads `.hs/` during dictation.
- HoldSpeak does not silently write `.hs/` files.
- Suggested `.hs/.../*.md` updates require explicit review and apply.
- Secret-looking content is skipped or rejected.

## 6. Install Claude/Codex Agent Hooks

Agent hooks let Claude Code and Codex tell HoldSpeak their current `cwd`,
session id, transcript path, and recent assistant state. This is how HoldSpeak
can know which project an LLM CLI is working in.

Use [Claude/Codex Agent Hook Install](AGENT_HOOK_INSTALL.md) for the full
machine-level install, verification, capture-mode, and AIPI companion checks.

Open:

```text
/dictation -> Agent Hooks
```

Copy the template for the tool you use. Or generate templates from the CLI:

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex
```

To let HoldSpeak capture the latest assistant message and detect when the agent
is waiting for your reply:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

Assistant-message capture stores only a small local snippet and can be cleared
from the `/dictation` banner.

## 7. Run A Dry-Run

Use the web UI:

```text
/dictation -> Dry-run
```

Try:

```text
ask codex to inspect the failing project context test and propose a minimal fix
```

Or use the CLI:

```bash
holdspeak dictation dry-run "ask codex to inspect the failing project context test and propose a minimal fix"
```

Check:

- runtime status is loaded or available;
- target profile is correct;
- stage telemetry has no unexpected fallback;
- final text is useful;
- project documentation suggestion appears only when it is genuinely useful.

## 8. Review Suggested Project Documentation

When the project-aware rewrite stage sees durable context worth preserving, it
may suggest a narrow project documentation update such as:

```text
.hs/memory/retry-worker-next-run.md
.hs/decisions/agent-hooks-context-channel.md
.hs/workflows/web-build-command.md
```

Open:

```text
/dictation -> Project Context
```

Review the suggested path, rationale, and content. You can edit the content
before applying or dismiss the suggestion. Apply only writes validated paths
under:

```text
.hs/memory/
.hs/decisions/
.hs/handoffs/
.hs/workflows/
.hs/issues/
```

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Runtime unavailable | Missing extra/model/server | Open Readiness and Runtime; run `holdspeak doctor` |
| Dry-run preserves original text | Stage fallback or no project context | Check dry-run telemetry and `.hs/instructions.md` |
| Target says `unknown` | Active-window hints unavailable | Set Target profile override |
| Codex/Claude cwd is missing | Hooks not installed/firing | Open Agent Hooks and copy templates again |
| Suggestions are noisy | Context too broad or prompt too generic | Narrow `.hs/instructions.md` and `.hs/targets.md` |
| Endpoint times out | Model/server too slow | Increase timeout or use a smaller/faster model |

## Good First Configuration

For daily coding-agent dictation, use:

```json
{
  "dictation": {
    "pipeline": {
      "enabled": true,
      "stages": ["intent-router", "project-rewriter", "kb-enricher"],
      "max_total_latency_ms": 600,
      "target_profile_override": "auto"
    },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
      "openai_compatible_model": "qwen2.5-7b-instruct",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 8,
      "warm_on_start": false
    }
  }
}
```

Then validate:

```bash
holdspeak doctor
holdspeak dictation runtime status
holdspeak dictation dry-run "ask codex to summarize what changed and suggest a next test"
```
