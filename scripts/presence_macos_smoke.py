#!/usr/bin/env python3
"""HS-41-04 smoke + screenshot for the macOS presence renderer.

Starts a real HoldSpeak web server (so /presence + /ws work), brings up the
native NSPanel + WKWebView HUD + the NSStatusItem glyph on the main thread,
drives a couple of states, verifies the frontmost app is NOT stolen, and
captures:

- the HUD panel window (by window number)
- a strip of the menu bar showing the glyph

    uv run python scripts/presence_macos_smoke.py <out-dir>

Requires the `presence` extra (pyobjc Cocoa + WebKit) and a GUI session.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def main(out_dir: str) -> int:
    import holdspeak.config as config_module
    from holdspeak.desktop_presence_cocoa import _CocoaPresenceUI
    from holdspeak.runtime_activity import RuntimeActivityTracker
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

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
        )
    )
    url = server.start()
    time.sleep(1.0)

    import AppKit

    # Who is frontmost *before* we show the HUD?
    ws = AppKit.NSWorkspace.sharedWorkspace()
    before = ws.frontmostApplication()
    before_name = before.localizedName() if before else "?"

    ui = _CocoaPresenceUI(f"{url}/presence")
    ui.show(activity)
    # Let the WKWebView load + render the card, pumping the runloop.
    for _ in range(40):
        ui.pump(0.05)
    time.sleep(0.3)

    # Focus-safety: a non-activating panel must NOT steal frontmost.
    after = ws.frontmostApplication()
    after_name = after.localizedName() if after else "?"
    focus_stolen = bool(before and after and before.processIdentifier() != after.processIdentifier())
    print(f"frontmost before: {before_name} | after: {after_name} | focus_stolen: {focus_stolen}")

    win_id = int(ui.panel.windowNumber())
    panel_png = out / "macos_presence_hud.png"
    subprocess.run(
        ["screencapture", "-x", "-o", f"-l{win_id}", str(panel_png)], check=False
    )

    # A menu-bar strip to show the status-item glyph (top-right).
    screen = AppKit.NSScreen.mainScreen().frame()
    sw = int(screen.size.width)
    glyph_png = out / "macos_presence_glyph.png"
    subprocess.run(
        ["screencapture", "-x", "-o", f"-R{sw - 360},0,360,40", str(glyph_png)],
        check=False,
    )

    ui.hide()
    ui.pump(0.2)
    server.stop()

    ok = (
        panel_png.exists()
        and panel_png.stat().st_size > 0
        and not focus_stolen
    )
    print(f"panel: {panel_png} ({panel_png.stat().st_size if panel_png.exists() else 0} B)")
    print(f"glyph: {glyph_png} ({glyph_png.stat().st_size if glyph_png.exists() else 0} B)")
    print(f"SMOKE {'PASSED' if ok else 'FAILED'} (focus not stolen + HUD captured)")
    return 0 if ok else 1


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    raise SystemExit(main(out_dir))
