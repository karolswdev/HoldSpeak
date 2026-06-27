#!/usr/bin/env bash
#
# framework-sync-proof.sh — the runbook for the owner's REAL-METAL proof of the
# Primitive Framework cross-surface sync loop (THE_PRIMITIVE_FRAMEWORK.md).
#
# Part A (this script, automated): boot the desktop hub locally and prove the
#   web → pull loop with curl — author a Note + Agent the WEB way, then read them
#   back off /api/sync/pull as proper {meta, value} records.
#
# Part B (manual, documented at the bottom): pair the cabled iPad to this Mac and
#   watch a desk-authored note land via /api/sync/pull. THE proof the owner runs.
#
# Usage:
#   scripts/framework-sync-proof.sh                 # ephemeral DB in a tmp dir
#   HS_HOST=0.0.0.0 HS_PORT=8765 scripts/framework-sync-proof.sh   # LAN bind for the iPad
#
# Off-loopback (HS_HOST != 127.0.0.1) the hub REQUIRES an auth token. Set
# HOLDSPEAK_WEB_TOKEN to a secret and the script threads it on every curl.
set -euo pipefail

HS_HOST="${HS_HOST:-127.0.0.1}"
HS_PORT="${HS_PORT:-8799}"
BASE="http://${HS_HOST}:${HS_PORT}"
TOKEN="${HOLDSPEAK_WEB_TOKEN:-}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

WORK="$(mktemp -d)"
export HOLDSPEAK_DB_PATH="${HOLDSPEAK_DB_PATH:-$WORK/holdspeak.db}"
SERVER_PID=""

cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

# curl with the token threaded when one is set (required off-loopback).
hs_curl() {
  if [ -n "$TOKEN" ]; then
    curl -fsS -H "x-holdspeak-token: $TOKEN" "$@"
  else
    curl -fsS "$@"
  fi
}

echo "==> Booting the desktop hub on ${BASE} (DB: $HOLDSPEAK_DB_PATH)"

# Boot the REAL MeetingWebServer (the production app factory) in the background.
HS_HOST="$HS_HOST" HS_PORT="$HS_PORT" HS_TOKEN="$TOKEN" \
uv run python - <<'PY' &
import os, time
from pathlib import Path
from holdspeak.db import get_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

get_database(Path(os.environ["HOLDSPEAK_DB_PATH"]))
server = MeetingWebServer(
    WebRuntimeCallbacks(
        on_bookmark=lambda *a, **k: None,
        on_stop=lambda *a, **k: None,
        get_state=lambda: None,
    ),
    host=os.environ.get("HS_HOST", "127.0.0.1"),
    port=int(os.environ.get("HS_PORT", "8799")),
    auth_token=os.environ.get("HS_TOKEN", ""),
)
server.start()
print(f"hub up at {server.url}", flush=True)
while True:
    time.sleep(3600)
PY
SERVER_PID=$!

# Wait for the port to answer.
for _ in $(seq 1 40); do
  if hs_curl "${BASE}/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done

echo
echo "==> [WEB surface] POST /api/notes  (author a Note the web way)"
NOTE_JSON="$(hs_curl -X POST "${BASE}/api/notes" \
  -H 'content-type: application/json' \
  -d '{"title":"Hub proof note","body_markdown":"authored via the web API","tags":["proof"]}')"
echo "$NOTE_JSON"
NOTE_ID="$(printf '%s' "$NOTE_JSON" | uv run python -c 'import sys,json;print(json.load(sys.stdin)["note"]["id"])')"

echo
echo "==> [WEB surface] POST /api/agents  (author an Agent persona the web way)"
AGENT_JSON="$(hs_curl -X POST "${BASE}/api/agents" \
  -H 'content-type: application/json' \
  -d '{"name":"Proof Persona","avatar":"🤖","role":"assistant","system_prompt":"You summarize.","user_template":"Summarize: {input}","tools":["web"]}')"
echo "$AGENT_JSON"

echo
echo "==> [iPad surface] POST /api/sync/push  (push a ChangeSet the iPad way)"
hs_curl -X POST "${BASE}/api/sync/push" \
  -H 'content-type: application/json' \
  -d '{
    "notes":[{"meta":{"id":"ipad_note_proof","kind":"note","last_modified":"2099-01-01T00:00:00Z","deleted":false},
              "value":{"id":"ipad_note_proof","title":"From the iPad","body_markdown":"drawn on the desk","tags":["mobile"],"created_at":"2099-01-01T00:00:00Z","last_modified":"2099-01-01T00:00:00Z","deleted":false}}]
  }'
echo

echo
echo "==> GET /api/sync/pull  (BOTH surfaces' work reconciled in one store)"
hs_curl "${BASE}/api/sync/pull" > "$WORK/pull.json"
uv run python - "$NOTE_ID" "$WORK/pull.json" <<'PY'
import sys, json
note_id = sys.argv[1]
with open(sys.argv[2]) as fh:
    body = json.load(fh)
def show(bucket, rid):
    for rec in body.get(bucket, []):
        if rec["meta"]["id"] == rid:
            print(f"  [{rec['meta']['kind']}] id={rec['meta']['id']} "
                  f"last_modified={rec['meta']['last_modified']} deleted={rec['meta']['deleted']}")
            print(f"      value keys: {sorted(rec['value'])}")
            return True
    print(f"  !! {rid} NOT found in {bucket}")
    return False
ok = show("notes", note_id)            # the web-authored note
ok &= show("notes", "ipad_note_proof") # the iPad-pushed note
ok &= any(a["value"].get("name") == "Proof Persona" for a in body.get("agents", []))
print()
print("PROOF:", "PASS — web-authored + iPad-pushed primitives both ride /api/sync/pull"
      if ok else "FAIL — a record did not round-trip")
sys.exit(0 if ok else 1)
PY

echo
echo "==> Hub loop proven. (Tearing down the ephemeral hub.)"

cat <<'RUNBOOK'

────────────────────────────────────────────────────────────────────────────
PART B — the cabled-iPad metal proof (manual; this is the owner's button)
────────────────────────────────────────────────────────────────────────────
Goal: a Note authored on the iPad desk lands in the Mac hub's /api/sync/pull.

1. Boot the hub bound to the LAN so the iPad can reach it. Off-loopback REQUIRES
   a token:
       export HOLDSPEAK_WEB_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(24))')"
       HS_HOST=0.0.0.0 HS_PORT=8765 scripts/framework-sync-proof.sh
   (Part A will run against the LAN bind; leave it up, or boot the real
    `holdspeak` runtime the same way.)

2. Find the Mac's LAN IP:   ipconfig getifaddr en0   (e.g. 192.168.1.13)

3. On the cabled iPad, point the HoldSpeak app's sync endpoint at the hub:
       Base URL:  http://<mac-lan-ip>:8765
       Token:     <the HOLDSPEAK_WEB_TOKEN value>
   (The iPad's HTTPSyncProvider threads the token as `x-holdspeak-token` /
    `?token=`, matching the hub's off-loopback auth gate.)

4. On the iPad desk, author a Note (and/or an Agent persona). Trigger a sync
   (the iPad pushes its ChangeSet to POST /api/sync/push).

5. From the Mac, watch it land:
       curl -fsS -H "x-holdspeak-token: $HOLDSPEAK_WEB_TOKEN" \
            http://<mac-lan-ip>:8765/api/sync/pull | python -m json.tool
   The iPad-authored note appears under "notes" as a {meta, value} record with
   meta.kind == "note" and your title in value.title. THAT is the metal proof:
   a primitive authored on the iPad is now first-class in the desktop hub.

6. Reverse leg (optional): author a Note on the Mac (POST /api/notes), pull from
   the iPad — it appears on the desk. Same store, both directions.
────────────────────────────────────────────────────────────────────────────
RUNBOOK
