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
#: A URL with a user and password, redacted up to the ``@``, or to the end of
#: the text when a cut took the ``@host`` away.
_URL_USERINFO = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^\s/@:]+:[^\s/@]*(@|\Z)")
#: ``Basic dXNlcjpwYXNz`` with no header name (``curl -H 'Basic ...'``). The
#: value must look like base64 (a digit, a ``=`` pad, or both letter cases),
#: so "Basic authentication failed" stays.
_BASIC = re.compile(r"(?<![A-Za-z])(basic\s+)([A-Za-z0-9+/]{8,}={0,2})(?![A-Za-z0-9+/=])", re.IGNORECASE)
_DIGIT = re.compile(r"\d")

#: The ``connector_watches.last_error`` column cap.
SOURCE_ERROR_CAP = 1000


def _auth_value(match: re.Match[str]) -> str:
    value = match.group(2)
    quote = value[:1] if value[:1] in {'"', "'"} else ""
    return match.group(1) + (f"{quote}{REDACTED}{quote}" if quote else REDACTED)


def _basic(match: re.Match[str]) -> str:
    value = match.group(2)
    if _DIGIT.search(value) or value.endswith("=") or (value != value.lower() and value != value.upper()):
        return match.group(1) + REDACTED
    return match.group(0)


def redact_secrets(text: object) -> str:
    """``text`` with every credential shape replaced by ``[redacted]``.
    Give it the whole text: cut it after, never before."""
    value = str(text if text is not None else "")
    if not value:
        return ""
    value = _AUTH_VALUE.sub(_auth_value, value)
    value = _URL_USERINFO.sub(lambda m: m.group(1) + REDACTED + m.group(2), value)
    value = _BASIC.sub(_basic, value)
    return redact(value)


def redact_error(text: object, limit: int | None = None) -> str:
    """A CLI's stderr, an HTTP error body or ``str(exc)`` made safe to
    raise, log, store and return: redacted whole, stripped, then cut to
    ``limit``."""
    value = redact_secrets(text).strip()
    return value[:limit] if limit is not None else value


def redact_source_error(error: object) -> str:
    """A Watch's raw read error made safe to store and show: redacted whole,
    then cut to the column cap. The helper #1093 named; every provider error
    text in ``services/*_provider.py`` and ``watch_sources.py`` uses it."""
    return redact_secrets(error)[:SOURCE_ERROR_CAP]


__all__ = ["REDACTED", "SOURCE_ERROR_CAP", "redact_error", "redact_secrets", "redact_source_error"]
