"""A path as a face shows it: the home folder reads as ``~``.

One rule for every face that must show a path (a saved Send folder, a SAVED
receipt, a Setup check): the owner's home folder is ``~`` on any HOME, macOS
or Linux, in its given and its resolved form. A path outside HOME stays
whole. The stored value never changes; only what a face reads does.
"""
from __future__ import annotations

import os
import re


def _homes() -> tuple[str, ...]:
    expanded = os.path.abspath(os.path.expanduser("~"))
    resolved = os.path.realpath(expanded)
    # The longer form first, so /private/var/... wins over /var/... on macOS.
    return tuple(sorted({expanded, resolved}, key=len, reverse=True))


def home_display(path: str) -> str:
    """One path, with the home folder as ``~``."""
    if not path:
        return path
    for candidate in dict.fromkeys((path, os.path.realpath(path))):
        for home in _homes():
            if candidate == home:
                return "~"
            if candidate.startswith(home + os.sep):
                return "~" + candidate[len(home):]
    return path


def home_text(text: str) -> str:
    """Every home path inside a line of text, with the home folder as ``~``."""
    if not text:
        return text
    for home in _homes():
        if home in ("", os.sep):
            continue
        # Only where a path STARTS with HOME: at the start of the text or
        # after a space, a quote, `(`, `=`, `,` or `;`, and followed by `/`
        # or the end of the path. A path that only CONTAINS HOME
        # (`/backup` + HOME + `/desk.db`) stays whole (Astra, #869 P2).
        text = re.sub(
            r"(?:(?<=^)|(?<=[\s'\"`(=,;]))" + re.escape(home) + r"(?=" + re.escape(os.sep) + r"|[\s;:,)'\"`]|$)",
            "~", text,
        )
    return text
