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


#: A key block with no header: three or more lines of base64 in a row.  A
#: source can hold the body of a key and not its ``-----BEGIN`` line.
_BLOB = re.compile(r"(?:^|(?<=\n))[ \t]*(?:[A-Za-z0-9+/]{40,}={0,2}[ \t]*(?:\n|$)[ \t]*){3,}")

#: Each pattern runs only when a word it needs is in the text.  A plain
#: substring test over a long transcript costs far less than the pattern.
_SECRET_WORDS = (
    "bearer", "token", "password", "passwd", "secret", "api", "authorization",
    "ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_", "xox", "sg.", "atatt",
    "sk-", "akia",
)
_DIGIT = re.compile(r"\d")
_LONG_WORD = re.compile(r"[A-Za-z0-9+/]{40}")


def redaction_spans(text: str) -> list[tuple[int, int]]:
    """Where the secrets are in ``text``: merged ``(start, end)`` spans.

    Every pattern reads the WHOLE text, so a secret of many lines (a key
    block) is one span however the text is cut afterwards.
    """
    value = str(text or "")
    if not value:
        return []
    spans: list[tuple[int, int]] = []
    if "-----BEGIN" in value:
        spans.extend(match.span() for match in _PEM.finditer(value))
    if "://" in value:
        spans.extend(match.span() for match in _DB_URL.finditer(value))
    if "eyJ" in value:
        spans.extend(match.span() for match in _JWT.finditer(value))
    lowered = value.casefold()
    if any(word in lowered for word in _SECRET_WORDS):
        spans.extend(match.span() for match in _SECRET.finditer(value))
    if _DIGIT.search(value):
        spans.extend(match.span() for match in _CARD.finditer(value) if _card(match) == REDACTED)
    if _LONG_WORD.search(value):
        spans.extend(
            (match.start(), match.start() + len(match.group(0).rstrip()))
            for match in _BLOB.finditer(value)
        )
    if not spans:
        return []
    spans.sort()
    merged = [spans[0]]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _apply(text: str, spans: list[tuple[int, int]], offset: int = 0) -> str:
    """``text`` (which starts at ``offset`` of the whole) with each span
    replaced.  A span that started before this piece still redacts the part
    of it that is here."""
    out: list[str] = []
    cursor = 0
    end_of_text = len(text)
    for start, end in spans:
        start, end = start - offset, end - offset
        if end <= 0 or start >= end_of_text:
            continue
        start, end = max(start, 0), min(end, end_of_text)
        out.append(text[cursor:start])
        out.append(REDACTED)
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def redact(text: str) -> str:
    """Return ``text`` with every secret shape replaced by ``[redacted]``.

    Give it the COMPLETE text.  A piece cut out of a text can hold part of a
    secret that no pattern knows; cut the snippet from what this returns.
    """
    value = str(text or "")
    spans = redaction_spans(value)
    return _apply(value, spans) if spans else value


def redact_parts(parts: list[str]) -> tuple[list[str], bool]:
    """Redact a text that is held as parts (a title, then the turns of a
    transcript or the paragraphs of a note) as ONE text, and give the parts
    back.  A secret that runs across parts is redacted in each of them.
    Returns ``(parts, changed)``.
    """
    texts = [str(part or "") for part in parts]
    joined = "\n".join(texts)
    spans = redaction_spans(joined)
    if not spans:
        return texts, False
    out: list[str] = []
    offset = 0
    for text in texts:
        out.append(_apply(text, spans, offset))
        offset += len(text) + 1
    return out, True


__all__ = ["REDACTED", "redact", "redact_parts", "redaction_spans"]
