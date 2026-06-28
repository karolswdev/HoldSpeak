"""The Cadence Telegram surface (CAD-4) — remote presence.

Delivers nudges and receives decisions over Telegram. This lives OUTSIDE
`holdspeak/cadence/` on purpose: the cadence core performs no external side effect
(a guard enforces it), while this surface does the egress. Off by default; inert
without `enabled` + a token.

Security:
- the bot token is a credential — joined into the URL only at call time, never logged
  or written into a message/row;
- only `allowed_chat_ids` may read anything (an unpaired chat gets one "not paired"
  line and NO data); `/pair <code>` self-pairs when the code matches;
- a destructive decision (kill) requires a typed/tapped second confirm;
- a pushed nudge notifies the paired user (you) — that is the product, not a leak;
  everything else needs an explicit command/button.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

from .logging_config import get_logger

log = get_logger("cadence.telegram")

_API = "https://api.telegram.org/bot{token}/{method}"


def call_telegram(token: str, method: str, params: dict, *, timeout: float = 10.0) -> dict:
    """POST to the Telegram Bot API. The token is joined here and nowhere else."""
    url = _API.format(token=token, method=method)
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — fixed api.telegram.org host
            return json.loads(resp.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error_code": int(exc.code), "description": str(exc.reason or "")}
    except Exception as exc:  # network down, etc. — never raise into the poller
        return {"ok": False, "description": str(exc)}


def _redact(text: str, token: str) -> str:
    return text.replace(token, "<token>") if token else text


class TelegramSurface:
    """Stateful (per process) Telegram command + decision handler for cadence."""

    def __init__(self, db, config, *, caller: Optional[Callable] = None,
                 on_pair: Optional[Callable[[str], None]] = None):
        self._db = db
        self._config = config                # a TelegramConfig
        self._call = caller or call_telegram  # injectable for tests
        self._on_pair = on_pair
        self._paired: set[str] = set(config.allowed_chat_ids)
        self._pending_kill: set[str] = set()  # "chat:loop" awaiting a confirm

    # ── transport ────────────────────────────────────────────────────────────
    def _send(self, chat_id: str, text: str, *, buttons: Optional[list] = None) -> dict:
        params: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if buttons:
            params["reply_markup"] = {"inline_keyboard": buttons}
        result = self._call(self._config.bot_token, "sendMessage", params)
        if not result.get("ok", True):
            log.warning("telegram send failed: %s", _redact(str(result.get("description")), self._config.bot_token))
        return result

    def _answer_callback(self, callback_id: str, text: str = "") -> None:
        self._call(self._config.bot_token, "answerCallbackQuery",
                   {"callback_query_id": callback_id, "text": text})

    # ── authorization ─────────────────────────────────────────────────────────
    def is_authorized(self, chat_id: str) -> bool:
        return str(chat_id) in self._paired

    def _pair(self, chat_id: str, code: str) -> bool:
        if self._config.pairing_code and code.strip() == self._config.pairing_code:
            self._paired.add(str(chat_id))
            if self._on_pair:
                try:
                    self._on_pair(str(chat_id))
                except Exception as exc:
                    log.error("pair persist failed: %s", exc)
            return True
        return False

    # ── update dispatch ───────────────────────────────────────────────────────
    def handle_update(self, update: dict) -> dict:
        """Process one getUpdates entry. Returns a small {action,...} for tests."""
        if "callback_query" in update:
            return self._handle_callback(update["callback_query"])
        msg = update.get("message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", "")).strip()
        text = str(msg.get("text", "")).strip()
        if not chat_id or not text:
            return {"action": "ignored"}
        return self._handle_command(chat_id, text)

    def _handle_command(self, chat_id: str, text: str) -> dict:
        parts = text.split()
        cmd = parts[0].lower().lstrip("/")
        # /start and /pair are reachable before pairing; everything else is gated.
        if cmd == "start":
            self._send(chat_id, "🧷 *HoldSpeak Cadence*\nPair this chat with `/pair <code>` "
                                "to receive nudges and act on them.")
            return {"action": "start"}
        if cmd == "pair":
            ok = self._pair(chat_id, parts[1] if len(parts) > 1 else "")
            self._send(chat_id, "✅ Paired. You'll get your highest-leverage moves here."
                       if ok else "❌ Wrong or missing pairing code.")
            return {"action": "pair", "ok": ok}
        if not self.is_authorized(chat_id):
            self._send(chat_id, "🔒 This chat is not paired. Send `/pair <code>`.")
            return {"action": "rejected"}
        if cmd in ("brief", "loops"):
            self._send_loops(chat_id, brief=(cmd == "brief"))
            return {"action": cmd}
        if cmd == "status":
            self._send(chat_id, self._render_status())
            return {"action": "status"}
        self._send(chat_id, "Commands: /brief /loops /status")
        return {"action": "help"}

    def _handle_callback(self, cb: dict) -> dict:
        chat_id = str(((cb.get("message") or {}).get("chat") or {}).get("id", "")).strip()
        cb_id = str(cb.get("id", ""))
        data = str(cb.get("data", ""))
        if not self.is_authorized(chat_id):
            self._answer_callback(cb_id, "Not paired.")
            return {"action": "rejected"}
        act, _, loop_id = data.partition(":")
        loop = self._db.cadence.get_loop(loop_id) if loop_id else None
        if loop is None:
            self._answer_callback(cb_id, "Loop is gone.")
            return {"action": "missing"}
        key = f"{chat_id}:{loop_id}"
        if act == "snooze":
            from datetime import datetime, timedelta
            self._db.cadence.snooze(loop_id, (datetime.now() + timedelta(hours=24)).isoformat())
            self._answer_callback(cb_id, "Snoozed 1 day.")
        elif act == "done":
            self._db.cadence.set_status(loop_id, "closed")
            self._answer_callback(cb_id, "Marked done.")
        elif act == "kill":
            # Destructive — require a second confirm.
            self._pending_kill.add(key)
            self._send(chat_id, f"⚠️ Kill *{loop.title}* permanently?",
                       buttons=[[{"text": "Yes, kill it", "callback_data": f"killyes:{loop_id}"},
                                 {"text": "Cancel", "callback_data": f"killno:{loop_id}"}]])
            self._answer_callback(cb_id)
            return {"action": "kill_confirm"}
        elif act == "killyes":
            if key in self._pending_kill:
                self._pending_kill.discard(key)
                self._db.cadence.set_status(loop_id, "killed")
                self._answer_callback(cb_id, "Killed.")
            else:
                self._answer_callback(cb_id, "Expired — tap Kill again.")
                return {"action": "kill_expired"}
        elif act == "killno":
            self._pending_kill.discard(key)
            self._answer_callback(cb_id, "Kept.")
            return {"action": "kill_cancelled"}
        else:
            self._answer_callback(cb_id)
            return {"action": "unknown"}
        return {"action": act}

    # ── rendering ─────────────────────────────────────────────────────────────
    def _loop_buttons(self, loop) -> list:
        return [[
            {"text": "Snooze 1d", "callback_data": f"snooze:{loop.id}"},
            {"text": "Done", "callback_data": f"done:{loop.id}"},
            {"text": "Kill", "callback_data": f"kill:{loop.id}"},
        ]]

    def _send_loops(self, chat_id: str, *, brief: bool) -> None:
        loops = [l for l in self._db.cadence.list_loops() if not l.needs_review]
        if not loops:
            self._send(chat_id, "🧷 Nothing pressing right now.")
            return
        if brief:
            top = loops[0]
            from .cadence.next_action import generate_next_action
            na = generate_next_action(top)
            header = f"🧷 *Your highest-leverage move*\n\n*{top.title}*\n{na.title}"
            self._send(chat_id, header, buttons=self._loop_buttons(top))
            return
        for loop in loops[:5]:
            self._send(chat_id, f"*{loop.title}*  ·  _{loop.source_type}_  ·  {loop.stale_score:.0f}",
                       buttons=self._loop_buttons(loop))

    def _render_status(self) -> str:
        counts: dict[str, int] = {}
        for l in self._db.cadence.list_loops(include_terminal=True):
            counts[l.status] = counts.get(l.status, 0) + 1
        line = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"
        return f"🧷 *Cadence status*\nPaired chats: {len(self._paired)}\nLoops: {line}"

    # ── push (driven by the tick) ─────────────────────────────────────────────
    def push_due_nudges(self, due_loops) -> int:
        """Send each due loop to every paired chat; record one nudge per loop. Returns sent."""
        if not self._paired:
            return 0
        from .cadence.models import Nudge

        sent = 0
        for loop in due_loops:
            for chat_id in sorted(self._paired):
                self._send(chat_id, f"🧷 *{loop.title}*  ·  {loop.stale_score:.0f}",
                           buttons=self._loop_buttons(loop))
                sent += 1
            self._db.cadence.record_nudge(Nudge(loop_id=loop.id, surface="telegram",
                                                title=loop.title, status="shown"))
            self._db.cadence.bump_nudge(loop.id)
        return sent

    # ── the live poller (the owner's button) ──────────────────────────────────
    def poll_once(self, offset: Optional[int]) -> int:
        """One getUpdates round; returns the next offset. Live only."""
        params = {"timeout": 25}
        if offset is not None:
            params["offset"] = offset
        result = self._call(self._config.bot_token, "getUpdates", params)
        next_offset = offset
        for update in result.get("result", []) or []:
            try:
                self.handle_update(update)
            except Exception as exc:
                log.error("telegram update failed: %s", exc)
            next_offset = int(update.get("update_id", 0)) + 1
        return next_offset
