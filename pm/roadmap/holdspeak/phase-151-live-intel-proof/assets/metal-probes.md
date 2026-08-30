# Phase 151 pre-charter metal probes — orchestrator-run, 2026-08-30

Live facts established BEFORE the charter, each by an actual probe
(the test-before-claiming law). These are the ground the stories
stand on.

## The box (.43 = 192.168.1.43, ssh karol@)

- x86_64, 62 GB RAM, RTX 4080 SUPER 16 GB (≈3.5 GB used by the
  resident server — Qwen3.6-35B runs `--cpu-moe`), llama.cpp built
  at `/home/karol/dev/llama.cpp`. **Disk 98% full (6 GB free) — NO
  downloads onto the box, ever; use what is on the shelf.**
- Port 8080 (the owner's resident server): Qwen3.6-35B-A3B-UD-Q5_K_XL,
  `/health` ok. **Launched with a server-level
  `--json-schema {"line": ...}` pin** (see the probe below).

## Probe 1 — the vision endpoint EXISTS now (port 8081)

The shelf already held a vision pair:
`Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf` (6.9 G) +
`mmproj-Qwythos-9B-Claude-Mythos-5-1M-f16.gguf` (876 M). Launched
beside the resident server, non-destructively:

```
ssh karol@192.168.1.43 'nohup /home/karol/dev/llama.cpp/build/bin/llama-server \
  -m /home/karol/dev/llama.cpp/models/Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf \
  --mmproj /home/karol/dev/llama.cpp/models/mmproj-Qwythos-9B-Claude-Mythos-5-1M-f16.gguf \
  --host 0.0.0.0 --port 8081 -ngl 99 -c 8192 -np 1 \
  > /tmp/hs151-vision-server.log 2>&1 & disown'
```

Healthy in ~25 s. **Survives the session, not a reboot** — the line
above is the relaunch recipe. Probe: a Chromium-rendered O365-style
week grid ([vision-probe-week.png](./vision-probe-week.png), 4
events) sent as a data-URI image to `/v1/chat/completions` at
temperature 0 returned ALL FOUR events with exact days, times, and
titles, first try:

```json
[{"day": "Mon Sep 1", "start": "11:00", "end": "12:00", "title": "Team planning"},
 {"day": "Tue Sep 2", "start": "09:00", "end": "09:30", "title": "1:1 w/ Ewa"},
 {"day": "Thu Sep 4", "start": "11:00", "end": "12:30", "title": "Architecture review"},
 {"day": "Fri Sep 5", "start": "14:00", "end": "15:00", "title": "Sprint retro"}]
```

This OVERRULES Audit A's "vision defers" conclusion (the audit ran
without knowledge of the 8081 launch). The snapshot adapter's
`_vision_capable()` pre-filter admits `openAICompatible` profiles —
a profile at `http://192.168.1.43:8081/v1` is the vision route.
Note: 8081 also serves plain completion with NO schema pin.

## Probe 2 — the 8080 schema pin vs request-level format (DECISIVE)

Bare request (no response_format), asking for
`{summary, action_items}` in the prompt:

```json
{"line": "Ewa will send the RFC, and Marek will update the runbook."}
```

The server-level pin SWALLOWS prompt-level JSON pleas. The same
request WITH request-level
`response_format: {type: json_schema, json_schema: {...summary,
action_items:[{task, owner}]...}}`:

```json
{"summary": "Ewa is responsible for sending the RFC, while Marek will update the runbook.",
 "action_items": [{"task": "Send RFC", "owner": "Ewa"},
                  {"task": "Update runbook", "owner": "Marek"}]}
```

Request-level format OVERRIDES the pin cleanly — and the model
emits REAL NAMED OWNERS unprompted.

## The latent defect this exposes (story 01's substance)

`holdspeak/intel/engine.py:294-303` — the cloud intel dispatch
sends NO `response_format`; it trusts the prompt's "return ONLY
JSON" instruction (`intel/parsing.py:16-46`). Against the owner's
actual resident server, production intel would receive
`{"line": ...}` and parse to nothing. The fix is request-level
structured output derived from the intel schema.

## The owner's rulings folded in (2026-08-30, their words)

1. "We can simulate it. I can certainly put up a youtube recording
   of a 1:1" — real-speech audio (YouTube 1:1 or the repo's
   `dogfood/_audio/meeting-*.wav` multi-speaker recordings) through
   the REAL import door (`POST /api/meetings/import` → real
   mlx-whisper → real intel) is the honest headless treatment; the
   mic hop is the one attended leg.
2. "you do have ssh keys to log in there... test the meetings
   adapter please" — the vision probe above; the full product-path
   snapshot proof is story 04.
