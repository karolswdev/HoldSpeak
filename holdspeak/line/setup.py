"""The Telnyx setup flow (LINE-3b, LINE design §8; owner 2026-10-29).

With his Telnyx API key (the keystore's ``calls.line.telnyx_api_key``) the hub:

1. **connects**: finds or creates the outbound voice profile and the
   credential connection named "HoldSpeak Line", with a generated SIP
   password (24 random bytes) that goes into ``calls.line.sip_password`` and
   nowhere else; ``calls.line.account`` gets the user, the domain, the
   connection id. Idempotent: a second press reuses the connection (and sets
   a new password only when the keystore lost the old one);
2. **finds numbers**: up to 10 with their monthly and upfront cost. Each
   row carries a ``quote``: the hub's own note of that number and that cost;
3. **buys** one ONLY on his press: the request carries the quote the
   confirm press sends, and the buy is the kernel operation
   ``calls.line.buy_number`` (owner principal only; the payload names the
   number and Telnyx's cost);
4. **assigns** it: points the number at the connection and writes
   ``calls.line.account.number``.

Every refusal says what failed, what is kept and the next action
(``context``: ``reason``, ``kept``, ``next``). Nothing here logs the key.
"""
from __future__ import annotations

import secrets as _random
import string
import threading
import time
from dataclasses import asdict
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..services.errors import ServiceError
from . import secrets as line_secrets
from .telnyx import Telnyx, TelnyxError

log = get_logger("line.setup")

CONNECTION_NAME = "HoldSpeak Line"
PROFILE_NAME = "HoldSpeak Line"
DOMAIN = "sip.telnyx.com"
OUTBOUND = f"sip:{DOMAIN};transport=tcp"
#: How long a number's quote holds (Find numbers again after this).
QUOTE_SECONDS = 15 * 60
#: The most numbers one look lists.
LIMIT = 10


def refusal(reason: str, words: str, *, kept: str, next_step: str, status: int = 409) -> ServiceError:
    return ServiceError(f"line_telnyx_{reason}", words,
                        context={"status": status, "reason": reason, "kept": kept, "next": next_step})


def _telnyx_refusal(exc: TelnyxError, doing: str, *, kept: str, next_step: str) -> ServiceError:
    if exc.status in {401, 403}:
        return refusal("key_refused", f"Telnyx did not take the key while it {doing}.", kept=kept,
                       next_step="Check the key in the Telnyx portal, then save it again.", status=502)
    if exc.status == 0:
        return refusal("unreachable", f"Telnyx did not answer while it {doing}.", kept=kept,
                       next_step="Check the network, then try again.", status=502)
    return refusal("telnyx", f"Telnyx refused while it {doing}: {exc.detail}", kept=kept, next_step=next_step,
                   status=502)


def _money(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    try:
        return f"{float(text):.2f}"
    except ValueError:
        return text


def _user() -> str:
    """A SIP user Telnyx takes: 4–32 letters and digits."""
    alphabet = string.ascii_lowercase + string.digits
    return "hs" + "".join(_random.choice(alphabet) for _ in range(10))


def _password() -> str:
    """24 random bytes (32 URL-safe characters: no ``;`` for the accounts line)."""
    return _random.token_urlsafe(24)


class TelnyxSetup:
    """The flow behind ``/api/calls/line/telnyx/*``. Every method blocks on
    the network: the routes run it off the loop."""

    def __init__(self, *, client_factory: Optional[Callable[[str], Telnyx]] = None) -> None:
        self._factory = client_factory or (lambda key: Telnyx(key))
        self._quotes: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    # ── config ────────────────────────────────────────────────────────

    @staticmethod
    def _account() -> dict[str, Any]:
        from ..config import Config

        return dict((Config.load().calls.line or {}).get("account") or {})

    @staticmethod
    def _write_account(patch: dict[str, Any]) -> dict[str, Any]:
        from ..config import Config
        from ..config.calls import CallsConfig

        config = Config.load()
        line = dict(config.calls.line or {})
        line["account"] = {**dict(line.get("account") or {}), **patch}
        calls = asdict(config.calls)
        calls["line"] = line
        config.calls = CallsConfig(**calls)
        config.save()
        return dict(config.calls.line["account"])

    def _client(self, *, kept: str) -> Telnyx:
        key = line_secrets.read(line_secrets.TELNYX_API_KEY)
        if not key:
            raise refusal("no_key", "There is no Telnyx API key.", kept=kept,
                          next_step="Save your Telnyx API key in step 1.")
        return self._factory(key)

    # ── the four presses ─────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Key present? Connection? Number? Balance (one read, when a key is there)."""
        account = self._account()
        telnyx = account.get("kind") == "telnyx"
        connection = ({"id": str(account.get("connection_id") or ""), "user": str(account.get("user") or ""),
                       "domain": str(account.get("domain") or DOMAIN)}
                      if telnyx and account.get("connection_id") else None)
        out: dict[str, Any] = {
            "key": line_secrets.where(line_secrets.TELNYX_API_KEY),
            "password": line_secrets.where(line_secrets.SIP_PASSWORD),
            "connection": connection, "number": str(account.get("number") or "") if telnyx else "",
            "balance": None, "error": "",
        }
        if out["key"] == "missing":
            return out
        try:
            with self._client(kept="") as client:
                data = client.balance()
            out["balance"] = {"balance": _money(data.get("balance")),
                              "available": _money(data.get("available_credit")),
                              "currency": str(data.get("currency") or "USD")}
        except TelnyxError as exc:
            out["error"] = ("Telnyx did not take the key." if exc.status in {401, 403}
                            else "Telnyx did not answer." if exc.status == 0 else exc.detail)
        return out

    def connect(self) -> dict[str, Any]:
        kept = "Your key is kept. Nothing was made at Telnyx."
        if line_secrets._store() is None:
            raise refusal("keystore", "The keystore is not available on this machine.", kept=kept,
                          next_step="Unlock the keychain, then press Connect again.")
        account = self._account()
        with self._client(kept=kept) as client:
            try:
                connection = client.find_connection(CONNECTION_NAME)
                created = False
                if connection is None:
                    profile = client.find_profile(PROFILE_NAME) or client.create_profile(PROFILE_NAME)
                    password = _password()
                    connection = client.create_connection(name=CONNECTION_NAME, user=_user(), password=password,
                                                          profile_id=str(profile.get("id") or ""))
                    created = True
                elif (str(account.get("connection_id") or "") == str(connection.get("id"))
                      and line_secrets.where(line_secrets.SIP_PASSWORD) == "keystore"):
                    password = ""  # the same connection, its password is in the keystore
                else:
                    password = _password()
                    client.set_connection_password(str(connection.get("id")), password)
            except TelnyxError as exc:
                raise _telnyx_refusal(exc, "made the SIP connection", kept=kept,
                                      next_step="Press Connect again.") from None
        if password:
            line_secrets.write(line_secrets.SIP_PASSWORD, password)
        saved = self._write_account({
            "kind": "telnyx", "user": str(connection.get("user_name") or ""), "domain": DOMAIN,
            "outbound": OUTBOUND, "connection_id": str(connection.get("id") or ""),
            "password_ref": line_secrets.SIP_PASSWORD,
        })
        log.info(f"line: Telnyx connection {'made' if created else 'reused'} ({saved['connection_id']})")
        return {"connected": True, "created": created, "connection_id": saved["connection_id"],
                "user": saved["user"], "domain": saved["domain"]}

    def numbers(self, area: str) -> dict[str, Any]:
        area = "".join(ch for ch in str(area or "") if ch.isdigit())[:3]
        if area and len(area) != 3:
            raise refusal("area", "An area code has three digits.", kept="Nothing changed.",
                          next_step="Type three digits, for example 212.", status=400)
        with self._client(kept="Nothing changed.") as client:
            try:
                rows = client.available_numbers(area, limit=LIMIT)
            except TelnyxError as exc:
                raise _telnyx_refusal(exc, "looked for numbers", kept="Nothing changed.",
                                      next_step="Press Find numbers again.") from None
        now = time.time()
        out = []
        with self._lock:
            self._quotes = {k: v for k, v in self._quotes.items() if now - v["at"] < QUOTE_SECONDS}
            for row in rows[:LIMIT]:
                cost = row.get("cost_information") or {}
                number = str(row.get("phone_number") or "")
                if not number:
                    continue
                quote = {"phone_number": number, "monthly_cost": _money(cost.get("monthly_cost")),
                         "upfront_cost": _money(cost.get("upfront_cost")),
                         "currency": str(cost.get("currency") or "USD"), "quote": _random.token_urlsafe(9),
                         "at": now}
                self._quotes[quote["quote"]] = quote
                out.append({k: v for k, v in quote.items() if k != "at"})
        return {"area": area, "numbers": out}

    def buy(self, principal: Any, phone_number: str, quote: str, *, database: Any = None) -> dict[str, Any]:
        """BUY (money). Refused without the quote his confirm press sends;
        the order is the kernel operation ``calls.line.buy_number``."""
        from ..kernel.line_ops import NAME
        from ..services import desk_kernel

        phone_number = str(phone_number or "").strip()
        with self._lock:
            held = self._quotes.get(str(quote or ""))
        if not quote:
            raise refusal("press_required", "A number is bought only on your press.", kept="Nothing was bought.",
                          next_step="Press Buy on the number, then confirm.", status=403)
        if held is None or held["phone_number"] != phone_number or time.time() - held["at"] >= QUOTE_SECONDS:
            raise refusal("quote_old", "That price is too old to buy on.", kept="Nothing was bought.",
                          next_step="Press Find numbers again.", status=409)
        account = self._account()
        payload = {"phone_number": phone_number, "monthly_cost": held["monthly_cost"],
                   "upfront_cost": held["upfront_cost"], "currency": held["currency"],
                   "connection_id": str(account.get("connection_id") or "")}

        def order(_minted: dict[str, Any]) -> dict[str, Any]:
            with self._client(kept="Nothing was bought.") as client:
                try:
                    return client.order_number(phone_number, connection_id=payload["connection_id"])
                except TelnyxError as exc:
                    raise _telnyx_refusal(exc, "bought the number", kept="Nothing was bought.",
                                          next_step="Press Find numbers again.") from None

        if database is None:
            from ..db import get_database

            database = get_database()
        placed, kernel = desk_kernel.run(database, principal, NAME, payload, order)
        with self._lock:
            self._quotes.pop(str(quote), None)
        log.info(f"line: bought a Telnyx number (order {placed.get('id')}, {placed.get('status')})")
        return {"phone_number": phone_number, "order_id": str(placed.get("id") or ""),
                "order_status": str(placed.get("status") or ""), "monthly_cost": payload["monthly_cost"],
                "upfront_cost": payload["upfront_cost"], "currency": payload["currency"], **(kernel or {})}

    def assign(self, phone_number: str) -> dict[str, Any]:
        phone_number = str(phone_number or "").strip()
        account = self._account()
        connection_id = str(account.get("connection_id") or "")
        if not connection_id:
            raise refusal("no_connection", "The line is not connected to Telnyx yet.", kept="The number is kept.",
                          next_step="Press Connect in step 2.")
        kept = "The number is yours and kept at Telnyx."
        with self._client(kept=kept) as client:
            try:
                found = client.find_number(phone_number)
                if found is None:
                    raise refusal("not_ready", "Telnyx has not finished the order yet.", kept=kept,
                                  next_step="Press Assign again in a minute.")
                if str(found.get("connection_id") or "") != connection_id:
                    client.assign(str(found.get("id")), connection_id)
            except TelnyxError as exc:
                raise _telnyx_refusal(exc, "pointed the number at the line", kept=kept,
                                      next_step="Press Assign again.") from None
        self._write_account({"number": phone_number})
        return {"phone_number": phone_number, "assigned": True, "connection_id": connection_id}


#: The hub's one setup flow.
TELNYX_SETUP = TelnyxSetup()

__all__ = ["CONNECTION_NAME", "DOMAIN", "OUTBOUND", "PROFILE_NAME", "QUOTE_SECONDS", "TELNYX_SETUP", "TelnyxSetup",
           "refusal"]
