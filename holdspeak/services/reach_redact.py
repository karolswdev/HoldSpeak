"""One redaction for every line Reach sends or shows (Astra's post-merge
check, 2026-11-01; ruling the same day).

Every Telegram message and every briefing page line goes through
:func:`reach_line`:

- the secret shapes of ``memory.defense.redact`` (keys, tokens, URLs with a
  password, cards);
- a password-shaped pair (``password: x``, ``token=x``, ``api_key x``): the
  value is hidden;
- a home folder path (``/Users/<name>/…``, ``/home/<name>/…`` and this
  machine's own home) reads ``~/…``;
- a diff or patch header (``diff --git …``, ``--- a/…``, ``+++ b/…``,
  ``@@ … @@``) anywhere in a line reads "a change".
"""
from __future__ import annotations

import os
import re
from typing import Any

HIDDEN = "[hidden]"
CHANGE = "a change"

_PASSWORD = re.compile(
    r"(?i)\b(pass(?:word|wd|phrase)?|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)s?"
    r"(\s*[:=]\s*|\s+is\s+|\s+)(?!\[hidden\]|\[redacted\])([^\s,;]+)")
_HOME = re.compile(r"(?<![\w.~])/(?:Users|home)/[^/\s:'\"`)]+")
_DIFF = re.compile(r"diff --git \S+(?: \S+)?|(?<!\S)(?:---|\+\+\+) (?:a|b)/\S+|@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")


def reach_line(text: Any) -> str:
    """``text`` as Reach may send or show it (see the module note)."""
    from ..memory.defense import redact

    value = redact(str(text or ""))
    home = os.path.expanduser("~")
    if home and home not in ("/", "~"):
        value = value.replace(home.rstrip("/") + "/", "~/")
        value = re.sub(re.escape(home.rstrip("/")) + r"(?![\w/])", "~", value)
    value = _HOME.sub("~", value)
    value = _DIFF.sub(CHANGE, value)

    def _hide(match: re.Match[str]) -> str:
        word, between, secret = match.group(1), match.group(2), match.group(3)
        if between.strip() == "" and not re.search(r"\d", secret) and len(secret) < 12:
            return match.group(0)  # "token of thanks", "secret plan": plain words
        return f"{word}{between}{HIDDEN}"

    return _PASSWORD.sub(_hide, value)


def reach_value(value: Any, *, skip: frozenset[str] = frozenset({"ref", "id", "program_id", "step_id", "desk",
                                                                   "url", "pr_url", "path", "token"})) -> Any:
    """Every string in a page answer through :func:`reach_line` (ids, refs
    and links kept)."""
    if isinstance(value, str):
        return reach_line(value)
    if isinstance(value, list):
        return [reach_value(item, skip=skip) for item in value]
    if isinstance(value, dict):
        return {key: (item if key in skip else reach_value(item, skip=skip)) for key, item in value.items()}
    return value


__all__ = ["CHANGE", "HIDDEN", "reach_line", "reach_value"]
