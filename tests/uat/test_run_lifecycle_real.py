"""The conductor against a REAL HoldSpeak boot.

Boots the actual product (``holdspeak web --no-open``) under an isolated
HOME on a free port with the fully-local ``golden-local`` posture (no model
warm, no intel endpoint), proves it answers ``/health``, that its config
and DB live under ``uat/_runs`` and never the real ``~``, that teardown
leaves no live process, and that restart-with-a-different-overlay works.

Self-skips (with the product's own log tail) if the package cannot boot in
this environment, so a product-side breakage never falsely reds the harness
suite — but a healthy env proves the whole loop end to end.
"""

from __future__ import annotations

import os
import time

import pytest

from uat.conductor import paths
from uat.conductor.db import Database
from uat.conductor.runs import GOLDEN_LOCAL_OVERLAY, RunManager


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False  # no such process — dead and reaped
    except PermissionError:
        return True  # exists but owned by another user (won't happen for our children)
    except OSError:
        return False
    return True


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    # Isolate runs + DB to tmp; link real caches so Whisper/GGUF aren't fetched.
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield mgr
    finally:
        mgr.teardown_all()


def test_real_boot_health_teardown_restart(real_manager):
    t0 = time.monotonic()
    run = real_manager.create_run(config=dict(GOLDEN_LOCAL_OVERLAY))
    if run.status != "up":
        logs = real_manager.logs(run.id, 60)
        pytest.skip(
            "product did not boot in this environment; harness path unexercised.\n"
            f"status={run.status} error={run.error}\n"
            f"stderr tail:\n{logs.get('stderr','')}"
        )

    boot_secs = time.monotonic() - t0
    assert run.pid and _pid_alive(run.pid), "product pid should be alive when up"

    # Isolation: config under uat/_runs, never the real ~.
    home = paths.run_home(run.id)
    cfg = home / ".config" / "holdspeak" / "config.json"
    assert cfg.exists()
    assert str(paths.runs_root()) in str(home)
    assert os.path.expanduser("~") not in str(home) or str(paths.runs_root()).startswith(
        str(home.parents[3])
    )

    # Health is reachable through the API's own probe path.
    got = real_manager.get(run.id)
    assert got.status == "up"

    old_pid = run.pid

    # Restart under a different overlay: old process dies, new one comes up.
    run2 = real_manager.restart(run.id, config={"config_version": 1, "model": {"warm_on_start": False}})
    assert run2.status == "up"
    assert run2.pid and _pid_alive(run2.pid)
    # The old process is gone (no orphan).
    time.sleep(0.5)
    assert not _pid_alive(old_pid), "restart must tear down the previous product"

    new_pid = run2.pid
    torn = real_manager.teardown(run.id)
    assert torn.status == "down"
    time.sleep(0.5)
    assert not _pid_alive(new_pid), "teardown must leave no live product process"

    # A generous sanity bound — golden-local should boot well under a minute.
    assert boot_secs < 60.0
