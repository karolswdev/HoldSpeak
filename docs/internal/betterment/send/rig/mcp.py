"""Call one MCP tool on a rig hub: mcp.py <port> <tool> '<json args>' [bearer]"""
import json, sys, urllib.request
port, tool = sys.argv[1], sys.argv[2]
args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
tok = sys.argv[4] if len(sys.argv) > 4 else "graph-walk-token"
body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}
if tool == "LIST":
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
req = urllib.request.Request(f"http://127.0.0.1:{port}/api/mcp", data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "Authorization": f"Bearer {tok}"})
try:
    out = urllib.request.urlopen(req, timeout=300).read().decode()
except urllib.error.HTTPError as e:
    out = e.read().decode()
print(out[:int(sys.argv[5]) if len(sys.argv) > 5 else 4000])
