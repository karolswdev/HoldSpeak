"""`holdspeak node serve` — the outbound node link worker (HS-94-03).

Turns THIS machine into a linked delivery node: it initiates every
connection to the hub (PLATFORM-CONTRACT §6 — no inbound server runs
here), authenticates with its OWN per-node token (never the browser
token), says hello with protocol/identity/capabilities/resume-cursor,
then heartbeats every 5 seconds carrying metadata-only event batches.

Custody rules (§6.1): the token rides an environment variable —
never argv, never logs. The event cursor persists at
``~/.holdspeak/node_cursor_<name>.json`` so kill/restart resumes
without duplicates or gaps (the hub's hello response is the acked
cursor; the node emits from there). Hub loss backs off exponentially
with jitter, bounded — the link is patient, never a hot loop.

Companion verbs (`holdspeak node token create|rotate|revoke|list`)
manage pairings in ``~/.holdspeak/node_auth_tokens.json`` on the HUB
machine; rotation/revocation takes effect immediately, no repository
edit involved.

Transport: outbound HTTP hello/heartbeat on the proven ``mesh serve``
pattern (see :mod:`holdspeak.delivery.node_link` for the rationale).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from ..delivery.node_link import (
    HEARTBEAT_SECONDS,
    NODE_PROTOCOL,
    NodeLinkError,
    NodeTokenStore,
)
from ..logging_config import get_logger

log = get_logger("node.serve")

DEFAULT_TOKEN_ENV = "HOLDSPEAK_NODE_TOKEN"
NODE_TOKEN_HEADER = "X-HoldSpeak-Node-Token"
DEFAULT_CAPABILITIES = ["delivery.source", "coder.steering"]
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
MAX_BATCH_EVENTS = 100


def default_cursor_path(name: str) -> Path:
    return Path.home() / ".holdspeak" / f"node_cursor_{name}.json"


def default_link_config_path(name: str) -> Path:
    return Path.home() / ".holdspeak" / f"node_link_{name}.json"


def load_node_capabilities(name: str, path: Optional[Path] = None) -> list[str]:
    """This node's declared capability list — declarative local
    config (``{"capabilities": [...]}``), defaults when absent."""
    config_path = Path(path) if path else default_link_config_path(name)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return list(DEFAULT_CAPABILITIES)
    caps = raw.get("capabilities") if isinstance(raw, dict) else None
    if isinstance(caps, list) and caps:
        return [str(c) for c in caps]
    return list(DEFAULT_CAPABILITIES)


def _default_http_post(
    url: str, payload: dict[str, Any], *, token: str, timeout: float
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers[NODE_TOKEN_HEADER] = token
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — the paired hub
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


class NodeLinkWorker:
    """hello → heartbeat loop, factored for tests (the MeshServeWorker
    discipline): every side effect is an injectable seam."""

    def __init__(
        self,
        *,
        hub_url: str,
        name: str,
        token: str,
        capabilities: Optional[list[str]] = None,
        cursor_path: Optional[Path] = None,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        http_post: Optional[Callable[..., dict[str, Any]]] = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: Callable[[], float] = random.random,
        timeout_seconds: float = 10.0,
        event_source: Optional[Callable[[], list[dict[str, Any]]]] = None,
        backoff_base_seconds: float = BACKOFF_BASE_SECONDS,
        backoff_max_seconds: float = BACKOFF_MAX_SECONDS,
    ) -> None:
        self.hub_url = str(hub_url or "").rstrip("/")
        self.name = str(name or "").strip()
        self._token = token
        self.capabilities = list(
            capabilities if capabilities is not None else load_node_capabilities(self.name)
        )
        self.cursor_path = Path(cursor_path) if cursor_path else default_cursor_path(self.name)
        self.heartbeat_seconds = max(0.05, float(heartbeat_seconds))
        self._http_post = http_post or _default_http_post
        self._sleep = sleep
        self._rng = rng
        self._timeout = timeout_seconds
        self._backoff_base = float(backoff_base_seconds)
        self._backoff_max = float(backoff_max_seconds)
        self._event_source = event_source
        self.instance_id = os.urandom(8).hex()
        self.cursor = self._load_cursor()
        self.connected = False
        self.node_id: Optional[str] = None
        self._stop = False
        self._failures = 0
        self._outbox: list[dict[str, Any]] = []  # unsequenced, not yet sent
        self._pending: list[dict[str, Any]] = []  # sequenced, awaiting ack

    # ── cursor custody ───────────────────────────────────────────────

    def _load_cursor(self) -> int:
        try:
            raw = json.loads(self.cursor_path.read_text(encoding="utf-8"))
            return max(0, int(raw.get("cursor", 0)))
        except (OSError, ValueError, TypeError, AttributeError):
            return 0

    def _save_cursor(self) -> None:
        try:
            self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
            self.cursor_path.write_text(
                json.dumps({"cursor": self.cursor}) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            log.warning("could not persist node cursor: %s", exc)

    # ── the wire ─────────────────────────────────────────────────────

    def stop(self, *_args: Any) -> None:
        self._stop = True

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._http_post(
            f"{self.hub_url}{path}", payload, token=self._token, timeout=self._timeout
        )

    def emit(self, event: dict[str, Any]) -> None:
        """Queue one metadata event (no seq — the worker sequences at
        send time so replays and resyncs renumber cleanly)."""
        self._outbox.append(dict(event))

    def hello(self) -> dict[str, Any]:
        """Introduce this node; adopt the hub's acked cursor as truth
        (a hub that remembers more than our file wins; a fresh hub
        adopts our persisted cursor)."""
        response = self._post(
            "/api/delivery/node/hello",
            {
                "node_protocol": NODE_PROTOCOL,
                "name": self.name,
                "instance_id": self.instance_id,
                "capabilities": self.capabilities,
                "resume_cursor": self.cursor,
            },
        )
        self.node_id = str(response.get("node_id") or "")
        self.cursor = int(response.get("cursor") or 0)
        self._save_cursor()
        self._resequence_pending()
        self.connected = True
        self._failures = 0
        log.info(
            "node %s linked to hub %s (cursor %d, commands %s)",
            self.name, self.hub_url, self.cursor,
            "enabled" if response.get("commands_enabled") else f"disabled: {response.get('compat')}",
        )
        return response

    def _resequence_pending(self) -> None:
        seq = self.cursor
        for event in self._pending:
            seq += 1
            event["seq"] = seq

    def _flush_batch(self) -> list[dict[str, Any]]:
        if self._event_source is not None:
            for event in self._event_source() or []:
                self.emit(event)
        next_seq = self.cursor + len(self._pending)
        while self._outbox and len(self._pending) < MAX_BATCH_EVENTS:
            event = self._outbox.pop(0)
            next_seq += 1
            event["seq"] = next_seq
            self._pending.append(event)
        return self._pending[:MAX_BATCH_EVENTS]

    def heartbeat(self) -> dict[str, Any]:
        batch = self._flush_batch()
        response = self._post(
            "/api/delivery/node/heartbeat",
            {"name": self.name, "instance_id": self.instance_id, "events": batch},
        )
        acked = int(response.get("cursor") or 0)
        if acked > self.cursor:
            self.cursor = acked
            self._save_cursor()
        self._pending = [e for e in self._pending if int(e["seq"]) > acked]
        if response.get("resync"):
            # The hub saw a gap it cannot replay across: renumber what
            # we still hold from its acked cursor and try again next
            # beat — never drop truth, never invent continuity.
            self.cursor = acked
            self._save_cursor()
            self._resequence_pending()
            log.warning("hub requested a resync at cursor %d", acked)
        return response

    # ── the loop ─────────────────────────────────────────────────────

    def _backoff_wait(self) -> float:
        """Bounded exponential backoff with jitter (§6.3)."""
        self._failures += 1
        ceiling = min(
            self._backoff_max, self._backoff_base * (2 ** (self._failures - 1))
        )
        return ceiling * (0.5 + 0.5 * self._rng())

    def step(self) -> bool:
        """One tick: (re)hello when unlinked, else heartbeat. Returns
        True when the link is up after the tick."""
        try:
            if not self.connected:
                self.hello()
            else:
                self.heartbeat()
            return True
        except NodeServeAuthError as exc:
            # Rotated/revoked mid-flight: keep backing off (a rotation
            # may land in our env on restart) but say why, by name.
            self.connected = False
            log.warning("hub refused this node's credential (%s); backing off", exc)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            self.connected = False
            log.warning("hub unreachable (%s); backing off", exc)
        self._sleep(self._backoff_wait())
        return False

    def run_once(self) -> int:
        """hello + one heartbeat, then exit (the scripting seam)."""
        try:
            self.hello()
            self.heartbeat()
        except Exception as exc:
            log.error("node link failed: %s", exc)
            return 1
        return 0

    def run_forever(self) -> int:
        log.info(
            "serving the node link as %s (hub %s, heartbeat %.1fs) — Ctrl-C to stop",
            self.name, self.hub_url, self.heartbeat_seconds,
        )
        while not self._stop:
            up = self.step()
            if self._stop:
                break
            if up:
                self._sleep(self.heartbeat_seconds)
        log.info("node %s stopped serving the link", self.name)
        return 0


class NodeServeAuthError(RuntimeError):
    """The hub rejected this node's credential (401) — distinct from
    transport loss so the operator sees rotation/revocation by name."""


def _raising_http_post(
    url: str, payload: dict[str, Any], *, token: str, timeout: float
) -> dict[str, Any]:
    """Default transport with typed 401 handling. Split from
    ``_default_http_post`` so tests can reuse either seam."""
    try:
        return _default_http_post(url, payload, token=token, timeout=timeout)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            pass
        reason = ""
        try:
            reason = str(json.loads(body).get("error") or "")
        except (ValueError, AttributeError):
            pass
        if int(exc.code) == 401:
            raise NodeServeAuthError(reason or "unauthorized") from None
        raise


def _tick_event_source(worker_ref: dict[str, Any]) -> Callable[[], list[dict[str, Any]]]:
    """`--emit-ticks`: one synthetic metadata event per heartbeat —
    the live proof that cursors resume across kill/restart without a
    duplicate or a gap."""

    def source() -> list[dict[str, Any]]:
        worker: NodeLinkWorker = worker_ref["worker"]
        tick = worker.cursor + len(worker._pending) + len(worker._outbox) + 1
        return [{"kind": "rail.cursor", "detail": {"tick": tick}}]

    return source


# ── CLI ──────────────────────────────────────────────────────────────


def run_node_serve_command(args: Any) -> int:
    hub_url = str(getattr(args, "hub", "") or "http://127.0.0.1:8765")
    name = str(getattr(args, "name", "") or "").strip()
    if not name:
        log.error("a node name is required (--name)")
        return 2
    token_env = str(getattr(args, "token_env", "") or DEFAULT_TOKEN_ENV)
    token = os.environ.get(token_env, "").strip()
    if not token:
        log.error(
            "no node token in $%s — pair on the hub with "
            "`holdspeak node token create --name %s` and export the token",
            token_env, name,
        )
        return 2

    capabilities = list(getattr(args, "capability", None) or []) or None
    cursor_path = getattr(args, "cursor_path", None)
    worker_ref: dict[str, Any] = {}
    event_source = None
    if getattr(args, "emit_ticks", False):
        event_source = _tick_event_source(worker_ref)
    worker = NodeLinkWorker(
        hub_url=hub_url,
        name=name,
        token=token,
        capabilities=capabilities,
        cursor_path=Path(cursor_path) if cursor_path else None,
        heartbeat_seconds=float(
            getattr(args, "heartbeat_seconds", None) or HEARTBEAT_SECONDS
        ),
        http_post=_raising_http_post,
        event_source=event_source,
        backoff_base_seconds=float(
            getattr(args, "backoff_base", None) or BACKOFF_BASE_SECONDS
        ),
        backoff_max_seconds=float(
            getattr(args, "backoff_max", None) or BACKOFF_MAX_SECONDS
        ),
    )
    worker_ref["worker"] = worker
    if getattr(args, "once", False):
        return worker.run_once()
    signal.signal(signal.SIGINT, worker.stop)
    signal.signal(signal.SIGTERM, worker.stop)
    return worker.run_forever()


def run_node_token_command(args: Any) -> int:
    """Pairing custody on the hub machine: create prints the token
    ONCE to stdout (that is the distribution moment); list never
    shows token material."""
    store_path = getattr(args, "store_path", None)
    store = NodeTokenStore(Path(store_path) if store_path else None)
    action = str(getattr(args, "token_action", "") or "")
    name = str(getattr(args, "name", "") or "").strip()
    try:
        if action == "create":
            node_id, token = store.create(name)
            print(token)
            log.info("paired node %s (%s); export the printed token as $%s",
                     name, node_id, DEFAULT_TOKEN_ENV)
            return 0
        if action == "rotate":
            print(store.rotate(name))
            log.info("rotated node token for %s; the old token is dead", name)
            return 0
        if action == "revoke":
            store.revoke(name)
            log.info("revoked node %s; its hello/heartbeat now refuse by name", name)
            return 0
        if action == "list":
            for row in store.status_rows():
                state = "revoked" if row["revoked"] else "paired"
                print(f"{row['name']}\t{row['node_id']}\t{state}\t{row['created_at']}")
            return 0
    except NodeLinkError as exc:
        log.error("%s", exc)
        return 1
    print("usage: holdspeak node token {create|rotate|revoke|list} [--name NAME]")
    return 2


def build_parser() -> argparse.ArgumentParser:
    """The `holdspeak node …` argument surface (also the module's own
    `python -m` entry, which is what the two-process proof drives)."""
    parser = argparse.ArgumentParser(prog="holdspeak node")
    sub = parser.add_subparsers(dest="node_command")

    serve = sub.add_parser("serve", help="Link this machine to a hub as a delivery node")
    serve.add_argument("--hub", default="http://127.0.0.1:8765", help="Hub base URL")
    serve.add_argument("--name", default="", help="This node's paired name")
    serve.add_argument(
        "--token-env", default=DEFAULT_TOKEN_ENV,
        help=f"Env var holding the node token (default: {DEFAULT_TOKEN_ENV})",
    )
    serve.add_argument(
        "--capability", action="append", default=None,
        help="Declare a capability (repeatable); default: local link config",
    )
    serve.add_argument("--cursor-path", default=None, help=argparse.SUPPRESS)
    serve.add_argument("--heartbeat-seconds", type=float, default=None, help=argparse.SUPPRESS)
    serve.add_argument("--backoff-base", type=float, default=None, help=argparse.SUPPRESS)
    serve.add_argument("--backoff-max", type=float, default=None, help=argparse.SUPPRESS)
    serve.add_argument("--emit-ticks", action="store_true", help=argparse.SUPPRESS)
    serve.add_argument("--once", action="store_true", help="hello + one heartbeat, then exit")

    token = sub.add_parser("token", help="Manage node pairings on the hub")
    token.add_argument("token_action", choices=["create", "rotate", "revoke", "list"])
    token.add_argument("--name", default="", help="Node name")
    token.add_argument("--store-path", default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.node_command == "serve":
        return run_node_serve_command(args)
    if args.node_command == "token":
        return run_node_token_command(args)
    print("usage: holdspeak node {serve|token} …")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
