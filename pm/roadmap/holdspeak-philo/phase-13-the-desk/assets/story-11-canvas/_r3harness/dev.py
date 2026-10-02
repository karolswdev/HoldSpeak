"""PHILO-13-11: hold one canvas stack up for design iteration (not part of the proof run).

Usage: .venv/bin/python <harness>/dev.py <mode> <statefile>; writes the URL and seed to
<statefile>; stops (and removes its HOME) when <statefile>.stop appears.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rig

mode, state = sys.argv[1], Path(sys.argv[2])
with rig.Stack(mode) as st:
    state.write_text(json.dumps({"url": st.url, "hub": st.hub, "seed": st.seed, "home": st.home, "guard": st.guard}))
    stop = Path(str(state) + ".stop")
    while not stop.exists():
        time.sleep(1)
    stop.unlink()
state.unlink(missing_ok=True)
