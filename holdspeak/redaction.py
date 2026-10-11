"""One redactor for the error text a CLI or an HTTP service gives back.

A provider (acli, gh, an email API, a Slack webhook, a model server) can echo
a credential in its stderr or its response body: a token, an Authorization
header, a password in a URL. That text goes into ServiceError messages,
logs, stored rows, send receipts and MCP tool results that agents read.
Every such text goes through this module first.

Two rules at every site: redact the WHOLE text first, then cut (a cut can
hide a secret's shape); never cut raw text that may hold a secret.

The patterns are the memory redactor's set (``holdspeak/memory/defense.py``)
plus three shapes it leaves alone (PHILO-17 evalerror, Astra r1 and r2; the
helper moved here from ``holdspeak/db/automations.py``, which still exports
it): an Authorization value of any scheme, a ``Basic`` credential with no
header name, and a URL with a user and a password. Cause words stay ("run:
gh auth login"), so the owner still sees what to do.
"""
from __future__ import annotations

import re

from holdspeak.memory.defense import REDACTED, redact

#: An Authorization (or Proxy-Authorization) value of ANY scheme -- header
#: ``:``, ``=`` or a JSON key -- is redacted whole: a quoted value to its
#: closing quote, else to the end of the line.
_AUTH_VALUE = re.compile(
    r"""(?im)(["']?\b(?:proxy-)?authorization["']?\s*[:=]\s*)("[^"\n]*"?|'[^'\n]*'?|[^\n]*)"""
)
#: A URL with a user and a password, redacted up to the ``@``, or to the end
#: of the text when a cut took the ``@host`` away (#1093). A ``host:port``
#: is not userinfo: a run of digits after the ``:`` that ends the URL or the
#: text stays, so ``http://127.0.0.1:8080`` keeps its diagnosis. Only the
#: scheme is bounded (at most 32 characters, so a long ``a-a-a-...`` run
#: cannot make the scan quadratic); the user and the password are not, so a
#: long password is never abandoned (Astra r2).
_URL_USERINFO = re.compile(
    r"(?i)(?<![A-Za-z0-9+.-])([a-z][a-z0-9+.-]{0,31}://)[^\s/@:]+:"
    r"(?![0-9]{1,5}(?:[/?#\s]|\Z))[^\s/@]*(@|\Z)"
)
#: ``Basic dXNlcjpwYXNz`` with no header name (``curl -H 'Basic ...'``).
_BASIC = re.compile(r"(?<![A-Za-z])(basic\s+)([A-Za-z0-9+/]{8,}={0,2})(?![A-Za-z0-9+/=])", re.IGNORECASE)
#: A label in quotes, as JSON or a Python dict prints it: ``"api_key":"..."``,
#: ``'password': '...'``, ``"access_token": bare``, and the same with escaped
#: quotes (``\\"api_key\\":\\"...\\"``, a JSON text inside a JSON string).
#: The memory redactor needs the ``:`` straight after the label, so the
#: closing quote hid these. The value parts are unbounded and linear: a
#: match starts only at a quote before a label, so no bound is needed and a
#: long value is never abandoned (Astra r2). An unclosed quoted value runs
#: to the end of the line: a cut text keeps none of it.
_QUOTED_LABEL = re.compile(
    r"""(?i)(\\?["'])([A-Za-z0-9_-]*(?:token|password|passwd|secret|api[_-]?key|apikey|credential))\1"""
    r"""(\s*[:=]\s*)(\\"(?:[^"\\\n]|\\(?!"))*(?:\\")?|"(?:[^"\\\n]|\\.)*"?|'[^'\n]*'?|[^\s,}\]]+)"""
)
#: Values after a quoted label that are not secrets.
_PLAIN_VALUES = frozenset({"null", "none", "true", "false", ""})
_DIGIT = re.compile(r"\d")

#: The ``connector_watches.last_error`` column cap.
SOURCE_ERROR_CAP = 1000


def _auth_value(match: re.Match[str]) -> str:
    value = match.group(2)
    quote = value[:1] if value[:1] in {'"', "'"} else ""
    return match.group(1) + (f"{quote}{REDACTED}{quote}" if quote else REDACTED)


def _basic(match: re.Match[str]) -> str:
    """Redact a base64-shaped credential, never an English word: it needs a
    digit, a ``+``, ``/`` or ``=``, or a capital letter after the first
    character in a value that is not all capitals ("dXNlcjpwYXNz" is
    redacted; "Authentication", "AUTHENTICATION", "authentication" stay)."""
    value = match.group(2)
    if (_DIGIT.search(value) or any(c in value for c in "+/=")
            or (not value.isupper() and any(c.isupper() for c in value[1:]))):
        return match.group(1) + REDACTED
    return match.group(0)


def _quoted_label(match: re.Match[str]) -> str:
    value = match.group(4)
    core = value.strip("\\\"'")
    if core.casefold() in _PLAIN_VALUES or core.isdigit():
        return match.group(0)
    head = match.group(1) + match.group(2) + match.group(1) + match.group(3)
    for quote in ('\\"', '"', "'"):
        if value.startswith(quote):
            closed = len(value) >= 2 * len(quote) and value.endswith(quote)
            return head + quote + REDACTED + (quote if closed else "")
    return head + REDACTED


def redact_secrets(text: object) -> str:
    """``text`` with every credential shape replaced by ``[redacted]``.
    Give it the whole text: cut it after, never before."""
    value = str(text if text is not None else "")
    if not value:
        return ""
    value = _AUTH_VALUE.sub(_auth_value, value)
    value = _QUOTED_LABEL.sub(_quoted_label, value)
    value = _URL_USERINFO.sub(lambda m: m.group(1) + REDACTED + m.group(2), value)
    value = _BASIC.sub(_basic, value)
    return redact(value)


#: The most text a redacted result keeps (P2 6).
SCAN_BOUND = 65536
#: The most text one scan reads. The patterns are linear, so the WHOLE text
#: up to this cap is redacted BEFORE any cut (Astra r2: a cut at 64k could
#: split a quoted secret). Past the cap the text is cut at its last white
#: space first, so the cut never leaves the head of a secret.
HARD_CAP = 1024 * 1024


def _cut_at_space(value: str, at: int) -> str:
    """``value[:at]`` without its last word (a linear ``rfind``)."""
    head = value[:at]
    space = max(head.rfind(" "), head.rfind("\n"), head.rfind("\t"))
    return head[: space + 1] if space >= 0 else ""


def redact_bounded(text: object, bound: int = SCAN_BOUND) -> str:
    """Like :func:`redact_secrets`, with a bounded result: the text (up to
    :data:`HARD_CAP`) is redacted whole, then cut to ``bound`` with a
    marker."""
    value = str(text if text is not None else "")
    if len(value) > HARD_CAP:
        value = _cut_at_space(value, HARD_CAP)
        cut = True
    else:
        cut = False
    out = redact_secrets(value)
    if len(out) > bound or cut:
        total = len(str(text if text is not None else ""))
        return out[:bound] + f" [cut: {total} characters in all]"
    return out


def redact_error(text: object, limit: int | None = None) -> str:
    """A CLI's stderr, an HTTP error body or ``str(exc)`` made safe to
    raise, log, store and return: redacted whole, stripped, then cut to
    ``limit``."""
    value = redact_bounded(text).strip()
    return value[:limit] if limit is not None else value


def redact_source_error(error: object) -> str:
    """A Watch's raw read error made safe to store and show: redacted whole,
    then cut to the column cap. The helper #1093 named; every provider error
    text in ``services/*_provider.py`` and ``watch_sources.py`` uses it."""
    return redact_bounded(error)[:SOURCE_ERROR_CAP]


__all__ = [
    "HARD_CAP", "REDACTED", "SCAN_BOUND", "SOURCE_ERROR_CAP", "redact_bounded", "redact_error", "redact_secrets",
    "redact_source_error",
]
