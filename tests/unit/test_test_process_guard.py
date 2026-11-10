"""A test process leak is attributed and killed, rather than hidden."""
import subprocess
import sys

from tests._process_guard import ProcessGuard


def test_session_guard_reaps_and_names_a_leaked_child(monkeypatch, tmp_path):
    guard = ProcessGuard()
    test = "test_leaker.py::test_leak"
    monkeypatch.setenv("PYTEST_CURRENT_TEST", test + " (call)")
    guard.paths[test] = str(tmp_path)
    guard.install()
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        leaks = guard.finish(str(tmp_path / "no-tmux"))
        assert len(leaks) == 1
        assert test in leaks[0] and str(tmp_path) in leaks[0]
        assert child.wait(timeout=5) != 0
    finally:
        subprocess.Popen.__init__ = guard.original
        if child.poll() is None:
            child.kill()
            child.wait()


def test_session_guard_finds_a_detached_child_after_its_parent_exits(monkeypatch, tmp_path):
    import os

    guard = ProcessGuard()
    test = "test_leaker.py::test_detached"
    monkeypatch.setenv("PYTEST_CURRENT_TEST", test + " (call)")
    guard.paths[test] = str(tmp_path)
    marker = tmp_path / "child.pid"
    guard.install()
    try:
        subprocess.run([
            sys.executable, "-c",
            "import os, signal, sys; from pathlib import Path; "
            "pid = os.fork(); "
            "Path(sys.argv[1]).write_text(str(pid)) if pid else signal.pause()",
            str(marker),
        ], check=True)
        pid = int(marker.read_text())
        leaks = guard.finish(str(tmp_path / "no-tmux"))
        assert any(f"pid={pid} " in leak and test in leak and str(tmp_path) in leak for leak in leaks), leaks
    finally:
        subprocess.Popen.__init__ = guard.original
        if marker.exists():
            try:
                os.kill(int(marker.read_text()), 9)
            except ProcessLookupError:
                pass
