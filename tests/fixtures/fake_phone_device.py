"""A fake paired phone for the Phone tests and the fixture recorder.

It is what the HoldSpeak Apple app will be, minus the screen: it redeems a
pairing token through the real ``POST /api/phone/devices``, keeps its device
token, reads the event log (``GET /api/phone/events?after_seq=``) or streams
it (``/api/phone/ws?after_seq=``), answers or ignores a ringing call, and
replies to a message. Every request carries only its own device token,
never the hub token.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional


class FakePhoneDevice:
    def __init__(self, client: Any, *, name: str = "Karol's iPhone", platform: str = "test",
                 push_token: Optional[str] = "fake-push-token", answer_calls: bool = True) -> None:
        self.client = client
        self.name = name
        self.platform = platform
        self.push_token = push_token
        self.answer_calls = answer_calls
        self.device_id = ""
        self.jwt = ""
        self.push_secret = ""
        self.last_seq = 0
        self.seen: list[dict[str, Any]] = []

    # ── the wire ──────────────────────────────────────────────────────

    def headers(self) -> dict[str, str]:
        # Only the device token: a test client's hub token is blanked.
        return {"Authorization": f"Bearer {self.jwt}", "X-HoldSpeak-Token": ""}

    def pair(self, pair_token: str) -> dict[str, Any]:
        response = self.client.post("/api/phone/devices", json={
            "pair_token": pair_token, "name": self.name, "platform": self.platform,
            **({"push_token": self.push_token, "push_kind": "null"} if self.push_token else {}),
        }, headers={"Authorization": "", "X-HoldSpeak-Token": ""})
        assert response.status_code == 201, response.text
        body = response.json()
        self.device_id, self.jwt, self.push_secret = body["device_id"], body["device_jwt"], body["push_secret"]
        return body

    def get(self, path: str) -> Any:
        return self.client.get(path, headers=self.headers())

    def post(self, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        return self.client.post(path, json=body or {}, headers=self.headers())

    def events(self) -> list[dict[str, Any]]:
        """Every event after the last one this phone saw (paged)."""
        out: list[dict[str, Any]] = []
        while True:
            response = self.get(f"/api/phone/events?after_seq={self.last_seq}")
            assert response.status_code == 200, response.text
            page = response.json()
            out.extend(page["events"])
            if page["events"]:
                self.last_seq = page["events"][-1]["seq"]
            if not page["has_more"]:
                break
        self.seen.extend(out)
        return out

    def stream(self, *, after_seq: Optional[int] = None, until: Callable[[dict[str, Any]], bool] = lambda e: False,
               limit: int = 50, between: Optional[Callable[[], None]] = None) -> tuple[list[dict[str, Any]], Any]:
        """Open the socket, read the hello and the replay (and live events)
        until ``until`` says stop; ``between`` runs after the hello."""
        after = self.last_seq if after_seq is None else after_seq
        got: list[dict[str, Any]] = []
        close = None
        with self.client.websocket_connect(f"/api/phone/ws?after_seq={after}", headers=self.headers()) as socket:
            hello = socket.receive_json()
            got.append(hello)
            if between is not None:
                between()
            for _ in range(limit):
                try:
                    event = socket.receive_json()
                except Exception as exc:  # the hub closed the socket (a revoke)
                    close = exc
                    break
                if event.get("type") == "ping":
                    continue
                got.append(event)
                if event.get("seq"):
                    self.last_seq = max(self.last_seq, int(event["seq"]))
                if until(event):
                    break
        self.seen.extend(event for event in got if event.get("seq"))
        return got, close

    # ── what the app does ─────────────────────────────────────────────

    def reply(self, text: str, reply_to: Optional[str]) -> dict[str, Any]:
        response = self.post("/api/phone/messages", {"text": text, "reply_to": reply_to})
        assert response.status_code == 201, response.text
        return response.json()

    def read(self, message_id: str) -> Any:
        return self.post(f"/api/phone/messages/{message_id}/read")

    def accept(self, call_id: str) -> Any:
        return self.post(f"/api/phone/calls/{call_id}/accept")

    def decline(self, call_id: str) -> Any:
        return self.post(f"/api/phone/calls/{call_id}/decline")

    def end(self, call_id: str) -> Any:
        return self.post(f"/api/phone/calls/{call_id}/end")

    def handle(self, events: list[dict[str, Any]]) -> list[str]:
        """Answer the ringing calls (or let them ring); returns the calls it took."""
        taken = []
        for event in events:
            if event.get("type") == "call.invite" and self.answer_calls:
                call_id = event["data"]["call"]["id"]
                if self.accept(call_id).status_code == 200:
                    taken.append(call_id)
        return taken

    @staticmethod
    def messages_in(events: list[dict[str, Any]], direction: str = "to_phone") -> list[dict[str, Any]]:
        return [event["data"]["message"] for event in events
                if event.get("type") == "message.new" and event["data"]["message"]["direction"] == direction]

    @staticmethod
    def dump(events: list[dict[str, Any]]) -> str:
        return json.dumps(events, indent=2)


__all__ = ["FakePhoneDevice"]
