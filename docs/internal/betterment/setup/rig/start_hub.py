"""Start an isolated rig hub for the setup betterment walk (ports 8841-8849).

start_hub.py <scratch-home> <port> [agent-state:on|off]
"""
import os, subprocess, sys
WT = "/Users/karol/dev/tools/wt-daily-delight-delivery-20261017"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(WT, "scripts"))
home, port = sys.argv[1], sys.argv[2]
agent_state = sys.argv[3] if len(sys.argv) > 3 else "off"
assert 8841 <= int(port) <= 8849
real_home = os.path.expanduser("~")
import graph_walk  # noqa: E402
env = graph_walk._isolated_hub_env(home, os.path.join(home, "repos", "platform"))
# stubs (if any) live inside the scratch HOME (under the temp root, so cli_guard lets them run)
env["PATH"] = os.path.join(home, "bin") + ":" + env["PATH"]
env["UV_CACHE_DIR"] = os.path.join(real_home, ".cache", "uv")
env["UV_NO_SYNC"] = "1"
env["SHELL"] = "/bin/sh"
env["HOLDSPEAK_AGENT_STATE"] = agent_state
log = open(os.path.join(SCR, f"hub-{port}.log"), "w")
p = subprocess.Popen([os.path.join(WT, ".venv/bin/python"), "scripts/graph_walk.py", "serve", "--port", port, "--scheduler"],
                     cwd=WT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print(p.pid)
