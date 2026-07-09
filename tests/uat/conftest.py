"""Fixtures for the UAT harness tests.

Every test runs against a throwaway runs-root and DB (env overrides read by
``uat.conductor.paths``), and cache-linking is off so a suite never reaches
into the real ``~``. A ``FakeProduct`` lets the run state machine be tested
deterministically without booting the real product; the real boot lives in
``test_run_lifecycle_real.py`` (marked, self-skipping).
"""

from __future__ import annotations

import pytest

from uat.conductor import runs as runs_mod
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    runs_root = tmp_path / "_runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UAT_RUNS_ROOT", str(runs_root))
    monkeypatch.setenv("UAT_DB_PATH", str(runs_root / "uat.db"))
    monkeypatch.setenv("UAT_REAL_HOME", str(tmp_path / "fake_real_home"))
    yield


class FakeProduct:
    """A drop-in for ProductProcess that simulates boot without a subprocess.

    ``FakeProduct.boot_ok`` (class attr) toggles whether ``wait_healthy``
    returns True, so a test can drive both the ``up`` and ``failed`` paths.
    """

    boot_ok = True
    instances: list["FakeProduct"] = []

    def __init__(self, *, home, port, host="127.0.0.1", log_dir, extra_env=None):
        self.home = home
        self.port = port
        self.host = host
        self.log_dir = log_dir
        self._started = False
        self._alive = False
        self._pid = 4242 + len(FakeProduct.instances)
        self.stopped = False
        FakeProduct.instances.append(self)
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "product.stdout.log").write_text("fake boot log\n")
        (log_dir / "product.stderr.log").write_text(
            "" if self.boot_ok else "fake boot error: endpoint refused\n"
        )

    def start(self):
        self._started = True
        self._alive = self.boot_ok

    @property
    def pid(self):
        return self._pid if self._started else None

    def is_alive(self):
        return self._alive

    def wait_healthy(self, timeout=45.0, interval=0.4):
        return self.boot_ok

    def stop(self, grace=6.0):
        self._alive = False
        self.stopped = True

    def tail(self, n=80):
        return {
            "stdout": (self.log_dir / "product.stdout.log").read_text(),
            "stderr": (self.log_dir / "product.stderr.log").read_text(),
        }

    @property
    def proc(self):
        class _P:
            def poll(_self):
                return None if self._alive else 1

        return _P()


@pytest.fixture
def fake_products(monkeypatch):
    FakeProduct.instances = []
    FakeProduct.boot_ok = True
    monkeypatch.setattr(runs_mod, "ProductProcess", FakeProduct)
    return FakeProduct


@pytest.fixture
def manager(fake_products):
    return RunManager(Database(), boot_timeout=1.0, link_caches=False)
