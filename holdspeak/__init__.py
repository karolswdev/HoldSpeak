"""HoldSpeak - Voice typing for macOS and Linux. Hold, speak, release."""

from __future__ import annotations

import os

# HS-60-06 (a real production finding): llama.cpp's GGML installs a signal
# handler that spawns `lldb --batch -o bt -o quit -p <pid>` on ANY in-process
# fault — including benign Mach exceptions other runtimes (MLX Metal,
# onnxruntime) handle internally. The attach SUSPENDS every thread, which
# wedged live transcription mid-flight for minutes during the wake-word
# closeout. A debugger auto-attach has no place in a user-facing audio
# runtime; a genuinely fatal fault should crash visibly instead. Must be set
# before llama_cpp first loads, hence the package root.
os.environ.setdefault("GGML_NO_BACKTRACE", "1")


def _resolve_version() -> str:
    """Return the one true version.

    The package metadata written from `pyproject.toml` is the single source of
    truth. An editable install (`uv pip install -e .`) registers that metadata,
    so this resolves correctly for both installed and source-tree runs. The
    fallback only matters when running from a raw checkout that was never
    installed; there we read the version straight out of `pyproject.toml`.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("holdspeak")
        except PackageNotFoundError:
            pass
    except Exception:
        pass

    try:
        import re
        from pathlib import Path

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
        if match:
            return match.group(1)
    except Exception:
        pass

    return "0.0.0+unknown"


__version__ = _resolve_version()
