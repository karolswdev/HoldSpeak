# Operator runbook: metal intel endpoint (.43)

Operational reference for running meeting intelligence against a self-hosted
llama.cpp server on the LAN. The reference box is 192.168.1.43 (x86_64, 62 GB
RAM, RTX 4080 SUPER 16 GB).

## The resident server (port 8080)

Port 8080 runs the owner's resident Qwen3.6-35B-A3B-UD-Q5_K_XL server with
`--cpu-moe` (about 3.5 GB VRAM). This server is launched with a server-level
`--json-schema` pin. Do not restart, reconfigure, or stop it.

The product sends request-level `response_format` with the meeting intel JSON
Schema. On llama.cpp builds that support request-level structured output, the
request-level format overrides the server pin cleanly.

## The vision server (port 8081)

Port 8081 serves Qwythos-9B-Claude-Mythos-5-1M with the vision projection.
It is launched manually and does not survive a reboot. Relaunch command:

```
ssh karol@192.168.1.43 'nohup /home/karol/dev/llama.cpp/build/bin/llama-server \
  -m /home/karol/dev/llama.cpp/models/Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf \
  --mmproj /home/karol/dev/llama.cpp/models/mmproj-Qwythos-9B-Claude-Mythos-5-1M-f16.gguf \
  --host 0.0.0.0 --port 8081 -ngl 99 -c 8192 -np 1 \
  > /tmp/hs151-vision-server.log 2>&1 & disown'
```

Healthy in about 25 seconds. Verify with `curl http://192.168.1.43:8081/health`.

Port 8081 has no `--json-schema` pin, so it also serves plain completion.
The `calendar.snapshot_extract` capability uses this endpoint for vision-based
calendar extraction.

## Disk (critical)

The box disk is 98% full (about 6 GB free). Never download anything to it.
Use only what is already on the shelf (`/home/karol/dev/llama.cpp/models/`).

## Wiring a fresh HOME for metal intel

`scripts/wire_metal_intel.py` creates an openAICompatible v2 profile and the
`meeting.deferred_analysis` assignment through the real adoption machinery.
Usage:

```bash
# Wire using a target HOME (the rig's isolated HOME)
HOME=/tmp/hs151-rig python scripts/wire_metal_intel.py

# Or specify explicitly
python scripts/wire_metal_intel.py --home /tmp/hs151-rig

# Override the default endpoint or model
python scripts/wire_metal_intel.py --base-url http://192.168.1.43:8080/v1
python scripts/wire_metal_intel.py --model my-model-id
```

Defaults: `--base-url http://192.168.1.43:8080/v1`, `--model qwen3.6-35b`.
The script is idempotent (revision CAS on all writes).

## What the wiring creates

| Artifact | Identity |
|---|---|
| v2 profile | `metal-intel` |
| v1 profile (legacy bridge) | `metal-intel` |
| Deployment head | `head-metal-intel` |
| Model artifact | `artifact-metal-intel` |
| Capability assignment | `meeting.deferred_analysis` to `metal-intel` |

## Verified latency (from metal probes)

| Operation | Wall clock |
|---|---|
| Transcription (mlx-whisper, 2 min audio) | about 10 s |
| Intel extraction (35B, cpu-moe, 8080) | about 8 s |
| Vision extraction (9B, GPU, 8081, truth image) | about 6 s |
| Vision extraction (9B, GPU, 8081, messy image) | about 13 s |

## The schema-pinned-server fact

The 8080 server was launched with `--json-schema {"line": ...}`. Without
request-level `response_format`, every response conforms to `{"line": ...}`
regardless of what the prompt asks for. The product's request-level
`response_format` override resolves this.

Bare request result (no response_format): `{"line": "..."}`.
With response_format (the product path): `{"summary": "...", "action_items": [...], "topics": [...]}`.
