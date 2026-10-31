"""Telegram reach (PG-DIRECTION DIR5, DIRECTION-2026-10-31.md §5, §8; all defaults approved 2026-10-31).

- **One bot, one owner chat.** The Cadence bot is the reach bot. Pairing is
  a one-time code shown on the desk (six digits, ten minutes): the first chat
  that sends ``/pair <code>`` is the one owner chat; a second chat cannot pair
  while one is paired. **Unpair** removes it.
- **The secret in the keystore.** The bot token is in the keystore slot
  ``reach.telegram.bot_token`` (the macOS Keychain or the Secret Service, or
  the rig's ``HOLDSPEAK_CHANNEL_KEYSTORE_FILE``), and so is the paired chat.
  :func:`repair_token` moves a token found in the config file into the
  keystore once and blanks it in the file, with one log line.
- **The message.** At most eight lines of plain text (no Markdown): the
  head, the question, what changed, each choice with what it does, the page
  link. Inline buttons: the item's own choices and **Later**; Later opens a
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

log = get_logger("services.telegram_reach")

TELEGRAM_ENV = "HOLDSPEAK_TELEGRAM"
SERVICE = "HoldSpeak Reach"
TOKEN_SLOT = "reach.telegram.bot_token"
CHAT_SLOT = "reach.telegram.chat"
CONNECTOR = "reach-telegram"
#: The named destination (the egress ledger's words).
DESTINATION_WORDS = "Telegram · owner chat"
PAIR_MINUTES = 10
SECOND_TAP_SECONDS = 120
MAX_LINES = 8
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
    """The keystore (the rig's key file, else the native keychain), or None."""
    from .channel_key_file import FileChannelKeyStore, channel_keystore_path

    path = channel_keystore_path()
    if path is not None:
        return FileChannelKeyStore(path, SERVICE, _Missing, "missing", "locked")
    from ..people.keys import home_has_a_keychain

    if not home_has_a_keychain():
        return None
    try:
        import keyring

        backend = keyring.get_keyring()
    except Exception as exc:
        log.info(f"telegram: no keychain ({type(exc).__name__})")
        return None

    class _Chain:
        def get(self, slot: str) -> str:
            value = backend.get_password(SERVICE, slot)
            if not value:
                raise _Missing("missing")
            return value

        def put(self, slot: str, value: str) -> None:
            if value:
                backend.set_password(SERVICE, slot, value)
            else:
                try:
                    backend.delete_password(SERVICE, slot)
                except Exception:
                    pass

    return _Chain()


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
        return {"ok": False, "error_code": int(exc.code), "description": str(exc.reason or "")}
    except Exception as exc:
        return {"ok": False, "description": _redact(str(exc), token)}


def _redact(text: str, token: str) -> str:
    return text.replace(token, "<token>") if token else text


def fence(text: str) -> str:
    """§5 "What is never sent": refuse a diff, a key or a token; redact a
    secret the Phone's way. Returns the text to send."""
    from ..redaction import redact_secrets

    for pattern in _NEVER:
        if pattern.search(text):
            raise TelegramRefused("never_sent", "The message held something that is never sent to Telegram.")
    return redact_secrets(text)


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


def render(body: Mapping[str, Any], link: Optional[str], now: datetime) -> str:
    """The package in at most eight lines of plain text (§5 "The message")."""
    head = str(body.get("head") or "")
    waits = _waits(body.get("since"), now)
    lines = [_line(" · ".join(part for part in (head, waits) if part)), _line(body.get("question"))]
    changed = [row.get("line") for row in body.get("changed") or [] if row.get("line")]
    if changed:
        lines.append(_line(f"Changed: {changed[0]}"))
    choices = list(body.get("choices") or [])
    room = MAX_LINES - len(lines) - 1
    for choice in choices[: max(0, room)]:
        lines.append(_line(f"{choice['label']}: {choice['consequence']}"))
    lines.append(f"Open the page: {link}" if link else "Open it on your desk.")
    return fence("\n".join(lines[:MAX_LINES]))


def choice_buttons(package_id: str, body: Mapping[str, Any]) -> list[list[dict[str, str]]]:
    row = [{"text": choice["label"], "callback_data": f"{CALLBACK}|{package_id}|{choice['id']}"}
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
        self._briefing = briefing
        self._reach = reach
        self._programs = programs
        self._clock = clock
        self._link = link
        self._cadence = cadence
        self._pairing: Optional[dict[str, Any]] = None  # {hash, expires_at}
        self._second: dict[tuple[str, str], float] = {}
        self._shapes: dict[str, dict[str, Any]] = {}

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

    def _api(self, method: str, params: Mapping[str, Any], *, data_class: str = "reach_package") -> dict[str, Any]:
        token = bot_token()
        if not token or not telegram_on():
            return {"ok": False, "description": "telegram is off"}
        if self._call is call_reach:
            result = call_reach(token, method, params, data_class=data_class)
        else:
            result = self._call(token, method, dict(params))
        if not result.get("ok", True):
            log.warning(f"telegram {method} failed: {_redact(str(result.get('description')), token)}")
        return result

    def _changed(self, ident: str, verb: str) -> None:
        try:
            from ..runtime import composition

            composition.notify_desk_changed("reach", ident, verb)
        except Exception:
            pass

    # ── state ────────────────────────────────────────────────────────

    def live(self) -> bool:
        """Sends may go: Telegram on, a token, a paired chat."""
        return telegram_on() and bool(bot_token()) and paired_chat() is not None

    def pairing_open(self) -> bool:
        pairing = self._pairing
        return bool(pairing and pairing["expires"] > time.monotonic())

    def should_poll(self) -> bool:
        """Nothing polls when unpaired and no code is open, or when off."""
        return telegram_on() and bool(bot_token()) and (paired_chat() is not None or self.pairing_open())

    def status(self) -> dict[str, Any]:
        chat = paired_chat()
        pairing = None
        if self.pairing_open() and self._pairing:
            pairing = {"expires_at": self._pairing["expires_at"]}
        return {"on": telegram_on(), "token": token_where(),
                "paired": {"name": str(chat.get("name") or ""), "at": chat.get("at")} if chat else None,
                "pairing": pairing, "destination": DESTINATION_WORDS}

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
        _write(TOKEN_SLOT, token)
        self._changed("telegram", "token")
        return {"token": token_where()}

    def start_pairing(self, principal: Any) -> dict[str, Any]:
        self._require_owner(principal)
        if paired_chat() is not None:
            raise TelegramRefused("already_paired", "A chat is paired. Unpair it first.")
        if not bot_token():
            raise TelegramRefused("token_missing", "Put the bot token in first.", status=409)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires = self.now() + timedelta(minutes=PAIR_MINUTES)
        with _lock:
            self._pairing = {"hash": hashlib.sha256(code.encode()).hexdigest(),
                             "expires": time.monotonic() + PAIR_MINUTES * 60,
                             "expires_at": expires.astimezone(timezone.utc).isoformat()}
        try:
            self.reach().wake()
        except Exception:
            pass
        self._changed("telegram", "pairing")
        return {"code": code, "words": f"{code[:3]} {code[3:]}", "expires_at": self._pairing["expires_at"],
                "say": f"Send /pair {code[:3]} {code[3:]} to your bot"}

    def unpair(self, principal: Any) -> dict[str, Any]:
        self._require_owner(principal)
        with _lock:
            self._pairing = None
            store = _store()
            if store is not None:
                store.put(CHAT_SLOT, "")
        self._changed("telegram", "unpaired")
        return {"paired": None}

    # ── briefs ───────────────────────────────────────────────────────

    def brief(self, ref: str) -> dict[str, Any]:
        """Make a package for one held item and send it to the owner chat."""
        chat = paired_chat()
        if not self.live() or chat is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        made = self.briefing().make(TELEGRAM_OWNER, [ref])
        return self.send_package(made["id"], made["path"])

    def send_package(self, package_id: str, path: str) -> dict[str, Any]:
        chat = paired_chat()
        package = self.store.get(package_id)
        if chat is None or package is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        body = dict(package["body"] or {})
        text = render(body, self.link_for(path), self.now())
        result = self._api("sendMessage", {"chat_id": chat["id"], "text": text,
                                           "reply_markup": {"inline_keyboard": choice_buttons(package_id, body)}})
        if not result.get("ok"):
            raise TelegramRefused("telegram_failed", "Telegram did not take the message. Nothing was sent.")
        message_id = (result.get("result") or {}).get("message_id")
        sent = list(package.get("sent") or [])
        sent.append({"via": "telegram", "at": self.now().astimezone(timezone.utc).isoformat(),
                     "message_id": message_id})
        self.store.set_sent(package_id, sent)
        self._changed(package_id, "sent")
        return {"id": package_id, "message_id": message_id, "text": text}

    def digest(self, items: list[Mapping[str, Any]]) -> dict[str, Any]:
        """One message: the count and one line per item with its kind word
        (§5 "The digest"). No buttons for the items."""
        from .briefing_service import KIND_WORDS

        chat = paired_chat()
        if chat is None:
            raise TelegramRefused("telegram_not_paired", "Pair Telegram first.")
        rows = items[:12]
        head = "1 waits on you" if len(items) == 1 else f"{len(items)} wait on you"
        lines = [head] + [_line(f"{KIND_WORDS.get(str(item.get('kind')), 'Waits on you')} · "
                                f"{item.get('program_title')} · step {item.get('ordinal')}") for item in rows]
        lines.append("Open your desk to see each one.")
        text = fence("\n".join(lines))
        result = self._api("sendMessage", {"chat_id": chat["id"], "text": text})
        return {"ok": bool(result.get("ok")), "text": text, "items": len(rows)}

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
            self._edit(chat["id"], row["message_id"], self._settled_text(body, package, words))
            row["settled"] = words
        self.store.set_sent(package["id"], list(package.get("sent") or []))

    def _settled_text(self, body: Mapping[str, Any], package: Mapping[str, Any], words: str,
                      link: Optional[str] = None) -> str:
        lines = [_line(body.get("head")), _line(body.get("question"))]
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

    def _edit(self, chat_id: Any, message_id: Any, text: str,
              keyboard: Optional[list[list[dict[str, str]]]] = None) -> dict[str, Any]:
        params: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if keyboard is not None:
            params["reply_markup"] = {"inline_keyboard": keyboard}
        return self._api("editMessageText", params)

    def _send(self, chat_id: Any, text: str, keyboard: Optional[list[list[dict[str, str]]]] = None,
              *, data_class: str = "reach_package") -> dict[str, Any]:
        params: dict[str, Any] = {"chat_id": chat_id, "text": fence(text)}
        if keyboard:
            params["reply_markup"] = {"inline_keyboard": keyboard}
        return self._api("sendMessage", params, data_class=data_class)

    def _ack(self, callback_id: str, text: str = "") -> None:
        self._api("answerCallbackQuery", {"callback_query_id": callback_id, "text": text},
                  data_class="reach_decision_ack")

    # ── updates ──────────────────────────────────────────────────────

    def poll_once(self, offset: Optional[int]) -> Optional[int]:
        """One getUpdates round (long poll, 25 s); the next offset."""
        params: dict[str, Any] = {"timeout": 25}
        if offset is not None:
            params["offset"] = offset
        result = self._api("getUpdates", params, data_class="reach_update_cursor")
        next_offset = offset
        for update in result.get("result", []) or []:
            try:
                self.handle_update(update)
            except Exception as exc:
                log.error(f"telegram update failed: {type(exc).__name__}: {_redact(str(exc), bot_token())}")
            next_offset = int(update.get("update_id", 0)) + 1
        return next_offset

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
        if command == "pair":
            return self._pair(chat_id, text, message)
        if not self._is_owner_chat(chat_id):
            self._send(chat_id, "This chat is not paired.", data_class="reach_refusal")
            return {"action": "rejected"}
        if text.startswith("/"):
            return self._cadence_update(update)
        return self._reply(chat_id, text, message)

    def _is_owner_chat(self, chat_id: str) -> bool:
        chat = paired_chat()
        return chat is not None and str(chat["id"]) == str(chat_id)

    def _pair(self, chat_id: str, text: str, message: Mapping[str, Any]) -> dict[str, Any]:
        code = "".join(text.split()[1:])
        with _lock:
            pairing = self._pairing
            if paired_chat() is not None:
                if self._is_owner_chat(chat_id):
                    self._send(chat_id, "This chat is paired already.", data_class="reach_refusal")
                    return {"action": "pair", "ok": True}
                self._send(chat_id, "This chat is not paired.", data_class="reach_refusal")
                return {"action": "pair", "ok": False}
            ok = bool(pairing and pairing["expires"] > time.monotonic()
                      and hashlib.sha256(code.encode()).hexdigest() == pairing["hash"])
            if not ok:
                self._send(chat_id, "Wrong or old code. Make a new one in Settings ▸ Reach.",
                           data_class="reach_refusal")
                return {"action": "pair", "ok": False}
            sender = dict(message.get("from") or {})
            name = str(sender.get("first_name") or (message.get("chat") or {}).get("first_name") or "")
            _write(CHAT_SLOT, json.dumps({"id": chat_id, "name": name,
                                          "at": self.now().astimezone(timezone.utc).isoformat()}))
            self._pairing = None
        self._send(chat_id, "Paired. HoldSpeak sends what waits on you here.", data_class="reach_refusal")
        self._changed("telegram", "paired")
        return {"action": "pair", "ok": True}

    def _cadence_update(self, update: Mapping[str, Any]) -> dict[str, Any]:
        """Commands and Cadence's own buttons go to the Cadence surface."""
        try:
            if self._cadence is not None:
                surface = self._cadence()
            else:
                from ..cadence_telegram import TelegramSurface
                from ..config import Config

                surface = TelegramSurface(self.db, cadence_config(Config.load().cadence_telegram))
            return {"action": "cadence", "result": surface.handle_update(dict(update))}
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
            result = self.briefing().answer_package(package["id"], ref, choice, via="telegram", later=later)
        except ServiceError as exc:
            words = exc.detail
            if exc.code == "answered_already":
                outcome = (exc.context or {}).get("outcome") or {}
                words = f"Answered already: {outcome.get('words')}" if outcome.get("words") else exc.detail
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

    def _open_package(self, message: Mapping[str, Any]) -> tuple[Optional[dict[str, Any]], Optional[str]]:
        """The package a text answers: the replied-to message, else the one
        open package sent to Telegram."""
        since = (self.now() - timedelta(days=2)).astimezone(timezone.utc).isoformat()
        sent = self.store.sent_since(since)
        replied = (message.get("reply_to_message") or {}).get("message_id")
        if replied is not None:
            for package in sent:
                if any(isinstance(row, dict) and row.get("message_id") == replied for row in package["sent"]):
                    return package, None
        open_rows = []
        for package in sent:
            ref = (package["refs"] or [""])[0]
            answer = (package.get("answers") or {}).get(ref) if isinstance(package.get("answers"), dict) else None
            if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
                continue
            if any(isinstance(row, dict) and row.get("via") == "telegram" and not row.get("settled")
                   for row in package["sent"]):
                open_rows.append(package)
        if len(open_rows) == 1:
            return open_rows[0], None
        if not open_rows:
            return None, "Nothing waits on you here now."
        return None, "Reply to the message you answer."

    def _reply(self, chat_id: str, text: str, message: Mapping[str, Any]) -> dict[str, Any]:
        from .reach_service import is_later_words

        package, refusal = self._open_package(message)
        if package is None:
            self._send(chat_id, refusal or "Nothing waits on you here now.")
            return {"action": "no_package"}
        body = dict(package["body"] or {})
        ref = str(body.get("ref") or "")
        words = " ".join(text.lower().split()).strip(".!")
        choices = list(body.get("choices") or [])
        by_word = {str(row["label"]).lower(): row["id"] for row in choices}
        by_word.update({alias: target for alias, target in _WORD_ALIASES.items()
                        if target in {row["id"] for row in choices}})
        message_id = next((row.get("message_id") for row in package["sent"]
                           if isinstance(row, dict) and row.get("via") == "telegram"), None)
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
                self._send(chat_id, f"Which one: {' or '.join(row['label'] for row in choices)}?")
                return {"action": "which"}
        if choice is None and words in ("no", "n", "nope"):
            if len(choices) == 2 and choices[1]["id"] in ("not_yet", "park"):
                choice = choices[1]["id"]
            else:
                self._send(chat_id, f"Which one: {' or '.join(row['label'] for row in choices)}?")
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
