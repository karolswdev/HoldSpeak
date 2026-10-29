"""The Line as a service on its machine (LINE-3): the systemd user unit, the
launchd agent, and the pinned user-space baresip build. Unit tier: no network,
nothing is installed or started."""
from __future__ import annotations

import plistlib
import re
from pathlib import Path

from holdspeak.line import install
from holdspeak.line.supervisor import FORBIDDEN, MODULES

SCRIPT = Path(install.BUILD_SCRIPT)
PY = "/home/karol/holdspeak-line/venv/bin/python"


def test_the_systemd_unit_runs_the_venvs_line_and_restarts_only_on_failure() -> None:
    text = install.systemd_unit(PY, env={"HOLDSPEAK_LINE_HOME": "/home/karol/holdspeak-line/state",
                                         "HOLDSPEAK_LINE_BIND": "100.118.33.80"})
    lines = text.splitlines()
    assert "ExecStart=/home/karol/holdspeak-line/venv/bin/holdspeak line run" in lines
    assert "Restart=on-failure" in lines and "RestartSec=5" in lines
    assert "WantedBy=default.target" in lines
    assert 'Environment="HOLDSPEAK_LINE_BIND=100.118.33.80"' in lines
    assert 'Environment="HOLDSPEAK_LINE_HOME=/home/karol/holdspeak-line/state"' in lines
    # A user unit: no User=, no root, and no other unit is named.
    assert not any(line.startswith(("User=", "Group=")) for line in lines)
    assert "llama" not in text and "sudo" not in text
    assert install.UNIT_NAME == "holdspeak-line.service"


def test_the_launchd_agent_is_a_valid_plist_that_restarts_only_after_a_failed_exit() -> None:
    python = "/Users/karol/.holdspeak/line/venv/bin/python"
    text = install.launchd_plist(python, env={"HF_HOME": "/Users/karol/.cache/hf"}, log_path="/tmp/line.log")
    plist = plistlib.loads(text.encode("utf-8"))
    assert plist["Label"] == "com.holdspeak.line"
    assert plist["ProgramArguments"] == ["/Users/karol/.holdspeak/line/venv/bin/holdspeak", "line", "run"]
    assert plist["KeepAlive"] == {"SuccessfulExit": False} and plist["RunAtLoad"] is True
    assert plist["EnvironmentVariables"] == {"HF_HOME": "/Users/karol/.cache/hf", "PYTHONUNBUFFERED": "1"}
    assert plist["StandardErrorPath"] == "/tmp/line.log"


def test_the_service_uses_a_python_the_speech_has_wheels_for(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOLDSPEAK_LINE_HOME", str(tmp_path))
    assert install.node_python("/x/python") == "/x/python"
    monkeypatch.setattr(install, "python_ok", lambda python: False)  # the hub's 3.14
    assert install.node_python() == str(tmp_path / "venv" / "bin" / "python")
    assert install.NODE_PYTHON == "3.13"


def test_the_build_script_pins_the_versions_and_builds_bsd_modules_only() -> None:
    text = SCRIPT.read_text()
    assert re.search(r'^BARESIP_VERSION="4\.12\.0"$', text, re.M)
    assert re.search(r'^LIBRE_VERSION="4\.12\.0"$', text, re.M)
    assert re.search(r'^BARESIP_SHA256="710d79d60c15c09f0aeb93e5d2f219e7f12ab93f62cab826e4280592a1ea155f"$', text, re.M)
    assert re.search(r'^LIBRE_SHA256="707b6194dd3b8d3fb1641ca08a0999aaac1d38d36b5c45514777a13ded311923"$', text, re.M)
    assert "sha256sum -c" in text
    modules = re.search(r'^MODULES="([^"]+)"$', text, re.M).group(1).split(";")
    assert tuple(modules) == MODULES  # the build list is the load list
    assert not set(modules) & set(FORBIDDEN)
    # No command runs sudo or apt (a message may name the owner's sudo press).
    code = [line for line in text.splitlines() if not line.lstrip().startswith(("#", "echo"))]
    assert not any(re.search(r"(^|[;&|(]\s*)(sudo|apt|apt-get)\b", line.strip()) for line in code)
    assert 'id -u)" = "0"' in text  # it refuses to run as root
    assert SCRIPT.stat().st_mode & 0o111


def test_linger_off_is_named_as_the_owners_one_press(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setenv("HOLDSPEAK_LINE_HOME", str(tmp_path))
    monkeypatch.setenv("USER", "karol")
    monkeypatch.setattr(install.platform, "system", lambda: "Linux")
    monkeypatch.setattr(install.subprocess, "run", lambda args, **kw: calls.append(args) or _Done())
    monkeypatch.setattr(install, "linger_on", lambda: False)
    done = install.install_unit(PY)
    assert done["kind"] == "systemd" and done["presses"] == ["sudo loginctl enable-linger karol"]
    assert (tmp_path / "holdspeak-line.service").exists()
    assert calls == [["systemctl", "--user", "enable", str(tmp_path / "holdspeak-line.service")],
                     ["systemctl", "--user", "restart", "holdspeak-line.service"]]


class _Done:
    returncode = 0
    stdout = ""
