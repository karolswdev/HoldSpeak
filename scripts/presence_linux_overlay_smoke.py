#!/usr/bin/env python3
"""HS-41-08 live smoke for the Linux GTK-WebKit overlay (cross-host).

Runs on the Mac: starts a HoldSpeak web server bound to the LAN (so /presence is
reachable), ships the presence modules to a Linux box, brings up the GTK overlay
there pointed at the Mac's /presence, captures the floating HUD window region,
and pulls the screenshot back.

    uv run python scripts/presence_linux_overlay_smoke.py <linux-host> <mac-lan-ip> <out.png>
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

REMOTE_DRIVER = r'''
import sys, time, subprocess
sys.path.insert(0, "/tmp/hs")
from holdspeak.desktop_presence_gtk import GtkOverlayRenderer, gtk_overlay_available
print("overlay_available:", gtk_overlay_available(), flush=True)
r = GtkOverlayRenderer(lambda: "%(base)s")
r.show()
time.sleep(3.2)  # let WebKit2 load + render the /presence card
subprocess.run(["import", "-window", "root", "-crop", "460x165+%(cropx)d+26", "/tmp/hs_overlay.png"], check=False)
r.close()
print("captured", flush=True)
'''


def main(linux_host: str, mac_ip: str, out_path: str) -> int:
    import holdspeak.config as config_module
    from holdspeak.runtime_activity import RuntimeActivityTracker
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    config_module.CONFIG_FILE = Path(tempfile.mkdtemp()) / "config.json"
    tracker = RuntimeActivityTracker()
    activity = tracker.update(
        "transcribing",
        source="hotkey",
        detail="Turning your speech into text…",
        last_event="dictation_transcribing",
    )
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=lambda: {"activity": activity, "runtime": {"activity": activity}},
        ),
    )  # loopback (no auth) — reached from the Linux box via an SSH reverse tunnel
    url = server.start()
    port = url.rsplit(":", 1)[-1].rstrip("/")
    fwd = 8899
    base = f"http://127.0.0.1:{fwd}"  # the .43 end of the reverse tunnel
    time.sleep(1.0)
    print(f"server on {url}; reverse-tunneled to {linux_host}:{fwd}")
    _ = mac_ip

    ssh = ["ssh", "-o", "BatchMode=yes", linux_host]
    ssh_fwd = ["ssh", "-o", "BatchMode=yes", "-R", f"{fwd}:127.0.0.1:{port}", linux_host]
    repo = Path(__file__).parent.parent
    mods = [
        "__init__.py", "logging_config.py", "runtime_activity.py",
        "desktop_presence.py", "desktop_presence_freedesktop.py", "desktop_presence_gtk.py",
    ]
    try:
        subprocess.run(ssh + ["rm -rf /tmp/hs && mkdir -p /tmp/hs/holdspeak"], check=True)
        subprocess.run(
            ["scp", "-o", "BatchMode=yes"]
            + [str(repo / "holdspeak" / m) for m in mods]
            + [f"{linux_host}:/tmp/hs/holdspeak/"],
            check=True,
        )
        driver = REMOTE_DRIVER % {"base": base, "cropx": 1920 - 460}
        remote = (
            'export DISPLAY=:0 XAUTHORITY="$HOME/.Xauthority" '
            'DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"; '
            f"python3 - <<'PY'\n{driver}\nPY"
        )
        out = subprocess.run(ssh_fwd + [remote], capture_output=True, text=True, timeout=60)
        print(out.stdout.strip())
        if out.stderr.strip():
            print("stderr:", out.stderr.strip()[:400])
        subprocess.run(
            ["scp", "-o", "BatchMode=yes", f"{linux_host}:/tmp/hs_overlay.png", out_path],
            check=False,
        )
        subprocess.run(ssh + ["rm -rf /tmp/hs /tmp/hs_overlay.png"], check=False)
    finally:
        server.stop()

    ok = Path(out_path).exists() and Path(out_path).stat().st_size > 0
    print(f"{'WROTE ' + out_path if ok else 'NO CAPTURE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: presence_linux_overlay_smoke.py <linux-host> <mac-lan-ip> <out.png>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
