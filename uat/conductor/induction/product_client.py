"""A thin HTTP client for driving the product under test.

Seeds and probes reach the product the same way its own web UI does — over
HTTP, through the public routes, carrying the run's own per-HOME web auth
token. This is a deliberate coupling: if a product route rename breaks a
seed or a probe, that is a real cross-surface break a failing harness test
should catch (HSU-1-02 risk table).

``httpx`` (a dependency already, not ``holdspeak``) keeps multipart upload
and timeouts trivial.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class ProductClient:
    """Talks to one booted product run at its loopback address."""

    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        # /health is auth-exempt; everything else wants the token when the run
        # is LAN-bound. Loopback runs ignore it, so always sending it is safe.
        return {"X-HoldSpeak-Token": self.token} if self.token else {}

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as c:
            return c.get(self.base_url + path, params=params, headers=self._headers())

    def get_json(self, path: str, params: dict | None = None) -> Any:
        return self.get(path, params=params).json()

    def post_json(self, path: str, body: dict | None = None) -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as c:
            return c.post(self.base_url + path, json=body or {}, headers=self._headers())

    def post_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as c:
            headers = {**self._headers(), "Content-Type": content_type}
            return c.post(self.base_url + path, content=data, headers=headers)

    def post_multipart(
        self,
        path: str,
        *,
        file_path: Path,
        data: dict | None = None,
        field: str = "file",
    ) -> httpx.Response:
        file_path = Path(file_path)
        with httpx.Client(timeout=self.timeout) as c, open(file_path, "rb") as fh:
            files = {field: (file_path.name, fh, "application/octet-stream")}
            return c.post(
                self.base_url + path,
                files=files,
                data={k: str(v) for k, v in (data or {}).items()},
                headers=self._headers(),
            )

    def health_ok(self) -> bool:
        try:
            return self.get("/health").status_code == 200
        except httpx.HTTPError:
            return False
