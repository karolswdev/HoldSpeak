"""PHILO-13-15/17: hold one canvas stack up for iteration (not part of the proof run).

Usage: .venv/bin/python <harness>/dev.py <mode> <shims> <statefile>; stops (and removes its HOME)
when <statefile>.stop appears."""
import json, sys, time
sys.dont_write_bytecode = True   # no __pycache__ in the tree
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rig

mode, shims, state = sys.argv[1], sys.argv[2], Path(sys.argv[3])
with rig.Stack(mode, shims) as st:
    state.write_text(json.dumps({"url": st.url, "hub": st.hub, "seed": st.seed, "home": st.home, "guard": st.guard}))
    stop = Path(str(state) + ".stop")
    while not stop.exists():
        time.sleep(1)
    stop.unlink()
state.unlink(missing_ok=True)
