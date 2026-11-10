"""Encode search-box text as data, never SQLite query syntax."""


def fts_literal(text: str) -> str:
    """An FTS5 phrase, including punctuation and operator words as text.

    FTS still applies its tokenizer (for example, follow-up is two tokens).
    Doubling embedded quotes also makes an unfinished quote ordinary text.
    A phrase with no tokens simply matches nothing.
    """
    return '"' + text.replace('"', '""') + '"'


def like_literal(text: str) -> str:
    """A contains pattern for SQL using ``LIKE ? ESCAPE '\\'``."""
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
