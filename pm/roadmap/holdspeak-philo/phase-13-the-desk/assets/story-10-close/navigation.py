import subprocess, sys
from pathlib import Path
import yaml
workflow=yaml.safe_load(Path(".github/workflows/test.yml").read_text())
steps=[s for j in workflow["jobs"].values() for s in j.get("steps", []) if s.get("name")=="Check public documentation links and headings"]
assert len(steps)==1
commands=[s for s in steps[0]["run"].splitlines() if s.strip()]
assert len(commands)==12
for command in commands:
    print("COMMAND:",command,flush=True)
    result=subprocess.run(command,shell=True,executable="/bin/bash")
    print("EXIT:",result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)
print("All 12 Documentation Navigation commands passed.")
