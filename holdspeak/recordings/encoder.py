"""ffmpeg, off the loop: one webm in, one iPhone-ready mp4 and a poster out.

``ffmpeg -i in.webm -vf "scale='min(1280,iw)':-2" -c:v libx264 -preset
veryfast -crf 28 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 64k
out.mp4``: H.264, AAC and faststart, so iPhone Safari plays it inline and
"Save Video" works. The progress comes from ``-progress pipe:1``
(``out_time_us``) over the recording's own wall-clock length: a browser webm
carries no duration header.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

#: The places Homebrew and the system put ffmpeg (a hub started by launchd
#: may have no Homebrew PATH).
FFMPEG_CANDIDATES = ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg")


def ffmpeg_path() -> Optional[str]:
    """``HOLDSPEAK_FFMPEG`` (tests; ``none`` = absent), else PATH, else Homebrew."""
    override = os.environ.get("HOLDSPEAK_FFMPEG", "").strip()
    if override:
        return None if override.lower() in {"none", "off", "0"} else override
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in FFMPEG_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def encode_command(ffmpeg: str, source: Path, target: Path) -> list[str]:
    return [
        ffmpeg, "-y", "-hide_banner", "-nostats", "-loglevel", "error",
        "-progress", "pipe:1",
        "-i", str(source),
        "-vf", "scale='min(1280,iw)':-2",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "64k",
        str(target),
    ]


def poster_command(ffmpeg: str, source: Path, target: Path, at: float) -> list[str]:
    return [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{max(0.0, at):.2f}", "-i", str(source),
        "-frames:v", "1", "-vf", "scale=480:-2", str(target),
    ]


def encode(
    ffmpeg: str,
    source: Path,
    target: Path,
    *,
    total_s: float,
    on_progress: Callable[[int], None] = lambda _pct: None,
) -> tuple[bool, str]:
    """Encode ``source`` into ``target``. Returns ``(ok, error words)``."""
    partial = target.with_name(target.stem + ".part" + target.suffix)
    log_path = target.with_name("encode.log")
    total_us = max(1.0, float(total_s) * 1_000_000)
    last = -1
    try:
        with log_path.open("wb") as log:
            proc = subprocess.Popen(
                encode_command(ffmpeg, source, partial),
                stdout=subprocess.PIPE, stderr=log, stdin=subprocess.DEVNULL,
            )
            assert proc.stdout is not None
            for raw in proc.stdout:
                line = raw.decode("utf-8", "ignore").strip()
                if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
                    try:
                        done = float(line.split("=", 1)[1])
                    except ValueError:
                        continue
                    pct = max(0, min(99, int(done * 100 / total_us)))
                    if pct != last:
                        last = pct
                        on_progress(pct)
            code = proc.wait()
    except OSError as exc:
        return False, f"ffmpeg did not start: {exc}"
    if code != 0 or not partial.exists() or partial.stat().st_size == 0:
        tail = ""
        try:
            tail = log_path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-1:][0]
        except (OSError, IndexError):
            pass
        partial.unlink(missing_ok=True)
        return False, f"ffmpeg stopped ({code}){': ' + tail[:160] if tail else ''}"
    os.replace(partial, target)
    on_progress(100)
    return True, ""


def poster(ffmpeg: str, source: Path, target: Path, *, duration_s: float) -> bool:
    """One frame at 2 s (at 0 s for a shorter recording); a failure is no poster."""
    at = 2.0 if duration_s > 2.5 else 0.0
    try:
        done = subprocess.run(
            poster_command(ffmpeg, source, target, at),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0 and target.exists()


__all__ = ["encode", "encode_command", "ffmpeg_path", "poster", "poster_command"]
