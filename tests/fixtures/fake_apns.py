"""A fake APNs: an HTTP/2 server (h2 with prior knowledge, plain TCP) on 127.0.0.1.

``ApnsPush(key, host=fake.url)`` sends to it exactly as it sends to Apple
(the client speaks HTTP/2 only). The server keeps each request it took
(method, path, headers, the JSON body) and answers with the status and body
the test set for the device token (Apple's own shapes: ``200`` with an
``apns-id``, ``410`` ``{"reason": "Unregistered"}``, ``400``
``{"reason": "BadDeviceToken"}``). Nothing leaves the machine.
"""
from __future__ import annotations

import json
import socket
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

import h2.config
import h2.connection
import h2.events


@dataclass
class FakeApns:
    answers: dict[str, tuple[int, dict[str, Any]]] = field(default_factory=dict)
    requests: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(8)
        self._sock.settimeout(0.2)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, name="fake-apns", daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._sock.getsockname()[1]}"

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self._sock.close()

    def __enter__(self) -> "FakeApns":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ── the server ────────────────────────────────────────────────────

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        h2c = h2.connection.H2Connection(config=h2.config.H2Configuration(client_side=False))
        h2c.initiate_connection()
        conn.sendall(h2c.data_to_send())
        streams: dict[int, dict[str, Any]] = {}
        conn.settimeout(5)
        try:
            while True:
                data = conn.recv(65535)
                if not data:
                    return
                for event in h2c.receive_data(data):
                    if isinstance(event, h2.events.RequestReceived):
                        headers = {_text(k): _text(v) for k, v in event.headers}
                        streams[event.stream_id] = {"headers": headers, "body": b""}
                    elif isinstance(event, h2.events.DataReceived):
                        streams[event.stream_id]["body"] += event.data
                        h2c.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
                    elif isinstance(event, h2.events.StreamEnded):
                        self._answer(h2c, event.stream_id, streams.pop(event.stream_id))
                    elif isinstance(event, h2.events.ConnectionTerminated):
                        conn.sendall(h2c.data_to_send())
                        return
                conn.sendall(h2c.data_to_send())
        except OSError:
            return
        finally:
            conn.close()

    def _answer(self, h2c: Any, stream_id: int, request: dict[str, Any]) -> None:
        headers = request["headers"]
        path = headers.get(":path", "")
        token = path.rsplit("/", 1)[-1]
        self.requests.append({
            "method": headers.get(":method"), "path": path, "headers": headers,
            "body": json.loads(request["body"] or b"{}"),
        })
        status, body = self.answers.get(token, (200, {}))
        raw = json.dumps(body).encode() if body else b""
        out = [(":status", str(status)), ("apns-id", str(uuid.uuid4()).upper())]
        if raw:
            out += [("content-type", "application/json"), ("content-length", str(len(raw)))]
        h2c.send_headers(stream_id, out, end_stream=not raw)
        if raw:
            h2c.send_data(stream_id, raw, end_stream=True)


def _text(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


__all__ = ["FakeApns"]
