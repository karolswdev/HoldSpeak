import subprocess
import json
run="35478778899"
meta=json.loads(subprocess.check_output(["gh", "run", "view", run, "--json", "headSha,url,name,conclusion"],text=True))
print("REMOTE BASELINE; fetched logs, not a local rerun")
print(json.dumps(meta,sort_keys=True))
log=subprocess.check_output(["gh", "run", "view", run, "--log-failed"],text=True)
for line in log.splitlines():
    if "FAILED tests/" in line:
        print(line)
