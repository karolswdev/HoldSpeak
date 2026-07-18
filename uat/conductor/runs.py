"""Run lifecycle: boot an isolated HoldSpeak, watch it, restart it, tear it down.

A *run* owns a fresh isolated HOME, a booted product subprocess, and its
captured logs. ``RunManager`` is the conductor's single owner of that
lifecycle — the site and the API talk to it, never to a subprocess
directly. Restart-with-a-different-deck is a first-class verb because
scenarios depend on breaking the world mid-sitting (a ``bad-endpoint``
restart, a killed node) and watching the product degrade honestly.

Run status is honest: ``booting → up`` on a healthy boot, ``failed`` (with
the product's own log tail) when it never answers, ``down`` after teardown.
Never a hang.
"""

from __future__ import annotations

import datetime as _dt
import secrets
import socket
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import home as home_mod
from . import paths
from .db import Database
from .product import ProductProcess
from .induction.decks import DeckRegistry
from .induction.nodes import NodeManager
from .induction.product_client import ProductClient
from .induction.recipes import RecipeEngine

# Port convention (HANDOVER §runbook): conductor 8799, product-under-test 8788,
# the real hub's 8765 left untouched so a sitting runs beside the owner's desk.
DEFAULT_PRODUCT_PORT = 8788

# A minimal, fully-local overlay: a product that boots fast with no model warm
# and no intel endpoint. Named decks (HSU-1-02) layer richer postures on top.
GOLDEN_LOCAL_OVERLAY = {
    "config_version": 1,
    "model": {"warm_on_start": False},
    "meeting": {"intel_enabled": False},
}


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _new_run_id() -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"run-{stamp}-{secrets.token_hex(3)}"


def _find_free_port(preferred: int) -> int:
    """First free TCP port at or above ``preferred`` (so a second run coexists).

    Probes the wildcard address WITHOUT SO_REUSEADDR: a loopback-only probe
    with SO_REUSEADDR reports a port as free while a LAN-bound (0.0.0.0)
    product still holds it, which stacked several runs onto one port and let
    a stale run answer another run's pairing URL.
    """
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    # Fall back to an ephemeral port the OS hands us.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _lan_ip() -> str:
    """Best-effort primary LAN address (no packet actually leaves the host)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


@dataclass
class Run:
    id: str
    status: str = "pending"
    deck: str | None = None
    config: dict = field(default_factory=dict)
    product_host: str = "127.0.0.1"
    product_port: int = DEFAULT_PRODUCT_PORT
    lan: bool = False
    token: str | None = None
    pairing_url: str | None = None
    pid: int | None = None
    error: str | None = None
    boot_link_caches: bool = True
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def to_public(self) -> dict:
        """The API/JSON shape — pairing facts included, the token surfaced so a
        device can be pointed at the run the way it pairs with the real hub."""
        d = asdict(self)
        d["home"] = str(paths.run_home(self.id))
        d["logs_dir"] = str(paths.run_logs_dir(self.id))
        d["pairing"] = {
            "url": self.pairing_url,
            "token": self.token,
            "token_source": "per-run web_auth_token (isolated HOME)" if self.token else None,
            "lan": self.lan,
        }
        return d

    def _db_row(self) -> dict:
        import json

        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "deck": self.deck,
            "config_json": json.dumps(self.config),
            "product_host": self.product_host,
            "product_port": self.product_port,
            "lan": 1 if self.lan else 0,
            "pairing_url": self.pairing_url,
            "token": self.token,
            "pid": self.pid,
            "error": self.error,
        }


class RunManager:
    """Owns every live run: create/boot, restart-with-deck, teardown, logs."""

    def __init__(
        self,
        db: Database | None = None,
        *,
        product_port: int = DEFAULT_PRODUCT_PORT,
        boot_timeout: float = 45.0,
        link_caches: bool = True,
        deck_registry: DeckRegistry | None = None,
        recipe_engine: RecipeEngine | None = None,
    ) -> None:
        self.db = db or Database()
        self.base_product_port = product_port
        self.boot_timeout = boot_timeout
        self.link_caches = link_caches
        self.decks = deck_registry or DeckRegistry()
        self.recipes = recipe_engine or RecipeEngine()
        self._runs: dict[str, tuple[Run, ProductProcess]] = {}
        self._node_managers: dict[str, NodeManager] = {}
        self._steer_sessions: dict[str, set[str]] = {}
        self._lock = threading.RLock()

    # --- creation / boot --------------------------------------------------

    def _resolve_overlay(self, deck: str | None, config: dict | None) -> dict:
        """A deck name resolves to its overlay; an explicit config overrides/merges.

        With neither, the fully-local golden overlay is used so a run always
        boots something real.
        """
        if deck is not None:
            base = dict(self.decks.load(deck))
        elif config is not None:
            base = {}
        else:
            base = dict(GOLDEN_LOCAL_OVERLAY)
        if config:
            base = _deep_merge(base, config)
        return base

    def create_run(
        self,
        *,
        config: dict | None = None,
        deck: str | None = None,
        lan: bool = False,
        port: int | None = None,
        link_caches: bool | None = None,
    ) -> Run:
        overlay = self._resolve_overlay(deck, config)
        run = Run(
            id=_new_run_id(),
            deck=deck,
            config=overlay,
            lan=lan,
            boot_link_caches=self.link_caches if link_caches is None else link_caches,
        )
        with self._lock:
            self._boot_into(run, overlay, lan=lan, port=port, link_caches=run.boot_link_caches)
            return run

    def _boot_into(
        self, run: Run, overlay: dict, *, lan: bool, port: int | None, link_caches: bool | None = None
    ) -> None:
        run.status = "booting"
        run.updated_at = _utcnow()
        run.lan = lan
        if link_caches is None:
            link_caches = run.boot_link_caches
        run.boot_link_caches = link_caches
        run.product_host = "0.0.0.0" if lan else "127.0.0.1"
        run.product_port = _find_free_port(port or self.base_product_port)

        home_dir = paths.run_home(run.id)
        home_mod.assemble_home(home_dir, link_caches=link_caches)

        # A LAN bind is refused by the product without an auth token, so a
        # LAN run gets its own token written into the overlay before boot.
        overlay = dict(overlay)
        if lan:
            # Keep one token for the whole sitting. Recipes restart the same run
            # onto different decks; rotating here would silently unpair every
            # iPhone/iPad halfway through a pack.
            token = (
                overlay.get("meeting", {}).get("web_auth_token")
                or run.token
                or secrets.token_urlsafe(24)
            )
            meeting = dict(overlay.get("meeting") or {})
            meeting["web_auth_token"] = token
            overlay["meeting"] = meeting
            run.token = token
        else:
            run.token = (overlay.get("meeting") or {}).get("web_auth_token")
        run.config = overlay
        home_mod.write_config(home_dir, overlay)

        product = ProductProcess(
            home=home_dir,
            port=run.product_port,
            host=run.product_host,
            log_dir=paths.run_logs_dir(run.id),
        )
        product.start()
        run.pid = product.pid
        self._runs[run.id] = (run, product)

        healthy = product.wait_healthy(timeout=self.boot_timeout)
        if healthy:
            run.status = "up"
            run.error = None
            run.pairing_url = self._pairing_url(run)
        else:
            run.status = "failed"
            tail = product.tail(60)
            run.error = _fail_summary(product, tail)
            # Leave the corpse un-reaped only briefly: stop it so it can't orphan.
            product.stop()
            run.pid = None
        run.updated_at = _utcnow()
        self.db.upsert_run(run._db_row())

    def _pairing_url(self, run: Run) -> str:
        host = _lan_ip() if run.lan else "127.0.0.1"
        base = f"http://{host}:{run.product_port}"
        if run.token:
            return f"{base}/?token={run.token}"
        return base

    # --- restart / teardown ----------------------------------------------

    def restart(
        self,
        run_id: str,
        *,
        config: dict | None = None,
        deck: str | None = None,
        lan: bool | None = None,
        link_caches: bool | None = None,
    ) -> Run:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is None:
                raise KeyError(run_id)
            run, product = entry
            product.stop()
            run.pid = None
            if deck is not None or config is not None:
                run.deck = deck if deck is not None else run.deck
                new_overlay = self._resolve_overlay(deck, config)
            else:
                new_overlay = dict(run.config)
            new_lan = run.lan if lan is None else lan
            self._boot_into(run, new_overlay, lan=new_lan, port=None, link_caches=link_caches)
            return run

    # --- induction host interface (RecipeHost) ---------------------------

    def ensure_deck(self, run_id: str, deck: str, *, link_caches: bool = True) -> bool:
        """Boot the run on ``deck`` + cache posture; restart only if it differs.

        Returns True if a restart happened. This is what makes recipe apply
        idempotent at the boot layer: applying the same recipe twice does not
        needlessly recycle the product.
        """
        with self._lock:
            run = self._runs.get(run_id, (None, None))[0]
            if run is None:
                raise KeyError(run_id)
            if run.status == "up" and run.deck == deck and run.boot_link_caches == link_caches:
                return False
            self.restart(run_id, deck=deck, link_caches=link_caches)
            return True

    def product_client(self, run_id: str) -> ProductClient:
        run = self.get(run_id)
        if run is None:
            raise KeyError(run_id)
        # Conductor→product calls always ride loopback (a LAN run still answers
        # there); the token is sent regardless so it works either way.
        return ProductClient(f"http://127.0.0.1:{run.product_port}", token=run.token)

    def run_home(self, run_id: str):
        return paths.run_home(run_id)

    def _nodes(self, run_id: str) -> NodeManager:
        nm = self._node_managers.get(run_id)
        if nm is None:
            nm = NodeManager()
            self._node_managers[run_id] = nm
        return nm

    def spawn_node(self, run_id: str, name: str) -> dict:
        with self._lock:
            run = self._runs.get(run_id, (None, None))[0]
            if run is None:
                raise KeyError(run_id)
            node = self._nodes(run_id).spawn(
                name=name,
                hub_url=f"http://127.0.0.1:{run.product_port}",
                home=paths.run_home(run_id),
                log_dir=paths.run_logs_dir(run_id),
                token=run.token,
            )
            return node.to_dict()

    def kill_node(self, run_id: str, name: str) -> bool:
        with self._lock:
            return self._nodes(run_id).kill(name)

    def spawn_pane(self, run_id: str, name: str, command: str) -> dict:
        """Spawn a tmux coder pane via the product's factory route; track the
        session so it's killed on teardown (no residue in the owner's tmux)."""
        from .induction import steering

        run = self._runs.get(run_id, (None, None))[0]
        if run is None:
            raise KeyError(run_id)
        session = steering.session_name(run_id, name)
        self._steer_sessions.setdefault(run_id, set()).add(session)
        return steering.spawn(self.product_client(run_id), session, command)

    def list_nodes(self, run_id: str) -> list[dict]:
        return [n.to_dict() for n in self._nodes(run_id).list()]

    def node_log_text(self, run_id: str, node: str) -> str:
        """The worker's own log for provenance reads — the harness owns the
        process it spawned, so scanning its log for a job's CLAIM marker is
        honest provenance, not a poke at the product DB. `mesh serve` logs
        through the product's file logger (`setup_logging`, non-verbose), which
        writes to `$HOME/.local/share/holdspeak/holdspeak.log` — the worker's
        HOME is this run's home — so we read that plus any captured std streams.
        Returns "" when nothing has been written yet."""
        home = paths.run_home(run_id)
        logs = paths.run_logs_dir(run_id)
        candidates = [
            home / ".local" / "share" / "holdspeak" / "holdspeak.log",
            logs / f"node-{node}.stdout.log",
            logs / f"node-{node}.stderr.log",
        ]
        blob = ""
        for p in candidates:
            if p.exists():
                try:
                    blob += p.read_text(errors="ignore")
                except OSError:
                    pass
        return blob

    def apply_recipe(self, run_id: str, name: str, *, allow_intel: bool = True):
        return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)

    def apply_seed(self, run_id: str, name: str) -> dict:
        """Apply a seed manifest to a booted run ad-hoc (outside a full recipe)."""
        from .induction.seeds import Seeder

        manifest = self.recipes.seed_registry.load(name)
        return Seeder(self.product_client(run_id)).apply(manifest).to_dict()

    def seed_names(self) -> list[str]:
        return self.recipes.seed_registry.names()

    def teardown(self, run_id: str) -> Run | None:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is None:
                row = self.db.get_run(run_id)
                return None if row is None else _run_from_row(row)
            run, product = entry
            nm = self._node_managers.pop(run_id, None)
            if nm is not None:
                nm.kill_all()
            for session in self._steer_sessions.pop(run_id, set()):
                from .induction import steering

                steering.kill_session(session)
            product.stop()
            run.status = "down"
            run.pid = None
            run.updated_at = _utcnow()
            self.db.upsert_run(run._db_row())
            del self._runs[run_id]
            return run

    def teardown_all(self) -> None:
        with self._lock:
            for run_id in list(self._runs.keys()):
                try:
                    self.teardown(run_id)
                except Exception:
                    pass

    # --- reads ------------------------------------------------------------

    def get(self, run_id: str) -> Run | None:
        with self._lock:
            entry = self._runs.get(run_id)
            if entry is not None:
                run, product = entry
                # Refresh liveness honestly — a crashed product flips to down.
                if run.status == "up" and not product.is_alive():
                    run.status = "down"
                    run.pid = None
                    run.updated_at = _utcnow()
                    self.db.upsert_run(run._db_row())
                return run
        row = self.db.get_run(run_id)
        return _run_from_row(row) if row else None

    def list_runs(self) -> list[Run]:
        with self._lock:
            live = {rid: run for rid, (run, _) in self._runs.items()}
        rows = self.db.list_runs()
        out: list[Run] = []
        for row in rows:
            out.append(live.get(row["id"]) or _run_from_row(row))
        # Include any live run not yet flushed (shouldn't happen, but be safe).
        for rid, run in live.items():
            if not any(r.id == rid for r in out):
                out.append(run)
        return out

    def logs(self, run_id: str, n: int = 80) -> dict[str, str]:
        from .product import _tail_file

        with self._lock:
            entry = self._runs.get(run_id)
            if entry is not None:
                streams = entry[1].tail(n)
                streams["application"] = _tail_file(
                    paths.run_home(run_id)
                    / ".local"
                    / "share"
                    / "holdspeak"
                    / "holdspeak.log",
                    n,
                )
                return streams
        # A torn-down run still has its logs on disk.
        logs_dir = paths.run_logs_dir(run_id)
        return {
            "stdout": _tail_file(logs_dir / "product.stdout.log", n),
            "stderr": _tail_file(logs_dir / "product.stderr.log", n),
            "application": _tail_file(
                paths.run_home(run_id)
                / ".local"
                / "share"
                / "holdspeak"
                / "holdspeak.log",
                n,
            ),
        }


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursive dict merge — overlay wins; nested mappings merge, not replace."""
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _fail_summary(product: ProductProcess, tail: dict[str, str]) -> str:
    lines = ["product failed to become healthy"]
    exit_code = product.proc.poll() if product.proc else None
    if exit_code is not None:
        lines.append(f"exit code: {exit_code}")
    if tail.get("stderr"):
        lines.append("--- stderr tail ---")
        lines.append(tail["stderr"])
    elif tail.get("stdout"):
        lines.append("--- stdout tail ---")
        lines.append(tail["stdout"])
    return "\n".join(lines)


def _run_from_row(row: dict) -> Run:
    import json

    try:
        config = json.loads(row.get("config_json") or "{}")
    except ValueError:
        config = {}
    return Run(
        id=row["id"],
        status=row["status"],
        deck=row.get("deck"),
        config=config,
        product_host=row.get("product_host") or "127.0.0.1",
        product_port=row.get("product_port") or DEFAULT_PRODUCT_PORT,
        lan=bool(row.get("lan")),
        token=row.get("token"),
        pairing_url=row.get("pairing_url"),
        pid=row.get("pid"),
        error=row.get("error"),
        created_at=row.get("created_at") or _utcnow(),
        updated_at=row.get("updated_at") or _utcnow(),
    )
