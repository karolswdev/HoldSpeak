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
#: text stays, so ``http://127.0.0.1:8080`` keeps its diagnosis. The scheme
#: is bounded (at most 32 characters) so a long ``a-a-a-...`` run cannot
#: make the scan quadratic.
_URL_USERINFO = re.compile(
    r"(?i)(?<![A-Za-z0-9+.-])([a-z][a-z0-9+.-]{0,31}://)[^\s/@:]{1,256}:"
    r"(?![0-9]{1,5}(?:[/?#\s]|\Z))[^\s/@]{0,512}(@|\Z)"
)
#: ``Basic dXNlcjpwYXNz`` with no header name (``curl -H 'Basic ...'``).
_BASIC = re.compile(r"(?<![A-Za-z])(basic\s+)([A-Za-z0-9+/]{8,}={0,2})(?![A-Za-z0-9+/=])", re.IGNORECASE)
#: A label in quotes, as JSON or a Python dict prints it: ``"api_key":"..."``,
#: ``'password': '...'``, ``"access_token": bare``. The memory redactor needs
#: the ``:`` straight after the label, so the closing quote hid these.
_QUOTED_LABEL = re.compile(
    r"""(?i)(["'])([A-Za-z0-9_-]{0,40}(?:token|password|passwd|secret|api[_-]?key|apikey|credential))\1"""
    r"""(\s{0,8}[:=]\s{0,8})("(?:[^"\\\n]|\\.){0,4096}"|'[^'\n]{0,4096}'|[^\s,}\]]{1,4096})"""
)
#: Values after a quoted label that are not secrets.
_PLAIN_VALUES = frozenset({"null", "none", "true", "false", '""', "''"})
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
    if value.casefold() in _PLAIN_VALUES or value.isdigit():
        return match.group(0)
    quote = value[:1] if value[:1] in {'"', "'"} else ""
    return match.group(1) + match.group(2) + match.group(1) + match.group(3) + quote + REDACTED + quote


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


#: The most text one scan reads (P2 6: a bounded cost per call).
SCAN_BOUND = 65536
_TRAILING_WORD = re.compile(r"\S+\Z")


def redact_bounded(text: object, bound: int = SCAN_BOUND) -> str:
    """Like :func:`redact_secrets`, but a text longer than ``bound`` is cut
    at ``bound`` first and ends in a marker. The last word before the cut is
    dropped too, so the cut never leaves the head of a secret that no
    pattern knows any more."""
    value = str(text if text is not None else "")
    if len(value) <= bound:
        return redact_secrets(value)
    head = _TRAILING_WORD.sub("", value[:bound])
    return redact_secrets(head) + f" [cut: {len(value) - len(head)} more characters]"


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
    "REDACTED", "SCAN_BOUND", "SOURCE_ERROR_CAP", "redact_bounded", "redact_error", "redact_secrets",
    "redact_source_error",
]
