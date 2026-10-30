"""A fake Telnyx API v2 for the Line's setup tests (LINE-3b): a real HTTP
server on 127.0.0.1, the only Telnyx any test reaches.

The response shapes are WRITTEN FROM THE DOCS, not recorded from a live
account (no live Telnyx call is made from this repo's tests): the field names
and the example values follow Telnyx's OpenAPI spec
(``team-telnyx/openapi`` ``openapi/spec3.json``) and its API reference pages,
read 2026-10-29: ``/balance``, ``/outbound_voice_profiles``,
``/credential_connections``, ``/available_phone_numbers``, ``/number_orders``,
``/phone_numbers``. Errors are Telnyx's ``{"errors": [{code, title, detail}]}``.

    with running_fake_telnyx(key="KEY-test") as fake:
        os.environ["HOLDSPEAK_TELNYX_API"] = fake.url
        ...
        fake.requests  # [(method, path, query, body)]
"""
from __future__ import annotations

import json
import threading
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlsplit

#: Ten numbers in 212 (Telnyx's example: "+19705555098", upfront 3.21, monthly 6.54; ours are
#: the docs' shape with 212 numbers and the US local price list).
AVAILABLE = [
    {"record_type": "available_phone_number", "phone_number": f"+1212555{100 + i:04d}",
     "vanity_format": "", "best_effort": False, "quickship": True, "reservable": True,
     "cost_information": {"upfront_cost": "1.00", "monthly_cost": "1.00", "currency": "USD"},
     "features": [{"name": "sms"}, {"name": "voice"}],
     "region_information": [{"region_type": "country_code", "region_name": "US"},
                            {"region_type": "rate_center", "region_name": "NEW YORK"}]}
    for i in range(12)
]
STAMP = "2026-10-29T21:00:00.000Z"


def _error(code: str, title: str, detail: str) -> dict[str, Any]:
    return {"errors": [{"code": code, "title": title, "detail": detail}]}


class FakeTelnyx:
    def __init__(self, key: str) -> None:
        self.key = key
        self.requests: list[tuple[str, str, dict[str, str], Any]] = []
        self.profiles: list[dict[str, Any]] = []
        self.connections: list[dict[str, Any]] = []
        self.numbers: list[dict[str, Any]] = []
        self.orders: list[dict[str, Any]] = []
        self.balance = {"record_type": "balance", "pending": "0.00", "balance": "20.00", "credit_limit": "0.00",
                        "available_credit": "20.00", "currency": "USD"}
        #: The order's status Telnyx answers (``success`` or ``pending``).
        self.order_status = "success"
        #: A path that answers this error (``{"/number_orders": (422, "...")}``).
        self.fail: dict[str, tuple[int, str]] = {}
        self.url = ""

    # ── the routes ───────────────────────────────────────────────────

    def handle(self, method: str, path: str, query: dict[str, str], body: Any) -> tuple[int, Any]:
        if path in self.fail:
            status, detail = self.fail[path]
            return status, _error("10015", "Bad Request", detail)
        if method == "GET" and path == "/balance":
            return 200, {"data": dict(self.balance)}
        if path == "/outbound_voice_profiles":
            if method == "GET":
                part = query.get("filter[name][contains]", "")
                rows = [p for p in self.profiles if part.lower() in p["name"].lower()]
                return 200, {"data": rows, "meta": self._meta(rows)}
            name = str((body or {}).get("name") or "")
            if len(name) < 3:
                return 422, _error("10015", "Invalid name", "name must be at least 3 characters")
            row = {"id": str(1293384261075731400 + len(self.profiles)), "record_type": "outbound_voice_profile",
                   "name": name, "connections_count": 0, "traffic_type": "conversational", "service_plan": "global",
                   "enabled": True, "whitelisted_destinations": ["US", "CA"], "created_at": STAMP, "updated_at": STAMP}
            self.profiles.append(row)
            return 200, {"data": row}
        if path == "/credential_connections":
            if method == "GET":
                part = query.get("filter[connection_name][contains]", "")
                rows = [self._shown(c) for c in self.connections if part.lower() in c["connection_name"].lower()]
                return 200, {"data": rows, "meta": self._meta(rows)}
            body = body or {}
            user, password = str(body.get("user_name") or ""), str(body.get("password") or "")
            if not (4 <= len(user) <= 32 and user.isalnum()) or not 8 <= len(password) <= 128:
                return 422, _error("10015", "Invalid credentials", "user_name or password is not valid")
            row = {"id": str(1684641123236054200 + len(self.connections)), "record_type": "credential_connection",
                   "active": True, "user_name": user, "password": password,
                   "connection_name": str(body.get("connection_name") or ""),
                   "sip_uri_calling_preference": str(body.get("sip_uri_calling_preference") or "disabled"),
                   "inbound": {"ani_number_format": "E.164-national", "dnis_number_format": "e164"},
                   "outbound": dict(body.get("outbound") or {}), "created_at": STAMP, "updated_at": STAMP}
            self.connections.append(row)
            return 201, {"data": dict(row)}  # the password in full on create
        if path.startswith("/credential_connections/") and method == "PATCH":
            row = next((c for c in self.connections if c["id"] == path.rsplit("/", 1)[1]), None)
            if row is None:
                return 404, _error("10005", "Resource not found", "The requested resource was not found.")
            row.update({k: v for k, v in (body or {}).items() if k in {"password", "user_name", "active"}})
            return 200, {"data": self._shown(row)}
        if method == "GET" and path == "/available_phone_numbers":
            if query.get("filter[features]") not in {None, "voice"}:
                return 400, _error("10015", "Bad filter", "features")
            area = query.get("filter[national_destination_code]", "")
            rows = [r for r in AVAILABLE if r["phone_number"][2:5] == area or not area]
            rows = rows[: int(query.get("filter[limit]") or 10)]
            return 200, {"data": rows, "meta": {"total_results": len(rows), "best_effort_results": 0},
                         "metadata": {"total_results": len(rows), "best_effort_results": 0}}
        if method == "POST" and path == "/number_orders":
            body = body or {}
            wanted = [str(p.get("phone_number") or "") for p in body.get("phone_numbers") or []]
            order_id = str(uuid.uuid4())
            numbers = []
            for number in wanted:
                row = {"id": str(1293384261075731499 + len(self.numbers)), "record_type": "phone_number",
                       "phone_number": number, "status": "active", "connection_id": str(body.get("connection_id") or ""),
                       "connection_name": "", "country_iso_alpha2": "US", "phone_number_type": "local",
                       "purchased_at": STAMP, "created_at": STAMP, "updated_at": STAMP}
                if self.order_status == "success":
                    self.numbers.append(row)
                numbers.append({"id": row["id"], "record_type": "number_order_phone_number", "phone_number": number,
                                "status": self.order_status, "requirements_met": True, "phone_number_type": "local",
                                "country_code": "US", "regulatory_requirements": []})
            order = {"id": order_id, "record_type": "number_order", "phone_numbers_count": len(numbers),
                     "connection_id": str(body.get("connection_id") or ""), "status": self.order_status,
                     "phone_numbers": numbers, "requirements_met": True, "created_at": STAMP, "updated_at": STAMP}
            self.orders.append(order)
            return 200, {"data": order}
        if method == "GET" and path == "/phone_numbers":
            digits = query.get("filter[phone_number]", "")
            rows = [n for n in self.numbers if digits in n["phone_number"]]
            return 200, {"data": rows, "meta": self._meta(rows)}
        if method == "PATCH" and path.startswith("/phone_numbers/"):
            row = next((n for n in self.numbers if n["id"] == path.rsplit("/", 1)[1]), None)
            if row is None:
                return 404, _error("10005", "Resource not found", "The requested resource was not found.")
            if "connection_id" in (body or {}):
                row["connection_id"] = str(body["connection_id"])
            return 200, {"data": dict(row)}
        return 404, _error("10005", "Resource not found", f"{method} {path}")

    @staticmethod
    def _shown(row: dict[str, Any]) -> dict[str, Any]:
        """A read masks the password (accounts made on or after 2026-09-08)."""
        return {**row, "password": "********"}

    @staticmethod
    def _meta(rows: list[Any]) -> dict[str, Any]:
        return {"total_pages": 1, "total_results": len(rows), "page_number": 1, "page_size": 250}


@contextmanager
def running_fake_telnyx(key: str = "KEY-test") -> Iterator[FakeTelnyx]:
    fake = FakeTelnyx(key)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            return None

        def _serve(self) -> None:
            parts = urlsplit(self.path)
            path = parts.path.removeprefix("/v2")
            query = dict(parse_qsl(parts.query))
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw) if raw else None
            fake.requests.append((self.command, path, query, body))
            if self.headers.get("Authorization") != f"Bearer {fake.key}":
                status, answer = 401, _error("10009", "Authentication failed", "Could not understand the provided credentials.")
            else:
                status, answer = fake.handle(self.command, path, query, body)
            data = json.dumps(answer).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_PATCH = _serve

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    fake.url = f"http://127.0.0.1:{server.server_address[1]}/v2"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield fake
    finally:
        server.shutdown()
        server.server_close()


__all__ = ["AVAILABLE", "FakeTelnyx", "running_fake_telnyx"]
