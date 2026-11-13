"""The one writer of Telegram messages.

Every message HoldSpeak sends to Telegram is built here: plain structure in,
the Bot API payload out. One parse mode (HTML, escaped here and nowhere
else), one length rule, one button-data rule, one "decided" edit.

A caller gives plain words. It never writes a tag, never escapes, never cuts a
text and never builds ``reply_markup`` by hand. ``telegram_reach.fence`` stays
in front: the writer asks for it on every piece of text (``fenced``).
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

#: Telegram refuses a message longer than this.
MAX_TEXT = 4096
#: Telegram refuses callback data longer than this (bytes).
MAX_BUTTON_DATA = 64
#: The lines after the body (the link, the closing lines) take at most this
#: much of a message that must be cut, so that they cannot push the body out.
MAX_TAIL = MAX_TEXT // 4
MORE_WORDS = "More on your desk"
OPEN_PAGE_WORDS = "Open the page"
OPEN_DESK_WORDS = "Open it on your desk."
PARSE_MODE = "HTML"


class WriterRefused(ValueError):
    """The message cannot be written as asked (a button's data is too long)."""


@dataclass(frozen=True)
class Button:
    text: str
    data: str


@dataclass(frozen=True)
class Message:
    """One message in plain words.

    ``head`` is the first line (drawn bold). ``lines`` are body lines.
    ``facts`` are (label, value) pairs: what a held call will write.
    ``question`` is what the owner is asked (drawn bold). ``link`` is the
    page on his desk. ``closing`` are plain lines after the link.
    """

    head: str = ""
    lines: Sequence[str] = ()
    facts: Sequence[tuple[str, str]] = ()
    question: str = ""
    buttons: Sequence[Sequence[Button]] = ()
    link: Optional[str] = None
    link_words: str = OPEN_PAGE_WORDS
    desk_words: Optional[str] = None  # the line that stands in for a link when there is none
    closing: Sequence[str] = field(default_factory=tuple)


def esc(text: Any) -> str:
    """THE one escape for Telegram's HTML parse mode."""
    return html.escape(str(text if text is not None else ""), quote=False)


def keyboard(rows: Sequence[Sequence[Button]]) -> list[list[dict[str, str]]]:
    """The inline keyboard. A button whose data is over Telegram's limit is
    refused here: Telegram would refuse the whole message."""
    out: list[list[dict[str, str]]] = []
    for row in rows:
        made: list[dict[str, str]] = []
        for button in row:
            if len(button.data.encode("utf-8")) > MAX_BUTTON_DATA:
                raise WriterRefused(f"button data is over {MAX_BUTTON_DATA} bytes")
            made.append({"text": button.text, "callback_data": button.data})
        if made:
            out.append(made)
    return out


def _pieces(message: Message, fenced: Callable[[str], str]) -> list[tuple[str, str]]:
    """(plain, html) for each line, in order. ``fenced`` runs on each plain
    piece before it is escaped."""
    out: list[tuple[str, str]] = []
    if message.head:
        head = fenced(message.head)
        out.append((head, f"<b>{esc(head)}</b>"))
    for line in message.lines:
        plain = fenced(str(line))
        out.append((plain, esc(plain)))
    for label, value in message.facts:
        label_plain, value_plain = fenced(str(label)), fenced(str(value))
        out.append((f"{label_plain}: {value_plain}", f"<b>{esc(label_plain)}:</b> {esc(value_plain)}"))
    if message.question:
        question = fenced(message.question)
        out.append((question, f"<b>{esc(question)}</b>"))
    return out


def _link(message: Message, fenced: Callable[[str], str]) -> Optional[str]:
    """The link as it may be sent. The link is put to the fence as every
    other piece is (review T2); a link that the fence changes held a secret
    (a password or a token in its query): it is not sent as a link."""
    if not message.link:
        return None
    link = str(message.link)
    return link if fenced(link) == link else None


def _tail(message: Message, fenced: Callable[[str], str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    link = _link(message, fenced)
    if link:
        words = fenced(message.link_words)
        out.append((f"{words}: {link}", f"{esc(words)}: {esc(link)}"))
    elif message.desk_words or message.link:
        words = fenced(message.desk_words or OPEN_DESK_WORDS)
        out.append((words, esc(words)))
    for line in message.closing:
        plain = fenced(str(line))
        out.append((plain, esc(plain)))
    return out


def _more(link: Optional[str]) -> tuple[str, str]:
    if link:
        return (f"{MORE_WORDS}: {link}", f"{esc(MORE_WORDS)}: {esc(link)}")
    return (f"{MORE_WORDS}.", f"{esc(MORE_WORDS)}.")


def write(message: Message, *, fenced: Callable[[str], str] = lambda text: text) -> tuple[str, str]:
    """``(plain, html)``. The html is what Telegram gets; the plain text is
    what the desk keeps as "what was sent". A message over Telegram's limit
    is cut at a line, never inside a word, and ends with ``MORE_WORDS``. The
    WHOLE message is bounded: the lines after the link too (a closing line
    that does not fit is not sent)."""
    body, tail = _pieces(message, fenced), _tail(message, fenced)
    rows = body + tail
    if len("\n".join(row[1] for row in rows)) <= MAX_TEXT:
        return "\n".join(row[0] for row in rows), "\n".join(row[1] for row in rows)
    link = _link(message, fenced)
    more = _more(link)
    # The link is in the "more" line: the tail's own link line is not said twice.
    after: list[tuple[str, str]] = []
    left = MAX_TEXT - len(more[1])
    room = MAX_TAIL
    for row in tail:
        if link and row[0].endswith(link):
            continue
        if len(row[1]) + 1 > room:
            break
        after.append(row)
        room -= len(row[1]) + 1
        left -= len(row[1]) + 1
    kept: list[tuple[str, str]] = []
    for row in body:
        if len(row[1]) + 1 > left:
            break
        kept.append(row)
        left -= len(row[1]) + 1
    rows = kept + [more] + after
    return "\n".join(row[0] for row in rows), "\n".join(row[1] for row in rows)


def payload(chat_id: Any, message: Message, *, fenced: Callable[[str], str] = lambda text: text,
            buttons: bool = True) -> tuple[dict[str, Any], str]:
    """The ``sendMessage`` parameters and the plain text of what they say."""
    plain, text = write(message, fenced=fenced)
    params: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": PARSE_MODE,
                              "disable_web_page_preview": True}
    rows = keyboard(message.buttons) if buttons else []
    if rows:
        params["reply_markup"] = {"inline_keyboard": rows}
    return params, plain


def edit_payload(chat_id: Any, message_id: Any, message: Message, *,
                 fenced: Callable[[str], str] = lambda text: text,
                 keep_buttons: bool = False) -> tuple[dict[str, Any], str]:
    """The ``editMessageText`` parameters. Buttons go unless ``keep_buttons``."""
    plain, text = write(message, fenced=fenced)
    params: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "text": text,
                              "parse_mode": PARSE_MODE, "disable_web_page_preview": True}
    if keep_buttons:
        params["reply_markup"] = {"inline_keyboard": keyboard(message.buttons)}
    return params, plain


def decided(head: str, words: str, link: Optional[str] = None) -> Message:
    """The one "decided" edit: the head, the page, the outcome. No buttons."""
    return Message(head=head, link=link, closing=(words,))


def from_buttons(rows: Sequence[Sequence[Mapping[str, str]]]) -> tuple[tuple[Button, ...], ...]:
    """Rows in the Bot API's own shape, as ``Button`` rows."""
    return tuple(tuple(Button(str(b["text"]), str(b["callback_data"])) for b in row) for row in rows)
