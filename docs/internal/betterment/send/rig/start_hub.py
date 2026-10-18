"""Start an isolated rig hub for the Send betterment walk: start_hub.py <HOME> <port> [cli-runner.json]"""
import os, subprocess, sys
WT = "/Users/karol/dev/tools/wt-daily-delight-delivery-20261017"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(WT, "scripts"))
home, port = sys.argv[1], sys.argv[2]
runner = sys.argv[3] if len(sys.argv) > 3 else None
real_home = os.path.expanduser("~")
import graph_walk  # noqa: E402
env = graph_walk._isolated_hub_env(home, os.path.join(home, "repos", "platform"))
env["UV_CACHE_DIR"] = os.path.join(real_home, ".cache", "uv")
env["UV_NO_SYNC"] = "1"
env["SHELL"] = "/bin/sh"
cmd = [os.path.join(WT, ".venv/bin/python"), "scripts/graph_walk.py", "serve", "--port", port, "--scheduler"]
if runner:
    cmd += ["--cli-runner", runner]
log = open(os.path.join(SCR, f"hub-{port}.log"), "w")
p = subprocess.Popen(cmd, cwd=WT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print(p.pid)
