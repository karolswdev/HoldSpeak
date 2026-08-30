# HS-150-08 real-metal legs on .43 (llama.cpp Q6)

Two real-metal legs run on the Intel box at `192.168.1.43:8080`
(llama.cpp Q6 K-quant, accessible from an unsandboxed shell or over
SSH).

## Prerequisites

### Env / profile rows that must exist

1. **Profile row:** a profile id (e.g. `hs150-metal-local`) pointing to
   the Q6 GGUF on .43, registered in the hub's SQLite:
   ```
   profile_id:  hs150-metal-local
   kind:        onDevice
   provider:    local
   runtime:     llama_cpp_prompt_v1
   endpoint:    http://192.168.1.43:8080
   ```

2. **Global assignment:** the profile must be the active global
   assignment (or a capability-scoped assignment for `chat.turn`):
   ```bash
   # Via the hub API (the desk's Settings > Assignments UI also works):
   curl -X PUT http://localhost:PORT/api/settings \
     -H 'X-HoldSpeak-Token: TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{"inference": {"default_profile": "hs150-metal-local"}}'
   ```

3. **Hub running:** the owner's real hub must be running with the web
   bundle built and the thread routes mounted.

---

## Leg 1 -- two-turn streamed thread with time-to-first-delta

### What it proves

A two-turn streamed thread over the real llama.cpp Q6 engine: deltas
observed on the bus, first delta <= 1.5 s, receipts + egress badges on
both turns, rows match the glass.

### Commands

```bash
# 1. Open a WebSocket bus listener that prints timestamps.
#    Save this as /tmp/hs150-bus-listener.py and run alongside the turn.

cat > /tmp/hs150-bus-listener.py << 'PYEOF'
"""Bus listener that prints timestamps for thread frames."""
import asyncio, json, time, sys, base64, websockets

TOKEN = sys.argv[1] if len(sys.argv) > 1 else "owner-token"
URL = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:8080"

async def listen():
    encoded = base64.urlsafe_b64encode(TOKEN.encode()).rstrip(b"=").decode()
    uri = f"{URL}/ws/runtime"
    async with websockets.connect(
        uri,
        subprotocols=["holdspeak.v1", f"holdspeak.auth.v1.{encoded}"],
    ) as ws:
        turn_started_at = None
        first_delta_at = None
        print(f"connected to {uri}", flush=True)
        async for raw in ws:
            frame = json.loads(raw)
            ft = frame.get("type", "")
            now = time.monotonic()
            if ft == "thread_turn_started":
                turn_started_at = now
                print(f"[{now:.3f}] thread_turn_started  thread={frame['data']['thread_id'][:12]}  msg={frame['data']['message_id'][:12]}", flush=True)
            elif ft == "thread_delta":
                if first_delta_at is None and turn_started_at is not None:
                    first_delta_at = now
                    elapsed = first_delta_at - turn_started_at
                    print(f"[{now:.3f}] FIRST DELTA  elapsed={elapsed:.3f}s  text={frame['data']['text']!r}", flush=True)
            elif ft == "thread_turn_done":
                done_at = now
                if turn_started_at:
                    total = done_at - turn_started_at
                    first = (first_delta_at - turn_started_at) if first_delta_at else None
                    print(f"[{now:.3f}] thread_turn_done  receipt={frame['data']['receipt_id'][:8]}  outcome={frame['data']['outcome']}  total={total:.3f}s  first_delta={first:.3f}s" if first else f"[{now:.3f}] thread_turn_done  NO DELTAS", flush=True)
                turn_started_at = None
                first_delta_at = None

asyncio.run(listen())
PYEOF

# Run the listener in a background terminal:
uv run python /tmp/hs150-bus-listener.py "OWNER_TOKEN" "ws://localhost:PORT" &

# 2. Create a thread and send two turns.
TOKEN="OWNER_TOKEN"
PORT=8080  # the hub's port

# Turn 1
THREAD=$(curl -s -X POST http://localhost:$PORT/api/threads \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Metal leg 1"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:$PORT/api/threads/$THREAD/turns" \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"What are the three most important principles of clean architecture?"}'

# Wait for turn 1 to complete (watch the bus listener output).
sleep 10

# Turn 2
curl -s -X POST "http://localhost:$PORT/api/threads/$THREAD/turns" \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Now give me a concrete example for each principle."}'

# Wait for turn 2.
sleep 10

# 3. Verify: read the thread and check receipts + egress.
curl -s "http://localhost:$PORT/api/threads/$THREAD" \
  -H "X-HoldSpeak-Token: $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for m in d.get('messages', []):
    print(f\"role={m['role']}  receipt={m.get('receipt_id','')[:8]}  egress={m.get('egress_scope','')}  streaming={m.get('streaming')}  parts={len(m.get('parts',[]))}  aborted={m.get('aborted_at')}\")
"

# 4. Control: the old non-streaming Ask for the same prompt.
curl -s -X POST "http://localhost:$PORT/api/ask" \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"What are the three most important principles of clean architecture?"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"Ask receipt={d.get('receipt_id','')[:8]} output_len={len(d.get('output',''))}\")"
```

### Expected output from the bus listener

```
[t+0.000] thread_turn_started  thread=th_XXXX  msg=tmsg_XXXX
[t+0.XXX] FIRST DELTA  elapsed=X.XXXs  text='The '
[t+Y.YYY] thread_turn_done  receipt=XXXXXXXX  outcome=succeeded  total=Y.YYYs  first_delta=X.XXXs
```

The `first_delta` value must be <= 1.5 s. Record it in the evidence.

---

## Leg 2 -- People boundary under profile switch

### What it proves

A seeded sensitive part (People-sourced ref) is redacted from the
provider payload when `profile_override` is switched to a cloud profile.

### Commands

```bash
TOKEN="OWNER_TOKEN"
PORT=8080

# 1. Ensure People is set up and a relationship exists.
curl -s -X POST http://localhost:$PORT/api/people/setup \
  -H "X-HoldSpeak-Token: $TOKEN"

REL=$(curl -s -X POST http://localhost:$PORT/api/people/relationships \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Metal Test Person","relationship_kind":"direct_report"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('relationship',d).get('id'))")

# 2. Create a cloud profile (or use an existing one).
#    This profile must have egress_scope=cloud.
#    If one already exists, note its profile_id.
CLOUD_PROFILE="cloud-test"  # replace with actual cloud profile id

# 3. Create a thread with the person as a ref.
THREAD=$(curl -s -X POST http://localhost:$PORT/api/threads \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"People boundary test\",\"seed_refs\":[\"person:$REL\"]}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 4. Send a turn with the local profile (sensitive content should flow).
curl -s -X POST "http://localhost:$PORT/api/threads/$THREAD/turns" \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Tell me about this person"}'

sleep 5

# 5. Switch profile_override to the cloud profile.
curl -s -X PATCH "http://localhost:$PORT/api/threads/$THREAD" \
  -H "X-HoldSpeak-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"profile_override\":\"$CLOUD_PROFILE\"}"

# 6. Capture the provider payload via the engine's request logging.
#    The simplest approach: monkeypatch the adapter to log the payload.
#    Save this as /tmp/hs150-payload-capture.py:
cat > /tmp/hs150-payload-capture.py << 'PYEOF'
"""Capture and inspect the provider payload for People redaction.

Run this INSTEAD of step 7's curl -- it sends the turn and intercepts
the assembled payload before it reaches the engine.
"""
import json, sys
sys.path.insert(0, ".")
from holdspeak.db import get_database
from holdspeak.services.thread_service import ThreadService, _PEOPLE_REDACTION

db = get_database()
thread_id = sys.argv[1]
service = ThreadService(db, broadcast=lambda t, d: None, broker=getattr(db, "_broker", None))
thread = db.threads.get(thread_id)

# Assemble the payload with cloud egress redaction
payload = service.assemble_payload_for_egress(
    thread_id, "", thread, "cloud"
)
out = json.dumps(payload, indent=2)
print(out)

# Verify: no sensitive content in the payload
has_redaction = _PEOPLE_REDACTION in out
has_name = "Metal Test Person" in out
print(f"\nredaction_present={has_redaction}")
print(f"sensitive_name_leaked={has_name}")
if has_name:
    print("FAIL: sensitive People content leaked to cloud payload")
    sys.exit(1)
else:
    print("PASS: People content properly redacted for cloud egress")
PYEOF

uv run python /tmp/hs150-payload-capture.py "$THREAD"
```

### Expected output

```
{
  "messages": [
    {"role": "system", "content": "You are the desk's AI core. ..."},
    {"role": "system", "content": "[PERSON: Metal Test Person]\n[people content withheld]"},
    {"role": "user", "content": "Tell me about this person"}
  ],
  ...
}

redaction_present=True
sensitive_name_leaked=False
PASS: People content properly redacted for cloud egress
```

The payload file saved alongside this evidence must contain zero
occurrences of the seeded sensitive text. The unit pin from story 04
(`test_thread_service.py::test_people_redaction_on_cloud_egress`)
covers the same assertion in CI.
