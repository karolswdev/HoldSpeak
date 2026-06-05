#!/usr/bin/env python
"""Capture native desktop presence screenshots for Phase 40 evidence.

This is an end-to-end harness: it starts the real desktop presence host, drives
runtime activity events through it, and uses macOS `screencapture` to capture
the top-right transient window region for each state.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from holdspeak.desktop_presence import (  # noqa: E402
    DesktopPresenceHost,
    TkPresenceRenderer,
    build_presence_window_view,
)
from scripts.desktop_presence_smoke import build_activities  # noqa: E402


DEFAULT_OUTPUT_ROOT = (
    ROOT
    / "pm/roadmap/holdspeak/phase-40-runtime-presence-indicators/evidence/native-presence-shots"
)


def _desktop_bounds() -> tuple[int, int, int, int]:
    output = subprocess.check_output(
        [
            "osascript",
            "-e",
            'tell application "Finder" to get bounds of window of desktop',
        ],
        text=True,
    ).strip()
    values = [int(part.strip()) for part in output.split(",")]
    if len(values) != 4:
        raise RuntimeError(f"Unexpected desktop bounds: {output!r}")
    return values[0], values[1], values[2], values[3]


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")


CaptureMode = Literal["auto", "macos", "rendered"]


def _capture_region(path: Path, region: tuple[int, int, int, int]) -> bool:
    x, y, width, height = region
    result = subprocess.run(
        ["screencapture", "-x", f"-R{x},{y},{width},{height}", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    path.unlink(missing_ok=True)
    message = (result.stderr or result.stdout or "").strip()
    print(f"screencapture unavailable for {path.name}: {message}", file=sys.stderr)
    return False


def _render_view_png(path: Path, view: object) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width = 452
    height = 196
    image = Image.new("RGB", (width, height), "#07090d")
    draw = ImageDraw.Draw(image)

    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 18)
        body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 13)
        mono_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 11)
    except Exception:
        label_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        mono_font = ImageFont.load_default()

    visible = bool(getattr(view, "visible"))
    if not visible:
        draw.rounded_rectangle((24, 42, width - 24, 138), radius=12, fill="#111318", outline="#2b303a")
        draw.ellipse((46, 70, 78, 102), outline="#8b95a7", width=3)
        draw.text((94, 68), "Ready", fill="#f5f7fb", font=label_font)
        draw.text((94, 94), "Desktop hidden while idle.", fill="#c8ced8", font=body_font)
        draw.text((94, 120), "Runtime  Desktop hidden", fill="#8b95a7", font=mono_font)
        image.save(path)
        return

    accent = str(getattr(view, "accent"))
    draw.rounded_rectangle((24, 34, width - 24, 156), radius=12, fill="#111318", outline="#343946")
    draw.ellipse((48, 64, 72, 88), fill=accent, outline=accent)
    draw.text((92, 56), str(getattr(view, "label")), fill="#f5f7fb", font=label_font)
    detail = str(getattr(view, "detail"))
    if len(detail) > 72:
        detail = detail[:71].rstrip() + "..."
    draw.text((92, 84), detail, fill="#c8ced8", font=body_font)
    event = str(getattr(view, "event"))
    mode = str(getattr(view, "mode"))
    draw.text((92, 118), f"{event}  {mode}", fill="#ff8a4c", font=mono_font)
    image.save(path)


def _write_contact_sheet(output_dir: Path, shots: list[dict[str, object]]) -> None:
    from PIL import Image, ImageDraw, ImageFont

    thumbs: list[tuple[dict[str, object], Image.Image]] = []
    for shot in shots:
        image = Image.open(output_dir / str(shot["file"])).convert("RGB")
        image.thumbnail((452, 196))
        thumbs.append((shot, image.copy()))

    if not thumbs:
        return

    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 15)
    except Exception:
        label_font = ImageFont.load_default()

    columns = 2
    cell_width = 500
    cell_height = 250
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#07090d")
    draw = ImageDraw.Draw(sheet)

    for index, (shot, image) in enumerate(thumbs):
        col = index % columns
        row = index // columns
        x = col * cell_width + 24
        y = row * cell_height + 22
        title = f"{index + 1:02d}. {shot['state']} · {shot['mode']} · {shot['capture_method']}"
        draw.text((x, y), title, fill="#f5f7fb", font=label_font)
        sheet.paste(image, (x, y + 30))

    sheet.save(output_dir / "contact-sheet.png")


def _default_region() -> tuple[int, int, int, int]:
    _left, top, right, _bottom = _desktop_bounds()
    width = 452
    height = 196
    x = max(0, right - width - 16)
    y = max(0, top + 36)
    return x, y, width, height


def capture_presence_shots(output_dir: Path, settle_seconds: float, capture_mode: CaptureMode) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    region = _default_region()
    manifest: dict[str, object] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "capture_region": {
            "x": region[0],
            "y": region[1],
            "width": region[2],
            "height": region[3],
        },
        "requested_capture_mode": capture_mode,
        "shots": [],
    }

    host = DesktopPresenceHost(TkPresenceRenderer())
    shots: list[dict[str, object]] = []
    try:
        for index, activity in enumerate(build_activities(), start=1):
            state = str(activity.get("state") or "idle")
            view = build_presence_window_view(activity)
            host.handle_activity(activity)
            time.sleep(settle_seconds)

            filename = f"{index:02d}-{_safe_name(state)}-{view.mode}.png"
            path = output_dir / filename
            capture_method = "rendered"
            if capture_mode in {"auto", "macos"}:
                captured = _capture_region(path, region)
                if captured:
                    capture_method = "macos_screencapture"
                elif capture_mode == "macos":
                    raise RuntimeError("macOS screencapture failed")
                else:
                    _render_view_png(path, view)
            else:
                _render_view_png(path, view)
            shots.append(
                {
                    "state": state,
                    "source": activity.get("source"),
                    "label": view.label,
                    "detail": view.detail,
                    "event": view.event,
                    "visible": view.visible,
                    "mode": view.mode,
                    "capture_method": capture_method,
                    "file": filename,
                }
            )
    finally:
        host.close()

    manifest["shots"] = shots
    _write_contact_sheet(output_dir, shots)
    manifest["contact_sheet"] = "contact-sheet.png"
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        help="Directory for PNG screenshots and manifest.json.",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.45,
        help="Seconds to wait after each activity before capture.",
    )
    parser.add_argument(
        "--capture-mode",
        choices=("auto", "macos", "rendered"),
        default="auto",
        help="Use macOS screencapture, generated renderer PNGs, or auto fallback.",
    )
    args = parser.parse_args()
    return capture_presence_shots(args.output_dir, args.settle, args.capture_mode)


if __name__ == "__main__":
    raise SystemExit(main())
