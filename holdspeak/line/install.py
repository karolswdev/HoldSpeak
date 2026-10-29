"""The Line on a machine: its credential, its build, its service (LINE-3).

- **The credential** (``<line home>/credential.json``, 0600): the hub URL,
  the node's name and the node token the hub minted at enrolment
  (``holdspeak line enrol``). The custody is the node link's
  (``holdspeak/delivery/node_credentials.py``): a no-follow, owner-only read
  and an atomic write.
- **The build** on Linux: ``scripts/line/build-baresip-linux.sh`` (user
  space, the versions pinned, BSD modules only, no sudo).
- **The node venv**: the Line's speech needs onnxruntime, which has no wheel
  for every Python the hub runs on (the hub's venv on the Mac is CPython
  3.14). ``holdspeak line install`` makes ``<line home>/venv`` with uv and
  Python 3.13 and installs ``holdspeak[line]`` from the hub's checkout. A
  machine whose own venv is Python 3.13 or older (the box) can use that one.
- **The service**: a systemd user unit on Linux, a launchd agent on the Mac,
  for this user only, no sudo. It runs ``holdspeak line run``; a node with no
  credential exits 0 ("Not enrolled"), so the service does not loop.
  On Linux a user unit runs after a reboot only with linger on:
  ``loginctl enable-linger`` is the owner's one press when it is off.
"""
from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from xml.sax.saxutils import escape

from .supervisor import state_dir

UNIT_NAME = "holdspeak-line.service"
AGENT_LABEL = "com.holdspeak.line"
#: The newest Python the Line's speech has wheels for (onnxruntime).
NODE_PYTHON = "3.13"
REPO = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO / "scripts" / "line" / "build-baresip-linux.sh"
#: What the service passes on, when set in the shell that installs it.
PASSED_ENV = ("HOLDSPEAK_LINE_HOME", "HOLDSPEAK_LINE_BIND", "HOLDSPEAK_LINE_SIP_PORT", "HOLDSPEAK_BARESIP",
              "HOLDSPEAK_LINE_SOCK_DIR", "HF_HOME")


# ── the credential ────────────────────────────────────────────────────


def credential_path(home: Optional[Path] = None) -> Path:
    return Path(home or state_dir()) / "credential.json"


def save_credential(hub: str, node: str, token: str, *, home: Optional[Path] = None) -> Path:
    from ..delivery.node_credentials import exclusive_custody_lock, write_private_document

    path = credential_path(home)
    with exclusive_custody_lock(path):
        write_private_document(path, {"line_credential_schema": 1, "hub": hub.rstrip("/"), "node": node,
                                      "node_token": token})
    return path


def load_credential(*, home: Optional[Path] = None) -> Optional[dict[str, str]]:
    """``{hub, node, node_token}``, or ``None`` when this machine is not enrolled."""
    from ..delivery.node_credentials import read_private_document

    document = read_private_document(credential_path(home))
    if not document:
        return None
    out = {key: str(document.get(key) or "") for key in ("hub", "node", "node_token")}
    return out if all(out.values()) else None


def forget_credential(*, home: Optional[Path] = None) -> bool:
    path = credential_path(home)
    if not path.exists():
        return False
    path.unlink()
    return True


def default_node_name() -> str:
    name = socket.gethostname().split(".")[0].strip().lower()
    return "".join(c if c.isalnum() or c == "-" else "-" for c in name)[:32] or "line"


# ── the build (Linux) ─────────────────────────────────────────────────


def build_baresip_linux(prefix: Optional[Path] = None) -> int:
    """Run the pinned user-space build. Its exit code (3: a header or a tool is
    missing, and installing it needs sudo: the owner's press)."""
    if os.geteuid() == 0:
        print("Do not build the Line as root.")
        return 2
    args = ["bash", str(BUILD_SCRIPT)] + ([str(prefix)] if prefix else [])
    return subprocess.run(args, check=False).returncode


# ── the node venv ─────────────────────────────────────────────────────


def venv_dir(home: Optional[Path] = None) -> Path:
    return Path(home or state_dir()) / "venv"


def venv_python(venv: Path) -> Path:
    return Path(venv) / "bin" / "python"


def python_ok(python: str) -> bool:
    """True when that Python is 3.13 or older (onnxruntime has its wheel)."""
    try:
        out = subprocess.run([python, "-c", "import sys;print(sys.version_info[1])"], capture_output=True,
                             text=True, timeout=20)
        return out.returncode == 0 and 10 <= int(out.stdout.strip()) <= 13
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def make_venv(checkout: Path, *, venv: Optional[Path] = None) -> Path:
    """``<line home>/venv`` on Python 3.13 with ``holdspeak[line]`` from the
    checkout (editable, so a hub update is the node's update)."""
    target = Path(venv or venv_dir())
    py = venv_python(target)
    if py.exists() and python_ok(str(py)):
        pass
    else:
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("uv is not installed: https://docs.astral.sh/uv/")
        subprocess.run([uv, "python", "install", NODE_PYTHON], check=True)
        subprocess.run([uv, "venv", "--python", NODE_PYTHON, str(target)], check=True)
    uv = shutil.which("uv")
    if uv:
        subprocess.run([uv, "pip", "install", "--python", str(py), "-e", f"{checkout}[line]"], check=True)
    else:
        subprocess.run([str(py), "-m", "pip", "install", "-e", f"{checkout}[line]"], check=True)
    return py


# ── the service ───────────────────────────────────────────────────────


def _passed_env(extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = {key: os.environ[key] for key in PASSED_ENV if os.environ.get(key)}
    env.update({k: v for k, v in (extra or {}).items() if v})
    return env


def _launcher(python: str) -> list[str]:
    """``holdspeak line run`` from that venv (the console script beside python)."""
    script = Path(python).parent / "holdspeak"
    return [str(script), "line", "run"]


def systemd_unit(python: str, *, env: Optional[dict[str, str]] = None) -> str:
    """The unit file. ``Restart=on-failure``: a clean exit (not enrolled, or
    ``HOLDSPEAK_LINE=off``) stays stopped; ``llama-qwen.service`` and every
    other unit are never named."""
    lines = [
        "[Unit]",
        "Description=HoldSpeak Line (this machine's phone line)",
        "After=network-online.target",
        "Wants=network-online.target",
        "",
        "[Service]",
        "Type=simple",
        "ExecStart=" + " ".join(_launcher(python)),
        "Restart=on-failure",
        "RestartSec=5",
        "Environment=PYTHONUNBUFFERED=1",
    ]
    lines += [f'Environment="{key}={value}"' for key, value in sorted((env or {}).items())]
    lines += ["", "[Install]", "WantedBy=default.target", ""]
    return "\n".join(lines)


def launchd_plist(python: str, *, env: Optional[dict[str, str]] = None, log_path: str = "") -> str:
    """The launchd agent. ``KeepAlive`` starts it again only after a failed exit."""
    args = "".join(f"<string>{escape(part)}</string>" for part in _launcher(python))
    env_xml = "".join(f"\n      <key>{escape(k)}</key><string>{escape(v)}</string>"
                      for k, v in sorted({"PYTHONUNBUFFERED": "1", **(env or {})}.items()))
    logs = ""
    if log_path:
        logs = (f"\n    <key>StandardOutPath</key><string>{escape(log_path)}</string>"
                f"\n    <key>StandardErrorPath</key><string>{escape(log_path)}</string>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>{AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>{args}</array>
    <key>EnvironmentVariables</key>
    <dict>{env_xml}
    </dict>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key>
    <dict><key>SuccessfulExit</key><false/></dict>
    <key>ThrottleInterval</key><integer>5</integer>{logs}
  </dict>
</plist>
"""


def unit_file(home: Optional[Path] = None) -> Path:
    """Where the unit text is kept: the Line's own folder (systemd links it)."""
    return Path(home or state_dir()) / UNIT_NAME


def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{AGENT_LABEL}.plist"


def linger_on() -> Optional[bool]:
    user = os.environ.get("USER") or ""
    try:
        out = subprocess.run(["loginctl", "show-user", user, "-p", "Linger"], capture_output=True, text=True,
                             timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip().endswith("yes") if out.returncode == 0 else None


def install_unit(python: str, *, start: bool = True) -> dict[str, Any]:
    """Write and enable the service for this user; what was done, and the
    owner's presses left."""
    env = _passed_env()
    presses: list[str] = []
    if platform.system() == "Darwin":
        path = plist_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        log_path = str(state_dir() / "line.log")
        path.write_text(launchd_plist(python, env=env, log_path=log_path))
        if start:
            domain = f"gui/{os.getuid()}"
            subprocess.run(["launchctl", "bootout", f"{domain}/{AGENT_LABEL}"], capture_output=True)
            subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=False)
        return {"kind": "launchd", "path": str(path), "presses": presses}
    path = unit_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(systemd_unit(python, env=env))
    subprocess.run(["systemctl", "--user", "enable", str(path)], check=False)
    if start:
        subprocess.run(["systemctl", "--user", "restart", UNIT_NAME], check=False)
    if linger_on() is False:
        presses.append(f"sudo loginctl enable-linger {os.environ.get('USER') or ''}".strip())
    return {"kind": "systemd", "path": str(path), "presses": presses}


def restart_unit() -> bool:
    """Start the service again after an enrolment, when it is installed."""
    if platform.system() == "Darwin":
        if not plist_path().exists():
            return False
        subprocess.run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{AGENT_LABEL}"], check=False)
        return True
    if not unit_file().exists():
        return False
    subprocess.run(["systemctl", "--user", "restart", UNIT_NAME], check=False)
    return True


def node_python(explicit: str = "") -> str:
    """The Python the service runs: the one named, else this one when it is
    3.13 or older, else the node venv's."""
    if explicit:
        return explicit
    if python_ok(sys.executable):
        return sys.executable
    return str(venv_python(venv_dir()))


__all__ = [
    "AGENT_LABEL", "BUILD_SCRIPT", "NODE_PYTHON", "UNIT_NAME", "build_baresip_linux", "credential_path",
    "default_node_name", "forget_credential", "install_unit", "launchd_plist", "linger_on", "load_credential",
    "make_venv", "node_python", "plist_path", "python_ok", "restart_unit", "save_credential", "systemd_unit",
    "unit_file", "venv_dir", "venv_python",
]
