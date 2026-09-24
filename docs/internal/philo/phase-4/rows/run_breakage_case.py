"""Run the actual breakage atlas variant in a process-local evening zone."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time


assert sys.argv[1:] in (["1440"], ["393"]), "Pass one viewport: 1440 or 393"
# Pick an IANA fixed-offset zone whose current hour is 20. Reproducible at
# any UTC hour; no machine setting or timestamp in the DB is rewritten.
offset = (20 - datetime.now(timezone.utc).hour + 12) % 24 - 12
zone = f"Etc/GMT{-offset:+d}" if offset else "Etc/GMT"
os.environ["TZ"] = zone
time.tzset()
local = datetime.now()
assert 17 <= local.hour < 23, (zone, local)
print(f"BREAKAGE_WINDOW TZ={zone} local={local.isoformat()} after_close=True", flush=True)
repo = Path(__file__).resolve().parents[5]
raise SystemExit(subprocess.call([
    sys.executable, "scripts/graph_walk.py", "run",
    "--atlas", "docs/internal/philo/graph/atlas-phase3.json",
    "--case", "case.closure.chain.s5_next_day_brief_with_breakage",
    "--brain", "astra", "--viewport", sys.argv[1], "--engine", "real",
    "--no-build", "--out",
    "pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/",
], cwd=repo))
