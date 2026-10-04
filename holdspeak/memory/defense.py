"""Memory defense: redact secrets before a text is hashed, stored or embedded.

One action only: redact.  No block, no policy file (MEMORY-DESIGN.md §5).
The patterns are the send-receipt scrubber's set
(``services/channel_contract.py``) plus PEM keys, JWTs, database URLs that
carry a password, and card numbers that pass a Luhn check.
"""
from __future__ import annotations

import re

REDACTED = "[redacted]"

_SECRET = re.compile(
    r"(?i)(bearer\s+\S+|(?:token|password|passwd|secret|api[_-]?key|authorization)\s*[=:]\s*(?:bearer\s+)?\S+"
    r"|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}|xox[abprs]-[A-Za-z0-9-]{10,}"
    r"|SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}|ATATT[A-Za-z0-9_=-]{16,}"
    r"|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})"
)
_PEM = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)",
    re.DOTALL,
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_DB_URL = re.compile(
    r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqp)://[^\s:/@]+:[^\s@/]+@\S+",
    re.IGNORECASE,
)
_CARD = re.compile(r"(?<![\d-])\d(?:[ -]?\d){12,18}(?![\d-])")


def _luhn(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _card(match: re.Match[str]) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    return REDACTED if 13 <= len(digits) <= 19 and _luhn(digits) else match.group(0)


def redact(text: str) -> str:
    """Return ``text`` with every secret shape replaced by ``[redacted]``."""
    value = str(text or "")
    value = _PEM.sub(REDACTED, value)
    value = _DB_URL.sub(REDACTED, value)
    value = _JWT.sub(REDACTED, value)
    value = _SECRET.sub(REDACTED, value)
    return _CARD.sub(_card, value)


__all__ = ["REDACTED", "redact"]
