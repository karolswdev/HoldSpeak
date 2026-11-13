"""Telegram reach (PG-DIRECTION DIR5, DIRECTION-2026-10-31.md §5, §8; all defaults approved 2026-10-31).

- **One bot, one owner chat.** The Cadence bot is the reach bot. Pairing is
  a one-time code shown on the desk (six digits, ten minutes): the first chat
  that sends ``/pair <code>`` is the one owner chat; a second chat cannot pair
  while one is paired. **Unpair** removes it.
- **The secret in the keystore.** The bot token is in the keystore slot
  ``reach.telegram.bot_token`` (the one keystore, ``holdspeak/keystore.py``,
  or the rig's ``HOLDSPEAK_CHANNEL_KEYSTORE_FILE``), and so is the paired chat.
  :func:`repair_token` moves a token found in the config file into the
  keystore once and blanks it in the file, with one log line.
- **The message.** At most ten lines of plain text (no Markdown): the
  head, the brief's lines in the package's order (the goal, the step, what
  happened, the question: ``briefing_service`` composes them, the owner's
  BRIEF RULE of 2026-10-31), each choice with what it does, the page link. Inline buttons: the item's own choices and **Later**; Later opens a
  second row (1 h · 13:00 · Tonight · Tomorrow). A choice that cannot be
  undone (Merge; a Skip that drops a proposed requirement) asks a second tap
  in place, good for two minutes. After the answer the message edits itself:
  the buttons go and the last line says the outcome.
- **Replies as text**, by rule (no model): a choice's word, "yes", "no",
  "later 2h", "waive: …" (refused: the page), and any other sentence on a
  Program item is a shaping sentence (``program.shape``, preview) sent back
  with **Apply** · **Not this**.
- **What is never sent**: a secret (a title with one is redacted the Phone's
  way), a diff, a file's content, a brief, a transcript, a log, other
  people's notes. :func:`fence` checks every message before it leaves.
- **Each send is egress** (``run_external_egress``, connector
  ``reach-telegram``, the data class ``reach_package``); the record holds the
  destination ``telegram:<method>:<chat>`` and a digest of the payload, never
  the token.
- **Outbound only.** Updates come by long poll (``getUpdates``) in the reach
  thread (``reach_service.ReachService.start``); nothing polls when no chat is
  paired and no code is open. ``HOLDSPEAK_TELEGRAM=off`` (every rig) turns the
  poll and every send off.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Optional

from ..db.briefing import BriefingStore
from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from ..timestamps import utc_now_iso
from .errors import ServiceError
from .telegram_writer import (Button, Message, WriterRefused, edit_payload, from_buttons,
                              payload as message_payload, write as write_message)

log = get_logger("services.telegram_reach")

TELEGRAM_ENV = "HOLDSPEAK_TELEGRAM"
SERVICE = "HoldSpeak Reach"
TOKEN_SLOT = "reach.telegram.bot_token"
CHAT_SLOT = "reach.telegram.chat"
CONNECTOR = "reach-telegram"
#: The named destination (the egress ledger's words).
DESTINATION_WORDS = "Telegram · owner chat"
PAIR_MINUTES = 10
#: Wrong pairing codes before the code is void (Astra post-merge 2026-11-01).
PAIR_WRONG_MAX = 5
SECOND_TAP_SECONDS = 120
#: §5 said eight; the owner's BRIEF RULE (2026-10-31) adds the goal, the step,
#: what happened and what the answer blocks, so ten: head, four brief lines,
#: the blocked line, three choices, the link.
MAX_LINES = 10
MAX_LINE = 200
CALLBACK = "r1"
_API = "https://api.telegram.org/bot{token}/{method}"
_TOKEN_SHAPE = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{30,}$")
#: §5 "What is never sent": the shapes a message must not carry.
_NEVER = (
    re.compile(r"^(diff --git|@@ |\+\+\+ |--- a/)", re.M),
    re.compile(r"\b\d{5,}:[A-Za-z0-9_-]{30,}\b"),  # a bot token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
#: Irreversible choices: a second tap (§5, decision 2).
_SECOND_TAP = {("merge", "merge"), ("requirement_proposed", "skip")}
_WORD_ALIASES = {"not yet": "not_yet", "go on": "go_on", "fix now": "fix_now", "send back": "send_back",
                 "not met": "unmet"}

TELEGRAM_OWNER = Principal(PrincipalKind.OWNER, "telegram-owner-chat")

_lock = threading.RLock()
_repaired = False
_HUB_PORT: Optional[int] = None


class TelegramRefused(ServiceError):
    def __init__(self, code: str, detail: str, *, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


def telegram_on() -> bool:
    """``HOLDSPEAK_TELEGRAM=off``: no poll, no send (every rig hub)."""
    return os.environ.get(TELEGRAM_ENV, "on").strip().lower() not in {"off", "0", "false", "no"}


def remember_port(port: Optional[int]) -> None:
    """The hub's port, for the page link's tailnet address."""
    global _HUB_PORT
    _HUB_PORT = int(port) if port else None


def page_base() -> Optional[str]:
    """The hub's tailnet address, or None (no Serve, or a rig)."""
    try:
        from ..recordings.service import recordings_on
        from ..recordings.tailnet import tailnet_base

        return tailnet_base(_HUB_PORT) if _HUB_PORT and recordings_on() else None
    except Exception:
        return None


# ── the keystore ─────────────────────────────────────────────────────


class _Missing(Exception):
    pass


def _store() -> Any:
    """The one keystore's Reach slots (``holdspeak/keystore.py``), or None when it is not open."""
    from .. import keystore

    slots = keystore.Slots(SERVICE, _Missing, missing="missing", locked="locked", unavailable="unavailable")
    return slots if slots.available() else None


def _read(slot: str) -> str:
    store = _store()
    if store is None:
        return ""
    try:
        return str(store.get(slot) or "")
    except Exception:
        return ""


def _write(slot: str, value: str) -> None:
    store = _store()
    if store is None:
        raise TelegramRefused("keystore_unavailable", "The keystore is not open. Unlock it and try again.")
    store.put(slot, str(value or ""))


def bot_token() -> str:
    return _read(TOKEN_SLOT)


def token_where() -> str:
    """``keystore`` or ``missing`` (never the value)."""
    return "keystore" if bot_token() else "missing"


def paired_chat() -> Optional[dict[str, Any]]:
    raw = _read(CHAT_SLOT)
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) and value.get("id") else None


def repair_token(load_config: Optional[Callable[[], Any]] = None) -> bool:
    """One time on startup: a bot token in the config file moves into the
    keystore and is blanked in the file (one log line). With one allowed
    chat in the file and none paired, that chat becomes the paired one."""
    global _repaired
    with _lock:
        try:
            if load_config is None:
                from ..config import Config

                load_config = Config.load
            config = load_config()
        except Exception as exc:
            log.info(f"telegram: the config was not read for the token move ({type(exc).__name__})")
            return False
        section = getattr(config, "cadence_telegram", None)
        value = str(getattr(section, "bot_token", "") or "").strip()
        if not value:
            return False
        if _store() is None:
            if not _repaired:
                log.warning("telegram: the bot token is in the config file and the keystore is not open; "
                            "it stays there until the keystore opens")
                _repaired = True
            return False
        if not bot_token():
            _write(TOKEN_SLOT, value)
        chats = [str(chat) for chat in getattr(section, "allowed_chat_ids", []) or [] if str(chat).strip()]
        if len(chats) == 1 and paired_chat() is None:
            _write(CHAT_SLOT, json.dumps({"id": chats[0], "name": "", "at": utc_now_iso()}))
        section.bot_token = ""
        section.pairing_code = ""
        config.save()
        log.info("telegram: moved the bot token from the config file into the keystore")
        _repaired = True
        return True


def cadence_config(section: Any) -> Any:
    """The Cadence surface's config with the token from the keystore and the
    paired chat (the one bot; the config file no longer holds either)."""
    from copy import copy

    resolved = copy(section)
    token = bot_token()
    if token:
        resolved.bot_token = token
    chat = paired_chat()
    if chat:
        resolved.allowed_chat_ids = [str(chat["id"])]
    resolved.pairing_code = ""
    return resolved


# ── the transport ────────────────────────────────────────────────────

# The long poll. Telegram holds ``getUpdates`` open for LONG_POLL_SECONDS; the
# client must wait longer than that, or every quiet poll ends as a client
# timeout (an ``indeterminate`` egress record) and the loop polls again at
# once. The client timeout is derived from the long poll so the two cannot
# drift apart.
LONG_POLL_SECONDS = 25
LONG_POLL_CLIENT_TIMEOUT = LONG_POLL_SECONDS + 10
# Review 14a (2026-11-13): updates now arrive, a backlog too.
UPDATES_POLICY = "reach_telegram_updates"  # the cadence policy row that holds the read update ids
UPDATE_TRIES = 3            # a handler that raises is tried this many times, then the update is skipped
REMEMBERED_UPDATES = 200    # the newest read update ids kept, to know a replay after a restart
REPLY_SKEW_SECONDS = 60     # Telegram's clock and this machine's may differ by this much
NO_TARGET_WORDS = "Reply to the question you answer, or press its button. Nothing is decided."
OLD_MESSAGE_WORDS = "That message is older than the question. Nothing is decided. Answer the question again."
SKIPPED_WORDS = "One message here could not be read. Nothing was decided from it. Send it again."

# ── the setup state (durable) and its words ──────────────────────────
SETUP_POLICY = "reach_telegram_setup"  # the cadence policy row: the bot, the pairing code's hash, health, the last test
TEST_CALLBACK = "test"
TEST_BUTTON = "It works"
HALTED = ("token_revoked", "another_desk")  # the poll waits for the owner in these states
HEALTH_WORDS = {
    "connected": "Telegram answers.",
    "not_checked": "Telegram has not checked this token yet. The desk checks it at the next poll.",
    "token_revoked": "Telegram does not accept this token. Paste a new token.",
    "bot_blocked": "The bot cannot send to your chat. Open the bot in Telegram and press Start.",
    "another_desk": "Another HoldSpeak reads this bot. This desk does not read it until you use it here.",
    "unreachable": "Telegram does not answer. The desk tries again.",
    "no_token": "No bot token is saved.",
    "keystore_locked": "The keystore is not open. Unlock it, then read again.",
    "off": "Telegram is off on this desk.",
}
TOKEN_UNKNOWN_WORDS = "Telegram does not know this token. Nothing was saved. Copy the token from BotFather again."
NOT_CONNECTED_WORDS = "No chat is connected. Connect your chat, then send the test."
TEST_FAILED_WORDS = "The test was not sent."
BOT_CHANGED_WORDS = "This is not the bot that is saved here. Nothing was removed. Read again."
PAIR_NOT_SAVED_WORDS = "Pairing did not work: the desk could not save it. Make a new code in Settings ▸ Reach."
WAITS_FOR_OWNER = "telegram waits for the owner"
_OUTBOX_LOCK = threading.RLock()
OUTBOX_POLICY = "reach_telegram_outbox"  # the cadence policy row: messages that wait to be sent, and the keys sent
REMEMBERED_SENDS = 300      # the newest sent keys kept, so one key is never sent two times
OUTBOX_MAX = 200            # more than this waits for nothing: the oldest go, and the owner is told
RETRY_FIRST_SECONDS = 5
RETRY_CAP_SECONDS = 300
DROPPED_WORDS = "Telegram refused one message. It was not sent."
OUTBOX_FULL_WORDS = "Too many messages waited for Telegram. The oldest were not sent."


def call_reach(token: str, method: str, params: Mapping[str, Any], *, timeout: float = 10.0,
               data_class: str = "reach_package") -> dict[str, Any]:
    """POST to the Bot API through ``run_external_egress``. The token is
    joined into the URL here only; the record holds the destination and a
    digest of the payload."""
    from ..kernel.external_egress import run_external_egress

    url = _API.format(token=token, method=method)
    body = json.dumps(dict(params)).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    chat = str(params.get("chat_id") or "bot")
    destination = f"telegram:{method.lower()}:{chat.lower()}"
    try:
        response = run_external_egress(
            connector_id=CONNECTOR, destination=destination, data_classes=(data_class,),
            payload_material=dict(params), sender=urllib.request.urlopen, args=(request,),
            kwargs={"timeout": timeout}, allowed_destinations=(destination,),
        )
        with response:
            return json.loads(response.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as exc:
        answer: dict[str, Any] = {"ok": False, "error_code": int(exc.code), "description": str(exc.reason or "")}
        try:
            told = json.loads(exc.read().decode("utf-8", "replace") or "{}")
            if isinstance(told, dict):
                if told.get("description"):
                    answer["description"] = _redact(str(told["description"]), token)
                if isinstance(told.get("parameters"), dict):
                    answer["parameters"] = {"retry_after": told["parameters"].get("retry_after")}
        except Exception:
            pass
        return answer
    except Exception as exc:
        return {"ok": False, "description": _redact(str(exc), token)}


def _redact(text: str, token: str) -> str:
    return text.replace(token, "<token>") if token else text


def fence(text: str) -> str:
    """§5 "What is never sent": refuse a diff, a key or a token; redact a
    secret the Phone's way. Returns the text to send."""
    from ..redaction import redact_secrets
    from .reach_redact import reach_line

    # What is never sent at all is refused first; then the one Reach
    # redaction (a home path, a diff header anywhere in a line, a
    # password-shaped pair; Astra post-merge 2026-11-01).
    for pattern in _NEVER:
        if pattern.search(text):
            raise TelegramRefused("never_sent", "The message held something that is never sent to Telegram.")
    return redact_secrets(reach_line(text))


def _line(text: Any) -> str:
    words = " ".join(str(text or "").split())
    return words if len(words) <= MAX_LINE else words[: MAX_LINE - 1].rstrip() + "…"


def _waits(since: Any, now: datetime) -> str:
    try:
        at = datetime.fromisoformat(str(since).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return ""
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    minutes = max(0, int((now - at).total_seconds() // 60))
    return f"waits {minutes // 60} h" if minutes >= 60 else f"waits {max(1, minutes)} min"


def package_message(body: Mapping[str, Any], link: Optional[str], now: datetime,
                    buttons: Any = ()) -> Message:
    """The package in at most ten lines (§5 "The message"): the head, the
    brief's lines, each choice with what it does (as many as fit; the
    buttons carry every choice), the page link."""
    from .brief_words import brief_lines

    head = str(body.get("head") or "")
    waits = _waits(body.get("since"), now)
    lines = [_line(row) for row in brief_lines(body)][: MAX_LINES - 2]
    choices = list(body.get("choices") or [])
    room = MAX_LINES - 2 - len(lines)
    for choice in choices[: max(0, room)]:
        lines.append(_line(f"{choice['label']}: {choice['consequence']}"))
    return Message(head=_line(" · ".join(part for part in (head, waits) if part)), lines=tuple(lines),
                   link=link, desk_words="Open it on your desk.", buttons=buttons)


def render(body: Mapping[str, Any], link: Optional[str], now: datetime) -> str:
    """The plain words of ``package_message`` (what the desk keeps as sent)."""
    return fence(write_message(package_message(body, link, now), fenced=fence)[0])


def as_message(text: Any, keyboard: Optional[list[list[dict[str, str]]]] = None) -> Message:
    """Words as a ``Message``: one line is a line; more lines are a head and
    its lines. A ``Message`` passes through (with the keyboard, if given)."""
    rows = from_buttons(keyboard) if keyboard else ()
    if isinstance(text, Message):
        return text if not rows else Message(head=text.head, lines=text.lines, facts=text.facts,
                                             question=text.question, buttons=rows, link=text.link,
                                             link_words=text.link_words, desk_words=text.desk_words,
                                             closing=text.closing)
    lines = str(text or "").split("\n")
    if len(lines) > 1:
        return Message(head=lines[0], lines=tuple(lines[1:]), buttons=rows)
    return Message(lines=(lines[0],), buttons=rows)


def choice_buttons(package_id: str, body: Mapping[str, Any]) -> list[list[dict[str, str]]]:
    # DIRECTION §3: a page-only item (a prepared send) has no tap here; the
    # message links its page, where the preview names the destination.
    row = [] if body.get("page_only") else [
        {"text": choice["label"], "callback_data": f"{CALLBACK}|{package_id}|{choice['id']}"}
        for choice in body.get("choices") or []]
    row.append({"text": "Later ▾", "callback_data": f"{CALLBACK}|{package_id}|later"})
    return [row]


def later_buttons(package_id: str) -> list[list[dict[str, str]]]:
    from .reach_service import LATER_CHOICES, LATER_LABELS

    return [[{"text": LATER_LABELS[choice], "callback_data": f"{CALLBACK}|{package_id}|L:{choice}"}
             for choice in LATER_CHOICES],
            [{"text": "Back", "callback_data": f"{CALLBACK}|{package_id}|back"}]]


def _second_tap_words(body: Mapping[str, Any], choice: str) -> str:
    if body.get("kind") == "merge":
        pr = next((row.get("label") for row in body.get("evidence") or [] if row.get("pane") == "pr"), "")
        number = str(pr or "the PR").replace("PR ", "")
        return f"Merge {number} to main?"
    return "Skip the proposed requirement? It is dropped."


class TelegramReach:
    """The reach bot: pairing, briefs, button taps and text replies."""

    def __init__(self, db: Any, *, caller: Optional[Callable[..., dict[str, Any]]] = None,
                 briefing: Any = None, reach: Any = None, programs: Optional[Callable[[], Any]] = None,
                 clock: Callable[[], str] = utc_now_iso, link: Optional[Callable[[str], Optional[str]]] = None,
                 cadence: Optional[Callable[[], Any]] = None) -> None:
        self.db = db
        self.store = BriefingStore(db)
        self._call = caller or call_reach
        self.last_poll_ok = True
        self._briefing = briefing
        self._reach = reach
        self._programs = programs
        self._clock = clock
        self._link = link
        self._cadence = cadence
        self._pair_code: Optional[str] = None   # the open code, for the owner's link; never stored
        self._void_codes: set[str] = set()      # hashes of codes voided here when the store could not be written
        self.last_answer_at: Optional[str] = None  # when Telegram last answered a call (this process)
        self._second: dict[tuple[str, str], float] = {}
        self._pending_kill: set[str] = set()   # Cadence loops whose Kill waits for its second tap
        self._shapes: dict[str, dict[str, Any]] = {}
        self._tries: dict[int, int] = {}       # update id -> handler failures so far
        self._done: Optional[list[int]] = None  # read update ids, loaded from the store one time

    # ── seams ────────────────────────────────────────────────────────

    def briefing(self) -> Any:
        if self._briefing is not None:
            return self._briefing
        from .briefing_service import default_briefing_service

        return default_briefing_service(self.db)

    def reach(self) -> Any:
        if self._reach is not None:
            return self._reach
        from .reach_service import default_reach_service

        return default_reach_service(self.db)

    def programs(self) -> Any:
        if self._programs is not None:
            return self._programs()
        return self.briefing().programs()

    def now(self) -> datetime:
        try:
            value = datetime.fromisoformat(str(self._clock()).replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    def link_for(self, path: str) -> Optional[str]:
        if self._link is not None:
            return self._link(path)
        base = page_base()
        return f"{base}{path}" if base else None

    def _api(self, method: str, params: Mapping[str, Any], *, data_class: str = "reach_package",
             timeout: Optional[float] = None) -> dict[str, Any]:
        if (method in ("sendMessage", "editMessageText") and isinstance(params.get("text"), str)
                and not params.get("parse_mode")):
            from .reach_redact import reach_line

            params = {**params, "text": reach_line(params["text"])}
        token = bot_token()
        if not token or not telegram_on():
            return {"ok": False, "description": "telegram is off"}
        if self.halted():
            # The token is revoked or another desk reads the bot: nothing is
            # sent and nothing polls until the owner acts (a new token,
            # ``use_here``, remove). No call, so no operation is recorded.
            return {"ok": False, "description": WAITS_FOR_OWNER, "halted": True}
        return self._raw(token, method, params, data_class=data_class, timeout=timeout)

    def _raw(self, token: str, method: str, params: Mapping[str, Any], *, data_class: str = "reach_package",
             timeout: Optional[float] = None) -> dict[str, Any]:
        """One call with this token through the one transport. The answer's
        ``error_code`` becomes the health state (``_note``)."""
        if self._call is call_reach:
            more = {"timeout": timeout} if timeout is not None else {}
            result = call_reach(token, method, params, data_class=data_class, **more)
        else:
            result = self._call(token, method, dict(params))
        if not result.get("ok", True):
            log.warning(f"telegram {method} failed: {_redact(str(result.get('description')), token)}")
        if token == bot_token():
            self._note(method, result)
        return result

    # ── the setup state (durable) ────────────────────────────────────

    def _setup(self) -> dict[str, Any]:
        return self._policy(SETUP_POLICY)

    def _save_setup(self, **changes: Any) -> bool:
        state = {**self._setup(), **changes}
        return self._save_policy(SETUP_POLICY, {key: value for key, value in state.items() if value is not None})

    def _stamp(self) -> str:
        return self.now().astimezone(timezone.utc).isoformat()

    def _note(self, method: str, result: Mapping[str, Any]) -> None:
        """Telegram's answer as a health state: 401 the token is revoked, 403
        on a send the bot is blocked, 409 on the poll another desk reads the
        bot, no answer at all unreachable, an answer connected. Saved on a
        change only."""
        code = result.get("error_code")
        before = str((self._setup().get("health") or {}).get("state") or "")
        sends = method in ("sendMessage", "editMessageText")
        if result.get("ok", True):
            self.last_answer_at = self._stamp()
            if before == "bot_blocked" and not sends:
                return  # a poll that answers does not prove the chat takes a message
            state = "connected"
        elif code == 401:
            state = "token_revoked"
        elif code == 403 and sends:
            state = "bot_blocked"
        elif code == 409 and method == "getUpdates":
            state = "another_desk"
        elif code is None:
            state = "unreachable"
        else:
            return
        if before in HALTED and state not in HALTED:
            # Review T1: a halt (the token is revoked, another desk reads the
            # bot) is cleared by an owner act only: a new token saved and
            # checked, ``use_here``, remove. An answer or a timeout that comes
            # in while halted changes nothing.
            return
        if state != before:
            self._save_setup(health={"state": state, "since": self._stamp()})
            self._changed("telegram", "health")

    def health(self, setup: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """``{state, since, words}``: one plain sentence for each state."""
        setup = self._setup() if setup is None else setup
        saved = dict(setup.get("health") or {})
        if not telegram_on():
            state, since = "off", None
        elif _store() is None:
            state, since = "keystore_locked", None
        elif not bot_token():
            state, since = "no_token", None
        elif saved.get("state"):
            state, since = str(saved["state"]), saved.get("since")
            if state == "connected" and self.last_answer_at:
                since = self.last_answer_at
        else:
            state, since = "not_checked", None
        return {"state": state, "since": since, "words": HEALTH_WORDS[state]}

    def _bot_public(self, setup: Optional[Mapping[str, Any]] = None) -> Optional[dict[str, Any]]:
        bot = (self._setup() if setup is None else setup).get("bot")
        if not isinstance(bot, dict) or not bot_token():
            return None
        return {"name": str(bot.get("name") or ""), "username": str(bot.get("username") or ""),
                "checked": bool(bot.get("checked"))}

    def _check_bot(self, token: str) -> Optional[dict[str, Any]]:
        """Ask Telegram who the bot is. ``{name, username, checked}``; None
        when Telegram does not know the token; ``checked`` false when it
        did not answer."""
        result = self._raw(token, "getMe", {}, data_class="reach_bot_identity")
        if result.get("ok", True):
            me = dict(result.get("result") or {})
            return {"name": str(me.get("first_name") or ""), "username": str(me.get("username") or ""),
                    "checked": True, "at": self._stamp()}
        if result.get("error_code") in (401, 404):
            return None
        return {"name": "", "username": "", "checked": False}

    def _ensure_bot(self) -> bool:
        """A token that was kept unchecked (Telegram did not answer, or it
        was saved before the check was made) is checked before a poll. False
        when Telegram does not know it: the poll does not run."""
        bot = self._setup().get("bot")
        if isinstance(bot, dict) and bot.get("checked"):
            return True
        token = bot_token()
        found = self._check_bot(token)
        if found is None:
            self._save_setup(health={"state": "token_revoked", "since": self._stamp()})
            self._changed("telegram", "health")
            return False
        self._save_setup(bot=found)
        return True

    def _changed(self, ident: str, verb: str) -> None:
        try:
            from ..runtime import composition

            composition.notify_desk_changed("reach", ident, verb)
        except Exception:
            pass

    # ── state ────────────────────────────────────────────────────────

    def halted(self) -> bool:
        """The token is revoked or another desk reads the bot (``HALTED``):
        no poll and no automatic send until the owner acts."""
        return str((self._setup().get("health") or {}).get("state") or "") in HALTED

    def live(self) -> bool:
        """Sends may go: Telegram on, a token, a paired chat, not halted."""
        return telegram_on() and bool(bot_token()) and paired_chat() is not None and not self.halted()

    def _pairing_state(self, setup: Optional[Mapping[str, Any]] = None) -> Optional[dict[str, Any]]:
        """The open pairing code's ``{hash, expires_at, wrong}`` from the
        store (it survives a restart), or None when none is open."""
        pairing = (self._setup() if setup is None else setup).get("pairing")
        if not isinstance(pairing, dict) or str(pairing.get("hash") or "") in self._void_codes:
            return None
        ends = _epoch(pairing.get("expires_at"))
        return dict(pairing) if ends is not None and ends > self.now().timestamp() else None

    def pairing_open(self) -> bool:
        return self._pairing_state() is not None

    def _pair_link(self, code: Optional[str], setup: Optional[Mapping[str, Any]] = None) -> Optional[str]:
        """``https://t.me/<bot>?start=<code>``: he presses Start in Telegram
        and the chat is connected. Only while this process holds the code."""
        username = str(((self._setup() if setup is None else setup).get("bot") or {}).get("username") or "")
        return f"https://t.me/{username}?start={code}" if username and code else None

    def should_poll(self) -> bool:
        """Nothing polls when unpaired and no code is open, when off, or
        while the poll waits for the owner (``HALTED``)."""
        if not (telegram_on() and bool(bot_token())):
            return False
        if self.halted():
            return False
        return paired_chat() is not None or self.pairing_open()

    def summary(self) -> dict[str, Any]:
        """The view that ANY forwarder may pass on (``ReachService.summary``,
        which ``phone.status`` returns to an agent over MCP): state words
        only. Never the pairing link or its code (review T1: an agent that
        read the link could pair its own chat), never the bot's username (it
        is where a stranger would send guesses), never a chat id or a token,
        never the test's message. A forwarder calls this and nothing else."""
        chat = paired_chat()
        setup = self._setup()
        health = self.health(setup)
        return {"on": telegram_on(), "token": token_where(),
                "paired": {"name": str(chat.get("name") or ""), "at": chat.get("at")} if chat else None,
                "pairing": {"expires_at": self._pairing_state(setup)["expires_at"]}
                if self._pairing_state(setup) else None,
                "destination": DESTINATION_WORDS,
                "health": {"state": health["state"], "since": health["since"], "words": health["words"]}}

    def status(self) -> dict[str, Any]:
        """THE OWNER'S VIEW, for ``ReachService.status`` only (``reach.status``,
        ``GET /api/reach``: ``_require_owner`` there, ``owner_only`` on the
        row). Never the token, the chat id or the code alone; the link holds
        the code and is for his own faces. Any other reader gets ``summary``."""
        chat = paired_chat()
        setup = self._setup()  # one read of the stored state for the whole answer
        pairing = None
        open_code = self._pairing_state(setup)
        if open_code:
            pairing = {"expires_at": open_code["expires_at"]}
            link = self._pair_link(self._pair_code, setup)
            if link:
                pairing["link"] = link
        store_open = _store() is not None
        test = setup.get("last_test")
        out = {"on": telegram_on(), "token": token_where(),
               "paired": {"name": str(chat.get("name") or ""), "at": chat.get("at")} if chat else None,
               "pairing": pairing, "destination": DESTINATION_WORDS,
               "bot": self._bot_public(setup), "health": self.health(setup),
               "last_test": {"sent_at": test.get("sent_at"), "answered_at": test.get("answered_at")}
               if isinstance(test, dict) else None,
               "keystore": "open" if store_open else "locked",
               "outbox": self.outbox_view()}
        if not store_open:
            out["keystore_words"] = HEALTH_WORDS["keystore_locked"]
        return out

    def skipped_updates(self) -> Optional[dict[str, Any]]:
        """``{count, at}`` of the updates that could not be read and were
        skipped, or None. Not in ``status()``: that answer's shape is stored
        by the desk's recordings; the owner reads the skip in his chat."""
        skipped = self._updates_state().get("skipped")
        return dict(skipped) if isinstance(skipped, dict) else None

    # ── the owner's verbs ────────────────────────────────────────────

    @staticmethod
    def _require_owner(principal: Any) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise TelegramRefused("owner_only", "Only you can pair Telegram.", status=403)

    def save_token(self, principal: Any, value: Any) -> dict[str, Any]:
        self._require_owner(principal)
        token = str(value or "").strip()
        if token and not _TOKEN_SHAPE.match(token):
            raise TelegramRefused("token_invalid", "This is not a bot token. BotFather gives one like "
                                  "123456:ABC… Paste it again.", status=400)
        bot: Optional[dict[str, Any]] = None
        if token:
            # Telegram says who the bot is before the token is kept. A token
            # it does not know is refused; no answer keeps it "not checked".
            bot = self._check_bot(token) if telegram_on() else {"name": "", "username": "", "checked": False}
            if bot is None:
                raise TelegramRefused("token_unknown", TOKEN_UNKNOWN_WORDS, status=400)
        _write(TOKEN_SLOT, token)
        health = {"state": "connected" if bot and bot["checked"] else "not_checked", "since": self._stamp()}
        self._save_policy(SETUP_POLICY, {**{key: value for key, value in self._setup().items()
                                           if key not in ("bot", "health")},
                                         **({"bot": bot, "health": health} if token else {})})
        self._changed("telegram", "token")
        return {"token": token_where(), "bot": self._bot_public()}

    def start_pairing(self, principal: Any) -> dict[str, Any]:
        self._require_owner(principal)
        if paired_chat() is not None:
            raise TelegramRefused("already_paired", "A chat is paired. Unpair it first.")
        if not bot_token():
            raise TelegramRefused("token_missing", "Put the bot token in first.", status=409)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = (self.now() + timedelta(minutes=PAIR_MINUTES)).astimezone(timezone.utc).isoformat()
        with _lock:
            # The hash and the expiry are stored (a restart keeps the code
            # good); the code itself stays in this process, for his link.
            if not self._save_setup(pairing={"hash": hashlib.sha256(code.encode()).hexdigest(),
                                             "expires_at": expires_at, "wrong": 0}):
                # A code whose hash and try count are not stored is not handed out.
                raise TelegramRefused("pairing_not_saved", "The desk could not save a pairing code. "
                                      "Try again.", status=503)
            self._pair_code = code
        try:
            self.reach().wake()
        except Exception:
            pass
        self._changed("telegram", "pairing")
        made = {"code": code, "words": f"{code[:3]} {code[3:]}", "expires_at": expires_at,
                "say": f"Send /pair {code[:3]} {code[3:]} to your bot"}
        link = self._pair_link(code)
        return {**made, "link": link} if link else made

    def unpair(self, principal: Any) -> dict[str, Any]:
        self._require_owner(principal)
        with _lock:
            self._drop_pairing()
            store = _store()
            if store is not None:
                store.put(CHAT_SLOT, "")
        self._changed("telegram", "unpaired")
        return {"paired": None}

    def _drop_pairing(self) -> bool:
        """The open code is no longer good. True when that is written; the
        code is voided in this process in every case."""
        self._pair_code = None
        setup = self._setup()
        pairing = setup.get("pairing")
        if pairing is None:
            return True
        if isinstance(pairing, dict) and pairing.get("hash"):
            self._void_codes.add(str(pairing["hash"]))
        return self._save_policy(SETUP_POLICY, {key: value for key, value in setup.items() if key != "pairing"})

    def send_test(self, principal: Any) -> dict[str, Any]:
        """``reach.telegram.test``: one message with one button to the paired
        chat. His press of the button is the proof (``last_test``)."""
        self._require_owner(principal)
        health = self.health()
        chat = paired_chat()
        if not bot_token() or chat is None or health["state"] in ("off", "keystore_locked") + HALTED:
            words = health["words"] if health["state"] not in ("connected", "not_checked", "unreachable",
                                                                 "bot_blocked") else NOT_CONNECTED_WORDS
            raise TelegramRefused("telegram_not_connected", words)
        sent_at = self._stamp()
        result = self._send(chat["id"], f"Test from your desk · {_clock(sent_at)}",
                            [[{"text": TEST_BUTTON, "callback_data": f"{CALLBACK}|{TEST_CALLBACK}|ok"}]],
                            data_class="reach_test")
        if not result.get("ok", True):
            raise TelegramRefused("telegram_failed", f"{TEST_FAILED_WORDS} {self.health()['words']}", status=502)
        self._save_setup(last_test={"sent_at": sent_at, "answered_at": None,
                                    "message_id": (result.get("result") or {}).get("message_id")})
        self._changed("telegram", "test")
        return {"last_test": {"sent_at": sent_at, "answered_at": None}}

    def remove_bot(self, principal: Any, username: Any) -> dict[str, Any]:
        """Take the bot off this desk: the token leaves the keystore, the
        chat is disconnected, the poll stops. Bound to the bot's username,
        so that a face that shows another bot removes nothing."""
        self._require_owner(principal)
        saved = str((self._setup().get("bot") or {}).get("username") or "").lower()
        if str(username or "").strip().lstrip("@").lower() != saved:
            raise TelegramRefused("answer_stale", BOT_CHANGED_WORDS)
        with _lock:
            _write(TOKEN_SLOT, "")
            _write(CHAT_SLOT, "")
            self._pair_code = None
            self.last_answer_at = None
            self._save_policy(SETUP_POLICY, {})
        self._changed("telegram", "removed")
        return {"token": token_where(), "paired": None, "bot": None}

    def use_here(self, principal: Any) -> dict[str, Any]:
        """Another HoldSpeak read this bot (409) and this desk stopped. The
        owner says: read it here. The poll starts again."""
        self._require_owner(principal)
        self._save_setup(health={"state": "not_checked", "since": self._stamp()})
        try:
            self.reach().wake()
        except Exception:
            pass
        self._changed("telegram", "health")
        try:
            self.flush()
        except Exception as exc:
            log.info(f"telegram: the outbox was not sent after use_here ({type(exc).__name__})")
        return {"health": self.health()}

    # ── briefs ───────────────────────────────────────────────────────

    def brief(self, ref: str, *, because: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """Make a package for one held item and send it to the owner chat."""
        chat = paired_chat()
        if not self.live() or chat is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        made = self.briefing().make(TELEGRAM_OWNER, [ref])
        return self.send_package(made["id"], made["path"], because=because)

    def send_package(self, package_id: str, path: str, *, because: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        chat = paired_chat()
        package = self.store.get(package_id)
        if chat is None or package is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        body = dict(package["body"] or {})
        message = package_message(body, self.link_for(path), self.now(),
                                  buttons=from_buttons(choice_buttons(package_id, body)))
        params, text = message_payload(chat["id"], self._written(message), fenced=fence)
        from .briefing_service import because_of

        # IMP5: why it travelled (the item's kind, and the ladder's rule when
        # the ladder sent it); never a permission.
        why = {**because_of(body.get("kind")), **{key: value for key, value in dict(because or {}).items()
                                                  if value is not None}}
        key = f"package:{package_id}"
        # The row is written before the send: the ladder counts it, so a
        # message that waits in the outbox is not made a second time.
        sent = list(package.get("sent") or [])
        sent.append({"via": "telegram", "at": self.now().astimezone(timezone.utc).isoformat(),
                     "message_id": None, "because": why, "key": key, "queued": True})
        self.store.set_sent(package_id, sent)
        outcome = self._deliver(key, "sendMessage", params, after={"kind": "package", "package_id": package_id},
                                ref=str((package.get("refs") or [""])[0] or "") or None)
        if outcome["state"] == "dropped":
            raise TelegramRefused("telegram_failed", "Telegram did not take the message. Nothing was sent.")
        self._changed(package_id, "sent" if outcome["state"] == "sent" else "queued")
        out = {"id": package_id, "message_id": outcome.get("message_id"), "text": text}
        if outcome["state"] != "sent":
            out["queued"] = True
        return out

    def digest(self, items: list[Mapping[str, Any]], *, tail: Optional[str] = None) -> dict[str, Any]:
        """One message: the count and one line per item with its kind word
        (§5 "The digest"), and ``tail`` (DIR7: the Cadence brief's line). No
        buttons for the items."""
        from .briefing_service import KIND_WORDS

        chat = paired_chat()
        if chat is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        rows = items[:12]
        head = "1 waits on you" if len(items) == 1 else f"{len(items)} wait on you"
        lines = [_line(f"{KIND_WORDS.get(str(item.get('kind')), 'Waits on you')} · {item.get('program_title')}"
                       + (f" · step {item['ordinal']}" if item.get("ordinal") else "")) for item in rows]
        lines.append("Open your desk to see each one.")
        if tail:
            lines.append(_line(tail))
        params, text = message_payload(chat["id"], self._written(Message(head=head, lines=tuple(lines))),
                                       fenced=fence)
        outcome = self._deliver(f"digest:{self._day()}", "sendMessage", params)
        return {"ok": outcome["state"] in ("sent", "queued", "duplicate"), "text": text, "items": len(rows),
                **({"queued": True} if outcome["state"] == "queued" else {})}

    def line(self, text: str) -> dict[str, Any]:
        """One plain message to the owner chat, no buttons (PG-LANG LANG12:
        the night's digest line)."""
        chat = paired_chat()
        if chat is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        params, body = message_payload(chat["id"], self._written(str(text or "")), fenced=fence)
        mark = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
        outcome = self._deliver(f"line:{self._day()}:{mark}", "sendMessage", params)
        return {"ok": outcome["state"] in ("sent", "queued", "duplicate"), "text": body,
                **({"queued": True} if outcome["state"] == "queued" else {})}

    def cadence_message(self, key: str, message: Message) -> dict[str, Any]:
        """One Cadence message (a due loop, the morning brief) to the owner
        chat, through the one writer and the outbox."""
        chat = paired_chat()
        if chat is None or not self.live():
            return {"ok": False, "state": "not_paired"}
        params, _text = message_payload(chat["id"], self._written(message), fenced=fence)
        outcome = self._deliver(key, "sendMessage", params, data_class="cadence_message")
        return {"ok": outcome["state"] in ("sent", "queued", "duplicate"), "state": outcome["state"]}

    def _day(self) -> str:
        return self.now().astimezone().strftime("%Y-%m-%d")

    # ── the outbox: a send that fails is not lost and not sent twice ──

    def _outbox(self) -> dict[str, Any]:
        state = self._policy(OUTBOX_POLICY)
        return {"items": list(state.get("items") or []), "sent": list(state.get("sent") or []),
                "last_error_words": state.get("last_error_words")}

    def _deliver(self, key: str, method: str, params: Mapping[str, Any], *, data_class: str = "reach_package",
                 after: Optional[Mapping[str, Any]] = None, ref: Optional[str] = None,
                 quiet: bool = True) -> dict[str, Any]:
        """Put one message in the outbox under its key and try it now.
        ``{state: sent | queued | duplicate | dropped, message_id?}``. One key
        is sent one time: a key that waits or was sent is a ``duplicate``.
        ``quiet`` False is for a message that does not notify (an edit)."""
        if not bot_token() or not telegram_on():
            return {"state": "dropped", "why": "off"}
        with _OUTBOX_LOCK:
            state = self._outbox()
            if key in state["sent"] or any(item.get("key") == key for item in state["items"]):
                return {"state": "duplicate"}
            state["items"].append({"key": key, "method": method, "params": dict(params), "data_class": data_class,
                                   "after": dict(after) if after else None, "ref": ref, "quiet": bool(quiet),
                                   "queued_at": self._stamp(), "tries": 0, "next_at": 0.0})
            if len(state["items"]) > OUTBOX_MAX:
                for gone in state["items"][: len(state["items"]) - OUTBOX_MAX]:
                    self._after(gone, None, "dropped")
                state["items"] = state["items"][-OUTBOX_MAX:]
                state["last_error_words"] = OUTBOX_FULL_WORDS
            if not self._save_policy(OUTBOX_POLICY, state):
                # It cannot be kept: send it now or say it was not sent.
                result = self._api(method, params, data_class=data_class)
                if result.get("ok"):
                    return {"state": "sent", "message_id": (result.get("result") or {}).get("message_id")}
                return {"state": "dropped", "why": "not_saved"}
        return self.flush().get("keys", {}).get(key) or {"state": "queued"}

    def flush(self, *, open_refs: Optional[set[str]] = None, quiet: bool = False) -> dict[str, Any]:
        """Send what waits, oldest first. A transport failure or a 429 waits
        (back-off, ``retry_after``) and stops the round; a 400 that can never
        succeed is dropped and said; nothing is sent while the poll waits for
        the owner. A question that is no longer open (``open_refs``) is not
        sent. In quiet hours (``quiet``) only edits go."""
        keys: dict[str, dict[str, Any]] = {}
        with _OUTBOX_LOCK:
            state = self._outbox()
            if not state["items"]:
                return {"sent": 0, "waiting": 0, "keys": keys}
            now = self.now().timestamp()
            keep: list[dict[str, Any]] = []
            stopped = False
            sent = 0
            for item in state["items"]:
                key = str(item.get("key"))
                if stopped or float(item.get("next_at") or 0) > now or (quiet and item.get("quiet", True)):
                    keep.append(item)
                    keys[key] = {"state": "queued"}
                    continue
                if open_refs is not None and item.get("ref") and item["ref"] not in open_refs:
                    self._after(item, None, "answered")
                    keys[key] = {"state": "dropped", "why": "answered"}
                    continue
                result = self._api(str(item["method"]), item["params"],
                                   data_class=str(item.get("data_class") or "reach_package"))
                verdict, wait = self._verdict(item, result)
                if verdict == "sent":
                    sent += 1
                    state["sent"] = (state["sent"] + [key])[-REMEMBERED_SENDS:]
                    self._after(item, result, "sent")
                    keys[key] = {"state": "sent", "message_id": (result.get("result") or {}).get("message_id")}
                elif verdict == "dropped":
                    state["last_error_words"] = DROPPED_WORDS
                    self._after(item, result, "dropped")
                    keys[key] = {"state": "dropped", "why": "refused"}
                else:
                    item = {**item, "tries": int(item.get("tries") or 0) + (1 if verdict == "retry" else 0),
                            "next_at": now + wait}
                    keep.append(item)
                    keys[key] = {"state": "queued"}
                    stopped = True  # the next one would fail the same way: oldest first, later
            if sent and not keep:
                state["last_error_words"] = None
            state["items"] = keep
            self._save_policy(OUTBOX_POLICY, state)
        return {"sent": sent, "waiting": len(keep), "keys": keys}

    def _verdict(self, item: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[str, float]:
        """``(sent | dropped | retry | wait, seconds)`` for one answer."""
        if result.get("ok"):
            return "sent", 0.0
        tries = int(item.get("tries") or 0)
        backoff = float(min(RETRY_CAP_SECONDS, RETRY_FIRST_SECONDS * (2 ** min(tries, 10))))
        if result.get("halted") or result.get("description") == "telegram is off":
            return "wait", 0.0  # the owner acts; then the next flush sends it
        code = result.get("error_code")
        described = str(result.get("description") or "").lower()
        if code == 429:
            told = (result.get("parameters") or {}).get("retry_after")
            return "wait", float(told) if isinstance(told, (int, float)) and told > 0 else backoff
        if code == 400:
            if item.get("method") == "editMessageText" and ("not modified" in described or "not found" in described):
                return "sent", 0.0  # the edit is there already, or its message is gone
            return "dropped", 0.0
        return "retry", backoff

    def _after(self, item: Mapping[str, Any], result: Optional[Mapping[str, Any]], outcome: str) -> None:
        """What a sent or a dropped message leaves on its object."""
        after = item.get("after") or {}
        if after.get("kind") != "package":
            return
        try:
            package = self.store.get(str(after.get("package_id")))
            if package is None:
                return
            rows = []
            for row in package.get("sent") or []:
                if isinstance(row, dict) and row.get("key") == item.get("key"):
                    if outcome != "sent":
                        continue  # it did not travel: the ladder may send the item again
                    row = {name: value for name, value in row.items() if name != "queued"}
                    row["message_id"] = ((result or {}).get("result") or {}).get("message_id")
                rows.append(row)
            self.store.set_sent(package["id"], rows)
        except Exception as exc:
            log.warning(f"telegram: a sent message was not written on its package ({type(exc).__name__})")

    def outbox_view(self) -> dict[str, Any]:
        state = self._outbox()
        items = state["items"]
        return {"waiting": len(items), "oldest_since": items[0].get("queued_at") if items else None,
                "last_error_words": state.get("last_error_words")}

    def settle(self, package: Mapping[str, Any], words: str) -> None:
        """The package's Telegram messages edit themselves to the outcome."""
        chat = paired_chat()
        if chat is None or not self.live():
            return
        body = dict(package.get("body") or {})
        for row in package.get("sent") or []:
            if not isinstance(row, dict) or row.get("via") != "telegram" or not row.get("message_id"):
                continue
            if row.get("settled"):
                continue
            params, _plain = edit_payload(chat["id"], row["message_id"],
                                          self._written(self._settled_text(body, package, words)), fenced=fence)
            mark = hashlib.sha256(str(words).encode("utf-8")).hexdigest()[:10]
            self._deliver(f"edit:{package['id']}:{row['message_id']}:{mark}", "editMessageText", params,
                          quiet=False)
            row["settled"] = words
        self.store.set_sent(package["id"], list(package.get("sent") or []))

    def _settled_text(self, body: Mapping[str, Any], package: Mapping[str, Any], words: str,
                      link: Optional[str] = None) -> str:
        lines = [_line(body.get("head"))]
        if link:
            lines.append(f"Open the page: {link}")
        return fence("\n".join(lines + [words]))

    def settle_gone(self, open_refs: set[str]) -> list[str]:
        """Messages whose item waits no more (answered on the desk or a call)
        settle: "Answered already on your desk"."""
        settled: list[str] = []
        since = (self.now() - timedelta(days=2)).astimezone(timezone.utc).isoformat()
        for package in self.store.sent_since(since):
            ref = (package["refs"] or [""])[0]
            if ref in open_refs:
                continue
            pending = [row for row in package["sent"] if isinstance(row, dict) and row.get("via") == "telegram"
                       and row.get("message_id") and not row.get("settled")]
            if not pending:
                continue
            answer = (package.get("answers") or {}).get(ref) if isinstance(package.get("answers"), dict) else None
            words = "Answered already on your desk"
            if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
                continue  # settled by its own answer
            self.settle(package, words)
            settled.append(package["id"])
        return settled

    def _written(self, text: Any, keyboard: Optional[list[list[dict[str, str]]]] = None) -> Message:
        """The message, with the whole text put to the fence one time (a
        thing that is never sent is refused before a piece is written)."""
        message = as_message(text, keyboard)
        fence(write_message(message)[0])
        return message

    def _edit(self, chat_id: Any, message_id: Any, text: Any,
              keyboard: Optional[list[list[dict[str, str]]]] = None) -> dict[str, Any]:
        params, _plain = edit_payload(chat_id, message_id, self._written(text, keyboard), fenced=fence,
                                      keep_buttons=keyboard is not None)
        return self._api("editMessageText", params)

    def _send(self, chat_id: Any, text: Any, keyboard: Optional[list[list[dict[str, str]]]] = None,
              *, data_class: str = "reach_package") -> dict[str, Any]:
        params, _plain = message_payload(chat_id, self._written(text, keyboard), fenced=fence)
        return self._api("sendMessage", params, data_class=data_class)

    def _ack(self, callback_id: str, text: str = "") -> None:
        self._api("answerCallbackQuery", {"callback_query_id": callback_id, "text": text},
                  data_class="reach_decision_ack")

    # ── updates ──────────────────────────────────────────────────────

    def poll_once(self, offset: Optional[int]) -> Optional[int]:
        """One getUpdates round (long poll); the next offset.

        ``last_poll_ok`` says if the loop may poll again at once: it is false
        after a poll that failed or timed out, and after an update whose
        handler raised (the cursor stays on that update; it is read again
        after the wait, ``UPDATE_TRIES`` times, then skipped with one line to
        the owner so that one bad update cannot stop the queue).

        An update id that was read before (a replay after a restart) is
        passed over: the read ids are kept in the cadence policy row
        ``UPDATES_POLICY``."""
        if self.halted() or not self._ensure_bot():
            self.last_poll_ok = False
            return offset
        params: dict[str, Any] = {"timeout": LONG_POLL_SECONDS}
        if offset is not None:
            params["offset"] = offset
        result = self._api("getUpdates", params, data_class="reach_update_cursor",
                           timeout=LONG_POLL_CLIENT_TIMEOUT)
        self.last_poll_ok = bool(result.get("ok", True))
        next_offset = offset
        for update in result.get("result", []) or []:
            uid = int(update.get("update_id", 0))
            if uid and uid in self._done_updates():
                next_offset = uid + 1
                continue
            try:
                self.handle_update(update)
            except Exception as exc:
                log.error(f"telegram update failed: {type(exc).__name__}: {_redact(str(exc), bot_token())}")
                tries = self._tries[uid] = self._tries.get(uid, 0) + 1
                if tries < UPDATE_TRIES:
                    self.last_poll_ok = False
                    break
                self._skip_update(update)
            self._tries.pop(uid, None)
            if uid:
                self._remember_update(uid)
            next_offset = uid + 1
        return next_offset

    # ── the read update ids (durable) ────────────────────────────────

    def _policy(self, name: str) -> dict[str, Any]:
        try:
            policy = self.db.cadence.get_policy(name)
            return dict((getattr(policy, "config", None) or {}) if policy else {})
        except Exception:
            return {}

    def _save_policy(self, name: str, state: Mapping[str, Any]) -> bool:
        """True when the state was written. A caller that guards something
        (the pairing code's wrong count, its invalidation) must look."""
        try:
            from ..cadence.models import CadencePolicy

            self.db.cadence.upsert_policy(CadencePolicy(name=name, config=dict(state)))
            return True
        except Exception as exc:
            log.warning(f"telegram: the state {name} was not saved ({type(exc).__name__})")
            return False

    def _updates_state(self) -> dict[str, Any]:
        return self._policy(UPDATES_POLICY)

    def _save_updates_state(self, state: Mapping[str, Any]) -> None:
        self._save_policy(UPDATES_POLICY, state)

    def _done_updates(self) -> list[int]:
        if self._done is None:
            self._done = [int(value) for value in self._updates_state().get("done") or []]
        return self._done

    def _remember_update(self, uid: int) -> None:
        done = [value for value in self._done_updates() if value != uid] + [uid]
        self._done = done[-REMEMBERED_UPDATES:]
        self._save_updates_state({**self._updates_state(), "done": self._done})

    def _skip_update(self, update: Mapping[str, Any]) -> None:
        """An update that could not be read ``UPDATE_TRIES`` times: one line
        in the log, the count and time kept (``skipped_updates``), and one
        line in the owner chat when the update came from it."""
        log.warning("telegram: one update could not be read and was skipped")
        state = self._updates_state()
        before = dict(state.get("skipped") or {})
        skipped = {"count": int(before.get("count") or 0) + 1,
                   "at": self.now().astimezone(timezone.utc).isoformat()}
        self._save_updates_state({**state, "skipped": skipped})
        message = update.get("message") or (update.get("callback_query") or {}).get("message") or {}
        chat_id = str(((message or {}).get("chat") or {}).get("id") or "").strip()
        if chat_id and self._is_owner_chat(chat_id):
            try:
                self._send(chat_id, SKIPPED_WORDS, data_class="reach_refusal")
            except Exception:
                pass

    def handle_update(self, update: Mapping[str, Any]) -> dict[str, Any]:
        """One update. Returns a small ``{action, …}`` for tests."""
        if "callback_query" in update:
            return self._callback(dict(update["callback_query"]))
        message = dict(update.get("message") or {})
        chat = dict(message.get("chat") or {})
        chat_id = str(chat.get("id") or "").strip()
        text = str(message.get("text") or "").strip()
        if not chat_id or not text:
            return {"action": "ignored"}
        command = text.split()[0].lower().lstrip("/")
        if command == "pair" or (command == "start" and len(text.split()) > 1):
            # ``/start <code>`` is what Telegram sends when he opens the
            # link ``t.me/<bot>?start=<code>`` and presses Start.
            return self._pair(chat_id, text, message)
        if not self._is_owner_chat(chat_id):
            self._send(chat_id, "This chat is not paired.", data_class="reach_refusal")
            return {"action": "rejected"}
        if text.startswith("/"):
            return self._cadence_update(update)
        return self._reply(chat_id, text, message)

    def _test_tap(self, chat_id: str, callback_id: str, message: Mapping[str, Any]) -> dict[str, Any]:
        """His press of ``It works`` on the test message."""
        test = self._setup().get("last_test")
        answered_at = self._stamp()
        if isinstance(test, dict):
            self._save_setup(last_test={**test, "answered_at": answered_at})
        head = str(message.get("text") or "Test from your desk").split("\n")[0]
        self._edit(chat_id, message.get("message_id"), f"{head}\n{TEST_BUTTON} · {_clock(answered_at)}")
        self._ack(callback_id, f"{TEST_BUTTON}.")
        self._changed("telegram", "test")
        return {"action": "test", "answered_at": answered_at}

    def _is_owner_chat(self, chat_id: str) -> bool:
        chat = paired_chat()
        return chat is not None and str(chat["id"]) == str(chat_id)

    def _pair(self, chat_id: str, text: str, message: Mapping[str, Any]) -> dict[str, Any]:
        code = "".join(text.split()[1:])
        with _lock:
            pairing = self._pairing_state()
            if paired_chat() is not None:
                if self._is_owner_chat(chat_id):
                    self._send(chat_id, "This chat is paired already.", data_class="reach_refusal")
                    return {"action": "pair", "ok": True}
                self._send(chat_id, "This chat is not paired.", data_class="reach_refusal")
                return {"action": "pair", "ok": False}
            ok = bool(pairing and hashlib.sha256(code.encode()).hexdigest() == pairing["hash"])
            if not ok:
                if pairing:
                    # Astra post-merge 2026-11-01: 5 wrong codes and the code
                    # is void; a new one is needed. The count is stored.
                    # Review T1: the try counts only when it was WRITTEN. A
                    # store that fails voids the code (in this process too),
                    # so that a guess can never be made again and again
                    # against a count that does not move.
                    pairing["wrong"] = int(pairing.get("wrong") or 0) + 1
                    if pairing["wrong"] >= PAIR_WRONG_MAX:
                        self._drop_pairing()
                        self._changed("telegram", "pairing_void")
                    elif not self._save_setup(pairing=pairing):
                        self._void_codes.add(str(pairing["hash"]))
                        self._pair_code = None
                        self._changed("telegram", "pairing_void")
                self._send(chat_id, "Wrong or old code. Make a new one in Settings ▸ Reach.",
                           data_class="reach_refusal")
                return {"action": "pair", "ok": False}
            # The right code. It is used up BEFORE the chat is connected: if
            # the desk cannot write that, nothing is paired and the code is
            # void (a code that stays good after a pairing could pair again).
            if not self._drop_pairing():
                self._send(chat_id, PAIR_NOT_SAVED_WORDS, data_class="reach_refusal")
                self._changed("telegram", "pairing_void")
                return {"action": "pair", "ok": False, "refused": "not_saved"}
            sender = dict(message.get("from") or {})
            name = str(sender.get("first_name") or (message.get("chat") or {}).get("first_name") or "")
            _write(CHAT_SLOT, json.dumps({"id": chat_id, "name": name,
                                          "at": self.now().astimezone(timezone.utc).isoformat()}))
        self._send(chat_id, "Paired. HoldSpeak sends what waits on you here.", data_class="reach_refusal")
        self._changed("telegram", "paired")
        return {"action": "pair", "ok": True}

    def _cadence_update(self, update: Mapping[str, Any]) -> dict[str, Any]:
        """A slash command or one of Cadence's buttons from the owner chat.
        Cadence reads and writes its loops (``reach_cadence``); the answer
        goes out through the one writer."""
        from . import reach_cadence

        try:
            if "callback_query" in update:
                query = dict(update["callback_query"])
                chat_id = str(((query.get("message") or {}).get("chat") or {}).get("id") or "").strip()
                action, words, message = reach_cadence.button(self.db, str(query.get("data") or ""),
                                                              self._pending_kill)
                if message is not None:
                    self._send(chat_id, message, data_class="cadence_message")
                self._ack(str(query.get("id") or ""), words)
                return {"action": "cadence", "result": {"action": action}}
            message = dict(update.get("message") or {})
            chat_id = str((message.get("chat") or {}).get("id") or "").strip()
            name = str(message.get("text") or "").split()[0].lower().lstrip("/")
            action, messages = reach_cadence.command(self.db, name)
            for made in messages:
                self._send(chat_id, made, data_class="cadence_message")
            return {"action": "cadence", "result": {"action": action}}
        except TelegramRefused:
            raise
        except Exception as exc:
            log.info(f"telegram: cadence update not handled ({type(exc).__name__})")
            return {"action": "cadence", "result": None}

    # ── a button ─────────────────────────────────────────────────────

    def _callback(self, query: dict[str, Any]) -> dict[str, Any]:
        message = dict(query.get("message") or {})
        chat_id = str((message.get("chat") or {}).get("id") or "").strip()
        callback_id = str(query.get("id") or "")
        data = str(query.get("data") or "")
        if not self._is_owner_chat(chat_id):
            self._ack(callback_id, "Not paired.")
            return {"action": "rejected"}
        parts = data.split("|")
        if len(parts) < 3 or parts[0] != CALLBACK:
            return self._cadence_update({"callback_query": query})
        if parts[1] == TEST_CALLBACK:
            return self._test_tap(chat_id, callback_id, message)
        if parts[1] == "shape":
            return self._shape_tap(chat_id, callback_id, message, parts[2], parts[3] if len(parts) > 3 else "")
        package_id, act = parts[1], parts[2]
        package = self.store.get(package_id)
        if package is None:
            self._ack(callback_id, "This item is gone.")
            return {"action": "missing"}
        body = dict(package["body"] or {})
        ref = str(body.get("ref") or "")
        message_id = message.get("message_id")
        # The page link is read back from the message Telegram holds: the hub
        # keeps only the token's hash, never the link.
        link = _link_in(message.get("text"))
        if act == "later":
            self._edit(chat_id, message_id, render(body, link, self.now()), later_buttons(package_id))
            self._ack(callback_id)
            return {"action": "later_menu"}
        if act == "back":
            for key in [key for key in self._second if key[0] == package_id]:
                self._second.pop(key, None)
            self._edit(chat_id, message_id, render(body, link, self.now()), choice_buttons(package_id, body))
            self._ack(callback_id)
            return {"action": "back"}
        if act.startswith("L:"):
            return self._answer(chat_id, callback_id, message_id, package, ref, "later", later=act[2:], link=link)
        confirmed = act.endswith("!")
        choice = act.rstrip("!")
        if (str(body.get("kind")), choice) in _SECOND_TAP and not confirmed:
            self._second[(package_id, choice)] = time.monotonic() + SECOND_TAP_SECONDS
            label = next((row["label"] for row in body.get("choices") or [] if row["id"] == choice), choice)
            other = "Not now"
            confirm = [_line(body.get("head")), _second_tap_words(body, choice)]
            if link:
                confirm.append(f"Open the page: {link}")
            self._edit(chat_id, message_id, fence("\n".join(confirm)),
                       [[{"text": label, "callback_data": f"{CALLBACK}|{package_id}|{choice}!"},
                         {"text": other, "callback_data": f"{CALLBACK}|{package_id}|back"}]])
            self._ack(callback_id)
            return {"action": "second_tap", "choice": choice}
        if confirmed:
            expires = self._second.pop((package_id, choice), 0.0)
            if expires < time.monotonic():
                self._edit(chat_id, message_id, render(body, link, self.now()), choice_buttons(package_id, body))
                self._ack(callback_id, "Too late. Tap it again.")
                return {"action": "second_tap_expired"}
        return self._answer(chat_id, callback_id, message_id, package, ref, choice, link=link)

    def _answer(self, chat_id: str, callback_id: Optional[str], message_id: Any, package: Mapping[str, Any],
                ref: str, choice: str, *, later: Optional[str] = None, link: Optional[str] = None) -> dict[str, Any]:
        body = dict(package.get("body") or {})
        try:
            result = self.briefing().answer_package(package["id"], ref, choice, via="telegram", later=later, binding=body.get("binding"))
        except ServiceError as exc:
            words = exc.detail
            if exc.code == "answered_already":
                # IMP5: when and where it was answered ("Answered at 21:46 from the desk").
                words = str((exc.context or {}).get("words") or exc.detail)
            if message_id is not None:
                self._edit(chat_id, message_id, self._settled_text(body, package, words, link))
            if callback_id:
                self._ack(callback_id, words[:190])
            return {"action": "refused", "code": exc.code, "words": words}
        outcome = (result.get("item") or {}).get("outcome") or {}
        words = str(outcome.get("words") or "")
        if outcome.get("choice") == "later":
            line = words
        else:
            line = f"Decided: {outcome.get('label')} · {_clock(outcome.get('at'))}"
        if message_id is not None:
            self._edit(chat_id, message_id, self._settled_text(body, package, line, link))
        if callback_id:
            self._ack(callback_id, line[:190])
        fresh = self.store.get(package["id"])
        if fresh is not None:
            sent = list(fresh.get("sent") or [])
            for row in sent:
                if isinstance(row, dict) and row.get("message_id") == message_id:
                    row["settled"] = line
            self.store.set_sent(fresh["id"], sent)
        return {"action": "answered", "choice": choice, "words": line}

    # ── a reply in words ─────────────────────────────────────────────

    def _open_package(self, message: Mapping[str, Any]
                      ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], Optional[str]]:
        """The package a text answers and the sent row of its question: ONLY
        the message this text is a Telegram reply to.

        Review 14a: a text with no replied-to question decides nothing. The
        old rule ("else the one open package") let a queued "yes" for
        question A answer question B that opened later."""
        since = (self.now() - timedelta(days=2)).astimezone(timezone.utc).isoformat()
        sent = self.store.sent_since(since)
        replied = (message.get("reply_to_message") or {}).get("message_id")
        if replied is not None:
            for package in sent:
                for row in package["sent"]:
                    if (isinstance(row, dict) and row.get("via") == "telegram"
                            and str(row.get("message_id")) == str(replied)):
                        return package, row, None
            return None, None, NO_TARGET_WORDS
        for package in sent:
            ref = (package["refs"] or [""])[0]
            answer = (package.get("answers") or {}).get(ref) if isinstance(package.get("answers"), dict) else None
            if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
                continue
            if any(isinstance(row, dict) and row.get("via") == "telegram" and not row.get("settled")
                   for row in package["sent"]):
                return None, None, NO_TARGET_WORDS
        return None, None, "Nothing waits on you here now."

    def _reply(self, chat_id: str, text: str, message: Mapping[str, Any]) -> dict[str, Any]:
        from .reach_service import is_later_words

        package, asked, refusal = self._open_package(message)
        if package is None or asked is None:
            self._send(chat_id, refusal or "Nothing waits on you here now.", data_class="reach_refusal")
            return {"action": "no_package"}
        said_at = message.get("date")
        asked_at = _epoch(asked.get("at"))
        if (asked_at is not None and isinstance(said_at, (int, float))
                and said_at < asked_at - REPLY_SKEW_SECONDS):
            # A message written before the question was asked never answers it.
            self._send(chat_id, OLD_MESSAGE_WORDS, data_class="reach_refusal")
            return {"action": "too_old"}
        body = dict(package["body"] or {})
        ref = str(body.get("ref") or "")
        words = " ".join(text.lower().split()).strip(".!")
        choices = list(body.get("choices") or [])
        by_word = {str(row["label"]).lower(): row["id"] for row in choices}
        by_word.update({alias: target for alias, target in _WORD_ALIASES.items()
                        if target in {row["id"] for row in choices}})
        message_id = asked.get("message_id")
        if isinstance(body.get("text"), Mapping) and not is_later_words(words):
            # DIR10: the agent asks; his reply in words is the answer.
            try:
                self.briefing().answer_package(package["id"], ref, "answer", via="telegram", reason=text, binding=(package.get("body") or {}).get("binding"))
            except ServiceError as exc:
                self._send(chat_id, exc.detail)
                return {"action": "refused", "code": exc.code}
            self._send(chat_id, "Typed to the agent.")
            return {"action": "answered", "choice": "answer"}
        if words.startswith("waive"):
            link = "Open it on your desk."
            self._send(chat_id, f"Waive on the page, with your reason. {link}")
            return {"action": "waive_refused"}
        if is_later_words(words):
            later = re.sub(r"^(ask me )?later\b", "", words).strip() or None
            if words in ("tonight", "tomorrow"):
                later = words
            return self._answer(chat_id, None, message_id, package, ref, "later", later=later or "")
        choice = by_word.get(words)
        if choice is None and words in ("yes", "ok", "okay", "y"):
            if len(choices) == 2 and choices[0]["id"] in ("go_on", "met", "merge", "resume", "continue", "apply",
                                                          "add", "send"):
                choice = choices[0]["id"]
            else:
                self._send(chat_id, f"Choose one: {' or '.join(row['label'] for row in choices)}.")
                return {"action": "which"}
        if choice is None and words in ("no", "n", "nope"):
            if len(choices) == 2 and choices[1]["id"] in ("not_yet", "park"):
                choice = choices[1]["id"]
            else:
                self._send(chat_id, f"Choose one: {' or '.join(row['label'] for row in choices)}.")
                return {"action": "which"}
        if choice is not None:
            if (str(body.get("kind")), choice) in _SECOND_TAP:
                self._second[(package["id"], choice)] = time.monotonic() + SECOND_TAP_SECONDS
                label = next((row["label"] for row in choices if row["id"] == choice), choice)
                self._send(chat_id, _second_tap_words(body, choice),
                           [[{"text": label, "callback_data": f"{CALLBACK}|{package['id']}|{choice}!"},
                             {"text": "Not now", "callback_data": f"{CALLBACK}|{package['id']}|back"}]])
                return {"action": "second_tap", "choice": choice}
            return self._answer(chat_id, None, message_id, package, ref, choice)
        if body.get("program_id"):
            return self._shape(chat_id, str(body["program_id"]), text)
        self._send(chat_id, "Kept as your words. Nothing is decided.")
        return {"action": "kept"}

    # ── a free sentence: a shaping sentence (PG-LANG §4) ─────────────

    def _shape(self, chat_id: str, program_id: str, sentence: str) -> dict[str, Any]:
        try:
            answer = self.programs().shape(TELEGRAM_OWNER, program_id, sentence, apply=False)
        except ServiceError as exc:
            self._send(chat_id, _line(exc.detail))
            return {"action": "shape_refused", "code": exc.code}
        rows = list(answer.get("changes") or [])
        if not rows:
            self._send(chat_id, _line(answer.get("question") or "No change. The program stays as it is."))
            return {"action": "shape_empty"}
        ident = secrets.token_hex(4)
        self._shapes[ident] = {"program_id": program_id, "proposed_text": answer.get("proposed_text"),
                               "base": answer.get("base"), "expires": time.monotonic() + 3600}
        lines = [_line(f"Change: {answer.get('say') or answer.get('sentence')}")]
        lines += [_line(f"{row.get('where')}: {row.get('say') or row.get('field')}") for row in rows[:5]]
        lines.append("Apply it, or Not this.")
        self._send(chat_id, "\n".join(lines[:MAX_LINES]),
                   [[{"text": "Apply", "callback_data": f"{CALLBACK}|shape|{ident}|apply"},
                     {"text": "Not this", "callback_data": f"{CALLBACK}|shape|{ident}|no"}]])
        return {"action": "shape_preview", "id": ident, "rows": len(rows)}

    def _shape_tap(self, chat_id: str, callback_id: str, message: Mapping[str, Any], ident: str,
                   act: str) -> dict[str, Any]:
        pending = self._shapes.pop(ident, None)
        message_id = message.get("message_id")
        head = str(message.get("text") or "").split("\n", 1)[0]
        if pending is None or pending["expires"] < time.monotonic():
            self._ack(callback_id, "This change is old. Write it again.")
            return {"action": "shape_expired"}
        if act != "apply":
            self._edit(chat_id, message_id, fence(f"{head}\nNot this. Nothing changed."))
            self._ack(callback_id, "Nothing changed.")
            return {"action": "shape_dropped"}
        try:
            applied = self.programs().text_apply(TELEGRAM_OWNER, pending["program_id"], pending["proposed_text"],
                                                 dry_run=False, base=pending["base"])
        except ServiceError as exc:
            self._edit(chat_id, message_id, fence(f"{head}\n{_line(exc.detail)}"))
            self._ack(callback_id, exc.detail[:190])
            return {"action": "shape_refused", "code": exc.code}
        words = "Applied." if applied.get("applied") else "It did not apply. Open the program on your desk."
        self._edit(chat_id, message_id, fence(f"{head}\n{words}"))
        self._ack(callback_id, words)
        return {"action": "shape_applied", "applied": bool(applied.get("applied"))}


def _link_in(text: Any) -> Optional[str]:
    found = re.search(r"Open the page: (https?://\S+)", str(text or ""))
    return found.group(1) if found else None


def _epoch(stamp: Any) -> Optional[float]:
    """An ISO stamp as seconds since the epoch (Telegram's ``date``), or None."""
    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()


def _clock(stamp: Any) -> str:
    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone().strftime("%H:%M")


_DEFAULT: Optional[TelegramReach] = None
_DEFAULT_DB: Any = None
_DEFAULT_LOCK = threading.Lock()


def default_telegram_reach(db: Any = None) -> TelegramReach:
    global _DEFAULT, _DEFAULT_DB
    if db is None:
        from ..db import get_database
        from ..runtime import composition

        db = composition.db_or(get_database)
    with _DEFAULT_LOCK:
        if _DEFAULT is None or _DEFAULT_DB is not db:
            _DEFAULT = TelegramReach(db)
            _DEFAULT_DB = db
        return _DEFAULT


__all__ = ["CHAT_SLOT", "DESTINATION_WORDS", "TELEGRAM_ENV", "TELEGRAM_OWNER", "TOKEN_SLOT", "TelegramReach",
           "TelegramRefused", "bot_token", "cadence_config", "call_reach", "choice_buttons", "default_telegram_reach",
           "fence", "later_buttons", "paired_chat", "remember_port", "render", "repair_token", "telegram_on",
           "token_where"]
