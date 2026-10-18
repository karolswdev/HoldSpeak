"""Start an isolated rig hub for the shell betterment walk: start_hub.py <home> <port>."""
import os, subprocess, sys
WT = "/Users/karol/dev/tools/wt-daily-delight-delivery-20261017"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(WT, "scripts"))
home = sys.argv[1]
port = sys.argv[2]
real_home = os.path.expanduser("~")
import graph_walk  # noqa: E402
env = graph_walk._isolated_hub_env(home, os.path.join(home, "repos", "platform"))
env["UV_CACHE_DIR"] = os.path.join(real_home, ".cache", "uv")
env["UV_NO_SYNC"] = "1"
env["SHELL"] = "/bin/sh"
log = open(os.path.join(SCR, f"hub-{port}.log"), "w")
p = subprocess.Popen([os.path.join(WT, ".venv/bin/python"), "scripts/graph_walk.py", "serve", "--port", port, "--scheduler"],
                     cwd=WT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print(p.pid)
