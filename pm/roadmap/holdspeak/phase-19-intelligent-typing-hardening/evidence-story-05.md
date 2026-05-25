# Evidence — HS-19-05 Real Endpoint Dogfood and Phase Exit

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-19-05](./story-05-endpoint-dogfood-and-exit.md)

## What changed

- Dogfooded a real local OpenAI-compatible `/v1` endpoint.
- Documented the known-good local endpoint profile in [Intelligent Typing Setup](../../../../docs/INTELLIGENT_TYPING_GUIDE.md).
- Added [final-summary.md](./final-summary.md) for Phase 19.
- Marked Phase 19 complete in the phase status file and parent roadmap.

## Endpoint discovery

```bash
for url in http://127.0.0.1:8000/v1/models http://127.0.0.1:1234/v1/models http://127.0.0.1:11434/v1/models http://127.0.0.1:8080/v1/models; do
  printf '%s -> ' "$url"
  curl -fsS --max-time 2 "$url"
done
```

Result excerpt:

```text
http://127.0.0.1:8000/v1/models -> unreachable (curl exit 7)
http://127.0.0.1:1234/v1/models -> unreachable (curl exit 7)
http://127.0.0.1:11434/v1/models -> unreachable (curl exit 7)
http://127.0.0.1:8080/v1/models -> {"models":[{"name":"Qwen3.5-9B-UD-Q6_K_XL.gguf","model":"Qwen3.5-9B-UD-Q6_K_XL.gguf",...}]}
```

## Direct chat-completions smoke

```bash
curl -fsS --max-time 20 http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen3.5-9B-UD-Q6_K_XL.gguf","messages":[{"role":"user","content":"Reply with exactly: holdspeak endpoint ok"}],"max_tokens":16,"temperature":0}'
```

Result:

```json
{"choices":[{"finish_reason":"stop","index":0,"message":{"role":"assistant","content":"holdspeak endpoint ok"}}],"created":1779665721,"model":"Qwen3.5-9B-UD-Q6_K_XL.gguf","system_fingerprint":"b8369-34818ea6c","object":"chat.completion","usage":{"completion_tokens":5,"prompt_tokens":20,"total_tokens":25},"id":"chatcmpl-qZNbxq09MdqzOJLipwuee9yjFgD6jgdG"}
```

## HoldSpeak dry-run smoke

First attempt showed the environment was missing the optional OpenAI client dependency:

```text
resolution: unavailable — Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]
warning: LLM runtime unavailable (Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]); running with intent-router skipped.
```

Installed the optional dependency into the active venv:

```bash
.venv/bin/python -m pip install 'openai>=1.0.0'
```

Result:

```text
Successfully installed distro-1.9.0 jiter-0.15.0 openai-2.38.0 sniffio-1.3.1
```

Then ran HoldSpeak against a temporary config/project:

```bash
HOME="$tmp/home" .venv/bin/holdspeak dictation runtime status
HOME="$tmp/home" .venv/bin/holdspeak dictation dry-run \
  'ask codex to inspect the web server device health endpoint and add a focused regression test if it is missing'
```

Result excerpt:

```text
requested backend: openai_compatible
openai_compatible_model: Qwen3.5-9B-UD-Q6_K_XL.gguf
openai_compatible_base_url: http://127.0.0.1:8080/v1
resolved backend: openai_compatible (explicit)
endpoint: configured (http://127.0.0.1:8080/v1, model=Qwen3.5-9B-UD-Q6_K_XL.gguf)

--- dry-run ---
project: project (holdspeak @ /tmp/holdspeak-hs19-dogfood.iqwJby/project)
resolved blocks: 0 from (no blocks file)
runtime: loaded (backend=openai_compatible)
input: 'ask codex to inspect the web server device health endpoint and add a focused regression test if it is missing'
---
[project-rewriter] elapsed_ms=778.18
  metadata: {'reason': 'rewritten', 'changed': True, 'context_dir': '/tmp/holdspeak-hs19-dogfood.iqwJby/project/.hs', 'target_profile': {'id': 'unknown', 'label': 'Unknown', 'confidence': 0.0, 'source': 'none'}, 'project_doc_suggestion': None, 'project_doc_suggestion_status': 'skipped_target'}
  text: 'Inspect the web server device health endpoint and add a focused regression test if it is missing.'
---
final_text: 'Inspect the web server device health endpoint and add a focused regression test if it is missing.'
total_elapsed_ms: 778.19
```

## Closeout validation

```bash
git diff --check
```

Result: passed.

```bash
npm run build
```

Result: passed from `web/`; 7 pages built into `holdspeak/static/_built/`.

```bash
.venv/bin/pytest -q tests/unit/test_device_active_frames.py tests/integration/test_device_audio_ingest.py tests/integration/test_device_meeting_session.py tests/integration/test_web_server.py
```

Result: `114 passed in 4.20s`.

```bash
.venv/bin/pytest -q tests/unit/test_dictation_telemetry.py tests/unit/test_project_doc_suggestions.py tests/unit/test_target_profile.py tests/unit/test_dictation_project_rewriter.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_dry_run_api.py tests/integration/test_web_project_kb_api.py
```

Result: `100 passed in 3.77s`.

```bash
.venv/bin/pytest -q tests/unit/test_controller.py tests/unit/test_meeting_state.py
```

Result: `50 passed in 0.45s`.

```bash
.venv/bin/pytest -q tests/e2e/test_voice_typing_flow.py
```

Result: `12 passed in 0.08s`.

```bash
.venv/bin/pytest -q -m 'not metal'
```

Result: `1809 passed, 5 skipped, 16 deselected in 123.71s`.

Skipped items were optional real-model/hardware checks: scipy-backed meeting transcription, llama.cpp runtime/e2e, MLX runtime, and llama-cpp grammar import.
