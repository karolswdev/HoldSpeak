"""`holdspeak mesh serve` — the reference mesh-edge worker (HS-85-03).

Turns THIS machine into a mesh edge: polls the hub's relay queue (HS-85-01),
executes each claimed run on this node's OWN provider (its engine, its
profiles, its keys — nothing transits the mesh), and posts the result back.

Running the command IS the consent (the voice-macro posture: configuring is
consent; nothing serves unless started). The token rides an env var — never
a flag — so credentials stay out of shell history. Every claim poll stamps
this node's liveness on the hub; that polling is the mesh's only heartbeat.

Deliberately a reference implementation: synchronous, one job at a time.
"""
from __future__ import annotations

import json
import os
import random
import signal
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

from ..logging_config import get_logger

log = get_logger("mesh.serve")

DEFAULT_POLL_INTERVAL_SECONDS = 3.0
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
DEFAULT_TOKEN_ENV = "HOLDSPEAK_HUB_TOKEN"


def _default_http_post(url: str, payload: dict[str, Any], *, token: str, timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-HoldSpeak-Token"] = token
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - the paired hub
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


class MeshServeWorker:
    """The poll → execute → report loop, factored for tests."""

    def __init__(
        self,
        *,
        hub_url: str,
        node: str,
        token: str = "",
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        http_post: Optional[Callable[..., dict[str, Any]]] = None,
        engine_factory: Optional[Callable[[], Any]] = None,
        sleep: Callable[[float], None] = time.sleep,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.hub_url = str(hub_url or "").rstrip("/")
        self.node = str(node or "").strip()
        self.token = token
        self.poll_interval = max(0.5, float(poll_interval_seconds))
        self._http_post = http_post or _default_http_post
        self._engine_factory = engine_factory
        self._engine: Any = None
        self._sleep = sleep
        self._timeout = timeout_seconds
        self._stop = False
        self._backoff = BACKOFF_BASE_SECONDS

    # ── the steps ────────────────────────────────────────────────────────

    def stop(self, *_args: Any) -> None:
        self._stop = True

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._http_post(
            f"{self.hub_url}{path}", payload, token=self.token, timeout=self._timeout
        )

    def claim_once(self) -> Optional[dict[str, Any]]:
        """One claim poll (this stamps the node's liveness hub-side)."""
        data = self._post("/api/mesh/relay/claim", {"node": self.node})
        return data.get("job")

    def _engine_for_run(self) -> Any:
        if self._engine is None:
            if self._engine_factory is not None:
                self._engine = self._engine_factory()
            else:
                # THIS node's own resolution — its engine, its profiles, its keys
                from ..intel.providers import build_configured_meeting_intel

                self._engine = build_configured_meeting_intel()
        return self._engine

    def execute(self, job: dict[str, Any]) -> bool:
        """Run one claimed job on this node's provider; report the outcome."""
        job_id = str(job.get("id") or "")
        started = time.monotonic()
        try:
            engine = self._engine_for_run()
            kwargs: dict[str, Any] = {
                "system_prompt": str(job.get("system_prompt") or ""),
                "user_prompt": str(job.get("user_prompt") or ""),
            }
            if job.get("temperature") is not None:
                kwargs["temperature"] = job["temperature"]
            if job.get("max_tokens") is not None:
                kwargs["max_tokens"] = job["max_tokens"]
            result = engine.run_prompt(**kwargs)
        except Exception as exc:
            log.info(
                "job %s FAILED on node %s after %.1fs: %s",
                job_id, self.node, time.monotonic() - started, exc,
            )
            try:
                self._post(f"/api/mesh/relay/{job_id}/fail", {"error": str(exc)})
            except Exception as report_exc:
                log.warning("could not report failure for %s: %s", job_id, report_exc)
            return False
        log.info(
            "job %s COMPLETED on node %s in %.1fs (%d chars)",
            job_id, self.node, time.monotonic() - started, len(result or ""),
        )
        try:
            self._post(f"/api/mesh/relay/{job_id}/complete", {"result": str(result or "")})
        except Exception as report_exc:
            log.warning("could not report completion for %s: %s", job_id, report_exc)
            return False
        return True

    def poll_step(self) -> bool:
        """One loop tick: claim; execute when work arrived. True = did work."""
        try:
            job = self.claim_once()
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            log.warning(
                "hub unreachable (%s); retrying in %.0fs", exc, self._backoff
            )
            self._sleep(self._backoff)
            self._backoff = min(BACKOFF_MAX_SECONDS, self._backoff * 2)
            return False
        self._backoff = BACKOFF_BASE_SECONDS
        if job is None:
            return False
        log.info("job %s CLAIMED for node %s", job.get("id"), self.node)
        self.execute(job)
        return True

    # ── the modes ────────────────────────────────────────────────────────

    def run_once(self) -> int:
        """Claim at most one job, run it, exit (the scripting/test seam)."""
        try:
            job = self.claim_once()
        except Exception as exc:
            log.error("hub unreachable: %s", exc)
            return 1
        if job is None:
            log.info("no relay work queued for node %s", self.node)
            return 0
        log.info("job %s CLAIMED for node %s", job.get("id"), self.node)
        return 0 if self.execute(job) else 1

    def run_forever(self) -> int:
        log.info(
            "serving the mesh as node %s (hub %s, poll %.1fs) — Ctrl-C to stop",
            self.node, self.hub_url, self.poll_interval,
        )
        while not self._stop:
            did_work = self.poll_step()
            if self._stop:
                break
            if not did_work:
                # jittered idle wait; a working loop re-polls immediately
                self._sleep(self.poll_interval * random.uniform(0.8, 1.2))
        log.info("node %s stopped serving the mesh", self.node)
        return 0


def run_mesh_serve_command(args: Any) -> int:
    hub_url = str(getattr(args, "hub", "") or "http://127.0.0.1:8765")
    token_env = str(getattr(args, "token_env", "") or DEFAULT_TOKEN_ENV)
    token = os.environ.get(token_env, "").strip()

    node = str(getattr(args, "node", "") or "").strip()
    if not node:
        from ..config import Config
        from ..mesh import resolve_device_name

        try:
            configured = Config.load().mesh.device_name
        except Exception:
            configured = ""
        node = resolve_device_name(configured)

    worker = MeshServeWorker(hub_url=hub_url, node=node, token=token)
    if getattr(args, "once", False):
        return worker.run_once()

    signal.signal(signal.SIGINT, worker.stop)
    signal.signal(signal.SIGTERM, worker.stop)
    return worker.run_forever()
