"""An isolated, authenticated HoldSpeak hub for desk walks."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

import httpx


class HubFixture:
    """Run the real FastAPI hub against one temporary seeded SQLite database.

    The fixture is deliberately usable outside pytest so a walk script can be
    invoked directly in CI. Enter it before creating a browser; exit it to
    stop the uvicorn thread and discard the database.
    """

    owner_token = "desk-walk-owner-token"

    def __init__(self) -> None:
        self._tempdir: tempfile.TemporaryDirectory[str] | None = None
        self.db_path: Path | None = None
        self.database: Any | None = None
        self.server: Any | None = None
        self.url: str | None = None
        self.seed_report: dict[str, Any] | None = None

    def __enter__(self) -> "HubFixture":
        from holdspeak.db import get_database, reset_database
        from holdspeak.principals import derive_owner
        from holdspeak.services.desk_service import DeskService
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        self._tempdir = tempfile.TemporaryDirectory(prefix="holdspeak-desk-walk-")
        self.db_path = Path(self._tempdir.name) / "desk-walk.db"

        # The application routes resolve the database through this singleton.
        # Resetting it on each side prevents a walk from ever touching a user's
        # local desk database.
        reset_database()
        self.database = get_database(self.db_path)
        principal = derive_owner(self.owner_token, self.owner_token)
        assert principal is not None, "walk fixture owner principal was not created"
        self.seed_report = DeskService(self.database).seed(principal)

        callbacks = WebRuntimeCallbacks(
            on_bookmark=lambda _label: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        )
        self.server = MeetingWebServer(
            callbacks,
            host="127.0.0.1",
            auth_token=self.owner_token,
        )
        self.url = self.server.start()
        self.wait_for_health()
        return self

    def wait_for_health(self, timeout: float = 5.0) -> None:
        """Wait for the public health endpoint instead of relying on thread timing."""
        if self.url is None:
            raise RuntimeError("HubFixture has not been started")
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"{self.url}/health", timeout=0.5)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
            time.sleep(0.05)
        raise RuntimeError(f"HubFixture health check timed out: {last_error}")

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        from holdspeak.db import reset_database

        try:
            if self.server is not None:
                self.server.stop()
        finally:
            self.server = None
            self.url = None
            self.database = None
            reset_database()
            if self._tempdir is not None:
                self._tempdir.cleanup()
                self._tempdir = None
